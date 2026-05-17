from __future__ import annotations

from pydantic import BaseModel, Field


class RetentionPoint(BaseModel):
    elapsed_video_time_ratio: float  # 0.0–1.0
    audience_watch_ratio: float      # 0.0–1.0


class AnalyticsReport(BaseModel):
    """Performance analytics snapshot for a published video."""

    id: str
    idea_id: str
    publishing_package_id: str | None = None

    views: int | None = None
    watch_time_hours: float | None = None
    avg_view_duration_seconds: float | None = None
    avg_view_percentage: float | None = None
    click_through_rate: float | None = None
    impressions: int | None = None

    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    subscribers_gained: int | None = None

    estimated_revenue_usd: float | None = None
    rpm: float | None = None

    retention_curve: list[RetentionPoint] = Field(default_factory=list)
    metric_snapshot: dict = Field(default_factory=dict)

    report_period_start: str | None = None
    report_period_end: str | None = None

    created_at: str | None = None
    updated_at: str | None = None


class RevenueStream(BaseModel):
    type: str
    # Values: ad_revenue | sponsorship | affiliate | merchandise | membership | tip | course | other
    description: str = ""
    notes: str = ""


class AffiliateLink(BaseModel):
    label: str
    url: str
    disclosure: str = ""


class MonetizationPlan(BaseModel):
    """
    Monetization strategy for a ContentIdea.

    Not a guarantee of income — a planning artifact documenting
    intended revenue approaches for a specific video.
    """

    id: str
    idea_id: str
    yt_partner_eligible: bool | None = None
    revenue_streams: list[RevenueStream] = Field(default_factory=list)
    primary_revenue_type: str | None = None
    sponsor_notes: str | None = None
    affiliate_links: list[AffiliateLink] = Field(default_factory=list)
    disclosure_required: bool = False
    status: str = "draft"
    # Values: draft | active | archived
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class YouTubeQuotaLedgerEntry(BaseModel):
    """Single quota consumption record for YouTube Data API v3."""

    id: str
    operation: str
    quota_cost: int
    endpoint: str | None = None
    http_status: int | None = None
    error_reason: str | None = None
    correlation_id: str | None = None
    idea_id: str | None = None
    created_at: str
