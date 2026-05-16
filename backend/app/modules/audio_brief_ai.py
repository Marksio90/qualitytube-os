from __future__ import annotations

import json
import time
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .ai_provider import AIProvider, MockProvider
from .audio_brief import VoiceStyle
from .llm_logging import LLMCall, LLMCallLogger
from .scripts import ScriptSection


class AudioBriefAIGenerationError(ValueError):
    """Deterministic exception for malformed or schema-invalid model responses."""


class AudioBriefPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    voice_style: VoiceStyle
    pace_wpm: int = Field(ge=90, le=220)
    emotional_tone: str = Field(min_length=1)
    pause_notes: str = Field(min_length=1)
    pronunciation_notes: str = Field(min_length=1)
    emphasis_notes: str = Field(min_length=1)
    synthetic_voice_used: bool
    disclosure_required: bool
    disclosure_notes: str = Field(min_length=1)
    export_text: str = Field(min_length=1)


class AudioBriefAIService:
    _AUDIO_BRIEF_PROMPT_PATH = Path(__file__).resolve().parents[3] / "docs" / "prompts" / "audio-brief-generation.md"

    def __init__(self, provider: AIProvider | None = None, logger: LLMCallLogger | None = None) -> None:
        self.provider = provider or MockProvider()
        self.logger = logger or LLMCallLogger()

    @staticmethod
    def _parse_strict_json(raw: str, schema: type[BaseModel]) -> BaseModel:
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AudioBriefAIGenerationError(f"invalid JSON returned by model: {exc}") from exc

        try:
            return schema.model_validate(parsed)
        except ValidationError as exc:
            raise AudioBriefAIGenerationError(f"model JSON did not match schema: {exc}") from exc

    def generate_audio_brief(
        self,
        *,
        approved_angle: str,
        approved_script_sections: list[ScriptSection],
        policy_context: str,
    ) -> AudioBriefPayload:
        sections_json = json.dumps([section.model_dump() for section in approved_script_sections])
        schema_json = json.dumps(AudioBriefPayload.model_json_schema(), separators=(",", ":"))
        prompt_template = self._AUDIO_BRIEF_PROMPT_PATH.read_text(encoding="utf-8").strip()
        prompt = (
            f"{prompt_template}\n\n"
            f"Approved angle: {approved_angle}\n"
            f"Approved script sections: {sections_json}\n"
            f"Policy context: {policy_context}\n\n"
            "Return strict JSON only.\n"
            f"Schema: {schema_json}"
        )

        correlation_id = str(uuid4())
        started = time.perf_counter()
        raw = self.provider.generate(prompt)
        latency_ms = int((time.perf_counter() - started) * 1000)
        self.logger.log(
            LLMCall(
                provider=type(self.provider).__name__,
                model=getattr(self.provider, "model", "mock-model"),
                operation="audio_brief_generation",
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
        parsed = self._parse_strict_json(raw, AudioBriefPayload)
        return parsed  # type: ignore[return-value]
