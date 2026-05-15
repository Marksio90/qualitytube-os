from pydantic import BaseModel


class ChannelMemory(BaseModel):
    channel_id: str
    tone_notes: list[str] = []
    banned_claims: list[str] = []
