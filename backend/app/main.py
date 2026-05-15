from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .modules import Script, ScriptAIService, ScriptQualityReport, ScriptRepository, ScriptSection, ScriptState

app = FastAPI(title="QualityTube OS API")


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GenerateScriptRequest(BaseModel):
    angle_id: str = Field(min_length=1)
    angle_status: str = Field(min_length=1)
    allow_draft_without_approval: bool = False


class StructuredOutline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: str = Field(min_length=8)
    beats: list[str] = Field(min_length=3)
    cta: str = Field(min_length=8)


class GenerateOutlineResponse(BaseModel):
    script: Script
    outline: StructuredOutline


class GenerateDraftResponse(BaseModel):
    script: Script


class ListScriptsResponse(BaseModel):
    idea_id: str
    scripts: list[Script]


class UpdateScriptRequest(BaseModel):
    sections: list[ScriptSection] | None = None
    state: ScriptState | None = None
    editor_event: str = Field(default="manual-update", min_length=1)


class GateRule(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_overall_score: float = Field(default=7.0, ge=0.0, le=10.0)
    min_hook_score: float = Field(default=7.0, ge=0.0, le=10.0)
    banned_phrases: list[str] = Field(default_factory=lambda: ["guaranteed viral", "zero effort success"])


class ScoreRequest(BaseModel):
    quality_report: ScriptQualityReport


class ImproveRequest(BaseModel):
    editor_event: str = Field(default="ai-improve", min_length=1)


class ApproveRequest(BaseModel):
    gates: GateRule = Field(default_factory=GateRule)


class OverrideRequest(BaseModel):
    reason: str = Field(min_length=8)
    approver: str = Field(min_length=1)


class ApprovalResult(BaseModel):
    approved: bool
    state: ScriptState


class ScriptVersionListResponse(BaseModel):
    versions: list[Any]


class CompareVersionsResponse(BaseModel):
    from_revision: int
    to_revision: int
    changed_sections: list[str]

class GateFailed(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}


repo = ScriptRepository()
script_by_id: dict[UUID, Script] = {}
script_ai = ScriptAIService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _ensure_angle_gate(request: GenerateScriptRequest) -> None:
    approved_angle = request.angle_status.lower().strip() == "approved"
    if not approved_angle and not request.allow_draft_without_approval:
        raise HTTPException(
            status_code=409,
            detail=ErrorPayload(
                code="ANGLE_NOT_APPROVED",
                message="idea angle must be approved before script generation",
                details={"required_status": "approved", "received_status": request.angle_status},
            ).model_dump(),
        )


def _basic_sections() -> list[ScriptSection]:
    return [
        ScriptSection(title="hook", content="Hook: Here's the contrarian insight creators miss when scaling channels."),
        ScriptSection(title="body", content="Body: Start with audience pain, reveal pattern breaks, then support with concrete examples and specific steps."),
        ScriptSection(title="cta", content="CTA: Ask viewers to test one tactic today and report outcomes in comments."),
    ]


def _enforce_approval_gates(script: Script, gates: GateRule) -> None:
    if not script.sections:
        raise GateFailed("EMPTY_SCRIPT", "script content is empty")

    hook_sections = [section for section in script.sections if section.title.lower().strip() == "hook"]
    if not hook_sections or len(hook_sections[0].content.strip()) < 20:
        raise GateFailed("HOOK_UNCLEAR", "script hook is missing or unclear")

    content = " ".join(section.content.lower() for section in script.sections)
    blocked = [phrase for phrase in gates.banned_phrases if phrase.lower() in content]
    if blocked:
        raise GateFailed("BANNED_PHRASES", "script contains blocked phrases", {"blocked_phrases": blocked})

    if script.quality_report is None:
        raise GateFailed("MISSING_SCORE", "script must be scored before approval")

    report = script.quality_report
    if report.overall_script_score < gates.min_overall_score:
        raise GateFailed(
            "SCORE_BELOW_THRESHOLD",
            "overall score below approval threshold",
            {"metric": "overall_script_score", "required": gates.min_overall_score, "actual": report.overall_script_score},
        )

    if report.hook_score < gates.min_hook_score:
        raise GateFailed(
            "SCORE_BELOW_THRESHOLD",
            "hook score below approval threshold",
            {"metric": "hook_score", "required": gates.min_hook_score, "actual": report.hook_score},
        )


@app.post("/api/v1/ideas/{idea_id}/scripts/generate-outline", response_model=GenerateOutlineResponse)
def generate_outline(idea_id: str, payload: GenerateScriptRequest) -> GenerateOutlineResponse:
    _ensure_angle_gate(payload)
    outline_payload = script_ai.generate_outline(
        angle=payload.angle_id,
        channel_memory="channel-memory-placeholder",
        research_brief="research-brief-placeholder",
    )
    script = Script(
        idea_id=idea_id,
        angle_id=payload.angle_id,
        sections=[
            ScriptSection(title="hook", content=outline_payload.hook),
            ScriptSection(title="body", content=" ".join(outline_payload.beats)),
            ScriptSection(title="cta", content=outline_payload.cta),
        ],
    )
    repo.create_script(script, editor_event="generate-outline")
    script_by_id[script.id] = script
    outline = StructuredOutline(hook=outline_payload.hook, beats=outline_payload.beats, cta=outline_payload.cta)
    return GenerateOutlineResponse(script=script, outline=outline)


@app.post("/api/v1/ideas/{idea_id}/scripts/generate-draft", response_model=GenerateDraftResponse)
def generate_draft(idea_id: str, payload: GenerateScriptRequest) -> GenerateDraftResponse:
    _ensure_angle_gate(payload)
    outline_payload = script_ai.generate_outline(
        angle=payload.angle_id,
        channel_memory="channel-memory-placeholder",
        research_brief="research-brief-placeholder",
    )
    draft_payload = script_ai.generate_draft(
        angle=payload.angle_id,
        channel_memory="channel-memory-placeholder",
        research_brief="research-brief-placeholder",
        outline=outline_payload,
    )
    script = Script(idea_id=idea_id, angle_id=payload.angle_id, sections=draft_payload.sections)
    repo.create_script(script, editor_event="generate-draft")
    script_by_id[script.id] = script
    return GenerateDraftResponse(script=script)


@app.get("/api/v1/ideas/{idea_id}/scripts", response_model=ListScriptsResponse)
def list_idea_scripts(idea_id: str) -> ListScriptsResponse:
    script = repo.get_script(idea_id)
    return ListScriptsResponse(idea_id=idea_id, scripts=[script] if script else [])


@app.get("/api/v1/scripts/{script_id}", response_model=Script)
def get_script(script_id: UUID) -> Script:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    return script


@app.patch("/api/v1/scripts/{script_id}", response_model=Script)
def patch_script(script_id: UUID, payload: UpdateScriptRequest) -> Script:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    updates: dict[str, Any] = {}
    if payload.sections is not None:
        updates["sections"] = payload.sections
    if payload.state is not None:
        updates["state"] = payload.state
    updated = script.model_copy(update=updates)
    repo.revise_script(script.idea_id, updated, payload.editor_event)
    script_by_id[script_id] = updated
    return updated


@app.post("/api/v1/scripts/{script_id}/score", response_model=Script)
def score_script(script_id: UUID, payload: ScoreRequest) -> Script:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    score_payload = script_ai.score_script(
        angle=script.angle_id,
        channel_memory="channel-memory-placeholder",
        research_brief="research-brief-placeholder",
        sections=script.sections,
    )
    updated = script.model_copy(update={"quality_report": score_payload.quality_report})
    repo.revise_script(script.idea_id, updated, "score")
    script_by_id[script_id] = updated
    return updated


@app.post("/api/v1/scripts/{script_id}/improve", response_model=Script)
def improve_script(script_id: UUID, payload: ImproveRequest) -> Script:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    improved_payload = script_ai.improve_script(
        angle=script.angle_id,
        channel_memory="channel-memory-placeholder",
        research_brief="research-brief-placeholder",
        sections=script.sections,
    )
    updated = script.model_copy(update={"sections": improved_payload.sections})
    repo.revise_script(script.idea_id, updated, payload.editor_event)
    script_by_id[script_id] = updated
    return updated




@app.get("/api/v1/scripts/{script_id}/versions")
def list_script_versions(script_id: UUID) -> dict[str, Any]:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    versions = repo.get_versions(script_id)
    return {"versions": [version.model_dump(mode="json") for version in versions]}


@app.get("/api/v1/scripts/{script_id}/compare")
def compare_script_versions(script_id: UUID, from_revision: int, to_revision: int) -> CompareVersionsResponse:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    versions = {item.revision: item for item in repo.get_versions(script_id)}
    if from_revision not in versions or to_revision not in versions:
        raise HTTPException(
            status_code=404,
            detail=ErrorPayload(code="REVISION_NOT_FOUND", message="requested revision not found").model_dump(),
        )
    before = {section.title.lower(): section.content for section in versions[from_revision].script_snapshot.sections}
    after = {section.title.lower(): section.content for section in versions[to_revision].script_snapshot.sections}
    all_titles = sorted(set(before.keys()) | set(after.keys()))
    changed_sections = [title for title in all_titles if before.get(title) != after.get(title)]
    return CompareVersionsResponse(from_revision=from_revision, to_revision=to_revision, changed_sections=changed_sections)


@app.post("/api/v1/scripts/{script_id}/approve", response_model=ApprovalResult)
def approve_script(script_id: UUID, payload: ApproveRequest) -> ApprovalResult:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    try:
        _enforce_approval_gates(script, payload.gates)
    except GateFailed as exc:
        raise HTTPException(status_code=409, detail=ErrorPayload(code=exc.code, message=exc.message, details=exc.details).model_dump())
    approved = script.model_copy(update={"state": ScriptState.approved})
    repo.revise_script(script.idea_id, approved, "approve")
    script_by_id[script_id] = approved
    return ApprovalResult(approved=True, state=approved.state)


@app.post("/api/v1/scripts/{script_id}/override", response_model=ApprovalResult)
def override_script(script_id: UUID, payload: OverrideRequest) -> ApprovalResult:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    approved = script.model_copy(update={"state": ScriptState.approved})
    repo.revise_script(script.idea_id, approved, f"override:{payload.approver}")
    script_by_id[script_id] = approved
    return ApprovalResult(approved=True, state=approved.state)
