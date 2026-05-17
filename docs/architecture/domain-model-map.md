# QualityTube OS — Domain Model Map

> **Status:** Authoritative mapping between canonical QualityTube OS domain concepts and their current implementation state.
> **Updated:** 2026-05-17
> **Rule:** Do not create a new concept if an equivalent exists. Do not rename without a compatibility adapter.

---

## How to read this document

| Column | Meaning |
|---|---|
| **Canonical concept** | The single authoritative name used across the entire system |
| **Existing implementation** | What exists today in `backend/app/modules/` |
| **Decision** | `reuse` · `extend` · `rename-later` · `create-new` |
| **Reason** | Why the decision was made |
| **Related files** | Source files affected |
| **Migration impact** | Whether an Alembic migration is required |
| **API impact** | Changes visible to API consumers |
| **Frontend/contract impact** | Changes visible to frontend or shared types |

---

## 1. Organization

| Field | Value |
|---|---|
| **Canonical concept** | `Organization` |
| **Existing implementation** | Does not exist |
| **Decision** | `create-new` |
| **Reason** | Top-level multi-tenant container. Required for agency use cases where multiple independent teams share an installation. Not implemented in the current scaffold, which has no auth or tenancy. |
| **Related files** | `backend/app/db/models/organization.py` (new ORM), `backend/app/modules/organization.py` (new Pydantic schema) |
| **Migration impact** | Yes — creates `organizations` table in initial migration |
| **API impact** | New endpoints in Phase 17 (auth + tenancy). No existing endpoints affected. |
| **Frontend/contract impact** | None until auth is introduced |

**ORM fields:** `id` (UUID PK), `name` (str, unique), `slug` (str, unique), `created_at`, `updated_at`

---

## 2. Workspace

| Field | Value |
|---|---|
| **Canonical concept** | `Workspace` |
| **Existing implementation** | Does not exist |
| **Decision** | `create-new` |
| **Reason** | A project or team within an Organization. Multiple workspaces per org. A single creator might have one workspace; an agency might have one per client. Required for multi-project isolation below org level. |
| **Related files** | `backend/app/db/models/organization.py` (co-located with Organization ORM), `backend/app/modules/organization.py` |
| **Migration impact** | Yes — creates `workspaces` table in initial migration |
| **API impact** | New endpoints in Phase 17. No existing endpoints affected. |
| **Frontend/contract impact** | None until auth is introduced |

**ORM fields:** `id` (UUID PK), `org_id` (FK → organizations), `name`, `slug`, `created_at`, `updated_at`

---

## 3. Channel

| Field | Value |
|---|---|
| **Canonical concept** | `Channel` |
| **Existing implementation** | Partially: `ChannelMemory` in `modules/channel_memory.py` holds `channel_id`, `tone_notes`, `banned_claims`. No Channel entity with lifecycle or YouTube link. |
| **Decision** | `create-new` (Channel ORM) + `extend` (ChannelMemory Pydantic) |
| **Reason** | `ChannelMemory` is a configuration blob, not a Channel entity. A `Channel` needs a full lifecycle (create, connect to YouTube, update profile). `ChannelMemory` should become a sub-document of `Channel`, not a separate entity. For backwards compatibility, `ChannelMemory` Pydantic model is kept as-is in `modules/`; the ORM `Channel` model absorbs its fields. |
| **Related files** | `backend/app/modules/channel_memory.py` (keep, no changes), `backend/app/modules/channel.py` (new Pydantic), `backend/app/db/models/channel.py` (new ORM) |
| **Migration impact** | Yes — creates `channels` table. `ChannelMemory` data migrates into `channels` rows when database layer is activated. |
| **API impact** | New `GET/POST/PATCH /api/v1/channels` endpoints (Phase 3). Existing endpoints that accept `channel_id` string continue to work via `ChannelMemoryRepository` until migration cutover. |
| **Frontend/contract impact** | No breaking changes. Channel Workspace UI additions only. |

