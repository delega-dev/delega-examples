"""
Delega API — Python Example
Full task lifecycle: create, comment, update, complete.
"""

import os
import sys
import requests

API_BASE = os.environ.get("DELEGA_API_URL", "https://api.delega.dev/v1").rstrip("/")
API_KEY = os.environ.get("DELEGA_API_KEY")

if not API_KEY:
    print("Error: Set DELEGA_API_KEY environment variable")
    print("  export DELEGA_API_KEY='dlg_...'")
    sys.exit(1)

HEADERS = {
    "X-Agent-Key": API_KEY,
    "Content-Type": "application/json",
}


def api(method: str, path: str, json=None):
    """Make an API request and return the parsed response."""
    url = f"{API_BASE}{path}"
    resp = requests.request(method, url, headers=HEADERS, json=json)
    resp.raise_for_status()
    return resp.json()


def main():
    # 1. List existing tasks
    print("=== Listing tasks ===")
    tasks = api("GET", "/tasks?completed=false")
    print(f"Found {len(tasks)} open tasks\n")

    # 2. Create a task
    print("=== Creating task ===")
    task = api("POST", "/tasks", json={
        "content": "Research competitor pricing models",
        "description": "Survey top 5 competitors and document their pricing tiers, "
                       "free plan limits, and enterprise pricing where available.",
        "priority": 2,
        "labels": ["research", "competitive-intel"],
    })
    task_id = task["id"]
    print(f"Created task {task_id}: {task['content']}")
    print(f"  Priority: {task['priority']}, Labels: {task['labels']}\n")

    # 3. Add a comment
    print("=== Adding comment ===")
    comment = api("POST", f"/tasks/{task_id}/comments", json={
        "content": "Started research — found 3 competitors with public pricing pages.",
    })
    print(f"Comment added (id: {comment['id']})\n")

    # 4. Update the task
    print("=== Updating task ===")
    updated = api("PUT", f"/tasks/{task_id}", json={
        "description": "Survey top 5 competitors. Found 3 with public pricing. "
                       "Still need data on Enterprise Corp and StartupHQ.",
        "labels": ["research", "competitive-intel", "in-progress"],
    })
    print(f"Updated labels: {updated['labels']}\n")

    # 5. Complete the task
    print("=== Completing task ===")
    completed = api("POST", f"/tasks/{task_id}/complete")
    print(f"Task completed at: {completed['completed_at']}\n")

    # 6. Show final state
    print("=== Final task state ===")
    final = api("GET", f"/tasks/{task_id}")
    for key in ["id", "content", "priority", "labels", "completed", "completed_at"]:
        print(f"  {key}: {final.get(key)}")


if __name__ == "__main__":
    main()
