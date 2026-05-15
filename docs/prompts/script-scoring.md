# Script Scoring Prompt

Inputs (required): approved angle, channel memory, research brief, script sections.

Rules:
- Reject generic intros and spammy CTAs.
- Score each category from 0 to 10.
- Return strict JSON only.

JSON schema:
```json
{"quality_report":{"hook_score":0,"clarity_score":0,"narrative_tension_score":0,"originality_score":0,"retention_score":0,"evidence_score":0,"human_voice_score":0,"cta_quality_score":0,"overall_script_score":0}}
```
