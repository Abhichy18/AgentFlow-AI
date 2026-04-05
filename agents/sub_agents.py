from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from core.llm import ModelFailoverError, invoke_with_failover
from tools.mcp_calendar import book_slot, find_free_slots
from tools.mcp_notes import find_relevant_notes
from tools.mcp_tasks import create_goal, create_tasks, update_task_scheduled_time


class PlannedTask(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(default="", max_length=500)
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    estimated_minutes: int = Field(default=60, ge=15, le=240)


def master_supervisor_node(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("notes_context", [])
    state.setdefault("task_breakdown", [])
    state.setdefault("scheduled_events", [])
    state.setdefault("execution_summary", "")
    state.setdefault("planner_model_used", "unknown")
    state.setdefault("planner_mode", "unknown")
    state.setdefault(
        "planner_diagnostics_summary",
        {"total_attempts": 0, "successful_model": "unknown"},
    )

    goal_text = state.get("goal_text", "").strip()
    if not goal_text:
        raise ValueError("goal_text is required")

    state["goal_text"] = goal_text
    return state


def notes_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    state["notes_context"] = find_relevant_notes(state["goal_text"])
    return state


def _fallback_tasks(goal_text: str, notes: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "title": "Understand the scope",
            "description": f"Break goal into measurable outcomes: {goal_text}",
            "priority": "high",
            "estimated_minutes": 45,
        },
        {
            "title": "Focused implementation session",
            "description": "Complete the highest-impact deliverable first using notes context.",
            "priority": "high",
            "estimated_minutes": 60,
        },
        {
            "title": "Review and revision",
            "description": f"Revise with key notes: {notes[0] if notes else 'No notes'}",
            "priority": "medium",
            "estimated_minutes": 30,
        },
    ]


def _extract_json_array(raw: str) -> str:
    content = raw.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if len(lines) >= 3:
            content = "\n".join(lines[1:-1]).strip()

    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON array found in model output")
    return content[start : end + 1]


def _validate_planned_tasks(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    for item in items:
        parsed = PlannedTask.model_validate(item)
        validated.append(parsed.model_dump())
    return validated


def _generate_tasks_with_llm(
    goal_text: str,
    notes: list[str],
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    prompt = (
        "You are a strict planning assistant. Return only valid JSON array with exactly 3 tasks. "
        "Do not include markdown, headings, explanation, or code fences. "
        "Each task object must include: title, description, priority, estimated_minutes. "
        "Allowed priority values: low, medium, high. "
        "Estimated minutes must be between 15 and 240. "
        f"Goal: {goal_text}. Notes: {notes}."
    )
    content, used_model, attempt_log = invoke_with_failover(prompt)
    json_block = _extract_json_array(content)
    parsed = json.loads(json_block)
    if not isinstance(parsed, list):
        raise ValueError("LLM output is not a list")
    return _validate_planned_tasks(parsed), used_model, attempt_log


def task_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    goal_id = create_goal(state["user_id"], state["goal_text"])
    state["goal_id"] = goal_id

    notes = state.get("notes_context", [])
    try:
        planned_tasks, used_model, attempt_log = _generate_tasks_with_llm(
            state["goal_text"],
            notes,
        )
        state["planner_model_used"] = used_model
        state["planner_mode"] = "llm"
        state["planner_diagnostics_summary"] = {
            "total_attempts": len(attempt_log),
            "successful_model": used_model,
        }
    except ModelFailoverError as exc:
        planned_tasks = _fallback_tasks(state["goal_text"], notes)
        state["planner_model_used"] = "fallback_deterministic"
        state["planner_mode"] = "fallback"
        state["planner_diagnostics_summary"] = {
            "total_attempts": len(exc.attempt_log),
            "successful_model": "fallback_deterministic",
        }
    except Exception:
        planned_tasks = _fallback_tasks(state["goal_text"], notes)
        state["planner_model_used"] = "fallback_deterministic"
        state["planner_mode"] = "fallback"
        state["planner_diagnostics_summary"] = {
            "total_attempts": 1,
            "successful_model": "fallback_deterministic",
        }

    planned_tasks = _validate_planned_tasks(planned_tasks)

    persisted = create_tasks(goal_id, planned_tasks)
    state["task_breakdown"] = persisted
    return state


def scheduler_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    tasks = state.get("task_breakdown", [])

    scheduled = []
    reserved_slots: set[str] = set()
    for task in tasks:
        duration = int(task.get("estimated_minutes", 60))
        slots = find_free_slots(duration_min=duration)
        slot = next((s for s in slots if s not in reserved_slots), "unassigned")
        reserved_slots.add(slot)

        event = book_slot(task.get("title", "Untitled Task"), slot)
        event["duration_min"] = duration
        scheduled.append(event)

        task_id = task.get("id")
        if isinstance(task_id, int):
            update_task_scheduled_time(task_id, slot)
            task["scheduled_time"] = slot

    state["scheduled_events"] = scheduled
    return state


def execution_agent_node(state: dict[str, Any]) -> dict[str, Any]:
    state["execution_summary"] = (
        f"Goal processed successfully with {len(state.get('task_breakdown', []))} tasks "
        f"and {len(state.get('scheduled_events', []))} scheduled events."
    )
    return state
