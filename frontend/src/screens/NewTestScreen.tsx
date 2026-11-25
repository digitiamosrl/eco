import { useRef, useState } from "react";
import { getPersonas, startPostTest, startPrototypeTest } from "../api";
import { AddVariantCard, Alert, FieldError, Icon, LaunchBar, Segmented } from "../ds";
import type { PrototypePath } from "../lib/prototype";
import { useLoad } from "../lib/useLoad";
import { MAX_VARIANTS, MIN_VARIANTS, nextLabel, textError, validateVariants, type VariantDraft } from "../lib/variants";
import type { Test } from "../types/test";
import PostEditor from "./PostEditor";
import PrototypeImport from "./PrototypeImport";

type Mode = Test["kind"];

const emptyVariant = (index: number): VariantDraft => ({
  id: crypto.randomUUID(),
  label: nextLabel(index),
  text: "",
  attachment: null,
});

const message = (e: unknown) => (e instanceof Error && e.message ? e.message : "Errore imprevisto.");

type Props = { onStarted: (testId: string) => void };

export default function NewTestScreen({ onStarted }: Props) {
  const [mode, setMode] = useState<Mode>("post");
  const [variants, setVariants] = useState<VariantDraft[]>([emptyVariant(0)]);
  const [errors, setErrors] = useState<string[]>([]);
  const [startError, setStartError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  // The last prototype launch, so "Riprova" can repeat it.
  const lastProto = useRef<{ id: string; paths: PrototypePath[]; task: string } | null>(null);
  const personas = useLoad(getPersonas, []);
  const panelSize = personas.data?.length ?? 0;

  const single = variants.length === 1;

  const update = (id: string, patch: Partial<VariantDraft>) => {
    setErrors([]);
    // A replaced attachment frees its object URL.
    if (patch.attachment) {
      const old = variants.find((v) => v.id === id)?.attachment;
      if (old) URL.revokeObjectURL(old.url);
    }
    setVariants((vs) => vs.map((v) => (v.id === id ? { ...v, ...patch } : v)));
  };

  const remove = (id: string) => {
    setErrors([]);
    const old = variants.find((v) => v.id === id)?.attachment;
    if (old) URL.revokeObjectURL(old.url);
    setVariants((vs) => vs.filter((v) => v.id !== id).map((v, i) => ({ ...v, label: nextLabel(i) })));
  };

  async function start(proto = lastProto.current) {
    if (mode === "post") {
      const found = validateVariants(variants);
      setErrors(found);
      if (found.length > 0) return;
    }
    if (mode === "prototype" && !proto) return;
    lastProto.current = proto;
    setSending(true);
    setStartError(null);
    try {
      const test =
        mode === "post" || !proto ? await startPostTest(variants) : await startPrototypeTest(proto.id, proto.paths, proto.task);
      onStarted(test.id);
    } catch (e) {
      setStartError(message(e));
    } finally {
      setSending(false);
    }
  }

  // Errors not tied to a single variant, e.g. the variant count.
  const otherErrors = errors.filter((e) => !variants.some((v) => textError(v, single) === e));

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>Nuovo test</h1>
          <p className="eco-sub">
            {mode === "prototype"
              ? "Allega un prototipo: il panel lo percorre dal punto di partenza"
              : single
                ? "Un post per leggere le reazioni del panel. Aggiungi una variante per confrontarle."
                : `Confronta fino a ${MAX_VARIANTS} varianti dello stesso post`}
          </p>
        </div>
        <Segmented
          value={mode}
          onChange={(m) => {
            setMode(m as Mode);
            setErrors([]);
            setStartError(null);
          }}
          options={[
            { value: "post", label: "Post LinkedIn", icon: <Icon name="linkedin" /> },
            { value: "prototype", label: "Prototipo", icon: <Icon name="phone" /> },
          ]}
        />
      </div>
      {startError && (
        <div style={{ marginBottom: 24 }}>
          <Alert title="Non è stato possibile avviare il test.">{startError}</Alert>
        </div>
      )}
      {personas.error && (
        <div style={{ marginBottom: 24 }}>
          <Alert title="Non riusciamo a caricare il panel.">{personas.error}</Alert>
        </div>
      )}
      {mode === "post" ? (
        <>
          <div
            className={
              "scr-variants" + (variants.length === 2 ? " scr-variants--two" : single ? " scr-variants--one" : "")
            }
          >
            {variants.map((v) => (
              <PostEditor
                key={v.id}
                letter={v.label}
                single={single}
                text={v.text}
                attachment={v.attachment}
                error={errors.find((e) => e === textError(v, single)) ?? undefined}
                onTextChange={(text) => update(v.id, { text })}
                onAttach={(attachment) => update(v.id, { attachment })}
                onRemove={variants.length > MIN_VARIANTS ? () => remove(v.id) : undefined}
              />
            ))}
            {variants.length < MAX_VARIANTS && (
              <AddVariantCard
                used={variants.length}
                max={MAX_VARIANTS}
                onAdd={() => setVariants((vs) => [...vs, emptyVariant(vs.length)])}
              />
            )}
          </div>
          {otherErrors.map((e) => (
            <FieldError key={e}>{e}</FieldError>
          ))}
          <LaunchBar
            personas={panelSize}
            onStart={() => start()}
            loading={sending}
            disabled={panelSize === 0}
            eta={`circa ${variants.length + 1} minuti`}
          />
        </>
      ) : (
        <PrototypeImport
          personas={panelSize}
          loading={sending}
          onStart={(id, paths, task) => start({ id, paths, task })}
        />
      )}
    </>
  );
}
