// The DS VariantEditor plus a PDF attachment, reusing its markup and classes.
import { Card, FieldError, Icon, Letter } from "../ds";
import type { Attachment } from "../lib/variants";

type Props = {
  letter: string;
  single?: boolean;
  text: string;
  onTextChange: (text: string) => void;
  attachment: Attachment | null;
  onAttach: (attachment: Attachment) => void;
  onRemove?: () => void;
  error?: string;
};

const isPdf = (f: File) => f.type === "application/pdf" || /\.pdf$/i.test(f.name);
const kb = (bytes: number) => Math.max(1, Math.round(bytes / 1024));

export default function PostEditor({ letter, single, text, onTextChange, attachment, onAttach, onRemove, error }: Props) {
  const id = "v-" + letter;
  const pdf = attachment?.kind === "pdf";
  return (
    <Card as="article" pad="none" className="eco-variant">
      <div className="eco-variant__head">
        <Letter>{letter}</Letter>
        <h2>{single ? "Il post" : "Variante " + letter}</h2>
        {onRemove && (
          <button type="button" className="eco-variant__remove" onClick={onRemove} aria-label={"Rimuovi variante " + letter}>
            Rimuovi
          </button>
        )}
      </div>
      <label className="eco-sr" htmlFor={id}>
        {single ? "Testo del post" : "Testo variante " + letter}
      </label>
      <textarea
        id={id}
        className="eco-textarea"
        value={text}
        placeholder="Scrivi qui il testo del post…"
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? id + "-err" : undefined}
        onChange={(e) => onTextChange(e.target.value)}
      />
      {error && <FieldError id={id + "-err"}>{error}</FieldError>}
      <label className={"eco-drop" + (attachment && !pdf ? " eco-drop--filled" : "") + (pdf ? " scr-pe-pdf" : "")}>
        <input
          type="file"
          accept="image/*,application/pdf,.pdf"
          aria-label={"Immagine o PDF della variante " + letter}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onAttach({ file, url: URL.createObjectURL(file), kind: isPdf(file) ? "pdf" : "image" });
            e.target.value = "";
          }}
        />
        {attachment && pdf ? (
          <>
            <span className="scr-pe-doc" aria-hidden="true">
              <b>PDF</b>
            </span>
            <span className="scr-pe-meta">
              <b>{attachment.file.name}</b>
              <span>Documento · il panel lo legge come carosello · {kb(attachment.file.size)} KB</span>
            </span>
            <span className="eco-drop__swap">Cambia file</span>
          </>
        ) : attachment ? (
          <>
            <img src={attachment.url} alt="" />
            <span className="eco-drop__swap">Cambia file</span>
          </>
        ) : (
          <>
            <span className="eco-drop__ico">
              <Icon name="image" strokeWidth={2.4} />
            </span>
            Immagine o PDF del post · trascina o scegli un file
          </>
        )}
      </label>
    </Card>
  );
}
