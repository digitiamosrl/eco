const normalize = (s: string) => s.trim().replace(/\s+/g, " ").toLowerCase();

// shortcut: computed on the client because the Report schema has no field for it; it should come from the backend report, as decided in PR #2.
export function diverges(said: string, thought: string): boolean {
  const s = normalize(said);
  return s !== "" && s !== normalize(thought);
}
