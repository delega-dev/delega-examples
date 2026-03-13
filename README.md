# Delega Integration Examples

Working integration examples for [Delega](https://delega.dev) — task infrastructure for AI agents.

Each example is self-contained and runs against `https://api.delega.dev`.

## Examples

| Directory | Framework | Description |
|-----------|-----------|-------------|
| [`python/`](python/) | Python (requests) | Raw API usage — create tasks, add comments, complete workflows |
| [`node/`](node/) | Node.js / TypeScript | TypeScript API client with full task lifecycle |
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

## License

MIT
