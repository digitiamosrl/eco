import type { Stimulus } from "../types/stimulus";

// image is the object URL given by the DS VariantEditor; the API turns it back into a file.
export type VariantDraft = { id: string; label: string; text: string; image: string | null };

export const MIN_VARIANTS = 2;
export const MAX_VARIANTS = 5;

export const nextLabel = (index: number) => String.fromCharCode(65 + index);

export const textError = (v: VariantDraft) => (v.text.trim() ? null : `La variante ${v.label} non ha testo.`);

export function validateVariants(variants: VariantDraft[]): string[] {
  const errors: string[] = [];
  if (variants.length < MIN_VARIANTS) errors.push(`Servono almeno ${MIN_VARIANTS} varianti.`);
  if (variants.length > MAX_VARIANTS) errors.push(`Massimo ${MAX_VARIANTS} varianti.`);
  for (const v of variants) {
    const error = textError(v);
    if (error) errors.push(error);
  }
  return errors;
}

export const variantName = (stimuli: Stimulus[] | undefined, stimulusId: string) =>
  stimuli?.find((s) => s.id === stimulusId)?.variant_label ?? stimulusId;
