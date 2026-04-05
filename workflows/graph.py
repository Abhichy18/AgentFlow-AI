from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.sub_agents import (
    execution_agent_node,
    master_supervisor_node,
    notes_agent_node,
    scheduler_agent_node,
    task_agent_node,
)


class AgentState(TypedDict, total=False):
    user_id: int
    goal_text: str
    goal_id: int
    notes_context: list[str]
    task_breakdown: list[dict[str, Any]]
    scheduled_events: list[dict[str, Any]]
    execution_summary: str
    planner_model_used: str
    planner_mode: str
    planner_diagnostics_summary: dict[str, Any]


workflow = StateGraph(AgentState)
workflow.add_node("master", master_supervisor_node)
workflow.add_node("notes", notes_agent_node)
workflow.add_node("task", task_agent_node)
workflow.add_node("scheduler", scheduler_agent_node)
workflow.add_node("execution", execution_agent_node)

workflow.set_entry_point("master")
workflow.add_edge("master", "notes")
workflow.add_edge("notes", "task")
workflow.add_edge("task", "scheduler")
workflow.add_edge("scheduler", "execution")
workflow.add_edge("execution", END)

app_graph = workflow.compile()


def execute_agentflow(goal_text: str, user_id: int) -> dict[str, Any]:
    result = app_graph.invoke(
        {
            "user_id": user_id,
            "goal_text": goal_text,
            "notes_context": [],
            "task_breakdown": [],
            "scheduled_events": [],
            "execution_summary": "",
            "planner_model_used": "unknown",
            "planner_mode": "unknown",
            "planner_diagnostics_summary": {
                "total_attempts": 0,
                "successful_model": "unknown",
            },
        }
    )
    return {
        "goal": goal_text,
        "goal_id": result.get("goal_id"),
        "supporting_notes": result.get("notes_context", []),
        "task_breakdown": result.get("task_breakdown", []),
        "scheduled_events": result.get("scheduled_events", []),
        "execution_summary": result.get("execution_summary", ""),
        "planner_model_used": result.get("planner_model_used", "unknown"),
        "planner_mode": result.get("planner_mode", "unknown"),
        "planner_diagnostics_summary": result.get(
            "planner_diagnostics_summary",
            {"total_attempts": 0, "successful_model": "unknown"},
        ),
    }
