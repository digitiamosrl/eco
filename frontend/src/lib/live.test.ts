import { describe, expect, it } from "vitest";
import type { Response } from "../types/response";
import type { Stimulus } from "../types/test";
import { liveStats, stimulusName } from "./live";

const A: Stimulus = { id: "variante-a", kind: "post", variant_label: "A", text: "x" };
const B: Stimulus = { id: "variante-b", kind: "post", variant_label: "B", text: "y" };
const answer = (stimulus_id: string, score: number): Response => ({
  persona_id: "p1",
  stimulus_id,
  thought: "t",
  said: "s",
  score,
  objections: [],
});

describe("liveStats", () => {
  it("counts the answers received so far for each stimulus, in test order", () => {
    const stats = liveStats([A, B], [answer("variante-b", 4), answer("variante-a", 2), answer("variante-b", 5)]);
    expect(stats.map((s) => [s.stimulus.id, s.count, s.mean])).toEqual([
      ["variante-a", 1, 2],
      ["variante-b", 2, 4.5],
    ]);
    expect(stats[1].distribution).toEqual({ 1: 0, 2: 0, 3: 0, 4: 1, 5: 1 });
  });

  it("has no mean before the first answer", () => {
    expect(liveStats([A], [])[0]).toMatchObject({ count: 0, mean: null });
  });
});

describe("stimulusName", () => {
  it("names variants by letter and screens by position and name", () => {
    const screen: Stimulus = { id: "s", kind: "prototype_screen", screen_index: 1, page_structure: "Prezzi" };
    expect(stimulusName(A)).toBe("Variante A");
    expect(stimulusName(screen)).toBe("Schermata 2 · Prezzi");
  });
});
