# Compliance Guard

## Purpose

Compliance Guard is a pre-publish control layer that evaluates synthetic or AI-assisted content against policy constraints before content can be released.

## Architecture

- **Ingress Layer**: receives content package (asset, metadata, provenance, destination).
- **Policy Classifier**: determines applicable policy packs (content type, jurisdictional or platform overlays, sensitivity class).
- **Compliance Review Engine**: executes deterministic checks + model-assisted checks using the compliance review prompt.
- **Risk Scoring Module**: aggregates findings into normalized severity bands.
- **Decision Gate**: enforces allow/hold/block outcome.
- **Audit Logger**: stores decision artifacts, evidence pointers, and reviewer metadata.
- **Override Controller**: handles exceptional manual overrides under strict controls.

## End-to-End Flow

1. Content enters Ingress Layer with provenance and destination metadata.
2. Policy Classifier selects required checks (reuse, disclosure, misleading/copyright/sensitive-topic, human contribution).
3. Compliance Review Engine executes checks and emits strict-schema JSON.
4. Risk Scoring Module computes aggregate risk and blocking reasons.
5. Decision Gate applies gate criteria:
   - **ALLOW**: no blocking findings; required disclosures present.
   - **HOLD**: uncertain/high-risk findings needing human review.
   - **BLOCK**: hard-policy violations (e.g., required disclosure absent, prohibited deceptive content, critical copyright risk).
6. Audit Logger records full trace for governance and incident response.

## Gate Criteria

### Allow

- No critical policy violations.
- All mandatory fields complete.
- Disclosure requirements satisfied where applicable.
- Human contribution requirements satisfied where applicable.

### Hold

- Ambiguous classification or confidence below threshold.
- Sensitive-topic flags requiring specialist review.
- Possible copyright/misleading issues with incomplete evidence.

### Block

- Missing required disclosure.
- Confirmed deceptive or prohibited claims.
- Confirmed high-confidence copyright infringement risk.
- Missing required human contribution when policy mandates it.
- Output contract violations (schema mismatch preventing reliable downstream enforcement).

## Override Policy

Overrides are exceptional and must be tightly governed.

- Allowed only for **HOLD** or narrowly defined false-positive **BLOCK** cases.
- Requires authorized human approver identity, reason code, and written rationale.
- Must capture scope (single asset vs. batch), expiration (time-bound), and compensating controls.
- Overrides for legal/compliance constraints do not constitute legal clearance.
- Overrides cannot be used to bypass mandatory disclosure obligations.
- All overrides are auditable and subject to periodic retrospective review.

## Non-Legal Positioning

Compliance Guard provides policy enforcement support. It does **not** provide legal advice and does not guarantee legal compliance.
