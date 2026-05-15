# Script Draft Generation Prompt

Inputs (required): approved angle, channel memory, research brief, outline.

Rules:
- Keep structure aligned with the outline.
- Reject generic intros and spammy CTAs.
- Maintain specific, evidence-oriented language.
- Return strict JSON only.

JSON schema:
```json
{"sections":[{"title":"hook","content":"string"},{"title":"body","content":"string"},{"title":"cta","content":"string"}]}
```
