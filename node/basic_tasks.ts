/**
 * Delega API — TypeScript Example
 * Full task lifecycle with native fetch.
 */

const API_BASE = process.env.DELEGA_API_URL ?? "https://api.delega.dev";
const API_KEY = process.env.DELEGA_API_KEY;

if (!API_KEY) {
  console.error("Error: Set DELEGA_API_KEY environment variable");
  console.error('  export DELEGA_API_KEY="dlg_..."');
  process.exit(1);
}

interface Task {
  id: string;
  content: string;
  description: string | null;
  priority: number;
  labels: string;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
}

interface Comment {
  id: string;
  content: string;
  author: string;
  created_at: string;
}

async function api<T = any>(
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<T> {
  const url = `${API_BASE}/v1${path}`;
  const resp = await fetch(url, {
    method,
    headers: {
      "X-Agent-Key": API_KEY!,
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(`${resp.status}: ${JSON.stringify(err)}`);
  }

  return resp.json() as Promise<T>;
}

async function main() {
  // 1. List projects
  console.log("=== Projects ===");
  const projects = await api<any[]>("GET", "/projects");
  for (const p of projects) {
    console.log(`  ${p.name} (${p.id})`);
  }
  console.log();

  // 2. List open tasks
  console.log("=== Open Tasks ===");
  const tasks = await api<Task[]>("GET", "/tasks?completed=false");
  console.log(`Found ${tasks.length} open tasks\n`);

  // 3. Create a task
  console.log("=== Creating Task ===");
  const task = await api<Task>("POST", "/tasks", {
    content: "Audit API response times",
    description:
      "Measure p50/p95/p99 latencies for all endpoints. " +
      "Flag anything over 500ms.",
    priority: 2,
    labels: ["performance", "audit"],
  });
  console.log(`Created: ${task.id} — ${task.content}`);
  console.log(`  Priority: ${task.priority}\n`);

  // 4. Add a comment
  console.log("=== Adding Comment ===");
  const comment = await api<Comment>("POST", `/tasks/${task.id}/comments`, {
    content: "Starting latency audit. Will test from US-East and EU-West.",
  });
  console.log(`Comment ${comment.id} added\n`);

  // 5. Search tasks
  console.log("=== Searching ===");
  const results = await api<Task[]>("GET", "/tasks?search=audit");
  console.log(`Found ${results.length} tasks matching "audit"\n`);

  // 6. Complete the task
  console.log("=== Completing ===");
  const completed = await api<Task>("POST", `/tasks/${task.id}/complete`);
  console.log(`Completed at: ${completed.completed_at}\n`);

  // 7. Final state
  console.log("=== Final State ===");
  const final = await api<Task>("GET", `/tasks/${task.id}`);
  console.log(JSON.stringify(final, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
