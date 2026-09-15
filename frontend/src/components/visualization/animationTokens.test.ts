import { describe, it, expect } from "vitest";
import { TOKENS } from "./animationTokens";

describe("animationTokens", () => {
  it("mirrors backend palette and camera", () => {
    expect(TOKENS.palette.highlight_fill).toBe("#1d4ed8");
    expect(TOKENS.camera.zoom_focus).toBe(1.25);
    expect(TOKENS.camera.zoom_full).toBe(1.0);
    expect(TOKENS.duration.highlight).toBe(0.35);
  });
});
