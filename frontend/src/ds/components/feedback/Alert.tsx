import type { ReactNode } from "react";
import { Icon, type IconName } from "../icons/Icon";

type AlertTone = "error" | "info" | "busy" | "offline";

const ICON: Record<AlertTone, IconName> = {
  error: "alert",
  info: "clock",
  busy: "clock",
  offline: "offline",
};

export type AlertProps = {
  tone?: AlertTone;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
  icon?: IconName;
};

export function Alert({ tone = "error", title, children, action, icon }: AlertProps) {
  const cls = tone === "info" ? " eco-alert--info" : tone === "busy" ? " eco-alert--busy" : "";
  return (
    <div className={"eco-alert" + cls} role={tone === "error" || tone === "offline" ? "alert" : "status"}>
      <span className="eco-alert__ico" aria-hidden="true">
        <Icon name={icon || ICON[tone]} />
      </span>
      <div className="eco-alert__body">
        {title && <b>{title}</b>}
        {children && <span>{children}</span>}
      </div>
      {action && <div className="eco-alert__act">{action}</div>}
    </div>
  );
}
