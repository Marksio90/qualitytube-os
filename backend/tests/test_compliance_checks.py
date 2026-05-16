from app.modules import (
    ComplianceCheckInput,
    ComplianceRecommendation,
    ComplianceReport,
    ReviewerSource,
    RiskLevel,
    publishing_blocked,
    run_compliance_checks,
)


def test_run_compliance_checks_returns_structured_signals() -> None:
    result = run_compliance_checks(
        ComplianceCheckInput(
            script_present=True,
            script_text="""
            You won't believe this secret trick. Guaranteed results with no risk.
            template template template template
            violence self-harm
            """,
            synthetic_disclosure_present=False,
            human_contribution_evidence_present=False,
        )
    )

    assert result.clickbait_or_misleading_claim_signals
    assert result.sensitive_topic_flags == ["violence", "self-harm"]
    assert result.synthetic_disclosure_required is True
    assert result.human_contribution_evidence_present is False


def test_publishing_blocked_predicates() -> None:
    report = ComplianceReport(
        idea_id="idea-1",
        reused_content_risk=RiskLevel.low,
        repetitive_content_risk=RiskLevel.low,
        mass_production_risk=RiskLevel.low,
        synthetic_content_disclosure_required=True,
        copyright_risk=RiskLevel.low,
        misleading_claims_risk=RiskLevel.low,
        sensitive_topic_risk=RiskLevel.low,
        clickbait_risk=RiskLevel.low,
        originality_evidence="source notes included",
        human_contribution_evidence="human edited",
        overall_risk=RiskLevel.low,
        recommendation=ComplianceRecommendation.approve,
        required_fixes=[],
        reviewer_source=ReviewerSource.deterministic,
    )
    assert publishing_blocked(report=report, required_fixes_resolved=False) is False

    unresolved_fixes = report.model_copy(update={"required_fixes": ["add disclosure"]})
    assert publishing_blocked(report=unresolved_fixes, required_fixes_resolved=False) is True

    do_not_publish = report.model_copy(update={"recommendation": ComplianceRecommendation.do_not_publish})
    assert publishing_blocked(report=do_not_publish, required_fixes_resolved=True) is True

    no_human_evidence = report.model_copy(update={"human_contribution_evidence": ["   ", ""]})
    assert publishing_blocked(report=no_human_evidence, required_fixes_resolved=True) is True
