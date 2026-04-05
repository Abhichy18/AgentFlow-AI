from memory.faiss_store import build_vector_store
from memory.sqlite_db import Goal, Task, User, SessionLocal, init_db


def seed_sqlite() -> None:
    init_db()

    session = SessionLocal()
    try:
        if session.query(User).count() > 0:
            return

        user = User(name="Hackathon User")
        session.add(user)
        session.flush()

        goal = Goal(user_id=user.id, text="Prepare for DBMS exam in 3 days", status="seeded")
        session.add(goal)
        session.flush()

        session.add_all(
            [
                Task(
                    goal_id=goal.id,
                    title="Revise SQL Joins",
                    description="Practice INNER, LEFT, RIGHT and FULL joins.",
                    priority="high",
                ),
                Task(
                    goal_id=goal.id,
                    title="Solve normalization problems",
                    description="Complete 10 questions on 1NF, 2NF, 3NF and BCNF.",
                    priority="high",
                ),
            ]
        )

        session.commit()
    finally:
        session.close()


def seed_faiss() -> None:
    notes = [
        "Use active recall and spaced repetition for exam preparation.",
        "DBMS study order: SQL basics, joins, normalization, transactions, indexing.",
        "For coding interviews, explain ACID properties with examples.",
        "Block deep work sessions in 60 to 90 minute intervals.",
    ]
    build_vector_store(notes)


def main() -> None:
    seed_sqlite()
    seed_faiss()
    print("Database and FAISS store initialized.")


if __name__ == "__main__":
    main()
