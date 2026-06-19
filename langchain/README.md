# LangChain — Delega Tool Integration

Custom LangChain tools that let a LangChain v1 agent create, list, comment on, and complete Delega tasks through natural language.

## Setup

```bash
pip install -r requirements.txt
export DELEGA_API_KEY="dlg_..."
export DELEGA_API_URL="https://api.delega.dev/v1"   # optional — this is the default
export OPENAI_API_KEY="sk-..."   # or configure your preferred LLM
```

Requires Python 3.10 or newer.

## Run

```bash
python task_agent.py
```

## What it does

1. Defines four LangChain tools: `create_task`, `list_tasks`, `add_comment`, `complete_task`
2. Creates a LangChain v1 agent with access to all tools
3. Starts an interactive REPL where you ask the agent to manage tasks
4. All task state is persisted in Delega

## Tools

| Tool | Description |
|------|-------------|
| `create_task` | Create a new task with content, description, priority, labels |
| `list_tasks` | List and filter tasks (by priority, label, search, completion) |
| `add_comment` | Add a progress note to a task |
| `complete_task` | Mark a task as done |
