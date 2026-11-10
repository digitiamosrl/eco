// Report of a test with one post (design: SinglePostReport).
import { useState } from "react";
import { Button, Card, Eyebrow, FilterChips, Objection, ResponseTable, ScoreBlock, Voices } from "../ds";
import { countActions } from "../lib/actions";
import { diverges } from "../lib/diverge";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Stimulus } from "../types/stimulus";

const VISIBLE = 10;

type Filter = "all" | "gap" | "vote";

type Props = {
  summary: string;
  item: Report["items"][number];
  stimulus?: Stimulus;
  personas: Persona[];
};

export default function SinglePostReport({ summary, item, stimulus, personas }: Props) {
  const [filter, setFilter] = useState<Filter>("all");
  const [showAll, setShowAll] = useState(false);
  const actions = countActions(item.responses);
  const actionTotal = actions.reduce((n, a) => n + a.count, 0);
  const maxAction = Math.max(1, ...actions.map((a) => a.count));
  const personaById = new Map(personas.map((p) => [p.id, p]));
  const total = item.responses.length;
  const rows = item.responses
    .map((r) => ({
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
      diverge: diverges(r.said, r.thought),
    }))
    .filter((r) => filter !== "gap" || r.diverge)
    .sort((a, b) => (filter === "vote" ? b.score - a.score : 0));
  const visible = showAll ? rows : rows.slice(0, VISIBLE);
  const gapCount = item.responses.filter((r) => diverges(r.said, r.thought)).length;

  return (
    <>
      <div className="eco-head" style={{ marginBottom: 0 }}>
        <div>
          <h1>Report · post</h1>
          <p className="eco-sub">Un post LinkedIn · {total} personas · una risposta ciascuna</p>
        </div>
      </div>
      <div className="scr-summary">
        <p className="eco-eyebrow" style={{ marginTop: 18 }}>
          Sintesi
        </p>
        <p>{summary}</p>
      </div>
      <div className="scr-podium">
        <Card as="article" pad="lg">
          <Eyebrow size={12}>Il post</Eyebrow>
          {stimulus?.text && <p className="scr-sp-quote">«{stimulus.text}»</p>}
          <div style={{ margin: "24px 0" }}>
            <ScoreBlock mean={item.mean_score} distribution={item.score_distribution} />
          </div>
          {item.objections.length > 0 && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
              {item.objections.map((o) => (
                <Objection key={o} count={item.responses.filter((r) => r.objections.includes(o)).length || null}>
                  {o}
                </Objection>
              ))}
            </div>
          )}
          <Voices said={item.said_summary} thought={item.thought_summary} />
        </Card>
        <Card as="section" pad="lg">
          <Eyebrow size={12}>La prima cosa che farebbero</Eyebrow>
          {actions.length === 0 ? (
            <p className="scr-sp-note">I dati sulle azioni non sono disponibili per questo test.</p>
          ) : (
            <>
              <div className="scr-sp-actions">
                {actions.map((a) => (
                  <div key={a.action} className="scr-sp-action">
                    <div className="scr-sp-action-head">
                      <span>{a.label}</span>
                      <b>{a.count}</b>
                    </div>
                    <div className="scr-sp-track" aria-hidden="true">
                      {a.count > 0 && <i style={{ width: (a.count / maxAction) * 100 + "%" }} />}
                    </div>
                    {a.detail && <small>{a.detail}</small>}
                  </div>
                ))}
              </div>
              <p className="scr-sp-note">
                Conteggi su {actionTotal} personas. Ogni persona sceglie una sola azione.
              </p>
            </>
          )}
        </Card>
      </div>
      <section style={{ marginTop: 40 }}>
        <div className="eco-answers-head">
          <h2>
            Le risposte{" "}
            <small>
              {visible.length} di {total}
            </small>
          </h2>
          <FilterChips
            value={filter}
            onChange={(f) => setFilter(f as Filter)}
            options={[
              { value: "all", label: "Tutte" },
              { value: "gap", label: "Solo dove divergono", dot: true, count: gapCount },
              { value: "vote", label: "Per voto" },
            ]}
          />
        </div>
        <ResponseTable groups={[{ letter: stimulus?.variant_label ?? "A", name: "Il post", rows: visible }]} />
        {rows.length > VISIBLE && !showAll && (
          <div style={{ marginTop: 20 }}>
            <Button variant="light" onClick={() => setShowAll(true)}>
              Mostra tutte le {rows.length} risposte
            </Button>
          </div>
        )}
        <p className="eco-scope-note">Con poche risposte eco scrive i conteggi, non le percentuali.</p>
      </section>
    </>
  );
}
