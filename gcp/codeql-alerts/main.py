import os
import json
import requests
import logging
from datetime import datetime
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_structured(message, severity="INFO", payload=None):
    """Log a structured JSON message for Google Cloud Logging."""
    entry = {
        "severity": severity,
        "message": message,
        "component": "codeql-alert-fetcher",
    }
    if payload:
        entry.update(payload)
    print(json.dumps(entry))  # Print to stdout is captured by Cloud Logging


def get_repos_by_topic(topic, github_token):
    """Search for repositories with a specific topic using GitHub API."""
    url = "https://api.github.com/search/repositories"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"q": f"topic:{topic}", "per_page": 100}

    repos = []
    page = 1

    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            log_structured(f"Failed to search repos: {response.text}", severity="ERROR")
            return []

        data = response.json()
        items = data.get("items", [])
        if not items:
            break

        repos.extend(items)
        # Check for pagination (incomplete check but sufficient for < 1000 repos)
        if len(repos) >= data.get("total_count", 0):
            break
        page += 1

    return repos


def get_all_open_alerts(repo_full_name, github_token):
    """Fetch all open CodeQL alerts for a repository."""
    url = f"https://api.github.com/repos/{repo_full_name}/code-scanning/alerts"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    params = {"tool_name": "CodeQL", "state": "open", "per_page": 100}

    all_alerts = []
    page = 1

    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 404:
            # Code scanning might not be enabled
            return []
        if response.status_code != 200:
            log_structured(
                f"Error fetching alerts for {repo_full_name}: {response.text}",
                severity="WARNING",
            )
            return []

        data = response.json()
        if not data:
            break

        all_alerts.extend(data)
        if len(data) < 100:
            break
        page += 1

    return all_alerts


def get_alert_details(alert, repo_full_name, repo_html_url):
    """Extract relevant details from an alert."""
    return {
        "repository": repo_full_name,
        "repo_url": repo_html_url,
        "alert_number": alert.get("number"),
        "html_url": alert.get("html_url"),
        "state": alert.get("state"),
        "created_at": alert.get("created_at"),
        "rule_id": alert.get("rule", {}).get("id"),
        "rule_description": alert.get("rule", {}).get("description"),
        "severity": alert.get("rule", {}).get("security_severity_level"),
        "original_severity": alert.get("rule", {}).get("severity"),
        "message": alert.get("most_recent_instance", {}).get("message", {}).get("text"),
    }


def upload_to_gcs(bucket_name, filename, data):
    """Upload data to Google Cloud Storage."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_string(
            json.dumps(data, indent=2), content_type="application/json"
        )
        log_structured(f"Uploaded {filename} to {bucket_name}", severity="INFO")
        return True
    except Exception as e:
        log_structured(f"Failed to upload to GCS: {str(e)}", severity="ERROR")
        return False


def main(request):
    """Cloud Function entry point."""
    # Getting configuration from Environment Variables
    github_token = os.environ.get("CODEQL_GITHUB_TOKEN")
    bucket_name = os.environ.get("CODEQL_GCS_BUCKET_NAME")
    topic = os.environ.get("CODEQL_GITHUB_TOPIC", "bcregistry")

    if not github_token:
        log_structured("CODEQL_GITHUB_TOKEN environment variable is not set", severity="ERROR")
        return "Internal Server Error: Missing Configuration", 500

    log_structured(f"Starting CodeQL alert fetch for topic: {topic}", severity="INFO")

    repos = get_repos_by_topic(topic, github_token)
    log_structured(f"Found {len(repos)} repositories", severity="INFO")

    critical_findings = []
    high_findings = []

    for repo in repos:
        full_name = repo["full_name"]
        html_url = repo["html_url"]

        alerts = get_all_open_alerts(full_name, github_token)

        if alerts:
            for alert in alerts:
                rule = alert.get("rule", {})
                sec_severity = rule.get("security_severity_level")

                details = get_alert_details(alert, full_name, html_url)

                if sec_severity == "critical":
                    critical_findings.append(details)
                elif sec_severity == "high":
                    high_findings.append(details)

    log_structured(
        f"Processing complete. Critical: {len(critical_findings)}, High: {len(high_findings)}",
        severity="INFO",
    )

    # Alerting via Logging
    if len(critical_findings) > 0:
        log_structured(
            f"Found {len(critical_findings)} CRITICAL CodeQL alerts!",
            severity="CRITICAL",
            payload={
                "alert_count": len(critical_findings),
                "findings": critical_findings[:10],
            },  # Limit payload size
        )

    if not bucket_name:
        log_structured("GCS_BUCKET_NAME not set, skipping upload", severity="WARNING")
        return json.dumps(
            {
                "status": "success",
                "critical_count": len(critical_findings),
                "high_count": len(high_findings),
                "message": "Processed successfully, but no bucket configured.",
            }
        ), 200

    # Upload results
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    upload_to_gcs(bucket_name, f"codeql_critical_{timestamp}.json", critical_findings)
    upload_to_gcs(bucket_name, f"codeql_high_{timestamp}.json", high_findings)

    # Also overwrite 'latest' files for easy access
    upload_to_gcs(bucket_name, "codeql_critical_latest.json", critical_findings)
    upload_to_gcs(bucket_name, "codeql_high_latest.json", high_findings)

    return json.dumps(
        {
            "status": "success",
            "critical_count": len(critical_findings),
            "high_count": len(high_findings),
            "bucket": bucket_name,
        }
    ), 200
