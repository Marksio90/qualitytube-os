from __future__ import annotations

import json
import time
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .ai_provider import AIProvider, MockProvider
from .llm_logging import LLMCall, LLMCallLogger


class TitleCandidate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    promise_alignment_notes: list[str] = Field(min_length=1)
    no_false_guarantees: bool
    clickbait_risk: float = Field(ge=0.0, le=10.0)

    @field_validator("title", mode="before")
    @classmethod
    def _validate_title(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("field must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("field must not be empty")
        return normalized

    @field_validator("promise_alignment_notes", mode="before")
    @classmethod
    def _validate_alignment_notes(cls, value: object) -> object:
        if not isinstance(value, list):
            raise ValueError("field must be a list of strings")
        if not value:
            raise ValueError("field must include at least one promise alignment note")
        return value


class GenerateTitlesPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    variants: list[TitleCandidate] = Field(min_length=1)


class ScoreTitlePayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    clickbait_risk: float = Field(ge=0.0, le=10.0)
    promise_alignment_score: float = Field(ge=0.0, le=10.0)
    no_false_guarantees: bool
    verdict: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class ThumbnailBrief(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    concept: str = Field(min_length=1, max_length=400)
    composition: str = Field(min_length=1, max_length=600)
    text_overlay: str = Field(min_length=1, max_length=120)
    promise_alignment_notes: list[str] = Field(min_length=1)
    clickbait_risk: float = Field(ge=0.0, le=10.0)
    no_false_guarantees: bool


class GenerateThumbnailBriefsPayload(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    briefs: list[ThumbnailBrief] = Field(min_length=1)


class TitleThumbnailAIService:
    def __init__(self, provider: AIProvider | None = None, logger: LLMCallLogger | None = None) -> None:
        self.provider = provider or MockProvider()
        self.logger = logger or LLMCallLogger()

    @staticmethod
    def _parse_strict_json(raw: str, schema: type[BaseModel]) -> BaseModel:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON returned by model: {exc}") from exc

        try:
            return schema.model_validate(parsed)
        except ValidationError as exc:
            raise ValueError(f"model JSON did not match schema: {exc}") from exc

    def generate_titles(
        self,
        idea: str,
        approved_angle: str,
        approved_script: str,
        channel_memory: str,
    ) -> GenerateTitlesPayload:
        prompt = (
            "Generate YouTube title variants as strict JSON only.\n"
            f"Idea: {idea}\n"
            f"Approved angle: {approved_angle}\n"
            f"Approved script: {approved_script}\n"
            f"Channel memory: {channel_memory}\n"
            "Constraints:\n"
            "- No false guarantees.\n"
            "- Every title promise must align with the approved angle and script.\n"
            "- Include explicit clickbait_risk from 0 to 10.\n"
            "Schema: {\"variants\":[{\"title\":string,\"promise_alignment_notes\":[string],\"no_false_guarantees\":bool,\"clickbait_risk\":float 0-10}]}"
        )
        correlation_id = str(uuid4())
        started = time.perf_counter()
        raw = self.provider.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.logger.log(
            LLMCall(
                provider=type(self.provider).__name__,
                model=getattr(self.provider, "model", "mock-model"),
                operation="title_generation",
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
        parsed = self._parse_strict_json(raw, GenerateTitlesPayload)
        return parsed  # type: ignore[return-value]

    def score_title(self, title_variant: str, idea_context: str) -> ScoreTitlePayload:
        prompt = (
            "Score this title as strict JSON only.\n"
            f"Title variant: {title_variant}\n"
            f"Idea context: {idea_context}\n"
            "Constraints:\n"
            "- No false guarantees.\n"
            "- Promise must align with idea context.\n"
            "- Include explicit clickbait_risk from 0 to 10.\n"
            "Schema: {\"clickbait_risk\":float 0-10,\"promise_alignment_score\":float 0-10,\"no_false_guarantees\":bool,\"verdict\":string,\"rationale\":string}"
        )
        correlation_id = str(uuid4())
        started = time.perf_counter()
        raw = self.provider.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.logger.log(
            LLMCall(
                provider=type(self.provider).__name__,
                model=getattr(self.provider, "model", "mock-model"),
                operation="title_scoring",
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
        parsed = self._parse_strict_json(raw, ScoreTitlePayload)
        return parsed  # type: ignore[return-value]

    def generate_thumbnail_briefs(
        self,
        idea_context: str,
        selected_or_top_titles: list[str],
        channel_memory: str,
    ) -> GenerateThumbnailBriefsPayload:
        if not selected_or_top_titles:
            raise ValueError("selected_or_top_titles must contain at least one title")
        titles_json = json.dumps(selected_or_top_titles)
        prompt = (
            "Generate thumbnail briefs as strict JSON only.\n"
            f"Idea context: {idea_context}\n"
            f"Selected/top titles: {titles_json}\n"
            f"Channel memory: {channel_memory}\n"
            "Constraints:\n"
            "- MVP mode: brief generation only, no image rendering calls or image prompt execution.\n"
            "- No false guarantees.\n"
            "- Promise and visual direction must align with title and idea context.\n"
            "- Include explicit clickbait_risk from 0 to 10 for each brief.\n"
            "Schema: {\"briefs\":[{\"title\":string,\"concept\":string,\"composition\":string,\"text_overlay\":string,\"promise_alignment_notes\":[string],\"clickbait_risk\":float 0-10,\"no_false_guarantees\":bool}]}"
        )
        correlation_id = str(uuid4())
        started = time.perf_counter()
        raw = self.provider.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.logger.log(
            LLMCall(
                provider=type(self.provider).__name__,
                model=getattr(self.provider, "model", "mock-model"),
                operation="thumbnail_brief_generation",
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
        parsed = self._parse_strict_json(raw, GenerateThumbnailBriefsPayload)
        return parsed  # type: ignore[return-value]
