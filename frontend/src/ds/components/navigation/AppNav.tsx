import type { HTMLAttributes } from "react";
import { Logo } from "../brand/Logo";

const TABS = [
  ["panel", "Panel"],
  ["test", "Test"],
  ["report", "Report"],
] as const;

export type AppNavTab = (typeof TABS)[number][0];

export type AppNavProps = HTMLAttributes<HTMLElement> & {
  current?: AppNavTab;
  onNavigate?: (tab: AppNavTab) => void;
};

export function AppNav({ current = "test", onNavigate, ...rest }: AppNavProps) {
  return (
    <nav className="eco-nav" aria-label="Navigazione eco" {...rest}>
      <div className="eco-brand">
        <Logo />
        <span className="eco-brand__sep" aria-hidden="true" />
        <span className="eco-brand__eco">eco</span>
      </div>
      <div className="eco-tabs">
        {TABS.map(([k, l]) => (
          <a
            key={k}
            className="eco-tab"
            href={"#" + k}
            aria-current={k === current ? "page" : undefined}
            onClick={(e) => {
              if (onNavigate) {
                e.preventDefault();
                onNavigate(k);
              }
            }}
          >
            {l}
          </a>
        ))}
      </div>
    </nav>
  );
}
