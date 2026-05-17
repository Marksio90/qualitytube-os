# QualityTube OS — Repository Reconnaissance Report

> **Status:** Read-only audit. No source files were modified.
> **Scope:** Full repository scan — backend, frontend, docs, tests, infrastructure.
> **Date:** 2026-05-17

---

## 1. Current Repository Structure

```
qualitytube-os/
├── backend/
│   ├── app/
│   │   ├── __init__.py                       (empty)
│   │   ├── main.py                           (1 256 lines — FastAPI app + all endpoints + inline request models)
│   │   └── modules/
│   │       ├── __init__.py                   (130 lines — centralised re-exports + __all__)
│   │       ├── ai_provider.py                (34 lines  — AIProvider Protocol + MockProvider)
│   │       ├── angle_approval.py             (7 lines   — AngleStatus enum; NOT wired to API)
│   │       ├── audio_brief.py                (126 lines — AudioBrief domain model + repo)
│   │       ├── audio_brief_ai.py             (94 lines  — AudioBriefAIService)
│   │       ├── channel_memory.py             (21 lines  — ChannelMemory model + repo)
│   │       ├── compliance.py                 (149 lines — ComplianceReport domain model)
│   │       ├── compliance_checks.py          (136 lines — deterministic checks + gate functions)
│   │       ├── ideas.py                      (8 lines   — Idea model; NOT wired to API)
│   │       ├── llm_logging.py                (25 lines  — LLMCall + LLMCallLogger)
│   │       ├── publishing_package.py         (170 lines — PublishingPackage model + repo)
│   │       ├── publishing_package_export.py  (65 lines  — JSON/markdown export service)
│   │       ├── publishing_package_validation.py (161 lines — deterministic validation service)
│   │       ├── research_brief.py             (7 lines   — ResearchBrief model; NOT wired to API)
│   │       ├── script_ai.py                  (315 lines — ScriptAIService: outline/draft/score/improve/hooks/retention/visual/publishing)
│   │       ├── scripts.py                    (315 lines — Script domain model + ScriptRepository)
│   │       ├── title_thumbnail_ai.py         (208 lines — TitleThumbnailAIService)
│   │       ├── title_thumbnail_lab.py        (153 lines — TitleVariant + ThumbnailConcept models + repo)
│   │       └── visual_plan.py                (138 lines — VisualPlan domain model + repo)
│   └── tests/
│       ├── test_audio_brief_ai_service.py
│       ├── test_compliance_checks.py
│       ├── test_compliance_extended.py
│       ├── test_health.py
│       ├── test_modules_import.py
│       ├── test_publishing_api.py
│       ├── test_script_ai_service.py
│       ├── test_scripts_api.py
│       ├── test_scripts_domain.py
│       ├── test_title_thumbnail_api.py
│       ├── test_visual_plan_ai_service.py
│       ├── test_visual_plan_api.py
│       └── test_visual_plan_models.py
├── frontend/
│   ├── src/
│   │   ├── main.jsx                          (React 18 + BrowserRouter setup)
│   │   ├── routes/
│   │   │   └── AppRoutes.jsx                 (React Router 6 route table)
│   │   ├── pages/
│   │   │   ├── HomePage.jsx                  (placeholder: `<main>QualityTube OS</main>`)
│   │   │   ├── IdeaDetailPage.jsx            (compliance + title lab + thumbnail lab + publishing tabs)
│   │   │   ├── IdeaDetailPage.test.jsx
│   │   │   ├── ScriptStudioPage.jsx          (script editor + hooks + retention + visual plan tabs)
│   │   │   └── ScriptStudioPage.test.jsx
│   │   └── components/
│   │       └── VisualPlanTab.jsx             (reusable visual plan editor component)
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
├── docs/
│   ├── architecture.md                       (2 lines — placeholder only)
│   ├── script-studio.md                      (3 lines — placeholder only; duplicates product/script-studio.md name)
│   ├── compliance/
│   │   ├── compliance-guard.md               (policy spec — richer than current implementation)
│   │   ├── reused-repetitive-content.md
│   │   └── synthetic-content-disclosure.md
│   ├── product/
│   │   ├── hook-retention-lab.md             (full spec — NOT yet implemented as described)
│   │   ├── publishing-package.md
│   │   ├── script-studio.md                  (161 lines — authoritative product flow doc)
│   │   ├── title-thumbnail-lab.md
│   │   └── visual-plan-builder.md
│   └── prompts/
│       ├── audio-brief-generation.md
│       ├── compliance-review.md
│       ├── hook-generation.md
│       ├── hook-scoring.md
│       ├── publishing-package-generation.md
│       ├── retention-review.md
│       ├── script-draft-generation.md
│       ├── script-improvement.md
│       ├── script-outline-generation.md
│       ├── script-scoring.md
│       ├── thumbnail-brief-generation.md
│       ├── title-generation.md
│       ├── title-scoring.md
│       └── visual-plan-generation.md
├── .gitignore
├── LICENSE
├── README.md                                 (12 lines — minimal quick-start only)
└── pyproject.toml                            (Python project config + deps + pytest + ruff)
```

**No files exist for:** Dockerfile, docker-compose.yml, .env.example, Makefile, GitHub Actions, database migrations, or any CI/CD configuration.

---

## 2. Current Product Narrative

QualityTube OS is described in `README.md` as a "monorepo scaffold." The actual implemented product is an **AI-assisted YouTube content production workspace** that covers:

1. **Script Studio** — generate, score, improve, version, and approve video scripts.
2. **Hook & Retention Lab** — generate and evaluate alternative hook openings against retention signals.
3. **Visual Plan Builder** — AI-proposed scene-by-scene visual strategy for approved scripts.
4. **Audio Brief** — voice delivery specification for narrators or voice synthesis.
5. **Title & Thumbnail Lab** — AI-generated title candidates and thumbnail visual briefs.
6. **Compliance Guard** — dual-pass (deterministic + AI) content policy review before publishing.
7. **Publishing Package** — structured YouTube upload metadata (title, description, tags, chapters, checklist) with validation, versioning, and export.

The philosophy encoded in the approval gates, compliance checks, and override audit trail is: **human-approved, policy-safe, measurably-scored content — not volume automation**.

