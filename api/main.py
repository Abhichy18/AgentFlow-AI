from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
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


class GoalRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    goal_text: str = Field(..., min_length=5, max_length=500)


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
