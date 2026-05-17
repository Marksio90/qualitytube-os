from __future__ import annotations

from pydantic import BaseModel, Field


class Channel(BaseModel):
    """
    Full channel profile — superset of ChannelMemory.

    ChannelMemory (channel_id, tone_notes, banned_claims) is the lightweight
    in-memory version used in current endpoints. Channel is the ORM-backed
    canonical entity that will replace it in Phase 3.
    """

    id: str
    workspace_id: str
    name: str
    youtube_channel_id: str | None = None
    language: str = "en"
    tone_notes: list[str] = Field(default_factory=list)
    banned_claims: list[str] = Field(default_factory=list)
    content_pillars: list[str] = Field(default_factory=list)
    audience_description: str = ""
    upload_schedule_target: int | None = None
    # Target uploads per week; None means no target set
    created_at: str | None = None
    updated_at: str | None = None
