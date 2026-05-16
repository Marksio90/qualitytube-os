from __future__ import annotations

from datetime import UTC, datetime
import json
import time
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .modules import ApprovalState, ChannelMemory, ChannelMemoryRepository, ComplianceCheckInput, ComplianceRecommendation, ComplianceReport, HookVariant, LLMCall, PublishingPackage, PublishingPackageExportFormat, PublishingPackageExportService, PublishingPackageRepository, PublishingPackageStatus, PublishingPackageValidationService, PublishingValidationResult, RetentionReview, ReviewerSource, RiskLevel, Script, ScriptAIService, ScriptQualityReport, ScriptRepository, ScriptSection, ScriptState, ThumbnailConcept, TitleThumbnailLabRepository, TitleVariant, compliance_gate_failures, run_compliance_checks

app = FastAPI(title="QualityTube OS API")


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GenerateScriptRequest(BaseModel):
    angle_id: str = Field(min_length=1)
    angle_status: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
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
    channel_id: str = Field(default="default", min_length=1)


class ImproveRequest(BaseModel):
    channel_id: str = Field(default="default", min_length=1)
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



class GenerateHooksResponse(BaseModel):
    script_id: UUID
    hooks: list[HookVariant]


class ListHooksResponse(BaseModel):
    script_id: UUID
    hooks: list[HookVariant]


class ScoreHookResponse(BaseModel):
    hook: HookVariant


class SelectHookResponse(BaseModel):
    hook: HookVariant


class GenerateIdeaTitlesRequest(BaseModel):
    angle_status: str = Field(min_length=1)


class GenerateIdeaTitlesResponse(BaseModel):
    idea_id: str
    titles: list[TitleVariant]


class ScoreTitleRequest(BaseModel):
    clarity_score: float = Field(ge=0.0, le=10.0)
    curiosity_score: float = Field(ge=0.0, le=10.0)
    truthfulness_score: float = Field(ge=0.0, le=10.0)
    promise_match_score: float = Field(ge=0.0, le=10.0)
    clickbait_risk: float = Field(ge=0.0, le=10.0)
    rationale: str | None = None
    warnings: str | None = None


class ScoreTitleResponse(BaseModel):
    title: TitleVariant


class SelectTitleResponse(BaseModel):
    title: TitleVariant


class ListTitlesResponse(BaseModel):
    idea_id: str
    titles: list[TitleVariant]


class GenerateThumbnailBriefsRequest(BaseModel):
    angle_status: str = Field(min_length=1)


class GenerateThumbnailBriefsResponse(BaseModel):
    idea_id: str
    thumbnails: list[ThumbnailConcept]


class SelectThumbnailResponse(BaseModel):
    thumbnail: ThumbnailConcept


class ListThumbnailsResponse(BaseModel):
    idea_id: str
    thumbnails: list[ThumbnailConcept]


class AnalyzeRetentionResponse(BaseModel):
    script_id: UUID
    review: RetentionReview


class LatestRetentionResponse(BaseModel):
    script_id: UUID
    review: RetentionReview


class ComplianceReviewRequest(BaseModel):
    channel_id: str = Field(default="default", min_length=1)


class ComplianceReportResponse(BaseModel):
    report: ComplianceReport


class ComplianceReportListResponse(BaseModel):
    idea_id: str
    reports: list[ComplianceReport]


class ComplianceApprovalRequest(BaseModel):
    approver: str = Field(min_length=1)


class ComplianceOverrideRequest(BaseModel):
    reason: str = Field(min_length=12)
    approver: str = Field(min_length=1)
    outcome_recommendation: ComplianceRecommendation
    outcome_overall_risk: RiskLevel

