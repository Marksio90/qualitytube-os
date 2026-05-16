from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, ValidationError

from .ai_provider import AIProvider, MockProvider
from .compliance import ComplianceRecommendation, ComplianceReport, RiskLevel
from .llm_logging import LLMCall, LLMCallLogger
from .scripts import HookVariantType, RetentionReview, ScriptQualityReport, ScriptSection


class OutlinePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hook: str
    beats: list[str]
    cta: str


class DraftPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[ScriptSection]


class ScorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quality_report: ScriptQualityReport


class ImprovementPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sections: list[ScriptSection]


class HookVariantsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variants: list["HookVariantCreatePayload"]


class HookVariantCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: HookVariantType
    text: str
    promise: str
    curiosity_gap: str
    risk_level: int
    score: float
    notes: str
    selected: bool


class HookScorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float
    notes: str
    risk_level: int


class RetentionAnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review: RetentionReview


class ComplianceReviewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reused_content_risk: RiskLevel
    repetitive_content_risk: RiskLevel
    mass_production_risk: RiskLevel
    synthetic_content_disclosure_required: bool
    copyright_risk: RiskLevel
    misleading_claims_risk: RiskLevel
    sensitive_topic_risk: RiskLevel
    clickbait_risk: RiskLevel
    overall_risk: RiskLevel
    recommendation: ComplianceRecommendation
    required_fixes: list[str]
    reviewer_notes: str


class PublishingPackagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    tags: list[str]
    chapters: list[str]
    pinned_comment: str | None = None
    thumbnail_brief: str
    disclosure_notes: str | None = None
    source_notes: str | None = None
    upload_checklist: list[str]
    promise_alignment_notes: list[str]