No YouTube API integration, user authentication, or database persistence is implemented yet.

---

## 3. Current Backend Architecture

**Framework:** FastAPI 0.115+, Python 3.11+, Pydantic v2.9+, Uvicorn.

**Entry point:** `backend/app/main.py`

**Pattern:** Monolith. All 50+ endpoints, all inline request/response models, all service orchestration, and all repository wiring live in a single 1 256-line file. There is no router splitting, no dependency injection framework, and no layered application structure.

**Persistence:** 100% in-memory Python dicts. All state is lost on process restart. No database driver, ORM, or migration toolchain is installed or referenced.

**State management in `main.py`:**

```python
repo = ScriptRepository()                      # canonical scripts + versions + hooks + retention
script_by_id: dict[UUID, Script] = {}          # SECONDARY index — must be kept in sync with repo manually
channel_memory_repo = ChannelMemoryRepository()
compliance_reports_by_idea: dict[str, list[ComplianceReport]] = {}
compliance_reports_by_id: dict[UUID, ComplianceReport] = {}
publishing_repo = PublishingPackageRepository()
title_thumbnail_repo = TitleThumbnailLabRepository()
visual_plan_repo = VisualPlanRepository()
audio_brief_repo = AudioBriefRepository()
```

> **Risk:** `script_by_id` is a second lookup dict manually maintained alongside `ScriptRepository._canonical_by_idea`. They must be updated together on every write. Desync = silent 404s.

**Service instances (module-level singletons):**

```python
script_ai = ScriptAIService()           # uses MockProvider by default
title_thumbnail_ai = TitleThumbnailAIService()
audio_brief_ai = AudioBriefAIService()
publishing_service = PublishingPackageService(publishing_repo)
publishing_export_service = PublishingPackageExportService()
```

**Seeded data:**

```python
channel_memory_repo.upsert(ChannelMemory(channel_id="default", ...))
```

All endpoints that require channel memory are hardcoded to `channel_id="default"`.

---

## 4. Current Frontend Architecture

**Framework:** React 18.3 + React Router 6.28 + Vite 5.4

**Entry point:** `frontend/src/main.jsx` → `BrowserRouter` → `AppRoutes`

**Route table** (`frontend/src/routes/AppRoutes.jsx`):

| Path | Component | Purpose |
|---|---|---|
| `/` | `HomePage` | Placeholder (`<main>QualityTube OS</main>`) |
| `/script-studio` | `ScriptStudioPage` | Script editor workspace |
| `/ideas/:ideaId` | `IdeaDetailPage` | Compliance + title/thumbnail + publishing |
| `*` | `Navigate to /` | Catch-all redirect |

**ScriptStudioPage tabs:** editor, hooks, retention, visual-plan

**IdeaDetailPage tabs:** compliance, title-lab, thumbnail-lab, publishing

**API helper:** A bare `fetch`-based `api()` function (inlined, not extracted to a shared file) that auto-parses JSON and propagates error payloads.

**State management:** React `useState` with isolated loading/error/success atoms per feature section. No global state manager (no Redux, Zustand, React Query, or context providers).

**Testing:** Vitest 2.1 + `@testing-library/react`. Two test files exist; coverage is unknown (tests not run during this audit).

**No design system, no component library, no TypeScript.** All frontend is plain JSX.

---

## 5. Current Worker / Celery Architecture

**Does not exist.** There are no Celery tasks, task queues, background workers, job schedulers, or async processing of any kind. All operations are synchronous HTTP request-response.

---

## 6. Current AI / LLM Provider Architecture

**Protocol definition** (`backend/app/modules/ai_provider.py`):

```python
class AIProvider(Protocol):
    model: str
    def generate(self, prompt: str) -> str: ...
```

Single method: `generate(prompt: str) -> str`. No streaming, no tool use, no multi-turn.

**MockProvider** (same file): Pattern-matched on lowercased prompt substring. Returns hardcoded JSON strings for each operation type. Covers: hook variants, hook scoring, retention review, outlines, drafts, quality scoring, title generation, title scoring, thumbnail briefs. Falls through to an improvement-style response by default.

**Real provider:** Does not exist. No OpenAI, Anthropic, Google, or other SDK is installed. `pyproject.toml` lists only `fastapi`, `uvicorn`, `pydantic`.

**Prompt templates** (14 files in `docs/prompts/`): Markdown files loaded at runtime by `ScriptAIService` and `AudioBriefAIService` using `Path.read_text()` for compliance-review, publishing-package-generation, visual-plan-generation, and audio-brief-generation operations. Other operations construct prompts inline as f-strings.

**LLM logging:** `LLMCallLogger` maintains an in-memory `list[LLMCall]` per service instance. Each call records: provider, model, operation, prompt, response, char/token counts, latency_ms, correlation_id. Not persisted, not exported, not observable externally.

**Plugging in a real provider:** Instantiate any class satisfying `AIProvider` protocol and pass it to `ScriptAIService(provider=...)`, `AudioBriefAIService(provider=...)`, `TitleThumbnailAIService(provider=...)`.

---

## 7. Current YouTube Integration Architecture

**Does not exist.** There is no YouTube Data API client, no OAuth 2.0 flow, no channel management, no video upload, no playlist management, and no analytics pull. The Publishing Package generates structured metadata for *manual* YouTube upload. The export endpoint produces JSON or markdown for the user to copy-paste.

---

## 8. Current Database / Domain Model Map

All persistence is in-memory. The domain model boundaries are:

### `Script` (canonical 1-per-idea)
- **File:** `backend/app/modules/scripts.py`
- **Fields:** `id` (UUID), `idea_id` (str), `angle_id` (str), `state` (ScriptState), `sections` (list[ScriptSection]), `quality_report` (ScriptQualityReport | None)
- **Invariants:** must include `hook`/`body`/`cta` sections; total chars ≥ 120; 1 canonical script per idea_id
- **Versioned by:** `ScriptVersion` (append-only, stores full script snapshot)
- **Associated:** `HookVariant` (list per script_id), `RetentionReview` (list per script_id)
- **Repo:** `ScriptRepository` in `scripts.py` + duplicate `script_by_id` dict in `main.py`

