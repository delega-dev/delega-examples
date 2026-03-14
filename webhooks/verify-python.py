import hashlib
import hmac
import os
from datetime import datetime, timezone

from flask import Flask, abort, request

app = Flask(__name__)
secret = os.environ.get("WEBHOOK_SECRET")

if not secret:
    raise RuntimeError("WEBHOOK_SECRET is required")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@app.post("/webhooks/delega")
def handle_webhook():
    signature = request.headers.get("X-Delega-Signature")
    timestamp = request.headers.get("X-Delega-Timestamp")
    payload = request.get_data(cache=False)

    if not signature or not signature.startswith("sha256=") or not timestamp:
        abort(400, "Missing signature headers")

    try:
        received_at = parse_timestamp(timestamp)
    except ValueError:
        abort(400, "Invalid timestamp")

    if abs((datetime.now(timezone.utc) - received_at).total_seconds()) > 300:
        abort(400, "Stale timestamp")

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        abort(400, "Invalid signature")

    print("verified", request.headers.get("X-Delega-Event"))
    return ("", 204)


if __name__ == "__main__":
    app.run(port=3000)