class ScriptAIService:
    _COMPLIANCE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "prompts" / "compliance-review.md"
    _PUBLISHING_PACKAGE_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "prompts" / "publishing-package-generation.md"

    def __init__(self, provider: AIProvider | None = None, logger: LLMCallLogger | None = None) -> None:
        self.provider = provider or MockProvider()
        self.logger = logger or LLMCallLogger()

    def _call(self, *, prompt: str, operation: str) -> str:
        correlation_id = str(uuid4())
        started = time.perf_counter()
        response = self.provider.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.logger.log(
            LLMCall(
                provider=type(self.provider).__name__,
                model=getattr(self.provider, "model", "mock-model"),
                prompt=prompt,
                response=response,
                prompt_chars=len(prompt),
                response_chars=len(response),
                prompt_tokens=max(1, len(prompt) // 4),
                completion_tokens=max(1, len(response) // 4),
                latency_ms=latency_ms,
                correlation_id=correlation_id,
                operation=operation,
            )
        )
        return response

    @staticmethod
    def _parse_strict_json(raw: str, schema: type[BaseModel]) -> BaseModel:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON returned by model: {exc}") from exc
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"model JSON did not match schema: {exc}") from exc

    def generate_outline(self, *, angle: str, channel_memory: str, research_brief: str) -> OutlinePayload:
        prompt = f"""Generate a script outline in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nResearch brief: {research_brief}\nReject generic intros and spammy CTAs.\nSchema: {{\"hook\": string, \"beats\": string[>=3], \"cta\": string}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="outline_generation"), OutlinePayload)
        return parsed  # type: ignore[return-value]

    def generate_draft(self, *, angle: str, channel_memory: str, research_brief: str, outline: OutlinePayload) -> DraftPayload:
        prompt = f"""Generate a script draft in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nResearch brief: {research_brief}\nOutline: {outline.model_dump_json()}\nReject generic intros and spammy CTAs.\nSchema: {{\"sections\": [{{\"title\": string, \"content\": string}}]}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="draft_generation"), DraftPayload)
        return parsed  # type: ignore[return-value]

    def score_script(self, *, angle: str, channel_memory: str, research_brief: str, sections: list[ScriptSection]) -> ScorePayload:
        prompt = f"""Score this script in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nResearch brief: {research_brief}\nSections: {json.dumps([s.model_dump() for s in sections])}\nReject generic intros and spammy CTAs.\nSchema: {{\"quality_report\": {{scores 0-10 for hook_score, clarity_score, narrative_tension_score, originality_score, retention_score, evidence_score, human_voice_score, cta_quality_score, overall_script_score}}}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="script_scoring"), ScorePayload)
        return parsed  # type: ignore[return-value]

    def improve_script(self, *, angle: str, channel_memory: str, research_brief: str, sections: list[ScriptSection]) -> ImprovementPayload:
        prompt = f"""Improve this script in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nResearch brief: {research_brief}\nSections: {json.dumps([s.model_dump() for s in sections])}\nReject generic intros and spammy CTAs.\nSchema: {{\"sections\": [{{\"title\": string, \"content\": string}}]}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="script_improvement"), ImprovementPayload)
        return parsed  # type: ignore[return-value]

    def generate_hooks(self, *, angle: str, channel_memory: str, sections: list[ScriptSection]) -> HookVariantsPayload:
        prompt = f"""Generate hook variants in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nScript sections: {json.dumps([s.model_dump() for s in sections])}\nSchema: {{\"variants\": [{{\"type\": \"contradiction|shock|question|story|mistake|before_after|hidden_mechanism\", \"text\": string, \"promise\": string, \"curiosity_gap\": string, \"risk_level\": int 0-5, \"score\": float 0-10, \"notes\": string, \"selected\": bool}}]}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="hook_generation"), HookVariantsPayload)
        return parsed  # type: ignore[return-value]

    def score_hook(self, *, angle: str, channel_memory: str, hook_text: str, script_sections: list[ScriptSection]) -> HookScorePayload:
        prompt = f"""Score this hook in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nHook text: {hook_text}\nScript sections: {json.dumps([s.model_dump() for s in script_sections])}\nSchema: {{\"score\": float 0-10, \"notes\": string, \"risk_level\": int 0-5}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="hook_scoring"), HookScorePayload)
        return parsed  # type: ignore[return-value]

    def analyze_retention(self, *, angle: str, channel_memory: str, sections: list[ScriptSection]) -> RetentionAnalysisPayload:
        prompt = f"""Analyze retention risks in strict JSON only.\nApproved angle: {angle}\nChannel memory: {channel_memory}\nScript sections: {json.dumps([s.model_dump() for s in sections])}\nSchema: {{\"review\": {{\"weak_intro_warning\": bool, \"slow_context_warning\": bool, \"payoff_delay_warning\": bool, \"repeated_sentence_warning\": bool, \"generic_section_warning\": bool, \"unclear_promise_warning\": bool, \"section_map\": [{{\"timestamp_range\": string, \"section_name\": string, \"script_excerpt\": string, \"purpose\": string, \"risk\": string, \"recommendation\": string}}], \"recommendations\": [string], \"timestamps\": [string]}}}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="retention_analysis"), RetentionAnalysisPayload)
        return parsed  # type: ignore[return-value]

    def review_compliance(self, *, angle: str, channel_memory: str, script_text: str) -> ComplianceReviewPayload:
        prompt_template = self._COMPLIANCE_PROMPT_PATH.read_text(encoding="utf-8").strip()
        schema_json = json.dumps(ComplianceReviewPayload.model_json_schema(), separators=(",", ":"))
        prompt = (
            f"{prompt_template}\n\n"
            f"Approved angle: {angle}\n"
            f"Channel memory: {channel_memory}\n"
            f"Script text: {script_text}\n\n"
            "Return strict JSON only.\n"
            f"Schema: {schema_json}\n"
            "Do not include any legal guarantees or disclaimers."
        )
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="compliance_review"), ComplianceReviewPayload)
        return parsed  # type: ignore[return-value]

    @staticmethod
    def _normalize_words(text: str) -> set[str]:
        normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
        return {part for part in normalized.split() if len(part) >= 4}

    def _validate_title_script_promise_consistency(
        self, *, title: str, promise_alignment_notes: list[str], approved_script_sections: list[ScriptSection]
    ) -> None:
        title_tokens = self._normalize_words(title)
        script_tokens = self._normalize_words(" ".join(section.content for section in approved_script_sections))
        if title_tokens and not (title_tokens & script_tokens):
            raise ValueError("generated publishing package title is not consistent with approved script content")
        if not promise_alignment_notes:
            raise ValueError("generated publishing package must include promise_alignment_notes")

    def generate_publishing_package(
        self,
        *,
        approved_angle: str,
        approved_script_sections: list[ScriptSection],
        compliance_report: ComplianceReport,
    ) -> PublishingPackagePayload:
        sections_json = json.dumps([section.model_dump() for section in approved_script_sections])
        compliance_json = compliance_report.model_dump_json()
        schema_json = json.dumps(PublishingPackagePayload.model_json_schema(), separators=(",", ":"))
        prompt_template = self._PUBLISHING_PACKAGE_PROMPT_PATH.read_text(encoding="utf-8").strip()
        prompt = (
            f"{prompt_template}\n\n"
            f"Approved angle: {approved_angle}\n"
            f"Approved script sections: {sections_json}\n"
            f"Compliance report: {compliance_json}\n\n"
            "Additional constraints:\n"
            "- Include promise_alignment_notes listing concrete title-to-script consistency checks.\n"
            "- Chapters must use 'mm:ss - title' or 'hh:mm:ss - title' format.\n\n"
            "Return strict JSON only.\n"
            f"Schema: {schema_json}"
        )
        parsed = self._parse_strict_json(
            self._call(prompt=prompt, operation="publishing_package_generation"),
            PublishingPackagePayload,
        )
        self._validate_title_script_promise_consistency(
            title=parsed.title,
            promise_alignment_notes=parsed.promise_alignment_notes,
            approved_script_sections=approved_script_sections,
        )
        return parsed  # type: ignore[return-value]

    # Backwards-compatible wrappers.
    def generate_hook_variants(self, *, angle: str, sections: list[ScriptSection]) -> HookVariantsPayload:
        return self.generate_hooks(angle=angle, channel_memory="", sections=sections)

    def score_hook_variant(self, *, angle: str, hook_text: str, script_sections: list[ScriptSection]) -> HookScorePayload:
        return self.score_hook(angle=angle, channel_memory="", hook_text=hook_text, script_sections=script_sections)
