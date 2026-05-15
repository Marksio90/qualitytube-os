from typing import Protocol


class AIProvider(Protocol):
    model: str

    def generate(self, prompt: str) -> str:
        ...


class MockProvider:
    model = "mock-gpt"

    def generate(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "schema: {\"hook\"" in lowered:
            return '{"hook":"Start with a surprising claim grounded in creator pain.","beats":["Name the hidden bottleneck","Prove with a concrete case","Deliver a 3-step fix"],"cta":"Ask viewers to test one tactic this week and share results."}'
        if "schema: {\"sections\"" in lowered and "outline:" in lowered:
            return '{"sections":[{"title":"hook","content":"Most creators copy growth advice that quietly kills retention in the first 30 seconds."},{"title":"body","content":"The real issue is misaligned promise-to-payoff flow. Start with audience pain, present one counter-example, then walk through three specific execution steps with measurable checkpoints."},{"title":"cta","content":"Pick one step today, run it on your next upload, and comment with your before/after retention graph."}]}'
        if "quality_report" in lowered:
            return '{"quality_report":{"hook_score":8.2,"clarity_score":8.1,"narrative_tension_score":7.9,"originality_score":8.0,"retention_score":8.3,"evidence_score":7.8,"human_voice_score":8.0,"cta_quality_score":8.1,"overall_script_score":8.1}}'
        return '{"sections":[{"title":"hook","content":"Here is a sharper opening that increases curiosity without sounding generic or spammy."},{"title":"body","content":"Keep the angle tight, preserve the proof sequence, and increase specificity in examples, metrics, and transitions to improve flow and trust."},{"title":"cta","content":"Invite a single realistic next action and ask for concrete follow-up outcomes in the comments."}]}'
