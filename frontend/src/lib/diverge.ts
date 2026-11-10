import type { Report } from "../types/report";
import type { Response } from "../types/response";

type Item = Report["items"][number];

const normalize = (s: string) => s.trim().replace(/\s+/g, " ").toLowerCase();

// shortcut: text comparison used only while the backend report does not send divergent_persona_ids; drop it once it does.
export function diverges(said: string, thought: string): boolean {
  const s = normalize(said);
  return s !== "" && s !== normalize(thought);
}

export const isDivergent = (item: Item, r: Response) =>
  item.divergent_persona_ids ? item.divergent_persona_ids.includes(r.persona_id) : diverges(r.said, r.thought);
