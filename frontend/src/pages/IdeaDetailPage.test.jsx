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

it("shows lab tab empty states", async () => {
  const container = document.createElement("div");
  mockFetchSequence([
    { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
    { ok: false, body: { detail: { message: "no publishing package" } } },
    { body: { titles: [] } },
    { body: { thumbnails: [] } },
  ]);
  renderPage(container);
  await act(async () => { await flush(); });
  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Title & Thumbnail Lab").click(); });
  expect(container.textContent).toContain("No title variants yet.");
  expect(container.textContent).toContain("No thumbnail concepts yet.");
});

it("generates titles success and shows error state", async () => {
  const container = document.createElement("div");
  mockFetchSequence([
    { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
    { ok: false, body: { detail: { message: "no publishing package" } } },
    { body: { titles: [] } },
    { body: { thumbnails: [] } },
    { body: { titles: [{ id: "t1", title_text: "Great Title", selected: false, clarity_score: 8, curiosity_score: 7, truthfulness_score: 9, promise_match_score: 8, overall_title_score: 8, clickbait_risk: 2 }] } },
    new Error("boom"),
  ]);
  renderPage(container);
  await act(async () => { await flush(); });
  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Title & Thumbnail Lab").click(); });

  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate title variants").click(); await flush(); });
  expect(container.textContent).toContain("Title variants generated.");

  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate title variants").click(); await flush(); });
  expect(container.textContent).toContain("Title lab action failed: boom");
});

it("shows score visibility with clickbait risk and syncs title selection", async () => {
  const container = document.createElement("div");
  mockFetchSequence([
    { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
    { body: { package: { title: "Old title", thumbnail_brief: "Old brief", validation: { warnings: [], errors: [], compliance_blockers: [] } } } },
    { body: { titles: [{ id: "t1", title_text: "One", selected: false, clarity_score: 8, curiosity_score: 7, truthfulness_score: 9, promise_match_score: 8, overall_title_score: 8, clickbait_risk: 2 }] } },
    { body: { thumbnails: [] } },
    { body: { title: { id: "t1", selected: true } } },
    { body: { titles: [{ id: "t1", title_text: "One", selected: true, clarity_score: 8, curiosity_score: 7, truthfulness_score: 9, promise_match_score: 8, overall_title_score: 8, clickbait_risk: 2 }] } },
    { body: { package: { title: "One", thumbnail_brief: "Old brief", validation: { warnings: [], errors: [], compliance_blockers: [] } } } },
  ]);
  renderPage(container);
  await act(async () => { await flush(); });
  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Title & Thumbnail Lab").click(); });
  expect(container.textContent).toContain("clickbait risk 2");

  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Select final title").click(); await flush(); });
  expect(container.textContent).toContain("Final title selected and synced to publishing package.");
  expect(container.textContent).toContain("Title:");
  expect(container.textContent).toContain("One");
});

it("generates and selects thumbnail concept with readability notes", async () => {
  const container = document.createElement("div");
  mockFetchSequence([
    { body: { report: { id: "r1", recommendation: "approve", overall_risk: "low", synthetic_content_disclosure_required: false, required_fixes: [], reused_content_risk: "low", repetitive_content_risk: "low", mass_production_risk: "low", copyright_risk: "low", misleading_claims_risk: "low", sensitive_topic_risk: "low", clickbait_risk: "low" } } },
    { body: { package: { title: "Any", thumbnail_brief: "Old", validation: { warnings: [], errors: [], compliance_blockers: [] } } } },
    { body: { titles: [{ id: "t1", title_text: "One", selected: true, clarity_score: 8, curiosity_score: 7, truthfulness_score: 9, promise_match_score: 8, overall_title_score: 8, clickbait_risk: 2 }] } },
    { body: { thumbnails: [] } },
    { body: { thumbnails: [{ id: "th1", main_object: "Face", selected: false, composition: "Close", text_overlay: "Hook", mobile_readability_notes: "Large type", avoid: "Clutter" }] } },
    { body: { thumbnail: { id: "th1", selected: true } } },
    { body: { thumbnails: [{ id: "th1", main_object: "Face", selected: true, composition: "Close", text_overlay: "Hook", mobile_readability_notes: "Large type", avoid: "Clutter" }] } },
    { body: { package: { title: "Any", thumbnail_brief: "Main object: Face", validation: { warnings: [], errors: [], compliance_blockers: [] } } } },
  ]);
  renderPage(container);
  await act(async () => { await flush(); });
  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Title & Thumbnail Lab").click(); });

  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate thumbnail briefs").click(); await flush(); });
  expect(container.textContent).toContain("Mobile readability: Large type");

  await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Select final thumbnail concept").click(); await flush(); });
  expect(container.textContent).toContain("Final thumbnail concept selected and synced to publishing package.");
});
