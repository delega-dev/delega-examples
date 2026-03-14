# Node.js / TypeScript — Raw API Example

Delega API usage with native `fetch`. Full task lifecycle with typed responses.

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
```

## What it does

1. Lists projects and open tasks
2. Creates a task with priority and labels
3. Adds a comment
4. Searches tasks by keyword
5. Completes the task
6. Shows final state
