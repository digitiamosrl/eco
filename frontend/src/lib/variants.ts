import type { Stimulus } from "../types/stimulus";

// The attachment keeps the File for the upload and an object URL for the preview.
export type Attachment = { file: File; url: string; kind: "image" | "pdf" };

export type VariantDraft = { id: string; label: string; text: string; attachment: Attachment | null };

export const MIN_VARIANTS = 1;
export const MAX_VARIANTS = 5;

export const nextLabel = (index: number) => String.fromCharCode(65 + index);

// With a single variant the UI calls it "il post".
export const textError = (v: VariantDraft, single = false) =>
  v.text.trim() ? null : single ? "Il post non ha testo." : `La variante ${v.label} non ha testo.`;

export function validateVariants(variants: VariantDraft[]): string[] {
  const errors: string[] = [];
  if (variants.length < MIN_VARIANTS) errors.push("Serve almeno un post.");
  if (variants.length > MAX_VARIANTS) errors.push(`Massimo ${MAX_VARIANTS} varianti.`);
  for (const v of variants) {
    const error = textError(v, variants.length === 1);
    if (error) errors.push(error);
  }
  return errors;
}

export const variantName = (stimuli: Stimulus[] | undefined, stimulusId: string) =>
  stimuli?.find((s) => s.id === stimulusId)?.variant_label ?? stimulusId;
