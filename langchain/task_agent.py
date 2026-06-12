"""
Delega + LangChain — Task Management Agent

Custom tools that let a LangChain v1 agent manage Delega tasks
through natural language.
"""

import os
import sys
import json
import requests
from langchain.agents import create_agent
from langchain.tools import tool
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Delega API client
# ---------------------------------------------------------------------------

API_BASE = os.environ.get("DELEGA_API_URL", "https://api.delega.dev/v1").rstrip("/")
API_KEY = os.environ.get("DELEGA_API_KEY")

if not API_KEY:
    print("Error: Set DELEGA_API_KEY environment variable")
    sys.exit(1)

HEADERS = {"X-Agent-Key": API_KEY, "Content-Type": "application/json"}


def delega_api(method: str, path: str, json_body=None):
    url = f"{API_BASE}{path}"
    resp = requests.request(method, url, headers=HEADERS, json=json_body)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

class CreateTaskArgs(BaseModel):
    content: str = Field(description="Task title")
    description: str = Field(default="", description="Detailed description")
    priority: int = Field(default=2, description="Priority 1 (highest) to 4 (lowest)")
    labels: str = Field(default="", description="Comma-separated labels, e.g. 'bug,urgent'")


class ListTasksArgs(BaseModel):
    search: str = Field(default="", description="Search keyword")
    priority: int = Field(default=0, description="Filter by priority (0=all)")
    completed: str = Field(default="", description="'true', 'false', or '' for all")


class AddCommentArgs(BaseModel):
    task_id: str = Field(description="Task ID")
    content: str = Field(description="Comment text")


class CompleteTaskArgs(BaseModel):
    task_id: str = Field(description="Task ID to mark complete")


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@tool(args_schema=CreateTaskArgs)
def create_task(content: str, description: str = "", priority: int = 2, labels: str = "") -> str:
    """Create a new Delega task and return its ID, content, and priority as JSON."""
    label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else []
    task = delega_api("POST", "/tasks", {
        "content": content,
        "description": description,
        "priority": priority,
        "labels": label_list,
    })
    return json.dumps({"id": task["id"], "content": task["content"], "priority": task["priority"]})


@tool(args_schema=ListTasksArgs)
def list_tasks(search: str = "", priority: int = 0, completed: str = "") -> str:
    """List Delega tasks with optional search, priority, and completion filters."""
    params = []
    if search:
        params.append(f"search={search}")
    if priority:
        params.append(f"priority={priority}")
    if completed:
        params.append(f"completed={completed}")
    query = "&".join(params)
    path = f"/tasks?{query}" if query else "/tasks"
    tasks = delega_api("GET", path)
    summary = [{"id": t["id"], "content": t["content"], "priority": t["priority"],
                "completed": t["completed"]} for t in tasks[:10]]
    return json.dumps({"count": len(tasks), "tasks": summary})


@tool(args_schema=AddCommentArgs)
def add_comment(task_id: str, content: str) -> str:
    """Add a progress note or comment to an existing Delega task."""
    delega_api("POST", f"/tasks/{task_id}/comments", {"content": content})
    return f"Comment added to task {task_id}"


@tool(args_schema=CompleteTaskArgs)
def complete_task(task_id: str) -> str:
    """Mark a Delega task complete."""
    delega_api("POST", f"/tasks/{task_id}/complete")
    return f"Task {task_id} marked complete"


# ---------------------------------------------------------------------------
# Build tools
# ---------------------------------------------------------------------------

tools = [create_task, list_tasks, add_comment, complete_task]

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a task management assistant that uses Delega to track work. "
    "You can create tasks, list them, add comments, and mark them complete. "
    "Always confirm actions with the user and show task IDs."
)

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
)


def final_message_text(result: dict) -> str:
    message = result["messages"][-1]
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Delega Task Agent (LangChain)")
    print("Type a request or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() in ("quit", "exit", "q"):
            break

        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        print(f"\nAgent: {final_message_text(result)}\n")
