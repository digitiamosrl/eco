// In-memory fake backend. Simulates a test that takes RUN_MS to complete.
import type { PrototypePath, Source } from "../lib/prototype";
import type { VariantDraft } from "../lib/variants";
import { mockPersonas, mockProtoImport, mockReport, mockSingleItem, mockSingleSummary, mockStimuli } from "../mocks";
import type { Persona } from "../types/persona";
import type { Prototype } from "../types/prototype";
import type { Report } from "../types/report";
import type { Stimulus, Test } from "../types/test";

export const RUN_MS = 5000;
export const IMPORT_MS = 1500;

const PRIVATE_FIGMA =
  "Non possiamo aprire il file: è privato. In Figma imposta la condivisione su «chiunque abbia il link» e riprova.";

const started = new Map<string, { test: Test; startedAt: number }>([
  [
    "t1",
    {
      test: {
        id: "t1",
        kind: "post",
        status: "done",
        created_at: "2026-10-15T10:00:00Z",
        done_count: 6,
        total_count: 6,
        stimuli: mockStimuli,
      },
      startedAt: 0,
    },
  ],
]);

export function progress(test: Test, startedAt: number, now: number): Test {
  const ratio = Math.min(1, (now - startedAt) / RUN_MS);
  return {
    ...test,
    status: ratio >= 1 ? "done" : "running",
    done_count: Math.round(ratio * test.total_count),
  };
}

export async function getPersonas(): Promise<Persona[]> {
  return mockPersonas;
}

function start(kind: Test["kind"], stimuli: Stimulus[]): Test {
  const id = `t${started.size + 1}`;
  const test: Test = {
    id,
    kind,
    status: "queued",
    created_at: new Date().toISOString(),
    done_count: 0,
    total_count: stimuli.length * mockPersonas.length,
    stimuli,
  };
  started.set(id, { test, startedAt: Date.now() });
  return test;
}

export async function startPostTest(variants: VariantDraft[]): Promise<Test> {
  return start(
    "post",
    variants.map((v) => ({
      id: `variante-${v.label.toLowerCase()}`,
      kind: "post",
      variant_label: v.label,
      text: v.text,
      ...(v.attachment ? { image_url: v.attachment.url, attachment_kind: v.attachment.kind } : {}),
    })),
  );
}

// A plain SVG with the screen name, standing in for the capture served by GET /files/….
const screenImage = (name: string) =>
  "data:image/svg+xml," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200"><rect width="320" height="200" fill="#f4f2ff"/><rect x="16" y="16" width="288" height="20" rx="6" fill="#e3defc"/><text x="160" y="116" font-family="sans-serif" font-size="20" font-weight="700" fill="#2a2353" text-anchor="middle">${name}</text></svg>`,
  );

const prototypes = new Map<string, Prototype>();

export type ImportInput = { source: Source; url?: string; file?: File };

export function importPrototype(input: ImportInput, signal?: AbortSignal): Promise<Prototype> {
  return new Promise((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Import annullato.", "AbortError"));
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      const url = input.url ?? "";
      if (input.source === "figma" && url.includes("privato")) return reject(new Error(PRIVATE_FIGMA));
      const data = mockProtoImport[input.source];
      const starts =
        input.source === "artifact" && url.includes("singola")
          ? [{ ...data.starts[0], screens: data.starts[0].screens.slice(0, 1) }]
          : data.starts;
      const prototype: Prototype = {
        id: `pr${prototypes.size + 1}`,
        source: input.source,
        name: data.name,
        imported_at: new Date().toISOString(),
        starts: starts.map((s) => ({
          id: s.id,
          name: s.name,
          screens: s.screens.map((name, index) => ({ index, name, image_url: screenImage(name) })),
        })),
      };
      prototypes.set(prototype.id, prototype);
      resolve(prototype);
    }, IMPORT_MS);
    if (signal?.aborted) abort();
    else signal?.addEventListener("abort", abort, { once: true });
  });
}

export async function startPrototypeTest(prototypeId: string, paths: PrototypePath[]): Promise<Test> {
  if (!prototypes.has(prototypeId)) throw new Error("Prototipo non trovato.");
  return start(
    "prototype",
    paths.flatMap((p) =>
      p.screen_indexes.map((i) => ({
        id: `${p.start_id}-${i}`,
        kind: "prototype_screen" as const,
        flow_id: p.start_id,
        screen_index: i,
      })),
    ),
  );
}

export async function getTest(id: string): Promise<Test> {
  const entry = started.get(id);
  if (!entry) throw new Error("Test non trovato.");
  return progress(entry.test, entry.startedAt, Date.now());
}

export async function getTests(): Promise<Test[]> {
  return [...started.values()].map((e) => progress(e.test, e.startedAt, Date.now())).reverse();
}

export async function getReport(id: string): Promise<Report> {
  const stimuli = started.get(id)?.test.stimuli ?? [];
  if (stimuli.length === 1)
    return { ...mockReport, test_id: id, summary: mockSingleSummary, items: [mockSingleItem(stimuli[0].id)] };
  return { ...mockReport, test_id: id };
}
