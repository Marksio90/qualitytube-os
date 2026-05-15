from pydantic import BaseModel


class LLMCallLog(BaseModel):
    provider: str
    model: str
    prompt_chars: int
    response_chars: int
