import pytest

from app.modules.script_ai import ScriptAIService


class BadProvider:
    model = "bad"

    def generate(self, prompt: str) -> str:
        return "not-json"


def test_strict_json_failure_raises() -> None:
    svc = ScriptAIService(provider=BadProvider())
    with pytest.raises(ValueError):
        svc.generate_outline(angle="a", channel_memory="m", research_brief="r")
