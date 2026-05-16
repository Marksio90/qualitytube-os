from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .compliance import ApprovalState

MIN_PACE_WPM = 90
MAX_PACE_WPM = 220


class VoiceStyle(StrEnum):
    documentary_calm = "documentary_calm"
    energetic_explainer = "energetic_explainer"
    dark_mystery = "dark_mystery"
    educational_neutral = "educational_neutral"
    business_authority = "business_authority"
    storytelling_warm = "storytelling_warm"


class AudioBrief(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    script_id: UUID

    voice_style: VoiceStyle
    pace_wpm: int = Field(ge=MIN_PACE_WPM, le=MAX_PACE_WPM)
    emotional_tone: str = Field(min_length=1)
    pause_notes: str = Field(min_length=1)
    pronunciation_notes: str = Field(min_length=1)
    emphasis_notes: str = Field(min_length=1)
    synthetic_voice_used: bool = False
    disclosure_required: bool = False
    disclosure_notes: str | None = None
    export_text: str = Field(min_length=1)

    approval_state: ApprovalState = ApprovalState.pending
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "emotional_tone",
        "pause_notes",
        "pronunciation_notes",
        "emphasis_notes",
        "export_text",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("disclosure_notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_disclosure_policy(self) -> "AudioBrief":
        policy_disclosure_applies = self.synthetic_voice_used
        if policy_disclosure_applies and not self.disclosure_required:
            raise ValueError("disclosure_required must be true when synthetic voice policy applies")
        if self.disclosure_required and not self.disclosure_notes:
            raise ValueError("disclosure_notes is required when disclosure_required is true")
        return self


class AudioBriefRepositoryError(Exception):
    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


class AudioBriefRepository:
    """In-memory repository keyed by script_id and audio_brief_id."""

    def __init__(self) -> None:
        self._by_script: dict[UUID, dict[UUID, AudioBrief]] = {}

    def create(self, brief: AudioBrief) -> AudioBrief:
        script_bucket = self._by_script.setdefault(brief.script_id, {})
        if brief.id in script_bucket:
            raise AudioBriefRepositoryError(409, "AUDIO_BRIEF_CONFLICT", "audio brief id already exists for script")
        script_bucket[brief.id] = brief
        return brief

    def get(self, script_id: UUID, audio_brief_id: UUID) -> AudioBrief:
        brief = self._by_script.get(script_id, {}).get(audio_brief_id)
        if brief is None:
            raise AudioBriefRepositoryError(404, "AUDIO_BRIEF_NOT_FOUND", "audio brief not found")
        return brief

    def update(self, script_id: UUID, updated_brief: AudioBrief) -> AudioBrief:
        if updated_brief.script_id != script_id:
            raise AudioBriefRepositoryError(422, "SCRIPT_ID_MISMATCH", "updated brief script_id must match target script")
        existing = self.get(script_id, updated_brief.id)
        if existing.approval_state == ApprovalState.approved:
            raise AudioBriefRepositoryError(409, "AUDIO_BRIEF_IMMUTABLE", "approved audio brief cannot be updated")

        revised = updated_brief.model_copy(update={"created_at": existing.created_at, "updated_at": datetime.now(UTC)})
        self._by_script[script_id][updated_brief.id] = revised
        return revised

    def approve(self, script_id: UUID, audio_brief_id: UUID) -> AudioBrief:
        brief = self.get(script_id, audio_brief_id)
        if brief.approval_state == ApprovalState.approved:
            raise AudioBriefRepositoryError(409, "AUDIO_BRIEF_ALREADY_APPROVED", "audio brief is already approved")

        approved = brief.model_copy(update={"approval_state": ApprovalState.approved, "updated_at": datetime.now(UTC)})
        self._by_script[script_id][audio_brief_id] = approved
        return approved
