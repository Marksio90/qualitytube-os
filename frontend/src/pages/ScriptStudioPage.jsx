import { useEffect, useMemo, useState } from "react";
import { VisualPlanTab } from "../components/VisualPlanTab";

const DEFAULT_IDEA_ID = "idea-studio-demo";
const DEFAULT_ANGLE_ID = "angle-studio-demo";

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

export function ScriptStudioPage() {
  const [script, setScript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [revisionData, setRevisionData] = useState({ loading: false, error: "", items: [] });
  const [selectedRevision, setSelectedRevision] = useState("");
  const [activeTab, setActiveTab] = useState("editor");
  const [hooksData, setHooksData] = useState({ loading: false, error: "", items: [], selectedId: "" });
  const [retentionData, setRetentionData] = useState({ loading: false, error: "", analysis: null });

  const warnings = useMemo(() => {
    if (!script) return [];
    const list = [];
    const content = script.sections.map((s) => s.content.toLowerCase()).join(" ");
    ["guaranteed viral", "zero effort success"].forEach((phrase) => {
      if (content.includes(phrase)) list.push(`Banned phrase detected: \"${phrase}\"`);
    });
    if (!script.quality_report) list.push("Script has not been scored.");
    if (script.quality_report && script.quality_report.overall_script_score < 7) list.push("Overall quality score is below the approval gate (7.0).");
    if (script.quality_report && script.quality_report.hook_score < 7) list.push("Hook score is below the approval gate (7.0).");
    return list;
  }, [script]);

  async function ensureScript() {
    setLoading(true);
    setError("");
    try {
      const existing = await api(`/api/v1/ideas/${DEFAULT_IDEA_ID}/scripts`);
      if (existing.scripts.length === 0) {
        const created = await api(`/api/v1/ideas/${DEFAULT_IDEA_ID}/scripts/generate-draft`, {
          method: "POST",
          body: JSON.stringify({ angle_id: DEFAULT_ANGLE_ID, angle_status: "approved" }),
        });
        setScript(created.script);
      } else {
        setScript(existing.scripts[0]);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadVersions(scriptId) {
    setRevisionData({ loading: true, error: "", items: [] });
    try {
      const data = await api(`/api/v1/scripts/${scriptId}/versions`);
      setRevisionData({ loading: false, error: "", items: data.versions });
    } catch (e) {
      setRevisionData({ loading: false, error: e.message, items: [] });
    }
  }

  useEffect(() => {
    ensureScript();
  }, []);

  useEffect(() => {
    if (script?.id) loadVersions(script.id);
  }, [script?.id]);

  async function patchSections(nextSections, event = "manual-edit") {
    setSaving(true);
    setActionError("");
    try {
      const updated = await api(`/api/v1/scripts/${script.id}`, {
        method: "PATCH",
        body: JSON.stringify({ sections: nextSections, editor_event: event }),
      });
      setScript(updated);
      await loadVersions(updated.id);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function runAction(path, body = {}) {
    setSaving(true);
    setActionError("");
    try {
      const data = await api(`/api/v1/scripts/${script.id}/${path}`, { method: "POST", body: JSON.stringify(body) });
      if (data.script) setScript(data.script);
      if (data.state) setScript((prev) => (prev ? { ...prev, state: data.state } : prev));
      await loadVersions(script.id);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function generateHooks() {
    setHooksData((prev) => ({ ...prev, loading: true, error: "" }));
    try {
      const data = await api(`/api/v1/scripts/${script.id}/hooks/generate`, { method: "POST", body: JSON.stringify({}) });
      setHooksData((prev) => ({ ...prev, loading: false, error: "", items: data.hooks || [] }));
    } catch (e) {
      setHooksData((prev) => ({ ...prev, loading: false, error: e.message, items: [] }));
    }
  }

  async function selectPrimaryHook(hookId) {
    setHooksData((prev) => ({ ...prev, loading: true, error: "" }));
    try {
      const data = await api(`/api/v1/scripts/${script.id}/hooks/select-primary`, { method: "POST", body: JSON.stringify({ hook_id: hookId }) });
      setHooksData((prev) => ({ ...prev, loading: false, error: "", selectedId: hookId, items: data.hooks || prev.items }));
      if (data.script) setScript(data.script);
    } catch (e) {
      setHooksData((prev) => ({ ...prev, loading: false, error: e.message }));
    }
  }

  async function analyzeRetention() {
    setRetentionData({ loading: true, error: "", analysis: null });
    try {
      const data = await api(`/api/v1/scripts/${script.id}/retention/analyze`, { method: "POST", body: JSON.stringify({}) });
      setRetentionData({ loading: false, error: "", analysis: data.analysis || null });
    } catch (e) {
      setRetentionData({ loading: false, error: e.message, analysis: null });
    }
  }

  if (loading) return <main><h1>Script Studio</h1><p>Loading script workspace…</p></main>;
  if (error) return <main><h1>Script Studio</h1><p role="alert">Failed to load: {error}</p></main>;
  if (!script) return <main><h1>Script Studio</h1><p>No script available yet.</p></main>;

  const selected = revisionData.items.find((v) => String(v.revision) === selectedRevision);

  return (
    <main style={{ padding: 16 }}>
      <h1>Script Studio</h1>
      <p>Approval state: <strong>{script.state}</strong></p>
      {actionError && <p role="alert">Action failed: {actionError}</p>}
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button onClick={() => setActiveTab("editor")} aria-pressed={activeTab === "editor"}>Editor</button>
        <button onClick={() => setActiveTab("hooks")} aria-pressed={activeTab === "hooks"}>Hook & Retention</button>
        <button onClick={() => setActiveTab("visual-plan")} aria-pressed={activeTab === "visual-plan"}>Visual Plan</button>
      </div>
      {activeTab === "editor" && <section style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", gap: 16 }}>
        <aside>
          <h2>Outline & History</h2>
          <ol>{script.sections.map((s) => <li key={s.title}>{s.title}</li>)}</ol>
          <h3>Version History</h3>
          {revisionData.loading && <p>Loading revisions…</p>}
          {revisionData.error && <p role="alert">Failed revisions: {revisionData.error}</p>}
          {!revisionData.loading && revisionData.items.length === 0 && <p>No revisions found.</p>}
          <select value={selectedRevision} onChange={(e) => setSelectedRevision(e.target.value)}>
            <option value="">Select revision</option>
            {revisionData.items.map((v) => <option key={v.id} value={v.revision}>r{v.revision} · {v.editor_event}</option>)}
          </select>
          {selected && <pre>{JSON.stringify(selected.script_snapshot.sections, null, 2)}</pre>}
        </aside>

        <section>
          <h2>Script Editor</h2>
          {script.sections.map((section, index) => (
            <div key={section.title}>
              <h3>{section.title}</h3>
              <textarea
                style={{ width: "100%", minHeight: 120 }}
                value={section.content}
                onChange={(e) => {
                  const next = [...script.sections];
                  next[index] = { ...next[index], content: e.target.value };
                  setScript({ ...script, sections: next });
                }}
              />
            </div>
          ))}
          <button disabled={saving} onClick={() => patchSections(script.sections)}>{saving ? "Saving…" : "Save Revision"}</button>
          <button disabled={saving} onClick={() => runAction("improve", { editor_event: "ai-improve" })}>Improve Script</button>
          <button disabled={saving} onClick={() => runAction("score", { quality_report: script.quality_report || {} })}>Rescore</button>
        </section>

        <aside>
          <h2>Scoring & Suggestions</h2>
          {script.quality_report ? <pre>{JSON.stringify(script.quality_report, null, 2)}</pre> : <p>Not scored yet.</p>}
          <h3>Quality Warnings</h3>
          {warnings.length === 0 ? <p>No warnings.</p> : <ul>{warnings.map((w) => <li key={w}>{w}</li>)}</ul>}
          <button disabled={saving} onClick={() => runAction("approve", {})}>Approve</button>
          <button disabled={saving} onClick={() => runAction("override", { reason: "Manual override", approver: "studio-user" })}>Override Approve</button>
        </aside>
      </section>}

      {activeTab === "hooks" && (
        <section>
          <h2>Hook & Retention</h2>
          <div>
            <h3>Hooks</h3>
            <button disabled={hooksData.loading} onClick={generateHooks}>{hooksData.loading ? "Generating hooks…" : "Generate hook variants"}</button>
            {hooksData.error && <p role="alert">Hook action failed: {hooksData.error}</p>}
            {!hooksData.loading && !hooksData.error && hooksData.items.length === 0 && <p>No hooks generated yet.</p>}
            {!hooksData.loading && hooksData.items.length > 0 && (
              <table>
                <thead><tr><th>Type</th><th>Text</th><th>Score</th><th>Risk</th><th>Notes</th><th>Action</th></tr></thead>
                <tbody>
                  {hooksData.items.map((hook) => (
                    <tr key={hook.id}>
                      <td>{hook.type}</td><td>{hook.text}</td><td>{hook.score}</td><td>{hook.risk}</td><td>{hook.notes}</td>
                      <td><button disabled={hooksData.loading} onClick={() => selectPrimaryHook(hook.id)}>{hooksData.selectedId === hook.id ? "Primary selected" : "Select primary hook"}</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div>
            <h3>Retention</h3>
            <button disabled={retentionData.loading} onClick={analyzeRetention}>{retentionData.loading ? "Analyzing retention…" : "Retention analysis"}</button>
            {retentionData.error && <p role="alert">Retention action failed: {retentionData.error}</p>}
            {!retentionData.loading && !retentionData.error && !retentionData.analysis && <p>No retention analysis yet.</p>}
            {retentionData.analysis && (
              <>
                <h4>Warnings</h4>
                <ul>{(retentionData.analysis.warnings || []).map((w) => <li key={w}>{w}</li>)}</ul>
                <h4>Recommendations</h4>
                <ul>{(retentionData.analysis.recommendations || []).map((r) => <li key={r}>{r}</li>)}</ul>
                <h4>Section Map</h4>
                <ul>{(retentionData.analysis.section_map || []).map((s) => <li key={s.section}>{s.section}: {s.risk}</li>)}</ul>
              </>
            )}
          </div>
        </section>
      )}


      {activeTab === "visual-plan" && (
        <VisualPlanTab scriptId={script.id} api={api} disabled={saving} />
      )}
    </main>
  );
}
