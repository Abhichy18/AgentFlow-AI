# AgentFlow AI: OpenRouter-Ready Final Build Blueprint

This document is the practical, implementation-first guide for building AgentFlow AI in VS Code.

It is customized for your setup:
- You are using an OpenRouter API key.
- You want an editor-friendly, step-by-step workflow.
- You want a hackathon-ready system that can be built fast and demonstrated clearly.

---

## 1. Product Vision in One Paragraph

AgentFlow AI converts a high-level user goal into execution-ready output.

Input example:
"I need to prepare for my DBMS exam in 3 days."

System output:
- A structured task list
- Context-aware notes retrieved via RAG
- A time-blocked schedule
- Optional mock execution actions

Core promise:
AgentFlow does not stop at suggestions. It produces a plan you can immediately execute.

---

## 2. Final Architecture (Simple and Hackathon-Safe)

### Layers
1. API Layer (FastAPI)
2. Workflow Layer (LangGraph)
3. Agents Layer (Supervisor + Specialist nodes)
4. Tools Layer (Notes, Tasks, Calendar)
5. Data Layer (SQLite + FAISS)

### Agent Sequence
1. Master Agent: validates and routes goal
2. Notes Agent: pulls relevant context from FAISS
3. Task Agent: creates sequenced tasks in SQLite
4. Scheduler Agent: allocates time slots using calendar tool
5. Execution Agent: returns final actionable response

---

## 3. OpenRouter Customization (Important)

You are not using OpenAI direct APIs. Configure OpenRouter as the LLM provider.

### Required Environment Variables
Create a .env file at the project root with:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
APP_ENV=dev
DATABASE_URL=sqlite:///./agentflow.db
```

### Recommended Free Models on OpenRouter
Use one of these in OPENROUTER_MODEL:
- meta-llama/llama-3.1-8b-instruct:free
- mistralai/mistral-7b-instruct:free
- google/gemma-2-9b-it:free

Notes:
- Free model availability can change.
- Keep model name in env so you can switch without code edits.

### LangChain Setup Pattern
Use ChatOpenAI with custom base URL and API key:

```python
from langchain_openai import ChatOpenAI
from core.config import settings

llm = ChatOpenAI(
    model=settings.openrouter_model,
    api_key=settings.openrouter_api_key,
    base_url=settings.openrouter_base_url,
    temperature=0.2,
)
```

---

## 4. Project Structure (Code Editor Friendly)

Create this exact structure:

```text
AgentFlow/
├── api/
│   ├── __init__.py
│   └── main.py
├── agents/
│   ├── __init__.py
│   └── sub_agents.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── llm.py
├── memory/
│   ├── __init__.py
│   ├── sqlite_db.py
│   ├── faiss_store.py
│   └── init_db.py
├── tools/
│   ├── __init__.py
│   ├── mcp_calendar.py
│   ├── mcp_tasks.py
│   └── mcp_notes.py
├── workflows/
│   ├── __init__.py
│   └── graph.py
├── tests/
│   ├── __init__.py
│   └── test_execute_api.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 5. Dependencies

Create requirements.txt:

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy
langchain
langchain-openai
langgraph
faiss-cpu
python-dotenv
httpx
pytest
```

Install:

```bash
pip install -r requirements.txt
```

---

## 6. Build Plan (Phase-by-Phase)

## Phase 1: Core Config and LLM Provider

Goal:
Centralize environment config and OpenRouter model setup.

Implement:
1. core/config.py
2. core/llm.py

Checklist:
- Load .env safely
- Validate API key exists at startup
- Expose one function get_llm() for all agents

Definition of done:
- Running a small script can generate one sample LLM response through OpenRouter.

---

## Phase 2: Data Layer

Goal:
Store goals/tasks and notes context.

Implement in memory/sqlite_db.py:
- User(id, name)
- Goal(id, user_id, text, status)
- Task(id, goal_id, title, description, priority, scheduled_time, is_completed)

Implement in memory/faiss_store.py:
- build_vector_store(seed_notes: list[str])
- search_notes(query: str, k: int = 4) -> list[str]

Implement in memory/init_db.py:
- Create tables
- Seed sample users/goals/tasks
- Seed exam/productivity notes into FAISS

Definition of done:
- SQLite file generated
- FAISS index generated
- Query returns relevant notes

---

## Phase 3: MCP-style Tool Layer

Goal:
Expose deterministic tool wrappers for agents.

Implement tools/mcp_notes.py:
- find_relevant_notes(goal_text: str) -> list[str]

Implement tools/mcp_tasks.py:
- create_tasks(goal_id: int, tasks: list[dict]) -> list[dict]
- get_tasks_by_goal(goal_id: int) -> list[dict]

Implement tools/mcp_calendar.py:
- find_free_slots(duration_min: int, day: str) -> list[str]
- book_slot(task_title: str, slot: str) -> dict

Definition of done:
- Each tool can be called independently from a quick test script.

---

## Phase 4: Agents and Prompts

Goal:
Define specialist responsibilities with strict output formats.

Implement agents/sub_agents.py:
- master_supervisor_node(state)
- notes_agent_node(state)
- task_agent_node(state)
- scheduler_agent_node(state)
- execution_agent_node(state)

Prompt discipline:
- Use short, deterministic prompts
- Ask for JSON output only where parsing is required
- Avoid free-form paragraphs in planner/scheduler outputs

Definition of done:
- Nodes return expected keys with no missing fields.

---

## Phase 5: Workflow Graph

Goal:
Wire all nodes in an ordered LangGraph pipeline.

Implement workflows/graph.py:
- Define AgentState TypedDict
- Add nodes and directed edges
- Compile and expose execute_agentflow(goal_text, user_id)

Suggested flow:
master -> notes -> task -> scheduler -> execution -> END

Definition of done:
- One invoke call returns final plan + schedule + metadata.

---

## Phase 6: API Layer

Goal:
Expose the full system through a single endpoint.

Implement api/main.py:
- POST /api/v1/execute
- Request model: user_id, goal_text
- Response: status, goal, tasks, schedule, supporting_notes

Add health route:
- GET /health returns provider status and DB connectivity status

Definition of done:
- Endpoint works from FastAPI docs and terminal cURL/PowerShell.

---

## 7. Starter Code (OpenRouter-Aware)

### core/config.py
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    database_url: str = "sqlite:///./agentflow.db"
    app_env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
```

