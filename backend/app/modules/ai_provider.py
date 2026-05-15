from typing import Protocol


class AIProvider(Protocol):
    model: str

    def generate(self, prompt: str) -> str:
        ...


class MockProvider:
    model = "mock-gpt"

    def generate(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "channel memory:" in lowered and "hook variants" in lowered and '"variants"' in lowered:
            return '{"variants":[{"type":"question","text":"What if your first 15 seconds are silently tanking every upload?","promise":"You will identify and fix the hidden retention killer.","curiosity_gap":"Most creators optimize thumbnails but miss this opening structure flaw.","risk_level":1,"score":8.4,"notes":"Strong curiosity with clear payoff.","selected":false},{"type":"contradiction","text":"More editing can hurt retention if your opening promise is fuzzy.","promise":"Learn a simpler open that holds viewers longer.","curiosity_gap":"The common editing advice creates a mismatch that viewers abandon.","risk_level":2,"score":8.0,"notes":"Contrarian angle with practical payoff.","selected":false}]}'
        if "channel memory:" in lowered and "schema: {\"score\"" in lowered and "hook text:" in lowered:
            return '{"score":8.6,"notes":"Clear and specific promise; slight risk of sounding absolute.","risk_level":2}'
        if "channel memory:" in lowered and '"review"' in lowered and "analyze retention risks" in lowered:
            return '{"review":{"weak_intro_warning":false,"slow_context_warning":true,"payoff_delay_warning":false,"repeated_sentence_warning":false,"generic_section_warning":false,"unclear_promise_warning":false,"section_map":[{"timestamp_range":"0:00-0:20","section_name":"hook","script_excerpt":"Most creators copy growth advice that quietly kills retention...","purpose":"Set contrarian premise","risk":"Context takes too long before concrete proof","recommendation":"Move proof example into first 12 seconds"}],"recommendations":["Show one concrete before/after example in first 15 seconds","Tighten transition between hook and body"],"timestamps":["0:00-0:20"]}}'
        if "schema: {\"hook\"" in lowered:
            return '{"hook":"Start with a surprising claim grounded in creator pain.","beats":["Name the hidden bottleneck","Prove with a concrete case","Deliver a 3-step fix"],"cta":"Ask viewers to test one tactic this week and share results."}'
        if "schema: {\"sections\"" in lowered and "outline:" in lowered:
            return '{"sections":[{"title":"hook","content":"Most creators copy growth advice that quietly kills retention in the first 30 seconds."},{"title":"body","content":"The real issue is misaligned promise-to-payoff flow. Start with audience pain, present one counter-example, then walk through three specific execution steps with measurable checkpoints."},{"title":"cta","content":"Pick one step today, run it on your next upload, and comment with your before/after retention graph."}]}'
        if "quality_report" in lowered:
            return '{"quality_report":{"hook_score":8.2,"clarity_score":8.1,"narrative_tension_score":7.9,"originality_score":8.0,"retention_score":8.3,"evidence_score":7.8,"human_voice_score":8.0,"cta_quality_score":8.1,"overall_script_score":8.1}}'
        return '{"sections":[{"title":"hook","content":"Here is a sharper opening that increases curiosity without sounding generic or spammy."},{"title":"body","content":"Keep the angle tight, preserve the proof sequence, and increase specificity in examples, metrics, and transitions to improve flow and trust."},{"title":"cta","content":"Invite a single realistic next action and ask for concrete follow-up outcomes in the comments."}]}'
