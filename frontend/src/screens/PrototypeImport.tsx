// Prototype import (design: ProtoLive): source, importing, review of paths and screens, launch.
import { useEffect, useRef, useState } from "react";
import { importPrototype } from "../api";
import { Alert, Button, Card, Eyebrow, FieldError, FilterChips, FlowOption, Icon, LaunchBar, Segmented, Skeleton } from "../ds";
import { MAX_PATHS, buildPaths, screenKey, sourceError, type PrototypePath, type Source } from "../lib/prototype";
import type { Prototype } from "../types/prototype";

const SAMPLE_FIGMA = "https://www.figma.com/proto/k2Q8xR/Onboarding-cliente-v3";

const importedOn = (iso: string) => new Date(iso).toLocaleDateString("it-IT", { day: "numeric", month: "long" });

const paths = (n: number) => (n === 1 ? "1 percorso" : `${n} percorsi`);

type Props = {
  personas: number;
  loading: boolean;
  onStart: (prototypeId: string, paths: PrototypePath[]) => void;
};

export default function PrototypeImport({ personas, loading, onStart }: Props) {
  const [source, setSource] = useState<Source>("figma");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);
  const [prototype, setPrototype] = useState<Prototype | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [focus, setFocus] = useState<string | null>(null);
  const [removed, setRemoved] = useState<Set<string>>(new Set());
  const abort = useRef<AbortController | null>(null);
  useEffect(() => () => abort.current?.abort(), []);

  async function runImport() {
    const local = sourceError(source, url, !!file);
    setError(local);
    if (local) return;
    const ctrl = new AbortController();
    abort.current = ctrl;
    setImporting(true);
    try {
      const p = await importPrototype(
        file && source === "artifact" ? { source, file } : { source, url: url.trim() },
        ctrl.signal,
      );
      setPrototype(p);
      setSelected([p.starts[0].id]);
      setFocus(p.starts[0].id);
      setRemoved(new Set());
    } catch (e) {
      if (!ctrl.signal.aborted) setError(e instanceof Error && e.message ? e.message : "Errore imprevisto.");
    } finally {
      if (abort.current === ctrl) setImporting(false);
    }
  }

  const cancel = () => {
    abort.current?.abort();
    setImporting(false);
  };

  const toggle = (id: string) => {
    if (selected.includes(id)) {
      const next = selected.filter((x) => x !== id);
      setSelected(next);
      if (focus === id) setFocus(next[0] ?? null);
    } else if (selected.length < MAX_PATHS) {
      setSelected([...selected, id]);
      if (!focus) setFocus(id);
    }
  };

  const toggleScreen = (key: string) =>
    setRemoved((r) => {
      const next = new Set(r);
      if (!next.delete(key)) next.add(key);
      return next;
    });

  const built = prototype ? buildPaths(prototype, selected, removed) : [];
  const kept = built.reduce((n, p) => n + p.screen_indexes.length, 0);
  const eta = !prototype
    ? "importa prima il prototipo"
    : !selected.length
      ? "scegli almeno un percorso"
      : !kept
        ? "tieni almeno una schermata"
        : `circa ${2 + built.length} minuti · ${paths(built.length)}, ${kept === 1 ? "1 schermata" : `${kept} schermate`}`;

  let body;
  if (importing) {
    body = (
      <div className="scr-stack">
        <Alert
          tone="busy"
          title="Stiamo leggendo il prototipo."
          action={
            <Button variant="light" onClick={cancel}>
              Annulla
            </Button>
          }
        >
          {source === "figma"
            ? "Frame e collegamenti del prototipo Figma."
            : "Schermate dell’artifact, seguendo pulsanti e link."}{" "}
          Ci vuole meno di un minuto.
        </Alert>
        <div className="scr-pt-strip" role="status" aria-label="Importazione in corso">
          {[0, 1, 2, 3, 4].map((i) => (
            <Skeleton key={i} shape="block" height={150} />
          ))}
        </div>
      </div>
    );
  } else if (prototype) {
    const screenCount = prototype.starts.reduce((n, s) => n + s.screens.length, 0);
    const chosen = prototype.starts.filter((s) => selected.includes(s.id));
    const shown = prototype.starts.find((s) => s.id === focus);
    const live = (s: Prototype["starts"][number]) => s.screens.filter((sc) => !removed.has(screenKey(s.id, sc.index)));
    body = (
      <>
        <div className="scr-pt-imported">
          <span className="scr-pt-chip">{prototype.source === "figma" ? "Figma" : "Artifact"}</span>
          <b>{prototype.name}</b>
          <span className="scr-pt-muted">
            {prototype.starts.length === 1 ? "1 percorso" : `${prototype.starts.length} punti di partenza`} ·{" "}
            {screenCount === 1 ? "1 schermata" : `${screenCount} schermate`} · importato ora
          </span>
          <span className="scr-pt-change">
            <Button variant="light" onClick={() => setPrototype(null)}>
              Cambia prototipo
            </Button>
          </span>
        </div>
        {screenCount === 1 && (
          <div style={{ marginBottom: 24 }}>
            <Alert tone="info" title="Abbiamo trovato una sola schermata.">
              {prototype.source === "figma"
                ? "Il prototipo non ha collegamenti che portano ad altre schermate. Il test valuta solo questa; se ce ne sono altre, controlla il punto di partenza in Figma."
                : "L’artifact non ha pulsanti o link che portano ad altre schermate. Il test valuta solo questa; se ce ne sono altre, carica il file HTML completo."}
            </Alert>
          </div>
        )}
        {prototype.starts.length > 1 && (
          <>
            <h2 className="scr-pt-h2">
              Quali percorsi far fare al panel{" "}
              <small>
                {selected.length} di {MAX_PATHS}
              </small>
            </h2>
            <div className="eco-flows">
              {prototype.starts.map((s) => (
                <FlowOption
                  key={s.id}
                  name={s.name}
                  screens={live(s).length}
                  capturedAt={importedOn(prototype.imported_at)}
                  thumbs={live(s).map((sc) => sc.image_url)}
                  selected={selected.includes(s.id)}
                  onToggle={() => toggle(s.id)}
                />
              ))}
            </div>
          </>
        )}
        {shown && (
          <>
            <div className="scr-pt-review-head">
              <h2 className="scr-pt-h2">
                Controlla le schermate{" "}
                <small>
                  {live(shown).length} di {shown.screens.length}, in ordine
                </small>
              </h2>
              {chosen.length > 1 && (
                <FilterChips
                  label="Percorso"
                  value={shown.id}
                  onChange={setFocus}
                  options={chosen.map((s) => ({ value: s.id, label: s.name }))}
                />
              )}
            </div>
            <div className="scr-pt-strip">
              {shown.screens.map((sc, i) => {
                const key = screenKey(shown.id, sc.index);
                const off = removed.has(key);
                return (
                  <div key={key} className={"scr-pt-shot" + (off ? " scr-pt-shot--off" : "")}>
                    <div className="eco-shot__img">
                      {off ? "Tolta dal percorso" : <img src={sc.image_url} alt={`Schermata ${i + 1}: ${sc.name}`} />}
                    </div>
                    <div className="eco-shot__top">
                      <span className="eco-shot__n">{i + 1}</span>
                      <span className="eco-shot__name">{sc.name}</span>
                    </div>
                    <button
                      type="button"
                      className="scr-pt-remove"
                      aria-label={`${off ? "Rimetti" : "Togli"} ${sc.name}`}
                      onClick={() => toggleScreen(key)}
                    >
                      {off ? "Rimetti" : "Togli"}
                    </button>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </>
    );
  } else {
    const figma = source === "figma";
    body = (
      <Card pad="lg" className="scr-pt-source">
        <div className="scr-pt-source-head">
          <Eyebrow size={12}>Da dove arriva</Eyebrow>
          <Segmented
            label="Sorgente"
            value={source}
            onChange={(v) => {
              setSource(v as Source);
              setError(null);
            }}
            options={[
              { value: "figma", label: "Prototipo Figma" },
              { value: "artifact", label: "Artifact Claude" },
            ]}
          />
        </div>
        <div className="scr-pt-fields">
          <label className="scr-pt-label" htmlFor="pt-url">
            {figma ? "Link al prototipo Figma" : "Link pubblico all’artifact"}
          </label>
          <div className="scr-pt-row">
            <input
              id="pt-url"
              className="scr-pt-input"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setFile(null);
                setError(null);
              }}
              onKeyDown={(e) => e.key === "Enter" && runImport()}
              placeholder={figma ? "https://www.figma.com/proto/…" : "https://claude.ai/public/artifacts/…"}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? "pt-err" : "pt-help"}
            />
            <Button onClick={runImport}>Importa</Button>
          </div>
          {error ? (
            <FieldError id="pt-err">{error}</FieldError>
          ) : (
            <p id="pt-help" className="scr-pt-help">
              {figma
                ? "Leggiamo frame e collegamenti dal punto di partenza del prototipo. Il file deve essere condiviso con «chiunque abbia il link»."
                : "Partiamo dalla prima schermata e seguiamo pulsanti e link nell’ordine in cui compaiono."}
            </p>
          )}
          {figma && !url && (
            <button type="button" className="scr-pt-sample" onClick={() => setUrl(SAMPLE_FIGMA)}>
              Usa un link di esempio
            </button>
          )}
          {!figma && (
            <>
              <div className="scr-pt-or">
                <span>oppure</span>
              </div>
              <label className={"eco-drop scr-pt-drop" + (file ? " scr-pt-drop--on" : "")}>
                <input
                  type="file"
                  accept=".html,text/html"
                  aria-label="File HTML dell'artifact"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      setFile(f);
                      setUrl("");
                      setError(null);
                    }
                    e.target.value = "";
                  }}
                />
                {file ? (
                  <>
                    <b>{file.name}</b>
                    <span>Cambia file</span>
                  </>
                ) : (
                  <>
                    <span className="eco-drop__ico">
                      <Icon name="plus" strokeWidth={2.4} />
                    </span>
                    File HTML dell’artifact · trascina o scegli un file
                  </>
                )}
              </label>
            </>
          )}
        </div>
      </Card>
    );
  }

  return (
    <>
      {body}
      <LaunchBar
        personas={personas}
        loading={loading}
        disabled={!prototype || importing || !built.length || personas === 0}
        onStart={() => prototype && built.length && onStart(prototype.id, built)}
        eta={eta}
      />
    </>
  );
}
