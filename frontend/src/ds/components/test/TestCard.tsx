import { Icon } from "../icons/Icon";

export type TestCardProps = {
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

export function TestCard({ href, kind, title, detail, when, by, status, percent = 0 }: TestCardProps) {
  return (
    <a className="eco-testcard" href={href}>
      <span className="eco-testcard__top">
        <span className="eco-testcard__kind" role="img" aria-label={kind === "post" ? "Post LinkedIn" : "Prototipo"}>
          <Icon name={kind === "post" ? "linkedin" : "phone"} />
        </span>
        <span className={`eco-testcard__status eco-testcard__status--${status}`}>
          {status === "running" ? `In corso · ${percent}%` : STATUS[status]}
        </span>
      </span>
      <b className="eco-testcard__title">{title}</b>
      <span className="eco-testcard__meta">{detail}</span>
      <span className="eco-testcard__meta">{[when, by].filter(Boolean).join(" · ")}</span>
    </a>
  );
}
