"""Initial schema — all QualityTube OS tables.

Revision ID: 0001
Revises:
Create Date: 2026-05-17

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Organization / Workspace ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_organizations_slug"),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("org_id", "slug", name="uq_workspaces_org_slug"),
    )
    op.create_index("ix_workspaces_org_id", "workspaces", ["org_id"])

    # --- Channel ---
    op.create_table(
        "channels",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("youtube_channel_id", sa.String(50), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("tone_notes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("banned_claims", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("content_pillars", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("audience_description", sa.Text, nullable=False, server_default=""),
        sa.Column("upload_schedule_target", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("youtube_channel_id", name="uq_channels_youtube_channel_id"),
    )
    op.create_index("ix_channels_workspace_id", "channels", ["workspace_id"])

    # --- Content Ideas ---
    op.create_table(
        "content_ideas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("channel_id", sa.String(36), sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("audience", sa.Text, nullable=False),
        sa.Column("premise", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_content_ideas_channel_id", "content_ideas", ["channel_id"])
    op.create_index("ix_content_ideas_status", "content_ideas", ["status"])

    # --- Research Briefs ---
    op.create_table(
        "research_briefs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("topic", sa.String(300), nullable=False),
        sa.Column("goals", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("references", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("key_questions", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("originality_notes", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_research_briefs_idea_id", "research_briefs", ["idea_id"])

    # --- Angles ---
    op.create_table(
        "angles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("argument", sa.Text, nullable=False),
        sa.Column("counter_narrative", sa.Text, nullable=False, server_default=""),
        sa.Column("audience_benefit", sa.Text, nullable=False, server_default=""),
        sa.Column("evidence_requirement", sa.Text, nullable=False, server_default=""),
        sa.Column("originality_score", sa.Float, nullable=True),
        sa.Column("differentiation_score", sa.Float, nullable=True),
        sa.Column("audience_value_score", sa.Float, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_angles_idea_id", "angles", ["idea_id"])
    op.create_index("ix_angles_status", "angles", ["status"])

    # --- Scripts ---
    op.create_table(
        "scripts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("angle_id", sa.String(36), nullable=False),
        sa.Column("state", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("sections", sa.JSON, nullable=False),
        sa.Column("quality_report", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_scripts_idea_id", "scripts", ["idea_id"])
    op.create_index("ix_scripts_state", "scripts", ["state"])

    op.create_table(
        "script_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("script_id", sa.String(36), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("editor_event", sa.String(100), nullable=False),
        sa.Column("script_snapshot", sa.JSON, nullable=False),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_script_versions_script_id", "script_versions", ["script_id"])

    op.create_table(
        "hook_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("script_id", sa.String(36), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("promise", sa.Text, nullable=False),
        sa.Column("curiosity_gap", sa.Text, nullable=False),
        sa.Column("risk_level", sa.Integer, nullable=False),
        sa.Column("score", sa.Float, nullable=False),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("selected", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_hook_variants_script_id", "hook_variants", ["script_id"])

    op.create_table(
        "retention_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("script_id", sa.String(36), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weak_intro_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("slow_context_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("payoff_delay_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("repeated_sentence_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("generic_section_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("unclear_promise_warning", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("section_map", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("recommendations", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("timestamps", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_retention_reviews_script_id", "retention_reviews", ["script_id"])

    # --- Visual Plans / Scenes ---
    op.create_table(
        "visual_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("script_id", sa.String(36), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approval_state", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("script_id", name="uq_visual_plans_script_id"),
    )
    op.create_index("ix_visual_plans_script_id", "visual_plans", ["script_id"])

    op.create_table(
        "visual_scenes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("plan_id", sa.String(36), sa.ForeignKey("visual_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scene_number", sa.Integer, nullable=False),
        sa.Column("narration_excerpt", sa.Text, nullable=False),
        sa.Column("visual_type", sa.String(40), nullable=False),
        sa.Column("visual_description", sa.Text, nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("asset_notes", sa.Text, nullable=True),
        sa.Column("risk_notes", sa.Text, nullable=True),
        sa.Column("filler_risk_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("scene_approval_state", sa.String(30), nullable=False, server_default="draft"),
    )
    op.create_index("ix_visual_scenes_plan_id", "visual_scenes", ["plan_id"])

    # --- Audio Briefs ---
    op.create_table(
        "audio_briefs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("script_id", sa.String(36), sa.ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("voice_style", sa.String(40), nullable=False),
        sa.Column("pace_wpm", sa.Integer, nullable=False),
        sa.Column("emotional_tone", sa.Text, nullable=False),
        sa.Column("pause_notes", sa.Text, nullable=False),
        sa.Column("pronunciation_notes", sa.Text, nullable=False),
        sa.Column("emphasis_notes", sa.Text, nullable=False),
        sa.Column("synthetic_voice_used", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("disclosure_required", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("disclosure_notes", sa.Text, nullable=True),
        sa.Column("export_text", sa.Text, nullable=False),
        sa.Column("approval_state", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audio_briefs_script_id", "audio_briefs", ["script_id"])

    # --- Title / Thumbnail Lab ---
    op.create_table(
        "title_variants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title_text", sa.String(200), nullable=False),
        sa.Column("selected", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("clarity_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("curiosity_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("truthfulness_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("promise_match_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("clickbait_risk", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("overall_title_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("warnings", sa.Text, nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_title_variants_idea_id", "title_variants", ["idea_id"])

    op.create_table(
        "thumbnail_concepts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("selected", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("main_object", sa.String(150), nullable=False),
        sa.Column("emotion", sa.String(120), nullable=False),
        sa.Column("composition", sa.Text, nullable=False),
        sa.Column("text_overlay", sa.String(120), nullable=False),
        sa.Column("visual_contrast", sa.Text, nullable=False),
        sa.Column("mobile_readability_notes", sa.Text, nullable=False),
        sa.Column("avoid", sa.Text, nullable=False),
        sa.Column("score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_thumbnail_concepts_idea_id", "thumbnail_concepts", ["idea_id"])

    # --- Compliance ---
    op.create_table(
        "compliance_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reused_content_risk", sa.String(10), nullable=False),
        sa.Column("repetitive_content_risk", sa.String(10), nullable=False),
        sa.Column("mass_production_risk", sa.String(10), nullable=False),
        sa.Column("synthetic_content_disclosure_required", sa.Boolean, nullable=False),
        sa.Column("copyright_risk", sa.String(10), nullable=False),
        sa.Column("misleading_claims_risk", sa.String(10), nullable=False),
        sa.Column("sensitive_topic_risk", sa.String(10), nullable=False),
        sa.Column("clickbait_risk", sa.String(10), nullable=False),
        sa.Column("originality_evidence", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("human_contribution_evidence", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("overall_risk", sa.String(10), nullable=False),
        sa.Column("recommendation", sa.String(30), nullable=False),
        sa.Column("required_fixes", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("reviewer_notes", sa.Text, nullable=False, server_default=""),
        sa.Column("reviewer_source", sa.String(30), nullable=False),
        sa.Column("approval_state", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("override_reason", sa.Text, nullable=True),
        sa.Column("override_actor", sa.String(200), nullable=True),
        sa.Column("override_recommendation", sa.String(30), nullable=True),
        sa.Column("override_overall_risk", sa.String(10), nullable=True),
        sa.Column("is_manually_overridden", sa.Boolean, nullable=False, server_default="0"),
        sa.Column("override_audit_log", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_compliance_reports_idea_id", "compliance_reports", ["idea_id"])

    # --- Publishing ---
    op.create_table(
        "publishing_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("compliance_report_id", sa.String(36), sa.ForeignKey("compliance_reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(95), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("tags", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("chapters", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("pinned_comment", sa.Text, nullable=True),
        sa.Column("thumbnail_brief", sa.Text, nullable=False),
        sa.Column("disclosure_notes", sa.Text, nullable=True),
        sa.Column("source_notes", sa.Text, nullable=True),
        sa.Column("upload_checklist", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idea_id", name="uq_publishing_packages_idea_id"),
    )
    op.create_index("ix_publishing_packages_idea_id", "publishing_packages", ["idea_id"])
    op.create_index("ix_publishing_packages_compliance_report_id", "publishing_packages", ["compliance_report_id"])

    op.create_table(
        "publishing_package_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("publishing_packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False),
        sa.Column("editor_event", sa.String(100), nullable=False),
        sa.Column("package_snapshot", sa.JSON, nullable=False),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_publishing_package_revisions_package_id", "publishing_package_revisions", ["package_id"])

    # --- Workflow ---
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("current_stage", sa.String(40), nullable=False, server_default="idea_captured"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idea_id", name="uq_workflow_runs_idea_id"),
    )
    op.create_index("ix_workflow_runs_idea_id", "workflow_runs", ["idea_id"])
    op.create_index("ix_workflow_runs_current_stage", "workflow_runs", ["current_stage"])
    op.create_index("ix_workflow_runs_status", "workflow_runs", ["status"])

    op.create_table(
        "workflow_steps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("actor", sa.String(200), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("started_at", sa.String(50), nullable=True),
        sa.Column("completed_at", sa.String(50), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_workflow_steps_run_id", "workflow_steps", ["run_id"])

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("action", sa.String(30), nullable=False),
        sa.Column("actor", sa.String(200), nullable=False),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("previous_state", sa.String(30), nullable=False),
        sa.Column("new_state", sa.String(30), nullable=False),
        sa.Column("created_at", sa.String(50), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_approvals_entity_type", "approvals", ["entity_type"])
    op.create_index("ix_approvals_entity_id", "approvals", ["entity_id"])

    # --- Analytics ---
    op.create_table(
        "analytics_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("publishing_package_id", sa.String(36), sa.ForeignKey("publishing_packages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("views", sa.String(20), nullable=True),
        sa.Column("watch_time_hours", sa.Float, nullable=True),
        sa.Column("avg_view_duration_seconds", sa.Float, nullable=True),
        sa.Column("avg_view_percentage", sa.Float, nullable=True),
        sa.Column("click_through_rate", sa.Float, nullable=True),
        sa.Column("impressions", sa.String(20), nullable=True),
        sa.Column("likes", sa.String(20), nullable=True),
        sa.Column("comments", sa.String(20), nullable=True),
        sa.Column("shares", sa.String(20), nullable=True),
        sa.Column("subscribers_gained", sa.String(20), nullable=True),
        sa.Column("estimated_revenue_usd", sa.Float, nullable=True),
        sa.Column("rpm", sa.Float, nullable=True),
        sa.Column("retention_curve", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("metric_snapshot", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("report_period_start", sa.String(20), nullable=True),
        sa.Column("report_period_end", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_analytics_reports_idea_id", "analytics_reports", ["idea_id"])
    op.create_index("ix_analytics_reports_publishing_package_id", "analytics_reports", ["publishing_package_id"])

    op.create_table(
        "monetization_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("yt_partner_eligible", sa.String(5), nullable=True),
        sa.Column("revenue_streams", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("primary_revenue_type", sa.String(50), nullable=True),
        sa.Column("sponsor_notes", sa.Text, nullable=True),
        sa.Column("affiliate_links", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("disclosure_required", sa.String(5), nullable=False, server_default="false"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idea_id", name="uq_monetization_plans_idea_id"),
    )
    op.create_index("ix_monetization_plans_idea_id", "monetization_plans", ["idea_id"])
    op.create_index("ix_monetization_plans_status", "monetization_plans", ["status"])

    # --- LLM Telemetry ---
    op.create_table(
        "llm_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("response", sa.Text, nullable=False),
        sa.Column("prompt_chars", sa.Integer, nullable=False),
        sa.Column("response_chars", sa.Integer, nullable=False),
        sa.Column("prompt_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer, nullable=False, server_default="0"),
        sa.Column("correlation_id", sa.String(100), nullable=False),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_llm_calls_provider", "llm_calls", ["provider"])
    op.create_index("ix_llm_calls_model", "llm_calls", ["model"])
    op.create_index("ix_llm_calls_operation", "llm_calls", ["operation"])
    op.create_index("ix_llm_calls_correlation_id", "llm_calls", ["correlation_id"])
    op.create_index("ix_llm_calls_idea_id", "llm_calls", ["idea_id"])

    op.create_table(
        "youtube_quota_ledger",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("quota_cost", sa.Integer, nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=True),
        sa.Column("http_status", sa.Integer, nullable=True),
        sa.Column("error_reason", sa.String(100), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("idea_id", sa.String(36), sa.ForeignKey("content_ideas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("ix_youtube_quota_ledger_operation", "youtube_quota_ledger", ["operation"])
    op.create_index("ix_youtube_quota_ledger_correlation_id", "youtube_quota_ledger", ["correlation_id"])
    op.create_index("ix_youtube_quota_ledger_idea_id", "youtube_quota_ledger", ["idea_id"])
    op.create_index("ix_youtube_quota_ledger_created_at", "youtube_quota_ledger", ["created_at"])


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("youtube_quota_ledger")
    op.drop_table("llm_calls")
    op.drop_table("monetization_plans")
    op.drop_table("analytics_reports")
    op.drop_table("approvals")
    op.drop_table("workflow_steps")
    op.drop_table("workflow_runs")
    op.drop_table("publishing_package_revisions")
    op.drop_table("publishing_packages")
    op.drop_table("compliance_reports")
    op.drop_table("thumbnail_concepts")
    op.drop_table("title_variants")
    op.drop_table("audio_briefs")
    op.drop_table("visual_scenes")
    op.drop_table("visual_plans")
    op.drop_table("retention_reviews")
    op.drop_table("hook_variants")
    op.drop_table("script_versions")
    op.drop_table("scripts")
    op.drop_table("angles")
    op.drop_table("research_briefs")
    op.drop_table("content_ideas")
    op.drop_table("channels")
    op.drop_table("workspaces")
    op.drop_table("organizations")
