# Hook Retention Lab Product Flow

Hook Retention Lab is the Script Studio sub-workflow for generating multiple opening-hook variants, scoring their predicted retention impact, and recording review outcomes before a script moves to final approval.

## Feature goals and Script Studio workflow

1. **Increase opening performance before full script polish**
   - Provide fast generation of multiple hook options from the current script context.
   - Surface retention-focused signals early so creators can select a strong opener before deeper edits.
2. **Keep the workflow embedded in Script Studio**
   - Hook Retention Lab is launched from an existing script in `/script-studio`.
   - The active script is the required dependency for all variant generation and review operations.
3. **Enable structured human + AI review loop**
   - AI proposes hook variants and retention rationale.
   - Human reviewer selects a preferred variant, captures notes, and optionally applies the variant back to script sections.
4. **Preserve full audit trail**
   - Every generated variant and review decision is versioned and attributable to actor + timestamp.

### In-product workflow sequence

1. Open Script Studio with an existing script in `draft` or `approved` state.
2. Open **Hook Retention Lab** panel for the active script.
3. Submit variant generation request (count, tone, target audience constraints).
4. Receive strictly structured JSON payload of hook variants with retention diagnostics.
5. Review variants, score confidence, and choose one of:
   - mark variant as winner,
   - request regeneration,
   - dismiss low-quality variants.
6. Save retention review entry.
7. Optionally apply winning variant to the script `hook` section and create a new script revision.

## Backend endpoint contracts

All endpoints are script-scoped and require a valid `script_id`.

### 1) Generate hook variants

`POST /api/v1/scripts/{script_id}/hook-retention/generate`

**Request**

```json
{
  "variant_count": 5,
  "style_constraints": ["punchy", "specific"],
  "target_audience": "early-career creators",
  "max_hook_chars": 220,
  "context": {
    "video_goal": "increase 30-second retention",
    "topic": "story-driven editing"
  }
}
```

**Success response (200)**

```json
{
  "lab_id": "uuid",
  "script_id": "uuid",
  "variants": [
    {
      "variant_id": "uuid",
      "hook_text": "string",
      "retention_hypothesis": "string",
      "expected_dropoff_risk": "low",
      "predicted_retention_score": 8.1,
      "signals": {
        "curiosity_gap": 8.7,
        "clarity": 7.9,
        "novelty": 7.4,
        "tempo": 8.0
      }
    }
  ],
  "generated_at": "2026-05-15T00:00:00Z"
}
```

**Error responses**

- `400 INVALID_REQUEST` for malformed fields, out-of-range counts, or unsupported enums.
- `404 SCRIPT_NOT_FOUND` when `script_id` does not resolve.
- `409 SCRIPT_DEPENDENCY_MISSING` when no canonical script sections are available for dependency context.
- `422 STRICT_JSON_VIOLATION` when upstream model output cannot be parsed into required schema.
- `503 MODEL_UNAVAILABLE` when generation provider fails or times out.

### 2) Submit retention review

`POST /api/v1/scripts/{script_id}/hook-retention/reviews`

**Request**

```json
{
  "lab_id": "uuid",
  "winning_variant_id": "uuid",
  "reviewer": "string",
  "decision": "accept",
  "confidence": 0.86,
  "notes": "Variant 3 has strongest tension and specificity.",
  "apply_to_script": true
}
```

**Success response (201)**

```json
{
  "review_id": "uuid",
  "script_id": "uuid",
  "lab_id": "uuid",
  "decision": "accept",
  "applied_revision": 4,
  "created_at": "2026-05-15T00:00:00Z"
}
```

**Error responses**

- `400 INVALID_REQUEST` for missing required review fields.
- `404 VARIANT_NOT_FOUND` when `winning_variant_id` is not part of the specified lab.
- `409 REVIEW_CONFLICT` when review attempts to apply a stale variant after script changed.
- `422 STRICT_JSON_VIOLATION` if payload parsing fails strict schema.

### 3) Fetch lab history

`GET /api/v1/scripts/{script_id}/hook-retention/labs`

**Success response (200)**

