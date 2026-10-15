import { describe, expect, it } from "vitest";
import { toBars } from "./distribution";

describe("toBars", () => {
  it("returns 5 bars with height relative to the tallest", () => {
    expect(toBars({ "1": 0, "2": 1, "3": 2, "4": 4, "5": 2 })).toEqual([
      { score: 1, count: 0, height: 0 },
      { score: 2, count: 1, height: 0.25 },
      { score: 3, count: 2, height: 0.5 },
      { score: 4, count: 4, height: 1 },
      { score: 5, count: 2, height: 0.5 },
    ]);
  });

  it("fills missing scores with zero", () => {
    expect(toBars({ "3": 2 }).map((b) => b.count)).toEqual([0, 0, 2, 0, 0]);
  });

  it("handles an empty distribution", () => {
    expect(toBars({}).map((b) => b.height)).toEqual([0, 0, 0, 0, 0]);
  });
});
