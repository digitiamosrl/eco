import { useState } from "react";
import { cx } from "../../cx";
import { Avatar } from "../responses/Avatar";

export type Persona = {
  id: string;
  role: string;
  sector: string;
  company_size: string;
  region: string;
  profile: string;
};

export type PersonaListProps = {
  personas?: Persona[];
};

export function PersonaList({ personas = [] }: PersonaListProps) {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  return (
    <ul className="eco-personas">
      {personas.map((p) => (
        <li key={p.id} className="eco-persona">
          <Avatar code={p.id} />
          <div className="eco-persona__who">
            <b>{p.role}</b>
            <div className="eco-persona__tags">
              <span className="eco-persona__tag">{p.sector}</span>
              <span className="eco-persona__tag">{p.company_size}</span>
              <span className="eco-persona__tag">{p.region}</span>
            </div>
          </div>
          <div className="eco-persona__body">
            <p className={cx("eco-persona__bio", open[p.id] && "eco-persona__bio--open")}>{p.profile}</p>
            <button
              type="button"
              className="eco-persona__more"
              aria-expanded={!!open[p.id]}
              onClick={() => setOpen((o) => ({ ...o, [p.id]: !o[p.id] }))}
            >
              {open[p.id] ? "Mostra meno" : "Leggi tutto"}
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
