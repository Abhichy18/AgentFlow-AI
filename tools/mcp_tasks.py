from __future__ import annotations

from memory.sqlite_db import Goal, Task, User, SessionLocal


def create_goal(user_id: int, goal_text: str) -> int:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user is None:
            user = User(id=user_id, name=f"User {user_id}")
            session.add(user)
            session.flush()

        goal = Goal(user_id=user_id, text=goal_text, status="planned")
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return goal.id
    finally:
        session.close()


def create_tasks(goal_id: int, tasks: list[dict]) -> list[dict]:
    session = SessionLocal()
    created: list[dict] = []

    try:
        for item in tasks:
            task = Task(
                goal_id=goal_id,
                title=item.get("title", "Untitled Task"),
                description=item.get("description", ""),
                priority=item.get("priority", "medium"),
                scheduled_time=item.get("scheduled_time", ""),
            )
            session.add(task)
            session.flush()
            created.append(
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "estimated_minutes": int(item.get("estimated_minutes", 60)),
                    "scheduled_time": task.scheduled_time,
                }
            )

        session.commit()
        return created
    finally:
        session.close()


def get_tasks_by_goal(goal_id: int) -> list[dict]:
    session = SessionLocal()
    try:
        rows = session.query(Task).filter(Task.goal_id == goal_id).all()
        return [
            {
                "id": row.id,
                "title": row.title,
                "description": row.description,
                "priority": row.priority,
                "scheduled_time": row.scheduled_time,
                "is_completed": row.is_completed,
            }
            for row in rows
        ]
    finally:
        session.close()


def update_task_scheduled_time(task_id: int, scheduled_time: str) -> None:
    session = SessionLocal()
    try:
        row = session.query(Task).filter(Task.id == task_id).first()
        if row is None:
            return

        row.scheduled_time = scheduled_time
        session.commit()
    finally:
        session.close()
