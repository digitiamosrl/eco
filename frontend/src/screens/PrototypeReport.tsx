// Report of a prototype test (wireframe 3b): one strip of screens per path, then the selected screen.
import { useState } from "react";
import { apiUrl } from "../api";
import { Card, Eyebrow, Objection, ResponseTable, ScoreBlock, ScreenStrip, Voices } from "../ds";
import { isDivergent } from "../lib/diverge";
import { reportPaths } from "../lib/prototype";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Stimulus } from "../types/stimulus";

type Props = { report: Report; stimuli: Stimulus[]; personas: Persona[] };

const screenName = (s: Stimulus) => s.page_structure || `Schermata ${(s.screen_index ?? 0) + 1}`;

export default function PrototypeReport({ report, stimuli, personas }: Props) {
  const paths = reportPaths(stimuli, report.items);
  const critical = report.items.find((it) => it.rank === 1);
  const [selectedId, setSelectedId] = useState(critical?.stimulus_id ?? paths[0]?.screens[0]?.stimulus.id);
  const many = paths.length > 1;
  const where = (id?: string) => {
    const p = paths.findIndex((path) => path.screens.some((s) => s.stimulus.id === id));
    const s = paths[p]?.screens.find((sc) => sc.stimulus.id === id);
    return s && { step: (s.stimulus.screen_index ?? 0) + 1, name: screenName(s.stimulus), path: p + 1, item: s.item };
  };
  const crit = where(critical?.stimulus_id);
  const sel = where(selectedId);
  const item = sel?.item;
  const personaById = new Map(personas.map((p) => [p.id, p]));
  const task = stimuli.find((s) => s.task)?.task;
  const screenCount = paths.reduce((n, p) => n + p.screens.length, 0);

  return (
    <>
      <div className="eco-head" style={{ marginBottom: 0 }}>
        <div>
          <h1>Report · prototipo</h1>
          <p className="eco-sub">
            {many ? `${paths.length} percorsi · ` : ""}
            {screenCount} schermate · {personas.length} personas
            {crit && (crit.item?.abandon_count ?? 0) > 0 &&
              ` · il punto critico è la schermata ${crit.step}${many ? ` del percorso ${crit.path}` : ""}`}
          </p>
          {task && <p className="eco-sub">Compito: «{task}»</p>}
        </div>
      </div>
      <div className="scr-summary">
        <p className="eco-eyebrow" style={{ marginTop: 18 }}>
          Sintesi
        </p>
        <p>{report.summary}</p>
      </div>

      {paths.map((path, p) => (
        <section key={path.flowId} style={{ marginBottom: 32 }}>
          {many && <Eyebrow size={12}>Percorso {p + 1}</Eyebrow>}
          <ScreenStrip
            screens={path.screens.map((s) => ({
              name: screenName(s.stimulus),
              image: s.stimulus.image_url && apiUrl(s.stimulus.image_url),
              abandon: s.item?.abandon_count,
            }))}
            selected={path.screens.findIndex((s) => s.stimulus.id === selectedId)}
            onSelect={(i) => setSelectedId(path.screens[i].stimulus.id)}
          />
        </section>
      ))}

      {sel && item && (
        <>
          <Card as="article" pad="lg">
            <Eyebrow size={12}>
              {many ? `Percorso ${sel.path} · ` : ""}Schermata {sel.step} · {sel.name}
            </Eyebrow>
            <p className="eco-sub">
              {item.abandon_count ?? 0} di {item.responses.length} lascerebbero perdere qui
            </p>
            <div style={{ margin: "24px 0" }}>
              <ScoreBlock mean={item.mean_score} distribution={item.score_distribution} />
            </div>
            {(item.objections.length > 0 || (item.misunderstood ?? []).length > 0) && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
                {(item.misunderstood ?? []).map((m) => (
                  <Objection key={"m" + m} label="Frainteso">
                    {m}
                  </Objection>
                ))}
                {item.objections.map((o) => (
                  <Objection key={"o" + o} count={item.responses.filter((r) => r.objections.includes(o)).length || null}>
                    {o}
                  </Objection>
                ))}
              </div>
            )}
            <Voices said={item.said_summary} thought={item.thought_summary} />
          </Card>
          <section style={{ marginTop: 40 }}>
            <div className="eco-answers-head">
              <h2>
                Le risposte su questa schermata <small>{item.responses.length}</small>
              </h2>
            </div>
            <ResponseTable
              groups={[
                {
                  letter: String(sel.step),
                  name: sel.name,
                  rows: item.responses.map((r) => ({
                    persona: personaById.get(r.persona_id) ?? {
                      id: r.persona_id,
                      role: "Persona non trovata",
                      sector: "",
                      company_size: "",
                      region: "",
                    },
                    score: r.score,
                    said: r.said,
                    thought: r.thought,
                    diverge: isDivergent(item, r),
                    abandon: r.would_abandon,
                  })),
                },
              ]}
            />
            <p className="eco-scope-note">Con poche risposte eco scrive i conteggi, non le percentuali.</p>
          </section>
        </>
      )}
    </>
  );
}
