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
});
