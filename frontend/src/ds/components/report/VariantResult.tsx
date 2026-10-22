import type { ReactNode } from "react";
import { Card } from "../surfaces/Card";
import { Voices } from "../voices/Voices";
import { Objection } from "./Objection";
import { RankMedal } from "./RankMedal";
import { ScoreBlock, type ScoreBlockProps } from "./ScoreBlock";

export type VariantResultProps = {
  rank?: number;
  name?: ReactNode;
  quote?: ReactNode;
  mean?: ScoreBlockProps["mean"];
  distribution?: ScoreBlockProps["distribution"];
  objections?: string[];
  said?: ReactNode;
  thought?: ReactNode;
};

export function VariantResult({ rank, name, quote, mean, distribution, objections = [], said, thought }: VariantResultProps) {
  const win = rank === 1;
  return (
    <Card as="article" variant={win ? "winner" : "standard"} pad="lg">
      <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
        <RankMedal rank={rank} />
        <h2 style={{ fontSize: 30 }}>{name}</h2>
        {quote && (
          <p
            style={{
              flexBasis: "100%",
              margin: 0,
              fontSize: 15,
              color: "var(--muted)",
              fontWeight: 600,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            «{quote}»
          </p>
        )}
      </div>
      <div style={{ margin: "24px 0" }}>
        <ScoreBlock mean={mean} distribution={distribution} tone={win ? "primary" : "secondary"} />
      </div>
      {objections.length > 0 && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 20 }}>
          {objections.map((o) => (
            <Objection key={o}>{o}</Objection>
          ))}
        </div>
      )}
      <Voices said={said} thought={thought} />
    </Card>
  );
}
