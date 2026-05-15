import pytest
from pydantic import ValidationError

from app.main import GateFailed, GateRule, _enforce_approval_gates
from app.modules import Script, ScriptQualityReport, ScriptRepository, ScriptSection, ScriptState


def _valid_sections() -> list[ScriptSection]:
    return [
        ScriptSection(title="hook", content="This opening line surprises with a strong promise and clear viewpoint."),
        ScriptSection(title="body", content="Main argument includes evidence, structured beats, and concrete audience outcomes."),
        ScriptSection(title="cta", content="Ask viewers to comment with their biggest challenge and next experiment."),
    ]


def _quality_report(overall: float = 8.2, hook: float = 8.5) -> ScriptQualityReport:
    return ScriptQualityReport(
        hook_score=hook,
        clarity_score=8.2,
        narrative_tension_score=8.1,
        originality_score=7.9,
        retention_score=8.0,
        evidence_score=8.6,
        human_voice_score=8.4,
        cta_quality_score=7.8,
        overall_script_score=overall,
    )


def test_script_model_supports_linkage_state_sections_and_quality() -> None:
    script = Script(idea_id="idea-1", angle_id="angle-2", state=ScriptState.draft, sections=_valid_sections(), quality_report=_quality_report())
    assert script.quality_report is not None


def test_script_requires_required_sections_and_minimum_length() -> None:
    with pytest.raises(ValidationError):
        Script(idea_id="idea-1", angle_id="angle-2", sections=[ScriptSection(title="hook", content="x" * 30)])


def test_script_repository_enforces_single_canonical_script_and_versions() -> None:
    repo = ScriptRepository()
    original = Script(idea_id="idea-1", angle_id="angle-a", sections=_valid_sections())
    repo.create_script(original)
    with pytest.raises(ValueError):
        repo.create_script(Script(idea_id="idea-1", angle_id="angle-b", sections=_valid_sections()))

    approved = original.model_copy(update={"state": ScriptState.approved})
    version = repo.revise_script("idea-1", approved, editor_event="improve-hook")
    assert version.revision == 2
    assert repo.get_script("idea-1").state == ScriptState.approved
    assert [v.revision for v in repo.get_versions(original.id)] == [1, 2]


def test_approval_gate_thresholds_and_banned_phrase_detection() -> None:
    script = Script(idea_id="idea-gate", angle_id="angle-gate", sections=_valid_sections(), quality_report=_quality_report(overall=6.9, hook=7.5))
    with pytest.raises(GateFailed, match="overall score below"):
        _enforce_approval_gates(script, GateRule(min_overall_score=7.0, min_hook_score=7.0))

    script2 = Script(idea_id="idea-gate2", angle_id="angle-gate", sections=_valid_sections(), quality_report=_quality_report(overall=7.5, hook=6.8))
    with pytest.raises(GateFailed, match="hook score below"):
        _enforce_approval_gates(script2, GateRule(min_overall_score=7.0, min_hook_score=7.0))

    banned_sections = _valid_sections()
    banned_sections[1] = ScriptSection(title="body", content="This claims guaranteed viral growth while promising unrealistic outcomes for everyone.")
    script3 = Script(idea_id="idea-gate3", angle_id="angle-gate", sections=banned_sections, quality_report=_quality_report())
    with pytest.raises(GateFailed) as exc:
        _enforce_approval_gates(script3, GateRule())
    assert exc.value.code == "BANNED_PHRASES"
