import type { VariantDraft } from "../lib/variants";
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

const postForm = async <T,>(path: string, body: FormData) =>
  parse<T>(await fetch(`/api${path}`, { method: "POST", body }));

export const getPersonas = () => (useMocks ? mock.getPersonas() : getJson<Persona[]>("/personas"));

export const getTests = () => (useMocks ? mock.getTests() : getJson<Test[]>("/tests"));

export const getTest = (id: string) => (useMocks ? mock.getTest(id) : getJson<Test>(`/tests/${id}`));

export const getReport = (id: string) =>
  useMocks ? mock.getReport(id) : getJson<Report>(`/tests/${id}/report`);

export function startPostTest(variants: VariantDraft[]): Promise<Test> {
  if (useMocks) return mock.startPostTest(variants.length);
  const form = new FormData();
  form.append("kind", "post");
  variants.forEach((v, i) => {
    form.append(`variants[${i}][label]`, v.label);
    form.append(`variants[${i}][text]`, v.text);
    if (v.image) form.append(`variants[${i}][image]`, v.image);
  });
  return postForm<Test>("/tests", form);
}
