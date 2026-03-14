const crypto = require("crypto");
const express = require("express");

const app = express();
const secret = process.env.WEBHOOK_SECRET;

if (!secret) {
  throw new Error("WEBHOOK_SECRET is required");
}

app.use(express.raw({ type: "application/json" }));

app.post("/webhooks/delega", (req, res) => {
  const signature = req.get("x-delega-signature");
  const timestamp = req.get("x-delega-timestamp");
  const payload = Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0);

  if (!signature?.startsWith("sha256=") || !timestamp) {
    return res.status(400).send("Missing signature headers");
  }

  const tsMillis = Date.parse(timestamp);
  if (Number.isNaN(tsMillis) || Math.abs(Date.now() - tsMillis) > 5 * 60 * 1000) {
    return res.status(400).send("Stale timestamp");
  }

  const expected = `sha256=${crypto
    .createHmac("sha256", secret)
    .update(timestamp)
    .update(".")
    .update(payload)
    .digest("hex")}`;

  const actualBytes = Buffer.from(signature, "utf8");
  const expectedBytes = Buffer.from(expected, "utf8");
  if (
    actualBytes.length !== expectedBytes.length ||
    !crypto.timingSafeEqual(actualBytes, expectedBytes)
  ) {
    return res.status(400).send("Invalid signature");
  }

  const event = JSON.parse(payload.toString("utf8"));
  console.log("verified", req.get("x-delega-event"), event.task?.id);
  return res.status(204).end();
});

app.listen(3000, () => {
  console.log("Listening on http://localhost:3000/webhooks/delega");
});
