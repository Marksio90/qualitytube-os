from __future__ import annotations

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class VisualPlan(Base, TimestampMixin):
    """
    Scene-by-scene visual strategy for an approved Script.

    Scenes are stored in a child visual_scenes table (not as JSON)
    to enable per-scene approval state in Phase 15.
    """

    __tablename__ = "visual_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    approval_state: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    # Values: draft | approved

    script: Mapped["Script"] = relationship(back_populates="visual_plan")  # noqa: F821
    scenes: Mapped[list[VisualScene]] = relationship(back_populates="plan", cascade="all, delete-orphan", order_by="VisualScene.scene_number")

    def __repr__(self) -> str:
        return f"<VisualPlan id={self.id!r} script_id={self.script_id!r} state={self.approval_state!r}>"


class VisualScene(Base):
    """
    A single scene within a VisualPlan.

    scene_approval_state is a new field (not in the current Pydantic model)
    to enable per-scene approval in Phase 15.
    """

    __tablename__ = "visual_scenes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("visual_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    narration_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    visual_type: Mapped[str] = mapped_column(String(40), nullable=False)
    visual_description: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    asset_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    filler_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Per-scene approval — Phase 15
    scene_approval_state: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    # Values: draft | approved | revision_requested | rejected

    plan: Mapped[VisualPlan] = relationship(back_populates="scenes")

    def __repr__(self) -> str:
        return f"<VisualScene plan_id={self.plan_id!r} scene={self.scene_number}>"


class AudioBrief(Base, TimestampMixin):
    """
    Voice and audio delivery brief for a Script.

    Mirrors the Pydantic AudioBrief in modules/audio_brief.py.
    """

    __tablename__ = "audio_briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    script_id: Mapped[str] = mapped_column(String(36), ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True)

    voice_style: Mapped[str] = mapped_column(String(40), nullable=False)
    pace_wpm: Mapped[int] = mapped_column(Integer, nullable=False)
    emotional_tone: Mapped[str] = mapped_column(Text, nullable=False)
    pause_notes: Mapped[str] = mapped_column(Text, nullable=False)
    pronunciation_notes: Mapped[str] = mapped_column(Text, nullable=False)
    emphasis_notes: Mapped[str] = mapped_column(Text, nullable=False)
    synthetic_voice_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disclosure_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disclosure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_text: Mapped[str] = mapped_column(Text, nullable=False)
    approval_state: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # Values: pending | approved | rejected | overridden

    script: Mapped["Script"] = relationship(back_populates="audio_briefs")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AudioBrief id={self.id!r} script_id={self.script_id!r} state={self.approval_state!r}>"


class TitleVariant(Base):
    """
    A title candidate for a ContentIdea.

    Mirrors the Pydantic TitleVariant in modules/title_thumbnail_lab.py.
    No updated_at — scores and selection state are updated in-place.
    """

    __tablename__ = "title_variants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True)

    title_text: Mapped[str] = mapped_column(String(200), nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    clarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    curiosity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    truthfulness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    promise_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    clickbait_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overall_title_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<TitleVariant id={self.id!r} idea_id={self.idea_id!r}>"


class ThumbnailConcept(Base):
    """
    A visual thumbnail concept for a ContentIdea.

    Mirrors the Pydantic ThumbnailConcept in modules/title_thumbnail_lab.py.
    """

    __tablename__ = "thumbnail_concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True)

    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    main_object: Mapped[str] = mapped_column(String(150), nullable=False)
    emotion: Mapped[str] = mapped_column(String(120), nullable=False)
    composition: Mapped[str] = mapped_column(Text, nullable=False)
    text_overlay: Mapped[str] = mapped_column(String(120), nullable=False)
    visual_contrast: Mapped[str] = mapped_column(Text, nullable=False)
    mobile_readability_notes: Mapped[str] = mapped_column(Text, nullable=False)
    avoid: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<ThumbnailConcept id={self.id!r} idea_id={self.idea_id!r}>"
