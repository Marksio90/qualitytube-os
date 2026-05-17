from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class WorkflowRun(Base, TimestampMixin):
    """
    Tracks a ContentIdea through its full production lifecycle.

    One WorkflowRun per ContentIdea. Stages mirror the canonical pipeline:
    idea_captured → researched → angle_approved → scripting → hooks_reviewed
    → compliance_reviewed → publishing_ready → published → archived
    """

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    current_stage: Mapped[str] = mapped_column(String(40), nullable=False, default="idea_captured", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    # Values: active | paused | completed | abandoned

    steps: Mapped[list[WorkflowStep]] = relationship(back_populates="run", cascade="all, delete-orphan", order_by="WorkflowStep.created_at")

    def __repr__(self) -> str:
        return f"<WorkflowRun id={self.id!r} idea_id={self.idea_id!r} stage={self.current_stage!r}>"


class WorkflowStep(Base):
    """
    Immutable record of a single stage transition in a WorkflowRun.

    Provides full audit history: who moved the content forward, when, and why.
    """

    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # Values: entered | completed | blocked | skipped

    actor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    run: Mapped[WorkflowRun] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<WorkflowStep run_id={self.run_id!r} stage={self.stage!r} status={self.status!r}>"


class Approval(Base):
    """
    Immutable approval event record for any approvable entity.

    Enables cross-entity audit queries and multi-approver flows (Phase 17).
    The embedded approval_state on each entity is kept in sync when an Approval
    record is created.
    """

    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    # Polymorphic entity reference
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Values: script | compliance_report | publishing_package | audio_brief | visual_plan

    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    action: Mapped[str] = mapped_column(String(30), nullable=False)
    # Values: approve | override | reject | request_changes

    actor: Mapped[str] = mapped_column(String(200), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_state: Mapped[str] = mapped_column(String(30), nullable=False)
    new_state: Mapped[str] = mapped_column(String(30), nullable=False)

    created_at: Mapped[str] = mapped_column(String(50), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Approval id={self.id!r} entity_type={self.entity_type!r} action={self.action!r}>"
