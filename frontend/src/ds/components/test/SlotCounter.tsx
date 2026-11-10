export type SlotCounterProps = {
  used?: number;
  max?: number;
  showText?: boolean;
};

export function SlotCounter({ used = 2, max = 5, showText = true }: SlotCounterProps) {
  const left = max - used;
  return (
    <>
      <div className="eco-slots" role="img" aria-label={used + " varianti su " + max}>
        {Array.from({ length: max }, (_, i) => (
          <i key={i} className={"eco-slot" + (i < used ? " eco-slot--full" : "")} />
        ))}
      </div>
      {showText && (
        <div className="eco-count">
          {used} di {max}
          <small>
            {left > 0
              ? left === 1
                ? "puoi aggiungerne ancora 1"
                : "puoi aggiungerne altre " + left
              : "hai raggiunto il massimo"}
          </small>
        </div>
      )}
    </>
  );
}
