# Visual Plan Builder

This document defines product behavior and boundaries for the Visual Plan Builder phase.

## Scope boundaries

The Visual Plan Builder is a **planning and validation layer only**.

In scope:
- Interpret approved script content into scene-level visual recommendations.
- Enforce prompt and schema constraints.
- Score and flag filler-risk and other quality risks.
- Support review, approval, and revision workflows.

Out of scope for this phase:
- Rendering images, video, or animations.
- Executing generation jobs against creative models.
- Asset downloading, editing, compositing, or timeline assembly.
- Final media export or publication.

## Visual types and when to use each

Use visual types intentionally based on communication goal.

- **Literal reenactment / depiction**
  - Use when the script references concrete actions, places, or objects.
  - Best for high-specificity narrative beats.

- **Diagram / explainer graphic**
  - Use for processes, systems, comparisons, and causal logic.
  - Prefer when comprehension is more important than cinematic realism.

- **Data visualization**
  - Use when numerical claims, trends, or proportions are central.
  - Must map directly to script-backed data.

- **Text-led card / pull quote**
  - Use for key definitions, disclaimers, or exact wording that must be retained.
  - Keep sparse and legible; avoid overuse.

- **Contextual b-roll**
  - Use only when it anchors a specific script point.
  - Avoid generic filler montage patterns.

- **Symbolic / metaphor visual**
  - Use selectively for abstract concepts when literal depiction is impossible or misleading.
  - Must include explicit risk notes to avoid ambiguity.

## Filler-risk scoring interpretation

Filler-risk estimates how likely a scene is to feel generic, low-information, or disconnected from script meaning.

Suggested interpretation bands:
- **0.00–0.24 (Low):** Specific and meaning-rich visual; strong script alignment.
- **0.25–0.49 (Moderate):** Some specificity, but includes mild trope risk; review suggested.
- **0.50–0.74 (High):** Likely generic or weakly justified; revision normally required.
- **0.75–1.00 (Critical):** Predominantly filler-like; reject or fully rework.

Reviewer guidance:
- High/critical scenes should not pass without explicit mitigation notes.
- Repeated moderate scores across adjacent scenes may indicate montage drift.

## Scene approval workflow

1. **Draft generation**
   - System proposes scene plan with visual type, purpose note, risk note, and filler-risk score.

2. **Automated validation**
   - Validate strict schema compliance.
   - Validate script-grounding constraints.
   - Flag missing purpose/risk notes.

3. **Editorial review**
   - Reviewer inspects scene intent, factual alignment, tone fit, and filler risk.
   - Reviewer can approve, request revision, or reject per scene.

4. **Revision cycle**
   - Revised scenes must preserve contract-valid schema.
   - Changes must include rationale and updated risk notes.

5. **Plan approval**
   - Plan transitions to approved only when all required scenes are approved.
   - Approval output is a planning artifact for downstream rendering systems.

## Endpoint contracts and expected UX states

### Contract principles

- All endpoints must return machine-parseable JSON.
- Request and response schemas are versioned and strict.
- Unknown keys are rejected unless explicitly allowed by version policy.
- Validation errors must be deterministic and field-scoped.

### Core endpoint responsibilities

- **Create plan endpoint**
  - Accepts approved script payload and planner options.
  - Returns draft plan with scene metadata and validation status.

- **Validate plan endpoint**
  - Performs schema + policy checks without mutating approval state.
  - Returns pass/fail plus field-level errors and warnings.

- **Review decision endpoint**
  - Accepts per-scene decisions (approve/revise/reject) and reviewer notes.
  - Returns updated plan state and pending actions.

- **Finalize plan endpoint**
  - Verifies all required approvals.
  - Emits immutable approved-plan artifact for downstream execution phases.

### Expected UX states

- **Idle:** No active draft loaded.
- **Drafting:** Plan is being generated or regenerated.
- **Validation Failed:** Schema/policy violations block progression.
- **Needs Review:** Draft is valid and awaiting reviewer decisions.
- **Revision Requested:** One or more scenes require changes.
- **Approved:** All mandatory scenes approved; plan locked for handoff.
- **Rejected:** Plan closed without approval.
- **System Error:** Non-validation failure (timeout/dependency/unknown).

State transitions should be explicit, auditable, and visible at both plan and scene level.
