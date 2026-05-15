from __future__ import annotations

from pydantic import BaseModel, Field


class LLMCall(BaseModel):
    provider: str
    model: str
    operation: str
    prompt: str
    response: str
    prompt_chars: int
    response_chars: int
    prompt_tokens: int = Field(ge=0)
    completion_tokens: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    correlation_id: str


class LLMCallLogger:
    def __init__(self) -> None:
        self.calls: list[LLMCall] = []

    def log(self, call: LLMCall) -> None:
        self.calls.append(call)
