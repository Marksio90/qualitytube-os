from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchBrief(BaseModel):
    topic: str
    goals: list[str]
    references: list[str]
    # Extended fields (nullable for backwards compatibility with existing callers)
    id: str | None = None
    idea_id: str | None = None
    key_questions: list[str] = Field(default_factory=list)
    originality_notes: str = ""
    created_at: str | None = None
    updated_at: str | None = None
