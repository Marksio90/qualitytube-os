from __future__ import annotations

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class ContentIdea(Base, TimestampMixin):
    """
    A content idea with a full lifecycle.

    Extends the stub Idea model in modules/ideas.py.
    The Pydantic Idea class will gain a ContentIdea alias in Phase 4.
    idea_id path parameters in existing API endpoints remain strings until Phase 6.
    """

    __tablename__ = "content_ideas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    channel_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    audience: Mapped[str] = mapped_column(String(500), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False)

    # Lifecycle stage — mirrors WorkflowRun.current_stage for fast filtering
    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="draft",
        index=True,
        # Values: draft | researched | angle_pending | angle_approved | scripting
        #         | in_review | published | archived
    )

    channel: Mapped["Channel"] = relationship(back_populates="content_ideas")  # noqa: F821
    research_briefs: Mapped[list[ResearchBrief]] = relationship(back_populates="idea", cascade="all, delete-orphan")
    angles: Mapped[list[Angle]] = relationship(back_populates="idea", cascade="all, delete-orphan")
    analytics_reports: Mapped[list["AnalyticsReport"]] = relationship(back_populates="idea", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ContentIdea id={self.id!r} title={self.title!r}>"


class ResearchBrief(Base, TimestampMixin):
    """
    Structured research for a ContentIdea.

    Extends the stub ResearchBrief in modules/research_brief.py by adding
    idea linkage, key_questions, and originality_notes.
    The Pydantic ResearchBrief will be extended to match in Phase 8.
    """

    __tablename__ = "research_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    goals: Mapped[list] = mapped_column(JSON, nullable=False, default=list)        # list[str]
    references: Mapped[list] = mapped_column(JSON, nullable=False, default=list)   # list[str]
    key_questions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # list[str]
    originality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    idea: Mapped[ContentIdea] = relationship(back_populates="research_briefs")

    def __repr__(self) -> str:
        return f"<ResearchBrief id={self.id!r} topic={self.topic!r}>"


class Angle(Base, TimestampMixin):
    """
    A specific content angle for a ContentIdea.

    AngleStatus enum from modules/angle_approval.py is the canonical status enum.
    Currently angle_id is passed as a raw string to script generation endpoints;
    this model enables full lifecycle management in Phase 4/9.
    """

    __tablename__ = "angles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    argument: Mapped[str] = mapped_column(Text, nullable=False)
    counter_narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience_benefit: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_requirement: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Scoring — populated by Originality Engine (Phase 9)
    originality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    differentiation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    audience_value_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # AngleStatus enum: pending | approved | rejected
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)

    idea: Mapped[ContentIdea] = relationship(back_populates="angles")

    def __repr__(self) -> str:
        return f"<Angle id={self.id!r} title={self.title!r} status={self.status!r}>"
