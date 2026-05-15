from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _gen_draft(idea_id: str = "idea-api", angle_status: str = "approved", allow: bool = False) -> str:
    response = client.post(
        f"/api/v1/ideas/{idea_id}/scripts/generate-draft",
        json={"angle_id": f"ang-{idea_id}", "angle_status": angle_status, "allow_draft_without_approval": allow},
    )
    assert response.status_code == 200
    return response.json()["script"]["id"]


def test_generate_requires_approved_angle_unless_flagged() -> None:
    response = client.post(
        "/api/v1/ideas/idea-a/scripts/generate-outline",
        json={"angle_id": "ang-1", "angle_status": "pending"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ANGLE_NOT_APPROVED"

    allowed = client.post(
        "/api/v1/ideas/idea-a-allow/scripts/generate-draft",
        json={"angle_id": "ang-2", "angle_status": "pending", "allow_draft_without_approval": True},
    )
    assert allowed.status_code == 200


def test_script_studio_endpoints_happy_paths_and_versioning() -> None:
    outline = client.post(
        "/api/v1/ideas/idea-outline/scripts/generate-outline",
        json={"angle_id": "ang-outline", "angle_status": "approved"},
    )
    assert outline.status_code == 200
    assert len(outline.json()["outline"]["beats"]) >= 3

    script_id = _gen_draft("idea-flow")

    get_script = client.get(f"/api/v1/scripts/{script_id}")
    assert get_script.status_code == 200

    listed = client.get("/api/v1/ideas/idea-flow/scripts")
    assert listed.status_code == 200
    assert len(listed.json()["scripts"]) == 1

    patch = client.patch(
        f"/api/v1/scripts/{script_id}",
        json={
            "editor_event": "manual-tweak",
            "sections": [
                {"title": "hook", "content": "Hook updated to remain specific while still meeting minimum section length."},
                {"title": "body", "content": "Body updated with examples, transitions, and supporting evidence for claims."},
                {"title": "cta", "content": "CTA updated to ask viewers for one measurable action they will implement."},
            ],
        },
    )
    assert patch.status_code == 200

    improve = client.post(f"/api/v1/scripts/{script_id}/improve", json={"editor_event": "ai-improve"})
    assert improve.status_code == 200

    score = client.post(
        f"/api/v1/scripts/{script_id}/score",
        json={
            "quality_report": {
                "hook_score": 1,
                "clarity_score": 1,
                "narrative_tension_score": 1,
                "originality_score": 1,
                "retention_score": 1,
                "evidence_score": 1,
                "human_voice_score": 1,
                "cta_quality_score": 1,
                "overall_script_score": 1,
            }
        },
    )
    assert score.status_code == 200

    versions = client.get(f"/api/v1/scripts/{script_id}/versions")
    assert versions.status_code == 200
    assert len(versions.json()["versions"]) >= 4

    compare = client.get(f"/api/v1/scripts/{script_id}/compare", params={"from_revision": 1, "to_revision": 2})
    assert compare.status_code == 200

    override = client.post(f"/api/v1/scripts/{script_id}/override", json={"reason": "Need this for editorial emergency", "approver": "qa-user"})
    assert override.status_code == 200
    assert override.json()["approved"] is True


def test_script_studio_negative_cases() -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    for method, path, body in [
        (client.get, f"/api/v1/scripts/{missing}", None),
        (client.patch, f"/api/v1/scripts/{missing}", {"editor_event": "e"}),
        (client.post, f"/api/v1/scripts/{missing}/score", {"quality_report": {"hook_score": 8, "clarity_score": 8, "narrative_tension_score": 8, "originality_score": 8, "retention_score": 8, "evidence_score": 8, "human_voice_score": 8, "cta_quality_score": 8, "overall_script_score": 8}}),
        (client.post, f"/api/v1/scripts/{missing}/improve", {"editor_event": "ai-improve"}),
        (client.get, f"/api/v1/scripts/{missing}/versions", None),
        (client.get, f"/api/v1/scripts/{missing}/compare?from_revision=1&to_revision=2", None),
        (client.post, f"/api/v1/scripts/{missing}/approve", {}),
        (client.post, f"/api/v1/scripts/{missing}/override", {"reason": "This is a valid reason", "approver": "qa"}),
    ]:
        response = method(path, json=body) if body is not None else method(path)
        assert response.status_code == 404

    script_id = _gen_draft("idea-negative")

    bad_update = client.patch(f"/api/v1/scripts/{script_id}", json={"sections": [{"title": "hook", "content": "too short"}]})
    assert bad_update.status_code == 422

    missing_revision = client.get(f"/api/v1/scripts/{script_id}/compare", params={"from_revision": 1, "to_revision": 999})
    assert missing_revision.status_code == 404
    assert missing_revision.json()["detail"]["code"] == "REVISION_NOT_FOUND"
