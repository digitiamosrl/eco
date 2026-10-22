import { cx } from "../../cx";

export type RankMedalProps = {
  rank?: number;
  size?: "sm" | "md";
};

export function RankMedal({ rank = 1, size = "md" }: RankMedalProps) {
  return (
    <span
      className={cx(
        "eco-medal",
        rank === 2 && "eco-medal--second",
        rank !== 1 && rank !== 2 && "eco-medal--other",
        size === "sm" && "eco-medal--sm",
      )}
      aria-label={"Posizione " + rank}
    >
      #{rank}
    </span>
  );
}
