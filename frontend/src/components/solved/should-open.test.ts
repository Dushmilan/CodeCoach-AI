import { describe, it, expect } from "vitest";
import { shouldOpenSolvedOverlay } from "./should-open";

describe("shouldOpenSolvedOverlay", () => {
  it("opens on a full pass once per question", () => {
    expect(
      shouldOpenSolvedOverlay(
        { passed_count: 3, total: 3 },
        null,
        "q1",
      ),
    ).toBe(true);
  });

  it("stays closed on partial pass", () => {
    expect(
      shouldOpenSolvedOverlay({ passed_count: 1, total: 3 }, null, "q1"),
    ).toBe(false);
  });

  it("does not reopen after already shown for the question", () => {
    expect(
      shouldOpenSolvedOverlay({ passed_count: 3, total: 3 }, "q1", "q1"),
    ).toBe(false);
  });

  it("stays closed without a submit result", () => {
    expect(shouldOpenSolvedOverlay(null, null, "q1")).toBe(false);
  });
});