### `ComplianceReport`
- **File:** `backend/app/modules/compliance.py`
- **Fields:** `id`, `idea_id`, 8 risk dimensions (all `RiskLevel`), `overall_risk`, `recommendation`, `required_fixes`, `approval_state`, `override_*` audit fields, `override_audit_log`
- **Repo:** two dicts directly in `main.py` (`compliance_reports_by_idea`, `compliance_reports_by_id`). No dedicated repository class.

### `PublishingPackage` (canonical 1-per-idea)
- **File:** `backend/app/modules/publishing_package.py`
- **Fields:** `id`, `idea_id`, `title` (≤95 chars), `description`, `tags`, `chapters` (timestamp format validated), `pinned_comment`, `thumbnail_brief`, `disclosure_notes`, `source_notes`, `upload_checklist`, `status`, `latest_compliance`
- **Versioned by:** `PublishingPackageRevision` (append-only, stores full snapshot)
- **Repo:** `PublishingPackageRepository` in `publishing_package.py`

### `VisualPlan` (canonical 1-per-script)
- **File:** `backend/app/modules/visual_plan.py`
- **Fields:** `id`, `script_id`, `scenes` (list[VisualScene]), `approval_state`, timestamps
- **VisualScene:** `scene_number` (strictly increasing), `narration_excerpt`, `visual_type` (VisualType enum), `visual_description`, `purpose`, `asset_notes`, `risk_notes`, `filler_risk_score` (0.0–1.0)
- **Repo:** `VisualPlanRepository` in `visual_plan.py`

### `AudioBrief`
- **File:** `backend/app/modules/audio_brief.py`
- **Fields:** `id`, `script_id`, `voice_style` (VoiceStyle enum), `pace_wpm` (90–220), `emotional_tone`, `pause_notes`, `pronunciation_notes`, `emphasis_notes`, `synthetic_voice_used`, `disclosure_required`, `disclosure_notes`, `export_text`, `approval_state`
- **Invariant:** `synthetic_voice_used=True` → `disclosure_required=True` → `disclosure_notes` required
- **Repo:** `AudioBriefRepository` in `audio_brief.py` (multiple briefs per script allowed)

### `TitleVariant`
- **File:** `backend/app/modules/title_thumbnail_lab.py`
- **Fields:** `id`, `idea_id`, `title_text` (≤200 chars), `selected`, 5 score dimensions (0–10), `rationale`, `warnings`
- **Repo:** `TitleThumbnailLabRepository` in `title_thumbnail_lab.py`

### `ThumbnailConcept`
- **File:** `backend/app/modules/title_thumbnail_lab.py`
- **Fields:** `id`, `idea_id`, `selected`, `main_object`, `emotion`, `composition`, `text_overlay`, `visual_contrast`, `mobile_readability_notes`, `avoid`, `score`
- **Repo:** `TitleThumbnailLabRepository` (same repo as TitleVariant)

### `ChannelMemory`
- **File:** `backend/app/modules/channel_memory.py`
- **Fields:** `channel_id`, `tone_notes` (list[str]), `banned_claims` (list[str])
- **Repo:** `ChannelMemoryRepository` — upsert-only by channel_id

### Orphaned domain models (defined, not wired to any API)

| Model | File | Status |
|---|---|---|
| `Idea` | `modules/ideas.py` | Defined, exported, never used in `main.py` |
| `AngleStatus` | `modules/angle_approval.py` | Enum defined; angle status validated as raw string in API |
| `ResearchBrief` | `modules/research_brief.py` | Defined, exported, never instantiated |
| `ScriptDraft` | `modules/scripts.py` (line 310) | Defined at bottom of file; not used anywhere |

---

## 9. Current API Route Map

All routes registered on the single FastAPI `app` instance in `backend/app/main.py`.

### Infrastructure
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check → `{"status": "ok"}` |

### Script Studio
| Method | Path | Gate | Notes |
|---|---|---|---|
| POST | `/api/v1/ideas/{idea_id}/scripts/generate-outline` | angle_status=approved (bypassable) | Returns Script + StructuredOutline |
| POST | `/api/v1/ideas/{idea_id}/scripts/generate-draft` | angle_status=approved (bypassable) | Calls outline then draft AI ops |
| GET | `/api/v1/ideas/{idea_id}/scripts` | — | Returns 0 or 1 canonical script |
| GET | `/api/v1/scripts/{script_id}` | — | Fetch by UUID |
| PATCH | `/api/v1/scripts/{script_id}` | — | Update sections/state, creates revision |
| POST | `/api/v1/scripts/{script_id}/score` | script exists | AI scoring → quality_report |
| POST | `/api/v1/scripts/{script_id}/improve` | script exists | AI rewrite → new revision |
| POST | `/api/v1/scripts/{script_id}/approve` | quality gates | draft → approved |
| POST | `/api/v1/scripts/{script_id}/override` | — | Force approve, audit trail |
| GET | `/api/v1/scripts/{script_id}/versions` | — | Full version history |
| GET | `/api/v1/scripts/{script_id}/compare?from=N&to=M` | — | Section diff between revisions |

### Hooks
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/scripts/{script_id}/hooks/generate` | Uses hardcoded `channel_id="default"` |
| GET | `/api/v1/scripts/{script_id}/hooks` | List all hook variants for script |
| POST | `/api/v1/hooks/{hook_id}/score` | AI re-score; iterates all scripts (O(n)) |
| POST | `/api/v1/hooks/{hook_id}/select` | Mark as selected; clears others |

### Visual Plan
| Method | Path | Gate | Notes |
|---|---|---|---|
| POST | `/api/v1/scripts/{script_id}/visual-plan/generate` | script approved | AI scene generation |
| GET | `/api/v1/scripts/{script_id}/visual-plan` | — | |
| PATCH | `/api/v1/visual-plans/{visual_plan_id}` | — | Update scenes |
| POST | `/api/v1/visual-plans/{visual_plan_id}/approve` | — | 409 if already approved |

### Audio Brief
| Method | Path | Gate | Notes |
|---|---|---|---|
| POST | `/api/v1/scripts/{script_id}/audio-brief/generate` | script approved | AI brief generation |
| GET | `/api/v1/scripts/{script_id}/audio-brief` | — | Returns latest by created_at |
| PATCH | `/api/v1/audio-briefs/{audio_brief_id}` | — | 409 if already approved |
| POST | `/api/v1/audio-briefs/{audio_brief_id}/approve` | — | 409 if already approved |
| POST | `/api/v1/audio-briefs/{audio_brief_id}/export` | script + brief approved | Returns export_text |

### Retention
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/scripts/{script_id}/retention/analyze` | |
| GET | `/api/v1/scripts/{script_id}/retention/latest` | |

