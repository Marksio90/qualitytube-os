from fastapi.testclient import TestClient

from app.main import (
    app,
    compliance_reports_by_idea,
    compliance_reports_by_id,
    publishing_repo,
    repo,
    script_by_id,
    title_thumbnail_ai,
    title_thumbnail_repo,
)
from app.modules import (
    ApprovalState,
    ComplianceRecommendation,
    ComplianceReport,
    PublishingPackage,
    RiskLevel,
    Script,
    ScriptSection,
    ScriptState,
)

client = TestClient(app)


def _seed_script_and_compliance(idea_id: str) -> None:
    script = Script(
        idea_id=idea_id,
        angle_id=f"angle-{idea_id}",
        sections=[
            ScriptSection(title="hook", content="Hook section with enough detail and context for robust generation."),
            ScriptSection(title="body", content="Body section contains practical steps and examples aligned with channel tone."),
            ScriptSection(title="cta", content="CTA asks viewer to test one specific tactic and report measurable outcomes."),
        ],
        state=ScriptState.approved,
    )
    repo.create_script(script, editor_event="test-seed")
    script_by_id[script.id] = script
    report = ComplianceReport(
        idea_id=idea_id,
        reused_content_risk=RiskLevel.low,
        repetitive_content_risk=RiskLevel.low,
        mass_production_risk=RiskLevel.low,
        synthetic_content_disclosure_required=False,
        copyright_risk=RiskLevel.low,
        misleading_claims_risk=RiskLevel.low,
        sensitive_topic_risk=RiskLevel.low,
        clickbait_risk=RiskLevel.low,
        overall_risk=RiskLevel.low,
        recommendation=ComplianceRecommendation.approve,
        required_fixes=[],
        approval_state=ApprovalState.approved,
    )
    compliance_reports_by_id[report.id] = report
    compliance_reports_by_idea.setdefault(idea_id, []).append(report)


def _seed_package(idea_id: str) -> None:
    package = PublishingPackage(
        idea_id=idea_id,
        title="Original package title",
        description="A long descriptive body that satisfies validations for integration tests.",
        tags=["x"],
        chapters=["00:00 Intro"],
        pinned_comment="Pinned",
        thumbnail_brief="Original brief",
        disclosure_notes="",
        source_notes="sources",
        upload_checklist=["check"],
    )
    try:
        publishing_repo.create_package(package, editor_event="seed")
    except ValueError:
        pass


def test_title_generation_and_scoring_endpoints() -> None:
    idea_id = "idea-title-lab"
    _seed_script_and_compliance(idea_id)

    generated = client.post(f"/api/v1/ideas/{idea_id}/titles/generate", json={"angle_status": "approved"})
    assert generated.status_code == 200
    titles = generated.json()["titles"]
    assert len(titles) > 0

    title_id = titles[0]["id"]
    scored = client.post(
        f"/api/v1/titles/{title_id}/score",
        json={
            "clarity_score": 8,
            "curiosity_score": 8,
            "truthfulness_score": 9,
            "promise_match_score": 8,
            "clickbait_risk": 2,
            "rationale": "Aligned",
            "warnings": "Low risk",
        },
    )
    assert scored.status_code == 200
    scored_title = scored.json()["title"]
    assert scored_title["overall_title_score"] > 0
    assert scored_title["clickbait_risk"] == 2


def test_thumbnail_generation_and_selection_syncs_with_publishing_package() -> None:
    idea_id = "idea-thumb-lab"
    _seed_script_and_compliance(idea_id)
    _seed_package(idea_id)
    titles = client.post(f"/api/v1/ideas/{idea_id}/titles/generate", json={"angle_status": "approved"}).json()["titles"]

    thumbs_response = client.post(
        f"/api/v1/ideas/{idea_id}/thumbnails/generate-briefs",
        json={"angle_status": "approved", "titles": [titles[0]["title_text"]]},
    )
    assert thumbs_response.status_code == 200
    thumbs = thumbs_response.json()["thumbnails"]
    assert len(thumbs) > 0

    selected = client.post(f"/api/v1/thumbnails/{thumbs[0]['id']}/select")
    assert selected.status_code == 200
    package = publishing_repo.get_package(idea_id)
    assert package is not None
    assert "Mobile readability:" in package.thumbnail_brief


def test_title_and_thumbnail_single_selection_and_package_sync() -> None:
    idea_id = "idea-select-invariant"
    _seed_script_and_compliance(idea_id)
    _seed_package(idea_id)

    generated = client.post(f"/api/v1/ideas/{idea_id}/titles/generate", json={"angle_status": "approved"}).json()["titles"]
    first_id = generated[0]["id"]
    second_id = generated[1]["id"]

    assert client.post(f"/api/v1/titles/{first_id}/select").status_code == 200
    assert client.post(f"/api/v1/titles/{second_id}/select").status_code == 200
    listed = client.get(f"/api/v1/ideas/{idea_id}/titles").json()["titles"]
    assert sum(1 for t in listed if t["selected"]) == 1
    assert next(t for t in listed if t["selected"])["id"] == second_id
    assert publishing_repo.get_package(idea_id).title == next(t for t in listed if t["selected"])["title_text"]


def test_error_paths_missing_approvals_unknown_ids_and_malformed_provider_json() -> None:
    idea_id = "idea-errors"
    script = Script(idea_id=idea_id, angle_id="angle", sections=[ScriptSection(title="hook", content="x" * 30)], state=ScriptState.draft)
    repo.create_script(script, editor_event="test-seed")
    script_by_id[script.id] = script

    missing_approval = client.post(f"/api/v1/ideas/{idea_id}/titles/generate", json={"angle_status": "approved"})
    assert missing_approval.status_code == 409
    assert missing_approval.json()["detail"]["code"] == "SCRIPT_APPROVAL_REQUIRED"

    unknown_title = client.post("/api/v1/titles/00000000-0000-0000-0000-000000000001/select")
    unknown_thumb = client.post("/api/v1/thumbnails/00000000-0000-0000-0000-000000000001/select")
    assert unknown_title.status_code == 404
    assert unknown_thumb.status_code == 404

    original_provider = title_thumbnail_ai.provider

    class BadProvider:
        model = "bad"

        def generate(self, prompt: str) -> str:
            return "{not-json"

    title_thumbnail_ai.provider = BadProvider()
    _seed_script_and_compliance("idea-malformed")
    malformed = client.post("/api/v1/ideas/idea-malformed/titles/generate", json={"angle_status": "approved"})
    assert malformed.status_code == 500
    title_thumbnail_ai.provider = original_provider
