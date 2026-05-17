from __future__ import annotations

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class AnalyticsReport(Base, TimestampMixin):
    """
    Performance analytics snapshot for a published video.

    Linked to both ContentIdea and PublishingPackage to enable
    feedback loops into the content pipeline.
    metric_snapshot stores raw YouTube Analytics API response as JSON.
    """

    __tablename__ = "analytics_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    publishing_package_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("publishing_packages.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Core performance metrics
    views: Mapped[int | None] = mapped_column(String(20), nullable=True)  # stored as str to avoid int overflow edge cases
    watch_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_view_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_view_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–100
    click_through_rate: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0–1
    impressions: Mapped[int | None] = mapped_column(String(20), nullable=True)

    # Engagement
    likes: Mapped[int | None] = mapped_column(String(20), nullable=True)
    comments: Mapped[int | None] = mapped_column(String(20), nullable=True)
    shares: Mapped[int | None] = mapped_column(String(20), nullable=True)
    subscribers_gained: Mapped[int | None] = mapped_column(String(20), nullable=True)

    # Revenue (nullable — not all channels are monetized)
    estimated_revenue_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    rpm: Mapped[float | None] = mapped_column(Float, nullable=True)  # revenue per mille

    # Retention curve and raw API payload
    retention_curve: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # list[{elapsed_video_time_ratio: float, audience_watch_ratio: float}]

    metric_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Full raw response from YouTube Analytics API for archiving

    report_period_start: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ISO date
    report_period_end: Mapped[str | None] = mapped_column(String(20), nullable=True)    # ISO date

    idea: Mapped["ContentIdea"] = relationship(back_populates="analytics_reports")  # noqa: F821
    publishing_package: Mapped["PublishingPackage | None"] = relationship(back_populates="analytics_reports")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AnalyticsReport id={self.id!r} idea_id={self.idea_id!r}>"


class MonetizationPlan(Base, TimestampMixin):
    """
    Monetization strategy and eligibility tracking for a ContentIdea.

    Records channel eligibility state and the planned revenue approach
    for a given video. Not a guarantee of income — a planning artifact.
    revenue_streams stored as JSON list of {type, description, estimated_monthly}.
    """

    __tablename__ = "monetization_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Channel eligibility snapshot at plan creation
    yt_partner_eligible: Mapped[bool | None] = mapped_column(String(5), nullable=True)
    # Stored as nullable string ("true"/"false"/null) — tri-state: eligible | ineligible | unknown

    # Planned revenue approaches
    revenue_streams: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # list[{type: str, description: str, notes: str}]
    # type values: ad_revenue | sponsorship | affiliate | merchandise | membership | tip | course | other

    primary_revenue_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sponsor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    affiliate_links: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    # list[{label: str, url: str, disclosure: str}]

    disclosure_required: Mapped[bool] = mapped_column(String(5), nullable=False, default="false")
    # Stored as "true"/"false" string to avoid SQLite bool serialisation edge case

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    # Values: draft | active | archived

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<MonetizationPlan id={self.id!r} idea_id={self.idea_id!r} status={self.status!r}>"
