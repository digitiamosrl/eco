export type VariantDraft = { id: string; label: string; text: string; image: File | null };

export const MIN_VARIANTS = 2;
export const MAX_VARIANTS = 5;

export const nextLabel = (index: number) => String.fromCharCode(65 + index);

export function validateVariants(variants: VariantDraft[]): string[] {
  const errors: string[] = [];
  if (variants.length < MIN_VARIANTS) errors.push(`Servono almeno ${MIN_VARIANTS} varianti.`);
  if (variants.length > MAX_VARIANTS) errors.push(`Massimo ${MAX_VARIANTS} varianti.`);
  for (const v of variants) {
    if (!v.text.trim()) errors.push(`La variante ${v.label} non ha testo.`);
  }
  return errors;
}
