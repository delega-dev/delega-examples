"""
Delega + OpenAI Agents SDK — Planning Agent

A planning agent that decomposes goals into Delega tasks,
tracks progress with comments, and completes work items.
"""

import os
import sys
import json
import requests
from agents import Agent, Runner, function_tool

# ---------------------------------------------------------------------------
# Delega API client
# ---------------------------------------------------------------------------

API_BASE = os.environ.get("DELEGA_API_URL", "https://api.delega.dev")
API_KEY = os.environ.get("DELEGA_API_KEY")

if not API_KEY:
    print("Error: Set DELEGA_API_KEY environment variable")
    sys.exit(1)

HEADERS = {"X-Agent-Key": API_KEY, "Content-Type": "application/json"}


def delega_api(method: str, path: str, json_body=None):
    url = f"{API_BASE}/v1{path}"
    resp = requests.request(method, url, headers=HEADERS, json=json_body)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Function tools
# ---------------------------------------------------------------------------

@function_tool
def create_task(content: str, description: str = "", priority: int = 2, labels: str = "") -> str:
    """Create a new task in Delega. Labels are comma-separated. Priority: 1=highest, 4=lowest."""
    label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else []
    task = delega_api("POST", "/tasks", {
        "content": content,
        "description": description,
        "priority": priority,
        "labels": label_list,
    })
    return json.dumps({
        "id": task["id"],
        "content": task["content"],
        "priority": task["priority"],
        "labels": task.get("labels", "[]"),
    })


@function_tool
def list_tasks(search: str = "", priority: int = 0, show_completed: bool = False) -> str:
    """List tasks from Delega. Optionally filter by search term or priority."""
    params = []
    if search:
        params.append(f"search={search}")
    if priority:
        params.append(f"priority={priority}")
    if not show_completed:
        params.append("completed=false")
    query = "&".join(params)
    path = f"/tasks?{query}" if query else "/tasks"
    tasks = delega_api("GET", path)
    return json.dumps([{
        "id": t["id"],
        "content": t["content"],
        "priority": t["priority"],
        "completed": t["completed"],
    } for t in tasks[:15]])


@function_tool
def get_task(task_id: str) -> str:
    """Get full details of a specific Delega task by ID."""
    task = delega_api("GET", f"/tasks/{task_id}")
    return json.dumps({
        "id": task["id"],
        "content": task["content"],
        "description": task.get("description"),
        "priority": task["priority"],
        "labels": task.get("labels", "[]"),
        "completed": task["completed"],
        "completed_at": task.get("completed_at"),
    })


@function_tool
def add_comment(task_id: str, content: str) -> str:
    """Add a progress comment to a Delega task."""
    delega_api("POST", f"/tasks/{task_id}/comments", {"content": content})
    return f"Comment added to task {task_id}"


@function_tool
def complete_task(task_id: str) -> str:
    """Mark a Delega task as complete."""
    result = delega_api("POST", f"/tasks/{task_id}/complete")
    return f"Task {task_id} completed at {result.get('completed_at', 'now')}"


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

planner = Agent(
    name="Planner",
    instructions=(
        "You are a planning agent that breaks down goals into actionable tasks. "
        "When given a goal:\n"
        "1. Break it into 3-5 concrete tasks with appropriate priorities\n"
        "2. Create each task in Delega using create_task\n"
        "3. For each task, simulate doing the work and add a comment with your findings\n"
        "4. Complete each task after adding your findings\n"
        "5. Provide a final summary of all tasks created and completed\n\n"
        "Use priority 1 for critical items, 2 for important, 3 for normal, 4 for low. "
        "Add relevant labels to help with organization."
    ),
    tools=[create_task, list_tasks, get_task, add_comment, complete_task],
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else (
        "Plan the launch of a new developer documentation site. "
        "Include content creation, technical setup, review process, and launch checklist."
    )

    print(f"Goal: {goal}\n")
    print("Planning...\n")

    result = Runner.run_sync(planner, goal)
    print(f"\n=== Result ===\n{result.final_output}")
