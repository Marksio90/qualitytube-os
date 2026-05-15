from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_generate_requires_approved_angle_unless_flagged() -> None:
    response = client.post(
        "/api/v1/ideas/idea-a/scripts/generate-outline",
        json={"angle_id": "ang-1", "angle_status": "pending"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ANGLE_NOT_APPROVED"


def test_generation_and_approval_gate_flow() -> None:
    create = client.post(
        "/api/v1/ideas/idea-b/scripts/generate-draft",
        json={"angle_id": "ang-2", "angle_status": "approved"},
    )
    assert create.status_code == 200
    script_id = create.json()["script"]["id"]

    approve_without_score = client.post(f"/api/v1/scripts/{script_id}/approve", json={})
    assert approve_without_score.status_code == 409
    assert approve_without_score.json()["detail"]["code"] == "MISSING_SCORE"

    score = client.post(
        f"/api/v1/scripts/{script_id}/score",
        json={
            "quality_report": {
                "hook_score": 8,
                "clarity_score": 8,
                "narrative_tension_score": 8,
                "originality_score": 8,
                "retention_score": 8,
                "evidence_score": 8,
                "human_voice_score": 8,
                "cta_quality_score": 8,
                "overall_script_score": 8,
            }
        },
    )
    assert score.status_code == 200

    approve = client.post(f"/api/v1/scripts/{script_id}/approve", json={})
    assert approve.status_code == 200
    assert approve.json()["approved"] is True
