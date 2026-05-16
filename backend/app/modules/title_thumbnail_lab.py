from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TitleVariant(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    idea_id: str = Field(min_length=1)
    title_text: str = Field(min_length=1, max_length=200)
    selected: bool = False
    clarity_score: float = Field(ge=0.0, le=10.0)
    curiosity_score: float = Field(ge=0.0, le=10.0)
    truthfulness_score: float = Field(ge=0.0, le=10.0)
    promise_match_score: float = Field(ge=0.0, le=10.0)
    clickbait_risk: float = Field(ge=0.0, le=10.0)
    overall_title_score: float = Field(ge=0.0, le=10.0)
    rationale: str | None = None
    warnings: str | None = None

    @field_validator("idea_id", "title_text", mode="before")
    @classmethod
    def non_empty_required_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("rationale", "warnings", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        return normalized or None


class ThumbnailConcept(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    idea_id: str = Field(min_length=1)
    selected: bool = False
    main_object: str = Field(min_length=1, max_length=150)
    emotion: str = Field(min_length=1, max_length=120)
    composition: str = Field(min_length=1, max_length=400)
    text_overlay: str = Field(min_length=1, max_length=120)
    visual_contrast: str = Field(min_length=1, max_length=250)
    mobile_readability_notes: str = Field(min_length=1, max_length=500)
    avoid: str = Field(min_length=1, max_length=500)
    score: float = Field(ge=0.0, le=10.0)

    @field_validator(
        "idea_id",
        "main_object",
        "emotion",
        "composition",
        "text_overlay",
        "visual_contrast",
        "mobile_readability_notes",
        "avoid",
        mode="before",
    )
    @classmethod
    def non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized


class TitleThumbnailLabRepository:
    """In-memory persistence for title and thumbnail options with selection rules."""

    def __init__(self) -> None:
        self._titles_by_idea: dict[str, list[TitleVariant]] = {}
        self._thumbnails_by_idea: dict[str, list[ThumbnailConcept]] = {}

    def create_title_variant(self, variant: TitleVariant) -> TitleVariant:
        items = self._titles_by_idea.setdefault(variant.idea_id, [])
        if variant.selected:
            for item in items:
                item.selected = False
        items.append(variant)
        return variant

    def list_title_variants(self, idea_id: str) -> tuple[TitleVariant, ...]:
        return tuple(self._titles_by_idea.get(idea_id, []))

    def update_title_variant(self, updated: TitleVariant) -> TitleVariant:
        items = self._titles_by_idea.get(updated.idea_id, [])
        for idx, item in enumerate(items):
            if item.id == updated.id:
                if updated.selected:
                    for peer in items:
                        peer.selected = False
                items[idx] = updated
                return updated
        raise KeyError(f"no title variant found for id={updated.id}")

    def select_title_variant(self, idea_id: str, variant_id: UUID) -> TitleVariant:
        items = self._titles_by_idea.get(idea_id, [])
        target: TitleVariant | None = None
        for item in items:
            item.selected = item.id == variant_id
            if item.selected:
                target = item
        if target is None:
            raise KeyError(f"no title variant found for id={variant_id} and idea_id={idea_id}")
        return target

    def create_thumbnail_concept(self, concept: ThumbnailConcept) -> ThumbnailConcept:
        items = self._thumbnails_by_idea.setdefault(concept.idea_id, [])
        if concept.selected:
            for item in items:
                item.selected = False
        items.append(concept)
        return concept

    def list_thumbnail_concepts(self, idea_id: str) -> tuple[ThumbnailConcept, ...]:
        return tuple(self._thumbnails_by_idea.get(idea_id, []))

    def update_thumbnail_concept(self, updated: ThumbnailConcept) -> ThumbnailConcept:
        items = self._thumbnails_by_idea.get(updated.idea_id, [])
        for idx, item in enumerate(items):
            if item.id == updated.id:
                if updated.selected:
                    for peer in items:
                        peer.selected = False
                items[idx] = updated
                return updated
        raise KeyError(f"no thumbnail concept found for id={updated.id}")

    def select_thumbnail_concept(self, idea_id: str, concept_id: UUID) -> ThumbnailConcept:
        items = self._thumbnails_by_idea.get(idea_id, [])
        target: ThumbnailConcept | None = None
        for item in items:
            item.selected = item.id == concept_id
            if item.selected:
                target = item
        if target is None:
            raise KeyError(f"no thumbnail concept found for id={concept_id} and idea_id={idea_id}")
        return target
