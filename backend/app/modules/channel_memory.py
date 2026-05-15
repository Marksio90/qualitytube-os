from pydantic import BaseModel


class ChannelMemory(BaseModel):
    channel_id: str
    tone_notes: list[str] = []
    banned_claims: list[str] = []


class ChannelMemoryRepository:
    """In-memory boundary for channel memory records."""

    def __init__(self) -> None:
        self._by_channel_id: dict[str, ChannelMemory] = {}

    def upsert(self, memory: ChannelMemory) -> ChannelMemory:
        self._by_channel_id[memory.channel_id] = memory
        return memory

    def get(self, channel_id: str) -> ChannelMemory | None:
        return self._by_channel_id.get(channel_id)
