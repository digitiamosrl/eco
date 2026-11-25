import type { Prototype } from "../types/prototype";
import type { Report } from "../types/report";
import type { Stimulus } from "../types/stimulus";

export type Source = Prototype["source"];
export type PrototypePath = { start_id: string; screen_indexes: number[] };

export const MAX_PATHS = 3;

// Key of a screen in the set of screens removed from a path.
export const screenKey = (startId: string, index: number) => `${startId}:${index}`;

// Local check before the import; the server still validates the link.
export function sourceError(source: Source, url: string, hasFile = false): string | null {
  const u = url.trim();
  if (source === "figma") {
    if (!u) return "Incolla il link del prototipo Figma.";
    if (!/figma\.com\/(proto|design|file)\//.test(u))
      return "Questo non sembra un link Figma. In Figma: Condividi › Copia link al prototipo.";
    return null;
  }
  return u || hasFile ? null : "Incolla il link dell’artifact oppure carica il file HTML.";
}

// Selected starts in prototype order, kept screens in order; paths left without screens are dropped.
export function buildPaths(prototype: Prototype, selected: string[], removed: Set<string>): PrototypePath[] {
  return prototype.starts
    .filter((s) => selected.includes(s.id))
    .map((s) => ({
      start_id: s.id,
      screen_indexes: s.screens.map((sc) => sc.index).filter((i) => !removed.has(screenKey(s.id, i))),
    }))
    .filter((p) => p.screen_indexes.length > 0)
    .slice(0, MAX_PATHS);
}

type ReportItem = Report["items"][number];
export type ReportPath = { flowId: string; screens: { stimulus: Stimulus; item?: ReportItem }[] };

// Screens of a prototype report grouped by tested path, in the order they were shown.
export function reportPaths(stimuli: Stimulus[], items: ReportItem[]): ReportPath[] {
  const byId = new Map(items.map((it) => [it.stimulus_id, it]));
  const paths = new Map<string, ReportPath>();
  for (const s of stimuli) {
    if (s.kind !== "prototype_screen") continue;
    const flowId = s.flow_id ?? "";
    if (!paths.has(flowId)) paths.set(flowId, { flowId, screens: [] });
    paths.get(flowId)!.screens.push({ stimulus: s, item: byId.get(s.id) });
  }
  for (const p of paths.values()) p.screens.sort((a, b) => (a.stimulus.screen_index ?? 0) - (b.stimulus.screen_index ?? 0));
  return [...paths.values()];
}
