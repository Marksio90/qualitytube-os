from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _gen_and_approve_script(idea_id: str) -> str:
    r = client.post(f"/api/v1/ideas/{idea_id}/scripts/generate-draft", json={"angle_id": f"ang-{idea_id}", "angle_status": "approved"})
    assert r.status_code == 200
    script_id = r.json()["script"]["id"]
    approve = client.post(f"/api/v1/scripts/{script_id}/approve", json={"gates": []})
    assert approve.status_code == 200
    return script_id


def test_visual_plan_generate_get_patch_approve_happy_path() -> None:
    script_id = _gen_and_approve_script("idea-vp-happy")
    generated = client.post(f"/api/v1/scripts/{script_id}/visual-plan/generate")
    assert generated.status_code == 200
    plan = generated.json()["plan"]

    fetched = client.get(f"/api/v1/scripts/{script_id}/visual-plan")
    assert fetched.status_code == 200

    patched = client.patch(
        f"/api/v1/visual-plans/{plan['id']}",
        json={"scenes": [{**plan["scenes"][0], "purpose": "Updated purpose"}]},
    )
    assert patched.status_code == 200
    assert patched.json()["plan"]["scenes"][0]["purpose"] == "Updated purpose"

    approved = client.post(f"/api/v1/visual-plans/{plan['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["plan"]["approval_state"] == "approved"


def test_visual_plan_404_and_validation_and_approval_conflict() -> None:
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/scripts/{missing}/visual-plan").status_code == 404
    assert client.patch(f"/api/v1/visual-plans/{missing}", json={"scenes": []}).status_code == 404
    assert client.post(f"/api/v1/visual-plans/{missing}/approve").status_code == 404

    script_id = _gen_and_approve_script("idea-vp-errors")
    generated = client.post(f"/api/v1/scripts/{script_id}/visual-plan/generate")
    plan = generated.json()["plan"]
    bad_scene = {**plan["scenes"][0], "scene_number": 0, "visual_type": "not-valid", "purpose": "", "filler_risk_score": 2}
    invalid = client.patch(f"/api/v1/visual-plans/{plan['id']}", json={"scenes": [bad_scene]})
    assert invalid.status_code == 422

    first = client.post(f"/api/v1/visual-plans/{plan['id']}/approve")
    assert first.status_code == 200
    second = client.post(f"/api/v1/visual-plans/{plan['id']}/approve")
    assert second.status_code == 409
