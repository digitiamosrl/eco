import { useEffect, useState } from "react";
import { getTest } from "../api";
import type { Test } from "../types/test";

const POLL_MS = 2000;

type Props = { initial: Test; onShowReport: (testId: string) => void };

export default function TestProgress({ initial, onShowReport }: Props) {
  const [test, setTest] = useState(initial);
  const [error, setError] = useState<string | null>(null);

  // Each new Test state schedules the next poll, until done or error.
  useEffect(() => {
    if (test.status === "done" || test.status === "error") return;
    const timer = setTimeout(() => {
      getTest(test.id).then(setTest, (e: Error) => setError(e.message));
    }, POLL_MS);
    return () => clearTimeout(timer);
  }, [test]);

  const retry = () => {
    setError(null);
    setTest({ ...test });
  };

  return (
    <section>
      <h1>{test.status === "done" ? "Test completato" : "Test in corso"}</h1>
      <progress max={test.total_count || 1} value={test.done_count} aria-label="Avanzamento del test" />
      <p>
        {test.done_count} risposte su {test.total_count}
      </p>
      {test.status === "error" && <p role="alert">{test.error ?? "Il test si è interrotto."}</p>}
      {error && (
        <p role="alert">
          {error}{" "}
          <button type="button" className="secondary" onClick={retry}>
            Riprova
          </button>
        </p>
      )}
      {test.status === "done" && (
        <button type="button" className="primary" onClick={() => onShowReport(test.id)}>
          Vai al report
        </button>
      )}
    </section>
  );
}
