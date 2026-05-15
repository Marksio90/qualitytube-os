# Script Improvement Prompt

Inputs (required): approved angle, channel memory, research brief, script sections.

Rules:
- Preserve the approved angle.
- Use channel memory and research brief constraints.
- Explicitly reject generic intros and spammy CTAs.
- Return strict JSON only.

JSON schema:
```json
{"sections":[{"title":"hook","content":"string"},{"title":"body","content":"string"},{"title":"cta","content":"string"}]}
```
