/**
 * Delega API — TypeScript Worker Loop Example
 * Claim tasks atomically, heartbeat to keep the lease alive while working,
 * release tasks you can't handle, and complete the rest.
 *
 * Run several copies of this script side by side — the claim endpoint is
 * atomic, so each task is only ever handed to one worker at a time.
 */

const API_BASE = (process.env.DELEGA_API_URL ?? "https://api.delega.dev/v1").replace(/\/+$/, "");
const API_KEY = process.env.DELEGA_API_KEY;

if (!API_KEY) {
  console.error("Error: Set DELEGA_API_KEY environment variable");
  console.error('  export DELEGA_API_KEY="dlg_..."');
  process.exit(1);
}

// Lease length requested when claiming/heartbeating (30-3600 seconds).
// Pick something comfortably longer than the gap between heartbeats.
const LEASE_SECONDS = 60;

// Only claim tasks carrying this label — lets this demo seed its own work
// without stealing unrelated tasks from your workspace.
const WORKER_LABEL = "worker-demo";

interface Task {
  id: string;
  content: string;
  description: string | null;
  priority: number;
  labels: string;
  completed: boolean;
  completed_at: string | null;
  created_at: string;
  claimed_by_agent_id: string | null;
  claimed_at: string | null;
  lease_expires_at: string | null;
}

class ApiError extends Error {
  constructor(public status: number, body: unknown) {
    super(`${status}: ${JSON.stringify(body)}`);
  }
}

async function api<T = any>(
  method: string,
  path: string,
  body?: Record<string, unknown>
): Promise<T> {
  const url = `${API_BASE}${path}`;
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
    throw new ApiError(resp.status, err);
  }

  return resp.json() as Promise<T>;
}

function sleep(seconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

/** Create a few demo tasks so the worker loop has something to claim. */
async function seedDemoTasks(): Promise<void> {
  console.log("=== Seeding demo tasks ===");
  const demoTasks = [
    {
      content: "Summarize last week's support tickets",
      priority: 1,
      labels: [WORKER_LABEL, "reporting"],
    },
    {
      content: "Refresh the pricing comparison spreadsheet",
      priority: 2,
      labels: [WORKER_LABEL, "research"],
    },
    {
      // This one is deliberately unhandleable — the worker will release
      // it back to the queue for a more capable worker.
      content: "UNSUPPORTED: transcribe the all-hands recording",
      priority: 3,
      labels: [WORKER_LABEL, "audio"],
    },
  ];
  for (const spec of demoTasks) {
    const task = await api<Task>("POST", "/tasks", spec);
    console.log(`  Created ${task.id}: ${task.content}`);
  }
  console.log();
}

/** Atomically claim the next open task, or return null if the queue is empty. */
async function claimNextTask(): Promise<Task | null> {
  const result = await api<{ task: Task | null }>("POST", "/tasks/claim", {
    labels: [WORKER_LABEL],
    lease_seconds: LEASE_SECONDS,
  });
  return result.task; // a task, or null if nothing is claimable
}

/** Extend our lease on the task. Throws ApiError(409) if the claim was lost. */
async function heartbeat(taskId: string): Promise<Task> {
  return api<Task>("POST", `/tasks/${taskId}/heartbeat`, {
    lease_seconds: LEASE_SECONDS,
  });
}

/**
 * Decide whether this worker knows how to do the task.
 *
 * A real worker would inspect labels or content to route work; here we
 * treat tasks marked UNSUPPORTED as out of scope.
 */
function canHandle(task: Task): boolean {
  return !task.content.startsWith("UNSUPPORTED:");
}

/**
 * Simulate doing the work in chunks, heartbeating between chunks.
 *
 * Long-running work should heartbeat regularly — if the worker crashes
 * and stops heartbeating, the lease expires and another worker can claim
 * the task.
 */
async function processTask(task: Task): Promise<void> {
  const chunks = 3;
  for (let chunk = 1; chunk <= chunks; chunk++) {
    console.log(`    Working on chunk ${chunk}/${chunks}...`);
    await sleep(2); // stand-in for real work

    if (chunk < chunks) {
      // Renew the lease before starting the next chunk. A 409 here means
      // we lost the claim (lease expired or task reassigned) and should
      // stop working on this task.
      await heartbeat(task.id);
      console.log(`    Heartbeat sent — lease extended ${LEASE_SECONDS}s`);
    }
  }
}

/** Claim-work-complete loop. Exits when no usable work remains. */
async function workLoop(): Promise<void> {
  let emptyPolls = 0;
  const maxEmptyPolls = 3;
  const pollInterval = 2; // seconds to sleep when the queue is empty
  const releasedIds = new Set<string>(); // tasks we already passed on

  while (emptyPolls < maxEmptyPolls) {
    const task = await claimNextTask();

    // Treat both an empty queue and "only tasks we already released" as
    // no usable work. In a real fleet, a released task would be picked
    // up by a different worker; in this single-process demo we skip it
    // so the loop can finish.
    if (task === null || releasedIds.has(task.id)) {
      if (task !== null) {
        await api("POST", `/tasks/${task.id}/release`);
      }
      emptyPolls++;
      console.log(
        `No claimable work — sleeping ${pollInterval}s (${emptyPolls}/${maxEmptyPolls})`
      );
      await sleep(pollInterval);
      continue;
    }

    emptyPolls = 0;
    console.log(`=== Claimed ${task.id}: ${task.content} ===`);
    console.log(`  Lease expires at: ${task.lease_expires_at}`);

    if (!canHandle(task)) {
      // Release puts the task back in the queue so another worker (one
      // that can handle it) gets a chance to claim it.
      await api("POST", `/tasks/${task.id}/release`);
      releasedIds.add(task.id);
      console.log("  Can't handle this task — released back to the queue\n");
      continue;
    }

    try {
      await processTask(task);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        // Our claim was lost (lease expired); another worker may have it
        // now, so abandon the task without completing it.
        console.log("  Lost the claim mid-work — abandoning task\n");
        continue;
      }
      throw err;
    }

    const completed = await api<Task>("POST", `/tasks/${task.id}/complete`);
    console.log(`  Completed at: ${completed.completed_at}\n`);
  }

  console.log("No more work — shutting down.");
}

async function main() {
  await seedDemoTasks();
  await workLoop();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
