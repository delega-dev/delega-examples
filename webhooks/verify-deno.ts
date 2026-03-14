const secret = Deno.env.get("WEBHOOK_SECRET");

if (!secret) {
  throw new Error("WEBHOOK_SECRET is required");
}

const encoder = new TextEncoder();
const toleranceMs = 5 * 60 * 1000;

async function signPayload(secret: string, timestamp: string, payload: string) {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    encoder.encode(`${timestamp}.${payload}`),
  );
  const hex = Array.from(new Uint8Array(signature))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
  return `sha256=${hex}`;
}

function timingSafeEqual(left: string, right: string) {
  const leftBytes = encoder.encode(left);
  const rightBytes = encoder.encode(right);
  if (leftBytes.length !== rightBytes.length) {
    return false;
  }
  let diff = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    diff |= leftBytes[index] ^ rightBytes[index];
  }
  return diff === 0;
}

Deno.serve({ port: 3000 }, async (request) => {
  const url = new URL(request.url);
  if (request.method !== "POST" || url.pathname !== "/webhooks/delega") {
    return new Response("Not found", { status: 404 });
  }

  const signature = request.headers.get("x-delega-signature");
  const timestamp = request.headers.get("x-delega-timestamp");
  const payload = await request.text();

  if (!signature?.startsWith("sha256=") || !timestamp) {
    return new Response("Missing signature headers", { status: 400 });
  }

  const tsMillis = Date.parse(timestamp);
  if (Number.isNaN(tsMillis) || Math.abs(Date.now() - tsMillis) > toleranceMs) {
    return new Response("Stale timestamp", { status: 400 });
  }

  const expected = await signPayload(secret, timestamp, payload);
  if (!timingSafeEqual(expected, signature)) {
    return new Response("Invalid signature", { status: 400 });
  }

  console.log("verified", request.headers.get("x-delega-event"));
  return new Response(null, { status: 204 });
});
