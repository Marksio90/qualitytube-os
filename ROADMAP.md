# QualityTube OS — Implementation Roadmap

> **Philosophy:** Build the quality infrastructure first. Every phase either adds a human-approved quality gate, improves compliance coverage, or makes the system more measurable. No phase exists to increase output volume for its own sake.

Status legend: `✅ Complete` `🔄 In progress` `⬜ Planned`

---

## Phase 0 — Repo Reconnaissance and Safety Baseline `✅ Complete`

**Goal:** Understand exactly what exists before adding anything new.

- [x] Full read-only codebase audit (domain models, endpoints, AI layer, tests, docs)
- [x] Identify confirmed bugs, duplicate concepts, and do-not-touch files
- [x] Map orphaned models and spec-vs-implementation gaps
- [x] Produce `docs/architecture/repo-reconnaissance.md`

**Key outputs:** Architecture reconnaissance report with 20 gap and risk findings, recommended implementation sequence.

---

## Phase 1 — Product Documentation Pivot `✅ Complete`

**Goal:** Align all documentation with the QualityTube OS product positioning before any code changes.

- [x] Update `README.md` with full product description, compliance philosophy, and quickstart
- [x] Create `ROADMAP.md`
- [x] Create `docs/product/vision.md`
- [x] Create `docs/product/positioning.md`
- [x] Create `docs/product/mvp-scope.md`
- [x] Create `docs/product/non-goals.md`
- [x] Create `docs/compliance/youtube-quality-policy.md`

**Key outputs:** Documentation suite that accurately represents the product and its boundaries.

---

## Phase 2 — Domain Model Unification `⬜ Planned`

**Goal:** Fix the three Phase 0 structural bugs and eliminate code duplication before building new features.

- [ ] Fix `generate_thumbnail_briefs` AttributeError (missing `titles` field on request model)
- [ ] Consolidate dual script lookup: add `get_by_id` to `ScriptRepository`, remove `script_by_id` dict from `main.py`
- [ ] Add `get_latest` and `get_by_id` to `AudioBriefRepository` to eliminate private `_by_script` access
- [ ] Move `PublishingPackageService` from `main.py` into `modules/publishing_package_service.py`
- [ ] Split `main.py` into FastAPI `APIRouter` modules per domain area
- [ ] Wire `AngleStatus` enum into gate validation; remove raw string comparison
- [ ] Remove orphaned `ScriptDraft` class from `scripts.py`
- [ ] Document or remove `ResearchBrief` model

**Key outputs:** Clean, testable module boundaries. No duplicate state. No confirmed crash bug.

---

## Phase 3 — Channel Workspace and Channel Memory `⬜ Planned`

**Goal:** Replace the hardcoded `channel_id="default"` scaffold with a real channel management system.

- [ ] Add `POST /api/v1/channels` — create channel profile
- [ ] Add `GET /api/v1/channels` — list channels for authenticated user
- [ ] Add `GET /api/v1/channels/{channel_id}` — fetch channel profile
- [ ] Add `PATCH /api/v1/channels/{channel_id}` — update tone notes, banned claims, content pillars
- [ ] Extend `ChannelMemory` with: language, upload schedule target, content pillars, audience description, brand voice notes
- [ ] Remove `channel_id="default"` hardcoding from all endpoints; resolve from request context
- [ ] Add channel memory to the Channel Workspace UI

**Key outputs:** Multi-channel support. Configurable brand voice per channel.

---

## Phase 4 — Content Idea Board `⬜ Planned`

**Goal:** Give ideas and angles a full lifecycle with API endpoints, not just a domain model.

