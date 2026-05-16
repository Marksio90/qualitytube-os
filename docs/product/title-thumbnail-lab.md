# Title & Thumbnail Lab Product Flow

Title & Thumbnail Lab is the pre-publish optimization workflow for generating, scoring, and selecting title + thumbnail **brief** candidates (copy + visual direction only), then synchronizing a selected pair into Publishing Package metadata.

> Scope note: MVP does **not** render images. It generates structured thumbnail briefs (composition, subject, text overlay guidance, mood, constraints) that humans or downstream tooling can execute later.

## MVP scope and non-goals

## In scope (MVP)
- Generate multiple title candidates from approved script context.
- Generate multiple thumbnail **brief** candidates (no pixels).
- Score each title and thumbnail brief with a deterministic rubric and policy flags.
- Suggest best pairings and allow human selection override.
- Sync selected title + thumbnail brief into Publishing Package draft fields.
- Persist full audit history of prompts, outputs, scores, policy checks, and selections.

## Out of scope (MVP)
- Raster image generation, editing, inpainting, or rendering endpoints.
- Automatic upload to destination platform thumbnail APIs.
- Multivariate live experiment orchestration on platforms (A/B tests).
- Autonomous publish with no human review.

## Workflow sequence and prerequisites

1. Open an approved script in Script Studio.
2. Launch **Title & Thumbnail Lab** from that script context.
3. Submit generation request for title and thumbnail-brief variants.
4. Receive strict JSON payload with candidates, scores, and policy diagnostics.
5. Review candidates, inspect risk flags, and choose one pair.
6. Save selection and optionally sync to a linked Publishing Package.
7. Continue package compliance checks and export in Publishing Package workflow.

Cross-system flow depends on Publishing Package rules and status lifecycle described in `docs/product/publishing-package.md`, plus foundational service boundaries and module conventions in `docs/architecture.md`.

## Backend endpoint contracts

All endpoints are script-scoped and require `script_id` whose source script is resolvable and policy-eligible.

### 1) Generate title + thumbnail brief candidates

`POST /api/v1/scripts/{script_id}/title-thumbnail-lab/generate`

**Request**

```json
{
  "title_count": 8,
  "thumbnail_count": 6,
  "tone": ["curiosity", "specific", "credible"],
  "audience": "new creators",
  "constraints": {
    "max_title_chars": 70,
    "allow_numbers": true,
    "avoid_claim_types": ["guaranteed_outcome", "medical_promise"],
    "brand_safety": "standard"
  },
  "context": {
    "video_goal": "increase CTR while preserving trust",
    "topic": "editing workflow systems"
  }
}
```

**Success response (200)**

```json
{
  "lab_id": "uuid",
  "script_id": "uuid",
  "titles": [
    {
      "candidate_id": "uuid",
      "text": "I Rebuilt My Editing Workflow in 7 Days",
      "scores": {
        "clarity": 8.4,
        "specificity": 8.0,
        "curiosity": 7.5,
        "credibility": 8.8,
        "policy_safety": 9.6,
        "overall": 8.5
      },
      "policy_flags": []
    }
  ],
  "thumbnail_briefs": [
    {
      "candidate_id": "uuid",
      "concept": "Before/after timeline split with creator reaction",
      "overlay_text": "Before vs After",
      "composition": "left/right split",
      "visual_truth_basis": "script shows exact workflow comparison",
      "scores": {
        "clarity": 8.7,
        "story_alignment": 8.9,
        "novelty": 7.3,
        "truthfulness": 9.1,
        "policy_safety": 9.7,
        "overall": 8.7
      },
      "policy_flags": []
    }
  ],
  "pairings": [
    {
      "title_candidate_id": "uuid",
      "thumbnail_candidate_id": "uuid",
      "pair_score": 8.8,
      "rationale": "Strong semantic alignment and honest curiosity gap"
    }
  ],
  "generated_at": "2026-05-16T00:00:00Z"
}
```

**Error responses**
- `400 INVALID_REQUEST` for malformed payload or out-of-range counts.
- `404 SCRIPT_NOT_FOUND` when `script_id` is unknown.
- `409 SCRIPT_NOT_APPROVED` when source script is not in approved state.
- `422 STRICT_JSON_VIOLATION` when model output fails required schema.
- `422 POLICY_CONTRACT_VIOLATION` when payload parses but violates hard truth/policy constraints.
- `503 MODEL_UNAVAILABLE` when generation provider fails/times out.

### 2) Save selected pair

`POST /api/v1/scripts/{script_id}/title-thumbnail-lab/selections`

**Request**

```json
{
  "lab_id": "uuid",
  "title_candidate_id": "uuid",
  "thumbnail_candidate_id": "uuid",
  "reviewer": "string",
  "confidence": 0.82,
  "notes": "Best balance of curiosity and factual grounding.",
  "sync_to_publishing_package": true,
  "publishing_package_id": "uuid"
}
```

**Success response (201)**

```json
{
  "selection_id": "uuid",
  "lab_id": "uuid",
  "script_id": "uuid",
  "sync": {
    "attempted": true,
    "publishing_package_id": "uuid",
    "status": "synced"
  },
  "created_at": "2026-05-16T00:00:00Z"
}
```

**Error responses**
- `404 CANDIDATE_NOT_FOUND` when either candidate is absent from `lab_id`.
- `409 LAB_SUPERSEDED` when selection is attempted on outdated lab output.
- `409 PACKAGE_STATE_CONFLICT` when package is not editable (e.g., `in_review`, `blocked`, `exported`).
- `422 LINKAGE_MISMATCH` when provided package does not map to same script lineage.

