// @vitest-environment jsdom
import React from "react";
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ScriptStudioPage } from "./ScriptStudioPage";

function flush() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function mockFetchSequence(responses) {
  global.fetch = vi.fn(async () => {
    const next = responses.shift();
    if (next instanceof Error) throw next;
    return {
      ok: next.ok ?? true,
      json: async () => next.body,
    };
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ScriptStudioPage smoke states", () => {
  it("renders loading then success", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [{ id: "s1", state: "draft", sections: [{ title: "hook", content: "This hook is long enough for validation and rendering." }, { title: "body", content: "Body section provides evidence and sequencing for the argument." }, { title: "cta", content: "Ask audience to share one experiment in comments today." }] }] } },
      { body: { versions: [] } },
    ]);

    await act(async () => {
      root.render(<ScriptStudioPage />);
    });
    await act(async () => {
      await flush();
      await flush();
    });
    expect(container.textContent).toContain("Script Studio");
    expect(container.textContent).toContain("Approval state: draft");
  });

  it("renders error state", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([new Error("network down")]);

    await act(async () => {
      root.render(<ScriptStudioPage />);
      await flush();
    });

    expect(container.textContent).toContain("Failed to load: network down");
  });

  it("renders empty state", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [] } },
      { body: { script: null }, ok: true },
    ]);

    await act(async () => {
      root.render(<ScriptStudioPage />);
      await flush();
      await flush();
    });

    expect(container.textContent).toContain("No script available yet");
  });

  it("handles hook generation success and selection", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [{ id: "s1", state: "draft", sections: [{ title: "hook", content: "This hook is long enough for validation and rendering." }, { title: "body", content: "Body section provides evidence and sequencing for the argument." }, { title: "cta", content: "Ask audience to share one experiment in comments today." }] }] } },
      { body: { versions: [] } },
      { body: { hooks: [{ id: "h1", type: "curiosity", text: "Wait until you see this.", score: 8.7, risk: "low", notes: "strong open loop" }] } },
      { body: { hooks: [{ id: "h1", type: "curiosity", text: "Wait until you see this.", score: 8.7, risk: "low", notes: "strong open loop" }] } },
    ]);

    await act(async () => {
      root.render(<ScriptStudioPage />);
    });
    await act(async () => { await flush(); await flush(); });

    const tab = Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Hook & Retention");
    await act(async () => { tab.click(); });

    const generate = Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate hook variants");
    await act(async () => { generate.click(); await flush(); });
    expect(container.textContent).toContain("Wait until you see this.");

    const select = Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Select primary hook");
    await act(async () => { select.click(); await flush(); });
    expect(container.textContent).toContain("Primary selected");
  });

  it("renders hook empty state", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [{ id: "s1", state: "draft", sections: [{ title: "hook", content: "This hook is long enough for validation and rendering." }, { title: "body", content: "Body section provides evidence and sequencing for the argument." }, { title: "cta", content: "Ask audience to share one experiment in comments today." }] }] } },
      { body: { versions: [] } },
      { body: { hooks: [] } },
    ]);
    await act(async () => { root.render(<ScriptStudioPage />); });
    await act(async () => { await flush(); await flush(); });
    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Hook & Retention").click();
    });
    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate hook variants").click();
      await flush();
    });
    expect(container.textContent).toContain("No hooks generated yet.");
  });

  it("renders retention analysis path", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [{ id: "s1", state: "draft", sections: [{ title: "hook", content: "This hook is long enough for validation and rendering." }, { title: "body", content: "Body section provides evidence and sequencing for the argument." }, { title: "cta", content: "Ask audience to share one experiment in comments today." }] }] } },
      { body: { versions: [] } },
      { body: { analysis: { warnings: ["Drop at 20s"], recommendations: ["Tighten setup"], section_map: [{ section: "hook", risk: "low" }] } } },
    ]);
    await act(async () => { root.render(<ScriptStudioPage />); });
    await act(async () => { await flush(); await flush(); });
    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Hook & Retention").click(); });
    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Retention analysis").click();
      await flush();
    });
    expect(container.textContent).toContain("Drop at 20s");
    expect(container.textContent).toContain("Tighten setup");
    expect(container.textContent).toContain("hook: low");
  });

  it("shows clear hook and retention API errors", async () => {
    const container = document.createElement("div");
    const root = createRoot(container);
    mockFetchSequence([
      { body: { scripts: [{ id: "s1", state: "draft", sections: [{ title: "hook", content: "This hook is long enough for validation and rendering." }, { title: "body", content: "Body section provides evidence and sequencing for the argument." }, { title: "cta", content: "Ask audience to share one experiment in comments today." }] }] } },
      { body: { versions: [] } },
      { ok: false, body: { message: "Hook endpoint unavailable" } },
      { ok: false, body: { message: "Retention service timeout" } },
    ]);
    await act(async () => { root.render(<ScriptStudioPage />); });
    await act(async () => { await flush(); await flush(); });
    await act(async () => { Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Hook & Retention").click(); });
    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Generate hook variants").click();
      await flush();
    });
    await act(async () => {
      Array.from(container.querySelectorAll("button")).find((b) => b.textContent === "Retention analysis").click();
      await flush();
    });
    expect(container.textContent).toContain("Hook action failed: Hook endpoint unavailable");
    expect(container.textContent).toContain("Retention action failed: Retention service timeout");
  });
});
