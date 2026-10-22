import { Card } from "../surfaces/Card";
import { Icon } from "../icons/Icon";
import { cx } from "../../cx";

export type FlowOptionProps = {
  name?: string;
  screens?: number;
  capturedAt?: string;
  selected?: boolean;
  onToggle?: () => void;
  thumbs?: string[];
};

export function FlowOption({ name, screens, capturedAt, selected, onToggle, thumbs }: FlowOptionProps) {
  const n = Math.min(screens || 0, 4);
  return (
    <Card as="label" pad="none" className={cx("eco-flow", selected && "eco-flow--on")}>
      <input type="checkbox" checked={!!selected} onChange={() => onToggle && onToggle()} />
      <div className="eco-flow__shots" aria-hidden="true">
        {Array.from({ length: n }, (_, i) => (
          <span
            key={i}
            className="eco-flow__shot"
            style={thumbs && thumbs[i] ? { backgroundImage: "url(" + thumbs[i] + ")", backgroundSize: "cover" } : undefined}
          />
        ))}
      </div>
      <div className="eco-flow__top">
        <div>
          <h3>{name}</h3>
          <div className="eco-flow__meta">
            {screens} schermate · catturato il {capturedAt}
          </div>
        </div>
        <span className="eco-flow__check">
          <Icon name="check" strokeWidth={3.5} />
        </span>
      </div>
    </Card>
  );
}
