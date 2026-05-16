// @vitest-environment jsdom
import React from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { IdeaDetailPage } from "./IdeaDetailPage";

function flush() { return new Promise((r) => setTimeout(r, 0)); }
function mockFetchSequence(responses) {
  global.fetch = vi.fn(async (url, opts) => {
    const next = responses.shift();
    if (next instanceof Error) throw next;
    return { ok: next.ok ?? true, json: async () => next.body };
  });
}
afterEach(() => vi.restoreAllMocks());

function renderPage(container) {
  const root = createRoot(container);
  act(() => {
    root.render(<MemoryRouter initialEntries={["/ideas/idea-1"]}><Routes><Route path="/ideas/:ideaId" element={<IdeaDetailPage />} /></Routes></MemoryRouter>);
  });
  return root;
}

describe("IdeaDetailPage compliance tab", () => {
  it("renders compliance success state with cards and blocked readiness", async () => {
    const container = document.createElement("div");
    mockFetchSequence([{ body: { report: { id: "r1", recommendation: "approve_with_fixes", overall_risk: "medium", synthetic_content_disclosure_required: true, required_fixes: ["Add disclosure"], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "medium", copyright_risk: "low", misleading_claims_risk: "medium", sensitive_topic_risk: "low", clickbait_risk: "medium" } } }]);
    renderPage(container);
    await act(async () => { await flush(); });
    expect(container.textContent).toContain("Risk cards");
    expect(container.textContent).toContain("Synthetic disclosure required: Required");
    expect(container.textContent).toContain("Blocked: compliance requirements are not fully satisfied");
  });

  it("renders loading/error/empty states", async () => {
    const c1=document.createElement("div");
    mockFetchSequence([new Error("service down")]);
    renderPage(c1);
    expect(c1.textContent).toContain("Loading compliance report");
    await act(async()=>{await flush();});
    expect(c1.textContent).toContain("Failed to load compliance: service down");

    const c2=document.createElement("div");
    mockFetchSequence([{ok:false, body:{detail:{message:"no compliance report found for idea"}}}]);
    renderPage(c2);
    await act(async()=>{await flush();});
    expect(c2.textContent).toContain("No compliance report available yet.");
  });

  it("handles approval + override error flow", async () => {
    const container = document.createElement("div");
    mockFetchSequence([
      { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
      { body: { report: {} } },
      { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } }
    ]);
    renderPage(container);
    await act(async () => { await flush(); });

    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Approve compliance").click(); await flush(); });
    expect(global.fetch).toHaveBeenCalledWith("/api/v1/compliance/r1/approve", expect.anything());

    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Override compliance").click(); });
    expect(container.textContent).toContain("Override reason is required.");

  });
});
