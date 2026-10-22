import { useEffect, useState } from "react";
import { getFlows, getPersonas, getTest, startPostTest, startPrototypeTest } from "../api";
import {
  AddVariantCard,
  Alert,
  Button,
  Card,
  FieldError,
  FlowOption,
  Icon,
  LaunchBar,
  Segmented,
  Skeleton,
  TestProgress,
  VariantEditor,
} from "../ds";
import { useLoad } from "../lib/useLoad";
import { MAX_VARIANTS, MIN_VARIANTS, nextLabel, textError, validateVariants, type VariantDraft } from "../lib/variants";
import type { Test } from "../types/test";

const POLL_MS = 1500;

type Mode = Test["kind"];

const emptyVariant = (index: number): VariantDraft => ({
  id: crypto.randomUUID(),
  label: nextLabel(index),
  text: "",
  image: null,
});

const message = (e: unknown) => (e instanceof Error && e.message ? e.message : "Errore imprevisto.");

const capturedOn = (iso: string) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "long" });

// "A, B e C"
const joinLabels = (labels: string[]) => labels.join(", ").replace(/, ([^,]*)$/, " e $1");

type Props = { onShowReport: (testId: string) => void };

export default function TestScreen({ onShowReport }: Props) {
  const [mode, setMode] = useState<Mode>("post");
  const [variants, setVariants] = useState<VariantDraft[]>([emptyVariant(0), emptyVariant(1)]);
  const [flowIds, setFlowIds] = useState<string[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [startError, setStartError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [test, setTest] = useState<Test | null>(null);
  const [pollError, setPollError] = useState<string | null>(null);
  const [flowsAttempt, setFlowsAttempt] = useState(0);
  const personas = useLoad(getPersonas, []);
  const flows = useLoad(getFlows, [flowsAttempt]);
  const panelSize = personas.data?.length ?? 0;

  // Each new Test state schedules the next poll, until done or error; unmounting clears the timer.
  useEffect(() => {
    if (!test || test.status === "done" || test.status === "error") return;
    const timer = setTimeout(() => {
      getTest(test.id).then(setTest, (e: unknown) => setPollError(message(e)));
    }, POLL_MS);
    return () => clearTimeout(timer);
  }, [test]);

  const update = (id: string, patch: Partial<VariantDraft>) => {
    setErrors([]);
    setVariants((vs) => vs.map((v) => (v.id === id ? { ...v, ...patch } : v)));
  };

  const remove = (id: string) => {
    setErrors([]);
    setVariants((vs) => vs.filter((v) => v.id !== id).map((v, i) => ({ ...v, label: nextLabel(i) })));
  };

  async function start() {
    if (mode === "post") {
      const found = validateVariants(variants);
      setErrors(found);
      if (found.length > 0) return;
    }
    setSending(true);
    setStartError(null);
    try {
      setTest(mode === "post" ? await startPostTest(variants) : await startPrototypeTest(flowIds));
    } catch (e) {
      setTest(null);
      setStartError(message(e));
    } finally {
      setSending(false);
    }
  }

  if (test) {
    const personasInTest = test.stimuli.length ? test.total_count / test.stimuli.length : panelSize;
    const subject =
      test.kind === "post"
        ? `${joinLabels(test.stimuli.map((s) => s.variant_label ?? s.id))} · post LinkedIn`
        : `${new Set(test.stimuli.map((s) => s.flow_id)).size} flussi · prototipo`;
    return (
      <>
        <div className="eco-head">
          <div>
            <h1>
              {test.status === "done" ? "Test completato" : test.status === "error" ? "Test interrotto" : "Test in corso"}
            </h1>
            <p className="eco-sub">
              {subject} · {personasInTest} personas
            </p>
          </div>
        </div>
        <Card pad="lg" style={{ marginBottom: 20 }}>
          <TestProgress
            done={test.done_count}
            total={test.total_count}
            personas={personasInTest}
            status={test.status === "error" ? "error" : "running"}
          />
        </Card>
        {pollError ? (
          <Alert
            tone="offline"
            title="Non riusciamo a leggere l'avanzamento."
            action={
              <Button
                variant="light"
                icon={<Icon name="refresh" />}
                onClick={() => {
                  setPollError(null);
                  setTest({ ...test });
                }}
              >
                Riprova
              </Button>
            }
          >
            {pollError}
          </Alert>
        ) : (
          test.status !== "done" &&
          test.status !== "error" && (
            <Alert tone="busy" title="Puoi chiudere la pagina.">
              Il test continua anche senza di te: lo ritrovi nel Report quando è finito.
            </Alert>
          )
        )}
        {test.status === "error" && (
          <Alert
            title="Il test si è interrotto."
            action={
              <Button variant="light" icon={<Icon name="refresh" />} loading={sending} onClick={start}>
                Riprova
              </Button>
            }
          >
            {test.error ?? "Errore imprevisto."}
          </Alert>
        )}
        {startError && (
          <div style={{ marginTop: 20 }}>
            <Alert title="Non è stato possibile avviare il test.">{startError}</Alert>
          </div>
        )}
        <div className="scr-actions">
          {test.status === "done" && (
            <Button icon={<Icon name="arrow" />} onClick={() => onShowReport(test.id)}>
              Vedi il report
            </Button>
          )}
          {(test.status === "done" || test.status === "error") && (
            <Button variant="light" onClick={() => setTest(null)}>
              Nuovo test
            </Button>
          )}
        </div>
      </>
    );
  }

  // Errors not tied to a single variant, e.g. the variant count.
  const otherErrors = errors.filter((e) => !variants.some((v) => textError(v) === e));

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>Nuovo test</h1>
          <p className="eco-sub">
            {mode === "post"
              ? `Confronta da ${MIN_VARIANTS} a ${MAX_VARIANTS} varianti dello stesso post`
              : "Scegli i flussi catturati da far percorrere al panel"}
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
        <div className={"scr-variants" + (variants.length === 2 ? " scr-variants--two" : "")}>
          {variants.map((v) => (
            <VariantEditor
              key={v.id}
              letter={v.label}
              text={v.text}
              image={v.image ?? undefined}
              error={errors.find((e) => e === textError(v))}
              onTextChange={(text) => update(v.id, { text })}
              onImage={(image) => update(v.id, { image })}
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
      ) : flows.error ? (
        <Alert
          title="Non riusciamo a caricare i flussi."
          action={
            <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setFlowsAttempt((n) => n + 1)}>
              Riprova
            </Button>
          }
        >
          {flows.error}
        </Alert>
      ) : !flows.data ? (
        <div role="status" aria-label="Caricamento dei flussi" className="eco-flows">
          <Skeleton shape="block" height={200} />
          <Skeleton shape="block" height={200} />
        </div>
      ) : (
        <div className="eco-flows">
          {flows.data.map((f) => (
            <FlowOption
              key={f.id}
              name={f.name}
              screens={f.screen_count}
              capturedAt={capturedOn(f.captured_at)}
              selected={flowIds.includes(f.id)}
              onToggle={() =>
                setFlowIds((ids) => (ids.includes(f.id) ? ids.filter((x) => x !== f.id) : [...ids, f.id]))
              }
            />
          ))}
        </div>
      )}
      {otherErrors.map((e) => (
        <FieldError key={e}>{e}</FieldError>
      ))}
      <LaunchBar
        personas={panelSize}
        onStart={start}
        loading={sending}
        disabled={panelSize === 0 || (mode === "prototype" && flowIds.length === 0)}
        eta={
          mode === "prototype" && flowIds.length === 0
            ? "scegli almeno un flusso"
            : `circa ${mode === "post" ? variants.length + 1 : flowIds.length * 2} minuti`
        }
      />
    </>
  );
}