**ORM fields:** `id` (UUID PK), `workspace_id` (FK → workspaces), `name`, `youtube_channel_id` (nullable), `language` (default `en`), `upload_schedule_target` (nullable int, videos/month), `tone_notes` (JSON array), `banned_claims` (JSON array), `content_pillars` (JSON array), `audience_description` (text), `created_at`, `updated_at`

---

## 4. ContentIdea

| Field | Value |
|---|---|
| **Canonical concept** | `ContentIdea` |
| **Existing implementation** | `Idea` in `modules/ideas.py` — fields: `id` (str), `title`, `audience`, `premise`. Model is defined but **never used** in any API endpoint. |
| **Decision** | `extend` + `rename-later` |
| **Reason** | `Idea` is the right concept but is too minimal (4 fields, no status, no channel link, no timestamps). Extending it to `ContentIdea` gives the canonical name while keeping `Idea` as an alias for backwards compatibility. The rename from `Idea` to `ContentIdea` in `__init__.py` exports can happen in Phase 4 when API endpoints are added. |
| **Related files** | `backend/app/modules/ideas.py` (extend in-place), `backend/app/db/models/content.py` (new ORM) |
| **Migration impact** | Yes — creates `content_ideas` table |
| **API impact** | New `GET/POST/PATCH /api/v1/ideas` endpoints (Phase 4). `idea_id` path param in existing endpoints remains a string; when DB is active, it must resolve to a valid UUID. |
| **Frontend/contract impact** | `ideaId` route param in `AppRoutes.jsx` already uses string IDs — no change needed until UUID enforcement is added. |

**ORM fields:** `id` (UUID PK), `channel_id` (FK → channels), `title`, `audience`, `premise`, `status` (enum: `draft`, `researched`, `angle_pending`, `angle_approved`, `scripting`, `in_review`, `published`, `archived`), `created_at`, `updated_at`

---

## 5. ResearchBrief

| Field | Value |
|---|---|
| **Canonical concept** | `ResearchBrief` |
| **Existing implementation** | `ResearchBrief` in `modules/research_brief.py` — fields: `topic`, `goals: list[str]`, `references: list[str]`. Defined and exported but **never instantiated** in any API endpoint or service. |
| **Decision** | `extend` |
| **Reason** | The existing model is a correct stub but is missing: `idea_id` linkage, `key_questions`, `originality_notes`, `id`, timestamps. Extend the existing file rather than creating a parallel concept. |
| **Related files** | `backend/app/modules/research_brief.py` (extend), `backend/app/db/models/content.py` (ORM co-located with ContentIdea) |
| **Migration impact** | Yes — creates `research_briefs` table |
| **API impact** | New `POST /api/v1/ideas/{idea_id}/research-brief` endpoint (Phase 8). No existing endpoints affected. |
| **Frontend/contract impact** | None currently — no frontend page uses ResearchBrief yet |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `topic`, `goals` (JSON), `references` (JSON), `key_questions` (JSON), `originality_notes` (text), `created_at`, `updated_at`

---

## 6. Angle

| Field | Value |
|---|---|
| **Canonical concept** | `Angle` |
| **Existing implementation** | `AngleStatus` enum only (`pending`, `approved`, `rejected`) in `modules/angle_approval.py`. No `Angle` entity model exists. Angle identity is passed as a raw `angle_id` string to all script generation endpoints. |
| **Decision** | `create-new` |
| **Reason** | An `Angle` is a first-class domain entity: it has an argument, an originality claim, evidence requirements, scoring, and a lifecycle. `AngleStatus` is retained as the enum for its `status` field. The current string-passing pattern is a temporary workaround to be resolved in Phase 4. |
| **Related files** | `backend/app/modules/angle_approval.py` (keep enum, no changes), `backend/app/modules/angle.py` (new Pydantic), `backend/app/db/models/content.py` (ORM co-located) |
| **Migration impact** | Yes — creates `angles` table |
| **API impact** | New angle lifecycle endpoints (Phase 4/9). Existing `angle_id` string params in script endpoints remain unchanged until Phase 9 connects angles to persisted records. |
| **Frontend/contract impact** | None until angle board UI is added (Phase 9) |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `title`, `argument`, `counter_narrative`, `audience_benefit`, `evidence_requirement`, `originality_score` (float, nullable), `differentiation_score` (float, nullable), `audience_value_score` (float, nullable), `status` (AngleStatus enum), `created_at`, `updated_at`