### Compliance
| Method | Path | Notes |
|---|---|---|
| POST | `/api/v1/ideas/{idea_id}/compliance/review` | Also registered at `/ideas/{idea_id}/compliance/review` (legacy) |
| GET | `/api/v1/ideas/{idea_id}/compliance/latest` | Also at `/ideas/{idea_id}/compliance/latest` |
| GET | `/api/v1/ideas/{idea_id}/compliance/reports` | Also at `/ideas/{idea_id}/compliance/reports` |
| POST | `/api/v1/compliance/{report_id}/approve` | Also at `/compliance/{report_id}/approve` |
| POST | `/api/v1/compliance/{report_id}/override` | Also at `/compliance/{report_id}/override` |

> 5 compliance endpoints are dual-registered with and without the `/api/v1` prefix. The unversioned aliases appear to be legacy paths added for frontend compatibility.

### Title & Thumbnail Lab
| Method | Path | Gate | Notes |
|---|---|---|---|
| POST | `/api/v1/ideas/{idea_id}/titles/generate` | script approved | **BUG: see §20** |
| GET | `/api/v1/ideas/{idea_id}/titles` | — | |
| POST | `/api/v1/titles/{title_id}/score` | — | Iterates all scripts (O(n)) |
| POST | `/api/v1/titles/{title_id}/select` | — | Syncs to publishing package; 409 if package missing |
| POST | `/api/v1/ideas/{idea_id}/thumbnails/generate-briefs` | script approved | **BUG: see §20** |
| GET | `/api/v1/ideas/{idea_id}/thumbnails` | — | |
| POST | `/api/v1/thumbnails/{thumbnail_id}/select` | — | Syncs to publishing package; 409 if package missing |

### Publishing Package
| Method | Path | Gate | Notes |
|---|---|---|---|
| POST | `/api/v1/ideas/{idea_id}/publishing-package` | approved script + approved compliance + angle approved | 409 if package already exists |
| GET | `/api/v1/ideas/{idea_id}/publishing-package` | — | |
| PATCH | `/api/v1/ideas/{idea_id}/publishing-package` | — | |
| POST | `/api/v1/ideas/{idea_id}/publishing-package/validate` | approved script + approved compliance | |
| POST | `/api/v1/ideas/{idea_id}/publishing-package/approve` | passes validation | |
| GET | `/api/v1/ideas/{idea_id}/publishing-package/revisions` | — | |
| POST | `/api/v1/publishing-packages/{package_id}/export` | — | format: json or markdown |

---

## 10. Current Shared Contracts / Types Map

### Enumerations

| Enum | File | Values |
|---|---|---|
| `ScriptState` | `scripts.py` | `draft`, `approved`, `ready_to_publish` |
| `HookVariantType` | `scripts.py` | `contradiction`, `shock`, `question`, `story`, `mistake`, `before_after`, `hidden_mechanism` |
| `RiskLevel` | `compliance.py` | `low`, `medium`, `high` |
| `ComplianceRecommendation` | `compliance.py` | `approve`, `approve_with_fixes`, `high_risk`, `do_not_publish` |
| `ReviewerSource` | `compliance.py` | `deterministic`, `ai_assisted`, `human_override` |
| `ApprovalState` | `compliance.py` | `pending`, `approved`, `rejected`, `overridden` |
| `PublishingPackageStatus` | `publishing_package.py` | `draft`, `ready_for_review`, `approved`, `blocked` |
| `VisualType` | `visual_plan.py` | `stock`, `ai_image`, `ai_video`, `diagram`, `timeline`, `map`, `chart`, `screen_recording`, `b_roll`, `text_animation`, `icon_animation` |
| `VisualPlanApprovalState` | `visual_plan.py` | `draft`, `approved` |
| `VoiceStyle` | `audio_brief.py` | `documentary_calm`, `energetic_explainer`, `dark_mystery`, `educational_neutral`, `business_authority`, `storytelling_warm` |
| `AngleStatus` | `angle_approval.py` | `pending`, `approved`, `rejected` |
| `PublishingPackageExportFormat` | `publishing_package_export.py` | `json`, `markdown` |

### AIProvider Protocol

```python
class AIProvider(Protocol):
    model: str
    def generate(self, prompt: str) -> str: ...
```

Any conforming class can be passed to `ScriptAIService`, `AudioBriefAIService`, or `TitleThumbnailAIService`. No streaming interface defined.

### Gate constants (in `main.py`)

```python
GateRule:
  min_overall_score: float = 7.0   # configurable per-request
  min_hook_score: float = 7.0
  banned_phrases: list[str] = ["guaranteed viral", "zero effort success"]
```

### Compliance gate logic (in `compliance_checks.py`)

`compliance_gate_failures(report, required_fixes_resolved)` — returns list of blocking failures. Called in `approve_compliance_report` and `_enforce_ready_to_publish_compliance`.

### Error envelope

```python
class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}
```

Used consistently on all error responses. HTTPException wraps it as `detail`.

---

## 11. Current Docs Map

| Path | Purpose | Quality |
|---|---|---|
| `docs/architecture.md` | Architecture stub | 2 lines — empty placeholder |
| `docs/script-studio.md` | Route label | 3 lines — empty placeholder (duplicates product file name) |
| `docs/product/script-studio.md` | Authoritative Script Studio flow | 161 lines — complete, matches implementation |
| `docs/product/hook-retention-lab.md` | Hook Retention Lab spec | Full spec — describes a richer API than what is implemented |
| `docs/product/visual-plan-builder.md` | Visual Plan Builder spec | Matches implementation intent; per-scene approve not yet implemented |
| `docs/product/title-thumbnail-lab.md` | Title/Thumbnail Lab spec | Present — content not read; assumed aligned |
| `docs/product/publishing-package.md` | Publishing Package spec | Present — content not read; assumed aligned |
| `docs/compliance/compliance-guard.md` | Compliance Guard policy spec | 66 lines — describes richer HOLD/BLOCK decision model; implementation uses simpler approve/override |
| `docs/compliance/synthetic-content-disclosure.md` | Disclosure policy | Present |
| `docs/compliance/reused-repetitive-content.md` | Reuse policy | Present |
| `docs/prompts/*.md` | 14 LLM prompt templates | Loaded at runtime by AI services |

