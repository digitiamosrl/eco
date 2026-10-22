import type { ReactNode } from "react";

export type SimulatedNoticeProps = {
  children?: ReactNode;
};

export function SimulatedNotice({ children }: SimulatedNoticeProps) {
  return (
    <div className="eco-notice" role="note">
      <span className="eco-notice__badge" aria-hidden="true">
        i
      </span>
      <span>
        {children || (
          <>
            <b>Risultati simulati.</b> Reazioni di personas sintetiche, non di persone reali. Usali per confrontare
            varianti, non come previsione.
          </>
        )}
      </span>
    </div>
  );
}
