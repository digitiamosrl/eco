import { Icon } from "../icons/Icon";

export type TestRowProps = {
  href: string;
  kind: "post" | "prototype";
  title: string;
  /** "2 varianti", "5 schermate" */
  detail: string;
  when: string;
  by?: string;
  status: "running" | "done" | "error";
  percent?: number;
};

const STATUS = { done: "Completato", error: "Interrotto" } as const;

export function TestRow({ href, kind, title, detail, when, by, status, percent = 0 }: TestRowProps) {
  return (
    <a className="eco-testrow" href={href}>
      <span className="eco-testrow__kind" role="img" aria-label={kind === "post" ? "Post LinkedIn" : "Prototipo"}>
        <Icon name={kind === "post" ? "linkedin" : "phone"} />
      </span>
      <span className="eco-testrow__main">
        <b>{title}</b>
        <span>{[detail, when, by].filter(Boolean).join(" · ")}</span>
      </span>
      <span className={`eco-testrow__status eco-testrow__status--${status}`}>
        {status === "running" ? `In corso · ${percent}%` : STATUS[status]}
      </span>
    </a>
  );
}
