import { describe, expect, it } from "vitest";
import type { Response as PersonaResponse } from "../types/response";
import { countActions } from "./actions";

const r = (action?: PersonaResponse["action"], reaction?: PersonaResponse["reaction"]): PersonaResponse => ({
  persona_id: "p",
  stimulus_id: "s",
  thought: "",
  said: "",
  score: 3,
  objections: [],
  action,
  reaction,
});

describe("countActions", () => {
  it("counts actions in descending order with labels", () => {
    const out = countActions([r("scroll"), r("scroll"), r("comment"), r("share"), r("scroll"), r("comment")]);
    expect(out.map((a) => [a.label, a.count])).toEqual([
      ["Scorrerebbe oltre", 3],
      ["Commenterebbe", 2],
      ["Condividerebbe", 1],
      ["Metterebbe una reazione", 0],
    ]);
  });

  it("details the reaction types under react, most used first", () => {
    const out = countActions([
      r("react", "consiglio"),
      r("react", "perspicace"),
      r("react", "perspicace"),
      r("scroll"),
    ]);
    expect(out[0]).toEqual({
      action: "react",
      label: "Metterebbe una reazione",
      count: 3,
      detail: "Perspicace 2 · Consiglio 1",
    });
    expect(out[1].detail).toBeUndefined();
  });

  it("keeps the label order on ties", () => {
    expect(countActions([r("share"), r("react")]).map((a) => a.action)).toEqual(["react", "share", "scroll", "comment"]);
  });

  it("is empty when no response has an action", () => {
    expect(countActions([r(), r()])).toEqual([]);
    expect(countActions([])).toEqual([]);
  });
});
