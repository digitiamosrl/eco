import { getPersonas, getReport, getTests } from "../api";
import ResponsesTable from "../components/ResponsesTable";
import SayThink from "../components/SayThink";
import ScoreBars from "../components/ScoreBars";
import SimulatedBanner from "../components/SimulatedBanner";
import { useLoad } from "../lib/useLoad";
import type { Report } from "../types/report";

export default function ReportScreen({ testId }: { testId?: string }) {
  const tests = useLoad(getTests, []);
  const personas = useLoad(getPersonas, []);
  const selected =
    testId ??
    tests.data
      ?.filter((t) => t.kind === "post" && t.status === "done")
      .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]?.id;
  const report = useLoad<Report | null>(
    () => (selected ? getReport(selected) : Promise.resolve(null)),
    [selected],
  );

  const error = tests.error ?? personas.error ?? report.error;
  if (error) return <p role="alert">{error}</p>;
  if (!tests.data) return <p role="status">Caricamento…</p>;
  if (!selected) return <p>Nessun test completato. Avviane uno dalla schermata Test.</p>;
  if (!report.data || !personas.data) return <p role="status">Caricamento del report…</p>;

  const personaList = personas.data;
  const items = [...report.data.items].sort((a, b) => a.rank - b.rank);

  return (
    <section>
      <SimulatedBanner />
      <h1>Report · {items.length} varianti</h1>
      <p className="sub">{report.data.summary}</p>
      {items.map((item) => (
        <article key={item.stimulus_id} className="card">
          <h2>
            #{item.rank} · Variante {item.stimulus_id}
          </h2>
          <ScoreBars distribution={item.score_distribution} mean={item.mean_score} />
          {item.objections.length > 0 && (
            <>
              <h3>Obiezioni principali</h3>
              <ul>
                {item.objections.map((o) => (
                  <li key={o}>{o}</li>
                ))}
              </ul>
            </>
          )}
          <SayThink said={item.said_summary} thought={item.thought_summary} />
          <ResponsesTable responses={item.responses} personas={personaList} />
        </article>
      ))}
    </section>
  );
}
