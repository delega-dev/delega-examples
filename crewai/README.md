# CrewAI — Multi-Agent Research Crew

A CrewAI crew that uses Delega for task management. A research agent investigates topics and a writer agent produces summaries, with all work tracked as Delega tasks.

## Setup

```bash
pip install -r requirements.txt
export DELEGA_API_KEY="dlg_..."
export DELEGA_API_URL="https://api.delega.dev/v1"   # or http://localhost:18890/api
export OPENAI_API_KEY="sk-..."   # or configure your preferred LLM
```

## Run

```bash
python research_crew.py
```

## What it does

1. Creates a parent research task in Delega
2. Research agent investigates the topic and logs findings as comments
3. Writer agent creates a summary task delegated from the parent
4. Both agents update task status as they work
5. Final output is tracked in Delega with full delegation chain

## Architecture

```
Research Task (Delega)
├── Comment: "Found 3 key sources..."
├── Comment: "Analysis complete"
└── Delegated: Write Summary (Delega)
    └── Comment: "Summary draft complete"
```
