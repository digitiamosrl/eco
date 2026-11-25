export type BreadcrumbProps = {
  /** Links before the current page, e.g. the dashboard. */
  trail: { label: string; href: string }[];
  current: string;
};

export function Breadcrumb({ trail, current }: BreadcrumbProps) {
  return (
    <nav className="eco-crumbs" aria-label="Percorso">
      <ol>
        {trail.map((t) => (
          <li key={t.href}>
            <a href={t.href}>{t.label}</a>
          </li>
        ))}
        <li aria-current="page">{current}</li>
      </ol>
    </nav>
  );
}
