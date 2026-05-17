from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid


class LLMCall(Base):
    """
    Immutable audit log entry for a single LLM invocation.

    Mirrors the Pydantic LLMCall in modules/llm_logging.py.
    Never updated after insertion — append-only telemetry table.
    created_at stored as ISO-8601 string (no server default needed —
    callers always supply a timestamp).
    """

    __tablename__ = "llm_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)

    prompt_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    response_chars: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Optional linkage back to a content idea for cost attribution
    idea_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    def __repr__(self) -> str:
        return f"<LLMCall id={self.id!r} operation={self.operation!r} model={self.model!r}>"


class YouTubeQuotaLedger(Base):
    """
    Append-only ledger tracking YouTube Data API v3 quota consumption.

    YouTube grants 10,000 units/day per project. Each row records one
    API call's cost so the running total can be queried at any time.
    created_at stored as ISO-8601 string supplied by the caller.
    """

    __tablename__ = "youtube_quota_ledger"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)

    operation: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "search.list", "videos.insert", "channels.list"

    quota_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    # Units consumed: search.list=100, videos.insert=1600, etc.

    endpoint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)

    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    idea_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # ISO-8601 datetime; index enables efficient "quota used today" queries

    def __repr__(self) -> str:
        return f"<YouTubeQuotaLedger id={self.id!r} operation={self.operation!r} cost={self.quota_cost}>"
