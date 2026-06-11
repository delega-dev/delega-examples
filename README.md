# Delega Integration Examples

Working integration examples for [Delega](https://delega.dev) — task infrastructure for AI agents.

Each example is self-contained and defaults to the hosted API at `https://api.delega.dev/v1`.

## Examples

| Directory | Framework | Description |
|-----------|-----------|-------------|
| [`python/`](python/) | Python 3.10+ (requests) | Raw API usage — task lifecycle (`basic_tasks.py`) and a claim/heartbeat/release worker loop (`worker_loop.py`) |
| [`node/`](node/) | Node.js / TypeScript | TypeScript API client — task lifecycle (`basic_tasks.ts`) and a claim/heartbeat/release worker loop (`worker_loop.ts`) |
| [`webhooks/`](webhooks/) | Node.js / Python / Deno | Raw-body webhook verification examples with HMAC-SHA256 signature checks |
| [`crewai/`](crewai/) | CrewAI | Multi-agent research crew with task delegation |
| [`langchain/`](langchain/) | LangChain | Custom Delega tools for LangChain agents |
| [`openai-agents/`](openai-agents/) | OpenAI Agents SDK | Planning agent with function-calling tools |

## Quick Start

1. **Get an API key** — sign up at [delega.dev/agent](https://delega.dev/agent) or via API:
   ```bash
   curl -X POST https://api.delega.dev/v1/agent/signup \
     -H "Content-Type: application/json" \
     -d '{"human_email":"you@example.com","agent_name":"my-agent"}'
   ```

2. **Set your key:**
   ```bash
   export DELEGA_API_KEY="dlg_..."
   ```

3. **Pick an example and run it** — each directory has its own README with setup instructions.

## API Reference

- **Docs:** https://delega.dev/docs
- **Skill file:** https://delega.dev/skill.md
- **Agent discovery:** https://delega.dev/.well-known/agent.json

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
