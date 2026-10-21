import type { Persona } from "../types/persona";
import type { Response } from "../types/response";

type Props = { responses: Response[]; personas: Persona[] };

export default function ResponsesTable({ responses, personas }: Props) {
  const label = (id: string) => {
    const p = personas.find((p) => p.id === id);
    return p ? `${p.role} · ${p.sector} · ${p.company_size}` : id;
  };

  return (
    <details>
      <summary>Risposte delle personas ({responses.length})</summary>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Risposte delle personas">
        <table>
          <thead>
            <tr>
              <th scope="col">Persona</th>
              <th scope="col">Voto</th>
              <th scope="col">Ha detto</th>
              <th scope="col">Ha pensato</th>
            </tr>
          </thead>
          <tbody>
            {responses.map((r) => (
              <tr key={r.persona_id}>
                <td>{label(r.persona_id)}</td>
                <td>{r.score}</td>
                <td>{r.said || "Non commenterebbe"}</td>
                <td className="think">{r.thought}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
