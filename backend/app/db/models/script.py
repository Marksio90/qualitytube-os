from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Script(Base, TimestampMixin):
    """
    Canonical script entity.

    Mirrors the Pydantic Script in modules/scripts.py.
    sections and quality_report are JSON columns — they are already structured
    JSON blobs and are not relational data.
    """

    __tablename__ = "scripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    angle_id: Mapped[str] = mapped_column(String(36), nullable=False)  # will become FK → angles in Phase 9
    state: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    # Values: draft | approved | ready_to_publish

    sections: Mapped[list] = mapped_column(JSON, nullable=False)       # list[{title, content}]
    quality_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # ScriptQualityReport fields

    versions: Mapped[list[ScriptVersion]] = relationship(back_populates="script", cascade="all, delete-orphan", order_by="ScriptVersion.revision")
    hook_variants: Mapped[list[HookVariant]] = relationship(back_populates="script", cascade="all, delete-orphan")
    retention_reviews: Mapped[list[RetentionReview]] = relationship(back_populates="script", cascade="all, delete-orphan")
    visual_plan: Mapped["VisualPlan | None"] = relationship(back_populates="script", uselist=False, cascade="all, delete-orphan")  # noqa: F821
    audio_briefs: Mapped[list["AudioBrief"]] = relationship(back_populates="script", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Script id={self.id!r} idea_id={self.idea_id!r} state={self.state!r}>"


class ScriptVersion(Base):
    """Append-only revision snapshot for a Script. Never updated after creation."""

    __tablename__ = "script_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    editor_event: Mapped[str] = mapped_column(String(100), nullable=False)
    script_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)  # full Script dump
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)  # ISO-8601 string

    script: Mapped[Script] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return f"<ScriptVersion script_id={self.script_id!r} revision={self.revision}>"


class HookVariant(Base, TimestampMixin):
    """
    A single hook opening variant for a Script.

    Mirrors the Pydantic HookVariant in modules/scripts.py.
    """

    __tablename__ = "hook_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)

    type: Mapped[str] = mapped_column(String(40), nullable=False)
    # Values: contradiction | shock | question | story | mistake | before_after | hidden_mechanism

    text: Mapped[str] = mapped_column(Text, nullable=False)
    promise: Mapped[str] = mapped_column(Text, nullable=False)
    curiosity_gap: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–5
    score: Mapped[float] = mapped_column(Float, nullable=False)        # 0.0–10.0
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    script: Mapped[Script] = relationship(back_populates="hook_variants")

    def __repr__(self) -> str:
        return f"<HookVariant id={self.id!r} type={self.type!r} score={self.score}>"


class RetentionReview(Base, TimestampMixin):
    """
    AI-generated retention risk analysis for a Script.

    Boolean warning flags become columns; section_map, recommendations,
    and timestamps become JSON columns.
    """

    __tablename__ = "retention_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)

    weak_intro_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    slow_context_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payoff_delay_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    repeated_sentence_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generic_section_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unclear_promise_warning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    section_map: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    timestamps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    script: Mapped[Script] = relationship(back_populates="retention_reviews")

    def __repr__(self) -> str:
        return f"<RetentionReview id={self.id!r} script_id={self.script_id!r}>"
