import os
import json
import base64
import httpx

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "reiyi-lai/sample-lead-workflow")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")
API_BASE = "https://api.github.com"

FILES_TO_SYNC = [
    "dashboard/data/events/discovered_events.json",
    "dashboard/data/events/scored_events.json",
    "dashboard/data/state/attendance.json",
    "dashboard/data/state/feedback.json",
]


def _headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def _get_file_sha(path: str) -> str | None:
    url = f"{API_BASE}/repos/{GITHUB_REPO}/contents/{path}?ref={GITHUB_BRANCH}"
    r = httpx.get(url, headers=_headers())
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def sync_file_to_github(local_path: str, commit_message: str = "sync data") -> bool:
    if not GITHUB_TOKEN:
        print("  [GitHub Sync] No GITHUB_TOKEN set, skipping")
        return False

    if not os.path.exists(local_path):
        return False

    with open(local_path, "r") as f:
        content = f.read()

    encoded = base64.b64encode(content.encode()).decode()
    sha = _get_file_sha(local_path)

    body = {
        "message": commit_message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha

    url = f"{API_BASE}/repos/{GITHUB_REPO}/contents/{local_path}"
    r = httpx.put(url, headers=_headers(), json=body)

    if r.status_code in (200, 201):
        print(f"  [GitHub Sync] {local_path} synced")
        return True
    else:
        print(f"  [GitHub Sync] Failed to sync {local_path}: {r.status_code} {r.text[:200]}")
        return False


def sync_all():
    if not GITHUB_TOKEN:
        print("  [GitHub Sync] No GITHUB_TOKEN set, skipping")
        return
    for path in FILES_TO_SYNC:
        sync_file_to_github(path, commit_message=f"auto-sync {os.path.basename(path)}")
