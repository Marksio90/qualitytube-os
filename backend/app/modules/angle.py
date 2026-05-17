from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.angle_approval import AngleStatus


class Angle(BaseModel):
    """
    A strategic content angle for a ContentIdea.

    Scores are nullable — they are populated after AI scoring
    and may be absent on newly created angles.
    """

    id: str
    idea_id: str
    title: str
    argument: str
    counter_narrative: str = ""
    audience_benefit: str = ""
    evidence_requirement: str = ""
    originality_score: float | None = None
    differentiation_score: float | None = None
    audience_value_score: float | None = None
    status: AngleStatus = AngleStatus.pending
    created_at: str | None = None
    updated_at: str | None = None
