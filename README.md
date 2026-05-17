# QualityTube OS

**AI-assisted, human-approved, compliance-aware YouTube content operations.**

QualityTube OS is a structured content production system for YouTube creators, small teams, expert brands and content agencies. It combines AI assistance with deterministic quality gates, compliance review, and human approval checkpoints to help produce original, measurable, policy-safe video content.

> **Core philosophy:** Create better YouTube videos with AI — not more spam.

---

## What the system does

- Generates and scores video scripts against nine quality dimensions.
- Proposes and evaluates multiple hook variants against retention signals.
- Runs deterministic and AI-assisted compliance checks against YouTube content policies.
- Builds structured publishing packages: title, description, tags, chapters, and upload checklist.
- Proposes scene-by-scene visual plans for approved scripts.
- Generates voice and audio delivery briefs for narrators or synthetic voice pipelines.
- Produces title candidates and thumbnail visual briefs with clickbait-risk scoring.
- Enforces approval gates at every lifecycle stage — script, compliance, and publishing.
- Maintains full version history and audit trails for every editorial decision.

## What the system explicitly does not do

- Does not mass-generate videos automatically without human review.
- Does not auto-upload content to YouTube without explicit human approval.
- Does not promise monetization outcomes, AdSense revenue, or passive income.
- Does not produce or endorse content designed to exploit loopholes in YouTube's policies.
- Does not replace human editorial judgment — it informs and assists it.
- Does not generate clickbait, misleading claims, or synthetic content without disclosure.

---

## Target users

| User type | Primary use case |
|---|---|
| Solo YouTube creators | Plan, write, and review content with AI assistance before publishing |
| Expert-led channels | Maintain brand voice, quality standards, and compliance across episodes |
| Small content teams | Structured approval workflows and version history across writers and reviewers |
| Content agencies | Manage multi-channel production with shared compliance policies |
| Educator and B2B channels | Produce accurate, evidence-backed, policy-safe video content at scale |

---

## Core modules

| Module | Purpose | Status |
|---|---|---|
| **Channel Workspace** | Channel profile, tone notes, banned claims | Scaffold — single hardcoded channel |
| **Script Studio** | Generate, score, improve, version, and approve scripts | Implemented |
| **Hook & Retention Lab** | Generate and evaluate hook variants with retention signals | Partial (flat hooks; full lab spec pending) |
| **Compliance Guard** | Deterministic + AI-assisted YouTube policy review | Implemented |
| **Publishing Package** | Structured upload metadata with validation and export | Implemented |
| **Visual Plan Builder** | Scene-by-scene visual strategy for approved scripts | Implemented |
| **Voice & Audio Studio** | Voice delivery briefs for narrators or synthesis pipelines | Implemented |
| **Title & Thumbnail Lab** | AI-generated titles and thumbnail concepts with risk scoring | Implemented |
| **Content Idea Board** | Idea capture and angle management | Model only — no API yet |
| **Analytics Feedback Loop** | Import performance data to inform future content decisions | Not yet implemented |

---

## MVP scope

The MVP covers the full content production lifecycle from idea to a reviewable, exportable publishing package:

**Included in MVP:**
- Channel Workspace and Channel Memory
- Content Idea Board (idea + angle lifecycle)
- Script Studio with quality scoring and approval gates
- Hook & Retention Lab (full lab spec)
- Compliance Guard (deterministic + AI-assisted review)
- Publishing Package (generation, validation, versioning, export)
- Title & Thumbnail Lab
- Visual Plan Builder
- Voice & Audio Studio
- Human Approval Workflow (gates, overrides, audit trail)
- Manual analytics feedback loop

**Excluded from MVP:**
- Automatic mass video generation without human review
- Blind auto-upload to YouTube
- Full YouTube Analytics API integration
- SaaS billing and subscription management
- Agency management and multi-tenant isolation
- Asset marketplace
- Full non-linear video editor
- Advanced TTS and voice synthesis integrations

See [`docs/product/mvp-scope.md`](docs/product/mvp-scope.md) for the complete MVP definition.

---

## Architecture overview

```
qualitytube-os/
├── backend/              # FastAPI application (Python 3.11+)
│   ├── app/
│   │   ├── main.py       # API endpoints and request/response models
│   │   └── modules/      # Domain models, repositories, AI services
│   └── tests/            # pytest test suite
├── frontend/             # React 18 + Vite (JSX, React Router 6)
│   └── src/
│       ├── pages/        # ScriptStudioPage, IdeaDetailPage, HomePage
│       ├── components/   # VisualPlanTab and shared components
│       └── routes/       # AppRoutes
└── docs/
    ├── architecture/     # Architectural records
    ├── compliance/       # YouTube policy specifications
    ├── product/          # Product vision, scope, and positioning
    └── prompts/          # LLM prompt templates (loaded at runtime)
```

**Backend:** FastAPI + Pydantic v2. All state is currently in-memory (database integration is in the roadmap). AI operations use a pluggable `AIProvider` protocol — `MockProvider` is the default for local development; any provider implementing `generate(prompt: str) -> str` can be injected.

**Frontend:** React 18 with React Router 6 and Vite. No global state manager. Feature state is isolated per page section.

**AI layer:** Single-method `AIProvider` protocol. Prompt templates for compliance, publishing, visual plan, and audio brief are stored as Markdown files in `docs/prompts/` and loaded at runtime.

