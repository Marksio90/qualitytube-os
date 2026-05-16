import pytest

from app.modules.script_ai import ScriptAIService


class MockProvider:
    model = "mock"

    def __init__(self, payload: str) -> None:
        self.payload = payload

    def generate(self, prompt: str) -> str:
        return self.payload


def test_visual_plan_strict_json_passes() -> None:
    svc = ScriptAIService(provider=MockProvider('{"scenes":[{"scene_number":1,"narration_excerpt":"A","visual_type":"stock","visual_description":"B","purpose":"C","filler_risk_score":0.3}]}'))
    result = svc.generate_visual_plan(approved_script_sections=[], approved_angle="angle", channel_memory="mem")
    assert len(result.scenes) == 1


def test_visual_plan_invalid_or_extra_fields_rejected() -> None:
    svc = ScriptAIService(provider=MockProvider('{"scenes":[{"scene_number":1,"narration_excerpt":"A","visual_type":"stock","visual_description":"B","purpose":"C","filler_risk_score":0.3,"extra":1}]}'))
    with pytest.raises(ValueError, match="did not match schema"):
        svc.generate_visual_plan(approved_script_sections=[], approved_angle="angle", channel_memory="mem")


def test_visual_plan_malformed_json_rejected() -> None:
    svc = ScriptAIService(provider=MockProvider("{"))
    with pytest.raises(ValueError, match="invalid JSON"):
        svc.generate_visual_plan(approved_script_sections=[], approved_angle="angle", channel_memory="mem")


def test_visual_plan_logs_operation_name() -> None:
    svc = ScriptAIService(provider=MockProvider('{"scenes":[{"scene_number":1,"narration_excerpt":"A","visual_type":"stock","visual_description":"B","purpose":"C","filler_risk_score":0.3}]}'))
    before = len(svc.logger.calls)
    svc.generate_visual_plan(approved_script_sections=[], approved_angle="angle", channel_memory="mem")
    assert len(svc.logger.calls) == before + 1
    assert svc.logger.calls[-1].operation == "visual_plan_generation"
