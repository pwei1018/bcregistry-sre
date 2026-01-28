import os
import argparse

import json
import yaml
import questionary
from jinja2 import Environment, FileSystemLoader


import shutil
import subprocess
from google.cloud import monitoring_v3, run_v2
from google.cloud import resourcemanager_v3
from googleapiclient import discovery
from googleapiclient.errors import HttpError
from google.auth import default


# Get script directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_BASE = os.path.join(SCRIPT_DIR, "outputs")
CACHE_FILE = os.path.join(OUTPUT_BASE, "resource_cache.json")


class CacheManager:
    def __init__(self, cache_file=CACHE_FILE):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value
        self.save_cache()


CACHE = CacheManager()


def get_cloud_run_services(project_id, refresh=False):
    """Fetches Cloud Run services using the Cloud Run v2 API."""
    cache_key = f"services_{project_id}"
    if not refresh:
        cached = CACHE.get(cache_key)
        if cached is not None:
            return cached

    try:
        client = run_v2.ServicesClient()
        parent = f"projects/{project_id}/locations/-"
        request = run_v2.ListServicesRequest(parent=parent)
        page_result = client.list_services(request=request)
        result = [s.name.split("/")[-1] for s in page_result]
        CACHE.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Error fetching Cloud Run services: {e}")
        return []


def get_cloud_sql_instances(project_id, refresh=False):
    """Fetches Cloud SQL instances using the SQL Admin API."""
    cache_key = f"db_instances_{project_id}"
    if not refresh:
        cached = CACHE.get(cache_key)
        if cached is not None:
            return cached

    try:
        credentials, _ = default()
        service = discovery.build("sqladmin", "v1beta4", credentials=credentials)
        request = service.instances().list(project=project_id)
        response = request.execute()
        instances = response.get("items", [])
        # Return format expected by main: dicts with name, connectionName, project
        result = [
            {
                "name": i["name"],
                "project": i["project"],
                "connectionName": i.get(
                    "connectionName", f"{i['project']}:{i['region']}:{i['name']}"
                ),
            }
            for i in instances
        ]
        CACHE.set(cache_key, result)
        return result
    except HttpError as e:
        # Simplified error message for common 403 API not enabled errors
        if e.resp.status == 403 and "accessNotConfigured" in str(e):
            print(
                "Warning: Cloud SQL Admin API not enabled or accessible in the current quota project. Skipping DB alerts."
            )
        else:
            print(f"Warning: Could not fetch Cloud SQL instances: {e.resp.reason}")
        return []
    except Exception as e:
        print(f"Error fetching Cloud SQL instances: {e}")
        return []


def get_uptime_checks(project_id, refresh=False):
    """Fetches Uptime Check Configs using the Monitoring API."""
    cache_key = f"uptime_checks_{project_id}"
    if not refresh:
        cached = CACHE.get(cache_key)
        if cached is not None:
            return cached

    try:
        client = monitoring_v3.UptimeCheckServiceClient()
        parent = f"projects/{project_id}"
        checks = client.list_uptime_check_configs(parent=parent)
        # Return format: dicts with name, displayName
        result = [{"name": c.name, "displayName": c.display_name} for c in checks]
        CACHE.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Error fetching Uptime Checks: {e}")
        return []


def get_active_projects(refresh=False):
    """Fetches active production projects (ending in -prod) using Resource Manager API."""
    cache_key = "active_projects"
    if not refresh:
        cached = CACHE.get(cache_key)
        if cached is not None:
            return cached

    try:
        client = resourcemanager_v3.ProjectsClient()
        request = resourcemanager_v3.SearchProjectsRequest(
            query="lifecycleState:ACTIVE"
        )
        page_result = client.search_projects(request=request)
        result = sorted(
            [p.project_id for p in page_result if p.project_id.endswith("-prod")]
        )
        CACHE.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Warning: Could not list projects: {e}")
        return []


def get_notification_channels(project_id, refresh=False):
    """Fetches Notification Channels using the Monitoring API."""
    cache_key = f"channels_{project_id}"
    if not refresh:
        cached = CACHE.get(cache_key)
        if cached is not None:
            return cached

    try:
        client = monitoring_v3.NotificationChannelServiceClient()
        parent = f"projects/{project_id}"
        # Fetch enabled channels
        channels = client.list_notification_channels(name=parent)
        # Return format: dicts with name (resource ID) and displayName
        result = [
            {"name": c.name, "displayName": c.display_name, "type": c.type}
            for c in channels
        ]
        CACHE.set(cache_key, result)
        return result
    except Exception as e:
        print(f"Error fetching Notification Channels: {e}")
        return []


