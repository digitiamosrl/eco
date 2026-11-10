import type { Response as PersonaResponse } from "../types/response";

type Action = NonNullable<PersonaResponse["action"]>;
type Reaction = NonNullable<PersonaResponse["reaction"]>;

// Key order breaks ties between equal counts.
const LABELS: Record<Action, string> = {
  react: "Metterebbe una reazione",
  scroll: "Scorrerebbe oltre",
  comment: "Commenterebbe",
  share: "Condividerebbe",
};

const REACTIONS: Record<Reaction, string> = {
  consiglio: "Consiglio",
  festeggio: "Festeggio",
  sostengo: "Sostengo",
  adoro: "Adoro",
  perspicace: "Perspicace",
  divertente: "Divertente",
};

export type ActionCount = { action: Action; label: string; count: number; detail?: string };

const byCountDesc = <T,>(counts: Map<T, number>) => [...counts].sort((a, b) => b[1] - a[1]);

// Counts the first action of each persona; empty when no response has an action.
export function countActions(responses: PersonaResponse[]): ActionCount[] {
  const actions = new Map<Action, number>((Object.keys(LABELS) as Action[]).map((a) => [a, 0]));
  const reactions = new Map<Reaction, number>();
  let any = false;
  for (const r of responses) {
    if (!r.action) continue;
    any = true;
    actions.set(r.action, (actions.get(r.action) ?? 0) + 1);
    if (r.action === "react" && r.reaction) reactions.set(r.reaction, (reactions.get(r.reaction) ?? 0) + 1);
  }
  if (!any) return [];
  const detail = byCountDesc(reactions)
    .map(([reaction, n]) => `${REACTIONS[reaction]} ${n}`)
    .join(" · ");
  return byCountDesc(actions).map(([action, count]) => ({
    action,
    label: LABELS[action],
    count,
    ...(action === "react" && detail ? { detail } : {}),
  }));
}