- [ ] Add `POST /api/v1/ideas` — create idea with title, audience, premise
- [ ] Add `GET /api/v1/ideas` — list ideas (filterable by state)
- [ ] Add `GET /api/v1/ideas/{idea_id}` — fetch idea
- [ ] Add `PATCH /api/v1/ideas/{idea_id}` — update idea fields
- [ ] Add angle lifecycle: `POST /api/v1/ideas/{idea_id}/angles` (create angle)
- [ ] Add `POST /api/v1/angles/{angle_id}/approve` and `reject` with reason
- [ ] Wire `AngleStatus` enum to persisted angle records; remove string-passing from script generation requests
- [ ] Add Content Idea Board page to frontend

**Key outputs:** Ideas have a trackable lifecycle. Angles are persisted and approved explicitly before script generation begins.

---

## Phase 5 — AI Provider Layer Hardening `⬜ Planned`

**Goal:** Replace `MockProvider` with a production-ready, observable AI layer.

- [ ] Add Anthropic SDK (or OpenAI SDK) to `pyproject.toml`
- [ ] Implement `AnthropicProvider` (or `OpenAIProvider`) satisfying the `AIProvider` protocol
- [ ] Add prompt caching for high-frequency operations (compliance review, script scoring)
- [ ] Extend prompt templates with structured schema enforcement and output validation
- [ ] Persist `LLMCall` log records to database (Phase 6 dependency)
- [ ] Add `GET /api/v1/llm-logs` (admin-only) for call observability and cost tracking
- [ ] Add environment variable configuration for provider, model, and API key
- [ ] Retain `MockProvider` for test isolation

**Key outputs:** Real AI generation. Observable, cost-trackable LLM calls. Provider-swappable architecture.

---

## Phase 6 — Database Persistence `⬜ Planned`

**Goal:** Replace all in-memory repositories with a real database so state survives process restarts.

- [ ] Add SQLAlchemy (async) + Alembic to `pyproject.toml`
- [ ] Define ORM models for all domain entities: `Channel`, `Idea`, `Angle`, `Script`, `ScriptVersion`, `ComplianceReport`, `PublishingPackage`, `PublishingPackageRevision`, `VisualPlan`, `AudioBrief`, `TitleVariant`, `ThumbnailConcept`, `HookVariant`, `LLMCallLog`
- [ ] Write initial Alembic migration
- [ ] Swap repository internals to use async database sessions; keep repository interfaces unchanged
- [ ] Add `DATABASE_URL` to environment variable configuration
- [ ] Update test fixtures to use isolated test databases
- [ ] Add `.env.example`

**Key outputs:** Persistent state across restarts. Production-ready data layer. Migration-controlled schema.

---

## Phase 7 — Niche Intelligence `⬜ Planned`

**Goal:** Give channels a structured understanding of their niche, audience, and competitive position.

- [ ] Add `NicheProfile` model: niche name, primary audience segments, channel differentiators, content gaps, competitive alternatives
- [ ] Add `POST /api/v1/channels/{channel_id}/niche-profile` — create or update niche profile
- [ ] Add AI-assisted niche gap analysis: given channel history and niche, surface underserved topic areas
- [ ] Wire niche profile into script generation context (alongside channel memory)
- [ ] Add Niche Intelligence section to Channel Workspace UI

**Key outputs:** Channels have a structured niche model. AI generation is niche-aware, not generic.

---

## Phase 8 — Topic Research Engine `⬜ Planned`

**Goal:** Surface topic ideas grounded in audience need, not trend-chasing or keyword volume.

- [ ] Add `TopicResearch` model: topic, search intent, audience questions, evidence sources, originality notes
- [ ] Add `POST /api/v1/ideas/{idea_id}/topic-research` — generate structured research brief
- [ ] AI-assisted research summary: given topic + niche profile, surface what is already well-covered and what is underexplored
- [ ] Wire research brief into script generation context to replace the current stub `ResearchBrief`
- [ ] Validate research brief against originality signals before idea progresses to angle stage

**Key outputs:** Ideas are backed by structured research. Angle generation is informed by evidence, not keyword stuffing.

---

## Phase 9 — Originality and Angle Engine `⬜ Planned`

