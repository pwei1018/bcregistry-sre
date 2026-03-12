"""
Scan all managed bcgov repos for tech stacks and dependency versions.

Focuses on Python, Node.js, Nuxt, Vue, and their major dependencies.
Handles monolithic repos by scanning subdirectories for dependency files.
Marks end-of-life (EOL) versions and exports results to CSV.
"""

import base64
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("CODEQL_GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("CODEQL_GITHUB_TOKEN is not set in .env")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

TODAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── EOL definitions ───────────────────────────────────────────────────
# Format: package -> list of (max_major, max_minor_or_None, eol_date, note)
# A version matches if its major version <= max_major (and minor <= max_minor if set)
EOL_VERSIONS = {
    # Python frameworks
    "flask": [
        (1, None, "2023-08-01", "Flask 1.x — unsupported, upgrade to 3.x"),
        (2, None, "2025-04-01", "Flask 2.x — end of support, upgrade to 3.x"),
    ],
    "django": [
        (3, None, "2024-04-01", "Django 3.x — EOL"),
        (4, 1, "2023-12-01", "Django 4.1 — EOL"),
    ],
    "sqlalchemy": [
        (1, None, "2024-09-05", "SQLAlchemy 1.x — EOL Sep 2024"),
    ],
    "pydantic": [
        (1, None, "2024-07-01", "Pydantic 1.x — superseded by v2"),
    ],
    "celery": [
        (4, None, "2023-07-01", "Celery 4.x — EOL"),
    ],
    "cryptography": [
        (41, None, "2024-01-01", "cryptography <42 — upgrade recommended"),
    ],
    "protobuf": [
        (3, None, "2024-06-01", "protobuf 3.x — EOL, upgrade to 4.x+"),
    ],
    # Node.js frameworks
    "vue": [
        (2, None, "2023-12-31", "Vue 2.x — EOL Dec 2023"),
    ],
    "nuxt": [
        (2, None, "2024-06-30", "Nuxt 2.x — EOL Jun 2024"),
        (3, None, "2026-07-31", "Nuxt 3.x — EOL Jul 2026, migrate to Nuxt 4"),
    ],
    "vuex": [
        (3, None, "2023-12-31", "Vuex 3.x — tied to Vue 2 (EOL), use Pinia"),
        (4, None, "2024-01-01", "Vuex 4.x — maintenance only, migrate to Pinia"),
    ],
    "webpack": [
        (4, None, "2023-01-01", "webpack 4.x — EOL, upgrade to 5.x+"),
    ],
    "typescript": [
        (3, None, "2023-01-01", "TypeScript 3.x — very outdated"),
        (4, None, "2025-01-01", "TypeScript 4.x — outdated, upgrade to 5.x"),
    ],
    "node": [
        (16, None, "2023-09-11", "Node.js 16 — EOL Sep 2023"),
        (18, None, "2025-04-30", "Node.js 18 — EOL Apr 2025"),
        (20, None, "2026-04-30", "Node.js 20 — EOL Apr 2026"),
    ],
    "jest": [
        (27, None, "2024-01-01", "Jest 27 — outdated, upgrade to 29+"),
    ],
    "axios": [
        (0, None, "2023-11-01", "axios 0.x — outdated, upgrade to 1.x"),
    ],
    "vue-router": [
        (3, None, "2023-12-31", "vue-router 3.x — tied to Vue 2 (EOL)"),
    ],
    "vite": [
        (3, None, "2024-01-01", "Vite 3.x — outdated"),
        (4, None, "2025-06-01", "Vite 4.x — outdated, upgrade to 5+"),
    ],
}


def extract_major_minor(version_str):
    """Extract (major, minor) from a version string. Returns None if unparseable."""
    if not version_str or version_str in ("unspecified", "latest", "catalog:"):
        return None
    # Strip common prefixes: ^, ~, >=, ==, <=, >, <, ~=, !=, =
    cleaned = re.sub(r"^[^0-9]*", "", version_str)
    match = re.match(r"(\d+)(?:\.(\d+))?", cleaned)
    if match:
        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else None
        return (major, minor)
    return None


def check_eol(package, version_str):
    """Check if a package version is EOL. Returns (is_eol, note) or (False, '')."""
    if package not in EOL_VERSIONS:
        return False, ""

    version = extract_major_minor(version_str)
    if version is None:
        return False, ""

    pkg_major, pkg_minor = version

    for eol_major, eol_minor, eol_date, note in EOL_VERSIONS[package]:
        if eol_minor is not None:
            # Check both major and minor
            if pkg_major < eol_major or (
                pkg_major == eol_major and (pkg_minor is None or pkg_minor <= eol_minor)
            ):
                return True, note
        else:
            # Check major only
            if pkg_major <= eol_major:
                return True, note

    return False, ""


# ── Python packages we care about ─────────────────────────────────────
PYTHON_KEY_DEPS = [
    "flask",
    "django",
    "fastapi",
    "starlette",
    "uvicorn",
    "gunicorn",
    "sqlalchemy",
    "alembic",
    "celery",
    "redis",
    "psycopg2",
    "psycopg2-binary",
    "pydantic",
    "marshmallow",
    "pytest",
    "requests",
    "httpx",
    "aiohttp",
    "sentry-sdk",
    "google-cloud-storage",
    "google-cloud-pubsub",
    "google-cloud-secret-manager",
    "protobuf",
    "grpcio",
    "cryptography",
    "authlib",
    "pyjwt",
    "python-jose",
    "jinja2",
    "nats-py",
    "launchdarkly-server-sdk",
]

# Node packages we care about
NODE_KEY_DEPS = [
    "vue",
    "nuxt",
    "react",
    "next",
    "angular",
    "@angular/core",
    "typescript",
    "vite",
    "webpack",
    "vitest",
    "jest",
    "cypress",
    "axios",
    "pinia",
    "vuex",
    "vue-router",
    "express",
    "tailwindcss",
    "@nuxt/ui",
    "primevue",
]


# ── GitHub API helpers ────────────────────────────────────────────────


def get_paginated(url):
    """Fetch all pages from a paginated GitHub API endpoint."""
    results = []
    while url:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        results.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
    return results


def get_file_content(owner, repo, path):
    """Fetch and decode a file from the GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return None
    data = resp.json()
    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return None


def get_repo_tree(owner, repo):
    """Get the full file tree for a repo (recursive)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        return []
    data = resp.json()
    return [item["path"] for item in data.get("tree", []) if item["type"] == "blob"]


# ── Dependency file parsing ───────────────────────────────────────────


def find_dep_files(file_paths):
    """Find dependency files from a list of file paths."""
    dep_files = {"python": [], "node": []}
    for path in file_paths:
        basename = os.path.basename(path)
        if basename in (
            "requirements.txt",
            "Pipfile",
            "setup.py",
            "setup.cfg",
            "pyproject.toml",
        ):
            dep_files["python"].append(path)
        elif "/requirements/" in path and path.endswith(".txt"):
            dep_files["python"].append(path)
        elif basename == "package.json" and "node_modules" not in path:
            dep_files["node"].append(path)
    return dep_files


def parse_requirements_txt(content):
    """Parse requirements.txt and return dict of {package: version}."""
    deps = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([><=!~]+\s*[\d.*]+)?", line)
        if match:
            pkg = match.group(1).lower().replace("_", "-")
            ver = match.group(2).strip() if match.group(2) else "unspecified"
            deps[pkg] = ver
    return deps


def parse_pyproject_toml(content):
    """Parse pyproject.toml for dependencies (basic parsing)."""
    deps = {}
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in ("[project.dependencies]", "dependencies = ["):
            in_deps = True
            continue
        if stripped.startswith("[tool.poetry.dependencies]"):
            in_deps = True
            continue
        if in_deps:
            if stripped.startswith("[") or (
                stripped == "" and not stripped.startswith('"')
            ):
                if stripped.startswith("["):
                    in_deps = False
                continue
            match = re.match(
                r'["\s]*([a-zA-Z0-9_.-]+)\s*([><=!~^]+\s*[\d.*]+)?', stripped
            )
            if match:
                pkg = match.group(1).lower().replace("_", "-")
                ver = match.group(2).strip() if match.group(2) else "unspecified"
                deps[pkg] = ver
            match2 = re.match(r'([a-zA-Z0-9_.-]+)\s*=\s*["\']([^"\']+)["\']', stripped)
            if match2:
                pkg = match2.group(1).lower().replace("_", "-")
                deps[pkg] = match2.group(2)
    return deps


def parse_package_json(content):
    """Parse package.json and return key info."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}

    info = {}
    engines = data.get("engines", {})
    if "node" in engines:
        info["node"] = engines["node"]

    all_deps = {}
    all_deps.update(data.get("dependencies", {}))
    all_deps.update(data.get("devDependencies", {}))

    for pkg in NODE_KEY_DEPS:
        if pkg in all_deps:
            info[pkg] = all_deps[pkg]

    return info


def filter_key_python_deps(deps):
    """Filter to only key Python dependencies."""
    return {k: v for k, v in deps.items() if k in PYTHON_KEY_DEPS}


def get_subproject_name(path):
    """Get the subproject name from a file path."""
    parts = path.split("/")
    if len(parts) <= 1:
        return "(root)"
    return "/".join(parts[:-1])


# ── Repo scanning ────────────────────────────────────────────────────


def scan_repo(owner, repo):
    """Scan a repo for tech stacks. Returns structured results."""
    results = {"python": [], "node": []}

    tree = get_repo_tree(owner, repo)
    if not tree:
        return results

    dep_files = find_dep_files(tree)

    for path in dep_files["python"]:
        content = get_file_content(owner, repo, path)
        if not content:
            continue
        basename = os.path.basename(path)
        if basename == "requirements.txt" or path.endswith(".txt"):
            deps = parse_requirements_txt(content)
        elif basename == "pyproject.toml":
            deps = parse_pyproject_toml(content)
        else:
            continue
        key_deps = filter_key_python_deps(deps)
        if key_deps:
            results["python"].append(
                {
                    "subproject": get_subproject_name(path),
                    "file": path,
                    "deps": key_deps,
                }
            )

    for path in dep_files["node"]:
        content = get_file_content(owner, repo, path)
        if not content:
            continue
        info = parse_package_json(content)
        if info:
            results["node"].append(
                {
                    "subproject": get_subproject_name(path),
                    "file": path,
                    "deps": info,
                }
            )

    return results


# ── Output ────────────────────────────────────────────────────────────


def build_rows(all_results):
    """Build flat rows for display and CSV export."""
    rows = []
    for repo, results in sorted(all_results.items()):
        for stack_type in ("python", "node"):
            for sp in results.get(stack_type, []):
                for pkg, ver in sorted(sp["deps"].items()):
                    is_eol, eol_note = check_eol(pkg, ver)
                    rows.append(
                        {
                            "repo": repo,
                            "subproject": sp["subproject"],
                            "type": "Python" if stack_type == "python" else "Node.js",
                            "package": pkg,
                            "version": ver,
                            "eol": "⛔ EOL" if is_eol else "✅",
                            "eol_note": eol_note if is_eol else "",
                        }
                    )
    return rows


def print_results(rows, all_results):
    """Print formatted results with EOL markers."""
    print("\n" + "=" * 90)
    print("  TECH STACK REPORT — bcgov REPOS")
    print("=" * 90)

    # Count EOL items
    eol_rows = [r for r in rows if r["eol"] == "⛔ EOL"]
    ok_rows = [r for r in rows if r["eol"] == "✅"]

    # ── EOL Summary ───────────────────────────────────────────────────
    if eol_rows:
        print(f"\n  🚨 END-OF-LIFE DEPENDENCIES ({len(eol_rows)} found)")
        print("  " + "-" * 86)
        print(f"  {'Repo':<30} {'Subproject':<20} {'Package':<18} {'Version':<12} Note")
        print("  " + "-" * 86)
        for r in eol_rows:
            repo_short = r["repo"].replace("bcgov/", "")
            print(
                f"  {repo_short:<30} {r['subproject']:<20} "
                f"{r['package']:<18} {r['version']:<12} {r['eol_note']}"
            )

    # ── Per-repo detail ───────────────────────────────────────────────
    current_repo = None
    current_sp = None
    for r in rows:
        if r["repo"] != current_repo:
            current_repo = r["repo"]
            current_sp = None
            print(f"\n  📁 {current_repo}")
        if r["subproject"] != current_sp:
            current_sp = r["subproject"]
            print(f"    📦 {current_sp} ({r['type']})")
        eol_marker = " ⛔ EOL" if r["eol"] == "⛔ EOL" else ""
        print(f"       {r['package']:<30} {r['version']:<15}{eol_marker}")

    # ── Summary stats ─────────────────────────────────────────────────
    repos = set(r["repo"] for r in rows)
    py_repos = set(r["repo"] for r in rows if r["type"] == "Python")
    node_repos = set(r["repo"] for r in rows if r["type"] == "Node.js")
    eol_repos = set(r["repo"] for r in eol_rows)

    print(f"\n{'─' * 90}")
    print("  SUMMARY")
    print(f"{'─' * 90}")
    print(f"  Total repos with dependencies: {len(repos)}")
    print(f"  Repos with Python:             {len(py_repos)}")
    print(f"  Repos with Node.js/Vue/Nuxt:   {len(node_repos)}")
    print(f"  Total dependencies tracked:    {len(rows)}")
    print(f"  ⛔ EOL dependencies:            {len(eol_rows)}")
    print(f"  ✅ Current dependencies:        {len(ok_rows)}")
    print(f"  Repos with EOL deps:           {len(eol_repos)}")
    print()


def export_csv(rows, filename):
    """Export rows to CSV file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "repo",
                "subproject",
                "type",
                "package",
                "version",
                "eol",
                "eol_note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"  📄 CSV exported to: {filepath}")
    return filepath


def export_markdown(rows, filename):
    """Export results as a markdown report."""
    filepath = os.path.join(OUTPUT_DIR, filename)

    eol_rows = [r for r in rows if r["eol"] == "⛔ EOL"]
    ok_rows = [r for r in rows if r["eol"] == "✅"]
    repos = sorted(set(r["repo"] for r in rows))
    eol_repos = sorted(set(r["repo"] for r in eol_rows))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Tech Stack Report — bcgov Repos\n\n")
        f.write(f"**Generated:** {TODAY}\n\n")

        # Summary
        f.write("## Summary\n\n")
        f.write("| Metric | Count |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total repos scanned | {len(repos)} |\n")
        f.write(f"| Total dependencies tracked | {len(rows)} |\n")
        f.write(f"| ⛔ EOL dependencies | {len(eol_rows)} |\n")
        f.write(f"| ✅ Current dependencies | {len(ok_rows)} |\n")
        f.write(f"| Repos with EOL deps | {len(eol_repos)} |\n\n")

        # EOL highlights
        if eol_rows:
            f.write("## ⛔ EOL Dependencies\n\n")
            f.write("| Repo | Subproject | Package | Version | Note |\n")
            f.write("|------|-----------|---------|---------|------|\n")
            for r in eol_rows:
                repo_short = r["repo"].replace("bcgov/", "")
                f.write(
                    f"| {repo_short} | {r['subproject']} | "
                    f"{r['package']} | `{r['version']}` | {r['eol_note']} |\n"
                )
            f.write("\n")

        # Per-repo detail
        f.write("## Repo Details\n\n")
        for repo in repos:
            repo_rows = [r for r in rows if r["repo"] == repo]
            repo_short = repo.replace("bcgov/", "")
            repo_eol_count = sum(1 for r in repo_rows if r["eol"] == "⛔ EOL")
            eol_badge = f" — ⛔ {repo_eol_count} EOL" if repo_eol_count > 0 else ""

            f.write(f"### [{repo_short}](https://github.com/{repo}){eol_badge}\n\n")

            # Group by subproject
            subprojects = []
            seen = set()
            for r in repo_rows:
                if r["subproject"] not in seen:
                    subprojects.append(r["subproject"])
                    seen.add(r["subproject"])

            for sp in subprojects:
                sp_rows = [r for r in repo_rows if r["subproject"] == sp]
                sp_type = sp_rows[0]["type"]
                f.write(f"**{sp}** ({sp_type})\n\n")
                f.write("| Package | Version | Status |\n")
                f.write("|---------|---------|--------|\n")
                for r in sp_rows:
                    status = "⛔ EOL" if r["eol"] == "⛔ EOL" else "✅"
                    f.write(f"| {r['package']} | `{r['version']}` | {status} |\n")
                f.write("\n")

    print(f"  📄 Markdown exported to: {filepath}")
    return filepath


# ── Main ──────────────────────────────────────────────────────────────


def main():
    print("Fetching managed bcgov repos...")
    repos_url = "https://api.github.com/user/repos?type=all&sort=updated&per_page=100"
    all_repos = get_paginated(repos_url)

    managed_repos = [
        r
        for r in all_repos
        if r.get("owner", {}).get("login") == "bcgov"
        and (
            r.get("permissions", {}).get("admin")
            or r.get("permissions", {}).get("maintain")
        )
        and not r.get("archived", False)
    ]
    print(f"Found {len(managed_repos)} active managed bcgov repos.\n")

    all_results = {}
    for i, repo in enumerate(managed_repos, 1):
        full_name = repo["full_name"]
        owner, name = full_name.split("/")
        sys.stdout.write(
            f"\r  Scanning [{i}/{len(managed_repos)}] {full_name}...".ljust(80)
        )
        sys.stdout.flush()

        try:
            results = scan_repo(owner, name)
            if results["python"] or results["node"]:
                all_results[full_name] = results
        except requests.exceptions.HTTPError as e:
            sys.stdout.write(f"\r  ⚠️  Error scanning {full_name}: {e}".ljust(80) + "\n")
            continue

    sys.stdout.write("\r" + " " * 80 + "\r")
    sys.stdout.flush()

    # Build flat rows for output
    rows = build_rows(all_results)

    # Print to console
    print_results(rows, all_results)

    # Export to CSV
    csv_filename = f"tech_stacks_{TODAY}.csv"
    export_csv(rows, csv_filename)

    # Also export EOL-only CSV for quick reference
    eol_rows = [r for r in rows if r["eol"] == "⛔ EOL"]
    if eol_rows:
        eol_filename = f"tech_stacks_eol_{TODAY}.csv"
        export_csv(eol_rows, eol_filename)

    # Export to Markdown
    md_filename = f"tech_stacks_{TODAY}.md"
    export_markdown(rows, md_filename)


if __name__ == "__main__":
    main()
