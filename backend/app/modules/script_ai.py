from __future__ import annotations

import json
import time
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, ValidationError

from .ai_provider import AIProvider, MockProvider
from .llm_logging import LLMCall, LLMCallLogger
from .scripts import HookVariantCreate, RetentionReview, ScriptQualityReport, ScriptSection


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

    variants: list[HookVariantCreate]


class HookScorePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float
    notes: str
    risk_level: int


class RetentionAnalysisPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review: RetentionReview


class ScriptAIService:
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

    def generate_hook_variants(self, *, angle: str, sections: list[ScriptSection]) -> HookVariantsPayload:
        prompt = f"""Generate hook variants in strict JSON only.\nApproved angle: {angle}\nSections: {json.dumps([s.model_dump() for s in sections])}\nSchema: {{\"variants\": [{{\"type\": \"contradiction|shock|question|story|mistake|before_after|hidden_mechanism\", \"text\": string, \"promise\": string, \"curiosity_gap\": string, \"risk_level\": int 0-5, \"score\": float 0-10, \"notes\": string, \"selected\": bool}}]}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="hook_generation"), HookVariantsPayload)
        return parsed  # type: ignore[return-value]

    def score_hook_variant(self, *, angle: str, hook_text: str, script_sections: list[ScriptSection]) -> HookScorePayload:
        prompt = f"""Score this hook in strict JSON only.\nApproved angle: {angle}\nHook text: {hook_text}\nScript sections: {json.dumps([s.model_dump() for s in script_sections])}\nSchema: {{\"score\": float 0-10, \"notes\": string, \"risk_level\": int 0-5}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="hook_scoring"), HookScorePayload)
        return parsed  # type: ignore[return-value]

    def analyze_retention(self, *, angle: str, sections: list[ScriptSection]) -> RetentionAnalysisPayload:
        prompt = f"""Analyze retention risks in strict JSON only.\nApproved angle: {angle}\nSections: {json.dumps([s.model_dump() for s in sections])}\nSchema: {{\"review\": {{\"weak_intro_warning\": bool, \"slow_context_warning\": bool, \"payoff_delay_warning\": bool, \"repeated_sentence_warning\": bool, \"generic_section_warning\": bool, \"unclear_promise_warning\": bool, \"section_map\": [{{\"timestamp_range\": string, \"section_name\": string, \"script_excerpt\": string, \"purpose\": string, \"risk\": string, \"recommendation\": string}}], \"recommendations\": [string], \"timestamps\": [string]}}}}"""
        parsed = self._parse_strict_json(self._call(prompt=prompt, operation="retention_analysis"), RetentionAnalysisPayload)
        return parsed  # type: ignore[return-value]
