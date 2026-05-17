# QualityTube OS — MVP Scope

This document defines what is and is not included in the MVP. It is the authoritative reference for prioritisation decisions and prevents scope creep from being introduced without a deliberate change to this document.

---

## MVP definition

The MVP covers the complete content production lifecycle from idea capture to a reviewable, exportable publishing package — with human approval checkpoints and compliance review at every critical stage.

The MVP is complete when a creator can run the following end-to-end workflow in a single session using a real AI provider:

1. Create a channel profile with tone notes and banned claims.
2. Create a content idea with audience and premise.
3. Conduct topic research and produce a research brief.
4. Generate and approve a content angle.
5. Generate, score, improve, and approve a script.
6. Generate and review hook variants in the Hook Retention Lab, select a winner.
7. Run compliance review, address required fixes, approve the compliance report.
8. Generate a publishing package with title, description, tags, chapters, and checklist.
9. Validate and approve the publishing package.
10. Export the publishing package as JSON or Markdown for manual YouTube upload.

---

## MVP includes

### Channel Workspace

A persistent channel profile that stores:
- Channel identity: name, niche description, target audience
- Tone notes: editorial voice guidelines for AI content generation
- Banned claims: phrases or claims the channel does not make
- Content pillars: topic areas the channel covers

AI generation across all modules is informed by channel memory.

### Channel Memory

The structured knowledge base attached to a channel profile. Channel Memory is the persistent context that makes AI assistance channel-specific rather than generic. It is updated by the creator and used automatically in script, hook, and title generation.

### Content Idea Board

A managed list of content ideas, each with:
- Title, audience, and premise
- Research brief (topic, goals, evidence sources)
- One or more angles, each with an approval state
- Workflow stage tracking from idea to publish

### Niche Intelligence

A niche profile for each channel that captures:
- Primary audience segments
- Competitive alternatives and how this channel differentiates
- Content gap analysis: underserved topic areas in the niche
- Niche context used in angle generation and topic research

### Topic Research Engine

Structured research per idea:
- What is already well-covered in this niche on this topic
- What is underexplored or misunderstood
- Key audience questions that the content should answer
- Evidence sources and reference notes
- Originality signals: what makes this treatment different

### Originality and Angle Engine

For each idea, one or more angles:
- Original argument or claim
- Counter-narrative (what generic treatment would say)
- Audience benefit
- Evidence requirement: what must be demonstrated for the claim to hold
- Scoring: originality, audience value, differentiation
- Approval lifecycle: pending → approved / rejected

A script cannot be generated until at least one angle is approved.

### Script Studio

Full script production and approval:
- Generate script outline (hook, beats, CTA) from approved angle and channel memory
- Generate full draft from outline
- Score script across 9 quality dimensions (0–10 each)
- Improve script with AI rewrite
- Approve script through configurable quality gates
- Override with documented justification and audit trail
- Version history with full snapshots and diff comparison

### Hook and Retention Lab

Lab-based hook variant generation and review:
- Generate multiple hook variants with retention diagnostics (curiosity gap, clarity, novelty, tempo)
- Score expected retention impact per variant
- Human reviewer selects winning variant, records decision and notes
- Apply winning variant to script hook section, creating a new revision
- Lab history maintained for audit

### Compliance Guard

Two-stage content policy review:
- **Stage 1 — Deterministic checks:** reused content signals, repetitive structure, mass-production indicators, synthetic disclosure requirement, clickbait phrases, sensitive topic flags. Runs without an AI call.
- **Stage 2 — AI-assisted review:** structured risk matrix across 8 dimensions, recommendation (approve / approve_with_fixes / high_risk / do_not_publish), required fixes list.
- Approve compliance report (with gate checks) or override with documented justification
- Publishing package cannot be approved while compliance is unresolved

### Publishing Package

Structured YouTube upload metadata:
- Title (validated against YouTube character limits)
- Description
- Tags
- Chapters (with timestamp format validation)
- Pinned first comment
- Thumbnail brief (text description for design handoff)
- Disclosure notes (required when synthetic content is used)
- Source notes
- Upload checklist
- Validation gate before approval
- Version history with full snapshots
- Export as JSON or Markdown for manual upload

### Title and Thumbnail Lab

- AI-generated title variants with clickbait-risk scoring and promise-alignment checks
- Human selection of preferred title, synced to publishing package
- AI-generated thumbnail visual briefs with composition, emotion, text overlay, and contrast guidance
- Human selection of preferred thumbnail concept, synced to publishing package

### Visual Plan Builder (MVP tier)

- AI-generated scene-by-scene visual plan from approved script
- Each scene includes: visual type, narration excerpt, purpose, asset notes, risk notes, filler-risk score
- Human review and approval of visual plan
- Export for production handoff

### Voice and Audio Studio (MVP tier)

- AI-generated audio delivery brief: voice style, pace, emotional tone, pause notes, pronunciation notes, emphasis notes
- Synthetic voice disclosure enforcement: if synthetic voice is used, disclosure is required in the brief and propagates to the publishing package
- Human approval before export

### Human Approval Workflow

Explicit approval gates at every lifecycle stage:
- Script: quality score gates, banned phrase scan, hook quality check
- Compliance report: risk level gates, required fixes resolution
- Publishing package: field validation, disclosure requirements, title-script consistency checks
- Audio brief: required before export
- Visual plan: required before handoff

All approvals and overrides recorded with actor identity, timestamp, and reason.

### Manual Analytics Feedback Loop

Post-publish performance recording:
- Creator manually records YouTube performance data (views, watch time, CTR, retention)
- Performance linked to the content idea and publishing package
- Data feeds back into channel notes for future content planning

---

## MVP excludes

### Automatic mass video generation

The system does not provide any mechanism to generate multiple videos without human review of each. There is no batch generation, no scheduled content queue, and no auto-publish trigger.

### Blind auto-upload to YouTube

The system generates publishing packages for human-reviewed manual upload. YouTube API integration (when added) will require explicit human confirmation on each upload — not scheduled or automatic.

### Full YouTube Analytics API integration

The MVP analytics feedback loop is manual. Creators review their YouTube Studio data and enter relevant metrics. Full YouTube Analytics API polling and automated ingestion is a post-MVP feature.

### SaaS billing and subscription management

No payment processing, subscription tiers, trial periods, or usage-based billing. The MVP is a self-hosted open system.

### Agency management and multi-tenant isolation

Multi-tenant user management, client organisation structures, white-labelling, and agency billing are out of scope. The MVP supports a single team with role-based access control.

### Asset marketplace

No stock footage search, royalty-free asset library, or third-party asset integration. The Visual Plan Builder produces planning documents for human asset sourcing.

### Full non-linear video editor

QualityTube OS does not edit video. It plans and approves the content of a video. Post-production is handled by the creator's existing toolchain.

### Advanced TTS and voice synthesis integrations

The Audio Studio generates delivery briefs for human narrators or existing voice synthesis workflows. The MVP does not integrate with ElevenLabs, Murf, Play.ht, or similar services. Synthetic voice disclosure enforcement applies regardless of which tool is used.

### Real-time collaboration

No simultaneous multi-user editing, presence indicators, or real-time conflict resolution in the MVP.

### Public API or developer SDK

The MVP API is an internal application API, not a published developer platform.