---

## Local development quickstart

### Prerequisites

- Python 3.11 or later
- Node.js 18 or later
- `pip` / `venv`

### Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Start the API server
uvicorn app.main:app --reload --app-dir backend
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### Frontend

```bash
# Install dependencies
npm install --prefix frontend

# Start the development server
npm run dev --prefix frontend
# UI available at http://localhost:5173
```

### Run both

```bash
# Terminal 1
uvicorn app.main:app --reload --app-dir backend

# Terminal 2
npm run dev --prefix frontend
```

---

## Environment variables

The current in-memory scaffold requires no environment variables. When database persistence and a real AI provider are added, the following variables will be required:

| Variable | Purpose | Required |
|---|---|---|
| `AI_PROVIDER` | Provider identifier (`anthropic`, `openai`) | When real LLM is configured |
| `AI_API_KEY` | API key for the configured AI provider | When real LLM is configured |
| `AI_MODEL` | Model identifier (e.g. `claude-sonnet-4-6`) | When real LLM is configured |
| `DATABASE_URL` | PostgreSQL connection string | When database is configured |
| `SECRET_KEY` | Application secret for JWT signing | When auth is enabled |

Copy `.env.example` to `.env` and fill in values (`.env.example` will be added in the database integration phase).

---

## Testing

### Backend tests

```bash
# Run all backend tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest backend/tests/test_scripts_api.py -v
```

### Frontend tests

```bash
# Run all frontend tests
npm run test --prefix frontend
```

### Linting

```bash
# Backend
ruff check backend

# Frontend
npm run lint --prefix frontend
```

---

## Compliance-first philosophy

QualityTube OS treats YouTube content policy compliance as a first-class concern, not an afterthought. Every piece of content passes through a two-stage compliance review before a publishing package can be approved:

1. **Deterministic checks** — text analysis for reused content signals, repetitive structure, mass-production indicators, clickbait phrases, synthetic disclosure requirements, and sensitive topic flags. These rules run without any AI model call and produce auditable, reproducible results.

2. **AI-assisted review** — a structured model review pass produces a risk matrix across eight dimensions, a recommendation (`approve`, `approve_with_fixes`, `high_risk`, `do_not_publish`), and a list of required fixes.

No publishing package can be approved while a compliance report carries unresolved required fixes or a `high` overall risk level.

See [`docs/compliance/youtube-quality-policy.md`](docs/compliance/youtube-quality-policy.md) for the full policy reference.

---

## Human approval workflow

AI assistance accelerates work but does not replace human judgment. Every major lifecycle stage requires explicit human approval:

| Stage | Gate | What is enforced |
|---|---|---|
| Script | Approval gate | Non-empty content, hook quality, banned phrases, quality score thresholds |
| Compliance report | Compliance gate | No unresolved required fixes, no `high` overall risk, no `do_not_publish` recommendation |
| Publishing package | Validation gate | Title length, chapter timestamps, description, disclosure notes when required |
| Audio brief | Approval gate | Approved brief required before export |
| Visual plan | Approval gate | Plan must be approved before handoff |

Every approval and override is recorded with actor identity, timestamp, and reason. Override paths exist for exceptional cases but are subject to audit and review.

---

## Quality gates

Script approval enforces these gates by default (configurable per request via `GateRule`):

| Gate | Rule | Default threshold |
|---|---|---|
| Non-empty content | Script must have sections | Required |
| Hook quality | Hook section ≥ 20 characters | Required |
| Banned phrases | Configurable blocked phrase list | `"guaranteed viral"`, `"zero effort success"` |
| Score presence | Quality report must exist before approval | Required |
| Minimum overall score | `overall_script_score` threshold | ≥ 7.0 / 10 |
| Minimum hook score | `hook_score` threshold | ≥ 7.0 / 10 |

Gates are enforced server-side. Frontend warnings are advisory mirrors of server logic and are not authoritative.

---

## Analytics feedback loop

The analytics feedback loop (roadmap Phase 18) will allow creators to import real YouTube performance data — watch time, audience retention curves, click-through rate, impressions — and feed it back into the Channel Memory and future content planning. The goal is a closed loop: measure what works, record it, and apply that knowledge to the next content cycle.

In the current MVP, this is a manual process: creators review their YouTube Studio analytics and update their channel notes directly.

---

## Documentation

| Document | Purpose |
|---|---|
| [`docs/product/vision.md`](docs/product/vision.md) | Why QualityTube OS exists and what problem it solves |
| [`docs/product/positioning.md`](docs/product/positioning.md) | Target users, differentiators, and product promise |
| [`docs/product/mvp-scope.md`](docs/product/mvp-scope.md) | What is and is not in the MVP |
| [`docs/product/non-goals.md`](docs/product/non-goals.md) | Explicit anti-goals |
| [`docs/compliance/youtube-quality-policy.md`](docs/compliance/youtube-quality-policy.md) | YouTube content policy reference |
| [`docs/architecture/repo-reconnaissance.md`](docs/architecture/repo-reconnaissance.md) | Full codebase audit and gap analysis |
| [`ROADMAP.md`](ROADMAP.md) | Implementation phases and priorities |

---

## License

See [LICENSE](LICENSE).