**Goal:** Ensure every content angle makes a specific, defensible, original argument before script work begins.

- [ ] Extend `Angle` model with: argument type, originality claim, counter-narrative, audience benefit, evidence requirement
- [ ] Add AI-assisted angle generation: given idea + research brief + niche profile, propose multiple distinct angles
- [ ] Add angle scoring: originality, audience value, differentiation from generic takes
- [ ] Require at least one originality evidence item before angle can be approved
- [ ] Wire approved angle into all downstream script generation as required context
- [ ] Add Angle Board to Content Idea Board UI

**Key outputs:** No script begins without a specific, scored, human-approved angle. Generic angles are blocked at the gate.

---

## Phase 10 — Script Studio `⬜ Planned` (hardening)

**Goal:** The core script generation and approval workflow is largely implemented. This phase completes and hardens it.

- [ ] Connect script generation to persisted `Idea` and `Angle` records (remove string-passing)
- [ ] Add `ready_to_publish` state as an explicit endpoint, not a PATCH state value
- [ ] Add per-section word count and reading time estimates
- [ ] Add configurable banned phrase list per channel (not just per-request)
- [ ] Add script export (plain text, structured JSON)
- [ ] Improve version history UI with diff highlighting
- [ ] Add script templates for common formats (documentary, tutorial, opinion, listicle)

**Key outputs:** Script Studio is fully connected to the idea pipeline and channel profile.

---

## Phase 11 — Hook and Retention Lab `⬜ Planned` (spec-complete)

**Goal:** Complete the Hook Retention Lab to the full spec in `docs/product/hook-retention-lab.md`.

Current state: flat hook generation and scoring exists. The lab entity, reviewer decisions, and history endpoint are missing.

- [ ] Add `HookRetentionLab` model: `id`, `script_id`, `status`, `prompt_config`, `created_by`, timestamps
- [ ] Add `HookRetentionVariant` model: `id`, `lab_id`, `hook_text`, `retention_hypothesis`, `expected_dropoff_risk`, `predicted_retention_score`, `signals` (curiosity_gap, clarity, novelty, tempo), `rank_order`
- [ ] Add `HookRetentionReview` model: `id`, `lab_id`, `winning_variant_id`, `decision` (accept/reject/regenerate), `confidence`, `notes`, `reviewer`, `applied_script_revision`
- [ ] Add `POST /api/v1/scripts/{script_id}/hook-retention/generate`
- [ ] Add `POST /api/v1/scripts/{script_id}/hook-retention/reviews`
- [ ] Add `GET /api/v1/scripts/{script_id}/hook-retention/labs`
- [ ] Maintain backward compatibility with existing flat `/hooks/generate` endpoint
- [ ] Add Hook Retention Lab UI panel to Script Studio

**Key outputs:** Full lab-based hook workflow with reviewer decisions and audit history.

---

## Phase 12 — Compliance and YouTube Policy Guard `⬜ Planned` (hardening)

**Goal:** Harden the compliance system to match the full spec in `docs/compliance/compliance-guard.md`.

Current state: deterministic checks + AI review + approve/override exist. HOLD gate and Policy Classifier are missing.

- [ ] Add `HOLD` compliance state for content requiring specialist human review before approve or block decision
- [ ] Add Policy Classifier: determine which policy packs apply based on content type, topic sensitivity, and destination
- [ ] Add per-check evidence recording (not just an aggregate recommendation)
- [ ] Add required evidence upload path for human contribution documentation
- [ ] Add compliance report PDF export for agency and legal review
- [ ] Add override expiration: time-bound overrides with compensating control notes
- [ ] Wire compliance report to publishing package validation (currently partially wired)

**Key outputs:** Compliance system matches documented spec. HOLD gate prevents borderline content from slipping through.

---

## Phase 13 — Publishing Package `⬜ Planned` (hardening)

**Goal:** Complete the publishing package workflow and close the known idempotency gap.

