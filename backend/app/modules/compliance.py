from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ComplianceRecommendation(StrEnum):
    approve = "approve"
    approve_with_fixes = "approve_with_fixes"
    high_risk = "high_risk"
    do_not_publish = "do_not_publish"


class ReviewerSource(StrEnum):
    deterministic = "deterministic"
    ai_assisted = "ai_assisted"
    human_override = "human_override"


class ApprovalState(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    overridden = "overridden"


class ComplianceOverrideAuditEntry(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    approver: str = Field(min_length=1)
    reason: str = Field(min_length=12)
    previous_recommendation: ComplianceRecommendation
    previous_overall_risk: RiskLevel
    overridden_recommendation: ComplianceRecommendation
    overridden_overall_risk: RiskLevel


class ComplianceReport(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    idea_id: str = Field(min_length=1)

    reused_content_risk: RiskLevel
    repetitive_content_risk: RiskLevel
    mass_production_risk: RiskLevel
    synthetic_content_disclosure_required: bool
    copyright_risk: RiskLevel
    misleading_claims_risk: RiskLevel
    sensitive_topic_risk: RiskLevel
    clickbait_risk: RiskLevel

    originality_evidence: str | list[str]
    human_contribution_evidence: str | list[str]

    overall_risk: RiskLevel
    recommendation: ComplianceRecommendation
    required_fixes: list[str] = Field(default_factory=list)
    reviewer_notes: str = Field(default="")

    reviewer_source: ReviewerSource
    approval_state: ApprovalState = ApprovalState.pending
    override_reason: str | None = None
    override_actor: str | None = None
    override_recommendation: ComplianceRecommendation | None = None
    override_overall_risk: RiskLevel | None = None
    is_manually_overridden: bool = False
    override_audit_log: list[ComplianceOverrideAuditEntry] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("idea_id", mode="before")
    @classmethod
    def validate_idea_id(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("idea_id must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("idea_id must not be empty")
        return normalized

    @field_validator("originality_evidence", "human_contribution_evidence")
    @classmethod
    def validate_evidence(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                raise ValueError("evidence text must not be empty")
            return normalized

        if isinstance(value, list):
            normalized_items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if not normalized_items:
                raise ValueError("evidence list must contain at least one non-empty text item")
            return normalized_items

        raise ValueError("evidence must be a non-empty text or list of non-empty text items")

    @field_validator("required_fixes")
    @classmethod
    def normalize_required_fixes(cls, fixes: list[str]) -> list[str]:
        normalized = [fix.strip() for fix in fixes if fix.strip()]
        return normalized

    @field_validator("reviewer_notes")
    @classmethod
    def normalize_reviewer_notes(cls, value: str) -> str:
        return value.strip()

    @field_validator("override_reason", "override_actor")
    @classmethod
    def normalize_nullable_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_conditional_fields(self) -> "ComplianceReport":
        allows_empty_fixes = self.recommendation == ComplianceRecommendation.approve
        if not allows_empty_fixes and not self.required_fixes:
            raise ValueError("required_fixes must not be empty unless recommendation is approve")

        has_override_data = self.override_reason is not None or self.override_actor is not None
        if has_override_data and self.approval_state != ApprovalState.overridden:
            raise ValueError("override fields require approval_state to be overridden")

        if self.approval_state == ApprovalState.overridden:
            if self.override_reason is None or self.override_actor is None:
                raise ValueError("override_reason and override_actor are required when approval_state is overridden")
            if self.override_recommendation is None or self.override_overall_risk is None:
                raise ValueError("override outcome is required when approval_state is overridden")

        if self.is_manually_overridden != (self.approval_state == ApprovalState.overridden):
            raise ValueError("is_manually_overridden must reflect approval_state")

        return self
