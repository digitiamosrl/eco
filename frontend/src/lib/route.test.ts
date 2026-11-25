import { describe, expect, it } from "vitest";
import { parseRoute, routeHref } from "./route";

describe("parseRoute", () => {
  it("reads every page", () => {
    expect(parseRoute("")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/panel")).toEqual({ page: "panel" });
    expect(parseRoute("#/test/nuovo")).toEqual({ page: "new-test" });
    expect(parseRoute("#/test/abc123")).toEqual({ page: "test", id: "abc123" });
  });
  it("sends unknown addresses to the dashboard", () => {
    expect(parseRoute("#/report")).toEqual({ page: "dashboard" });
    expect(parseRoute("#/test/")).toEqual({ page: "dashboard" });
  });
  it("round-trips", () => {
    expect(parseRoute(routeHref({ page: "test", id: "t9" }))).toEqual({ page: "test", id: "t9" });
  });
});
