# Visual Plan Generation Prompt Constraints

Use these constraints when generating a visual plan from a script. These are **hard requirements**.

## 1) Use only approved script content

- Include only scenes, beats, claims, and details that are present in the approved script package.
- Do not invent new facts, events, entities, settings, timelines, or outcomes.
- If requested content is missing from the approved script package, return a structured validation failure instead of fabricating details.

## 2) Every visual must support meaning

- Each visual choice must have a clear narrative or instructional purpose.
- Visuals must directly reinforce the associated line, beat, or concept.
- Reject visuals that are merely decorative, redundant, or emotionally manipulative without informational value.

## 3) Avoid filler and generic stock montage choices

- Do not use generic montage fillers (e.g., random skyline, people walking in office hallways, abstract typing hands) unless explicitly justified by script meaning.
- Prefer specific, context-anchored visual ideas over broad stock shorthand.
- Penalize repetitive visual tropes and low-information b-roll.

## 4) Require purpose + risk notes for each scene

For **every** scene, provide:
- `purpose_note`: why this visual improves comprehension, retention, or narrative clarity.
- `risk_note`: key risk(s) such as factual drift, mismatch to tone, cliché usage, ambiguity, legal/compliance sensitivity, or potential audience misinterpretation.

A scene is incomplete if either note is missing.

## 5) Strict JSON output with exact schema keys

- Return **JSON only** (no prose before/after the object).
- Use the schema exactly as defined by the caller contract.
- Do not add, remove, or rename keys.
- Preserve required key order when order is specified.
- If validation fails, still return a JSON object conforming to the same top-level schema, including machine-readable error details in the designated error fields.

## Non-compliance handling

If any constraint cannot be satisfied:
1. Mark the affected scene(s) as non-compliant.
2. Provide concise machine-readable reasons.
3. Do not substitute invented visuals.
4. Return contract-valid JSON describing the failure.
