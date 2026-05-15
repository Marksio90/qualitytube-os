import pytest
from pydantic import ValidationError
from uuid import uuid4

from app.main import GateFailed, GateRule, _enforce_approval_gates
from app.modules import HookVariantCreate, RetentionReview, Script, ScriptQualityReport, ScriptRepository, ScriptSection, ScriptState
from app.modules.scripts import HookVariantType


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


def test_update_hook_score_success_and_missing_hook_error() -> None:
    repo = ScriptRepository()
    script = Script(idea_id="idea-hooks", angle_id="angle-hooks", sections=_valid_sections())
    repo.create_script(script)
    created = repo.create_hook_variants(
        script.id,
        [
            HookVariantCreate(
                type=HookVariantType.question,
                text="What if your intro is losing viewers in 3 seconds?",
                promise="Pinpoint the leaky opening beat.",
                curiosity_gap="The drop-off reason is not what most creators assume.",
                risk_level=1,
                score=5.2,
            )
        ],
    )[0]

    updated = repo.update_hook_score(created.id, score=8.4, risk_level=2, notes="Improved opening clarity.")
    assert updated.score == 8.4
    assert updated.risk_level == 2
    assert updated.notes == "Improved opening clarity."
    assert updated.updated_at.tzinfo is not None

    with pytest.raises(KeyError):
        repo.update_hook_score(script.id, score=7.0)


def test_selecting_one_hook_clears_other_selected_flags() -> None:
    repo = ScriptRepository()
    script = Script(idea_id="idea-select", angle_id="angle-select", sections=_valid_sections())
    repo.create_script(script)
    hooks = repo.create_hook_variants(
        script.id,
        [
            HookVariantCreate(
                type=HookVariantType.shock,
                text="Most channels kill retention before the first sentence ends.",
                promise="Reveal the exact mistake lowering watch time.",
                curiosity_gap="It is hidden in one phrase almost everyone uses.",
                risk_level=2,
                score=7.1,
                selected=True,
            ),
            HookVariantCreate(
                type=HookVariantType.story,
                text="I rewrote one opening and doubled average view duration.",
                promise="Show the before/after hook structure.",
                curiosity_gap="The biggest change was counterintuitive.",
                risk_level=1,
                score=7.8,
                selected=False,
            ),
        ],
    )
    first, second = hooks
    assert first.selected is True
    assert second.selected is False

    repo.update_hook_score(second.id, score=8.3, selected=True)
    refreshed_first = repo.get_hook(first.id)
    refreshed_second = repo.get_hook(second.id)
    assert refreshed_first.selected is False
    assert refreshed_second.selected is True


def test_get_latest_retention_review_returns_newest_persisted_review() -> None:
    repo = ScriptRepository()
    script = Script(idea_id="idea-retention", angle_id="angle-retention", sections=_valid_sections())
    repo.create_script(script)

    review_one = RetentionReview(
        weak_intro_warning=True,
        slow_context_warning=False,
        payoff_delay_warning=False,
        repeated_sentence_warning=False,
        generic_section_warning=False,
        unclear_promise_warning=False,
    )
    saved_one = repo.save_retention_review(script.id, review_one)

    review_two = RetentionReview(
        weak_intro_warning=False,
        slow_context_warning=True,
        payoff_delay_warning=True,
        repeated_sentence_warning=False,
        generic_section_warning=False,
        unclear_promise_warning=False,
    )
    saved_two = repo.save_retention_review(script.id, review_two)

    latest = repo.get_latest_retention_review(script.id)
    assert latest is not None
    assert latest.updated_at >= saved_one.updated_at
    assert latest.updated_at == saved_two.updated_at

    assert repo.get_latest_retention_review(script.id) is not None
    assert repo.get_latest_retention_review(uuid4()) is None
