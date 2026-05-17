from __future__ import annotations

from pydantic import BaseModel, Field


class Organization(BaseModel):
    """Top-level tenant grouping workspaces."""

    id: str
    name: str
    slug: str
    created_at: str | None = None
    updated_at: str | None = None


class Workspace(BaseModel):
    """A named project space within an Organization, containing one or more Channels."""

    id: str
    org_id: str
    name: str
    slug: str
    created_at: str | None = None
    updated_at: str | None = None
