from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, new_uuid


class Organization(Base, TimestampMixin):
    """Top-level tenant. An agency, company, or individual creator account."""

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    workspaces: Mapped[list[Workspace]] = relationship(back_populates="organization", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("slug", name="uq_org_slug"),)

    def __repr__(self) -> str:
        return f"<Organization id={self.id!r} slug={self.slug!r}>"


class Workspace(Base, TimestampMixin):
    """A project or team within an Organization. Maps to one channel portfolio."""

    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="workspaces")
    channels: Mapped[list["Channel"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")  # noqa: F821

    __table_args__ = (UniqueConstraint("org_id", "slug", name="uq_workspace_org_slug"),)

    def __repr__(self) -> str:
        return f"<Workspace id={self.id!r} slug={self.slug!r}>"
