import { describe, expect, it } from "vitest";
import { fidelityMeaning } from "./FidelityStatus";

describe("fidelityMeaning", () => {
  it("reads the tau bands", () => {
    expect(fidelityMeaning(-0.03)).toMatch(/non prevede/);
    expect(fidelityMeaning(0.2)).toMatch(/in parte/);
    expect(fidelityMeaning(0.45)).toMatch(/come il pubblico reale/);
    expect(fidelityMeaning(-0.4)).toMatch(/al contrario/);
  });
});