### core/llm.py
```python
from langchain_openai import ChatOpenAI
from core.config import settings


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )
```

### api/main.py
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from workflows.graph import execute_agentflow


app = FastAPI(title="AgentFlow AI", version="1.0.0")


class GoalRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    goal_text: str = Field(..., min_length=5, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/execute")
def execute_goal(req: GoalRequest):
    try:
        result = execute_agentflow(goal_text=req.goal_text, user_id=req.user_id)
        return {"status": "success", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
```

---

## 8. State Contract for LangGraph

Use a single shared state object:

```python
from typing import TypedDict, List, Dict


class AgentState(TypedDict):
    user_id: int
    goal_text: str
    notes_context: List[str]
    task_breakdown: List[Dict]
    scheduled_events: List[Dict]
    execution_summary: str
```

This avoids key mismatch bugs between nodes.

---

## 9. Local Run Instructions (Windows + VS Code)

### Step 1: Create and activate venv
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 2: Install deps
```powershell
pip install -r requirements.txt
```

### Step 3: Add .env values
Make sure OPENROUTER_API_KEY is valid.

### Step 4: Seed local data
```powershell
python -m memory.init_db
```

### Step 5: Run API
```powershell
uvicorn api.main:app --reload --port 8000
```

### Step 6: Test endpoint
```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/v1/execute" -ContentType "application/json" -Body '{"user_id":1,"goal_text":"Prepare for DBMS exam in 3 days"}'
```

---

## 10. Prompt Templates for Consistent Agent Outputs

Use these prompt design rules:
- Master agent: classify and route only
- Notes agent: return bullet context only
- Task agent: return strict JSON array
- Scheduler agent: return strict JSON with start/end times
- Execution agent: return concise final summary

Task Agent JSON contract:

```json
[
  {
    "title": "Revise SQL Joins",
    "description": "Practice INNER, LEFT, RIGHT joins",
    "priority": "high",
    "estimated_minutes": 60
  }
]
```

---

## 11. Common Failure Points and Fixes

1. Error: Authentication failed
- Check OPENROUTER_API_KEY in .env
- Restart terminal after editing .env

2. Error: Model not found
- Change OPENROUTER_MODEL to another free model

3. Error: Empty notes context
- Rebuild FAISS index in init_db.py
- Verify seed notes list is not empty

4. Error: SQLite locked
- Ensure only one writer session is open
- Close background scripts before retry

5. Error: JSON parse failure from agent
- Tighten prompt with JSON-only instruction
- Add schema validation before DB insert

---

## 12. Minimal Testing Plan

Add tests:
- test_health_endpoint
- test_execute_endpoint_success
- test_execute_endpoint_invalid_payload
- test_task_tool_insert_and_fetch
- test_notes_tool_retrieval_non_empty

Run:

```bash
pytest -q
```

---

## 13. Demo Script for Hackathon (3 Minutes)

1. Show problem:
"Normal task apps need manual planning."

2. Send one real user goal to API:
"I need to complete React hooks + mini project by tomorrow."

3. Show logs by stage:
- supervisor routed request
- notes retrieved context
- tasks generated
- schedule allocated

4. Show final response:
- tasks + slots + summary

5. Closing line:
"AgentFlow converts intent into execution-ready structure in one run."

---

## 14. Production Upgrade Path (After Hackathon)

1. Replace mock calendar with Google Calendar API
2. Add Redis for task queue and retries
3. Add auth (JWT + user sessions)
4. Add Postgres migration from SQLite
5. Add frontend dashboard (Next.js)

---

## 15. Build Order Summary (Copy This First)

1. Create folder structure
2. Add requirements and install
3. Add .env with OpenRouter values
4. Build config + LLM modules
5. Build SQLite + FAISS layer
6. Build tools
7. Build agents
8. Build LangGraph workflow
9. Build FastAPI endpoint
10. Test full goal-to-execution flow

If you follow this exact order, implementation will be smooth in VS Code and easy to debug stage by stage.