---

## 12. Current Docker / Infra / CI Setup

**None exists.** The following are confirmed absent:

- No `Dockerfile`
- No `docker-compose.yml` or `docker-compose.yaml`
- No `.env` or `.env.example`
- No `.github/` directory or GitHub Actions workflows
- No `Makefile`
- No `nginx.conf` or reverse proxy config
- No cloud infrastructure files (Terraform, Pulumi, CDK)
- No container registry references

The only runtime instruction is in `README.md`:

```bash
uvicorn app.main:app --reload --app-dir backend
npm run dev --prefix frontend
```

---

## 13. Current Test Coverage Summary

**Backend:** 13 test files using `pytest` + `fastapi.testclient.TestClient`.

| Test file | What it covers |
|---|---|
| `test_health.py` | Health endpoint |
| `test_modules_import.py` | Module-level import smoke test |
| `test_scripts_api.py` | Script CRUD, generate-outline, generate-draft, score, improve, approve, override, versions, compare, hooks |
| `test_script_ai_service.py` | `ScriptAIService` unit tests against MockProvider |
| `test_scripts_domain.py` | `Script` model validation — sections, length rules, state |
| `test_visual_plan_api.py` | Visual plan generate, get, patch, approve endpoints |
| `test_visual_plan_ai_service.py` | `generate_visual_plan` AI service unit test |
| `test_visual_plan_models.py` | `VisualScene` / `VisualPlan` model validation |
| `test_title_thumbnail_api.py` | Title generate, score, select; thumbnail generate, select endpoints |
| `test_audio_brief_ai_service.py` | `AudioBriefAIService` unit test |
| `test_compliance_checks.py` | `run_compliance_checks`, `publishing_blocked` unit tests |
| `test_compliance_extended.py` | Extended compliance scenarios |
| `test_publishing_api.py` | Publishing package generate, get, patch, validate, approve, export |

**Frontend:** 2 test files (`IdeaDetailPage.test.jsx`, `ScriptStudioPage.test.jsx`). Test strategy and coverage level are not known without running them.

**Not tested:**

- Channel memory endpoints (no test file)
- Retention endpoints (no dedicated test file)
- Audio brief CRUD endpoints (AI service tested; API CRUD not confirmed)
- `compliance_gate_failures` edge cases with override states
- `generate_thumbnail_briefs` bug path (see §20)

**Test configuration** (`pyproject.toml`):

```toml
[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["backend"]
```

---

## 14. Existing Modules Related to Key QualityTube OS Concerns

### Channels

- **Exists:** `ChannelMemory` model + `ChannelMemoryRepository` (`channel_memory.py`)
- **Coverage:** `channel_id`, `tone_notes`, `banned_claims`; upsert-only; one entry seeded (`channel_id="default"`)
- **Not implemented:** channel CRUD API (no `POST /api/v1/channels`), multi-channel support, channel profile management, YouTube channel association

### Topics / Content Ideas

- **Exists:** `Idea` model in `ideas.py` (`id`, `title`, `audience`, `premise`)
- **Not implemented:** no CRUD API for ideas, no topic/trend research, no idea pipeline; idea_id is passed as a raw path string to all endpoints

### Script

- **Fully implemented:** `Script`, `ScriptSection`, `ScriptQualityReport`, `ScriptVersion`, `ScriptRepository`, `ScriptAIService`, all 11 script endpoints

### Hooks

- **Implemented:** `HookVariant`, hook generation/scoring/selection endpoints
- **Spec gap:** `docs/product/hook-retention-lab.md` describes a richer `lab_id`-based system with `retention_hypothesis`, `expected_dropoff_risk`, structured reviewer decisions, and three separate endpoints. Current implementation is simpler (no lab entity, no reviewer decision record, no history endpoint).

### Briefs

- **Implemented:** `AudioBrief`, `AudioBriefAIService`, 5 audio brief endpoints
- **Not implemented:** Research briefs (model exists, not wired)

### Publishing

- **Implemented:** `PublishingPackage`, `PublishingPackageRevision`, `PublishingPackageRepository`, `PublishingPackageValidationService`, `PublishingPackageExportService`, 7 publishing endpoints

### Analytics

- **Does not exist.** No YouTube Analytics API integration, no retention data ingestion, no performance dashboards.

### Compliance

- **Implemented:** `ComplianceReport`, `compliance_checks.py` (deterministic), AI-assisted review via `ScriptAIService.provider`, 5 compliance endpoints + override with audit log
- **Spec gap:** `docs/compliance/compliance-guard.md` describes a richer ALLOW/HOLD/BLOCK model with a Policy Classifier, Risk Scoring Module, and separate Audit Logger service. Current implementation collapses this to a single `review_compliance` function.

### YouTube OAuth

- **Does not exist.** No OAuth2 flow, no token storage, no YouTube API client.

### Media

- **Does not exist.** No file upload, no media storage, no asset management.

### AI Agents

- **Pattern exists:** `AIProvider` protocol + `MockProvider`. Not a true agent framework (no tool use, no memory, no multi-step reasoning). Each AI operation is a single `generate(prompt) -> str` call.

### LLM Calls

- **Implemented:** `LLMCall` model + `LLMCallLogger` (in-memory only). Every AI call is logged with provider, model, operation, prompt, response, token estimates, latency, correlation_id. Not persisted, not observable.

### Workflow / Pipeline Runs

- **Does not exist.** No DAG runner, no pipeline orchestration, no step-by-step workflow tracking across the full idea→script→compliance→publishing lifecycle.

---

## 15. Duplicate or Overlapping Concepts

