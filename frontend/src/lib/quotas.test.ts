import { describe, expect, it } from "vitest";
import { areaOf, quotaRows } from "./quotas";

describe("areaOf", () => {
  it("maps regions to macro-areas", () => {
    expect(["Lombardia", "Lazio", "Sicilia", "Puglia"].map(areaOf)).toEqual([
      "Nord",
      "Centro",
      "Sud e isole",
      "Sud e isole",
    ]);
  });

  it("keeps unknown regions as they are", () => {
    expect(areaOf("Estero")).toBe("Estero");
  });
});

describe("quotaRows", () => {
  it("counts values, most frequent first", () => {
    expect(quotaRows(["a", "b", "b", "c", "b", "a"])).toEqual([
      { label: "b", count: 3 },
      { label: "a", count: 2 },
      { label: "c", count: 1 },
    ]);
  });

  it("groups the rows past top", () => {
    expect(quotaRows(["a", "a", "a", "b", "b", "c", "d"], 2)).toEqual([
      { label: "a", count: 3 },
      { label: "b", count: 2 },
      { label: "Altri (2)", count: 2 },
    ]);
  });

  it("handles an empty panel", () => {
    expect(quotaRows([])).toEqual([]);
  });
});
