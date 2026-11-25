import type { Test } from "../types/test";

const DAY = new Intl.DateTimeFormat("it-IT", { day: "numeric", month: "short" });
const TIME = new Intl.DateTimeFormat("it-IT", { hour: "2-digit", minute: "2-digit" });

/** "25 nov, 14:32", in local time. */
export function formatWhen(iso: string) {
  const d = new Date(iso);
  return `${DAY.format(d)}, ${TIME.format(d)}`;
}

// Tests saved before the dashboard have no title.
export const testTitle = (test: Pick<Test, "title">) => test.title || "Senza titolo";
