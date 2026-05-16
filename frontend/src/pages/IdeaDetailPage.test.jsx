// @vitest-environment jsdom
import React from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { IdeaDetailPage } from "./IdeaDetailPage";

function flush() { return new Promise((r) => setTimeout(r, 0)); }
function mockFetchSequence(responses) {
  global.fetch = vi.fn(async () => {
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

describe("IdeaDetailPage", () => {
  it("renders tabs and compliance state", async () => {
    const container = document.createElement("div");
    mockFetchSequence([
      { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
      { ok: false, body: { detail: { message: "no publishing package" } } },
      { body: { titles: [] } },
      { body: { thumbnails: [] } },
    ]);

    renderPage(container);
    await act(async () => { await flush(); });

    expect(container.textContent).toContain("Compliance");
    expect(container.textContent).toContain("Publishing");
    expect(container.textContent).toContain("Risk cards");
  });

  it("supports edit/save flow and shows validation warnings", async () => {
    const container = document.createElement("div");
    mockFetchSequence([
      { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
      { body: { package: { title: "Initial", description: "desc", tags: "", chapters: "", pinned_comment: "", thumbnail_brief: "", disclosure_notes: "", checklist: "", validation: { warnings: ["tone warning"], errors: [], compliance_blockers: [] } } } },
      { body: { titles: [] } },
      { body: { thumbnails: [] } },
      { body: { package: { title: "Updated" } } },
    ]);

    renderPage(container);
    await act(async () => { await flush(); });
    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Publishing").click(); });

    expect(container.textContent).toContain("⚠️ tone warning");

    const titleInput = container.querySelector("input");
    await act(async () => {
      titleInput.value = "Updated";
      titleInput.dispatchEvent(new Event("input", { bubbles: true }));
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Save edits").click();
      await flush();
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/v1/ideas/idea-1/publishing", expect.anything());
    expect(container.textContent).toContain("Publishing edits saved.");
  });

  it("toggles approve disabled/enabled and triggers export actions", async () => {
    const container = document.createElement("div");
    mockFetchSequence([
      { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
      { body: { package: { title: "Existing", description: "desc", validation: { warnings: [], errors: ["title too short"], compliance_blockers: ["missing disclosure"] } } } },
      { body: { titles: [] } },
      { body: { thumbnails: [] } },
      { body: { validation: { warnings: [], errors: [], compliance_blockers: [] }, package: { title: "Existing" } } },
      { body: { package: { title: "Existing" } } },
      { body: { package: { title: "Existing" } } },
      { body: { package: { title: "Existing" } } },
    ]);

    renderPage(container);
    await act(async () => { await flush(); });
    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Publishing").click(); });

    expect(container.textContent).toContain("title too short");
    let approveBtn = Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Approve publish package");
    expect(approveBtn.disabled).toBe(true);

    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Validate").click();
      await flush();
    });
    approveBtn = Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Approve publish package");
    expect(approveBtn.disabled).toBe(false);

    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Export markdown").click();
      await flush();
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Export JSON").click();
      await flush();
      approveBtn.click();
      await flush();
    });

    expect(global.fetch).toHaveBeenCalledWith("/api/v1/ideas/idea-1/publishing/export?format=markdown", expect.anything());
    expect(global.fetch).toHaveBeenCalledWith("/api/v1/ideas/idea-1/publishing/export?format=json", expect.anything());
    expect(global.fetch).toHaveBeenCalledWith("/api/v1/ideas/idea-1/publishing/approve", expect.anything());
  });
});
