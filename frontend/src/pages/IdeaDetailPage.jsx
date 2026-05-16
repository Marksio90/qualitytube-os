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

const RISK_FIELDS = [
  "reused_content_risk",
  "repetitive_content_risk",
  "mass_production_risk",
  "copyright_risk",
  "misleading_claims_risk",
  "sensitive_topic_risk",
  "clickbait_risk",
];

export function IdeaDetailPage() {
  const { ideaId = "" } = useParams();
  const [activeTab, setActiveTab] = useState("compliance");
  const [state, setState] = useState({ loading: true, error: "", report: null });
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState("");
  const [overrideReason, setOverrideReason] = useState("");

  const loadCompliance = async () => {
    setState({ loading: true, error: "", report: null });
    try {
      const data = await api(`/api/v1/ideas/${ideaId}/compliance/latest`);
      setState({ loading: false, error: "", report: data.report || null });
    } catch (e) {
      if (e.message.includes("no compliance report")) {
        setState({ loading: false, error: "", report: null });
      } else {
        setState({ loading: false, error: e.message, report: null });
      }
    }
  };

  useEffect(() => {
    loadCompliance();
  }, [ideaId]);

  const blocked = useMemo(() => {
    const report = state.report;
    if (!report) return true;
    return report.recommendation === "do_not_publish" || report.overall_risk === "high" || (report.required_fixes || []).length > 0;
  }, [state.report]);

  async function runApproval() {
    if (!state.report) return;
    setActionBusy(true);
    setActionError("");
    try {
      await api(`/api/v1/compliance/${state.report.id}/approve`, { method: "POST", body: JSON.stringify({ approver: "idea-detail-user" }) });
      await loadCompliance();
    } catch (e) {
      setActionError(e.message);
    } finally { setActionBusy(false); }
  }

  async function runOverride() {
    if (!state.report || !overrideReason.trim()) {
      setActionError("Override reason is required.");
      return;
    }
    setActionBusy(true);
    setActionError("");
    try {
      await api(`/api/v1/compliance/${state.report.id}/override`, {
        method: "POST",
        body: JSON.stringify({
          reason: overrideReason,
          approver: "idea-detail-user",
          outcome_recommendation: "approve_with_fixes",
          outcome_overall_risk: "medium",
        }),
      });
      await loadCompliance();
    } catch (e) {
      setActionError(e.message);
    } finally { setActionBusy(false); }
  }

  return <main style={{ padding: 16 }}>
    <h1>Idea Detail</h1>
    <p>Idea ID: <strong>{ideaId}</strong></p>
    <div style={{ display: "flex", gap: 8 }}>
      <button aria-pressed={activeTab === "compliance"} onClick={() => setActiveTab("compliance")}>Compliance</button>
    </div>
    {activeTab === "compliance" && <section>
      <h2>Compliance</h2>
      {state.loading && <p>Loading compliance report…</p>}
      {state.error && <p role="alert">Failed to load compliance: {state.error}</p>}
      {!state.loading && !state.error && !state.report && <p>No compliance report available yet.</p>}
      {!state.loading && state.report && <>
        <p>Recommendation: <strong>{state.report.recommendation}</strong></p>
        <p>Overall risk: <strong>{state.report.overall_risk}</strong></p>
        <p>Synthetic disclosure required: <strong>{state.report.synthetic_content_disclosure_required ? "Required" : "Not required"}</strong></p>
        <h3>Risk cards</h3>
        <div>{RISK_FIELDS.map((key) => <article key={key}><strong>{key}:</strong> {state.report[key]}</article>)}</div>
        <h3>Required fixes</h3>
        {(state.report.required_fixes || []).length === 0 ? <p>None</p> : <ul>{state.report.required_fixes.map((fix) => <li key={fix}>{fix} — <strong>Unresolved</strong></li>)}</ul>}
        <h3>Publish readiness</h3>
        <p>{blocked ? "Blocked: compliance requirements are not fully satisfied." : "Ready: compliance checks cleared for publish."}</p>
        {actionError && <p role="alert">Compliance action failed: {actionError}</p>}
        <button disabled={actionBusy} onClick={runApproval}>{actionBusy ? "Working…" : "Approve compliance"}</button>
        <div>
          <label htmlFor="override-reason">Override reason (required)</label>
          <input id="override-reason" value={overrideReason} onChange={(e) => setOverrideReason(e.target.value)} />
          <button disabled={actionBusy} onClick={runOverride}>Override compliance</button>
        </div>
      </>}
    </section>}
  </main>;
}
