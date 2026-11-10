import { Fragment } from "react";
import { Letter } from "../test/Letter";
import { Said } from "../voices/Said";
import { Thought } from "../voices/Thought";
import { Avatar } from "./Avatar";
import { Vote } from "./Vote";

export type ResponseRow = {
  persona: { id: string; role: string; sector: string; company_size: string; region: string };
  score: number;
  said?: string;
  thought?: string;
  diverge?: boolean;
};

export type ResponseGroup = {
  letter: string;
  name?: string;
  rank?: number;
  rows: ResponseRow[];
};

export type ResponseTableProps = {
  groups?: ResponseGroup[];
  saidLabel?: string;
  thoughtLabel?: string;
};

export function ResponseTable({ groups = [], saidLabel = "Ha detto", thoughtLabel = "Ha pensato" }: ResponseTableProps) {
  return (
    <table className="eco-table">
      <thead>
        <tr>
          <th className="eco-col-who">Persona</th>
          <th className="eco-col-vote">Voto</th>
          <th>{saidLabel}</th>
          <th>{thoughtLabel}</th>
        </tr>
      </thead>
      <tbody>
        {groups.map((g) => (
          <Fragment key={g.letter}>
            <tr className="eco-group">
              <td colSpan={4}>
                <span className="eco-group-title">
                  <Letter size="sm">{g.letter}</Letter>
                  {g.name}
                  {g.rank && <small>#{g.rank}</small>}
                </span>
              </td>
            </tr>
            {g.rows.map((r, i) => (
              <tr key={g.letter + i}>
                <td>
                  <div className="eco-who">
                    <Avatar code={r.persona.id} />
                    <div>
                      <b>{r.persona.role}</b>
                      <span>{[r.persona.sector, r.persona.company_size, r.persona.region].join(" · ")}</span>
                    </div>
                  </div>
                </td>
                <td>
                  <Vote score={r.score} />
                </td>
                <td data-l={saidLabel}>
                  <Said>{r.said ? "«" + r.said + "»" : ""}</Said>
                </td>
                <td data-l={thoughtLabel}>
                  <Thought diverge={r.diverge}>«{r.thought}»</Thought>
                </td>
              </tr>
            ))}
          </Fragment>
        ))}
      </tbody>
    </table>
  );
}
