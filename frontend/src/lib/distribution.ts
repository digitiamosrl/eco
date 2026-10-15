export type Bar = { score: number; count: number; height: number };

const SCORES = [1, 2, 3, 4, 5];

export function toBars(distribution: Record<string, number>): Bar[] {
  const counts = SCORES.map((s) => distribution[String(s)] ?? 0);
  const max = Math.max(...counts);
  return SCORES.map((score, i) => ({
    score,
    count: counts[i],
    height: max === 0 ? 0 : counts[i] / max,
  }));
}
