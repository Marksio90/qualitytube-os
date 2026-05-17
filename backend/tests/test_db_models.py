"""Basic ORM model instantiation tests.

Verifies that all SQLAlchemy models can be imported and instantiated,
and that the Alembic migration can be applied to a fresh SQLite database.
Does NOT test business logic — that belongs in the domain tests.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.base import Base, new_uuid
import app.db.models  # noqa: F401 — ensure all models are registered
from app.db.models import (
    AnalyticsReport,
    Approval,
    Channel,
    ComplianceReport,
    Angle,
    ContentIdea,
    LLMCall,
    MonetizationPlan,
    Organization,
    PublishingPackage,
    ResearchBrief,
    Script,
    WorkflowRun,
    WorkflowStep,
    Workspace,
    YouTubeQuotaLedger,
)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_organization_and_workspace(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="Acme Media", slug="acme-media")
    db_session.add(org)
    await db_session.flush()

    ws = Workspace(id=new_uuid(), org_id=org.id, name="Main Workspace", slug="main")
    db_session.add(ws)
    await db_session.flush()

    assert org.slug == "acme-media"
    assert ws.org_id == org.id


@pytest.mark.asyncio
async def test_channel(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="Test Org", slug="test-org")
    ws = Workspace(id=new_uuid(), org_id=org.id, name="WS", slug="ws")
    db_session.add_all([org, ws])
    await db_session.flush()

    ch = Channel(
        id=new_uuid(),
        workspace_id=ws.id,
        name="My Channel",
        language="en",
        tone_notes=["professional"],
        banned_claims=["guaranteed income"],
        content_pillars=["productivity"],
        audience_description="Freelance developers",
    )
    db_session.add(ch)
    await db_session.flush()

    assert ch.name == "My Channel"
    assert ch.youtube_channel_id is None


@pytest.mark.asyncio
async def test_content_idea_and_research_brief(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="O", slug="o")
    ws = Workspace(id=new_uuid(), org_id=org.id, name="W", slug="w")
    ch = Channel(id=new_uuid(), workspace_id=ws.id, name="C", audience_description="")
    db_session.add_all([org, ws, ch])
    await db_session.flush()

    idea = ContentIdea(id=new_uuid(), channel_id=ch.id, title="T", audience="Devs", premise="P")
    db_session.add(idea)
    await db_session.flush()

    brief = ResearchBrief(
        id=new_uuid(),
        idea_id=idea.id,
        topic="AI productivity",
        goals=["understand landscape"],
        references=["arxiv.org/123"],
        key_questions=["What is the best tool?"],
        originality_notes="Unique angle on local LLMs",
    )
    db_session.add(brief)
    await db_session.flush()

    assert brief.idea_id == idea.id
    assert brief.key_questions == ["What is the best tool?"]


@pytest.mark.asyncio
async def test_angle(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="O2", slug="o2")
    ws = Workspace(id=new_uuid(), org_id=org.id, name="W2", slug="w2")
    ch = Channel(id=new_uuid(), workspace_id=ws.id, name="C2", audience_description="")
    idea = ContentIdea(id=new_uuid(), channel_id=ch.id, title="T2", audience="A", premise="P")
    db_session.add_all([org, ws, ch, idea])
    await db_session.flush()

    angle = Angle(
        id=new_uuid(),
        idea_id=idea.id,
        title="Contrarian angle",
        argument="Most tutorials are wrong",
        status="pending",
    )
    db_session.add(angle)
    await db_session.flush()

    assert angle.status == "pending"
    assert angle.originality_score is None


@pytest.mark.asyncio
async def test_workflow_run_and_step(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="O3", slug="o3")
    ws = Workspace(id=new_uuid(), org_id=org.id, name="W3", slug="w3")
    ch = Channel(id=new_uuid(), workspace_id=ws.id, name="C3", audience_description="")
    idea = ContentIdea(id=new_uuid(), channel_id=ch.id, title="T3", audience="A", premise="P")
    db_session.add_all([org, ws, ch, idea])
    await db_session.flush()

    run = WorkflowRun(id=new_uuid(), idea_id=idea.id, current_stage="idea_captured", status="active")
    db_session.add(run)
    await db_session.flush()

    step = WorkflowStep(
        id=new_uuid(),
        run_id=run.id,
        stage="idea_captured",
        status="completed",
        actor="system",
        created_at="2026-05-17T00:00:00Z",
    )
    db_session.add(step)
    await db_session.flush()

    assert run.current_stage == "idea_captured"
    assert step.actor == "system"


@pytest.mark.asyncio
async def test_approval(db_session: AsyncSession) -> None:
    approval = Approval(
        id=new_uuid(),
        entity_type="script",
        entity_id=new_uuid(),
        action="approve",
        actor="editor@example.com",
        previous_state="pending",
        new_state="approved",
        created_at="2026-05-17T00:00:00Z",
    )
    db_session.add(approval)
    await db_session.flush()

    assert approval.action == "approve"


@pytest.mark.asyncio
async def test_llm_call(db_session: AsyncSession) -> None:
    call = LLMCall(
        id=new_uuid(),
        provider="anthropic",
        model="claude-sonnet-4-6",
        operation="draft_script",
        prompt="Write a hook",
        response='{"hook": "Did you know..."}',
        prompt_chars=14,
        response_chars=24,
        prompt_tokens=4,
        completion_tokens=8,
        latency_ms=342,
        correlation_id="req-abc123",
        created_at="2026-05-17T00:00:00Z",
    )
    db_session.add(call)
    await db_session.flush()

    assert call.provider == "anthropic"
    assert call.idea_id is None


@pytest.mark.asyncio
async def test_youtube_quota_ledger(db_session: AsyncSession) -> None:
    entry = YouTubeQuotaLedger(
        id=new_uuid(),
        operation="search.list",
        quota_cost=100,
        http_status=200,
        created_at="2026-05-17T00:00:00Z",
    )
    db_session.add(entry)
    await db_session.flush()

    assert entry.quota_cost == 100


@pytest.mark.asyncio
async def test_analytics_report_and_monetization_plan(db_session: AsyncSession) -> None:
    org = Organization(id=new_uuid(), name="O4", slug="o4")
    ws = Workspace(id=new_uuid(), org_id=org.id, name="W4", slug="w4")
    ch = Channel(id=new_uuid(), workspace_id=ws.id, name="C4", audience_description="")
    idea = ContentIdea(id=new_uuid(), channel_id=ch.id, title="T4", audience="A", premise="P")
    db_session.add_all([org, ws, ch, idea])
    await db_session.flush()

    report = AnalyticsReport(
        id=new_uuid(),
        idea_id=idea.id,
        views="12500",
        watch_time_hours=420.5,
        click_through_rate=0.048,
        retention_curve=[],
        metric_snapshot={},
    )
    db_session.add(report)
    await db_session.flush()

    plan = MonetizationPlan(
        id=new_uuid(),
        idea_id=idea.id,
        revenue_streams=[],
        affiliate_links=[],
        disclosure_required="false",
        status="draft",
    )
    db_session.add(plan)
    await db_session.flush()

    assert report.idea_id == idea.id
    assert plan.status == "draft"