### Dual script lookup structures

`ScriptRepository._canonical_by_idea` (keyed by idea_id) and `script_by_id: dict[UUID, Script]` (keyed by script UUID) in `main.py` both hold canonical `Script` objects. Every write operation must update both. This is a consistency bug waiting to happen; the repository should own both lookups.

### Duplicate compliance path registration

Five compliance endpoints are registered twice (`/api/v1/...` and the unversioned `/...` form). This doubles the route table and may cause confusion for API consumers and test authors.

### `ScriptDraft` vs `Script`

`ScriptDraft` (defined at line 310 of `scripts.py`) contains `idea_id`, `hook`, `outline`, `cta`. This overlaps with `Script.sections` and `OutlinePayload`. It is unused and should be removed or explained.

### `ResearchBrief` vs channel context string

`ResearchBrief` (`research_brief.py`) has `topic`, `goals`, `references`. In `main.py`, research context is passed as a raw formatted string to AI services (`_build_script_studio_context` → `script_context`). The typed model is unused.

### `AngleStatus` vs string comparison

`AngleStatus` enum (in `angle_approval.py`) defines `pending/approved/rejected`, but angle approval is validated in `_ensure_angle_gate` by string comparison (`request.angle_status.lower().strip() == "approved"`). The enum is not used.

### Hook scoring in two places

Hook scoring is in `ScriptAIService.score_hook`. The `score_hook` endpoint in `main.py` also directly mutates hook fields (`hook.score = ...`) on the live object rather than going through the repository's `update_hook_score` method. Both paths exist.

### `PublishingPackageService` inside `main.py`

`PublishingPackageService` is a full service class defined inline within `main.py` rather than in the modules directory. This breaks the module boundary.

---

## 16. Safe Extension Points

The following are clean, low-risk integration points for new QualityTube OS features:

1. **Real LLM provider**: Implement `AIProvider` protocol with any provider SDK. Inject into `ScriptAIService(provider=MyProvider())`, `AudioBriefAIService(provider=...)`, `TitleThumbnailAIService(provider=...)`. Zero changes to business logic required.

2. **Database persistence layer**: All repositories follow the same pattern (`_canonical_by_X: dict`, `create`, `revise`, `get`, `get_by_id`). Replace the dict-backed internals with SQLAlchemy/asyncpg sessions without changing repository interfaces or the API layer.

3. **New channel memory fields**: `ChannelMemory` has no strict model constraints. New fields (language, upload schedule, brand kit, content pillars) can be added without breaking existing consumers.

4. **Prompt template improvements**: Prompt files in `docs/prompts/` are loaded at runtime. Edit them without touching Python code.

5. **Additional approval gates**: `GateRule` is passed per-request. New gate rules can be added to `GateRule` and enforced in `_enforce_approval_gates` without touching other endpoints.

6. **New export formats**: `PublishingPackageExportFormat` is an enum + `PublishingPackageExportService`. Add a new enum value and a render method with no API changes.

7. **Compliance check rules**: `run_compliance_checks` in `compliance_checks.py` is a pure function with a `ComplianceCheckInput` dataclass. New deterministic rules can be added without touching the API layer.

8. **VisualScene additional fields**: `VisualScene` has `asset_notes` and `risk_notes` as nullable strings. New optional metadata fields for downstream rendering pipelines can be added without breaking existing scenes.

9. **Frontend routing**: `AppRoutes.jsx` has a clean route table. New top-level pages (analytics, channel settings, idea pipeline) can be added without modifying existing routes.

10. **Ideas API**: `Idea` model (`ideas.py`) is defined but has no endpoints. Adding CRUD at `/api/v1/ideas` requires only a new in-memory repository and endpoint block — no other modules need to change.

---

## 17. Do-Not-Touch List

Files that encode enforced business rules or have wide downstream impact. Changes require full regression testing and careful cross-file audit.

| File | Reason |
|---|---|
| `backend/app/modules/scripts.py` | `Script.validate_sections` enforces the hook/body/cta structure and 120-char minimum. Relaxing these breaks approval gate assumptions. |
| `backend/app/modules/compliance.py` | `ComplianceReport.validate_conditional_fields` enforces override consistency constraints. Changing override rules requires audit log contract review. |
| `backend/app/modules/compliance_checks.py` | `compliance_gate_failures` and `run_compliance_checks` are the core policy enforcement functions. Changes alter what content can be published. |
| `backend/app/modules/publishing_package.py` | `PublishingPackage.validate_disclosure_requirement` links compliance synthetic disclosure flag to required field presence. Changing it may allow undisclosed AI content to publish. |
| `backend/app/modules/audio_brief.py` | `AudioBrief.validate_disclosure_policy` ensures `synthetic_voice_used=True` always requires disclosure. Do not weaken this invariant. |
| `backend/app/main.py` — `_enforce_approval_gates` | The server-side gate function. Client-side warnings mirror these values; they must stay in sync. |
| `backend/app/main.py` — `_enforce_ready_to_publish_compliance` | Compliance gate check on state transition to `ready_to_publish`. |
| `backend/app/modules/__init__.py` | Central re-export hub. Adding/removing here immediately affects all consumers of the package. |
| `docs/prompts/compliance-review.md` | Loaded at runtime. Prompt changes alter compliance AI recommendations for all content. |
| `docs/prompts/publishing-package-generation.md` | Loaded at runtime. Prompt changes alter generated metadata for all publishing packages. |

---

## 18. Gaps Blocking QualityTube OS Implementation

These are confirmed missing capabilities required to ship a production-ready system:

### Critical gaps (system cannot function without these)

1. **No real LLM provider wired.** `MockProvider` returns hardcoded JSON. No real AI generation occurs. Plugging in OpenAI / Anthropic / Google requires implementing `AIProvider` protocol and injecting it.

2. **No database persistence.** All state is in-memory and ephemeral. A process restart wipes all ideas, scripts, compliance reports, and publishing packages. Requires: ORM selection, schema design, migration toolchain, connection pooling.

3. **No authentication or authorisation.** Any user can approve, override, or export any content. No identity, no roles, no RBAC, no API keys.

