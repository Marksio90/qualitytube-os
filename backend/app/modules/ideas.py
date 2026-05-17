from __future__ import annotations

from pydantic import BaseModel, Field


class Idea(BaseModel):
    """Lightweight idea reference — preserved for backwards compatibility."""

    id: str
    title: str
    audience: str
    premise: str


class ContentIdea(BaseModel):
    """Canonical content idea with full pipeline metadata."""

    id: str
    channel_id: str = "default"
    title: str
    audience: str
    premise: str
    status: str = "draft"
    # Values: draft | active | archived | published
    created_at: str | None = None
    updated_at: str | None = None
