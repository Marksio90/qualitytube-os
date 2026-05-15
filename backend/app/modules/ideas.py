from pydantic import BaseModel


class Idea(BaseModel):
    id: str
    title: str
    audience: str
    premise: str
