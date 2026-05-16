import { useMemo, useState } from "react";

const FILLER_RISK_WARNING_THRESHOLD = 7;

const requiredFields = [
  "scene_number",
  "narration_excerpt",
  "visual_type",
  "visual_description",
  "purpose",
  "asset_notes",
  "risk_notes",
  "filler_risk_score",
];

function sceneErrors(scene) {
  const errors = {};
  requiredFields.forEach((field) => {
    const value = scene?.[field];
    if (field === "filler_risk_score") {
      const n = Number(value);
      if (Number.isNaN(n) || n < 0 || n > 10) errors[field] = "Must be a number between 0 and 10.";
      return;
    }
    if (value == null || String(value).trim() === "") {
      errors[field] = "Required.";
    }
  });
  return errors;
}

export function VisualPlanTab({ scriptId, api, disabled }) {
  const [planData, setPlanData] = useState({ loading: false, error: "", success: "", plan: null });
  const [draftScenes, setDraftScenes] = useState([]);
  const [savingSceneId, setSavingSceneId] = useState("");
  const [savingAll, setSavingAll] = useState(false);
  const [approving, setApproving] = useState(false);

  const validation = useMemo(() => draftScenes.map((scene) => sceneErrors(scene)), [draftScenes]);
  const hasValidationErrors = validation.some((errs) => Object.keys(errs).length > 0);

  function hydratePlan(plan) {
    const scenes = plan?.scenes || [];
    setDraftScenes(scenes.map((s) => ({ ...s })));
    setPlanData((prev) => ({ ...prev, plan }));
  }

  async function fetchPlan() {
    setPlanData((prev) => ({ ...prev, loading: true, error: "", success: "" }));
    try {
      const data = await api(`/api/v1/scripts/${scriptId}/visual-plan`);
      hydratePlan(data.visual_plan || null);
      setPlanData((prev) => ({ ...prev, loading: false, error: "" }));
    } catch (e) {
      setPlanData((prev) => ({ ...prev, loading: false, error: e.message }));
    }
  }

  async function generatePlan() {
    setPlanData((prev) => ({ ...prev, loading: true, error: "", success: "" }));
    try {
      const data = await api(`/api/v1/scripts/${scriptId}/visual-plan/generate`, { method: "POST", body: JSON.stringify({}) });
      hydratePlan(data.visual_plan || null);
      setPlanData((prev) => ({ ...prev, loading: false, error: "", success: "Visual plan generated." }));
    } catch (e) {
      setPlanData((prev) => ({ ...prev, loading: false, error: e.message }));
    }
  }

  async function saveScene(sceneIndex) {
    const scene = draftScenes[sceneIndex];
    const errors = sceneErrors(scene);
    if (Object.keys(errors).length) {
      setPlanData((prev) => ({ ...prev, error: `Scene ${scene.scene_number || sceneIndex + 1} has validation errors.`, success: "" }));
      return;
    }
    setSavingSceneId(scene.id || String(sceneIndex));
    setPlanData((prev) => ({ ...prev, error: "", success: "" }));
    try {
      const data = await api(`/api/v1/scripts/${scriptId}/visual-plan`, {
        method: "PATCH",
        body: JSON.stringify({ scenes: [scene] }),
      });
      hydratePlan(data.visual_plan || { ...(planData.plan || {}), scenes: draftScenes });
      setPlanData((prev) => ({ ...prev, success: `Scene ${scene.scene_number || sceneIndex + 1} saved.` }));
    } catch (e) {
      setPlanData((prev) => ({ ...prev, error: e.message }));
    } finally {
      setSavingSceneId("");
    }
  }

  async function saveAll() {
    if (hasValidationErrors) {
      setPlanData((prev) => ({ ...prev, error: "Resolve validation errors before saving.", success: "" }));
      return;
    }
    setSavingAll(true);
    setPlanData((prev) => ({ ...prev, error: "", success: "" }));
    try {
      const data = await api(`/api/v1/scripts/${scriptId}/visual-plan`, {
        method: "PATCH",
        body: JSON.stringify({ scenes: draftScenes }),
      });
      hydratePlan(data.visual_plan || { ...(planData.plan || {}), scenes: draftScenes });
      setPlanData((prev) => ({ ...prev, success: "Full visual plan saved." }));
    } catch (e) {
      setPlanData((prev) => ({ ...prev, error: e.message }));
    } finally {
      setSavingAll(false);
    }
  }

  async function approvePlan() {
    if (hasValidationErrors) {
      setPlanData((prev) => ({ ...prev, error: "Cannot approve while there are validation errors.", success: "" }));
      return;
    }
    setApproving(true);
    setPlanData((prev) => ({ ...prev, error: "", success: "" }));
    try {
      await api(`/api/v1/scripts/${scriptId}/visual-plan/approve`, { method: "POST", body: JSON.stringify({}) });
      setPlanData((prev) => ({ ...prev, success: "Visual plan approval requested." }));
    } catch (e) {
      setPlanData((prev) => ({ ...prev, error: e.message }));
    } finally {
      setApproving(false);
    }
  }

  return (
    <section>
      <h2>Visual Plan</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button disabled={disabled || planData.loading} onClick={generatePlan}>{planData.loading ? "Working…" : "Generate visual plan"}</button>
        <button disabled={disabled || planData.loading} onClick={fetchPlan}>Fetch visual plan</button>
        <button disabled={disabled || savingAll || draftScenes.length === 0} onClick={saveAll}>{savingAll ? "Saving all…" : "Save full plan"}</button>
        <button disabled={disabled || approving || draftScenes.length === 0 || hasValidationErrors} onClick={approvePlan}>{approving ? "Approving…" : "Approve visual plan"}</button>
      </div>

      {planData.error && <p role="alert">Visual plan failed: {planData.error}</p>}
      {planData.success && <p role="status">{planData.success}</p>}
      {planData.loading && <p>Loading visual plan…</p>}
      {!planData.loading && !planData.error && draftScenes.length === 0 && <p>No visual plan yet. Generate or fetch to start.</p>}

      {draftScenes.length > 0 && (
        <div style={{ display: "grid", gap: 12 }}>
          {draftScenes.map((scene, index) => {
            const errs = validation[index] || {};
            const fillerRisk = Number(scene.filler_risk_score);
            const isFillerRiskWarning = !Number.isNaN(fillerRisk) && fillerRisk >= FILLER_RISK_WARNING_THRESHOLD;
            return (
              <article key={scene.id || `${scene.scene_number}-${index}`} style={{ border: "1px solid #ccc", borderRadius: 8, padding: 12 }}>
                <h3>Scene {scene.scene_number || index + 1}</h3>
                {isFillerRiskWarning && <p style={{ color: "#b45309", fontWeight: 600 }}>⚠️ High filler risk: {fillerRisk} (threshold {FILLER_RISK_WARNING_THRESHOLD})</p>}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(240px, 1fr))", gap: 8 }}>
                  {requiredFields.map((field) => (
                    <label key={field} style={{ display: "grid", gap: 4 }}>
                      <span>{field}</span>
                      <input
                        value={scene[field] ?? ""}
                        type={field === "filler_risk_score" ? "number" : "text"}
                        min={field === "filler_risk_score" ? 0 : undefined}
                        max={field === "filler_risk_score" ? 10 : undefined}
                        onChange={(e) => {
                          const next = [...draftScenes];
                          next[index] = { ...scene, [field]: field === "filler_risk_score" ? Number(e.target.value) : e.target.value };
                          setDraftScenes(next);
                        }}
                        style={errs[field] ? { borderColor: "#dc2626" } : undefined}
                      />
                      {errs[field] && <small style={{ color: "#dc2626" }}>{errs[field]}</small>}
                    </label>
                  ))}
                </div>
                <button disabled={disabled || savingSceneId === (scene.id || String(index))} onClick={() => saveScene(index)}>
                  {savingSceneId === (scene.id || String(index)) ? "Saving…" : "Save scene"}
                </button>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
