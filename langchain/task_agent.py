"""
Delega + LangChain — Task Management Agent

Custom tools that let a LangChain ReAct agent manage Delega tasks
through natural language.
"""

import os
import sys
import json
import requests
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

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

def create_task(content: str, description: str = "", priority: int = 2, labels: str = "") -> str:
    label_list = [l.strip() for l in labels.split(",") if l.strip()] if labels else []
    task = delega_api("POST", "/tasks", {
        "content": content,
        "description": description,
        "priority": priority,
        "labels": label_list,
    })
    return json.dumps({"id": task["id"], "content": task["content"], "priority": task["priority"]})


def list_tasks(search: str = "", priority: int = 0, completed: str = "") -> str:
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


def add_comment(task_id: str, content: str) -> str:
    comment = delega_api("POST", f"/tasks/{task_id}/comments", {"content": content})
    return f"Comment added to task {task_id}"


def complete_task(task_id: str) -> str:
    delega_api("POST", f"/tasks/{task_id}/complete")
    return f"Task {task_id} marked complete"


# ---------------------------------------------------------------------------
# Build tools
# ---------------------------------------------------------------------------

tools = [
    StructuredTool.from_function(
        func=create_task,
        name="create_task",
        description="Create a new Delega task. Returns the task ID.",
        args_schema=CreateTaskArgs,
    ),
    StructuredTool.from_function(
        func=list_tasks,
        name="list_tasks",
        description="List Delega tasks with optional filters (search, priority, completed).",
        args_schema=ListTasksArgs,
    ),
    StructuredTool.from_function(
        func=add_comment,
        name="add_comment",
        description="Add a comment/note to an existing Delega task.",
        args_schema=AddCommentArgs,
    ),
    StructuredTool.from_function(
        func=complete_task,
        name="complete_task",
        description="Mark a Delega task as complete.",
        args_schema=CompleteTaskArgs,
    ),
]

# ---------------------------------------------------------------------------
# Agent setup
# ---------------------------------------------------------------------------

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a task management assistant that uses Delega to track work. "
     "You can create tasks, list them, add comments, and mark them complete. "
     "Always confirm actions with the user and show task IDs.\n\n"
     "Tools available:\n{tools}\n\nTool names: {tool_names}\n\n"
     "Use this format:\n"
     "Thought: what to do next\n"
     "Action: tool_name\n"
     "Action Input: {{\"arg\": \"value\"}}\n"
     "Observation: tool result\n"
     "... repeat ...\n"
     "Thought: I have the answer\n"
     "Final Answer: response to the user\n"),
    ("human", "{input}\n\n{agent_scratchpad}"),
])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
agent = create_react_agent(llm, tools, PROMPT)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

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

        result = executor.invoke({"input": user_input})
        print(f"\nAgent: {result['output']}\n")
