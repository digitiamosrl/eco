import { describe, expect, it } from "vitest";
import { diverges, isDivergent } from "./diverge";

describe("diverges", () => {
  it("is true when said and thought differ", () => {
    expect(diverges("Tema importante.", "Il solito post.")).toBe(true);
  });

  it("is false when said is empty", () => {
    expect(diverges("   ", "Non ho capito cosa vendono.")).toBe(false);
  });

  it("ignores spaces and case", () => {
    expect(diverges("  Lo giro  al TEAM.", "lo giro al team.")).toBe(false);
  });
});

describe("isDivergent", () => {
  const r = { persona_id: "p1", stimulus_id: "a", said: "Tema importante.", thought: "Il solito post.", score: 3, objections: [] };
  const item = { stimulus_id: "a", rank: 1, mean_score: 3, score_distribution: {}, objections: [], said_summary: "", thought_summary: "", responses: [r] };

  it("uses the backend list when present", () => {
    expect(isDivergent({ ...item, divergent_persona_ids: [] }, r)).toBe(false);
    expect(isDivergent({ ...item, divergent_persona_ids: ["p1"] }, r)).toBe(true);
  });

  it("falls back to comparing the texts", () => {
    expect(isDivergent(item, r)).toBe(true);
  });
});
