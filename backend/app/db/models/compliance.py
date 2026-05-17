from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class ComplianceReport(Base, TimestampMixin):
    """
    Persisted compliance assessment for a ContentIdea.

    Mirrors the Pydantic ComplianceReport in modules/compliance.py.
    All RiskLevel fields become string enum columns.
    override_audit_log is stored as a JSON column.

    NOTE: ComplianceCheckResult in modules/compliance_checks.py is an
    intermediate computation type, NOT a stored entity. This ORM model
    is the only persisted compliance artifact.
    """

    __tablename__ = "compliance_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True)

    # Risk dimensions — RiskLevel enum values: low | medium | high
    reused_content_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    repetitive_content_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    mass_production_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    synthetic_content_disclosure_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    copyright_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    misleading_claims_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    sensitive_topic_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    clickbait_risk: Mapped[str] = mapped_column(String(10), nullable=False)

    # Evidence — list[str] stored as JSON
    originality_evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    human_contribution_evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Outcome
    overall_risk: Mapped[str] = mapped_column(String(10), nullable=False)
    recommendation: Mapped[str] = mapped_column(String(30), nullable=False)
    # Values: approve | approve_with_fixes | high_risk | do_not_publish

    required_fixes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    reviewer_notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reviewer_source: Mapped[str] = mapped_column(String(30), nullable=False)
    # Values: deterministic | ai_assisted | human_override

    # Approval lifecycle
    approval_state: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # Values: pending | approved | rejected | overridden

    # Override fields
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    override_actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    override_recommendation: Mapped[str | None] = mapped_column(String(30), nullable=True)
    override_overall_risk: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_manually_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_audit_log: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    publishing_packages: Mapped[list["PublishingPackage"]] = relationship(back_populates="compliance_report")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ComplianceReport id={self.id!r} idea_id={self.idea_id!r} state={self.approval_state!r}>"
