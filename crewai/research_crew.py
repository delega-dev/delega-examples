"""
Delega + CrewAI — Multi-Agent Research Crew

A research agent investigates a topic and a writer agent produces a summary.
All work is tracked as Delega tasks with delegation and comments.
"""

import os
import sys
import requests
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from typing import Type
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


def delega_api(method: str, path: str, json=None):
    url = f"{API_BASE}{path}"
    resp = requests.request(method, url, headers=HEADERS, json=json)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# CrewAI Tools — Delega integration
# ---------------------------------------------------------------------------

class CreateTaskInput(BaseModel):
    content: str = Field(description="Task title/content")
    description: str = Field(default="", description="Detailed description")
    priority: int = Field(default=2, description="Priority 1-4 (1=highest)")
    labels: list[str] = Field(default_factory=list, description="Task labels")


class CreateTaskTool(BaseTool):
    name: str = "create_delega_task"
    description: str = "Create a new task in Delega to track work."
    args_schema: Type[BaseModel] = CreateTaskInput

    def _run(self, content: str, description: str = "", priority: int = 2, labels: list[str] = []) -> str:
        task = delega_api("POST", "/tasks", {
            "content": content,
            "description": description,
            "priority": priority,
            "labels": labels,
        })
        return f"Created task {task['id']}: {content}"


class AddCommentInput(BaseModel):
    task_id: str = Field(description="Delega task ID")
    content: str = Field(description="Comment text")


class AddCommentTool(BaseTool):
    name: str = "add_delega_comment"
    description: str = "Add a progress comment to an existing Delega task."
    args_schema: Type[BaseModel] = AddCommentInput

    def _run(self, task_id: str, content: str) -> str:
        comment = delega_api("POST", f"/tasks/{task_id}/comments", {
            "content": content,
        })
        return f"Comment added to task {task_id}"


class CompleteTaskInput(BaseModel):
    task_id: str = Field(description="Delega task ID to complete")


class CompleteTaskTool(BaseTool):
    name: str = "complete_delega_task"
    description: str = "Mark a Delega task as complete."
    args_schema: Type[BaseModel] = CompleteTaskInput

    def _run(self, task_id: str) -> str:
        delega_api("POST", f"/tasks/{task_id}/complete")
        return f"Task {task_id} completed"


class DelegateTaskInput(BaseModel):
    parent_task_id: str = Field(description="Parent task ID to delegate from")
    content: str = Field(description="Delegated task content")
    description: str = Field(default="", description="Delegated task description")


class DelegateTaskTool(BaseTool):
    name: str = "delegate_delega_task"
    description: str = "Create a subtask delegated from a parent task."
    args_schema: Type[BaseModel] = DelegateTaskInput

    def _run(self, parent_task_id: str, content: str, description: str = "") -> str:
        child = delega_api("POST", f"/tasks/{parent_task_id}/delegate", {
            "content": content,
            "description": description,
        })
        return f"Delegated task {child['id']}: {content}"


# ---------------------------------------------------------------------------
# Crew definition
# ---------------------------------------------------------------------------

delega_tools = [CreateTaskTool(), AddCommentTool(), CompleteTaskTool(), DelegateTaskTool()]

researcher = Agent(
    role="Research Analyst",
    goal="Investigate topics thoroughly and document findings in Delega tasks",
    backstory="You are a meticulous researcher who tracks all work in Delega. "
              "You create tasks for research objectives, log findings as comments, "
              "and delegate writing tasks when analysis is complete.",
    tools=delega_tools,
    verbose=True,
)

writer = Agent(
    role="Technical Writer",
    goal="Produce clear summaries from research findings",
    backstory="You take research findings and produce concise, actionable summaries. "
              "You track your writing progress in Delega with comments.",
    tools=delega_tools,
    verbose=True,
)

# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

research_task = Task(
    description=(
        "Research the current state of AI agent task management tools. "
        "1. Create a Delega task to track this research. "
        "2. Investigate at least 3 tools in the space. "
        "3. Log key findings as comments on the task. "
        "4. When done, delegate a 'Write Summary' task from the research task."
    ),
    expected_output="A Delega task ID with research findings logged as comments, "
                    "and a delegated writing task created.",
    agent=researcher,
)

writing_task = Task(
    description=(
        "Using the research findings from the previous task: "
        "1. Read the research task comments for context. "
        "2. Write a concise 3-paragraph summary. "
        "3. Log the summary as a comment on the delegated writing task. "
        "4. Complete both the writing task and the original research task."
    ),
    expected_output="A completed summary logged in Delega with all tasks marked done.",
    agent=writer,
)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("Starting research crew...\n")
    result = crew.kickoff()
    print(f"\n=== Crew Result ===\n{result}")