---

## 7. Script

| Field | Value |
|---|---|
| **Canonical concept** | `Script` |
| **Existing implementation** | `Script` in `modules/scripts.py` — fully implemented Pydantic model with `id` (UUID), `idea_id` (str), `angle_id` (str), `state` (ScriptState), `sections` (list[ScriptSection]), `quality_report` (optional). `ScriptRepository` (in-memory). 11 API endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | The Pydantic model and repository are correct and battle-tested. The ORM model adds persistence but keeps the same field structure. `sections` and `quality_report` are stored as JSON columns — they are already structured JSON, not relational data. |
| **Related files** | `backend/app/modules/scripts.py` (no changes to Pydantic), `backend/app/db/models/script.py` (new ORM) |
| **Migration impact** | Yes — creates `scripts` table |
| **API impact** | Zero. All 11 script endpoints continue to work via `ScriptRepository`. Database swap is a repository-internal change. |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `angle_id` (str, later FK → angles), `state` (ScriptState enum), `sections` (JSON), `quality_report` (JSON, nullable), `created_at`, `updated_at`

---

## 8. ScriptVersion

| Field | Value |
|---|---|
| **Canonical concept** | `ScriptVersion` |
| **Existing implementation** | `ScriptVersion` in `modules/scripts.py` — Pydantic model: `id` (UUID), `script_id`, `revision` (int), `created_at`, `editor_event`, `script_snapshot` (full Script). Stored in-memory in `ScriptRepository._versions_by_script_id`. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. `script_snapshot` becomes a JSON column. Revision history is append-only by design — no updates to version records. |
| **Related files** | `backend/app/modules/scripts.py` (no changes), `backend/app/db/models/script.py` |
| **Migration impact** | Yes — creates `script_versions` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `script_id` (FK → scripts), `revision` (int), `editor_event`, `script_snapshot` (JSON), `created_at`

---

## 9. HookVariant

| Field | Value |
|---|---|
| **Canonical concept** | `HookVariant` |
| **Existing implementation** | `HookVariant` in `modules/scripts.py` — fully implemented Pydantic model with all required fields. Stored in `ScriptRepository._hooks_by_script_id`. 4 hook API endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept and implementation. ORM adds persistence. |
| **Related files** | `backend/app/modules/scripts.py` (no changes), `backend/app/db/models/script.py` |
| **Migration impact** | Yes — creates `hook_variants` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `script_id` (FK → scripts), `type` (HookVariantType enum), `text`, `promise`, `curiosity_gap`, `risk_level` (int 0–5), `score` (float), `notes`, `selected` (bool), `created_at`, `updated_at`

---

## 10. RetentionReview

| Field | Value |
|---|---|
| **Canonical concept** | `RetentionReview` |
| **Existing implementation** | `RetentionReview` in `modules/scripts.py` — Pydantic model with 6 boolean warning flags, `section_map`, `recommendations`, `timestamps`. Stored in `ScriptRepository._retention_reviews_by_script_id`. 2 retention API endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. Boolean flags become columns; list fields become JSON. |
| **Related files** | `backend/app/modules/scripts.py` (no changes), `backend/app/db/models/script.py` |
| **Migration impact** | Yes — creates `retention_reviews` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `script_id` (FK → scripts), `weak_intro_warning` (bool), `slow_context_warning` (bool), `payoff_delay_warning` (bool), `repeated_sentence_warning` (bool), `generic_section_warning` (bool), `unclear_promise_warning` (bool), `section_map` (JSON), `recommendations` (JSON), `timestamps` (JSON), `created_at`, `updated_at`

