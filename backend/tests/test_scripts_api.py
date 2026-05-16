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


def test_compliance_override_persists_audit_and_exposes_manual_override_state() -> None:
    _gen_draft("idea-compliance-override")
    review = client.post("/api/v1/ideas/idea-compliance-override/compliance/review", json={"channel_id": "default"})
    assert review.status_code == 200
    report = review.json()["report"]
    report_id = report["id"]
    original_recommendation = report["recommendation"]
    original_risk = report["overall_risk"]

    override = client.post(
        f"/api/v1/compliance/{report_id}/override",
        json={
            "reason": "Editorial and legal jointly approved this publication exception.",
            "approver": "policy-admin",
            "outcome_recommendation": "approve_with_fixes",
            "outcome_overall_risk": "medium",
        },
    )
    assert override.status_code == 200
    overridden = override.json()["report"]
    assert overridden["approval_state"] == "overridden"
    assert overridden["is_manually_overridden"] is True
    assert overridden["override_recommendation"] == "approve_with_fixes"
    assert overridden["override_overall_risk"] == "medium"
    assert overridden["recommendation"] == original_recommendation
    assert overridden["overall_risk"] == original_risk
    assert len(overridden["override_audit_log"]) == 1
    audit = overridden["override_audit_log"][0]
    assert audit["approver"] == "policy-admin"
    assert audit["reason"] == "Editorial and legal jointly approved this publication exception."
    assert audit["previous_recommendation"] == original_recommendation
    assert audit["previous_overall_risk"] == original_risk
    assert audit["overridden_recommendation"] == "approve_with_fixes"
    assert audit["overridden_overall_risk"] == "medium"
    assert audit["timestamp"]

    latest = client.get("/api/v1/ideas/idea-compliance-override/compliance/latest")
    assert latest.status_code == 200
    assert latest.json()["report"]["is_manually_overridden"] is True

    listed = client.get("/api/v1/ideas/idea-compliance-override/compliance/reports")
    assert listed.status_code == 200
    assert listed.json()["reports"][-1]["is_manually_overridden"] is True

def test_export_publishing_package_json_and_markdown() -> None:
    from app.main import publishing_repo
    from app.modules import PublishingPackage

    package = PublishingPackage(
        idea_id="idea-export",
        title="Canonical Export Title",
        description="Canonical export description.",
        tags=["alpha", "beta"],
        chapters=["00:00 - Intro", "00:30 - Topic"],
        pinned_comment="Remember to subscribe.",
        thumbnail_brief="Creator close-up with bold text.",
        disclosure_notes="AI-assisted visual polish.",
        source_notes="Sources verified in docs.",
        upload_checklist=["Add end screen", "Verify links"],
    )
    try:
        publishing_repo.create_package(package, editor_event="test-export")
    except ValueError:
        pass

    json_resp = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "json"})
    assert json_resp.status_code == 200
    assert json_resp.json()["format"] == "json"
    assert json_resp.json()["content"]["title"] == "Canonical Export Title"

    md_resp = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "markdown"})
    assert md_resp.status_code == 200
    markdown = md_resp.json()["content"]
    assert markdown.index("## Title") < markdown.index("## Description") < markdown.index("## Tags")
    assert markdown.index("## Chapters") < markdown.index("## Pinned Comment") < markdown.index("## Thumbnail Brief")
    assert markdown.index("## Disclosure Notes") < markdown.index("## Source Notes") < markdown.index("## Checklist") < markdown.index("## Status")


def test_export_publishing_package_rejects_unsupported_format() -> None:
    from app.main import publishing_repo
    from app.modules import PublishingPackage

    package = PublishingPackage(
        idea_id="idea-export-format-error",
        title="Format Error Title",
        description="Desc",
        thumbnail_brief="Thumb brief",
    )
    try:
        publishing_repo.create_package(package, editor_event="test-export-format")
    except ValueError:
        pass

    response = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "xml"})
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_EXPORT_FORMAT"
    assert detail["details"]["received_format"] == "xml"
    assert set(detail["details"]["supported_formats"]) == {"json", "markdown"}