class GateFailed(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.details = details or {}


repo = ScriptRepository()
script_by_id: dict[UUID, Script] = {}
channel_memory_repo = ChannelMemoryRepository()
script_ai = ScriptAIService()
compliance_reports_by_idea: dict[str, list[ComplianceReport]] = {}
compliance_reports_by_id: dict[UUID, ComplianceReport] = {}
publishing_repo = PublishingPackageRepository()
title_thumbnail_repo = TitleThumbnailLabRepository()


# Seed sample memory for local/dev flows.
channel_memory_repo.upsert(ChannelMemory(channel_id="default", tone_notes=["pragmatic", "specific"], banned_claims=["instant guaranteed growth"]))


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








def _risk_from_bool(flag: bool) -> RiskLevel:
    return RiskLevel.high if flag else RiskLevel.low


def _run_deterministic_compliance_checks(idea_id: str) -> dict[str, Any]:
    script = repo.get_script(idea_id)
    joined = " ".join(section.content for section in script.sections) if script else ""
    result = run_compliance_checks(
        ComplianceCheckInput(
            script_present=script is not None,
            script_text=joined,
            synthetic_disclosure_present="synthetic disclosure" in joined.lower(),
            human_contribution_evidence_present="edited by" in joined.lower() or "human review" in joined.lower(),
        )
    )
    return result.as_dict()


def _ai_assisted_compliance_review(*, idea_id: str, deterministic: dict[str, Any], channel_id: str) -> dict[str, Any]:
    prompt = (
        "Produce strict JSON for compliance review. "
        f"idea_id={idea_id}; channel_id={channel_id}; deterministic={json.dumps(deterministic)}; "
        "schema={reused_content_risk,repetitive_content_risk,mass_production_risk,synthetic_content_disclosure_required,"
        "copyright_risk,misleading_claims_risk,sensitive_topic_risk,clickbait_risk,originality_evidence,human_contribution_evidence,"
        "overall_risk,recommendation,required_fixes,reviewer_notes}."
    )
    correlation_id = str(uuid4())
    started = time.perf_counter()
    raw = script_ai.provider.generate(prompt)
    latency_ms = int((time.perf_counter() - started) * 1000)
    script_ai.logger.log(
        LLMCall(
            provider=type(script_ai.provider).__name__,
            model=getattr(script_ai.provider, "model", "mock-model"),
            operation="compliance_review",
            prompt=prompt,
            response=raw,
            prompt_chars=len(prompt),
            response_chars=len(raw),
            prompt_tokens=max(1, len(prompt) // 4),
            completion_tokens=max(1, len(raw) // 4),
            latency_ms=latency_ms,
            correlation_id=correlation_id,
        )
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _persist_compliance_report(report: ComplianceReport) -> ComplianceReport:
    compliance_reports_by_idea.setdefault(report.idea_id, []).append(report)
    compliance_reports_by_idea[report.idea_id].sort(key=lambda item: item.created_at)
    compliance_reports_by_id[report.id] = report
    return report

def _api_error(status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> HTTPException:
    return HTTPException(status_code=status_code, detail=ErrorPayload(code=code, message=message, details=details or {}).model_dump())


def _resolve_channel_memory_or_424(channel_id: str) -> ChannelMemory:
    memory = channel_memory_repo.get(channel_id)
    if memory is None:
        raise _api_error(424, "CHANNEL_MEMORY_NOT_FOUND", "channel memory dependency missing", {"channel_id": channel_id})
    return memory


def _build_channel_memory_context(memory: ChannelMemory) -> str:
    return f"channel_id={memory.channel_id}; tone_notes={memory.tone_notes}; banned_claims={memory.banned_claims}"


def _build_script_context(script: Script) -> str:
    section_map = [{"title": section.title, "content": section.content} for section in script.sections]
    return f"script_id={script.id}; sections={section_map}"


def _build_script_studio_context(*, channel_id: str, script: Script | None = None) -> tuple[str, str]:
    memory = _resolve_channel_memory_or_424(channel_id)
    channel_context = _build_channel_memory_context(memory)
    script_context = _build_script_context(script) if script is not None else "script=none"
    return channel_context, script_context


def _get_script_or_404(script_id: UUID) -> Script:
    script = script_by_id.get(script_id)
    if script is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="SCRIPT_NOT_FOUND", message="script not found").model_dump())
    return script


def _approved_script_or_409(idea_id: str) -> Script:
    script = repo.get_script(idea_id)
    if script is None or script.state != ScriptState.approved:
        details: dict[str, Any] = {"idea_id": idea_id}
        if script is not None:
            details["script_state"] = script.state.value
        raise _api_error(409, "SCRIPT_APPROVAL_REQUIRED", "approved script is required before this operation", details)
    return script



def _latest_compliance_report_or_409(idea_id: str) -> ComplianceReport:
    reports = compliance_reports_by_idea.get(idea_id, [])
    if not reports:
        raise _api_error(409, "COMPLIANCE_REPORT_REQUIRED", "latest compliance report is required before marking ready_to_publish", {"idea_id": idea_id})
    return reports[-1]


def _enforce_ready_to_publish_compliance(idea_id: str) -> None:
    latest_report = _latest_compliance_report_or_409(idea_id)
    failures = compliance_gate_failures(report=latest_report, required_fixes_resolved=not bool(latest_report.required_fixes))
    if failures:
        raise _api_error(409, "READY_TO_PUBLISH_BLOCKED", "ready_to_publish blocked by compliance preconditions", {"idea_id": idea_id, "report_id": str(latest_report.id), "failures": failures})

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


class PublishingPackageGenerateRequest(BaseModel):
    angle_status: str = Field(min_length=1)


class PublishingPackageUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    chapters: list[str] | None = None
    pinned_comment: str | None = None
    thumbnail_brief: str | None = None
    disclosure_notes: str | None = None
    source_notes: str | None = None
    upload_checklist: list[str] | None = None


class PublishingPackageApproveRequest(BaseModel):
    angle_status: str = Field(min_length=1)


class PublishingPackageValidationResponse(BaseModel):
    result: PublishingValidationResult


class PublishingPackageExportRequest(BaseModel):
    format: str = Field(min_length=1)


class PublishingPackageExportResponse(BaseModel):
    format: str
    content: str | dict[str, Any]


class PublishingPackageService:
    def __init__(self, repository: PublishingPackageRepository) -> None:
        self.repository = repository
        self.validation_service = PublishingPackageValidationService()

    def _latest_script_or_409(self, idea_id: str) -> Script:
        script = repo.get_script(idea_id)
        if script is None:
            raise _api_error(409, "SCRIPT_APPROVAL_REQUIRED", "approved script is required before publishing package operations", {"idea_id": idea_id})
        if script.state != ScriptState.approved:
            raise _api_error(409, "SCRIPT_APPROVAL_REQUIRED", "approved script is required before publishing package operations", {"idea_id": idea_id, "script_state": script.state.value})
        return script

    def _approved_compliance_or_409(self, idea_id: str) -> ComplianceReport:
        report = _latest_compliance_report_or_409(idea_id)
        if report.approval_state != ApprovalState.approved:
            raise _api_error(409, "COMPLIANCE_APPROVAL_REQUIRED", "approved compliance report is required", {"idea_id": idea_id, "report_id": str(report.id)})
        return report

    def _assert_angle_approved(self, angle_status: str) -> None:
        if angle_status.lower().strip() != "approved":
            raise _api_error(409, "ANGLE_NOT_APPROVED", "approved angle is required", {"required_status": "approved", "received_status": angle_status})

    def generate(self, idea_id: str, angle_status: str) -> PublishingPackage:
        self._assert_angle_approved(angle_status)
        script = self._latest_script_or_409(idea_id)
        report = self._approved_compliance_or_409(idea_id)
        generated = script_ai.generate_publishing_package(
            approved_angle=script.angle_id,
            approved_script_sections=script.sections,
            compliance_report=report,
        )
        package = PublishingPackage(
            idea_id=idea_id,
            title=generated.title,
            description=generated.description,
            tags=generated.tags,
            chapters=generated.chapters,
            pinned_comment=generated.pinned_comment,
            thumbnail_brief=generated.thumbnail_brief,
            disclosure_notes=generated.disclosure_notes,
            source_notes=generated.source_notes,
            upload_checklist=generated.upload_checklist,
            latest_compliance=report,
            status=PublishingPackageStatus.ready_for_review,
        )
        try:
            return self.repository.create_package(package, editor_event="generate")
        except ValueError as exc:
            raise _api_error(409, "PUBLISHING_PACKAGE_EXISTS", "publishing package already exists for idea", {"idea_id": idea_id}) from exc

    def validate(self, idea_id: str, angle_status: str) -> PublishingValidationResult:
        self._assert_angle_approved(angle_status)
        script = self._latest_script_or_409(idea_id)
        report = self._approved_compliance_or_409(idea_id)
        package = self.repository.get_package(idea_id)
        if package is None:
            raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"idea_id": idea_id})
        return self.validation_service.validate(
            package=package,
            script=script,
            compliance_overall_risk=report.overall_risk,
            synthetic_disclosure_required=report.synthetic_content_disclosure_required,
        )

    def approve(self, idea_id: str, angle_status: str) -> PublishingPackage:
        validation_result = self.validate(idea_id, angle_status)
        if not validation_result.eligible_for_approval:
            raise _api_error(
                409,
                "PUBLISHING_APPROVAL_BLOCKED",
                "cannot approve publishing package until validation passes",
                {"idea_id": idea_id, "errors": [error.model_dump() for error in validation_result.errors]},
            )
        report = self._approved_compliance_or_409(idea_id)
        existing = self.repository.get_package(idea_id)
        if existing is None:
            raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"idea_id": idea_id})
        updated = existing.model_copy(update={"status": PublishingPackageStatus.approved, "latest_compliance": report})
        self.repository.revise_package(idea_id, updated, "approve")
        return updated


