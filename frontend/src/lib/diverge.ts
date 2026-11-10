import type { Report } from "../types/report";
import type { Response } from "../types/response";

// The backend report lists, per item, the personas whose said and thought diverge (decision in PR #2).
export const isDivergent = (item: Report["items"][number], r: Response) =>
  item.divergent_persona_ids?.includes(r.persona_id) ?? false;