---

## 11. VisualPlan

| Field | Value |
|---|---|
| **Canonical concept** | `VisualPlan` |
| **Existing implementation** | `VisualPlan` in `modules/visual_plan.py` — Pydantic model with `id` (UUID), `script_id`, `scenes` (list[VisualScene]), `approval_state` (VisualPlanApprovalState). `VisualPlanRepository` (in-memory). 4 visual plan endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. In the ORM, `scenes` move to a child `visual_scenes` table rather than a JSON column — this enables per-scene approval state (Phase 15). |
| **Related files** | `backend/app/modules/visual_plan.py` (no changes to Pydantic), `backend/app/db/models/media.py` (new ORM) |
| **Migration impact** | Yes — creates `visual_plans` and `visual_scenes` tables |
| **API impact** | Zero initially. Per-scene approval endpoints added in Phase 15. |
| **Frontend/contract impact** | Zero |

**ORM fields (visual_plans):** `id` (UUID PK), `script_id` (FK → scripts), `approval_state` (enum), `created_at`, `updated_at`

---

## 12. VisualScene

| Field | Value |
|---|---|
| **Canonical concept** | `VisualScene` |
| **Existing implementation** | `VisualScene` in `modules/visual_plan.py` — Pydantic model with all fields. Currently stored as a list within `VisualPlan` in-memory. |
| **Decision** | `reuse` + `extend` (ORM — separate table) |
| **Reason** | Moving scenes to a separate table enables per-scene approval state and efficient querying by risk level. `scene_approval_state` is a new field not in the current Pydantic model — it will be added in Phase 15. |
| **Related files** | `backend/app/modules/visual_plan.py` (no changes to Pydantic), `backend/app/db/models/media.py` |
| **Migration impact** | Yes — creates `visual_scenes` table (child of `visual_plans`) |
| **API impact** | Zero initially |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `plan_id` (FK → visual_plans), `scene_number` (int), `narration_excerpt` (text), `visual_type` (enum), `visual_description` (text), `purpose` (text), `asset_notes` (text, nullable), `risk_notes` (text, nullable), `filler_risk_score` (float), `scene_approval_state` (enum: `draft`, `approved`, `revision_requested`, `rejected`, default `draft`)

---

## 13. AudioBrief

| Field | Value |
|---|---|
| **Canonical concept** | `AudioBrief` |
| **Existing implementation** | `AudioBrief` in `modules/audio_brief.py` — fully implemented Pydantic model. `AudioBriefRepository` (in-memory). 5 audio brief endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept and implementation. ORM adds persistence. |
| **Related files** | `backend/app/modules/audio_brief.py` (no changes), `backend/app/db/models/media.py` |
| **Migration impact** | Yes — creates `audio_briefs` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `script_id` (FK → scripts), `voice_style` (enum), `pace_wpm` (int), `emotional_tone`, `pause_notes`, `pronunciation_notes`, `emphasis_notes`, `synthetic_voice_used` (bool), `disclosure_required` (bool), `disclosure_notes` (nullable), `export_text`, `approval_state` (ApprovalState enum), `created_at`, `updated_at`

---

## 14. TitleVariant

| Field | Value |
|---|---|
| **Canonical concept** | `TitleVariant` |
| **Existing implementation** | `TitleVariant` in `modules/title_thumbnail_lab.py` — fully implemented Pydantic model. `TitleThumbnailLabRepository` (in-memory). 3 title endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. ORM adds persistence. |
| **Related files** | `backend/app/modules/title_thumbnail_lab.py` (no changes), `backend/app/db/models/publishing.py` (ORM co-located with ThumbnailConcept) |
| **Migration impact** | Yes — creates `title_variants` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `title_text`, `selected` (bool), `clarity_score` (float), `curiosity_score` (float), `truthfulness_score` (float), `promise_match_score` (float), `clickbait_risk` (float), `overall_title_score` (float), `rationale` (nullable), `warnings` (nullable), `created_at`

