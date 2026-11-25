import { Logo } from "../brand/Logo";

export type SidebarItem = { key: string; label: string; href: string };

export type SidebarProps = {
  items: SidebarItem[];
  current?: string;
  user?: string;
  onChangeUser?: () => void;
};

export function Sidebar({ items, current, user, onChangeUser }: SidebarProps) {
  return (
    <nav className="eco-side" aria-label="Navigazione eco">
      <div className="eco-brand">
        <Logo />
        <span className="eco-brand__sep" aria-hidden="true" />
        <span className="eco-brand__eco">eco</span>
      </div>
      <ul className="eco-side__items">
        {items.map((it) => (
          <li key={it.key}>
            <a className="eco-side__item" href={it.href} aria-current={it.key === current ? "page" : undefined}>
              {it.label}
            </a>
          </li>
        ))}
      </ul>
      {user && (
        <div className="eco-side__user">
          <span>{user}</span>
          {onChangeUser && (
            <button type="button" className="eco-side__change" onClick={onChangeUser}>
              Cambia
            </button>
          )}
        </div>
      )}
    </nav>
  );
}
