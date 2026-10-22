import type { VariantDraft } from "../lib/variants";
import type { Flow } from "../types/flow";
import type { Persona } from "../types/persona";
import type { Report } from "../types/report";
import type { Test } from "../types/test";
import * as mock from "./mock";

const useMocks = import.meta.env.VITE_USE_MOCKS !== "false";

async function parse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => null);
  if (!res.ok || data === null) {
    throw new Error(typeof data?.detail === "string" ? data.detail : `Errore del server (${res.status}).`);
  }
  return data as T;
}

const getJson = async <T,>(path: string) => parse<T>(await fetch(`/api${path}`));

const post = async <T,>(path: string, body: FormData | object) =>
  parse<T>(
    await fetch(`/api${path}`, {
      method: "POST",
      ...(body instanceof FormData
        ? { body }
        : { body: JSON.stringify(body), headers: { "Content-Type": "application/json" } }),
    }),
  );

export const getPersonas = () => (useMocks ? mock.getPersonas() : getJson<Persona[]>("/personas"));

export const getFlows = () => (useMocks ? mock.getFlows() : getJson<Flow[]>("/flows"));

export const getTests = () => (useMocks ? mock.getTests() : getJson<Test[]>("/tests"));

export const getTest = (id: string) => (useMocks ? mock.getTest(id) : getJson<Test>(`/tests/${id}`));

export const getReport = (id: string) =>
  useMocks ? mock.getReport(id) : getJson<Report>(`/tests/${id}/report`);

export async function startPostTest(variants: VariantDraft[]): Promise<Test> {
  if (useMocks) return mock.startPostTest(variants);
  const form = new FormData();
  form.append("kind", "post");
  for (const [i, v] of variants.entries()) {
    form.append(`variants[${i}][label]`, v.label);
    form.append(`variants[${i}][text]`, v.text);
    if (v.image) form.append(`variants[${i}][image]`, await (await fetch(v.image)).blob());
  }
  return post<Test>("/tests", form);
}

export const startPrototypeTest = (flowIds: string[]) =>
  useMocks ? mock.startPrototypeTest(flowIds) : post<Test>("/tests", { kind: "prototype", flow_ids: flowIds });