4. **No Idea management API.** `idea_id` is a raw string path parameter. There is no way to create, list, search, or manage ideas through the API. The `Idea` model exists but is unregistered.

5. **No channel management API.** Only one hardcoded `channel_id="default"` channel exists. Multi-creator, multi-channel, and agency workflows are impossible. No CRUD for channels.

### Functional gaps (required for the QualityTube OS vision)

6. **No YouTube API integration.** OAuth 2.0 flow, YouTube Data API v3 (video upload, metadata update, chapters, thumbnail upload), channel analytics pull — none exist.

7. **No angle/idea pipeline.** No endpoints to create idea angles, approve/reject angles, or link angles to ideas. `AngleStatus` enum is defined but unused. The frontend receives `angle_status` as a user-supplied string with no server-side lifecycle.

8. **Hook Retention Lab spec gap.** `docs/product/hook-retention-lab.md` specifies: `POST /api/v1/scripts/{script_id}/hook-retention/generate` (with lab_id, retention_hypothesis, expected_dropoff_risk, signals), `POST /hook-retention/reviews` (with reviewer decision, apply_to_script), `GET /hook-retention/labs`. The current implementation exposes a simpler flat hook endpoint with no lab entity, no reviewer decision record, and no lab history endpoint.

9. **Compliance Guard spec gap.** `docs/compliance/compliance-guard.md` describes a HOLD gate (ambiguous risk requiring human review), a Policy Classifier, and a jurisdictional overlay system. Current implementation has only ALLOW/BLOCK with override.

10. **Per-scene visual plan approval.** `docs/product/visual-plan-builder.md` describes per-scene approve/revise/reject decisions. Current implementation approves the entire plan as a unit.

11. **No LLM observability.** `LLMCallLogger` holds call logs in memory on each service instance. No persistence, no API endpoint to query logs, no dashboard, no cost tracking.

12. **No async / background processing.** Large AI operations (visual plan generation, publishing package generation with multi-step validation) block the HTTP request thread. No Celery, no task queue, no progress endpoint.

13. **No file or asset management.** Thumbnail briefs are text. No image upload, storage, CDN, or thumbnail generation pipeline.

14. **No analytics ingestion.** No YouTube Analytics API pull, no retention curve data, no CTR/impression tracking.

15. **Duplicate path bug (`generate_thumbnail_briefs`).** See §20.

---

## 19. Recommended Implementation Sequence

This sequence minimises merge conflicts and architectural duplication by building on existing extension points:

### Phase 0 — Stabilise the existing codebase (no new features)
1. Fix the `generate_thumbnail_briefs` bug (§20).
2. Eliminate the dual script lookup (`script_by_id` + `ScriptRepository`): move the UUID index into `ScriptRepository`.
3. Remove duplicate compliance URL aliases or document them explicitly.
4. Move `PublishingPackageService` from `main.py` into `modules/publishing_package_service.py`.
5. Split `main.py` into FastAPI sub-routers (scripts, compliance, publishing, visual_plan, audio_brief, title_thumbnail) using `APIRouter`.
6. Delete or wire up orphaned models (`ScriptDraft`, `ResearchBrief`). Delete `AngleStatus` or use it in gate validation.

### Phase 1 — Database and persistence layer
7. Add `sqlalchemy` (async) + migration tool (`alembic`) to `pyproject.toml`.
8. Define ORM models for: `Channel`, `Idea`, `Angle`, `Script`, `ScriptVersion`, `ComplianceReport`, `PublishingPackage`, `PublishingPackageRevision`, `VisualPlan`, `AudioBrief`, `TitleVariant`, `ThumbnailConcept`, `HookVariant`, `LLMCallLog`.
9. Swap repository internals to use database sessions; keep repository interfaces unchanged.

### Phase 2 — Authentication and channel management
10. Add auth middleware (FastAPI-Users or custom JWT). Define `User` model.
11. Add `POST /api/v1/channels`, `GET /api/v1/channels`, `PATCH /api/v1/channels/{channel_id}` wired to `ChannelMemory`.
12. Multi-channel support: remove hardcoded `channel_id="default"`; resolve from authenticated user context.

### Phase 3 — Idea and angle pipeline
13. Add `POST /api/v1/ideas`, `GET /api/v1/ideas`, `GET /api/v1/ideas/{idea_id}` wired to `Idea` model.
14. Add `AngleStatus` lifecycle: `POST /api/v1/ideas/{idea_id}/angles`, `POST /api/v1/angles/{angle_id}/approve`.
15. Update `GenerateScriptRequest` to validate against persisted angle state rather than accepting raw string.

### Phase 4 — Real LLM provider
16. Add Anthropic or OpenAI SDK to `pyproject.toml`.
17. Implement `AIProvider` protocol for the chosen provider with prompt caching where applicable.
18. Persist `LLMCall` logs to the database via the `LLMCallLogger`.
19. Add `GET /api/v1/llm-logs` (admin-only) for observability.

### Phase 5 — Hook Retention Lab (spec-complete)
20. Add `HookRetentionLab` domain model, `HookRetentionVariant`, `HookRetentionReview` per the product spec.
21. Implement the three new endpoints described in `docs/product/hook-retention-lab.md`.
22. Keep existing `/hooks/generate` and `/hooks/{hook_id}/score` endpoints for backwards compatibility.

### Phase 6 — YouTube integration
23. Add `google-api-python-client` + OAuth2 flow.
24. Add `POST /api/v1/channels/{channel_id}/youtube/connect` OAuth initiation.
25. Add `POST /api/v1/publishing-packages/{package_id}/upload` to push to YouTube Data API v3.
26. Add `GET /api/v1/channels/{channel_id}/analytics` for YouTube Analytics pull.

### Phase 7 — Async workers
27. Add Celery + Redis.
28. Move AI generation operations (visual plan, publishing package, compliance review) to Celery tasks.
29. Add `GET /api/v1/tasks/{task_id}` polling endpoint.

---

## 20. Immediate Risks and Mitigation Plan

### Risk 1 — CONFIRMED BUG: `generate_thumbnail_briefs` crashes at runtime

**Location:** `backend/app/main.py`, line 1040

