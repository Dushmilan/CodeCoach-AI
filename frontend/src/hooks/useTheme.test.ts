import { describe, it, expect, vi } from "vitest";
import { useTheme } from "./useTheme";

vi.mock("@/providers/ThemeProvider", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

describe("useTheme", () => {
  it("returns theme object with current theme", () => {
    const result = useTheme();
    expect(result).toHaveProperty("theme");
    expect(result).toHaveProperty("setTheme");
  });

  it("returns dark theme", () => {
    const result = useTheme();
    expect(result.theme).toBe("dark");
  });
});
