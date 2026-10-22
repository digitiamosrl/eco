import { useState } from "react";
import { getPersonas, getReport, getTests } from "../api";
import {
  Alert,
  Button,
  EmptyState,
  FidelityStatus,
  FilterChips,
  Icon,
  ResponseTable,
  Skeleton,
  SimulatedNotice,
  VariantResult,
} from "../ds";
import { diverges } from "../lib/diverge";
import { useLoad } from "../lib/useLoad";
import { variantName } from "../lib/variants";
import type { Report } from "../types/report";
import SinglePostReport from "./SinglePostReport";

type Filter = "all" | "gap" | "vote";

type Props = { testId?: string; onGoTest: () => void };

export default function ReportScreen({ testId, onGoTest }: Props) {
  const [attempt, setAttempt] = useState(0);
  const [filter, setFilter] = useState<Filter>("all");
  const tests = useLoad(getTests, [attempt]);
  const personas = useLoad(getPersonas, [attempt]);
  // GET /tests lists the most recent test first.
  const test = tests.data?.find((t) => (testId ? t.id === testId : t.status === "done"));
  // The backend has no prototype report yet (501), so it is not requested.
  const selected = test?.kind === "post" ? test.id : undefined;
  const report = useLoad<Report | null>(
    () => (selected ? getReport(selected) : Promise.resolve(null)),
    [selected, attempt],
  );

  const notices = (
    <div className="eco-notices" style={{ marginBottom: 36 }}>
      <SimulatedNotice />
      <FidelityStatus />
    </div>
  );

  const error = tests.error ?? personas.error ?? report.error;
  if (error)
    return (
      <>
        {notices}
        <Alert
          tone="offline"
          title="Non riusciamo a caricare il report."
          action={
            <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
              Riprova
            </Button>
          }
        >
          {error}
        </Alert>
      </>
    );

  if (tests.data && !test)
    return (
      <>
        {notices}
        <EmptyState title="Nessun test ancora" action={<Button onClick={onGoTest}>Vai a Test</Button>}>
          Il report compare qui quando il primo test è completato. Basta un post, o fino a 5 varianti da confrontare,
          oppure un prototipo.
        </EmptyState>
      </>
    );

  if (test?.kind === "prototype")
    return (
      <>
        {notices}
        <EmptyState title="Il report del prototipo non è ancora disponibile" action={<Button onClick={onGoTest}>Vai a Test</Button>}>
          Il test è salvo: il report delle schermate arriverà con una prossima versione.
        </EmptyState>
      </>
    );

  if (!test || !report.data || !personas.data)
    return (
      <>
        {notices}
        <div role="status" aria-label="Caricamento del report" className="scr-stack">
          <Skeleton shape="title" width={320} height={48} />
          <Skeleton width="60%" height={28} />
          <div className="scr-podium">
            <Skeleton shape="block" height={420} />
            <Skeleton shape="block" height={420} />
          </div>
        </div>
      </>
    );

  const stimuli = test.stimuli;
  if (report.data.items.length === 1) {
    const item = report.data.items[0];
    return (
      <>
        {notices}
        <SinglePostReport
          summary={report.data.summary}
          item={item}
          stimulus={stimuli.find((s) => s.id === item.stimulus_id)}
          personas={personas.data}
        />
      </>
    );
  }
  const personaById = new Map(personas.data.map((p) => [p.id, p]));
  const items = [...report.data.items].sort((a, b) => a.rank - b.rank);
  const responseCount = items.reduce((n, it) => n + it.responses.length, 0);
  const groups = items
    .map((it) => ({
      letter: variantName(stimuli, it.stimulus_id),
      name: `Variante ${variantName(stimuli, it.stimulus_id)}`,
      rank: it.rank,
      rows: it.responses
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
        .sort((a, b) => (filter === "vote" ? b.score - a.score : 0)),
    }))
    .filter((g) => g.rows.length > 0);
  const gapCount = items.reduce((n, it) => n + it.responses.filter((r) => diverges(r.said, r.thought)).length, 0);

  return (
    <>
      {notices}
      <div className="eco-head" style={{ marginBottom: 0 }}>
        <h1>Report · post</h1>
      </div>
      <div className="scr-summary">
        <p className="eco-eyebrow" style={{ marginTop: 18 }}>
          Sintesi
        </p>
        <p>{report.data.summary}</p>
      </div>
      <div className="scr-podium">
        {items.map((it) => (
          <VariantResult
            key={it.stimulus_id}
            rank={it.rank}
            name={`Variante ${variantName(stimuli, it.stimulus_id)}`}
            quote={stimuli.find((s) => s.id === it.stimulus_id)?.text}
            mean={it.mean_score}
            distribution={it.score_distribution}
            objections={it.objections}
            said={it.said_summary}
            thought={it.thought_summary}
          />
        ))}
      </div>
      <section style={{ marginTop: 40 }}>
        <div className="eco-answers-head">
          <h2>
            Le risposte{" "}
            <small>
              {personas.data.length} personas · {responseCount} risposte
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
        <ResponseTable groups={groups} />
        <p className="eco-scope-note">Con poche risposte eco scrive i conteggi, non le percentuali.</p>
      </section>
    </>
  );
}