---

## 15. ThumbnailConcept

| Field | Value |
|---|---|
| **Canonical concept** | `ThumbnailConcept` |
| **Existing implementation** | `ThumbnailConcept` in `modules/title_thumbnail_lab.py` — fully implemented Pydantic model. `TitleThumbnailLabRepository`. 3 thumbnail endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. ORM adds persistence. |
| **Related files** | `backend/app/modules/title_thumbnail_lab.py` (no changes), `backend/app/db/models/publishing.py` |
| **Migration impact** | Yes — creates `thumbnail_concepts` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `selected` (bool), `main_object`, `emotion`, `composition`, `text_overlay`, `visual_contrast`, `mobile_readability_notes`, `avoid`, `score` (float), `created_at`

---

## 16. PublishingPackage

| Field | Value |
|---|---|
| **Canonical concept** | `PublishingPackage` |
| **Existing implementation** | `PublishingPackage` in `modules/publishing_package.py` — fully implemented Pydantic model with strict validation. `PublishingPackageRepository` (in-memory). 7 publishing endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. No naming conflict. `latest_compliance` FK becomes a proper FK column in the ORM. List fields (`tags`, `chapters`, `upload_checklist`) become JSON columns. |
| **Related files** | `backend/app/modules/publishing_package.py` (no changes), `backend/app/db/models/publishing.py` |
| **Migration impact** | Yes — creates `publishing_packages` and `publishing_package_revisions` tables |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `compliance_report_id` (FK → compliance_reports, nullable), `title`, `description` (text), `tags` (JSON), `chapters` (JSON), `pinned_comment` (nullable), `thumbnail_brief` (text), `disclosure_notes` (nullable), `source_notes` (nullable), `upload_checklist` (JSON), `status` (PublishingPackageStatus enum), `created_at`, `updated_at`

---

## 17. ComplianceReport

| Field | Value |
|---|---|
| **Canonical concept** | `ComplianceReport` |
| **Existing implementation** | `ComplianceReport` in `modules/compliance.py` — fully implemented Pydantic model with strict validation and conditional field validators. Stored in two dicts directly in `main.py`. 5 compliance endpoints. |
| **Decision** | `reuse` + `extend` (ORM) |
| **Reason** | Correct concept. No naming conflict with `ComplianceCheck` — the deterministic check result (`ComplianceCheckResult`) is an intermediate computation type, not a stored entity. The `ComplianceReport` is the persisted artifact. All risk fields become enum columns. Override audit log becomes a JSON column. |
| **Related files** | `backend/app/modules/compliance.py` (no changes), `backend/app/modules/compliance_checks.py` (no changes), `backend/app/db/models/compliance.py` (new ORM) |
| **Migration impact** | Yes — creates `compliance_reports` table |
| **API impact** | Zero |
| **Frontend/contract impact** | Zero |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `reused_content_risk` (enum), `repetitive_content_risk` (enum), `mass_production_risk` (enum), `synthetic_content_disclosure_required` (bool), `copyright_risk` (enum), `misleading_claims_risk` (enum), `sensitive_topic_risk` (enum), `clickbait_risk` (enum), `originality_evidence` (JSON), `human_contribution_evidence` (JSON), `overall_risk` (enum), `recommendation` (enum), `required_fixes` (JSON), `reviewer_notes` (text), `reviewer_source` (enum), `approval_state` (enum), `override_reason` (nullable), `override_actor` (nullable), `override_recommendation` (nullable), `override_overall_risk` (nullable), `is_manually_overridden` (bool), `override_audit_log` (JSON), `created_at`, `updated_at`