```json
{
  "script_id": "uuid",
  "labs": [
    {
      "lab_id": "uuid",
      "status": "reviewed",
      "variant_count": 5,
      "winner_variant_id": "uuid",
      "last_reviewed_at": "2026-05-15T00:00:00Z"
    }
  ]
}
```

## Validation requirements

1. **Strict JSON contract (no loose text fallback)**
   - AI generation output must parse as valid JSON object matching exact Hook Variant schema.
   - Unknown keys are rejected in strict mode.
   - Type coercion is disallowed (e.g., string `"8.1"` is invalid for numeric fields).
2. **Required script dependency**
   - Hook generation requires an existing script with non-empty `hook` + `body` context.
   - If script is missing, empty, or soft-deleted, requests fail with `SCRIPT_DEPENDENCY_MISSING`.
3. **Field-level constraints**
   - `variant_count`: integer range `1..10`.
   - `max_hook_chars`: integer range `80..300`.
   - `predicted_retention_score` and signal scores: numeric range `0.0..10.0`.
   - `decision`: enum `accept | reject | regenerate`.
4. **Cross-entity integrity checks**
   - `winning_variant_id` must belong to provided `lab_id` and `script_id`.
   - Apply-to-script path requires script version lock to avoid stale overwrite.

## Data persistence model

Hook Retention Lab persistence should preserve generated artifacts and reviewer decisions as separate, linked entities.

### Table: `hook_retention_labs`
- `id` (UUID, PK)
- `script_id` (UUID, FK -> scripts.id)
- `created_by` (string)
- `prompt_config` (JSONB)
- `status` (`generated | reviewed | superseded`)
- `created_at`, `updated_at` (timestamp)

### Table: `hook_retention_variants`
- `id` (UUID, PK)
- `lab_id` (UUID, FK -> hook_retention_labs.id)
- `script_id` (UUID, indexed)
- `hook_text` (text)
- `retention_hypothesis` (text)
- `expected_dropoff_risk` (enum: `low | medium | high`)
- `predicted_retention_score` (numeric(3,1))
- `signals` (JSONB)
- `rank_order` (int)
- `created_at` (timestamp)

### Table: `hook_retention_reviews`
- `id` (UUID, PK)
- `lab_id` (UUID, FK)
- `script_id` (UUID, FK)
- `winning_variant_id` (UUID, nullable for reject/regenerate)
- `decision` (enum: `accept | reject | regenerate`)
- `confidence` (numeric(3,2), nullable)
- `notes` (text)
- `reviewer` (string)
- `applied_script_revision` (int, nullable)
- `created_at` (timestamp)

### Derived relationships and lifecycle
- One script can have many labs.
- One lab can have many variants and many reviews (append-only review audit).
- Latest accepted review may be denormalized on `hook_retention_labs` for fast UI retrieval.

## Known UX states and failure handling

### UX states

- **Idle**: panel unopened or awaiting user action.
- **Generating**: request in flight; generation controls disabled.
- **Generated**: variants loaded; review actions enabled.
- **Review Saving**: review submission in flight.
- **Applied**: winning variant applied to script and revision incremented.
- **Empty History**: no prior labs for script.

### Failure handling behaviors

1. **Strict JSON parse failure (`422 STRICT_JSON_VIOLATION`)**
   - Show non-destructive inline error.
   - Keep prior successful variants visible.
   - Offer `Regenerate` with same parameters.
2. **Script dependency failure (`409 SCRIPT_DEPENDENCY_MISSING`)**
   - Block generation CTA.
   - Prompt user to create or load script draft first.
3. **Timeout/provider failure (`503 MODEL_UNAVAILABLE`)**
   - Display retry affordance with exponential backoff guidance.
   - Preserve form inputs for quick retry.
4. **Stale apply conflict (`409 REVIEW_CONFLICT`)**
   - Inform user script changed since variant creation.
   - Offer compare + regenerate path bound to latest script revision.
5. **Network/intermittent errors**
   - Use optimistic-disabled controls with explicit retry button.
   - Avoid silent failures; always show actionable message and trace id when available.