publishing_service = PublishingPackageService(publishing_repo)
publishing_export_service = PublishingPackageExportService()


@app.post("/api/v1/ideas/{idea_id}/scripts/generate-outline", response_model=GenerateOutlineResponse)
def generate_outline(idea_id: str, payload: GenerateScriptRequest) -> GenerateOutlineResponse:
    _ensure_angle_gate(payload)
    channel_context, upstream_script_context = _build_script_studio_context(channel_id=payload.channel_id)
    outline_payload = script_ai.generate_outline(
        angle=payload.angle_id,
        channel_memory=channel_context,
        research_brief=upstream_script_context,
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
    channel_context, upstream_script_context = _build_script_studio_context(channel_id=payload.channel_id)
    outline_payload = script_ai.generate_outline(
        angle=payload.angle_id,
        channel_memory=channel_context,
        research_brief=upstream_script_context,
    )
    draft_payload = script_ai.generate_draft(
        angle=payload.angle_id,
        channel_memory=_build_script_studio_context(channel_id=payload.channel_id)[0],
        research_brief=_build_script_studio_context(channel_id=payload.channel_id)[1],
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
        if payload.state == ScriptState.ready_to_publish:
            _enforce_ready_to_publish_compliance(script.idea_id)
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
    channel_context, script_context = _build_script_studio_context(channel_id=payload.channel_id, script=script)
    score_payload = script_ai.score_script(
        angle=script.angle_id,
        channel_memory=channel_context,
        research_brief=script_context,
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
    channel_context, script_context = _build_script_studio_context(channel_id=payload.channel_id, script=script)
    improved_payload = script_ai.improve_script(
        angle=script.angle_id,
        channel_memory=channel_context,
        research_brief=script_context,
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


@app.post("/api/v1/scripts/{script_id}/hooks/generate", response_model=GenerateHooksResponse)
def generate_hooks(script_id: UUID) -> GenerateHooksResponse:
    script = _get_script_or_404(script_id)
    channel_context, _ = _build_script_studio_context(channel_id="default", script=script)
    generated = script_ai.generate_hooks(angle=script.angle_id, channel_memory=channel_context, sections=script.sections)
    hooks = list(repo.create_hook_variants(script_id, generated.variants))
    return GenerateHooksResponse(script_id=script_id, hooks=hooks)


@app.get("/api/v1/scripts/{script_id}/hooks", response_model=ListHooksResponse)
def list_hooks(script_id: UUID) -> ListHooksResponse:
    _get_script_or_404(script_id)
    return ListHooksResponse(script_id=script_id, hooks=list(repo.list_hooks(script_id)))


@app.post("/api/v1/hooks/{hook_id}/score", response_model=ScoreHookResponse)
def score_hook(hook_id: UUID) -> ScoreHookResponse:
    for script_id, script in script_by_id.items():
        for hook in repo.list_hooks(script_id):
            if hook.id == hook_id:
                channel_context, _ = _build_script_studio_context(channel_id="default", script=script)
                rescored = script_ai.score_hook(angle=script.angle_id, channel_memory=channel_context, hook_text=hook.text, script_sections=script.sections)
                hook.score = rescored.score
                hook.notes = rescored.notes
                hook.risk_level = rescored.risk_level
                return ScoreHookResponse(hook=hook)
    raise HTTPException(status_code=404, detail=ErrorPayload(code="HOOK_NOT_FOUND", message="hook not found").model_dump())


@app.post("/api/v1/hooks/{hook_id}/select", response_model=SelectHookResponse)
def select_hook(hook_id: UUID) -> SelectHookResponse:
    try:
        hook = repo.select_hook(hook_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="HOOK_NOT_FOUND", message="hook not found").model_dump()) from exc
    return SelectHookResponse(hook=hook)


@app.post("/api/v1/ideas/{idea_id}/titles/generate", response_model=GenerateIdeaTitlesResponse)
def generate_titles(idea_id: str, payload: GenerateIdeaTitlesRequest) -> GenerateIdeaTitlesResponse:
    _ensure_angle_gate(
        GenerateScriptRequest(angle_id="approved-angle", angle_status=payload.angle_status, channel_id="default", allow_draft_without_approval=False)
    )
    script = _approved_script_or_409(idea_id)
    body_text = " ".join(section.content for section in script.sections)
    base = body_text[:70] if body_text else "High-impact creator system"
    generated = [
        TitleVariant(
            idea_id=idea_id,
            title_text=f"{base} — Practical breakdown",
            clarity_score=8.2,
            curiosity_score=7.9,
            truthfulness_score=8.6,
            promise_match_score=8.1,
            clickbait_risk=2.1,
            overall_title_score=8.2,
            rationale="Aligned with script promise and concrete takeaway.",
        ),
        TitleVariant(
            idea_id=idea_id,
            title_text=f"What most creators miss about {base[:40]}",
            clarity_score=7.7,
            curiosity_score=8.5,
            truthfulness_score=8.1,
            promise_match_score=7.8,
            clickbait_risk=2.8,
            overall_title_score=8.0,
            rationale="Raises a strong gap while staying truthful.",
        ),
    ]
    created = [title_thumbnail_repo.create_title_variant(item) for item in generated]
    return GenerateIdeaTitlesResponse(idea_id=idea_id, titles=created)


@app.post("/api/v1/titles/{title_id}/score", response_model=ScoreTitleResponse)
def score_title(title_id: UUID, payload: ScoreTitleRequest) -> ScoreTitleResponse:
    for idea_titles in (title_thumbnail_repo.list_title_variants(idea_id) for idea_id in {s.idea_id for s in script_by_id.values()}):
        for title in idea_titles:
            if title.id == title_id:
                overall = (payload.clarity_score + payload.curiosity_score + payload.truthfulness_score + payload.promise_match_score + (10 - payload.clickbait_risk)) / 5
                updated = title.model_copy(update={**payload.model_dump(), "overall_title_score": round(overall, 2)})
                title_thumbnail_repo.update_title_variant(updated)
                return ScoreTitleResponse(title=updated)
    raise _api_error(404, "TITLE_NOT_FOUND", "title not found", {"title_id": str(title_id)})


@app.post("/api/v1/titles/{title_id}/select", response_model=SelectTitleResponse)
def select_title(title_id: UUID) -> SelectTitleResponse:
    for idea_id in {script.idea_id for script in script_by_id.values()}:
        try:
            selected = title_thumbnail_repo.select_title_variant(idea_id, title_id)
            return SelectTitleResponse(title=selected)
        except KeyError:
            continue
    raise _api_error(404, "TITLE_NOT_FOUND", "title not found", {"title_id": str(title_id)})


@app.get("/api/v1/ideas/{idea_id}/titles", response_model=ListTitlesResponse)
def list_titles(idea_id: str) -> ListTitlesResponse:
    return ListTitlesResponse(idea_id=idea_id, titles=list(title_thumbnail_repo.list_title_variants(idea_id)))


@app.post("/api/v1/ideas/{idea_id}/thumbnails/generate-briefs", response_model=GenerateThumbnailBriefsResponse)
def generate_thumbnail_briefs(idea_id: str, payload: GenerateThumbnailBriefsRequest) -> GenerateThumbnailBriefsResponse:
    _ensure_angle_gate(
        GenerateScriptRequest(angle_id="approved-angle", angle_status=payload.angle_status, channel_id="default", allow_draft_without_approval=False)
    )
    _approved_script_or_409(idea_id)
    concepts = [
        ThumbnailConcept(
            idea_id=idea_id,
            main_object="Creator dashboard with steep growth line",
            emotion="Urgency with confidence",
            composition="Subject on right third, graph spike on left, bold contrast lighting",
            text_overlay="STOP Guessing",
            visual_contrast="Neon green graph against dark blue background",
            mobile_readability_notes="Keep overlay to two short words, 12% top margin",
            avoid="No tiny text, no cluttered analytics tables",
            score=8.4,
        ),
        ThumbnailConcept(
            idea_id=idea_id,
            main_object="Before/after channel performance split",
            emotion="Surprise",
            composition="Vertical split with dramatic expression and metrics badge",
            text_overlay="Before / After",
            visual_contrast="Warm red left side, cool teal right side",
            mobile_readability_notes="Large face crop with high edge contrast",
            avoid="No more than one badge and one arrow",
            score=8.1,
        ),
    ]
    created = [title_thumbnail_repo.create_thumbnail_concept(item) for item in concepts]
    return GenerateThumbnailBriefsResponse(idea_id=idea_id, thumbnails=created)


@app.post("/api/v1/thumbnails/{thumbnail_id}/select", response_model=SelectThumbnailResponse)
def select_thumbnail(thumbnail_id: UUID) -> SelectThumbnailResponse:
    for idea_id in {script.idea_id for script in script_by_id.values()}:
        try:
            selected = title_thumbnail_repo.select_thumbnail_concept(idea_id, thumbnail_id)
            return SelectThumbnailResponse(thumbnail=selected)
        except KeyError:
            continue
    raise _api_error(404, "THUMBNAIL_NOT_FOUND", "thumbnail not found", {"thumbnail_id": str(thumbnail_id)})


@app.get("/api/v1/ideas/{idea_id}/thumbnails", response_model=ListThumbnailsResponse)
def list_thumbnails(idea_id: str) -> ListThumbnailsResponse:
    return ListThumbnailsResponse(idea_id=idea_id, thumbnails=list(title_thumbnail_repo.list_thumbnail_concepts(idea_id)))


@app.post("/api/v1/scripts/{script_id}/retention/analyze", response_model=AnalyzeRetentionResponse)
def analyze_retention(script_id: UUID) -> AnalyzeRetentionResponse:
    script = _get_script_or_404(script_id)
    channel_context, _ = _build_script_studio_context(channel_id="default", script=script)
    analysis = script_ai.analyze_retention(angle=script.angle_id, channel_memory=channel_context, sections=script.sections)
    review = repo.save_retention_review(script_id, analysis.review)
    return AnalyzeRetentionResponse(script_id=script_id, review=review)


@app.get("/api/v1/scripts/{script_id}/retention/latest", response_model=LatestRetentionResponse)
def get_latest_retention(script_id: UUID) -> LatestRetentionResponse:
    _get_script_or_404(script_id)
    review = repo.get_latest_retention_review(script_id)
    if review is None:
        raise HTTPException(status_code=404, detail=ErrorPayload(code="RETENTION_REVIEW_NOT_FOUND", message="no retention review found for script").model_dump())
    return LatestRetentionResponse(script_id=script_id, review=review)


@app.post("/api/v1/ideas/{idea_id}/compliance/review", response_model=ComplianceReportResponse)
@app.post("/ideas/{idea_id}/compliance/review", response_model=ComplianceReportResponse)
def review_compliance(idea_id: str, payload: ComplianceReviewRequest) -> ComplianceReportResponse:
    deterministic = _run_deterministic_compliance_checks(idea_id)
    ai_result = _ai_assisted_compliance_review(idea_id=idea_id, deterministic=deterministic, channel_id=payload.channel_id)
    report = ComplianceReport(
        idea_id=idea_id,
        reused_content_risk=_risk_from_bool(bool(deterministic["reused_content_signals"])),
        repetitive_content_risk=_risk_from_bool(bool(deterministic["repetitive_structure_signals"])),
        mass_production_risk=_risk_from_bool(bool(deterministic["mass_production_indicators"])),
        synthetic_content_disclosure_required=bool(deterministic["synthetic_disclosure_required"]),
        copyright_risk=RiskLevel.low,
        misleading_claims_risk=_risk_from_bool(bool(deterministic["clickbait_or_misleading_claim_signals"])),
        sensitive_topic_risk=_risk_from_bool(bool(deterministic["sensitive_topic_flags"])),
        clickbait_risk=_risk_from_bool(bool(deterministic["clickbait_or_misleading_claim_signals"])),
        originality_evidence=ai_result.get("originality_evidence", ["Deterministic+AI review completed"]),
        human_contribution_evidence=ai_result.get("human_contribution_evidence", ["Human editorial checkpoints recorded"]),
        overall_risk=RiskLevel.high if any(bool(value) for value in deterministic.values()) else RiskLevel.low,
        recommendation=ComplianceRecommendation.high_risk if any(bool(value) for value in deterministic.values()) else ComplianceRecommendation.approve,
        required_fixes=ai_result.get("required_fixes", ["Address flagged deterministic risks"] if any(bool(value) for value in deterministic.values()) else []),
        reviewer_notes=ai_result.get("reviewer_notes", "Deterministic checks executed before AI-assisted pass."),
        reviewer_source=ReviewerSource.ai_assisted,
    )
    persisted = _persist_compliance_report(report)
    return ComplianceReportResponse(report=persisted)


@app.get("/api/v1/ideas/{idea_id}/compliance/latest", response_model=ComplianceReportResponse)
@app.get("/ideas/{idea_id}/compliance/latest", response_model=ComplianceReportResponse)
def get_latest_compliance_report(idea_id: str) -> ComplianceReportResponse:
    reports = compliance_reports_by_idea.get(idea_id, [])
    if not reports:
        raise _api_error(404, "COMPLIANCE_REPORT_NOT_FOUND", "no compliance report found for idea", {"idea_id": idea_id})
    return ComplianceReportResponse(report=max(reports, key=lambda r: r.created_at))


@app.get("/api/v1/ideas/{idea_id}/compliance/reports", response_model=ComplianceReportListResponse)
@app.get("/ideas/{idea_id}/compliance/reports", response_model=ComplianceReportListResponse)
def list_compliance_reports(idea_id: str) -> ComplianceReportListResponse:
    reports = sorted(compliance_reports_by_idea.get(idea_id, []), key=lambda r: r.created_at)
    return ComplianceReportListResponse(idea_id=idea_id, reports=reports)


@app.post("/api/v1/compliance/{report_id}/approve", response_model=ComplianceReportResponse)
@app.post("/compliance/{report_id}/approve", response_model=ComplianceReportResponse)
def approve_compliance_report(report_id: UUID, payload: ComplianceApprovalRequest) -> ComplianceReportResponse:
    report = compliance_reports_by_id.get(report_id)
    if report is None:
        raise _api_error(404, "COMPLIANCE_REPORT_NOT_FOUND", "compliance report not found", {"report_id": str(report_id)})
    failures = compliance_gate_failures(report=report, required_fixes_resolved=False)
    if failures:
        raise _api_error(409, "COMPLIANCE_BLOCKED", "blocking compliance conditions must be resolved before approval", {"report_id": str(report_id), "failures": failures})
    updated = report.model_copy(update={"approval_state": ApprovalState.approved, "updated_at": datetime.now(UTC), "reviewer_notes": f"{report.reviewer_notes} Approved by {payload.approver}.".strip()})
    compliance_reports_by_id[report_id] = updated
    compliance_reports_by_idea[updated.idea_id] = [updated if item.id == report_id else item for item in compliance_reports_by_idea.get(updated.idea_id, [])]
    return ComplianceReportResponse(report=updated)


@app.post("/api/v1/ideas/{idea_id}/publishing-package", response_model=PublishingPackage)
def generate_publishing_package(idea_id: str, payload: PublishingPackageGenerateRequest) -> PublishingPackage:
    return publishing_service.generate(idea_id, payload.angle_status)


@app.get("/api/v1/ideas/{idea_id}/publishing-package", response_model=PublishingPackage)
def get_publishing_package(idea_id: str) -> PublishingPackage:
    package = publishing_repo.get_package(idea_id)
    if package is None:
        raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"idea_id": idea_id})
    return package


@app.patch("/api/v1/ideas/{idea_id}/publishing-package", response_model=PublishingPackage)
def update_publishing_package(idea_id: str, payload: PublishingPackageUpdateRequest) -> PublishingPackage:
    existing = publishing_repo.get_package(idea_id)
    if existing is None:
        raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"idea_id": idea_id})
    updates = payload.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=updates)
    publishing_repo.revise_package(idea_id, updated, "manual-update")
    return updated


