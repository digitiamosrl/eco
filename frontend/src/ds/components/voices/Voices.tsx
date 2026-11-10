import type { ReactNode } from "react";
import { Said } from "./Said";
import { Thought } from "./Thought";

export type VoicesProps = {
  said?: ReactNode;
  thought?: ReactNode;
  diverge?: boolean;
  saidLabel?: string;
  thoughtLabel?: string;
};

export function Voices({ said, thought, diverge, saidLabel = "Cosa dicono", thoughtLabel = "Cosa pensano" }: VoicesProps) {
  return (
    <div className="eco-voices">
      <div>
        <div className="eco-voice-label">{saidLabel}</div>
        <Said>{said}</Said>
      </div>
      <div>
        <div className="eco-voice-label">{thoughtLabel}</div>
        <Thought diverge={diverge}>{thought}</Thought>
      </div>
    </div>
  );
}
