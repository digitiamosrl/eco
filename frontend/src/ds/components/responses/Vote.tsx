export type VoteProps = {
  score: number;
  caption?: boolean;
};

export function Vote({ score, caption = true }: VoteProps) {
  return (
    <>
      <span className={"eco-vote" + (score >= 4 ? " eco-vote--hi" : "")} aria-label={"Voto " + score + " su 5"}>
        {score}
      </span>
      {caption && (
        <span className="eco-vote-cap" aria-hidden="true">
          su 5
        </span>
      )}
    </>
  );
}
