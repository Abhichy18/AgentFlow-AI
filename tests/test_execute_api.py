from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_execute_endpoint_invalid_payload():
    response = client.post(
        "/api/v1/execute",
        json={"user_id": 0, "goal_text": "abc"},
    )
    assert response.status_code == 422


def test_execute_endpoint_success(monkeypatch):
    def fake_execute_agentflow(goal_text: str, user_id: int):
        return {
            "goal": goal_text,
            "goal_id": 1,
            "supporting_notes": ["note a"],
            "task_breakdown": [{"title": "Task 1"}],
            "scheduled_events": [{"task_title": "Task 1", "slot": "mock"}],
            "execution_summary": "ok",
            "planner_model_used": "meta-llama/llama-3.1-8b-instruct:free",
            "planner_mode": "llm",
            "planner_diagnostics_summary": {
                "total_attempts": 1,
                "successful_model": "meta-llama/llama-3.1-8b-instruct:free",
            },
        }

    monkeypatch.setattr("api.main.execute_agentflow", fake_execute_agentflow)

    response = client.post(
        "/api/v1/execute",
        json={"user_id": 1, "goal_text": "Prepare for test"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "success"
    assert body["goal"] == "Prepare for test"
    assert body["planner_mode"] == "llm"
    assert body["planner_diagnostics_summary"]["total_attempts"] == 1
