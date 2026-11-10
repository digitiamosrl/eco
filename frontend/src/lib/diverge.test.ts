import { describe, expect, it } from "vitest";
import { isDivergent } from "./diverge";

describe("isDivergent", () => {
  const r = { persona_id: "p1", stimulus_id: "a", said: "Tema importante.", thought: "Il solito post.", score: 3, objections: [] };
  const item = { stimulus_id: "a", rank: 1, mean_score: 3, score_distribution: {}, objections: [], said_summary: "", thought_summary: "", responses: [r] };

  it("follows the backend list", () => {
    expect(isDivergent({ ...item, divergent_persona_ids: [] }, r)).toBe(false);
    expect(isDivergent({ ...item, divergent_persona_ids: ["p1"] }, r)).toBe(true);
  });
});

describe("isDivergent without the backend list", () => {
  it("shows no divergence", () => {
    const r = { persona_id: "p1", stimulus_id: "a", said: "x", thought: "y", score: 3, objections: [] };
    expect(isDivergent({ stimulus_id: "a", rank: 1, mean_score: 3, score_distribution: {}, objections: [], said_summary: "", thought_summary: "", responses: [r] }, r)).toBe(false);
  });
});
