import type { SVGAttributes } from "react";

/* linkedin, phone, image, diverge: tracciati presi dalla tavola A.
   Gli altri seguono Lucide (stesso tratto tondo), con spessore 2.5 come nella tavola. */
const P = {
  linkedin: '<rect x="3" y="3" width="18" height="18" rx="5"/><path d="M8 11v5M8 8v.01M12 16v-5M16 16v-3a2 2 0 0 0-4 0"/>',
  phone: '<rect x="6" y="2" width="12" height="20" rx="4"/><path d="M11 18h2"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="4"/><circle cx="9" cy="10" r="2"/><path d="m21 16-5-5-9 9"/>',
  diverge: '<path d="M12 21v-7L5 4M12 14l7-10"/>',
  alert: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>',
  refresh: '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  plus: '<path d="M5 12h14M12 5v14"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
  offline: '<path d="M12 20h.01M8.5 16.43a5 5 0 0 1 7 0M2 8.82a15 15 0 0 1 4.18-2.64M22 8.82a15 15 0 0 0-11.29-3.76M5 12.86a10 10 0 0 1 5.17-2.69M19 12.86a10 10 0 0 0-2-1.52M2 2l20 20"/>',
  arrow: '<path d="M5 12h14M12 5l7 7-7 7"/>',
} as const;

export type IconName = keyof typeof P;

export const ICON_NAMES = Object.keys(P) as IconName[];

export type IconProps = Omit<SVGAttributes<SVGSVGElement>, "name" | "dangerouslySetInnerHTML"> & {
  name: IconName;
  size?: number | string;
  title?: string;
};

export function Icon({ name, size, strokeWidth = 2.5, title, style, ...rest }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={title ? undefined : true}
      role={title ? "img" : undefined}
      aria-label={title}
      style={size ? { width: size, height: size, ...style } : style}
      dangerouslySetInnerHTML={{ __html: P[name] }}
      {...rest}
    />
  );
}
