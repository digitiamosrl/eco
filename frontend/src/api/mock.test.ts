import { describe, expect, it } from "vitest";
import type { Test } from "../types/test";
import { RUN_MS, progress } from "./mock";

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
