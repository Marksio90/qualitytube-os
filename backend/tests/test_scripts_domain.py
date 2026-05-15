import pytest
from pydantic import ValidationError

from app.modules import Script, ScriptQualityReport, ScriptRepository, ScriptSection, ScriptState


def _valid_sections() -> list[ScriptSection]:
    return [
        ScriptSection(title="hook", content="This opening line surprises with a strong promise."),
        ScriptSection(title="body", content="Main argument includes evidence and structured story beats."),
        ScriptSection(title="cta", content="Ask viewers to comment with their biggest challenge today."),
    ]


def _quality_report() -> ScriptQualityReport:
    return ScriptQualityReport(
        hook_score=8.5,
        clarity_score=8.2,
        narrative_tension_score=8.1,
        originality_score=7.9,
        retention_score=8.0,
        evidence_score=8.6,
        human_voice_score=8.4,
        cta_quality_score=7.8,
        overall_script_score=8.2,
    )


def test_script_model_supports_linkage_state_sections_and_quality() -> None:
    script = Script(
        idea_id="idea-1",
        angle_id="angle-2",
        state=ScriptState.draft,
        sections=_valid_sections(),
        quality_report=_quality_report(),
    )

    assert script.idea_id == "idea-1"
    assert script.angle_id == "angle-2"
    assert script.state == ScriptState.draft
    assert script.quality_report is not None
    assert script.quality_report.overall_script_score == 8.2


def test_script_requires_required_sections_and_minimum_length() -> None:
    with pytest.raises(ValidationError):
        Script(
            idea_id="idea-1",
            angle_id="angle-2",
            sections=[ScriptSection(title="hook", content="x" * 30)],
        )


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
    assert len(repo.get_versions(original.id)) == 2
