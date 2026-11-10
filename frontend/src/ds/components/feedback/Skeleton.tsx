import type { CSSProperties } from "react";

export type SkeletonProps = {
  shape?: "line" | "title" | "block" | "circle";
  width?: CSSProperties["width"];
  height?: CSSProperties["height"];
  style?: CSSProperties;
};

export function Skeleton({ shape = "line", width = "100%", height, style }: SkeletonProps) {
  return <span className={"eco-skel eco-skel--" + shape} aria-hidden="true" style={{ width, height, ...style }} />;
}
