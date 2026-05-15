from typing import Protocol


class AIProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class MockProvider:
    def generate(self, prompt: str) -> str:
        return f"mock-response::{prompt[:40]}"
