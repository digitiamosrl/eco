import type { PrototypePath } from "../lib/prototype";
import type { VariantDraft } from "../lib/variants";
import type { Persona } from "../types/persona";
import type { Prototype } from "../types/prototype";
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

const post = async <T,>(path: string, body: FormData | object, signal?: AbortSignal) =>
  parse<T>(
    await fetch(`/api${path}`, {
      method: "POST",
      signal,
      ...(body instanceof FormData
        ? { body }
        : { body: JSON.stringify(body), headers: { "Content-Type": "application/json" } }),
    }),
  );

export const getPersonas = () => (useMocks ? mock.getPersonas() : getJson<Persona[]>("/personas"));

export const getTests = () => (useMocks ? mock.getTests() : getJson<Test[]>("/tests"));

export const getTest = (id: string) => (useMocks ? mock.getTest(id) : getJson<Test>(`/tests/${id}`));

export const getReport = (id: string) =>
  useMocks ? mock.getReport(id) : getJson<Report>(`/tests/${id}/report`);

export function startPostTest(variants: VariantDraft[]): Promise<Test> {
  if (useMocks) return mock.startPostTest(variants);
  const form = new FormData();
  form.append("kind", "post");
  for (const [i, v] of variants.entries()) {
    form.append(`variants[${i}][label]`, v.label);
    form.append(`variants[${i}][text]`, v.text);
    // Image or PDF: the backend tells them apart by magic bytes.
    if (v.attachment) form.append(`variants[${i}][image]`, v.attachment.file);
  }
  return post<Test>("/tests", form);
}

// A link goes as JSON, an artifact HTML file as multipart. The signal backs "Annulla".
export function importPrototype(input: mock.ImportInput, signal?: AbortSignal): Promise<Prototype> {
  if (useMocks) return mock.importPrototype(input, signal);
  if (input.file) {
    const form = new FormData();
    form.append("source", "artifact");
    form.append("file", input.file);
    return post<Prototype>("/prototypes/import", form, signal);
  }
  return post<Prototype>("/prototypes/import", { source: input.source, url: input.url }, signal);
}

export const startPrototypeTest = (prototypeId: string, paths: PrototypePath[]) =>
  useMocks
    ? mock.startPrototypeTest(prototypeId, paths)
    : post<Test>("/tests", { kind: "prototype", prototype_id: prototypeId, paths });