---

## 18. Approval

| Field | Value |
|---|---|
| **Canonical concept** | `Approval` |
| **Existing implementation** | `ApprovalState` enum exists (`pending`, `approved`, `rejected`, `overridden`). Approval state is embedded as a field on `ComplianceReport`, `AudioBrief`, and `VisualPlan`. No standalone `Approval` entity exists. |
| **Decision** | `create-new` |
| **Reason** | Embedded approval state is sufficient for single-entity approval tracking. A standalone `Approval` record is needed for: cross-entity audit queries ("show me all approvals by reviewer X"), two-approver flows (Phase 17), and a unified review queue. The standalone `Approval` entity captures a decision event and links to any approvable entity by type+id. The embedded `approval_state` on each entity is retained and updated when an `Approval` record is created. |
| **Related files** | `backend/app/db/models/workflow.py` (new ORM), `backend/app/modules/workflow.py` (new Pydantic) |
| **Migration impact** | Yes — creates `approvals` table |
| **API impact** | New `GET /api/v1/review-queue` endpoint (Phase 17). Existing approve/override endpoints continue to work. |
| **Frontend/contract impact** | None until review queue UI is added |

**ORM fields:** `id` (UUID PK), `entity_type` (str — `script`, `compliance_report`, `publishing_package`, `audio_brief`, `visual_plan`), `entity_id` (UUID), `action` (enum: `approve`, `override`, `reject`, `request_changes`), `actor` (str), `reason` (nullable text), `previous_state` (str), `new_state` (str), `created_at`

---

## 19. WorkflowRun

| Field | Value |
|---|---|
| **Canonical concept** | `WorkflowRun` |
| **Existing implementation** | Does not exist. Content pipeline is entirely implicit — there is no entity tracking where an idea is in the lifecycle. |
| **Decision** | `create-new` |
| **Reason** | Explicit workflow tracking is required for the dashboard, the review queue, and the analytics feedback loop. A `WorkflowRun` tracks one idea through its complete lifecycle. |
| **Related files** | `backend/app/db/models/workflow.py`, `backend/app/modules/workflow.py` |
| **Migration impact** | Yes — creates `workflow_runs` and `workflow_steps` tables |
| **API impact** | New `GET /api/v1/ideas/{idea_id}/workflow` and `POST .../advance` endpoints (Phase 18) |
| **Frontend/contract impact** | New workflow dashboard page |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `current_stage` (WorkflowStage enum), `status` (enum: `active`, `paused`, `completed`, `abandoned`), `created_at`, `updated_at`

---

## 20. WorkflowStep

| Field | Value |
|---|---|
| **Canonical concept** | `WorkflowStep` |
| **Existing implementation** | Does not exist |
| **Decision** | `create-new` |
| **Reason** | Each stage transition in a `WorkflowRun` is recorded as an immutable step. Used for audit and performance analysis (how long does each stage take). |
| **Related files** | `backend/app/db/models/workflow.py`, `backend/app/modules/workflow.py` |
| **Migration impact** | Yes — creates `workflow_steps` table |
| **API impact** | Surfaced via `GET /api/v1/ideas/{idea_id}/workflow` |
| **Frontend/contract impact** | None until workflow UI is added |

**ORM fields:** `id` (UUID PK), `run_id` (FK → workflow_runs), `stage` (WorkflowStage enum), `status` (enum: `entered`, `completed`, `blocked`, `skipped`), `actor` (nullable str), `notes` (nullable text), `started_at`, `completed_at` (nullable), `created_at`

---

## 21. LLMCall

