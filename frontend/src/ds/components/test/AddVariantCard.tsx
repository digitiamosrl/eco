import { Button } from "../actions/Button";
import { Card } from "../surfaces/Card";
import { SlotCounter } from "./SlotCounter";

export type AddVariantCardProps = {
  used?: number;
  max?: number;
  onAdd?: () => void;
};

export function AddVariantCard({ used = 2, max = 5, onAdd }: AddVariantCardProps) {
  return (
    <Card variant="dashed" pad="none" className="eco-add">
      <SlotCounter used={used} max={max} />
      <Button variant="light" onClick={onAdd} disabled={used >= max}>
        + Aggiungi variante
      </Button>
    </Card>
  );
}
