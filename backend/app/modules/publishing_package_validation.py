from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .compliance import RiskLevel
from .publishing_package import PublishingPackage, SAFE_YOUTUBE_TITLE_MAX_LENGTH
from .scripts import Script


class PublishingValidationIssue(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class PublishingValidationResult(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    eligible_for_approval: bool
    errors: list[PublishingValidationIssue] = Field(default_factory=list)
    warnings: list[PublishingValidationIssue] = Field(default_factory=list)


class PublishingPackageValidationService:
    """Deterministic publishing-package validation rules."""

    def validate(
        self,
        *,
        package: PublishingPackage,
        script: Script,
        compliance_overall_risk: RiskLevel,
        synthetic_disclosure_required: bool,
    ) -> PublishingValidationResult:
        errors: list[PublishingValidationIssue] = []
        warnings: list[PublishingValidationIssue] = []

        title = package.title.strip()
        if not title:
            errors.append(PublishingValidationIssue(code="TITLE_REQUIRED", message="title is required"))
        if len(title) > SAFE_YOUTUBE_TITLE_MAX_LENGTH:
            errors.append(
                PublishingValidationIssue(
                    code="TITLE_TOO_LONG",
                    message="title exceeds safe length",
                    details={"max_length": str(SAFE_YOUTUBE_TITLE_MAX_LENGTH), "actual_length": str(len(title))},
                )
            )

        if not package.description.strip():
            errors.append(PublishingValidationIssue(code="DESCRIPTION_REQUIRED", message="description is required"))

        chapter_seconds: list[int] = []
        for index, chapter in enumerate(package.chapters):
            chapter_text = chapter.strip()
            if " - " not in chapter_text:
                errors.append(
                    PublishingValidationIssue(
                        code="CHAPTER_INVALID_FORMAT",
                        message="chapter must be '<timestamp> - <title>'",
                        details={"index": str(index), "value": chapter_text},
                    )
                )
                continue
            timestamp, chapter_title = chapter_text.split(" - ", maxsplit=1)
            if not chapter_title.strip():
                errors.append(
                    PublishingValidationIssue(
                        code="CHAPTER_EMPTY_TITLE",
                        message="chapter title is required",
                        details={"index": str(index), "timestamp": timestamp.strip()},
                    )
                )
            parsed_seconds = self._parse_timestamp_to_seconds(timestamp)
            if parsed_seconds is None:
                errors.append(
                    PublishingValidationIssue(
                        code="CHAPTER_INVALID_TIMESTAMP",
                        message="chapter timestamp must be mm:ss or hh:mm:ss",
                        details={"index": str(index), "timestamp": timestamp.strip()},
                    )
                )
                continue
            chapter_seconds.append(parsed_seconds)

        for idx in range(1, len(chapter_seconds)):
            if chapter_seconds[idx] <= chapter_seconds[idx - 1]:
                errors.append(
                    PublishingValidationIssue(
                        code="CHAPTER_TIMESTAMPS_NOT_INCREASING",
                        message="chapter timestamps must be strictly increasing",
                        details={"index": str(idx)},
                    )
                )
                break

        if synthetic_disclosure_required and not (package.disclosure_notes or "").strip():
            errors.append(
                PublishingValidationIssue(
                    code="DISCLOSURE_NOTES_REQUIRED",
                    message="disclosure_notes is required when synthetic disclosure is required",
                )
            )

        contradiction_markers = self._title_script_contradiction_markers(title, script_text=self._script_text(script))
        if contradiction_markers:
            warnings.append(
                PublishingValidationIssue(
                    code="TITLE_SCRIPT_CONTRADICTION",
                    message="title may contradict the script promise",
                    details={"markers": ", ".join(contradiction_markers)},
                )
            )

        if compliance_overall_risk == RiskLevel.high:
            errors.append(
                PublishingValidationIssue(
                    code="HIGH_COMPLIANCE_RISK",
                    message="approval blocked because compliance overall risk is high",
                )
            )

        return PublishingValidationResult(
            eligible_for_approval=not errors,
            errors=errors,
            warnings=warnings,
        )

    def _script_text(self, script: Script) -> str:
        return " ".join(section.content.strip().lower() for section in script.sections)

    def _parse_timestamp_to_seconds(self, timestamp: str) -> int | None:
        parts = timestamp.strip().split(":")
        if len(parts) not in {2, 3}:
            return None
        if not all(part.isdigit() and len(part) == 2 for part in parts):
            return None
        numbers = [int(part) for part in parts]
        if len(numbers) == 2:
            minutes, seconds = numbers
            return minutes * 60 + seconds
        hours, minutes, seconds = numbers
        return hours * 3600 + minutes * 60 + seconds

    def _title_script_contradiction_markers(self, title: str, *, script_text: str) -> list[str]:
        checks = [
            ("beginner", "advanced"),
            ("advanced", "beginner"),
            ("fast", "slow"),
            ("easy", "hard"),
            ("never", "always"),
        ]
        lowered_title = title.lower()
        markers: list[str] = []
        for left, right in checks:
            if left in lowered_title and right in script_text:
                markers.append(f"title:{left}/script:{right}")
        return markers
