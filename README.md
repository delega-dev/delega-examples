# Delega Integration Examples

> **Historical examples:** Delega’s public hosted service retired on July 28, 2026. These examples are preserved as verifiable engineering artifacts. They work only with an existing owner credential or a compatible private deployment. See the [case study](https://ryanmcmillan.com/delega).

Integration examples for Delega — production task coordination for AI agents.

Each example is self-contained and defaults to Ryan McMillan’s owner-only runtime at `https://api.delega.dev/v1`.

## Examples

| Directory | Framework | Description |
|-----------|-----------|-------------|
| [`python/`](python/) | Python 3.10+ (requests) | Raw API usage — task lifecycle (`basic_tasks.py`) and a claim/heartbeat/release worker loop (`worker_loop.py`) |
| [`node/`](node/) | Node.js / TypeScript | TypeScript API client — task lifecycle (`basic_tasks.ts`) and a claim/heartbeat/release worker loop (`worker_loop.ts`) |
| [`webhooks/`](webhooks/) | Node.js / Python / Deno | Raw-body webhook verification examples with HMAC-SHA256 signature checks |
| [`crewai/`](crewai/) | CrewAI | Multi-agent research crew with task delegation |
| [`langchain/`](langchain/) | LangChain | Custom Delega tools for LangChain agents |
| [`openai-agents/`](openai-agents/) | OpenAI Agents SDK | Planning agent with function-calling tools |

## Existing owner credential

1. **Set an existing authorized key:**
   ```bash
   export DELEGA_API_KEY="dlg_..."
   ```

2. **Pick an example and run it** — each directory has its own historical setup instructions.

## API Reference

- **Docs:** https://delega.dev/docs
- **Case study:** https://ryanmcmillan.com/delega
- **Architecture:** https://delega.dev/architecture

## Auth

All API requests use the `X-Agent-Key` header:
```
X-Agent-Key: dlg_your_key_here
```

Examples expect `DELEGA_API_URL` to be the full API base, including the `/v1` prefix (e.g. `https://api.delega.dev/v1`).

## Webhooks

[`webhooks/`](webhooks/) contains verification servers for Node.js, Python, and Deno. Each example validates `X-Delega-Signature` by recomputing `HMAC-SHA256(secret, "{timestamp}.{raw_body}")`, enforcing a 5 minute timestamp window, and using timing-safe comparison.

## License

MIT
