"""
Delega API — Python Worker Loop Example
Claim tasks atomically, heartbeat to keep the lease alive while working,
release tasks you can't handle, and complete the rest.

Run several copies of this script side by side — the claim endpoint is
atomic, so each task is only ever handed to one worker at a time.
"""

import os
import sys
import time
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

# Lease length requested when claiming/heartbeating (30-3600 seconds).
# Pick something comfortably longer than the gap between heartbeats.
LEASE_SECONDS = 60

# Only claim tasks carrying this label — lets this demo seed its own work
# without stealing unrelated tasks from your workspace.
WORKER_LABEL = "worker-demo"


def api(method: str, path: str, json=None):
    """Make an API request and return the parsed response."""
    url = f"{API_BASE}{path}"
    resp = requests.request(method, url, headers=HEADERS, json=json)
    resp.raise_for_status()
    return resp.json()


def seed_demo_tasks():
    """Create a few demo tasks so the worker loop has something to claim."""
    print("=== Seeding demo tasks ===")
    demo_tasks = [
        {
            "content": "Summarize last week's support tickets",
            "priority": 1,
            "labels": [WORKER_LABEL, "reporting"],
        },
        {
            "content": "Refresh the pricing comparison spreadsheet",
            "priority": 2,
            "labels": [WORKER_LABEL, "research"],
        },
        {
            # This one is deliberately unhandleable — the worker will
            # release it back to the queue for a more capable worker.
            "content": "UNSUPPORTED: transcribe the all-hands recording",
            "priority": 3,
            "labels": [WORKER_LABEL, "audio"],
        },
    ]
    for spec in demo_tasks:
        task = api("POST", "/tasks", json=spec)
        print(f"  Created {task['id']}: {task['content']}")
    print()


def claim_next_task():
    """Atomically claim the next open task, or return None if the queue is empty."""
    result = api("POST", "/tasks/claim", json={
        "labels": [WORKER_LABEL],
        "lease_seconds": LEASE_SECONDS,
    })
    return result["task"]  # a task dict, or None if nothing is claimable


def heartbeat(task_id: str):
    """Extend our lease on the task. Raises on 409 if the claim was lost."""
    return api("POST", f"/tasks/{task_id}/heartbeat", json={
        "lease_seconds": LEASE_SECONDS,
    })


def can_handle(task) -> bool:
    """Decide whether this worker knows how to do the task.

    A real worker would inspect labels or content to route work; here we
    treat tasks marked UNSUPPORTED as out of scope.
    """
    return not task["content"].startswith("UNSUPPORTED:")


def process_task(task):
    """Simulate doing the work in chunks, heartbeating between chunks.

    Long-running work should heartbeat regularly — if the worker crashes
    and stops heartbeating, the lease expires and another worker can
    claim the task.
    """
    task_id = task["id"]
    chunks = 3
    for chunk in range(1, chunks + 1):
        print(f"    Working on chunk {chunk}/{chunks}...")
        time.sleep(2)  # stand-in for real work

        if chunk < chunks:
            # Renew the lease before starting the next chunk. A 409 here
            # means we lost the claim (lease expired or task reassigned)
            # and should stop working on this task.
            heartbeat(task_id)
            print(f"    Heartbeat sent — lease extended {LEASE_SECONDS}s")


def work_loop():
    """Claim-work-complete loop. Exits when no usable work remains."""
    empty_polls = 0
    max_empty_polls = 3
    poll_interval = 2  # seconds to sleep when the queue is empty
    released_ids = set()  # tasks we already passed on

    while empty_polls < max_empty_polls:
        task = claim_next_task()

        # Treat both an empty queue and "only tasks we already released"
        # as no usable work. In a real fleet, a released task would be
        # picked up by a different worker; in this single-process demo we
        # skip it so the loop can finish.
        if task is None or task["id"] in released_ids:
            if task is not None:
                api("POST", f"/tasks/{task['id']}/release")
            empty_polls += 1
            print(f"No claimable work — sleeping {poll_interval}s "
                  f"({empty_polls}/{max_empty_polls})")
            time.sleep(poll_interval)
            continue

        empty_polls = 0
        print(f"=== Claimed {task['id']}: {task['content']} ===")
        print(f"  Lease expires at: {task['lease_expires_at']}")

        if not can_handle(task):
            # Release puts the task back in the queue so another worker
            # (one that can handle it) gets a chance to claim it.
            api("POST", f"/tasks/{task['id']}/release")
            released_ids.add(task["id"])
            print("  Can't handle this task — released back to the queue\n")
            continue

        try:
            process_task(task)
        except requests.HTTPError as err:
            if err.response is not None and err.response.status_code == 409:
                # Our claim was lost (lease expired); another worker may
                # have it now, so abandon the task without completing it.
                print("  Lost the claim mid-work — abandoning task\n")
                continue
            raise

        completed = api("POST", f"/tasks/{task['id']}/complete")
        print(f"  Completed at: {completed['completed_at']}\n")

    print("No more work — shutting down.")


def main():
    seed_demo_tasks()
    work_loop()


if __name__ == "__main__":
    main()
