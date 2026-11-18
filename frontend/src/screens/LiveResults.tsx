import { Card, ResponseTable, ScoreBlock, SimulatedNotice } from "../ds";
import { liveStats, stimulusName } from "../lib/live";
import type { Persona } from "../types/persona";
import type { Response } from "../types/response";
import type { Stimulus } from "../types/test";

type Props = {
  stimuli: Stimulus[];
  responses: Response[];
  personas: Persona[];
  finished: boolean;
};

const unknownPersona = (id: string) => ({ id, role: "Persona non trovata", sector: "", company_size: "", region: "" });

/** What the panel has answered so far, refreshed at every poll while the test runs. */
export default function LiveResults({ stimuli, responses, personas, finished }: Props) {
  const personaById = new Map(personas.map((p) => [p.id, p]));
  const stats = liveStats(stimuli, responses);
  // Newest first, so a new answer appears at the top of each group.
  const groups = stats
    .map(({ stimulus }) => ({
      letter: stimulus.variant_label ?? String((stimulus.screen_index ?? 0) + 1),
      name: stimulusName(stimulus),
      rows: responses
        .filter((r) => r.stimulus_id === stimulus.id)
        .reverse()
        .map((r) => ({
          persona: personaById.get(r.persona_id) ?? unknownPersona(r.persona_id),
          score: r.score,
          said: r.said,
          thought: r.thought,
        })),
    }))
    .filter((g) => g.rows.length > 0);

  return (
    <section className="scr-live" aria-live="polite">
      <SimulatedNotice>
        <b>{finished ? "Risposte complete, report in arrivo." : "Risultati provvisori."}</b> Medie e voti cambiano a
        ogni nuova risposta; la sintesi e la divergenza arrivano con il report.
      </SimulatedNotice>
      <div className="scr-live__stats">
        {stats.map((s) => (
          <Card key={s.stimulus.id} pad="lg">
            <p className="eco-eyebrow">{stimulusName(s.stimulus)}</p>
            <ScoreBlock mean={s.mean} distribution={s.distribution} />
          </Card>
        ))}
      </div>
      {groups.length > 0 && <ResponseTable groups={groups} />}
    </section>
  );
}