@app.post("/api/v1/ideas/{idea_id}/publishing-package/validate", response_model=PublishingPackageValidationResponse)
def validate_publishing_package(idea_id: str, payload: PublishingPackageApproveRequest) -> PublishingPackageValidationResponse:
    return PublishingPackageValidationResponse(result=publishing_service.validate(idea_id, payload.angle_status))


@app.post("/api/v1/ideas/{idea_id}/publishing-package/approve", response_model=PublishingPackage)
def approve_publishing_package(idea_id: str, payload: PublishingPackageApproveRequest) -> PublishingPackage:
    return publishing_service.approve(idea_id, payload.angle_status)


@app.get("/api/v1/ideas/{idea_id}/publishing-package/revisions")
def list_publishing_package_revisions(idea_id: str) -> dict[str, Any]:
    package = publishing_repo.get_package(idea_id)
    if package is None:
        raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"idea_id": idea_id})
    revisions = publishing_repo.get_revisions(package.id)
    return {"revisions": [revision.model_dump(mode="json") for revision in revisions]}


@app.post("/api/v1/publishing-packages/{package_id}/export", response_model=PublishingPackageExportResponse)
def export_publishing_package(package_id: UUID, payload: PublishingPackageExportRequest) -> PublishingPackageExportResponse:
    package = publishing_repo.get_package_by_id(package_id)
    if package is None:
        raise _api_error(404, "PUBLISHING_PACKAGE_NOT_FOUND", "publishing package not found", {"package_id": str(package_id)})

    requested = payload.format.strip().lower()
    try:
        export_format = PublishingPackageExportFormat(requested)
    except ValueError as exc:
        raise _api_error(
            422,
            "UNSUPPORTED_EXPORT_FORMAT",
            "unsupported export format",
            {"received_format": requested, "supported_formats": [fmt.value for fmt in PublishingPackageExportFormat]},
        ) from exc

    content = publishing_export_service.export(package, export_format)
    return PublishingPackageExportResponse(format=export_format.value, content=content)


