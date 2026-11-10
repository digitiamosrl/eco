import { Card } from "../surfaces/Card";
import { FieldError } from "../feedback/FieldError";
import { Icon } from "../icons/Icon";
import { Letter } from "./Letter";

export type VariantEditorProps = {
  letter?: string;
  text?: string;
  onTextChange?: (text: string) => void;
  image?: string;
  onImage?: (url: string) => void;
  onRemove?: () => void;
  error?: string;
  placeholder?: string;
};

export function VariantEditor({
  letter = "A",
  text = "",
  onTextChange,
  image,
  onImage,
  onRemove,
  error,
  placeholder = "Scrivi qui il testo del post…",
}: VariantEditorProps) {
  const id = "v-" + letter;
  return (
    <Card as="article" pad="none" className="eco-variant">
      <div className="eco-variant__head">
        <Letter>{letter}</Letter>
        <h2>Variante {letter}</h2>
        {onRemove && (
          <button type="button" className="eco-variant__remove" onClick={onRemove} aria-label={"Rimuovi variante " + letter}>
            Rimuovi
          </button>
        )}
      </div>
      <label className="eco-sr" htmlFor={id}>
        Testo variante {letter}
      </label>
      <textarea
        id={id}
        className="eco-textarea"
        value={text}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? id + "-err" : undefined}
        onChange={(e) => onTextChange && onTextChange(e.target.value)}
      />
      {error && <FieldError id={id + "-err"}>{error}</FieldError>}
      <label className={"eco-drop" + (image ? " eco-drop--filled" : "")}>
        <input
          type="file"
          accept="image/*"
          aria-label={"Immagine della variante " + letter}
          onChange={(e) => {
            const f = e.target.files && e.target.files[0];
            if (f && onImage) onImage(URL.createObjectURL(f));
          }}
        />
        {image ? (
          <>
            <img src={image} alt="" />
            <span className="eco-drop__swap">Cambia immagine</span>
          </>
        ) : (
          <>
            <span className="eco-drop__ico">
              <Icon name="image" strokeWidth={2.4} />
            </span>
            Immagine del post · trascina o scegli un file
          </>
        )}
      </label>
    </Card>
  );
}
