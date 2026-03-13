# Python — Raw API Example

Basic Delega API usage with `requests`. Creates tasks, adds comments, lists and completes them.

## Setup

```bash
pip install -r requirements.txt
export DELEGA_API_KEY="dlg_..."
```

## Run

```bash
python basic_tasks.py
```

## What it does

1. Lists existing tasks
2. Creates a new task with priority and labels
3. Adds a comment to the task
4. Updates the task description
5. Marks the task as complete
6. Shows the final task state
