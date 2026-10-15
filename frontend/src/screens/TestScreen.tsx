import { useState } from "react";
import { startPostTest } from "../api";
import TestProgress from "../components/TestProgress";
import {
  MAX_VARIANTS,
  MIN_VARIANTS,
  nextLabel,
  validateVariants,
  type VariantDraft,
} from "../lib/variants";
import type { Test } from "../types/test";

const emptyVariant = (index: number): VariantDraft => ({
  id: crypto.randomUUID(),
  label: nextLabel(index),
  text: "",
  image: null,
});

type Props = { onShowReport: (testId: string) => void };

export default function TestScreen({ onShowReport }: Props) {
  const [variants, setVariants] = useState<VariantDraft[]>([emptyVariant(0), emptyVariant(1)]);
  const [errors, setErrors] = useState<string[]>([]);
  const [sending, setSending] = useState(false);
  const [test, setTest] = useState<Test | null>(null);

  const update = (id: string, patch: Partial<VariantDraft>) =>
    setVariants((vs) => vs.map((v) => (v.id === id ? { ...v, ...patch } : v)));

  const remove = (id: string) =>
    setVariants((vs) => vs.filter((v) => v.id !== id).map((v, i) => ({ ...v, label: nextLabel(i) })));

  async function start() {
    const found = validateVariants(variants);
    setErrors(found);
    if (found.length > 0) return;
    setSending(true);
    try {
      setTest(await startPostTest(variants));
    } catch (e) {
      setErrors([(e as Error).message]);
    } finally {
      setSending(false);
    }
  }

  if (test) return <TestProgress initial={test} onShowReport={onShowReport} />;

  return (
    <section>
      <h1>Nuovo test</h1>
      <p className="sub">
        Confronta da {MIN_VARIANTS} a {MAX_VARIANTS} varianti dello stesso post LinkedIn
      </p>
      <div className="grid">
        {variants.map((v) => (
          <div key={v.id} className="card">
            <h2>Variante {v.label}</h2>
            <label>
              Testo del post
              <textarea value={v.text} onChange={(e) => update(v.id, { text: e.target.value })} />
            </label>
            <label>
              Immagine (facoltativa)
              <input
                type="file"
                accept="image/*"
                onChange={(e) => update(v.id, { image: e.target.files?.[0] ?? null })}
              />
            </label>
            {variants.length > MIN_VARIANTS && (
              <button type="button" className="secondary" onClick={() => remove(v.id)}>
                Rimuovi
              </button>
            )}
          </div>
        ))}
        {variants.length < MAX_VARIANTS && (
          <button
            type="button"
            className="secondary"
            onClick={() => setVariants((vs) => [...vs, emptyVariant(vs.length)])}
          >
            + Aggiungi variante
          </button>
        )}
      </div>
      {errors.length > 0 && (
        <ul role="alert">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}
      <button type="button" className="primary" disabled={sending} onClick={start}>
        {sending ? "Avvio…" : "Avvia test"}
      </button>
    </section>
  );
}
