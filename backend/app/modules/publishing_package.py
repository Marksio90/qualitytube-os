from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .compliance import ComplianceReport

SAFE_YOUTUBE_TITLE_MAX_LENGTH = 95


class PublishingPackageStatus(StrEnum):
    draft = "draft"
    ready_for_review = "ready_for_review"
    approved = "approved"
    blocked = "blocked"


class PublishingPackage(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    idea_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=SAFE_YOUTUBE_TITLE_MAX_LENGTH)
    description: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    chapters: list[str] = Field(default_factory=list)
    pinned_comment: str | None = None
    thumbnail_brief: str = Field(min_length=1)
    disclosure_notes: str | None = None
    source_notes: str | None = None
    upload_checklist: list[str] = Field(default_factory=list)
    status: PublishingPackageStatus = PublishingPackageStatus.draft
    latest_compliance: ComplianceReport | None = None

    @field_validator("idea_id", "title", "description", "thumbnail_brief", mode="before")
    @classmethod
    def required_non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("title")
    @classmethod
    def safe_title_length(cls, value: str) -> str:
        if len(value) > SAFE_YOUTUBE_TITLE_MAX_LENGTH:
            raise ValueError("title exceeds safe YouTube title length")
        return value

    @field_validator("tags", "chapters", "upload_checklist")
    @classmethod
    def normalize_string_lists(cls, value: list[str]) -> list[str]:
        normalized = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        return normalized

    @field_validator("chapters")
    @classmethod
    def validate_chapters_format(cls, value: list[str]) -> list[str]:
        for chapter in value:
            if " - " not in chapter:
                raise ValueError("chapter format must be '<timestamp> - <title>'")
            timestamp, chapter_title = chapter.split(" - ", maxsplit=1)
            if not timestamp or not chapter_title.strip():
                raise ValueError("chapter format must include timestamp and non-empty title")
            parts = timestamp.split(":")
            if len(parts) not in {2, 3} or not all(part.isdigit() and len(part) == 2 for part in parts):
                raise ValueError("chapter timestamp must be mm:ss or hh:mm:ss")
        return value

    @field_validator("pinned_comment", "disclosure_notes", "source_notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_disclosure_requirement(self) -> "PublishingPackage":
        if (
            self.latest_compliance is not None
            and self.latest_compliance.synthetic_content_disclosure_required
            and not self.disclosure_notes
        ):
            raise ValueError(
                "disclosure_notes is required when latest compliance indicates synthetic disclosure"
            )
        return self


class PublishingPackageRevision(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    package_id: UUID
    revision: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    editor_event: str = Field(min_length=1)
    package_snapshot: PublishingPackage

    @field_validator("editor_event")
    @classmethod
    def non_empty_event(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("editor event must not be empty")
        return normalized


class PublishingPackageRepository:
    """In-memory persistence boundary for canonical publishing package + revisions."""

    def __init__(self) -> None:
        self._canonical_by_idea: dict[str, PublishingPackage] = {}
        self._revisions_by_package_id: dict[UUID, list[PublishingPackageRevision]] = {}

    def create_package(
        self, package: PublishingPackage, editor_event: str = "create"
    ) -> PublishingPackage:
        if package.idea_id in self._canonical_by_idea:
            raise ValueError("only one canonical publishing package is allowed per idea")
        self._canonical_by_idea[package.idea_id] = package
        revision = PublishingPackageRevision(
            package_id=package.id,
            revision=1,
            editor_event=editor_event,
            package_snapshot=package,
        )
        self._revisions_by_package_id[package.id] = [revision]
        return package

    def revise_package(
        self, idea_id: str, updated_package: PublishingPackage, editor_event: str
    ) -> PublishingPackageRevision:
        existing = self._canonical_by_idea.get(idea_id)
        if existing is None:
            raise KeyError(f"no publishing package found for idea_id={idea_id}")
        if updated_package.id != existing.id:
            raise ValueError("publishing package id is immutable across revisions")
        if updated_package.idea_id != idea_id:
            raise ValueError("idea linkage is immutable for canonical publishing package")

        self._canonical_by_idea[idea_id] = updated_package
        revisions = self._revisions_by_package_id[existing.id]
        new_revision = PublishingPackageRevision(
            package_id=existing.id,
            revision=len(revisions) + 1,
            editor_event=editor_event,
            package_snapshot=updated_package,
        )
        revisions.append(new_revision)
        return new_revision

    def get_package(self, idea_id: str) -> PublishingPackage | None:
        return self._canonical_by_idea.get(idea_id)

    def get_revisions(self, package_id: UUID) -> tuple[PublishingPackageRevision, ...]:
        return tuple(self._revisions_by_package_id.get(package_id, []))

    def get_package_by_id(self, package_id: UUID) -> PublishingPackage | None:
        revisions = self._revisions_by_package_id.get(package_id)
        if not revisions:
            return None
        return revisions[-1].package_snapshot
