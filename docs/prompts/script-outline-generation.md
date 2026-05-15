# Script Outline Generation Prompt

Inputs (required):
- Approved angle
- Channel memory
- Research brief

Rules:
- Use the approved angle as the strategic thesis.
- Incorporate channel memory constraints and audience patterns.
- Ground claims in the research brief.
- Explicitly reject generic intros and spammy CTAs.
- Return strict JSON only.

JSON schema:
```json
{"hook":"string","beats":["string","string","string"],"cta":"string"}
```