@app.post("/api/v1/compliance/{report_id}/override", response_model=ComplianceReportResponse)
@app.post("/compliance/{report_id}/override", response_model=ComplianceReportResponse)
def override_compliance_report(report_id: UUID, payload: ComplianceOverrideRequest) -> ComplianceReportResponse:
    report = compliance_reports_by_id.get(report_id)
    if report is None:
        raise _api_error(404, "COMPLIANCE_REPORT_NOT_FOUND", "compliance report not found", {"report_id": str(report_id)})
    reason = payload.reason.strip()
    approver = payload.approver.strip()
    if len(reason) < 12:
        raise _api_error(422, "OVERRIDE_REASON_REQUIRED", "override reason is required")
    if not approver:
        raise _api_error(422, "OVERRIDE_APPROVER_REQUIRED", "override approver identity is required")
    timestamp = datetime.now(UTC)
    audit_entry = {
        "timestamp": timestamp,
        "approver": approver,
        "reason": reason,
        "previous_recommendation": report.recommendation,
        "previous_overall_risk": report.overall_risk,
        "overridden_recommendation": payload.outcome_recommendation,
        "overridden_overall_risk": payload.outcome_overall_risk,
    }
    updated = report.model_copy(
        update={
            "approval_state": ApprovalState.overridden,
            "override_reason": reason,
            "override_actor": approver,
            "override_recommendation": payload.outcome_recommendation,
            "override_overall_risk": payload.outcome_overall_risk,
            "is_manually_overridden": True,
            "override_audit_log": [*report.override_audit_log, audit_entry],
            "reviewer_source": ReviewerSource.human_override,
            "updated_at": timestamp,
        }
    )
    compliance_reports_by_id[report_id] = updated
    compliance_reports_by_idea[updated.idea_id] = [updated if item.id == report_id else item for item in compliance_reports_by_idea.get(updated.idea_id, [])]
    return ComplianceReportResponse(report=updated)
