import pytest

from app.modules.audio_brief_ai import AudioBriefAIGenerationError, AudioBriefAIService, AudioBriefPayload


class MockProvider:
    model = "mock"

    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.payload


def test_audio_brief_strict_json_passes() -> None:
    provider = MockProvider('{"voice_style":"educational_neutral","pace_wpm":130,"emotional_tone":"calm confidence","pause_notes":"Pause before key numbers.","pronunciation_notes":"Say SaaS as sass.","emphasis_notes":"Stress the contrast sentence.","export_text":"Narration guidance only."}')
    svc = AudioBriefAIService(provider=provider)

    result = svc.generate_audio_brief(approved_angle="angle", approved_script_sections=[], policy_context="No paid TTS")
    assert isinstance(result, AudioBriefPayload)
    assert result.voice_style == "educational_neutral"
    assert "Policy context:" in provider.prompts[-1]


def test_audio_brief_invalid_json_rejected() -> None:
    svc = AudioBriefAIService(provider=MockProvider("{"))
    with pytest.raises(AudioBriefAIGenerationError, match="invalid JSON"):
        svc.generate_audio_brief(approved_angle="angle", approved_script_sections=[], policy_context="policy")


def test_audio_brief_schema_violation_rejected() -> None:
    svc = AudioBriefAIService(provider=MockProvider('{"voice_style":"educational_neutral","pace_wpm":130,"emotional_tone":"ok","pause_notes":"ok","pronunciation_notes":"ok","emphasis_notes":"ok","export_text":"ok","synthetic_voice_used":true}'))
    with pytest.raises(AudioBriefAIGenerationError, match="did not match schema"):
        svc.generate_audio_brief(approved_angle="angle", approved_script_sections=[], policy_context="policy")


def test_audio_brief_logs_operation_name() -> None:
    svc = AudioBriefAIService(provider=MockProvider('{"voice_style":"educational_neutral","pace_wpm":130,"emotional_tone":"calm confidence","pause_notes":"Pause before key numbers.","pronunciation_notes":"Say SaaS as sass.","emphasis_notes":"Stress the contrast sentence.","export_text":"Narration guidance only."}'))
    before = len(svc.logger.calls)
    svc.generate_audio_brief(approved_angle="angle", approved_script_sections=[], policy_context="policy")
    assert len(svc.logger.calls) == before + 1
    assert svc.logger.calls[-1].operation == "audio_brief_generation"
