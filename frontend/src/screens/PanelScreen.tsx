import { useState } from "react";
import { getPersonas } from "../api";
import { Alert, Button, Icon, PanelDots, PersonaList, QuotaCard, Skeleton } from "../ds";
import { useLoad } from "../lib/useLoad";
import { areaOf, quotaRows } from "../lib/quotas";

const TOP_SECTORS = 4;

export default function PanelScreen() {
  const [attempt, setAttempt] = useState(0);
  const { data: personas, error } = useLoad(getPersonas, [attempt]);

  const head = (
    <div className="eco-head">
      <div>
        <h1>Panel</h1>
        <p className="eco-sub">Pubblico della pagina LinkedIn Digitiamo · personas sintetiche, in sola lettura</p>
      </div>
    </div>
  );

  if (error)
    return (
      <>
        {head}
        <Alert
          title="Non riusciamo a caricare il panel."
          action={
            <Button variant="light" icon={<Icon name="refresh" />} onClick={() => setAttempt((n) => n + 1)}>
              Riprova
            </Button>
          }
        >
          {error}
        </Alert>
      </>
    );

  if (!personas)
    return (
      <>
        {head}
        <div role="status" aria-label="Caricamento del panel" className="scr-stack">
          <div className="eco-quotas">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} shape="block" height={220} />
            ))}
          </div>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ display: "flex", gap: 16 }}>
              <Skeleton shape="circle" width={44} height={44} />
              <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
                <Skeleton width="30%" />
                <Skeleton width="80%" />
              </div>
            </div>
          ))}
        </div>
      </>
    );

  return (
    <>
      {head}
      <div className="eco-launch" style={{ marginTop: 0, marginBottom: 32 }}>
        <div className="eco-panel">
          <PanelDots total={personas.length} />
          <div>
            <b>{personas.length} personas</b>
            <span>Decision maker di PMI italiane · campionate da ISTAT e dalla pagina LinkedIn, seed fisso</span>
          </div>
        </div>
      </div>
      <h2 style={{ fontSize: 32, marginBottom: 18 }}>Composizione</h2>
      <div className="eco-quotas" style={{ marginBottom: 40 }}>
        <QuotaCard title="Dimensione d'impresa" rows={quotaRows(personas.map((p) => p.company_size))} />
        <QuotaCard title="Area" rows={quotaRows(personas.map((p) => areaOf(p.region)))} />
        <QuotaCard title="Settore" rows={quotaRows(personas.map((p) => p.sector), TOP_SECTORS)} />
      </div>
      <div className="eco-answers-head">
        <h2>
          Le personas <small>{personas.length} · in sola lettura</small>
        </h2>
      </div>
      <div className="eco-card" style={{ padding: "6px 20px" }}>
        <PersonaList personas={personas} />
      </div>
    </>
  );
}
