# Publishing Package Product Flow

Publishing Package is the pre-release bundling and governance workflow that converts an approved Script Studio artifact into an exportable deliverable package gated by Compliance Guard.

## Workflow sequence and prerequisites

1. **Script readiness precondition**
   - Input script must exist and be in Script Studio state `approved`.
   - Draft-mode script artifacts are not publish-ready, even when generated with `allow_draft_without_approval`.
2. **Package assembly**
   - Operator creates a package shell from an approved script and selects destination profile(s).
   - System snapshots current script revision and immutable linkage (`idea_id`, `angle_id`, `script_id`, `revision`).
3. **Metadata completion**
   - Required package metadata, disclosure fields, and provenance fields are completed.
   - Field-level validation runs on save and again at submission.
4. **Compliance preflight**
   - Compliance Guard Ingress receives package payload (content + metadata + destination).
   - Policy Classifier selects applicable checks and Compliance Review Engine emits findings.
5. **Approval gates**
   - Decision Gate applies Script Studio readiness gates + Compliance Guard outcome.
   - High-risk compliance findings trigger a hard block (no export).
6. **Export generation**
   - On gate pass, export artifacts are generated in selected formats.
   - Package status advances to `exported` and audit event is recorded.

## Required fields and validation rules

## Package identity and linkage
- `package_id` (UUID): immutable package identifier.
- `script_id` (UUID): required; must resolve to an existing script.
- `idea_id` (string): required; must match linked script.
- `angle_id` (string): required; must match linked script.
- `script_revision` (integer): required; must reference an existing stored revision.

### Validation rules
- Linkage mismatch fails validation (`LINKAGE_MISMATCH`).
- Unknown script or revision fails validation (`SOURCE_NOT_FOUND`).
- Script state not `approved` fails submission (`SCRIPT_NOT_APPROVED`).

## Destination and release metadata
- `destination` (enum/string): required target channel profile.
- `locale` (IETF language tag): required when destination profile marks locale as mandatory.
- `title` (string, 1–120 chars): required.
- `description` (string, 1–5000 chars): required for long-form destinations.
- `tags` (array of strings): optional unless destination profile requires minimum tag count.

### Validation rules
- Title and description are trimmed before length checks.
- Unsupported destination fails validation (`DESTINATION_UNSUPPORTED`).
- Destination-specific requirement failures return `DESTINATION_REQUIREMENT_FAILED` with field details.

## Provenance and disclosure metadata
- `ai_assistance_used` (boolean): required.
- `human_editor` (string): required when human contribution policy applies.
- `disclosure_text` (string): conditionally required by policy pack/destination.
- `source_attribution` (array): required when evidence/copyright policy indicates citations are mandatory.

### Validation rules
- Missing required disclosure fails gate as hard block (`MISSING_DISCLOSURE`).
- Missing required human contribution fails gate (`MISSING_HUMAN_CONTRIBUTION`).
- Empty disclosure strings after trim are treated as missing.

## Approval gates and high-risk compliance block

Approval is evaluated in deterministic order:

1. **Structural package integrity**
   - Required fields and linkage checks must pass.
2. **Script Studio readiness gate**
   - Source script must remain `approved` at evaluation time.
   - Optional freshness policy may require latest scored revision.
3. **Compliance Guard decision gate**
   - `ALLOW`: gate passes and export may continue.
   - `HOLD`: package moves to manual review queue; export is paused.
   - `BLOCK`: package is rejected; export is denied.
4. **High-risk compliance block (hard stop)**
   - Any critical finding (e.g., missing required disclosure, confirmed deceptive claim, confirmed critical copyright risk) forces terminal block.
   - Override is not allowed for mandatory disclosure obligations.

### Override boundaries
- Override path is exceptional and auditable.
- Only eligible `HOLD` (and narrowly-scoped false-positive `BLOCK`) outcomes may be overridden by authorized approvers.
- High-risk mandatory-disclosure failures cannot be overridden.

## Endpoint behaviors and export formats

## Endpoint summary
- `POST /api/v1/publishing-packages`
  - Creates package shell from approved script linkage.
  - Returns `201` with package in `draft` status.
- `GET /api/v1/publishing-packages/{package_id}`
  - Returns current package state, validation errors, and latest gate decision.
- `PATCH /api/v1/publishing-packages/{package_id}`
  - Updates mutable metadata fields; re-runs field validation.
- `POST /api/v1/publishing-packages/{package_id}/submit`
  - Freezes editable fields, runs full gate evaluation, and transitions state to `in_review`, `blocked`, or `approved_for_export`.
- `POST /api/v1/publishing-packages/{package_id}/review-decision`
  - Manual reviewer action for `HOLD` queue (`approve`, `request_changes`, `block`).
- `POST /api/v1/publishing-packages/{package_id}/export`
  - Generates exports only when gate state is export-eligible.
- `GET /api/v1/publishing-packages/{package_id}/exports`
  - Lists generated artifacts with format, checksum, and timestamp.

## Response and error behavior
- Validation failures return `422` with `details.fields` map.
- Gate denial returns `409` with machine-readable code and finding summary.
- Compliance engine schema/output contract failures return `409 OUTPUT_CONTRACT_VIOLATION` and force `BLOCK`.

## Export formats
Supported export formats are destination-profile driven and may include:
- `json` (canonical machine payload)
- `md` (editorial handoff)
- `txt` (plain text fallback)
- `csv` (batch metadata manifests)

### Export guarantees
- Every export includes package metadata header and source linkage identifiers.
- Canonical `json` is always generated when export succeeds.
- Artifact checksums are emitted for downstream integrity verification.

## UI behavior and status lifecycle

## UI behavior
- Publishing Package panel is disabled unless source script state is `approved`.
- Field-level validation appears inline on blur and on submit.
- Compliance findings are grouped by severity band and show gate impact (`ALLOW`, `HOLD`, `BLOCK`).
- When `HOLD`, UI exposes manual review queue state and reviewer notes.
- When `BLOCK`, UI displays blocking findings and required remediation actions.

## Status lifecycle

- `draft`
  - Initial package state after creation.
  - Editable fields remain mutable.
- `ready_for_review`
  - Client-side validation passed; awaiting submit action.
- `in_review`
  - Submitted and currently in Compliance Guard evaluation or manual review.
- `changes_requested`
  - Reviewer requested edits; package returns to editable state.
- `blocked`
  - Decision Gate or high-risk compliance block denied release.
- `approved_for_export`
  - Gates satisfied and package is export-eligible.
- `exported`
  - One or more export artifacts generated successfully.

### Transition notes
- `draft -> ready_for_review` requires local field validity.
- `ready_for_review -> in_review` occurs on successful submit.
- `in_review -> approved_for_export | changes_requested | blocked` is driven by automated + manual gate outcomes.
- `approved_for_export -> exported` occurs after successful export generation.
