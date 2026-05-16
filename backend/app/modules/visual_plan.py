from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VisualType(StrEnum):
    stock = "stock"
    ai_image = "ai_image"
    ai_video = "ai_video"
    diagram = "diagram"
    timeline = "timeline"
    map = "map"
    chart = "chart"
    screen_recording = "screen_recording"
    b_roll = "b_roll"
    text_animation = "text_animation"
    icon_animation = "icon_animation"


class VisualPlanApprovalState(StrEnum):
    draft = "draft"
    approved = "approved"


class VisualScene(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    scene_number: int = Field(ge=1)
    narration_excerpt: str = Field(min_length=1)
    visual_type: VisualType
    visual_description: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    asset_notes: str | None = None
    risk_notes: str | None = None
    filler_risk_score: float = Field(ge=0.0, le=1.0)

    @field_validator(
        "narration_excerpt",
        "visual_description",
        "purpose",
        mode="before",
    )
    @classmethod
    def required_non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("asset_notes", "risk_notes", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        return normalized or None


class VisualPlan(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    script_id: UUID
    scenes: list[VisualScene] = Field(default_factory=list)
    approval_state: VisualPlanApprovalState = VisualPlanApprovalState.draft
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_scene_numbering(self) -> "VisualPlan":
        previous_scene_number: int | None = None
        for scene in self.scenes:
            if previous_scene_number is not None and scene.scene_number <= previous_scene_number:
                raise ValueError("scene_number must be strictly increasing in list order")
            previous_scene_number = scene.scene_number
        return self


class VisualPlanRepository:
    """In-memory persistence boundary for canonical visual plan by script."""

    def __init__(self) -> None:
        self._by_script_id: dict[UUID, VisualPlan] = {}
        self._script_id_by_plan_id: dict[UUID, UUID] = {}

    def create_or_update(self, plan: VisualPlan) -> VisualPlan:
        existing = self._by_script_id.get(plan.script_id)

        if existing is None:
            self._by_script_id[plan.script_id] = plan
            self._script_id_by_plan_id[plan.id] = plan.script_id
            return plan

        if plan.id != existing.id:
            raise ValueError("visual plan id is immutable for script_id")

        if plan.approval_state != existing.approval_state:
            raise ValueError("approval_state transition must use approve")

        updated = plan.model_copy(update={"updated_at": datetime.now(UTC)})
        self._by_script_id[plan.script_id] = updated
        self._script_id_by_plan_id[updated.id] = updated.script_id
        return updated

    def get_by_script_id(self, script_id: UUID) -> VisualPlan | None:
        return self._by_script_id.get(script_id)

    def get_by_visual_plan_id(self, visual_plan_id: UUID) -> VisualPlan | None:
        script_id = self._script_id_by_plan_id.get(visual_plan_id)
        if script_id is None:
            return None
        return self._by_script_id.get(script_id)

    def approve(self, visual_plan_id: UUID) -> VisualPlan:
        current = self.get_by_visual_plan_id(visual_plan_id)
        if current is None:
            raise KeyError(f"no visual plan found for visual_plan_id={visual_plan_id}")
        if current.approval_state == VisualPlanApprovalState.approved:
            return current

        approved = current.model_copy(
            update={
                "approval_state": VisualPlanApprovalState.approved,
                "updated_at": datetime.now(UTC),
            }
        )
        self._by_script_id[approved.script_id] = approved
        self._script_id_by_plan_id[approved.id] = approved.script_id
        return approved
