# Compliance Review Prompt

Use this checklist to perform a strict pre-publish compliance review of generated or edited content. The reviewer must return machine-readable JSON only, and the JSON **must exactly match** the backend model schema.

## 1) Reused / Repetitive / Mass-Production Checks

- Detect obvious reuse from prior outputs, templates, or near-duplicate variants.
- Flag repetitive structure patterns that indicate low-originality mass production.
- Identify spin/rehash behavior (same ideas with superficial wording changes).
- Identify batches that appear generated from a single prompt pattern with minimal differentiation.
- Require explicit evidence of meaningful variation and purpose when reviewing multi-item sets.

## 2) Disclosure Requirement Checks

- Determine whether synthetic/AI-assisted creation disclosure is required for this content type, workflow, and destination.
- Confirm disclosure placement, visibility, and wording are compliant with platform or policy requirements.
- Mark as non-compliant when disclosure is required but missing, incomplete, hidden, or ambiguous.

## 3) Misleading / Copyright / Sensitive-Topic Checks

- Misleading risk: detect fabricated claims, impersonation, deceptive presentation, false authority, or unverifiable assertions presented as fact.
- Copyright risk: detect probable unlicensed protected material, close paraphrase, derivative copying, or trademark misuse.
- Sensitive topics: identify high-risk content areas (health, legal, finance, elections, minors, self-harm, violence, identity-based harm, regulated claims).
- Require escalation flags where policy requires specialist or human review.

## 4) Human Contribution Requirement

- Verify and record meaningful human contribution where required by policy.
- Reject purely automated outputs when policy requires material human authorship/editorial input.
- Check provenance notes: who contributed, what was changed, and why those edits are substantive.

## 5) Output Contract (Strict Schema Requirement)

- Return **JSON only** (no Markdown, no prose wrappers, no trailing commentary).
- Output **must exactly match** the backend response model (field names, enums, nesting, required fields, and data types).
- Do not add unspecified keys.
- If uncertain, populate uncertainty in approved schema fields only.

## 6) Legal Safety Statement (Required)

- Include an explicit statement in reasoning/notes fields (where schema allows) that the review is a policy/compliance assessment and **not legal advice**.
- Never claim legal certainty, legal clearance, or legal guarantees.
- Explicit instruction: **no legal guarantees** under any circumstance.