**Description:** The endpoint handler passes `payload.titles` to `title_thumbnail_ai.generate_thumbnail_briefs()`, but `GenerateThumbnailBriefsRequest` only defines `angle_status` — there is no `titles` field. Calling this endpoint raises `AttributeError: 'GenerateThumbnailBriefsRequest' object has no attribute 'titles'`.

**Mitigation:** Add `titles: list[str] = Field(default_factory=list)` to `GenerateThumbnailBriefsRequest`, or derive selected titles from `TitleThumbnailLabRepository` based on `idea_id` before calling the service. The AI service requires at least one title (`ValueError` if empty).

**Risk level:** High — endpoint is unreachable in its current state. The test file for title/thumbnail API likely does not cover this path.

---

### Risk 2 — Dual script lookup desync

**Location:** `main.py` — `script_by_id` dict vs `ScriptRepository._canonical_by_idea`

**Description:** Both are written on create (`repo.create_script` + `script_by_id[script.id] = script`) and on revise (`repo.revise_script` + `script_by_id[script_id] = updated`). A future developer adding an endpoint may write to one and forget the other, causing stale data on lookups by UUID.

**Mitigation:** Move `_by_script_id: dict[UUID, Script]` into `ScriptRepository` and add a `get_by_id(script_id: UUID)` method. Remove `script_by_id` from `main.py`. Priority: Phase 0.

---

### Risk 3 — Internal repository state access in `main.py`

**Location:** `main.py` lines 866, 429

**Description:** `get_audio_brief` and `_audio_brief_by_id_or_404` directly access `audio_brief_repo._by_script` (a private attribute). This couples `main.py` to the internal dict structure of `AudioBriefRepository`.

**Mitigation:** Add `AudioBriefRepository.get_latest(script_id)` and `AudioBriefRepository.get_by_id(audio_brief_id)` methods. Remove direct `_by_script` access from `main.py`.

---

### Risk 4 — No authentication

**Description:** All endpoints are fully public. Any caller can approve, override, or export compliance reports and publishing packages without any identity verification. Override audit entries record an `approver` string but it is user-supplied with no verification.

**Mitigation:** Add FastAPI middleware with JWT validation before Phase 3. Mark all override and approve endpoints as requiring an `admin` or `reviewer` role.

---

### Risk 5 — `ready_to_publish` state is not a valid transition

**Description:** `ScriptState` includes `ready_to_publish`, and `PATCH /scripts/{id}` allows setting `state=ready_to_publish`. This triggers `_enforce_ready_to_publish_compliance`. However, no endpoint transitions `state` to `ready_to_publish` programmatically — only the PATCH endpoint with a user-supplied state value does this. The state is not mentioned in the Script Studio product spec's state machine.

**Mitigation:** Either add a dedicated `POST /api/v1/scripts/{script_id}/ready-to-publish` endpoint with proper gate enforcement, or remove `ready_to_publish` from the PATCH payload options. Clarify the state machine in `docs/product/script-studio.md`.

---

### Risk 6 — `generate_draft` calls `_build_script_studio_context` twice

**Location:** `main.py`, `generate_draft` function, lines 676–680

**Description:** `_build_script_studio_context(channel_id=payload.channel_id)` is called twice redundantly when building context for `generate_draft`. This calls `channel_memory_repo.get` twice and is inefficient.

**Mitigation:** Extract the tuple result once. Low priority but indicates incomplete refactor.

---

### Risk 7 — No idempotency on publishing package generation

**Description:** `POST /api/v1/ideas/{idea_id}/publishing-package` returns `409 PUBLISHING_PACKAGE_EXISTS` on second call. There is no way to regenerate the publishing package once created (no delete, no regenerate endpoint). The user is stuck with the first generated version or must use PATCH to overwrite fields manually.

**Mitigation:** Add a `force=true` query param or a `POST /ideas/{idea_id}/publishing-package/regenerate` endpoint that archives the existing package and creates a new one.

---

### Risk 8 — `PublishingPackageService` leaks into `main.py`

**Description:** `PublishingPackageService` is a 80-line service class defined inside `main.py`. It mixes infrastructure concerns (repository wiring, error raising) with domain logic. It is not importable or testable independently.

**Mitigation:** Move to `backend/app/modules/publishing_package_service.py`. Priority: Phase 0.

---

## Summary

| Category | Status |
|---|---|
| Backend framework | FastAPI — working |
| Domain models | Complete for current scope |
| API endpoints | ~50 endpoints — working with MockProvider |
| Frontend | Working scaffold — 3 pages, 2 tests |
| Real LLM | Not wired |
| Database | Not wired (in-memory only) |
| Authentication | Not implemented |
| YouTube API | Not implemented |
| Celery / async workers | Not implemented |
| Docker / CI | Not implemented |
| Idea management | Model only, no API |
| Channel management | Hardcoded to "default" |
| Analytics | Not implemented |
| Hook Retention Lab | Partial (simpler than spec) |
| Compliance Guard | Partial (simpler than spec) |
| Known bugs | 1 confirmed crash bug (thumbnail briefs) |
| Test coverage | 13 backend test files — moderate; frontend minimal |

---

## Files Created

- `docs/architecture/repo-reconnaissance.md` *(this file)*

## Files Changed

- None

## Tests Run

- None (read-only audit)

## Known Limitations

- Frontend test content was not read; coverage level for `IdeaDetailPage.test.jsx` and `ScriptStudioPage.test.jsx` is unverified.
- `docs/product/title-thumbnail-lab.md` and `docs/product/publishing-package.md` were not read in full; their spec-vs-implementation alignment is assumed rather than confirmed.
- Exact line counts for frontend JSX files are approximate (not counted during audit).
- No running instance was tested; runtime behaviour of MockProvider responses was inferred from source inspection only.

## Recommended Next Prompt

> "Fix the three Phase 0 issues identified in the reconnaissance report: (1) the `generate_thumbnail_briefs` AttributeError bug in `main.py`; (2) consolidate the dual script lookup by adding `get_by_id` to `ScriptRepository` and removing `script_by_id` from `main.py`; (3) add `get_latest` and `get_by_id` methods to `AudioBriefRepository` to eliminate direct `_by_script` access. Do not change any domain models, endpoint contracts, or test files beyond what is required to fix these three issues."
