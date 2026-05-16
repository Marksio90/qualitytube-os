from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app, compliance_reports_by_id, compliance_reports_by_idea, script_ai
from app.modules import (
    ApprovalState,
    ComplianceCheckInput,
    ComplianceRecommendation,
    ComplianceReport,
    ReviewerSource,
    RiskLevel,
    compliance_gate_failures,
    run_compliance_checks,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_compliance_state() -> None:
    compliance_reports_by_id.clear()
    compliance_reports_by_idea.clear()


def _create_script(idea_id: str, body: str) -> None:
    response = client.post(
        f"/api/v1/ideas/{idea_id}/scripts/generate-draft",
        json={"angle_id": f"ang-{idea_id}", "angle_status": "approved", "channel_id": "default"},
    )
    assert response.status_code == 200
    script_id = response.json()["script"]["id"]
    patch = client.patch(
        f"/api/v1/scripts/{script_id}",
        json={
            "sections": [
                {"title": "hook", "content": "Hook line with concrete claim and context."},
                {"title": "body", "content": body},
                {"title": "cta", "content": "CTA asks viewers for one actionable experiment."},
            ]
        },
    )
    assert patch.status_code == 200


def test_compliance_schema_validation_required_and_enum_constraints() -> None:
    with pytest.raises(ValidationError):
        ComplianceReport.model_validate(
            {
                "idea_id": "idea-a",
                "reused_content_risk": "severe",
                "repetitive_content_risk": "low",
                "mass_production_risk": "low",
                "synthetic_content_disclosure_required": False,
                "copyright_risk": "low",
                "misleading_claims_risk": "low",
                "sensitive_topic_risk": "low",
                "clickbait_risk": "low",
                "originality_evidence": "source notes",
                "human_contribution_evidence": "human edited",
                "overall_risk": "low",
                "recommendation": "approve",
                "required_fixes": [],
                "reviewer_source": "deterministic",
            }
        )

    with pytest.raises(ValidationError):
        ComplianceReport.model_validate(
            {
                "idea_id": "idea-b",
                "reused_content_risk": "low",
                "repetitive_content_risk": "low",
                "mass_production_risk": "low",
                "synthetic_content_disclosure_required": False,
                "copyright_risk": "low",
                "misleading_claims_risk": "low",
                "sensitive_topic_risk": "low",
                "clickbait_risk": "low",
                "originality_evidence": "source notes",
                "human_contribution_evidence": "human edited",
                "overall_risk": "high",
                "recommendation": "high_risk",
                "required_fixes": [],
                "reviewer_source": "deterministic",
            }
        )


def test_compliance_routes_happy_and_negative() -> None:
    idea_id = "idea-compliance-routes"
    _create_script(idea_id, "Human review applied. Original synthesis used with citations and no risky claims.")

    review = client.post(f"/api/v1/ideas/{idea_id}/compliance/review", json={"channel_id": "default"})
    assert review.status_code == 200
    report = review.json()["report"]
    report_id = report["id"]

    latest = client.get(f"/api/v1/ideas/{idea_id}/compliance/latest")
    assert latest.status_code == 200

    listed = client.get(f"/api/v1/ideas/{idea_id}/compliance/reports")
    assert listed.status_code == 200
    assert len(listed.json()["reports"]) >= 1

    approve = client.post(f"/api/v1/compliance/{report_id}/approve", json={"approver": "qa"})
    assert approve.status_code in (200, 409)

    not_found = "00000000-0000-0000-0000-000000000000"
    missing_latest = client.get("/api/v1/ideas/missing-idea/compliance/latest")
    assert missing_latest.status_code == 404
    assert missing_latest.json()["detail"]["code"] == "COMPLIANCE_REPORT_NOT_FOUND"

    missing_approve = client.post(f"/api/v1/compliance/{not_found}/approve", json={"approver": "qa"})
    assert missing_approve.status_code == 404


def test_publishing_gate_blocking_logic() -> None:
    base = ComplianceReport(
        idea_id="idea-gate",
        reused_content_risk=RiskLevel.low,
        repetitive_content_risk=RiskLevel.low,
        mass_production_risk=RiskLevel.low,
        synthetic_content_disclosure_required=False,
        copyright_risk=RiskLevel.low,
        misleading_claims_risk=RiskLevel.low,
        sensitive_topic_risk=RiskLevel.low,
        clickbait_risk=RiskLevel.low,
        originality_evidence="notes",
        human_contribution_evidence="editor review",
        overall_risk=RiskLevel.low,
        recommendation=ComplianceRecommendation.approve,
        required_fixes=[],
        reviewer_source=ReviewerSource.deterministic,
    )
    assert compliance_gate_failures(report=base, required_fixes_resolved=True) == []

    blocked = base.model_copy(update={"overall_risk": RiskLevel.high})
    failures = compliance_gate_failures(report=blocked, required_fixes_resolved=True)
    assert any(item["rule"] == "overall_risk_not_high" for item in failures)


def test_override_audit_trail_appends_and_persists() -> None:
    idea_id = "idea-override-audit"
    _create_script(idea_id, "template template template guaranteed no risk and secret trick")
    review = client.post(f"/api/v1/ideas/{idea_id}/compliance/review", json={"channel_id": "default"})
    assert review.status_code == 200
    report_id = review.json()["report"]["id"]

    first = client.post(
        f"/api/v1/compliance/{report_id}/override",
        json={
            "reason": "Editorial legal decision for controlled exception one.",
            "approver": "approver-1",
            "outcome_recommendation": "approve_with_fixes",
            "outcome_overall_risk": "medium",
        },
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/compliance/{report_id}/override",
        json={
            "reason": "Editorial legal decision for controlled exception two.",
            "approver": "approver-2",
            "outcome_recommendation": "approve",
            "outcome_overall_risk": "low",
        },
    )
    assert second.status_code == 200
    entries = second.json()["report"]["override_audit_log"]
    assert len(entries) == 2
    assert entries[0]["approver"] == "approver-1"
    assert entries[1]["approver"] == "approver-2"


def test_ai_assisted_review_with_mocked_provider_valid_and_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    idea_id = "idea-ai-review"
    _create_script(idea_id, "Body with human review mention.")

    def valid_json(_: str) -> str:
        return '{"originality_evidence": ["manual notes"], "human_contribution_evidence": ["edited by team"], "required_fixes": ["none"], "reviewer_notes": "ok"}'

    monkeypatch.setattr(script_ai.provider, "generate", valid_json)
    valid = client.post(f"/api/v1/ideas/{idea_id}/compliance/review", json={"channel_id": "default"})
    assert valid.status_code == 200
    assert valid.json()["report"]["reviewer_notes"] == "ok"

    def invalid_json(_: str) -> str:
        return "not-json"

    monkeypatch.setattr(script_ai.provider, "generate", invalid_json)
    invalid = client.post(f"/api/v1/ideas/{idea_id}/compliance/review", json={"channel_id": "default"})
    assert invalid.status_code == 200
    assert invalid.json()["report"]["reviewer_notes"] == "Deterministic checks executed before AI-assisted pass."


def test_deterministic_checker_risk_dimensions_and_block_conditions() -> None:
    result = run_compliance_checks(
        ComplianceCheckInput(
            script_present=False,
            script_text=(
                "You won't believe this secret trick guaranteed no risk template template template "
                "copy and paste violence medical financial advice"
            ),
            synthetic_disclosure_present=False,
            human_contribution_evidence_present=False,
        )
    )

    assert "missing_script" in result.reused_content_signals
    assert "explicit_reuse_language" in result.reused_content_signals
    assert result.repetitive_structure_signals
    assert result.mass_production_indicators
    assert result.clickbait_or_misleading_claim_signals
    assert "violence" in result.sensitive_topic_flags
    assert "medical" in result.sensitive_topic_flags

    base_report = ComplianceReport(
        idea_id="idea-dimensions",
        reused_content_risk=RiskLevel.high,
        repetitive_content_risk=RiskLevel.high,
        mass_production_risk=RiskLevel.high,
        synthetic_content_disclosure_required=True,
        copyright_risk=RiskLevel.low,
        misleading_claims_risk=RiskLevel.high,
        sensitive_topic_risk=RiskLevel.high,
        clickbait_risk=RiskLevel.high,
        originality_evidence="has evidence",
        human_contribution_evidence="has evidence",
        overall_risk=RiskLevel.high,
        recommendation=ComplianceRecommendation.do_not_publish,
        required_fixes=["fix disclosure"],
        reviewer_source=ReviewerSource.deterministic,
    )
    report = base_report.model_copy(update={"originality_evidence": "", "human_contribution_evidence": ""})
    failures = compliance_gate_failures(report=report, required_fixes_resolved=False)
    rules = {item["rule"] for item in failures}
    assert {
        "overall_risk_not_high",
        "recommendation_not_do_not_publish",
        "required_fixes_resolved",
        "synthetic_disclosure_present_when_required",
        "human_contribution_evidence_present",
    }.issubset(rules)