def get_current_project_id():
    """Attempts to get the current project ID from authorization environment."""
    try:
        _, project = default()
        return project
    except Exception:
        return None


def get_existing_policies(project_id):
    """
    Fetches existing alert policies for the project.
    Returns a dictionary mapping displayName to policy name (projects/.../alertPolicies/...).
    """
    print("Fetching existing alert policies...")
    try:
        # List all policies with their name and displayName
        cmd = [
            "gcloud",
            "alpha",
            "monitoring",
            "policies",
            "list",
            f"--project={project_id}",
            "--format=json(name,displayName)",
        ]
        result = subprocess.run(cmd, check=True, capture_output=True)
        policies_json = json.loads(result.stdout)

        # Create map: "My Alert Display Name" -> "projects/123/alertPolicies/456"
        policy_map = {p.get("displayName"): p.get("name") for p in policies_json}
        return policy_map
    except Exception as e:
        print(f"Warning: Could not fetch existing policies: {e}")
        return {}


def apply_policies(output_dirs, project_id, dry_run=False):
    """
    Applies all alert policies in the specified output directories to the project.
    """
    if isinstance(output_dirs, str):
        output_dirs = [output_dirs]

    all_files = []
    for d in output_dirs:
        if os.path.exists(d):
            all_files.extend([(d, f) for f in os.listdir(d) if f.endswith(".yaml")])

    if not all_files:
        print("No policy files found to apply.")
        return

    # Fetch existing policies for upsert logic
    existing_policies = get_existing_policies(project_id) if not dry_run else {}

    print(f"\nReady to apply {len(all_files)} alert policies to project '{project_id}'")
    if dry_run:
        print("DRY RUN MODE: Commands will be printed but not executed.")

    confirm = questionary.confirm(
        "Do you want to apply these policies now?", default=False
    ).ask()

    if not confirm:
        print("Skipping application.")
        return

    for output_dir, filename in all_files:
        filepath = os.path.join(output_dir, filename)

        # Read the file to get displayName
        try:
            with open(filepath, "r") as f:
                policy_content = yaml.safe_load(f)
                display_name = policy_content.get("displayName")
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        if not display_name:
            print(f"Skipping {filename}: Could not determine displayName")
            continue

        existing_name = existing_policies.get(display_name)

        if existing_name:
            # UPDATE
            action = "update"
            identifier = existing_name
            print(f"Updating existing policy '{display_name}' ({existing_name})...")
        else:
            # CREATE
            action = "create"
            identifier = None
            print(f"Creating new policy '{display_name}'...")

        # Construct Command
        cmd = ["gcloud", "alpha", "monitoring", "policies"]

        if action == "update":
            cmd.append("update")
            cmd.append(identifier)
            cmd.append(f"--policy-from-file={filepath}")
        else:
            cmd.append("create")
            cmd.append(f"--policy-from-file={filepath}")

        cmd.append(f"--project={project_id}")
        cmd.append("--quiet")

        if dry_run:
            print(f"[Dry Run] Would execute: {' '.join(cmd)}")
        else:
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✅ Successfully {action}d policy from {filename}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to {action} policy from {filename}")
                print(f"Error: {e.stderr.decode()}")


def load_config():
    """Loads the configs.yml file from the script directory."""
    config_path = os.path.join(SCRIPT_DIR, "configs.yml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load configs.yml: {e}")
            return {}
    return {}


