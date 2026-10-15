import { mockReport } from "../mocks";

export default function ReportScreen() {
  return (
    <section>
      <h1>Report</h1>
      <p>
        <strong>Risultati simulati</strong> da personas sintetiche, non da persone reali.
      </p>
      {mockReport.items.map((item) => (
        <article key={item.stimulus_id}>
          <h2>
            #{item.rank} · {item.stimulus_id} · media {item.mean_score.toFixed(1)}
          </h2>
          <p>
            Distribuzione:{" "}
            {Object.entries(item.score_distribution)
              .map(([score, count]) => `${score}: ${count}`)
              .join(" · ")}
          </p>
        </article>
      ))}
    </section>
  );
}
