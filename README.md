# AgentFlow AI

OpenRouter-ready Goal-to-Execution backend built with FastAPI, LangGraph, SQLite, and FAISS.

The current scope is intentionally focused:
- Stable multi-agent coordination
- End-to-end workflow: goal -> tasks -> schedule -> response
- Clean API output for demo presentation

## Quick Start

1. Create a Python virtual environment.
2. Install dependencies from requirements.txt.
3. Copy .env.example to .env and set OPENROUTER_API_KEY.
4. Run database and FAISS seed script.
5. Start FastAPI with uvicorn.

## Commands

- Seed: python -m memory.init_db
- Run: uvicorn api.main:app --reload --port 8000
- Test: pytest -q

## Clean API Response

The execute endpoint returns a concise response payload for demo use:

```json
{
	"status": "success",
	"goal": "Plan DSA revision and mock interview practice for 2 days",
	"goal_id": 12,
	"supporting_notes": ["..."],
	"task_breakdown": [{"id": 1, "title": "..."}],
	"scheduled_events": [{"task_title": "...", "slot": "..."}],
	"execution_summary": "Goal processed successfully with 3 tasks and 3 scheduled events.",
	"planner_model_used": "meta-llama/llama-3.1-8b-instruct:free",
	"planner_mode": "llm",
	"planner_diagnostics_summary": {
		"total_attempts": 1,
		"successful_model": "meta-llama/llama-3.1-8b-instruct:free"
	}
}
```

## Deployment Readiness

1. Environment
- Set OPENROUTER_API_KEY in .env
- Keep fallback models configured in OPENROUTER_FALLBACK_MODELS

2. Run checks before deploy
- pytest -q
- Smoke call to POST /api/v1/execute

3. Production run command
- uvicorn api.main:app --host 0.0.0.0 --port 8000

4. Minimal deployment targets
- Render Web Service
- Railway
- Any VPS with Python 3.11+

## Demo Readiness Checklist

1. Start API server and verify /health.
2. Send one goal to /api/v1/execute.
3. Show task_breakdown and scheduled_events.
4. Show planner_diagnostics_summary to prove reliability.
5. Keep one backup goal prompt ready in case network is unstable.
