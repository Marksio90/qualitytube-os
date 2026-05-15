from __future__ import annotations

import json
import time
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, ValidationError

from .ai_provider import AIProvider, MockProvider
from .llm_logging import LLMCall, LLMCallLogger
from .scripts import ScriptQualityReport, ScriptSection


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