| Field | Value |
|---|---|
| **Canonical concept** | `LLMCall` |
| **Existing implementation** | `LLMCall` Pydantic model + `LLMCallLogger` in `modules/llm_logging.py`. Logger holds calls in a process-scoped list. Not persisted. Fields: `provider`, `model`, `operation`, `prompt`, `response`, `prompt_chars`, `response_chars`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `correlation_id`. |
| **Decision** | `extend` (add `id`, `entity_type`, `entity_id`; persist via ORM) |
| **Reason** | The existing Pydantic model has all the right fields but lacks an `id` (for unique DB records), an `entity_type`/`entity_id` link (to know which script/idea the call was for), and a `created_at` timestamp (correlation_id is not a substitute). Adding these fields to the ORM without changing the Pydantic model preserves all existing logging call sites. |
| **Related files** | `backend/app/modules/llm_logging.py` (Pydantic unchanged), `backend/app/db/models/llm.py` (new ORM) |
| **Migration impact** | Yes — creates `llm_calls` table |
| **API impact** | New `GET /api/v1/llm-logs` admin endpoint (Phase 5) |
| **Frontend/contract impact** | None until observability UI is added |

**ORM fields:** `id` (UUID PK), `provider`, `model`, `operation`, `prompt` (text), `response` (text), `prompt_chars` (int), `response_chars` (int), `prompt_tokens` (int), `completion_tokens` (int), `latency_ms` (int), `correlation_id`, `entity_type` (nullable str), `entity_id` (nullable UUID), `created_at`

---

## 22. YouTubeQuotaLedger

| Field | Value |
|---|---|
| **Canonical concept** | `YouTubeQuotaLedger` |
| **Existing implementation** | Does not exist. No YouTube API integration exists. |
| **Decision** | `create-new` |
| **Reason** | YouTube Data API v3 has a daily quota of 10 000 units. Every API operation has a cost. Tracking quota usage per channel per day is required to prevent quota exhaustion and to allow safe retry scheduling. |
| **Related files** | `backend/app/db/models/llm.py` (co-located with LLMCall for observability grouping), `backend/app/modules/analytics.py` |
| **Migration impact** | Yes — creates `youtube_quota_ledger` table |
| **API impact** | Internal — consumed by the YouTube integration layer (Phase 21) |
| **Frontend/contract impact** | None initially |

**ORM fields:** `id` (UUID PK), `channel_id` (FK → channels), `operation` (str — YouTube API method name), `units_used` (int), `quota_date` (date), `created_at`

**Index:** `(channel_id, quota_date)` for daily total queries

---

## 23. AnalyticsReport

| Field | Value |
|---|---|
| **Canonical concept** | `AnalyticsReport` |
| **Existing implementation** | Does not exist. No analytics integration. |
| **Decision** | `create-new` |
| **Reason** | Required for the analytics feedback loop (Phase 19). Records real YouTube performance data against a specific idea and publishing package. Feeds back into Channel Memory. |
| **Related files** | `backend/app/db/models/analytics.py` (new ORM), `backend/app/modules/analytics.py` (new Pydantic) |
| **Migration impact** | Yes — creates `analytics_reports` table |
| **API impact** | New `POST /api/v1/ideas/{idea_id}/performance` endpoint (Phase 19) |
| **Frontend/contract impact** | New performance section in Idea Detail page |

**ORM fields:** `id` (UUID PK), `idea_id` (FK → content_ideas), `publishing_package_id` (FK → publishing_packages, nullable), `youtube_video_id` (nullable str), `upload_date` (nullable date), `impressions` (nullable int), `ctr` (nullable float — click-through rate), `average_view_duration_seconds` (nullable int), `retention_curve` (JSON, nullable), `subscriber_change` (nullable int), `created_at`, `updated_at`

---

## 24. MonetizationPlan

| Field | Value |
|---|---|
| **Canonical concept** | `MonetizationPlan` |
| **Existing implementation** | Does not exist |
| **Decision** | `create-new` |
| **Reason** | Captures the channel's revenue strategy: which streams exist, how content maps to revenue, and diversification goals. Feeds into content planning context (Phase 20). Deliberately named `MonetizationPlan` not `IncomeStrategy` or similar to avoid passive-income framing in the codebase. |
| **Related files** | `backend/app/db/models/analytics.py` (co-located with AnalyticsReport), `backend/app/modules/analytics.py` |
| **Migration impact** | Yes — creates `monetization_plans` table |
| **API impact** | New endpoints (Phase 20) |
| **Frontend/contract impact** | None until monetization strategy UI is added |

