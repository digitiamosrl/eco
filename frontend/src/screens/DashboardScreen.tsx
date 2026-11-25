import { useState } from "react";
import { getTests } from "../api";
import { Alert, Button, EmptyState, Icon, Skeleton, TestCard } from "../ds";
import { formatWhen, testTitle } from "../lib/format";
import { go, routeHref } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import type { Test } from "../types/test";

const detail = (t: Test) => {
  if (t.kind === "post") return t.stimuli.length === 1 ? "1 post" : `${t.stimuli.length} varianti`;
  return t.stimuli.length === 1 ? "1 schermata" : `${t.stimuli.length} schermate`;
};

/** Home: the tests run so far, most recent first, and the way to start a new one. */
export default function DashboardScreen() {
  const [attempt, setAttempt] = useState(0);
  const tests = useLoad(getTests, [attempt]);
  const newTest = (
    <Button icon={<Icon name="plus" />} onClick={() => go({ page: "new-test" })}>
      Nuovo test
    </Button>
  );

  return (
    <>
      <div className="eco-head">
        <div>
          <h1>I tuoi test</h1>
          <p className="eco-sub">Post e prototipi provati sul panel, dal più recente</p>
        </div>
        {newTest}
      </div>
      {tests.error ? (
        <Alert
          tone="offline"
          title="Non riusciamo a caricare i test."
          action={
            <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
              Riprova
            </Button>
          }
        >
          {tests.error}
        </Alert>
      ) : !tests.data ? (
        <div role="status" aria-label="Caricamento dei test" className="scr-stack">
          <Skeleton shape="block" height={76} />
          <Skeleton shape="block" height={76} />
        </div>
      ) : tests.data.length === 0 ? (
        <EmptyState title="Nessun test ancora" action={newTest}>
          Lancia il primo: un post, fino a 5 varianti da confrontare, oppure un prototipo.
        </EmptyState>
      ) : (
        <ul className="eco-testlist">
          {tests.data.map((t) => (
            <li key={t.id}>
              <TestCard
                href={routeHref({ page: "test", id: t.id })}
                kind={t.kind}
                title={testTitle(t)}
                detail={detail(t)}
                when={formatWhen(t.created_at)}
                status={t.status === "done" || t.status === "error" ? t.status : "running"}
                percent={t.total_count ? Math.round((t.done_count / t.total_count) * 100) : 0}
              />
            </li>
          ))}
        </ul>
      )}
    </>
  );
}
