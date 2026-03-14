# Delega Webhook Verification

These examples show how to receive and verify Delega webhook deliveries without changing the signed payload.

## Files

- `verify-node.js` - Express server using Node's `crypto` module
- `verify-python.py` - Flask server using `hmac.compare_digest()`
- `verify-deno.ts` - `Deno.serve()` example using the Web Crypto API

## Signing Algorithm

Every signed delivery includes:

- `X-Delega-Timestamp`
- `X-Delega-Signature`

To verify a delivery:

1. Read the raw request body exactly as received.
2. Build `{timestamp}.{raw_body}` using the `X-Delega-Timestamp` header value.
3. Compute `HMAC-SHA256` with your webhook secret.
4. Prefix the hex digest with `sha256=`.
5. Reject the request if the signature does not match or the timestamp is older than 5 minutes.

## Run

### Node.js

```bash
npm install express
export WEBHOOK_SECRET="whsec_..."
node verify-node.js
```

### Python

```bash
pip install flask
export WEBHOOK_SECRET="whsec_..."
python verify-python.py
```

### Deno

```bash
export WEBHOOK_SECRET="whsec_..."
deno run --allow-env --allow-net verify-deno.ts
```

All three examples listen on `http://localhost:3000/webhooks/delega`.

## Common Pitfalls

- Verify the raw body bytes before parsing JSON. Re-serializing JSON can change whitespace or key order and break the signature.
- Use timing-safe comparison helpers such as `crypto.timingSafeEqual()` or `hmac.compare_digest()`.
- Keep your system clock synchronized. Signature checks use a 5 minute tolerance window for replay protection.
