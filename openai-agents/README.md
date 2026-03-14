# OpenAI Agents SDK — Planning Agent

A planning agent that breaks down goals into Delega tasks, executes them, and tracks progress — all through OpenAI's Agents SDK with function-calling tools.

## Setup

```bash
pip install -r requirements.txt
export DELEGA_API_KEY="dlg_..."
export DELEGA_API_URL="https://api.delega.dev/v1"   # or http://localhost:18890/api
export OPENAI_API_KEY="sk-..."
```

## Run

```bash
python planning_agent.py
```

## What it does

1. Takes a high-level goal as input
2. Breaks it down into prioritized subtasks in Delega
3. "Executes" each task (simulated) and adds progress comments
4. Completes tasks as they finish
5. Reports a final summary with all task IDs

## Tools

| Tool | Description |
|------|-------------|
| `create_task` | Create a Delega task with priority and labels |
| `list_tasks` | List open tasks, optionally filtered |
| `add_comment` | Log progress on a task |
| `complete_task` | Mark a task done |
| `get_task` | Fetch a single task's full details |
