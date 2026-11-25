import { useState } from "react";
import { Button, Card, FieldError } from "../ds";

type Props = { initial?: string; onDone: (name: string) => void };

/** First run, or "Cambia" in the sidebar: a name saved with each test. Not an account. */
export default function NameScreen({ initial = "", onDone }: Props) {
  const [name, setName] = useState(initial);
  const [error, setError] = useState<string | null>(null);

  return (
    <Card pad="lg" style={{ maxWidth: 520, margin: "40px auto" }}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (name.trim()) onDone(name.trim().slice(0, 60));
          else setError("Scrivi un nome, anche solo il tuo.");
        }}
      >
        <h1 style={{ fontSize: 32 }}>Come ti chiami?</h1>
        <p className="eco-sub">Lo salviamo con ogni test che lanci, così nella dashboard si vede chi l'ha fatto.</p>
        <label className="scr-name-label" htmlFor="eco-name">
          Nome
        </label>
        <input
          id="eco-name"
          className="scr-pt-input scr-name-input"
          value={name}
          maxLength={60}
          autoFocus
          onChange={(e) => {
            setName(e.target.value);
            setError(null);
          }}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? "eco-name-err" : undefined}
        />
        {error && <FieldError id="eco-name-err">{error}</FieldError>}
        <div style={{ marginTop: 20 }}>
          <Button type="submit">Continua</Button>
        </div>
      </form>
    </Card>
  );
}
