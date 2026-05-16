from fastapi.testclient import TestClient

from app.main import app, compliance_reports_by_idea, compliance_reports_by_id, publishing_repo, repo, script_by_id
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


def _seed_approved_script(idea_id: str) -> Script:
    script = Script(
        idea_id=idea_id,
        angle_id=f"ang-{idea_id}",
        sections=[
            ScriptSection(title="hook", content="Hook section content that is long enough for all validators to pass safely."),
            ScriptSection(title="body", content="Body section content with clear supporting claims and concrete details for viewers."),
            ScriptSection(title="cta", content="CTA section content asking viewers to take one concrete, measurable action now."),
        ],
        state=ScriptState.approved,
    )
    repo.create_script(script, editor_event="test-seed-script")
    script_by_id[script.id] = script
    return script


def _seed_compliance(idea_id: str, *, approved: bool = True, overall_risk: RiskLevel = RiskLevel.low) -> ComplianceReport:
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
        overall_risk=overall_risk,
        recommendation=ComplianceRecommendation.approve if overall_risk != RiskLevel.high else ComplianceRecommendation.high_risk,
        required_fixes=[],
        approval_state=ApprovalState.approved if approved else ApprovalState.pending,
    )
    compliance_reports_by_id[report.id] = report
    compliance_reports_by_idea.setdefault(idea_id, []).append(report)
    return report


def _seed_package(idea_id: str, *, disclosure_notes: str = "") -> PublishingPackage:
    package = PublishingPackage(
        idea_id=idea_id,
        title="A strong title for publishing package",
        description="A detailed and useful long-form description for publication.",
        tags=["alpha", "beta"],
        chapters=["00:00 Intro", "00:30 Context"],
        pinned_comment="Remember to subscribe and share your practical result.",
        thumbnail_brief="Creator close-up with concise high-contrast headline.",
        disclosure_notes=disclosure_notes,
        source_notes="Sources reviewed and linked in production docs.",
        upload_checklist=["Verify links", "Add cards"],
    )
    try:
        return publishing_repo.create_package(package, editor_event="test-seed-package")
    except ValueError:
        return publishing_repo.get_package(idea_id)


def test_generate_publishing_package_success_and_schema() -> None:
    idea_id = "idea-pub-generate"
    _seed_approved_script(idea_id)
    _seed_compliance(idea_id, approved=True)

    response = client.post(f"/api/v1/ideas/{idea_id}/publishing-package", json={"angle_status": "approved"})
    assert response.status_code == 200
    body = response.json()

    for key in ["id", "idea_id", "title", "description", "tags", "chapters", "status", "latest_compliance", "created_at", "updated_at"]:
        assert key in body
    assert body["idea_id"] == idea_id
    assert isinstance(body["tags"], list)
    assert isinstance(body["chapters"], list)
    assert body["status"] == "ready_for_review"


def test_validation_failures_per_rule_and_error_payload() -> None:
    idea_id = "idea-pub-validate"
    _seed_approved_script(idea_id)
    _seed_compliance(idea_id, approved=True, overall_risk=RiskLevel.high)
    _seed_package(idea_id, disclosure_notes="")

    response = client.post(f"/api/v1/ideas/{idea_id}/publishing-package/validate", json={"angle_status": "approved"})
    assert response.status_code == 200

    result = response.json()["result"]
    codes = {item["code"] for item in result["errors"]}
    assert "DISCLOSURE_REQUIRED" in codes
    assert "HIGH_RISK_COMPLIANCE_REQUIRES_OVERRIDE" in codes
    assert result["eligible_for_approval"] is False


def test_approval_gate_blocks_on_high_risk_compliance() -> None:
    idea_id = "idea-pub-approval-gate"
    _seed_approved_script(idea_id)
    _seed_compliance(idea_id, approved=True, overall_risk=RiskLevel.high)
    _seed_package(idea_id, disclosure_notes="")

    response = client.post(f"/api/v1/ideas/{idea_id}/publishing-package/approve", json={"angle_status": "approved"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "PUBLISHING_APPROVAL_BLOCKED"
    assert isinstance(detail["details"]["errors"], list)


def test_export_markdown_and_json_correctness() -> None:
    package = _seed_package("idea-pub-export", disclosure_notes="AI visuals were used for b-roll polish.")

    json_response = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "json"})
    assert json_response.status_code == 200
    assert json_response.json()["format"] == "json"
    assert json_response.json()["content"]["title"] == package.title

    md_response = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "markdown"})
    assert md_response.status_code == 200
    markdown = md_response.json()["content"]
    assert "## Title" in markdown
    assert "## Description" in markdown
    assert "## Tags" in markdown
    assert "## Checklist" in markdown


def test_endpoint_status_codes_and_error_payloads() -> None:
    # Missing package returns structured 404 payload.
    missing = client.get("/api/v1/ideas/idea-does-not-exist/publishing-package")
    assert missing.status_code == 404
    assert missing.json()["detail"]["code"] == "PUBLISHING_PACKAGE_NOT_FOUND"

    # Unsupported export returns 422 + structured details.
    package = _seed_package("idea-export-unsupported")
    unsupported = client.post(f"/api/v1/publishing-packages/{package.id}/export", json={"format": "yaml"})
    assert unsupported.status_code == 422
    detail = unsupported.json()["detail"]
    assert detail["code"] == "UNSUPPORTED_EXPORT_FORMAT"
    assert detail["details"]["received_format"] == "yaml"
