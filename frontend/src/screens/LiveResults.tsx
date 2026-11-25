import { Card, ResponseTable, ScoreBlock, SimulatedNotice } from "../ds";
import { liveStats, stimulusName } from "../lib/live";
import type { Persona } from "../types/persona";
import type { Response } from "../types/response";
import type { Stimulus } from "../types/test";

type Props = {
  stimuli: Stimulus[];
  responses: Response[];
  personas: Persona[];
  status: "running" | "done" | "error";
};

const NOTE = {
  running: "risultati provvisori: medie e voti cambiano a ogni risposta, sintesi e divergenza arrivano con il report.",
  done: "risposte complete, il report è in preparazione.",
  error: "il test si è interrotto: sono le risposte arrivate prima dell'errore, il report non verrà generato.",
} as const;

const unknownPersona = (id: string) => ({ id, role: "Persona non trovata", sector: "", company_size: "", region: "" });

/** What the panel has answered so far, refreshed at every poll while the test runs. */
export default function LiveResults({ stimuli, responses, personas, status }: Props) {
  const personaById = new Map(personas.map((p) => [p.id, p]));
  const stats = liveStats(stimuli, responses);
  // Newest first, so a new answer appears at the top of each group.
  const groups = stats
    .map(({ stimulus }, i) => ({
      // A position over the whole test: screen numbers repeat across paths and the letter is the React key.
      letter: stimulus.variant_label ?? String(i + 1),
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
    <section className="scr-live">
      <SimulatedNotice />
      <p className="eco-sub">
        <b aria-live="polite">{responses.length === 1 ? "1 risposta" : `${responses.length} risposte`}</b> · {NOTE[status]}
      </p>
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
