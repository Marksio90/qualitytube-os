# Script Studio Product Flow

Script Studio is the script production workspace that turns an approved idea angle into a revisable, scoreable, approvable script artifact. The feature spans backend API orchestration and frontend editing/approval controls on `/script-studio`.

## End-to-end workflow

1. **Angle precondition**
   - Script generation endpoints require an idea angle status of `approved`.
   - The backend enforces this through `GenerateScriptRequest.angle_status` and rejects non-approved status with `409 ANGLE_NOT_APPROVED` unless draft bypass is enabled.
2. **Draft mode exception**
   - `allow_draft_without_approval=true` bypasses the angle precondition and allows script generation while angle approval is pending.
   - This is intended for early experimentation, not final publishing readiness.
3. **Generation**
   - `generate-outline` creates a structured outline (`hook`, `beats`, `cta`) and persists a canonical draft script.
   - `generate-draft` produces full script sections and persists revision `r1`.
4. **Scoring**
   - `score` computes a `quality_report` with 0–10 dimension scores and an overall score.
   - Approval is blocked until a score exists.
5. **Improve**
   - `improve` regenerates sections from current draft context and appends a new revision (`editor_event` defaults to `ai-improve`).
6. **Approve**
   - `approve` runs approval gates (content, banned phrase, and score thresholds).
   - On pass, script state transitions `draft -> approved`.
7. **Override**
   - `override` force-approves a script with audit metadata (`reason`, `approver`) even if gates would fail.
   - Used as an explicit exception path for human review authority.

## Script data structure

## Script (`Script`)
- `id` (UUID): immutable script id.
- `idea_id` (string): canonical idea linkage; immutable across revisions.
- `angle_id` (string): source angle linkage.
- `state` (`draft` | `approved`): workflow state.
- `sections` (list of `ScriptSection`): required section payload.
- `quality_report` (`ScriptQualityReport | null`): computed quality metrics.

### Section (`ScriptSection`)
- `title` (string, 1–120 chars).
- `content` (string, min 20 chars after trim).

### Required structural rules
- Script must include titles matching: `hook`, `body`, `cta` (case-insensitive check).
- Aggregate trimmed character count across sections must be >= 120.
- Exactly one canonical script is stored per `idea_id`; subsequent edits create versions.

## Scoring rubric (`ScriptQualityReport`)
All dimensions are numeric in range **0.0–10.0**:

- `hook_score`: opening strength and curiosity pull.
- `clarity_score`: readability and explicitness of claims.
- `narrative_tension_score`: pacing, stakes, and forward momentum.
- `originality_score`: novelty and differentiation versus generic advice.
- `retention_score`: expected viewer hold through transitions/beats.
- `evidence_score`: specificity, support, and factual grounding.
- `human_voice_score`: natural conversational tone vs robotic phrasing.
- `cta_quality_score`: clarity/actionability of final call to action.
- `overall_script_score`: blended global script quality.

## Approval gate policy

`POST /api/v1/scripts/{script_id}/approve` enforces gates in order:

1. **Non-empty script**
   - Fails with `EMPTY_SCRIPT` if there are no sections.
2. **Hook quality baseline**
   - Hook section must exist and contain at least 20 trimmed characters.
   - Fails with `HOOK_UNCLEAR` otherwise.
3. **Banned phrase scan**
   - Default blocked phrases:
     - `guaranteed viral`
     - `zero effort success`
   - Match is case-insensitive substring over joined section content.
   - On match: `409 BANNED_PHRASES` with `details.blocked_phrases` containing matched entries.
4. **Score presence**
   - Fails with `MISSING_SCORE` when `quality_report` is absent.
5. **Threshold checks**
   - Defaults: `min_overall_score = 7.0`, `min_hook_score = 7.0`.
   - If either fails, returns `SCORE_BELOW_THRESHOLD` including `metric`, `required`, and `actual`.

### Configurable gate thresholds
- Approve accepts optional `gates` payload:
  - `min_overall_score` (0–10)
  - `min_hook_score` (0–10)
  - `banned_phrases` (string list)
- This supports stricter/looser release modes per operator policy.

## API endpoints summary

### Idea-scoped generation/list
- `POST /api/v1/ideas/{idea_id}/scripts/generate-outline`
  - Body: `{ angle_id, angle_status, allow_draft_without_approval? }`
  - Returns: `{ script, outline }`.
- `POST /api/v1/ideas/{idea_id}/scripts/generate-draft`
  - Body: same as above.
  - Returns: `{ script }`.
- `GET /api/v1/ideas/{idea_id}/scripts`
  - Returns canonical script list for the idea (`0..1` currently).

### Script-scoped edit and quality lifecycle
- `GET /api/v1/scripts/{script_id}` → current script.
- `PATCH /api/v1/scripts/{script_id}`
  - Body: optional `sections`, optional `state`, optional `editor_event`.
  - Creates a new revision.
- `POST /api/v1/scripts/{script_id}/score`
  - Triggers AI scoring and stores `quality_report`.
- `POST /api/v1/scripts/{script_id}/improve`
  - Triggers AI rewrite/improvement and stores updated sections.
- `POST /api/v1/scripts/{script_id}/approve`
  - Runs approval gate policy and sets state to `approved` on success.
- `POST /api/v1/scripts/{script_id}/override`
  - Force-approves with `reason` and `approver` audit fields.

### Revision and comparison
- `GET /api/v1/scripts/{script_id}/versions`
  - Returns version list with `revision`, `created_at`, `editor_event`, and snapshots.
- `GET /api/v1/scripts/{script_id}/compare?from_revision={n}&to_revision={m}`
  - Returns section titles with changed content between revisions.

## Frontend behavior and state mapping

`ScriptStudioPage` maps backend lifecycle to UI state as follows:

- **Bootstrap**
  - On load, fetches `GET /ideas/{idea_id}/scripts`.
  - If empty, auto-generates via `generate-draft` using `angle_status: approved`.
- **Local state atoms**
  - `script`: active canonical script object.
  - `loading`: workspace load spinner.
  - `saving`: action-in-flight lock for save/improve/score/approve/override.
  - `error`: top-level load failure.
  - `actionError`: action-specific backend failure display.
  - `revisionData`: versions fetch state and payload.
  - `selectedRevision`: selected revision id for snapshot preview.
- **Action mapping**
  - Save button -> `PATCH /scripts/{id}` with `editor_event: manual-edit`.
  - Improve button -> `POST /scripts/{id}/improve`.
  - Rescore button -> `POST /scripts/{id}/score`.
  - Approve button -> `POST /scripts/{id}/approve`.
  - Override Approve button -> `POST /scripts/{id}/override`.
- **Warnings panel (pre-gate signals)**
  - Detects banned phrases client-side (`guaranteed viral`, `zero effort success`).
  - Warns when script is unscored.
  - Warns when `overall_script_score < 7`.
  - Warns when `hook_score < 7`.
  - These warnings are advisory; server gates remain source of truth.

## State machine reference

- Initial state: `draft`.
- Allowed transitions in current implementation:
  - `draft -> approved` via `approve` (gate pass).
  - `draft -> approved` via `override` (manual force-approve).
  - `approved` can still be patched/improved/rescored; state remains unless explicitly patched.

## Notes for product and QA

- Approval logic is deterministic and server-side; frontend warnings mirror defaults but should not be treated as authoritative policy.
- Banned phrase behavior is substring-based and case-insensitive, so partial sentence inclusion still fails approval.
- Version history is append-only per canonical script and should be used for audit and comparison workflows.
