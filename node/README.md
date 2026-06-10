# Node.js / TypeScript — Raw API Examples

Delega API usage with native `fetch` and typed responses.

| Script | Description |
|--------|-------------|
| `basic_tasks.ts` | Full task lifecycle — create, comment, search, complete |
| `worker_loop.ts` | Worker loop — atomically claim tasks, heartbeat to hold the lease, release unhandleable work, complete the rest |

## Setup

```bash
npm install
export DELEGA_API_KEY="dlg_..."
export DELEGA_API_URL="https://api.delega.dev/v1"   # or http://localhost:18890/api
```

## Run

```bash
npm start
# or: npx tsx basic_tasks.ts
npx tsx worker_loop.ts
```

## What `basic_tasks.ts` does

1. Lists projects and open tasks
2. Creates a task with priority and labels
3. Adds a comment
4. Searches tasks by keyword
5. Completes the task
6. Shows final state

## What `worker_loop.ts` does

1. Seeds three demo tasks (labeled `worker-demo`) so the loop has work
2. Atomically claims the next task via `POST /tasks/claim` with a lease
3. Works in chunks, calling `POST /tasks/{id}/heartbeat` between chunks to keep the lease alive
4. Releases a task it can't handle via `POST /tasks/{id}/release` so another worker can claim it
5. Completes handled tasks and exits when the queue stays empty

Run multiple copies side by side — claiming is atomic, so each task goes to exactly one worker.
