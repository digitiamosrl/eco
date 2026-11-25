import type { Response } from "../types/response";
import type { Stimulus } from "../types/test";

type Distribution = Record<1 | 2 | 3 | 4 | 5, number>;

export type LiveStat = {
  stimulus: Stimulus;
  count: number;
  mean: number | null;
  distribution: Distribution;
};

const SCORES = [1, 2, 3, 4, 5] as const;

/** Partial results while the panel answers: provisional, they change at every poll. */
export function liveStats(stimuli: Stimulus[], responses: Response[]): LiveStat[] {
  return stimuli.map((stimulus) => {
    const scores = responses.filter((r) => r.stimulus_id === stimulus.id).map((r) => r.score);
    const distribution = Object.fromEntries(SCORES.map((s) => [s, scores.filter((x) => x === s).length])) as Distribution;
    const mean = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null;
    return { stimulus, count: scores.length, mean, distribution };
  });
}

export function stimulusName(stimulus: Stimulus): string {
  if (stimulus.kind === "prototype_screen") {
    const position = `Schermata ${(stimulus.screen_index ?? 0) + 1}`;
    return stimulus.page_structure ? `${position} · ${stimulus.page_structure}` : position;
  }
  return `Variante ${stimulus.variant_label ?? stimulus.id}`;
}