def main():
    parser = argparse.ArgumentParser(
        description="Generate Alert Policies Interactively"
    )
    # We keep these as optional overrides, but interactive is primary
    parser.add_argument("--product", help="Product name (e.g., auth, pay)")
    parser.add_argument(
        "--channels", nargs="+", help="List of notification channel resource IDs"
    )
    # Allow overriding project, otherwise try to detect
    parser.add_argument("--project", help="GCP Project ID")
    parser.add_argument(
        "--refresh", action="store_true", help="Refresh cached resources"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate policy application (print commands only)",
    )

    args = parser.parse_args()
    refresh_cache = args.refresh

    print("--- Alert Policy Generator (Production) ---")

    # Load Config
    config = load_config()

    # 1. Product Name Selection (First Step now)
    # keys in config that assume to be products (exclude 'channels' key if present as top level)
    # Based on file content, 'channels' is a key at the bottom.
    config_products = sorted([k for k in config.keys() if k != "channels"])

    # Merge with hardcoded list if needed, or just use config + existing defaults?
    # Existing defaults had "common", "devops", "sre" etc.
    # config seems to have most of them. Let's strictly prefer config + Other.

    product_choices = config_products + ["Other"]

    if args.product:
        product_name = args.product
    else:
        product_name = questionary.select(
            "Select Product Name:", choices=product_choices
        ).ask()

        if product_name == "Other":
            product_name = questionary.text("Enter Product Name manually:").ask()

    if not product_name:
        print("Product name is required.")
        return

    # Auto-resolve from config
    project_id = args.project
    channels = args.channels

    MONITORING_PROJECT_ID = "google-mpf-547144339658"

    if product_name in config and not project_id:
        print(f"Using configuration for '{product_name}'...")
        product_config = config[product_name]

        # Set Project ID
        project_id = product_config.get("project_id")
        print(f"  -> Project ID: {project_id}")
        # Resolve Channels
        if not channels:
            config_channel_names = product_config.get("channels", [])
            print(f"  -> resolving channels: {config_channel_names}...")

            available_channels = get_notification_channels(
                MONITORING_PROJECT_ID, refresh=refresh_cache
            )

            # Map displayName to Name (ID)
            channel_map = {c["displayName"]: c["name"] for c in available_channels}

            # Expand channel group names to people names
            # e.g., "SRE" -> ["Patrick Wei", "Andriy Bolyachevets"]
            people_names = []
            channels_section = config.get("channels", {})
            for group_name in config_channel_names:
                if group_name in channels_section:
                    people_names.extend(channels_section[group_name])
                else:
                    # If not a group, treat as a direct channel name
                    people_names.append(group_name)

            resolved_ids = []
            for name in people_names:
                if name in channel_map:
                    resolved_ids.append(channel_map[name])
                else:
                    print(f"  [Warning] Channel '{name}' not found in GCP.")

            if resolved_ids:
                channels = resolved_ids
                print(f"  -> Resolved {len(channels)} channels.")
            else:
                print("  [Warning] No channels resolved from config.")

    # Fallback for Project ID
    if not project_id:
        # Try to list projects
        print("Fetching available projects...")
        projects = get_active_projects(refresh=refresh_cache)

        if projects:
            current = get_current_project_id()
            default_choice = current if current in projects else None

            project_id = questionary.select(
                "Select Production GCP Project:",
                choices=projects + ["Exit"],
                default=default_choice,
            ).ask()

            if project_id == "Exit":
                print("Exiting...")
                return
        else:
            project_id = questionary.text("Enter GCP Project ID:").ask()

    if not project_id:
        print("Project ID is required.")
        return

    # Fallback for Channels
    if not channels:
        print(f"\nFetching Notification Channels from {MONITORING_PROJECT_ID}...")
        available_channels = get_notification_channels(
            MONITORING_PROJECT_ID, refresh=refresh_cache
        )

        if available_channels:
            channel_choices = [
                questionary.Choice(
                    title=f"{c['displayName']} ({c['type']})", value=c["name"]
                )
                for c in available_channels
            ]

            channels = questionary.checkbox(
                "Select Notification Channels (Space to select, Enter to confirm):",
                choices=channel_choices,
            ).ask()

        else:
            print("No notification channels found or error occurred.")
            channels_input = questionary.text(
                "Enter Notification Channel IDs manually (space separated):"
            ).ask()
            channels = channels_input.split() if channels_input else []

    # 3. Resource Type Selection
    resource_type = questionary.select(
        "Select Resource Type:",
        choices=["Cloud Run Service", "Cloud SQL Database", "Exit"],
    ).ask()

    if resource_type == "Exit":
        print("Exiting...")
        return

    # Initialize variables
    selected_services = []  # List of tuples/dicts or just names
    uptime_checks = []  # Cache uptime checks if needed

    if resource_type == "Cloud Run Service":
        # Cloud Run Service Selection
        print(f"\nFetching Cloud Run Services from {project_id}...")
        services = get_cloud_run_services(project_id, refresh=refresh_cache)

        if not services:
            print("No Cloud Run services found.")
            manual_service = questionary.text(
                "Enter Cloud Run Service Name manually:"
            ).ask()
            if manual_service:
                selected_services = [manual_service]
        else:
            selected_services = questionary.checkbox(
                "Select Cloud Run Services (Space to select, Enter to confirm):",
                choices=services,
            ).ask()

        if not selected_services:
            print("No services selected. Exiting.")
            return

        # Fetch Uptime Checks once for auto-matching
        print(f"\nFetching Uptime Checks from {project_id}...")
        uptime_checks = get_uptime_checks(project_id, refresh=refresh_cache)

    elif resource_type == "Cloud SQL Database":
        # Cloud SQL Database Selection
        print(f"\nFetching Cloud SQL Instances from {project_id}...")
        db_instances = get_cloud_sql_instances(project_id, refresh=refresh_cache)

        if not db_instances:
            print("No Cloud SQL instances found. Skipping generation.")
            return

        db_choices = [f"{i['name']} ({i['connectionName']})" for i in db_instances]
        selected_db_str = questionary.select(
            "Select Cloud SQL Database:", choices=db_choices
        ).ask()

        selected_instance = next(
            i
            for i in db_instances
            if f"{i['name']} ({i['connectionName']})" == selected_db_str
        )
        # Standardize structure to list for loop processing
        # Use a dict to store metadata
        selected_services = [
            {
                "type": "sql",
                "name": selected_instance["name"],
                "connectionName": selected_instance["connectionName"],
            }
        ]

    # --- Generation ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = os.path.join(base_dir, "templates")
    env_loader = Environment(loader=FileSystemLoader(template_dir))

    generated_dirs = []

    print(f"\nGenerating alerts for {product_name}...")

    for service_item in selected_services:
        context = {
            "project_id": project_id,
            "product_name": product_name,
            "environment": "prod",
            "notification_channels": channels,
        }

        templates = []

        if resource_type == "Cloud Run Service":
            # service_item is a string (service_resource_name)
            service_resource_name = service_item

            # Clean service name
            if service_resource_name.endswith("-prod"):
                service_name = service_resource_name[:-5]
            else:
                service_name = service_resource_name

            context["service_name"] = service_name
            context["service_display_name"] = service_name.replace("-", " ").upper()
            context["service_resource_name"] = service_resource_name

            # Templates for Cloud Run
            templates = [
                ("cloud_run_runtime.yaml.j2", "runtime.yaml"),
                ("cloud_run_crashes.yaml.j2", "crashes.yaml"),
                ("cloud_run_errors.yaml.j2", "errors.yaml"),
            ]

            # Auto-match Uptime Check
            # Logic: Look for uptime check where displayName contains service_name
            # or is roughly similar.
            service_uptime_id = None
            if uptime_checks:
                # Try exact match first or contains
                # e.g. service=pay-api, uptime="Pay API Uptime" or "pay-api-prod"
                for check in uptime_checks:
                    # Simple heuristic: exact match of resource name or display name contains service name
                    # Adjust as needed based on naming conventions
                    # Convention seen: "Pay API Startup Latency" (alert), Uptime check might be "pay-api" or "Pay API"
                    c_name = check["displayName"].lower()
                    if (
                        service_name.lower() in c_name
                        or service_name.replace("-", " ").lower() in c_name
                    ):
                        service_uptime_id = check["name"].split("/")[-1]
                        break

            if service_uptime_id:
                context["uptime_check_id"] = service_uptime_id
                templates.append(("cloud_run_uptime.yaml.j2", "uptime_failure.yaml"))
                print(f"  [Info] Matched Uptime Check for {service_name}")
            else:
                print(f"  [Info] No matching Uptime Check found for {service_name}")

        elif resource_type == "Cloud SQL Database":
            # service_item is a dict
            database_id = service_item["connectionName"]
            db_name_short = service_item["name"]

            service_name = (
                db_name_short[:-5] if db_name_short.endswith("-prod") else db_name_short
            )

            context["service_name"] = service_name
            context["service_display_name"] = service_name.replace("-", " ").upper()
            context["service_resource_name"] = db_name_short
            context["database_id"] = database_id
            context["db_name"] = db_name_short

            templates = [("cloud_sql_runtime.yaml.j2", "db_runtime.yaml")]

        # Output Generation
        output_dir = os.path.join(
            OUTPUT_BASE, "generated_policies", product_name, context["service_name"]
        )

        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)

        generated_dirs.append(output_dir)

        for template_name, output_name in templates:
            try:
                template = env_loader.get_template(template_name)
                output = template.render(context)

                output_path = os.path.join(output_dir, output_name)
                with open(output_path, "w") as f:
                    f.write(output)
                # print(f"Generated {output_path}")
            except Exception as e:
                print(
                    f"Error generating {output_name} for {context['service_name']}: {e}"
                )

        print(f"  -> Generated {len(templates)} policies for {context['service_name']}")

    print("\nGeneration Complete. Files are ready.")

    # Prompt to apply
    # Use global MONITORING_PROJECT_ID (google-mpf...) as the target project for creating policies
    # assuming policies are defined there (scoping project).
    MONITORING_PROJECT_ID = "google-mpf-547144339658"
    apply_policies(generated_dirs, MONITORING_PROJECT_ID, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
