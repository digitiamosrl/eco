import { describe, expect, it } from "vitest";
import { diverges } from "./diverge";

describe("diverges", () => {
  it("is true when said and thought differ", () => {
    expect(diverges("Tema importante.", "Il solito post.")).toBe(true);
  });

  it("is false when said is empty", () => {
    expect(diverges("   ", "Non ho capito cosa vendono.")).toBe(false);
  });

  it("ignores spaces and case", () => {
    expect(diverges("  Lo giro  al TEAM.", "lo giro al team.")).toBe(false);
  });
});
