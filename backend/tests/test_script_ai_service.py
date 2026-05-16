import pytest

from app.modules.script_ai import ComplianceReviewPayload, OutlinePayload, ScriptAIService


class BadProvider:
    model = "bad"

    def generate(self, prompt: str) -> str:
        return "not-json"


class MockProvider:
    model = "mock"

    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


def test_strict_json_failure_raises() -> None:
    svc = ScriptAIService(provider=BadProvider())
    with pytest.raises(ValueError, match="invalid JSON"):
        svc.generate_outline(angle="a", channel_memory="m", research_brief="r")


def test_strict_json_schema_mismatch_raises() -> None:
    provider = MockProvider(['{"hook":"x", "beats": ["a", "b", "c"], "cta": "ok", "extra": 1}'])
    svc = ScriptAIService(provider=provider)
    with pytest.raises(ValueError, match="did not match schema"):
        svc.generate_outline(angle="a", channel_memory="m", research_brief="r")


def test_generation_with_mock_provider_and_scoring_and_improvement() -> None:
    provider = MockProvider(
        [
            '{"hook":"Hook line strong", "beats": ["beat one details", "beat two details", "beat three details"], "cta": "comment your take"}',
            '{"sections": [{"title": "hook", "content": "This hook is long enough to pass validation and feel specific."}, {"title": "body", "content": "This body includes concrete details, examples, and pacing for retention."}, {"title": "cta", "content": "Comment your workflow and subscribe for the next breakdown."}]}',
            '{"quality_report": {"hook_score": 8, "clarity_score": 7.5, "narrative_tension_score": 7.2, "originality_score": 7.1, "retention_score": 7.8, "evidence_score": 7.7, "human_voice_score": 8.1, "cta_quality_score": 7.3, "overall_script_score": 7.6}}',
            '{"sections": [{"title": "hook", "content": "Improved hook with urgency and a concrete promised payoff for viewers."}, {"title": "body", "content": "Improved body now contains examples, transitions, and concise narrative beats."}, {"title": "cta", "content": "Ask viewers to test one tactic and report measurable outcomes below."}]}'
        ]
    )
    svc = ScriptAIService(provider=provider)

    outline = svc.generate_outline(angle="approved-angle", channel_memory="mem", research_brief="brief")
    assert isinstance(outline, OutlinePayload)

    draft = svc.generate_draft(angle="approved-angle", channel_memory="mem", research_brief="brief", outline=outline)
    assert len(draft.sections) == 3

    score = svc.score_script(angle="approved-angle", channel_memory="mem", research_brief="brief", sections=draft.sections)
    assert score.quality_report.overall_script_score == 7.6

    improved = svc.improve_script(angle="approved-angle", channel_memory="mem", research_brief="brief", sections=draft.sections)
    assert improved.sections[0].title.lower() == "hook"
    assert all("Approved angle:" in prompt for prompt in provider.prompts)


def test_generate_hooks_strict_schema_acceptance() -> None:
    provider = MockProvider(
        [
            '{"variants":[{"type":"question","text":"Hook?","promise":"Promise","curiosity_gap":"Gap","risk_level":1,"score":8.5,"notes":"n","selected":false}]}'
        ]
    )
    svc = ScriptAIService(provider=provider)
    hooks = svc.generate_hooks(angle="a", channel_memory="mem", sections=[])
    assert hooks.variants[0].type == "question"
    assert "Channel memory:" in provider.prompts[-1]


def test_score_hook_malformed_json_rejected() -> None:
    provider = MockProvider(["{"])
    svc = ScriptAIService(provider=provider)
    with pytest.raises(ValueError, match="invalid JSON"):
        svc.score_hook(angle="a", channel_memory="mem", hook_text="h", script_sections=[])


def test_analyze_retention_unexpected_field_rejected() -> None:
    provider = MockProvider(
        [
            '{"review":{"weak_intro_warning":false,"slow_context_warning":false,"payoff_delay_warning":false,"repeated_sentence_warning":false,"generic_section_warning":false,"unclear_promise_warning":false,"section_map":[],"recommendations":[],"timestamps":[],"unexpected":1}}'
        ]
    )
    svc = ScriptAIService(provider=provider)
    with pytest.raises(ValueError, match="did not match schema"):
        svc.analyze_retention(angle="a", channel_memory="mem", sections=[])


def test_review_compliance_uses_prompt_file_and_strict_schema() -> None:
    provider = MockProvider(
        [
            '{"reused_content_risk":"low","repetitive_content_risk":"medium","mass_production_risk":"low","synthetic_content_disclosure_required":false,"copyright_risk":"low","misleading_claims_risk":"low","sensitive_topic_risk":"low","clickbait_risk":"medium","overall_risk":"low","recommendation":"approve","required_fixes":[],"reviewer_notes":"Looks compliant with minor style risk."}'
        ]
    )
    svc = ScriptAIService(provider=provider)
    result = svc.review_compliance(angle="a", channel_memory="mem", script_text="script body")
    assert isinstance(result, ComplianceReviewPayload)
    assert result.recommendation == "approve"
    assert "Do not include any legal guarantees or disclaimers." in provider.prompts[-1]


def test_review_compliance_rejects_extra_fields() -> None:
    provider = MockProvider(
        [
            '{"reused_content_risk":"low","repetitive_content_risk":"medium","mass_production_risk":"low","synthetic_content_disclosure_required":false,"copyright_risk":"low","misleading_claims_risk":"low","sensitive_topic_risk":"low","clickbait_risk":"medium","overall_risk":"low","recommendation":"approve","required_fixes":[],"reviewer_notes":"ok","legal_guarantee":"none"}'
        ]
    )
    svc = ScriptAIService(provider=provider)
    with pytest.raises(ValueError, match="did not match schema"):
        svc.review_compliance(angle="a", channel_memory="mem", script_text="script body")
