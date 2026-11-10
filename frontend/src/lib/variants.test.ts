import { describe, expect, it } from "vitest";
import type { Stimulus } from "../types/stimulus";
import { nextLabel, textError, validateVariants, variantName, type VariantDraft } from "./variants";

const variant = (label: string, text: string): VariantDraft => ({ id: label, label, text, attachment: null });

describe("validateVariants", () => {
  it("accepts a single post with text", () => {
    expect(validateVariants([variant("A", "uno")])).toEqual([]);
  });

  it("accepts 2 variants with text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "due")])).toEqual([]);
  });

  it("rejects no variants", () => {
    expect(validateVariants([])).toEqual(["Serve almeno un post."]);
  });

  it("rejects more than 5 variants", () => {
    const six = ["A", "B", "C", "D", "E", "F"].map((l) => variant(l, "testo"));
    expect(validateVariants(six)).toEqual(["Massimo 5 varianti."]);
  });

  it("rejects variants with blank text", () => {
    expect(validateVariants([variant("A", "uno"), variant("B", "   ")])).toEqual(["La variante B non ha testo."]);
  });

  it("calls a single blank variant the post", () => {
    expect(validateVariants([variant("A", " ")])).toEqual(["Il post non ha testo."]);
    expect(textError(variant("A", ""), true)).toBe("Il post non ha testo.");
  });
});

describe("nextLabel", () => {
  it("labels variants with letters", () => {
    expect([0, 1, 4].map(nextLabel)).toEqual(["A", "B", "E"]);
  });
});

describe("variantName", () => {
  const stimuli: Stimulus[] = [{ id: "variante-a", kind: "post", variant_label: "A" }];

  it("uses the variant label of the stimulus", () => {
    expect(variantName(stimuli, "variante-a")).toBe("A");
  });

  it("falls back to the stimulus id when the stimulus is unknown", () => {
    expect(variantName(stimuli, "variante-z")).toBe("variante-z");
    expect(variantName(undefined, "variante-a")).toBe("variante-a");
  });
});
