import { mockPersonas, mockReport } from "../mocks";

const personaLabel = (id: string) => {
  const p = mockPersonas.find((p) => p.id === id);
  return p ? `${p.role} · ${p.sector} · ${p.company_size}` : id;
};

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
          <p>
            <strong>Cosa dicono:</strong> {item.said_summary}
          </p>
          <p>
            <strong>Cosa pensano:</strong> {item.thought_summary}
          </p>
          <details>
            <summary>Risposte delle personas ({item.responses.length})</summary>
            <table>
              <thead>
                <tr>
                  <th>Persona</th>
                  <th>Voto</th>
                  <th>Ha detto</th>
                  <th>Ha pensato</th>
                </tr>
              </thead>
              <tbody>
                {item.responses.map((r) => (
                  <tr key={r.persona_id}>
                    <td>{personaLabel(r.persona_id)}</td>
                    <td>{r.score}</td>
                    <td>{r.said}</td>
                    <td>{r.thought}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </article>
      ))}
    </section>
  );
}
