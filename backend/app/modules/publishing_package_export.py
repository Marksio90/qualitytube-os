from __future__ import annotations

from enum import StrEnum
from typing import Any

from .publishing_package import PublishingPackage


class PublishingPackageExportFormat(StrEnum):
    json = "json"
    markdown = "markdown"


class PublishingPackageExportService:
    def export(self, package: PublishingPackage, format: PublishingPackageExportFormat) -> dict[str, Any] | str:
        if format == PublishingPackageExportFormat.json:
            return package.model_dump(mode="json")
        return self._render_markdown(package)

    def _render_markdown(self, package: PublishingPackage) -> str:
        sections: list[str] = [
            "## Title",
            package.title,
            "",
            "## Description",
            package.description,
            "",
            "## Tags",
            self._render_list(package.tags),
            "",
            "## Chapters",
            self._render_list(package.chapters),
            "",
            "## Pinned Comment",
            package.pinned_comment or "None",
            "",
            "## Thumbnail Brief",
            package.thumbnail_brief,
            "",
            "## Disclosure Notes",
            package.disclosure_notes or "None",
            "",
            "## Source Notes",
            package.source_notes or "None",
            "",
            "## Checklist",
            self._render_checkbox_list(package.upload_checklist),
            "",
            "## Status",
            package.status.value,
        ]
        return "\n".join(sections)

    @staticmethod
    def _render_list(items: list[str]) -> str:
        if not items:
            return "None"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _render_checkbox_list(items: list[str]) -> str:
        if not items:
            return "None"
        return "\n".join(f"- [ ] {item}" for item in items)
