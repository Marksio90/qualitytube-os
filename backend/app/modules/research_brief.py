from pydantic import BaseModel


class ResearchBrief(BaseModel):
    topic: str
    goals: list[str]
    references: list[str]
