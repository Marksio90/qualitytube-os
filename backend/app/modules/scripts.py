from pydantic import BaseModel


class ScriptDraft(BaseModel):
    idea_id: str
    hook: str
    outline: list[str]
    cta: str
