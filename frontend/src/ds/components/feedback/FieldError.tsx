import type { ReactNode } from "react";
import { Icon } from "../icons/Icon";

export type FieldErrorProps = {
  children?: ReactNode;
  id?: string;
};

export function FieldError({ children, id }: FieldErrorProps) {
  return (
    <p className="eco-field-error" id={id}>
      <Icon name="alert" />
      {children}
    </p>
  );
}
