import { getPersonas } from "../api";
import { useLoad } from "../lib/useLoad";

const SIZES = ["micro", "piccola", "media"] as const;

export default function PanelScreen() {
  const { data: personas, error } = useLoad(getPersonas, []);

  if (error) return <p role="alert">{error}</p>;
  if (!personas) return <p role="status">Caricamento del panel…</p>;

  return (
    <section>
      <h1>Panel</h1>
      <p className="sub">Decision maker di PMI italiane · {personas.length} personas sintetiche</p>
      <div className="grid">
        {SIZES.map((size) => (
          <div key={size} className="card">
            <h2>{size}</h2>
            <strong>{personas.filter((p) => p.company_size === size).length}</strong> personas
          </div>
        ))}
      </div>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Elenco personas">
        <table>
          <thead>
            <tr>
              <th scope="col">Ruolo</th>
              <th scope="col">Settore</th>
              <th scope="col">Dimensione</th>
              <th scope="col">Regione</th>
              <th scope="col">Profilo</th>
            </tr>
          </thead>
          <tbody>
            {personas.map((p) => (
              <tr key={p.id}>
                <td>{p.role}</td>
                <td>{p.sector}</td>
                <td>{p.company_size}</td>
                <td>{p.region}</td>
                <td>{p.profile}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
