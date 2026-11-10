import { describe, expect, it } from "vitest";
import type { Prototype } from "../types/prototype";
import { buildPaths, screenKey, sourceError } from "./prototype";

const screens = (n: number) => Array.from({ length: n }, (_, index) => ({ index, name: `S${index}`, image_url: "" }));

const proto: Prototype = {
  id: "pr1",
  source: "figma",
  name: "Test",
  imported_at: "2026-10-22T10:00:00Z",
  starts: [
    { id: "s1", name: "Uno", screens: screens(4) },
    { id: "s2", name: "Due", screens: screens(2) },
    { id: "s3", name: "Tre", screens: screens(3) },
  ],
};

describe("buildPaths", () => {
  it("keeps every screen of the selected starts, in prototype order", () => {
    expect(buildPaths(proto, ["s3", "s1"], new Set())).toEqual([
      { start_id: "s1", screen_indexes: [0, 1, 2, 3] },
      { start_id: "s3", screen_indexes: [0, 1, 2] },
    ]);
  });

  it("leaves out removed screens", () => {
    const removed = new Set([screenKey("s1", 1), screenKey("s1", 3), screenKey("s2", 0)]);
    expect(buildPaths(proto, ["s1"], removed)).toEqual([{ start_id: "s1", screen_indexes: [0, 2] }]);
  });

  it("drops paths with no screens left", () => {
    const removed = new Set([screenKey("s2", 0), screenKey("s2", 1)]);
    expect(buildPaths(proto, ["s1", "s2"], removed).map((p) => p.start_id)).toEqual(["s1"]);
  });

  it("is empty with nothing selected", () => {
    expect(buildPaths(proto, [], new Set())).toEqual([]);
  });
});

describe("sourceError", () => {
  it("asks for the Figma link when empty", () => {
    expect(sourceError("figma", "  ")).toBe("Incolla il link del prototipo Figma.");
  });

  it("rejects links that are not Figma", () => {
    expect(sourceError("figma", "https://example.com/x")).toBe(
      "Questo non sembra un link Figma. In Figma: Condividi › Copia link al prototipo.",
    );
  });

  it("accepts proto, design and file links", () => {
    for (const kind of ["proto", "design", "file"])
      expect(sourceError("figma", `https://www.figma.com/${kind}/abc/Nome`)).toBeNull();
  });

  it("needs a link or a file for the artifact", () => {
    expect(sourceError("artifact", "")).toBe("Incolla il link dell’artifact oppure carica il file HTML.");
    expect(sourceError("artifact", "", true)).toBeNull();
    expect(sourceError("artifact", "https://claude.ai/public/artifacts/x")).toBeNull();
  });
});
