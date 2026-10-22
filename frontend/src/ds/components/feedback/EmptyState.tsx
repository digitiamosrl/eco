import type { ReactNode } from "react";
import { Icon, type IconName } from "../icons/Icon";

export type EmptyStateProps = {
  icon?: IconName;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
};

export function EmptyState({ icon = "inbox", title, children, action }: EmptyStateProps) {
  return (
    <div className="eco-empty">
      <span className="eco-empty__ico" aria-hidden="true">
        <Icon name={icon} />
      </span>
      <h2>{title}</h2>
      {children && <p>{children}</p>}
      {action}
    </div>
  );
}
