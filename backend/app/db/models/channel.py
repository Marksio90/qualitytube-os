from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Channel(Base, TimestampMixin):
    """
    A YouTube channel managed within a Workspace.

    Absorbs ChannelMemory fields (tone_notes, banned_claims) so that the
    in-memory ChannelMemoryRepository can be replaced by this ORM model in Phase 3.
    ChannelMemory Pydantic model in modules/channel_memory.py remains unchanged.
    """

    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    youtube_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")

    # Channel Memory fields (migrated from in-memory ChannelMemoryRepository)
    tone_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    banned_claims: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    content_pillars: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    audience_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_schedule_target: Mapped[int | None] = mapped_column(Integer, nullable=True)  # videos per month

    workspace: Mapped["Workspace"] = relationship(back_populates="channels")  # noqa: F821
    content_ideas: Mapped[list["ContentIdea"]] = relationship(back_populates="channel", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Channel id={self.id!r} name={self.name!r}>"