- [ ] Fix `generate_thumbnail_briefs` bug (carried from Phase 2)
- [ ] Add `POST /api/v1/ideas/{idea_id}/publishing-package/regenerate` for re-generation without creating a new package
- [ ] Add publishing package template system: starter metadata templates per content format
- [ ] Add tag suggestion service: AI-generated tags with policy risk scoring
- [ ] Add first-comment template with CTA and disclosure notes
- [ ] Improve markdown export formatting

**Key outputs:** Publishing package is idempotent, complete, and ready for structured upload.

---

## Phase 14 — Title and Thumbnail Lab `⬜ Planned` (hardening)

**Goal:** Complete title and thumbnail generation with full title-to-script promise alignment checks.

- [ ] Fix `payload.titles` bug in thumbnail generation endpoint (carried from Phase 2)
- [ ] Add `GET /api/v1/ideas/{idea_id}/titles/selected` — fetch only the selected title variant
- [ ] Add title A/B experiment tracking: record which title variant was uploaded and its resulting CTR
- [ ] Add thumbnail concept rejection with notes
- [ ] Add thumbnail brief export for design handoff (structured JSON for Figma or Canva workflows)
- [ ] Wire selected title back to publishing package automatically (currently requires package to exist first)

**Key outputs:** Title and thumbnail pipeline is complete, auditable, and connected to analytics tracking.

---

## Phase 15 — Visual Plan Builder `⬜ Planned` (hardening)

**Goal:** Complete per-scene approval workflow as specified in `docs/product/visual-plan-builder.md`.

Current state: plan-level approval only. Per-scene approve/revise/reject is not implemented.

- [ ] Add `scene_approval_state` to `VisualScene`: `draft`, `approved`, `revision_requested`, `rejected`
- [ ] Add `POST /api/v1/visual-plans/{plan_id}/scenes/{scene_number}/approve`
- [ ] Add `POST /api/v1/visual-plans/{plan_id}/scenes/{scene_number}/request-revision` with notes
- [ ] Block plan-level approval until all scenes are individually approved
- [ ] Add filler-risk threshold gate: plans with too many high-risk scenes cannot be approved without override
- [ ] Add visual plan export for production handoff (JSON schema for downstream asset sourcing tools)

**Key outputs:** Full per-scene approval workflow. Plans cannot be approved with unreviewed high-risk scenes.

---

## Phase 16 — Voice and Audio Studio `⬜ Planned` (hardening)

**Goal:** Complete the audio brief lifecycle and add synthetic voice disclosure enforcement.

Current state: audio brief generation, approval, and export are implemented. Integration with publishing package disclosure is partial.

- [ ] Add multiple audio brief versions per script (currently only one approved brief is meaningful)
- [ ] Add voice sample reference field for narrator briefs
- [ ] Wire `synthetic_voice_used=true` disclosure flag automatically to publishing package `disclosure_notes`
- [ ] Add `POST /api/v1/audio-briefs/{audio_brief_id}/revise` for post-approval correction with audit trail
- [ ] Add audio brief template library per `VoiceStyle`

**Key outputs:** Synthetic voice disclosure is enforced end-to-end from audio brief to publishing package.

---

## Phase 17 — Human Approval Workflow `⬜ Planned`

**Goal:** Build a structured reviewer interface and notification system so approval decisions are tracked and attributed.

- [ ] Add `Reviewer` identity model: `id`, `name`, `role` (writer, reviewer, publisher, admin)
- [ ] Add authentication (FastAPI-Users or JWT): all approve/override endpoints require reviewer identity
- [ ] Add `approval_requested_at` and `approved_by` fields to all approvable entities
- [ ] Add reviewer assignment: an idea/script can be assigned to a named reviewer
- [ ] Add `GET /api/v1/review-queue` — list all items awaiting approval for the authenticated reviewer
- [ ] Add override approval policy: overrides above risk level `high` require a second approver
- [ ] Add approval timeline view to frontend

