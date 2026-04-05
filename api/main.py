from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from memory.sqlite_db import init_db
from workflows.graph import execute_agentflow


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AgentFlow AI",
    description="Autonomous Goal-to-Execution API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


class GoalRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    goal_text: str = Field(..., min_length=5, max_length=500)


@app.get("/")
def root() -> RedirectResponse:
    if FRONTEND_DIR.exists():
        return RedirectResponse(url="/frontend/")
    return RedirectResponse(url="/docs")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/execute")
def execute_goal(req: GoalRequest) -> dict:
    try:
        init_db()
        result = execute_agentflow(goal_text=req.goal_text, user_id=req.user_id)
        return {"status": "success", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
