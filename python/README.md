# Python — Raw API Examples

Basic Delega API usage with `requests`.

| Script | Description |
|--------|-------------|
| `basic_tasks.py` | Full task lifecycle — create, comment, update, complete |
| `worker_loop.py` | Worker loop — atomically claim tasks, heartbeat to hold the lease, release unhandleable work, complete the rest |

## Setup

```bash
pip install -r requirements.txt
export DELEGA_API_KEY="dlg_..."
export DELEGA_API_URL="https://api.delega.dev/v1"   # or http://localhost:18890/api
```

## Run

```bash
python basic_tasks.py
python worker_loop.py
```

## What `basic_tasks.py` does

1. Lists existing tasks
2. Creates a new task with priority and labels
3. Adds a comment to the task
4. Updates the task description
5. Marks the task as complete
6. Shows the final task state

## What `worker_loop.py` does

1. Seeds three demo tasks (labeled `worker-demo`) so the loop has work
2. Atomically claims the next task via `POST /tasks/claim` with a lease
3. Works in chunks, calling `POST /tasks/{id}/heartbeat` between chunks to keep the lease alive
4. Releases a task it can't handle via `POST /tasks/{id}/release` so another worker can claim it
5. Completes handled tasks and exits when the queue stays empty

Run multiple copies side by side — claiming is atomic, so each task goes to exactly one worker.
