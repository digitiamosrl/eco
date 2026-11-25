import { useEffect, useRef, useState } from "react";
import { getPersonas, getResponses, getTest } from "../api";
import { Alert, Button, Card, Icon, Skeleton, TestProgress } from "../ds";
import { go } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import type { Response } from "../types/response";
import type { Test } from "../types/test";
import LiveResults from "./LiveResults";
import ReportScreen from "./ReportScreen";

const POLL_MS = 1500;
const message = (e: unknown) => (e instanceof Error && e.message ? e.message : "Errore imprevisto.");

// "A, B e C"
const joinLabels = (labels: string[]) => labels.join(", ").replace(/, ([^,]*)$/, " e $1");

/** One test: progress and live answers while it runs, its report when done. */
export default function TestPage({ id }: { id: string }) {
  const [test, setTest] = useState<Test | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [responses, setResponses] = useState<Response[]>([]);
  const personas = useLoad(getPersonas, []);

  // First read, and again on "Riprova".
  useEffect(() => {
    let alive = true;
    setError(null);
    getTest(id).then(
      (t) => alive && setTest(t),
      (e: unknown) => alive && setError(message(e)),
    );
    return () => {
      alive = false;
    };
  }, [id, attempt]);

  // Each new state schedules the next poll until the test ends.
  useEffect(() => {
    if (!test || test.status === "done" || test.status === "error") return;
    const timer = setTimeout(() => getTest(id).then(setTest, (e: unknown) => setError(message(e))), POLL_MS);
    return () => clearTimeout(timer);
  }, [test, id]);

  // Answers follow the progress: one read each time done_count changes.
  const doneCount = test?.done_count ?? 0;
  const shown = useRef(id);
  shown.current = id;
  useEffect(() => {
    if (doneCount === 0) return setResponses([]);
    getResponses(id).then(
      (r) => shown.current === id && setResponses((prev) => (r.length >= prev.length ? r : prev)),
      (e: unknown) => setError(message(e)),
    );
  }, [id, doneCount, attempt]);

  const retry = (
    <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
      Riprova
    </Button>
  );

  if (!test)
    return error ? (
      <Alert tone="offline" title="Non riusciamo a caricare il test." action={retry}>
        {error}
      </Alert>
    ) : (
      <div role="status" aria-label="Caricamento del test" className="scr-stack">
        <Skeleton shape="title" width={320} height={48} />
        <Skeleton shape="block" height={160} />
      </div>
    );

  if (test.status === "done") return <ReportScreen test={test} />;

  const personasInTest = test.stimuli.length ? test.total_count / test.stimuli.length : 0;
  const pathCount = new Set(test.stimuli.map((s) => s.flow_id)).size;
  const subject =
    test.kind === "prototype"
      ? `${pathCount === 1 ? "1 percorso" : `${pathCount} percorsi`} · prototipo`
      : test.stimuli.length === 1
        ? "Un post LinkedIn"
        : `${joinLabels(test.stimuli.map((s) => s.variant_label ?? s.id))} · post LinkedIn`;

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>{test.status === "error" ? "Test interrotto" : "Test in corso"}</h1>
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
      {error ? (
        <Alert tone="offline" title="Non riusciamo a leggere l'avanzamento." action={retry}>
          {error}
        </Alert>
      ) : test.status === "error" ? (
        <Alert
          title="Il test si è interrotto."
          action={
            <Button variant="light" onClick={() => go({ page: "new-test" })}>
              Nuovo test
            </Button>
          }
        >
          {test.error ?? "Errore imprevisto."}
        </Alert>
      ) : (
        <Alert tone="busy" title="Puoi chiudere la pagina.">
          Il test continua anche senza di te: lo ritrovi nella dashboard, con il report quando è finito.
        </Alert>
      )}
      {responses.length > 0 && (
        <LiveResults
          stimuli={test.stimuli}
          responses={responses}
          personas={personas.data ?? []}
          status={test.status === "error" ? "error" : "running"}
        />
      )}
    </>
  );
}
