from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class PublishingPackage(Base, TimestampMixin):
    """
    Structured YouTube upload metadata for a ContentIdea.

    Mirrors the Pydantic PublishingPackage in modules/publishing_package.py.
    tags, chapters, and upload_checklist are stored as JSON columns.
    compliance_report_id is a proper FK here (embedded as latest_compliance object in Pydantic).
    """

    __tablename__ = "publishing_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    idea_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    compliance_report_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("compliance_reports.id", ondelete="SET NULL"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(95), nullable=False)  # SAFE_YOUTUBE_TITLE_MAX_LENGTH = 95
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    chapters: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    pinned_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_brief: Mapped[str] = mapped_column(Text, nullable=False)
    disclosure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    upload_checklist: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    # Values: draft | ready_for_review | approved | blocked

    compliance_report: Mapped["ComplianceReport | None"] = relationship(back_populates="publishing_packages")  # noqa: F821
    revisions: Mapped[list[PublishingPackageRevision]] = relationship(
        back_populates="package",
        cascade="all, delete-orphan",
        order_by="PublishingPackageRevision.revision",
    )
    analytics_reports: Mapped[list["AnalyticsReport"]] = relationship(back_populates="publishing_package", cascade="all, delete-orphan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PublishingPackage id={self.id!r} idea_id={self.idea_id!r} status={self.status!r}>"


class PublishingPackageRevision(Base):
    """Append-only revision snapshot for a PublishingPackage. Never updated."""

    __tablename__ = "publishing_package_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    package_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("publishing_packages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    editor_event: Mapped[str] = mapped_column(String(100), nullable=False)
    package_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    package: Mapped[PublishingPackage] = relationship(back_populates="revisions")

    def __repr__(self) -> str:
        return f"<PublishingPackageRevision package_id={self.package_id!r} revision={self.revision}>"