**Key outputs:** All approvals and overrides are attributed to verified identities. Review queue is navigable.

---

## Phase 18 — Workflow Engine `⬜ Planned`

**Goal:** Replace the implicit manual content pipeline with an explicit, trackable workflow state machine.

- [ ] Add `ContentWorkflow` model: tracks the current stage of each idea across the full pipeline (research → angle → script → compliance → publishing)
- [ ] Add `POST /api/v1/ideas/{idea_id}/workflow/advance` — explicit stage progression with gate checks
- [ ] Add `GET /api/v1/ideas/{idea_id}/workflow` — current stage, blockers, next actions
- [ ] Add Celery task queue for async AI operations (visual plan, compliance review, publishing package generation)
- [ ] Add `GET /api/v1/tasks/{task_id}` — poll async task status
- [ ] Add workflow dashboard to frontend showing all ideas and their current pipeline stage

**Key outputs:** Content pipeline is visible, navigable, and asynchronous for long-running AI operations.

---

## Phase 19 — Analytics Feedback Loop `⬜ Planned`

**Goal:** Close the content improvement loop by feeding real performance data back into the channel's knowledge base.

- [ ] Add `ContentPerformanceRecord` model: `idea_id`, `youtube_video_id`, upload date, impressions, CTR, average view duration, retention curve (JSON), subscriber change
- [ ] Add `POST /api/v1/ideas/{idea_id}/performance` — manually record performance data after upload
- [ ] Add performance summary view to Idea Detail page
- [ ] Add `ChannelInsight` model: AI-generated summary of what content attributes correlate with higher retention across the channel's history
- [ ] Add `POST /api/v1/channels/{channel_id}/insights/generate` — AI insight generation from performance history
- [ ] Wire channel insights into Channel Memory for future script and angle generation context

**Key outputs:** Real performance data informs future content decisions. Feedback loop is explicit and human-reviewed.

---

## Phase 20 — Monetization Strategy Engine `⬜ Planned`

**Goal:** Help channels understand the relationship between content quality, audience trust, and sustainable revenue — without making performance guarantees.

- [ ] Add `MonetizationStrategy` model: current revenue streams, content-to-revenue mapping notes, diversification goals
- [ ] Add AI-assisted monetization review: given content type and performance history, surface which formats have historically supported audience trust and revenue alignment
- [ ] Add affiliate and sponsorship disclosure tracking: flag when content mentions brand relationships and enforce disclosure in publishing package
- [ ] Wire monetization strategy notes into channel memory for content planning context

**Key outputs:** Revenue context is explicit and tied to content quality — not to volume or automation shortcuts.

---

## Phase 21 — YouTube Integration Hardening `⬜ Planned`

**Goal:** Add structured, human-approved YouTube API integration for channel data and upload preparation.

- [ ] Add OAuth 2.0 flow for YouTube account connection
- [ ] Add `GET /api/v1/channels/{channel_id}/youtube/channel-data` — pull channel metadata from YouTube Data API v3
- [ ] Add `POST /api/v1/publishing-packages/{package_id}/prepare-upload` — validate all fields against YouTube API limits before upload
- [ ] Add human-confirmed upload step: `POST /api/v1/publishing-packages/{package_id}/upload` with explicit confirmation flag
- [ ] Add YouTube video ID recording on successful upload, linked to `ContentPerformanceRecord`
- [ ] Add YouTube thumbnail upload via API after human thumbnail approval

**Key outputs:** YouTube integration is structured, gated by human confirmation, and audit-trailed.

---

## Phase 22 — Frontend Polish `⬜ Planned`

**Goal:** Bring the frontend to a production-ready state for real creator workflows.

