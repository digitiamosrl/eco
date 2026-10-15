import { mockPersonas } from "../mocks";

export default function PanelScreen() {
  return (
    <section>
      <h1>Panel</h1>
      <ul>
        {mockPersonas.map((p) => (
          <li key={p.id}>
            {p.role} · {p.sector} · {p.region}
          </li>
        ))}
      </ul>
    </section>
  );
}
