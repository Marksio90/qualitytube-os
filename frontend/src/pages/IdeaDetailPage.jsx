import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data?.detail?.message || data?.message || "Request failed");
  }
  return data;
}

const ideaApi = {
  loadCompliance: (ideaId) => api(`/api/v1/ideas/${ideaId}/compliance/latest`),
  loadPublishing: (ideaId) => api(`/api/v1/ideas/${ideaId}/publishing`),
  generateTitles: (ideaId) => api(`/api/v1/ideas/${ideaId}/titles/generate`, { method: "POST", body: JSON.stringify({ angle_status: "approved" }) }),
  listTitles: (ideaId) => api(`/api/v1/ideas/${ideaId}/titles`),
  selectTitle: (titleId) => api(`/api/v1/titles/${titleId}/select`, { method: "POST" }),
  generateThumbnails: (ideaId, titles) => api(`/api/v1/ideas/${ideaId}/thumbnails/generate-briefs`, { method: "POST", body: JSON.stringify({ angle_status: "approved", titles }) }),
  listThumbnails: (ideaId) => api(`/api/v1/ideas/${ideaId}/thumbnails`),
  selectThumbnail: (thumbnailId) => api(`/api/v1/thumbnails/${thumbnailId}/select`, { method: "POST" }),
};

const RISK_FIELDS = ["reused_content_risk", "repetitive_content_risk", "mass_production_risk", "copyright_risk", "misleading_claims_risk", "sensitive_topic_risk", "clickbait_risk"];

const emptyPublishingForm = { title: "", description: "", tags: "", chapters: "", pinned_comment: "", thumbnail_brief: "", disclosure_notes: "", checklist: "" };
const emptyLabState = { loading: false, error: "", success: "", items: [] };