- [ ] Replace placeholder `HomePage` with a real dashboard (channel overview, recent ideas, pending approvals)
- [ ] Add TypeScript migration for type safety across all components
- [ ] Add shared API client module (remove duplicated `api()` inline helpers)
- [ ] Add loading skeletons and error boundary components
- [ ] Add toast notification system for approval and gate events
- [ ] Add keyboard navigation for approval actions
- [ ] Add mobile-responsive layout for review workflows
- [ ] Ensure consistent compliance status indicators across all pages

**Key outputs:** Frontend is navigable, type-safe, and production-ready for creator teams.

---

## Phase 23 — Worker Reliability `⬜ Planned`

**Goal:** Make async AI operations reliable, observable, and recoverable.

- [ ] Add Celery worker with Redis or RabbitMQ broker
- [ ] Add task retry logic with exponential backoff for AI provider failures
- [ ] Add dead-letter queue for failed tasks with manual retry UI
- [ ] Add task timeout enforcement: AI calls that exceed a configured threshold are cancelled and flagged
- [ ] Add worker health endpoint for monitoring
- [ ] Add LLM call cost tracking: estimate token costs per operation and aggregate by channel/month

**Key outputs:** No AI operation blocks the HTTP thread. Failed operations are retried or surfaced for manual action.

---

## Phase 24 — Security Hardening `⬜ Planned`

**Goal:** Ensure the system is safe for real creator and agency use.

- [ ] Add JWT authentication with role-based access control (writer, reviewer, publisher, admin)
- [ ] Add rate limiting on AI generation endpoints
- [ ] Add input sanitization audit: all user-supplied strings validated and length-bounded
- [ ] Add output validation audit: all AI-generated content validated against strict schemas before persistence
- [ ] Add audit log API: `GET /api/v1/audit-log` for all approval, override, and upload events
- [ ] Add environment variable secret management documentation
- [ ] Remove any hardcoded values (channel_id="default", banned_phrases in code)

**Key outputs:** System is safe for multi-user, multi-channel production use.

---

## Phase 25 — Tests, Contracts, and CI `⬜ Planned`

**Goal:** Ensure every module is tested, every contract is validated, and CI prevents regressions.

- [ ] Add GitHub Actions CI: run pytest, ruff, and vitest on every pull request
- [ ] Add contract tests for all AI service payloads (validate schema compliance of MockProvider responses)
- [ ] Add integration tests for full idea → script → compliance → publishing package flow
- [ ] Add test coverage reporting (target: ≥ 80% backend coverage)
- [ ] Add property-based tests for compliance gate logic (hypothesis or similar)
- [ ] Add frontend test coverage for IdeaDetailPage and ScriptStudioPage approval flows
- [ ] Add `Dockerfile` and `docker-compose.yml` for reproducible local environments
- [ ] Add `.env.example` with all required variable documentation

**Key outputs:** CI catches regressions. Contract tests prevent provider schema drift. Docker makes onboarding reproducible.

---

## Phase 26 — Final MVP Demo Flow `⬜ Planned`

**Goal:** Validate the full end-to-end creator workflow in a single session with a real AI provider.

- [ ] Run full flow: channel setup → idea creation → topic research → angle approval → script generation → hook lab → compliance review → publishing package → export
- [ ] Verify all approval gates function as documented
- [ ] Verify all compliance checks produce correct results on known test content
- [ ] Verify audit trail is complete and reviewable
- [ ] Verify publishing package export is upload-ready
- [ ] Record demo video for documentation
- [ ] Update `docs/product/mvp-scope.md` with confirmed feature status

**Key outputs:** Validated, documented, demo-ready MVP.

---

## What this roadmap deliberately excludes

- Automatic mass video production pipelines
- Blind scheduling or auto-publishing
- Passive income claims or monetization guarantees
- Content farming or volume-over-quality workflows
- Social media cross-posting automation
- SEO keyword stuffing or clickbait optimisation
- Any feature designed to circumvent YouTube's content policies

See [`docs/product/non-goals.md`](docs/product/non-goals.md) for the full anti-goals definition.