### 3) List lab runs and selections

`GET /api/v1/scripts/{script_id}/title-thumbnail-lab/labs`

Returns generated labs, candidate counts, top pair score, and latest saved selection summary for audit/navigation.

## Scoring rubric definitions and ranges

All dimension scores are numeric `0.0..10.0` with one decimal precision. `overall` is weighted and rounded to one decimal.

## Title rubric
- `clarity` (20%): How quickly intent/topic is understood.
- `specificity` (20%): Presence of concrete detail (timeframe, scope, object).
- `curiosity` (20%): Open loop strength without deception.
- `credibility` (20%): Plausibility and claim restraint.
- `policy_safety` (20%): Absence of restricted or misleading framing.

## Thumbnail brief rubric
- `clarity` (20%): Visual idea understood in <1 second.
- `story_alignment` (25%): Matches script’s actual narrative arc.
- `novelty` (15%): Distinctiveness relative to common tropes.
- `truthfulness` (25%): Depicts what video truly contains.
- `policy_safety` (15%): No prohibited sensational/deceptive cues.

## Pair score rubric
- `semantic_alignment` (40%): Title promise matches thumbnail promise.
- `combined_truthfulness` (35%): Pair remains accurate together, not just separately.
- `click_potential` (25%): Predicted CTR upside under policy-safe assumptions.

### Suggested interpretation bands
- `9.0–10.0`: excellent
- `8.0–8.9`: strong
- `7.0–7.9`: usable with edits
- `<7.0`: weak, likely regenerate

## Anti-clickbait and truthfulness constraints

Hard policy constraints are evaluated before candidates are eligible for selection.

1. **No fabricated outcomes or unverifiable guarantees**
   - Reject claims implying certainty where script evidence is probabilistic or absent.
2. **No false urgency/manipulation framing**
   - Disallow exploitative “watch now or fail” style fear claims.
3. **No mismatch between promise and delivered content**
   - Title and thumbnail brief must each map to script sections or documented evidence.
4. **No deceptive visual implication**
   - Thumbnail brief cannot describe scenes/objects/events not present or not reproducibly demonstrable.
5. **No prohibited high-risk claims in restricted domains**
   - e.g., medical, legal, financial guarantees without approved substantiation path.

If a candidate violates a hard rule, set `eligibility = blocked`, attach `policy_flags`, and exclude it from auto-top-pick ranking.

## Selection and PublishingPackage sync behavior

Selection does not publish content by itself; it updates metadata candidates that Publishing Package later governs.

- Sync target fields in package draft:
  - `title` <- selected title text
  - `thumbnail_brief` <- selected brief object (structured JSON)
  - `thumbnail_truth_basis` <- selected brief `visual_truth_basis`
- Sync is allowed only when package state is editable (`draft`, `ready_for_review`, `changes_requested`).
- On sync success, store provenance:
  - `title_thumbnail_selection_id`
  - `lab_id`
  - source `script_revision`
  - sync timestamp and actor
- On sync conflict, selection save remains valid but `sync.status = failed_conflict`; UI offers retry after package returns to editable state.

This behavior must remain consistent with package validation/gating constraints in `docs/product/publishing-package.md`.

## Failure modes and UX states

## UX states
- **Idle**: no lab run yet.
- **Generating**: generation request in flight; controls disabled.
- **Generated**: candidates + scores visible; selection enabled.
- **Blocked Candidates**: some candidates hidden/disabled due to policy flags.
- **Selection Saving**: save/sync mutation in flight.
- **Synced**: selection saved and package updated.
- **Sync Conflict**: selection saved but package sync failed due to state/linkage conflict.
- **Empty History**: no prior labs for script.

## Failure handling expectations
1. `STRICT_JSON_VIOLATION`
   - Show non-destructive inline error with retry.
   - Preserve prior successful lab results in UI.
2. `POLICY_CONTRACT_VIOLATION`
   - Explain violated rule family and allow regenerate with stricter constraints.
3. `MODEL_UNAVAILABLE`
   - Show transient service message and retry affordance.
4. `PACKAGE_STATE_CONFLICT`
   - Keep selection persisted; mark sync failure; deep-link to package state details.
5. `LAB_SUPERSEDED`
   - Prompt refresh and prevent stale-write selection.

## Telemetry and LLM logging expectations

## Product telemetry events
- `tt_lab_generate_requested`
- `tt_lab_generate_succeeded`
- `tt_lab_generate_failed`
- `tt_lab_candidate_policy_blocked`
- `tt_lab_selection_saved`
- `tt_lab_sync_attempted`
- `tt_lab_sync_succeeded`
- `tt_lab_sync_failed`

Each event should include: `script_id`, `lab_id` (when present), actor id/role, latency, model/provider version, and outcome code.

## LLM observability/logging
- Persist prompt template version and input hash (not raw sensitive user data when avoidable).
- Persist raw model response in protected logs for audit/debug with retention controls.
- Persist normalized parsed JSON artifact used by product UI.
- Log schema parse result, policy evaluation result, and final eligibility decision per candidate.
- Attach trace/span ids so cross-service root-cause analysis can correlate lab generation with package sync.

## Privacy and retention guardrails
- Redact direct personal data from analytics payloads.
- Restrict raw prompt/response access to authorized roles.
- Apply bounded retention windows per compliance policy pack.

## Architecture cross-links

- Product workflow alignment: `docs/product/publishing-package.md`
- System architecture baseline: `docs/architecture.md`
- Related generation prompts:
  - `docs/prompts/title-generation.md`
  - `docs/prompts/title-scoring.md`
  - `docs/prompts/thumbnail-brief-generation.md`
