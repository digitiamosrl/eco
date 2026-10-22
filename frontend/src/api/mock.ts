// In-memory fake backend. Simulates a test that takes RUN_MS to complete.
import type { VariantDraft } from "../lib/variants";
import { mockFlows, mockPersonas, mockReport, mockStimuli } from "../mocks";
import type { Flow } from "../types/flow";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Stimulus, Test } from "../types/test";

export const RUN_MS = 5000;

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

export async function getFlows(): Promise<Flow[]> {
  return mockFlows;
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
    variants.map((v) => ({ id: `variante-${v.label.toLowerCase()}`, kind: "post", variant_label: v.label, text: v.text })),
  );
}

export async function startPrototypeTest(flowIds: string[]): Promise<Test> {
  return start(
    "prototype",
    mockFlows
      .filter((f) => flowIds.includes(f.id))
      .flatMap((f) =>
        Array.from({ length: f.screen_count }, (_, i) => ({
          id: `${f.id}-${i}`,
          kind: "prototype_screen" as const,
          flow_id: f.id,
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
  return { ...mockReport, test_id: id };
}
