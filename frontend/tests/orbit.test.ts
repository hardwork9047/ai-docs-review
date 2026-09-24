import { describe, expect, it } from "vitest";

import { orbitPosition, wrapAngle } from "../src/logic/orbit";

describe("wrapAngle", () => {
  it("returns angles in [0, 2π) unchanged", () => {
    expect(wrapAngle(1.5)).toBeCloseTo(1.5);
  });

  it("wraps angles above 2π", () => {
    expect(wrapAngle(Math.PI * 2 + 0.5)).toBeCloseTo(0.5);
  });

  it("wraps negative angles into positive range", () => {
    expect(wrapAngle(-Math.PI / 2)).toBeCloseTo((Math.PI * 3) / 2);
  });
});

describe("orbitPosition", () => {
  it("starts on the +X axis at t=0", () => {
    const pos = orbitPosition(2, 1, 0);
    expect(pos.x).toBeCloseTo(2);
    expect(pos.y).toBe(0);
    expect(pos.z).toBeCloseTo(0);
  });

  it("reaches the +Z axis after a quarter turn", () => {
    const pos = orbitPosition(2, Math.PI / 2, 1);
    expect(pos.x).toBeCloseTo(0);
    expect(pos.z).toBeCloseTo(2);
  });

  it("throws on negative radius", () => {
    expect(() => orbitPosition(-1, 1, 0)).toThrow(RangeError);
  });
});
