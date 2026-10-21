import { describe, expect, it } from "vitest";
import { nextLabel, validateVariants, type VariantDraft } from "./variants";

const variant = (label: string, text: string): VariantDraft => ({ id: label, label, text, image: null });

describe("validateVariants", () => {
  it("accepts 2 variants with text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "due")])).toEqual([]);
  });

  it("rejects fewer than 2 variants", () => {
    expect(validateVariants([variant("A", "uno")])).toEqual(["Servono almeno 2 varianti."]);
  });

  it("rejects more than 5 variants", () => {
    const six = ["A", "B", "C", "D", "E", "F"].map((l) => variant(l, "testo"));
    expect(validateVariants(six)).toEqual(["Massimo 5 varianti."]);
  });

  it("rejects variants with blank text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "   ")])).toEqual([
      "La variante B non ha testo.",
    ]);
  });
});

describe("nextLabel", () => {
  it("labels variants with letters", () => {
    expect([0, 1, 4].map(nextLabel)).toEqual(["A", "B", "E"]);
  });
});
