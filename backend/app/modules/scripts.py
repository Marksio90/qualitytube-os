from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MIN_SECTION_LENGTH = 20


class ScriptState(StrEnum):
    draft = "draft"
    approved = "approved"


class ScriptSection(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=MIN_SECTION_LENGTH)

    @field_validator("content")
    @classmethod
    def normalize_content(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < MIN_SECTION_LENGTH:
            raise ValueError("script section content is too short")
        return normalized


class ScriptQualityReport(BaseModel):
    hook_score: float = Field(ge=0.0, le=10.0)
    clarity_score: float = Field(ge=0.0, le=10.0)
    narrative_tension_score: float = Field(ge=0.0, le=10.0)
    originality_score: float = Field(ge=0.0, le=10.0)
    retention_score: float = Field(ge=0.0, le=10.0)
    evidence_score: float = Field(ge=0.0, le=10.0)
    human_voice_score: float = Field(ge=0.0, le=10.0)
    cta_quality_score: float = Field(ge=0.0, le=10.0)
    overall_script_score: float = Field(ge=0.0, le=10.0)


class Script(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    idea_id: str = Field(min_length=1)
    angle_id: str = Field(min_length=1)
    state: ScriptState = ScriptState.draft
    sections: list[ScriptSection] = Field(min_length=1)
    quality_report: ScriptQualityReport | None = None

    @field_validator("idea_id", "angle_id")
    @classmethod
    def non_empty_identifier(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("identifier must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_sections(self) -> "Script":
        missing_sections = {
            "hook": False,
            "body": False,
            "cta": False,
        }
        total_chars = 0

        for section in self.sections:
            total_chars += len(section.content.strip())
            lowered = section.title.lower()
            if lowered in missing_sections:
                missing_sections[lowered] = True

        if total_chars < 120:
            raise ValueError("script is too short for persistence")

        missing = [name for name, present in missing_sections.items() if not present]
        if missing:
            raise ValueError(
                f"script must include required sections: {', '.join(sorted(missing_sections.keys()))}"
            )

        return self


class ScriptVersion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    script_id: UUID
    revision: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    editor_event: str = Field(min_length=1)
    script_snapshot: Script

    @field_validator("editor_event")
    @classmethod
    def non_empty_event(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("editor event must not be empty")
        return normalized


class HookVariantType(StrEnum):
    contradiction = "contradiction"
    shock = "shock"
    question = "question"
    story = "story"
    mistake = "mistake"
    before_after = "before_after"
    hidden_mechanism = "hidden_mechanism"


class HookVariant(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    script_id: UUID
    type: HookVariantType
    text: str = Field(min_length=1, max_length=500)
    promise: str = Field(min_length=1, max_length=400)
    curiosity_gap: str = Field(min_length=1, max_length=400)
    risk_level: int = Field(ge=0, le=5)
    score: float = Field(ge=0.0, le=10.0)
    notes: str = Field(default="", max_length=2000)
    selected: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RetentionSectionMapEntry(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    timestamp_range: str = Field(min_length=1, max_length=120)
    section_name: str = Field(min_length=1, max_length=120)
    script_excerpt: str = Field(min_length=1, max_length=2000)
    purpose: str = Field(min_length=1, max_length=300)
    risk: str = Field(min_length=1, max_length=300)
    recommendation: str = Field(min_length=1, max_length=500)


class RetentionReview(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    weak_intro_warning: bool
    slow_context_warning: bool
    payoff_delay_warning: bool
    repeated_sentence_warning: bool
    generic_section_warning: bool
    unclear_promise_warning: bool
    section_map: list[RetentionSectionMapEntry] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    timestamps: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HookVariantCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    type: HookVariantType
    text: str = Field(min_length=1, max_length=500)
    promise: str = Field(min_length=1, max_length=400)
    curiosity_gap: str = Field(min_length=1, max_length=400)
    risk_level: int = Field(ge=0, le=5)
    score: float = Field(ge=0.0, le=10.0)
    notes: str = Field(default="", max_length=2000)
    selected: bool = False


class ScriptRepository:
    """In-memory persistence boundary with business rules enforcement."""

    def __init__(self) -> None:
        self._canonical_by_idea: dict[str, Script] = {}
        self._versions_by_script_id: dict[UUID, list[ScriptVersion]] = {}
        self._hooks_by_script_id: dict[UUID, list[HookVariant]] = {}
        self._retention_reviews_by_script_id: dict[UUID, list[RetentionReview]] = {}

    def create_script(self, script: Script, editor_event: str = "create") -> Script:
        if script.idea_id in self._canonical_by_idea:
            raise ValueError("only one canonical script is allowed per idea")
        self._canonical_by_idea[script.idea_id] = script
        version = ScriptVersion(
            script_id=script.id,
            revision=1,
            editor_event=editor_event,
            script_snapshot=script,
        )
        self._versions_by_script_id[script.id] = [version]
        return script

    def revise_script(self, idea_id: str, updated_script: Script, editor_event: str) -> ScriptVersion:
        existing = self._canonical_by_idea.get(idea_id)
        if existing is None:
            raise KeyError(f"no script found for idea_id={idea_id}")
        if updated_script.id != existing.id:
            raise ValueError("script id is immutable across revisions")
        if updated_script.idea_id != idea_id:
            raise ValueError("idea linkage is immutable for canonical script")

        self._canonical_by_idea[idea_id] = updated_script
        versions = self._versions_by_script_id[existing.id]
        new_version = ScriptVersion(
            script_id=existing.id,
            revision=len(versions) + 1,
            editor_event=editor_event,
            script_snapshot=updated_script,
        )
        versions.append(new_version)
        return new_version

    def get_script(self, idea_id: str) -> Script | None:
        return self._canonical_by_idea.get(idea_id)

    def get_versions(self, script_id: UUID) -> tuple[ScriptVersion, ...]:
        versions = self._versions_by_script_id.get(script_id, [])
        return tuple(versions)

    def create_hook_variants(
        self, script_id: UUID, variants: list[HookVariantCreate]
    ) -> tuple[HookVariant, ...]:
        existing = self._hooks_by_script_id.get(script_id, [])
        created: list[HookVariant] = []

        for variant in variants:
            payload = variant.model_dump()
            selected = bool(payload.get("selected", False))
            if selected:
                for hook in existing:
                    hook.selected = False
                    hook.updated_at = datetime.now(UTC)
                for hook in created:
                    hook.selected = False
                    hook.updated_at = datetime.now(UTC)

            created.append(HookVariant(script_id=script_id, **payload))

        self._hooks_by_script_id.setdefault(script_id, []).extend(created)
        return tuple(created)

    def list_hooks(self, script_id: UUID) -> tuple[HookVariant, ...]:
        hooks = self._hooks_by_script_id.get(script_id, [])
        return tuple(hooks)

    def get_hook(self, hook_id: UUID) -> HookVariant:
        for hooks in self._hooks_by_script_id.values():
            for hook in hooks:
                if hook.id == hook_id:
                    return hook
        raise KeyError(f"no hook found for hook_id={hook_id}")

    def update_hook_score(
        self,
        hook_id: UUID,
        *,
        score: float | None = None,
        risk_level: int | None = None,
        notes: str | None = None,
        selected: bool | None = None,
    ) -> HookVariant:
        for script_id, hooks in self._hooks_by_script_id.items():
            for hook in hooks:
                if hook.id != hook_id:
                    continue

                if score is not None:
                    hook.score = score
                if risk_level is not None:
                    hook.risk_level = risk_level
                if notes is not None:
                    hook.notes = notes

                now = datetime.now(UTC)
                if selected is True:
                    for script_hook in self._hooks_by_script_id.get(script_id, []):
                        script_hook.selected = script_hook.id == hook_id
                        script_hook.updated_at = now
                elif selected is False:
                    hook.selected = False
                    hook.updated_at = now
                else:
                    hook.updated_at = now

                return hook
        raise KeyError(f"no hook found for hook_id={hook_id}")

    def select_hook(self, hook_id: UUID) -> HookVariant:
        for script_id, hooks in self._hooks_by_script_id.items():
            for hook in hooks:
                if hook.id == hook_id:
                    for script_hook in self._hooks_by_script_id.get(script_id, []):
                        script_hook.selected = script_hook.id == hook_id
                        script_hook.updated_at = datetime.now(UTC)
                    return hook
        raise KeyError(f"no hook found for hook_id={hook_id}")

    def save_retention_review(self, script_id: UUID, review: RetentionReview) -> RetentionReview:
        review_payload = review.model_dump()
        review_payload["updated_at"] = datetime.now(UTC)
        normalized_review = RetentionReview(**review_payload)
        self._retention_reviews_by_script_id.setdefault(script_id, []).append(normalized_review)
        return normalized_review

    def get_latest_retention_review(self, script_id: UUID) -> RetentionReview | None:
        reviews = self._retention_reviews_by_script_id.get(script_id)
        if not reviews:
            return None
        return max(reviews, key=lambda review: review.updated_at)

class ScriptDraft(BaseModel):
    idea_id: str
    hook: str
    outline: list[str]
    cta: str
