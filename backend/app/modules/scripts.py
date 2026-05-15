from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

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


class ScriptRepository:
    """In-memory persistence boundary with business rules enforcement."""

    def __init__(self) -> None:
        self._canonical_by_idea: dict[str, Script] = {}
        self._versions_by_script_id: dict[UUID, list[ScriptVersion]] = {}

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


class ScriptDraft(BaseModel):
    idea_id: str
    hook: str
    outline: list[str]
    cta: str
