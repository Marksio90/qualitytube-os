from __future__ import annotations

from pydantic import BaseModel, Field


class WorkflowRun(BaseModel):
    """Tracks a ContentIdea through its full production lifecycle."""

    id: str
    idea_id: str
    current_stage: str = "idea_captured"
    # idea_captured → researched → angle_approved → scripting → hooks_reviewed
    # → compliance_reviewed → publishing_ready → published → archived
    status: str = "active"
    # Values: active | paused | completed | abandoned
    created_at: str | None = None
    updated_at: str | None = None
    steps: list[WorkflowStep] = Field(default_factory=list)


class WorkflowStep(BaseModel):
    """Immutable record of a single stage transition."""

    id: str
    run_id: str
    stage: str
    status: str
    # Values: entered | completed | blocked | skipped
    actor: str | None = None
    notes: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str


class Approval(BaseModel):
    """Immutable approval event for any approvable entity."""

    id: str
    entity_type: str
    # Values: script | compliance_report | publishing_package | audio_brief | visual_plan
    entity_id: str
    action: str
    # Values: approve | override | reject | request_changes
    actor: str
    reason: str | None = None
    previous_state: str
    new_state: str
    created_at: str


# Forward ref resolution
WorkflowRun.model_rebuild()
