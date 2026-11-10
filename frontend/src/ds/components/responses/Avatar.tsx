export type AvatarProps = {
  code?: string;
  size?: "md" | "sm";
};

export function Avatar({ code, size = "md" }: AvatarProps) {
  return (
    <span className={"eco-ava" + (size === "sm" ? " eco-ava--sm" : "")} aria-hidden="true">
      {code}
    </span>
  );
}