export function IdeaDetailPage() {
  const { ideaId = "" } = useParams();
  const [activeTab, setActiveTab] = useState("compliance");
  const [state, setState] = useState({ loading: true, error: "", report: null });
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [publishing, setPublishing] = useState({ loading: true, error: "", success: "", data: null });
  const [publishingForm, setPublishingForm] = useState(emptyPublishingForm);
  const [publishingBusy, setPublishingBusy] = useState(false);
  const [validation, setValidation] = useState({ warnings: [], errors: [], compliance_blockers: [] });

  const [titlesState, setTitlesState] = useState({ ...emptyLabState, loading: true });
  const [thumbsState, setThumbsState] = useState({ ...emptyLabState, loading: true });

  const refreshPublishing = async () => { await loadPublishing(); };

  const loadCompliance = async () => {
    setState({ loading: true, error: "", report: null });
    try {
      const data = await ideaApi.loadCompliance(ideaId);
      setState({ loading: false, error: "", report: data.report || null });
    } catch (e) {
      if (e.message.includes("no compliance report")) setState({ loading: false, error: "", report: null });
      else setState({ loading: false, error: e.message, report: null });
    }
  };

  const loadPublishing = async () => {
    setPublishing({ loading: true, error: "", success: "", data: null });
    try {
      const data = await ideaApi.loadPublishing(ideaId);
      const pkg = data.package || null;
      setPublishing({ loading: false, error: "", success: "", data: pkg });
      if (pkg) {
        setPublishingForm({ ...emptyPublishingForm, ...pkg });
        setValidation(pkg.validation || { warnings: [], errors: [], compliance_blockers: [] });
      }
    } catch (e) {
      if (e.message.includes("not found") || e.message.includes("no publishing package")) setPublishing({ loading: false, error: "", success: "", data: null });
      else setPublishing({ loading: false, error: e.message, success: "", data: null });
    }
  };

  const loadLabOptions = async () => {
    setTitlesState((curr) => ({ ...curr, loading: true, error: "" }));
    setThumbsState((curr) => ({ ...curr, loading: true, error: "" }));
    try { const t = await ideaApi.listTitles(ideaId); setTitlesState({ loading: false, error: "", success: "", items: t.titles || [] }); }
    catch (e) { setTitlesState({ loading: false, error: e.message, success: "", items: [] }); }
    try { const t = await ideaApi.listThumbnails(ideaId); setThumbsState({ loading: false, error: "", success: "", items: t.thumbnails || [] }); }
    catch (e) { setThumbsState({ loading: false, error: e.message, success: "", items: [] }); }
  };

  useEffect(() => { loadCompliance(); loadPublishing(); loadLabOptions(); }, [ideaId]);

  const blocked = useMemo(() => { const report = state.report; if (!report) return true; return report.recommendation === "do_not_publish" || report.overall_risk === "high" || (report.required_fixes || []).length > 0; }, [state.report]);
  const approvalBlocked = blocked || validation.errors.length > 0 || validation.compliance_blockers.length > 0;

  async function runApproval() { if (!state.report) return; setActionBusy(true); setActionError(""); try { await api(`/api/v1/compliance/${state.report.id}/approve`, { method: "POST", body: JSON.stringify({ approver: "idea-detail-user" }) }); await loadCompliance(); } catch (e) { setActionError(e.message); } finally { setActionBusy(false); } }

  async function runOverride() { if (!state.report || !overrideReason.trim()) { setActionError("Override reason is required."); return; } setActionBusy(true); setActionError(""); try { await api(`/api/v1/compliance/${state.report.id}/override`, { method: "POST", body: JSON.stringify({ reason: overrideReason, approver: "idea-detail-user", outcome_recommendation: "approve_with_fixes", outcome_overall_risk: "medium" }) }); await loadCompliance(); } catch (e) { setActionError(e.message); } finally { setActionBusy(false); } }

  async function publishingAction(action, message) { setPublishingBusy(true); setPublishing((curr) => ({ ...curr, error: "", success: "" })); try { const data = await action(); if (data?.package) setPublishingForm({ ...emptyPublishingForm, ...data.package }); if (data?.validation) setValidation(data.validation); setPublishing((curr) => ({ ...curr, success: message, data: data?.package || curr.data })); } catch (e) { setPublishing((curr) => ({ ...curr, error: e.message })); } finally { setPublishingBusy(false); } }

  const runTitleAction = async (action, success) => { setTitlesState((c) => ({ ...c, loading: true, error: "", success: "" })); try { const data = await action(); setTitlesState({ loading: false, error: "", success, items: data.titles || [] }); } catch (e) { setTitlesState((c) => ({ ...c, loading: false, error: `Title lab action failed: ${e.message}` })); } };
  const runThumbAction = async (action, success) => { setThumbsState((c) => ({ ...c, loading: true, error: "", success: "" })); try { const data = await action(); setThumbsState({ loading: false, error: "", success, items: data.thumbnails || [] }); } catch (e) { setThumbsState((c) => ({ ...c, loading: false, error: `Thumbnail lab action failed: ${e.message}` })); } };

  const updateField = (key) => (e) => setPublishingForm((curr) => ({ ...curr, [key]: e.target.value }));

  return <main style={{ padding: 16 }}><h1>Idea Detail</h1><p>Idea ID: <strong>{ideaId}</strong></p><div style={{ display: "flex", gap: 8 }}><button aria-pressed={activeTab === "compliance"} onClick={() => setActiveTab("compliance")}>Compliance</button><button aria-pressed={activeTab === "publishing"} onClick={() => setActiveTab("publishing")}>Publishing</button><button aria-pressed={activeTab === "title-thumbnail-lab"} onClick={() => setActiveTab("title-thumbnail-lab")}>Title & Thumbnail Lab</button></div>
    {activeTab === "compliance" && <section><h2>Compliance</h2>{state.loading && <p>Loading compliance report…</p>}{state.error && <p role="alert">Failed to load compliance: {state.error}</p>}{!state.loading && !state.error && !state.report && <p>No compliance report available yet.</p>}{!state.loading && state.report && <><p>Recommendation: <strong>{state.report.recommendation}</strong></p><p>Overall risk: <strong>{state.report.overall_risk}</strong></p><p>Synthetic disclosure required: <strong>{state.report.synthetic_content_disclosure_required ? "Required" : "Not required"}</strong></p><h3>Risk cards</h3><div>{RISK_FIELDS.map((key) => <article key={key}><strong>{key}:</strong> {state.report[key]}</article>)}</div><h3>Required fixes</h3>{(state.report.required_fixes || []).length === 0 ? <p>None</p> : <ul>{state.report.required_fixes.map((fix) => <li key={fix}>{fix} — <strong>Unresolved</strong></li>)}</ul>}<h3>Publish readiness</h3><p>{blocked ? "Blocked: compliance requirements are not fully satisfied." : "Ready: compliance checks cleared for publish."}</p>{actionError && <p role="alert">Compliance action failed: {actionError}</p>}<button disabled={actionBusy} onClick={runApproval}>{actionBusy ? "Working…" : "Approve compliance"}</button><div><label htmlFor="override-reason">Override reason (required)</label><input id="override-reason" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} /><button disabled={actionBusy} onClick={runOverride}>Override compliance</button></div></>}</section>}
    {activeTab === "publishing" && <section><h2>Publishing</h2>{publishing.loading && <p>Loading publishing package…</p>}{publishing.error && <p role="alert">Publishing error: {publishing.error}</p>}{publishing.success && <p>{publishing.success}</p>}{!publishing.loading && !publishing.error && !publishing.data && <><p>No publishing package available yet.</p><button disabled={publishingBusy} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing/generate`, { method: "POST" }), "Publishing package generated.")}>Generate package</button></>}{!publishing.loading && (publishing.data || publishing.success) && <><label>Title<input value={publishingForm.title} onChange={updateField("title")} /></label><label>Description<textarea value={publishingForm.description} onChange={updateField("description")} /></label><label>Tags<input value={publishingForm.tags} onChange={updateField("tags")} /></label><label>Chapters<textarea value={publishingForm.chapters} onChange={updateField("chapters")} /></label><label>Pinned comment<textarea value={publishingForm.pinned_comment} onChange={updateField("pinned_comment")} /></label><label>Thumbnail brief<textarea value={publishingForm.thumbnail_brief} onChange={updateField("thumbnail_brief")} /></label><label>Disclosure notes<textarea value={publishingForm.disclosure_notes} onChange={updateField("disclosure_notes")} /></label><label>Checklist<textarea value={publishingForm.checklist} onChange={updateField("checklist")} /></label><div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}><button disabled={publishingBusy} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing`, { method: "PATCH", body: JSON.stringify(publishingForm) }), "Publishing edits saved.")}>Save edits</button><button disabled={publishingBusy} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing/validate`, { method: "POST", body: JSON.stringify(publishingForm) }), "Validation completed.")}>Validate</button><button disabled={publishingBusy || approvalBlocked} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing/approve`, { method: "POST" }), "Publishing package approved.")}>Approve publish package</button><button disabled={publishingBusy} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing/export?format=markdown`), "Markdown export ready.")}>Export markdown</button><button disabled={publishingBusy} onClick={() => publishingAction(() => api(`/api/v1/ideas/${ideaId}/publishing/export?format=json`), "JSON export ready.")}>Export JSON</button></div><h3>Validation</h3>{validation.warnings.length > 0 && <ul>{validation.warnings.map((w) => <li key={w}>⚠️ {w}</li>)}</ul>}{validation.errors.length > 0 && <ul>{validation.errors.map((er) => <li key={er} role="alert">❌ {er}</li>)}</ul>}{validation.compliance_blockers.length > 0 && <ul>{validation.compliance_blockers.map((b) => <li key={b} role="alert">🚫 {b}</li>)}</ul>}</>}</section>}

    {activeTab === "title-thumbnail-lab" && <section>
      <h2>Title & Thumbnail Lab</h2>
      <div>
        <h3>Titles</h3>
        <button onClick={() => runTitleAction(() => ideaApi.generateTitles(ideaId), "Title variants generated.")}>Generate title variants</button>
        {titlesState.loading && <p>Loading title variants…</p>}
        {titlesState.error && <p role="alert">{titlesState.error}</p>}
        {!titlesState.loading && !titlesState.error && titlesState.items.length === 0 && <p>No title variants yet.</p>}
        {titlesState.success && <p>{titlesState.success}</p>}
        {titlesState.items.map((title) => <article key={title.id}><p><strong>{title.title_text}</strong> {title.selected ? "(Selected)" : ""}</p><p>clarity {title.clarity_score} • curiosity {title.curiosity_score} • truthfulness {title.truthfulness_score} • promise match {title.promise_match_score} • overall {title.overall_title_score} • clickbait risk {title.clickbait_risk}</p><button disabled={title.selected} onClick={async () => { await runTitleAction(async () => { await ideaApi.selectTitle(title.id); const listed = await ideaApi.listTitles(ideaId); await refreshPublishing(); return listed; }, "Final title selected and synced to publishing package."); }}>Select final title</button></article>)}
      </div>
      <div>
        <h3>Thumbnails</h3>
        <button onClick={() => runThumbAction(() => ideaApi.generateThumbnails(ideaId, titlesState.items.filter((t) => t.selected).map((t) => t.title_text)), "Thumbnail briefs generated.")}>Generate thumbnail briefs</button>
        {thumbsState.loading && <p>Loading thumbnail briefs…</p>}
        {thumbsState.error && <p role="alert">{thumbsState.error}</p>}
        {!thumbsState.loading && !thumbsState.error && thumbsState.items.length === 0 && <p>No thumbnail concepts yet.</p>}
        {thumbsState.success && <p>{thumbsState.success}</p>}
        {thumbsState.items.map((thumb) => <article key={thumb.id}><p><strong>{thumb.main_object}</strong> {thumb.selected ? "(Selected)" : ""}</p><p>Composition: {thumb.composition}</p><p>Text overlay: {thumb.text_overlay}</p><p>Mobile readability: {thumb.mobile_readability_notes}</p><p>Avoid: {thumb.avoid}</p><button disabled={thumb.selected} onClick={async () => { await runThumbAction(async () => { await ideaApi.selectThumbnail(thumb.id); const listed = await ideaApi.listThumbnails(ideaId); await refreshPublishing(); return listed; }, "Final thumbnail concept selected and synced to publishing package."); }}>Select final thumbnail concept</button></article>)}
      </div>
      {!publishing.loading && publishing.data && <div><h3>Synced publishing package values</h3><p><strong>Title:</strong> {publishingForm.title || "—"}</p><p><strong>Thumbnail brief:</strong> {publishingForm.thumbnail_brief || "—"}</p></div>}
    </section>}
  </main>;
}
