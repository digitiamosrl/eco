import { describe, expect, it, vi } from "vitest";
import type { Test } from "../types/test";
import { IMPORT_MS, RUN_MS, getReport, importPrototype, progress, startPostTest } from "./mock";

const test: Test = {
  id: "t9",
  kind: "post",
  status: "queued",
  created_at: "2026-10-15T10:00:00Z",
  done_count: 0,
  total_count: 6,
  stimuli: [],
};

describe("progress", () => {
  it("is running with no answers at start", () => {
    expect(progress(test, 1000, 1000)).toMatchObject({ status: "running", done_count: 0 });
  });

  it("is halfway after half the run", () => {
    expect(progress(test, 1000, 1000 + RUN_MS / 2)).toMatchObject({ status: "running", done_count: 3 });
  });

  it("is done after the full run", () => {
    expect(progress(test, 1000, 1000 + RUN_MS * 2)).toMatchObject({ status: "done", done_count: 6 });
  });
});

describe("importPrototype", () => {
  it("returns the Figma paths, or the 403 error for a private file", async () => {
    vi.useFakeTimers();
    const ok = importPrototype({ source: "figma", url: "https://www.figma.com/proto/x/Nome" });
    const ko = importPrototype({ source: "figma", url: "https://www.figma.com/proto/privato/Nome" });
    const ko2 = expect(ko).rejects.toThrow("è privato");
    await vi.advanceTimersByTimeAsync(IMPORT_MS);
    expect((await ok).starts.map((s) => s.screens.length)).toEqual([5, 4, 3]);
    await ko2;
    vi.useRealTimers();
  });

  it("finds a single screen for an artifact named singola", async () => {
    vi.useFakeTimers();
    const one = importPrototype({ source: "artifact", url: "https://claude.ai/public/artifacts/singola" });
    await vi.advanceTimersByTimeAsync(IMPORT_MS);
    expect((await one).starts.flatMap((s) => s.screens).map((s) => s.name)).toEqual(["Benvenuto"]);
    vi.useRealTimers();
  });

  it("rejects with AbortError when cancelled", async () => {
    const ctrl = new AbortController();
    const p = importPrototype({ source: "artifact", url: "x" }, ctrl.signal);
    ctrl.abort();
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
  });
});

describe("getReport", () => {
  it("has a single item for a test with one post", async () => {
    const t = await startPostTest([{ id: "a", label: "A", text: "Ciao", attachment: null }]);
    const report = await getReport(t.id);
    expect(report.items).toHaveLength(1);
    expect(report.items[0].responses.every((r) => r.action)).toBe(true);
  });
});
