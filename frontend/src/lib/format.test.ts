import { describe, expect, it } from "vitest";
import { formatWhen, testTitle } from "./format";

describe("formatWhen", () => {
  it("writes day, short month and time", () => {
    expect(formatWhen("2026-11-25T14:32:00")).toBe("25 nov, 14:32");
  });
});

describe("testTitle", () => {
  it("falls back when the test has no title", () => {
    expect(testTitle({ title: "Caso cliente" })).toBe("Caso cliente");
    expect(testTitle({})).toBe("Senza titolo");
  });
});
