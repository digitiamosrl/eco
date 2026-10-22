export type QuotaRow = { label: string; count: number };

// ISTAT macro-areas; the panel shows "Sud e isole" as one group.
const AREAS: Record<string, string> = {
  Piemonte: "Nord",
  "Valle d'Aosta": "Nord",
  Lombardia: "Nord",
  "Trentino-Alto Adige": "Nord",
  Veneto: "Nord",
  "Friuli-Venezia Giulia": "Nord",
  Liguria: "Nord",
  "Emilia-Romagna": "Nord",
  Toscana: "Centro",
  Umbria: "Centro",
  Marche: "Centro",
  Lazio: "Centro",
  Abruzzo: "Sud e isole",
  Molise: "Sud e isole",
  Campania: "Sud e isole",
  Puglia: "Sud e isole",
  Basilicata: "Sud e isole",
  Calabria: "Sud e isole",
  Sicilia: "Sud e isole",
  Sardegna: "Sud e isole",
};

export const areaOf = (region: string) => AREAS[region] ?? region;

// Counts each value, most frequent first; past `top` rows the rest is grouped as "Altri (n)".
export function quotaRows(values: string[], top = Infinity): QuotaRow[] {
  const counts = new Map<string, number>();
  for (const v of values) counts.set(v, (counts.get(v) ?? 0) + 1);
  const rows = [...counts].map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count);
  if (rows.length <= top) return rows;
  const rest = rows.slice(top);
  return [
    ...rows.slice(0, top),
    { label: `Altri (${rest.length})`, count: rest.reduce((sum, r) => sum + r.count, 0) },
  ];
}