**ORM fields:** `id` (UUID PK), `channel_id` (FK → channels), `revenue_streams` (JSON — list of stream descriptions), `content_revenue_notes` (text, nullable), `diversification_goals` (JSON), `affiliate_disclosure_policy` (text, nullable), `created_at`, `updated_at`

---

## Concept collision map — what does NOT exist as a duplicate

| Would-be duplicate | Canonical concept | Resolution |
|---|---|---|
| `Topic` vs `ContentIdea` | `ContentIdea` | No `Topic` model will be created. A topic is a field within `ContentIdea`, not a separate entity. |
| `Brief`, `ResearchBrief`, `VideoBrief` | `ResearchBrief` | Only `ResearchBrief` exists. `AudioBrief` is a separate concept (voice delivery, not research). No `VideoBrief` or `Brief` base class is needed. |
| `ComplianceCheck` vs `ComplianceReport` | `ComplianceReport` | `ComplianceCheckResult` is an intermediate computation type returned by `run_compliance_checks()`. It is not a stored entity. The stored entity is always `ComplianceReport`. |
| `PublishingPackage` vs `PublicationPackage` | `PublishingPackage` | `PublishingPackage` is the canonical name. `PublicationPackage` must not be introduced. |
| `Idea` vs `ContentIdea` | `ContentIdea` | `Idea` in `modules/ideas.py` is an alias; `ContentIdea` is the canonical name. The `Idea` class in `modules/ideas.py` will be renamed to `ContentIdea` with a `Idea = ContentIdea` alias for backwards compatibility. |
| `HookRetentionLab` vs `HookVariant` | `HookVariant` (+ `HookRetentionLab` as aggregate) | `HookVariant` is the item entity. `HookRetentionLab` is the lab session aggregate (Phase 11). Both can exist without collision. |
| `Angle` vs `AngleStatus` | `Angle` (entity) + `AngleStatus` (enum on Angle.status) | `AngleStatus` remains the enum. `Angle` is the entity. No collision. |

---

## Migration strategy

### Phase A — Infrastructure (this phase)
- Add SQLAlchemy 2.0 + Alembic + asyncpg to `pyproject.toml`
- Create `backend/app/db/` package with declarative base and session factory
- Create all ORM model files
- Create initial Alembic migration (`0001_initial_schema.py`)
- No existing code changes — ORM layer sits alongside in-memory repositories

### Phase B — Repository swap (Phase 6 in roadmap)
- Swap in-memory repository internals with SQLAlchemy session calls
- Keep all repository interfaces unchanged (same method signatures)
- Tests continue to pass — test fixtures use SQLite via `aiosqlite`

### Phase C — FK enforcement (Phase 4/9 in roadmap)
- When Idea/Angle API endpoints are added, enforce UUID lookups instead of raw strings
- `idea_id` path params validated against `content_ideas` table
- `angle_id` validated against `angles` table

---

## Breaking changes log

No breaking changes in this phase. All existing Pydantic models, API contracts, and in-memory repositories are unchanged. The ORM layer is additive.

The following will become breaking changes in future phases and must be documented when they occur:

| Future change | Phase | Impact |
|---|---|---|
| `Idea` renamed to `ContentIdea` in `__init__.py` exports | Phase 4 | Import path changes for any code using `from app.modules import Idea` — mitigated by alias |
| `idea_id` path params enforced as UUID FK | Phase 6 | Callers using arbitrary string idea IDs will fail — migration guide required |
| `channel_id="default"` removed | Phase 3 | All endpoints that hardcode `channel_id="default"` will require channel resolution from auth context |
