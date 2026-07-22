import { describe, it, expect } from "vitest";
import { seededShuffle, getDailySeed } from "./shuffle";

describe("seededShuffle", () => {
  it("shuffles array deterministically with numeric seed", () => {
    const input = [1, 2, 3, 4, 5];
    const result1 = seededShuffle(input, 42);
    const result2 = seededShuffle(input, 42);
    expect(result1).toEqual(result2);
  });

  it("produces different result with different seeds", () => {
    const input = [1, 2, 3, 4, 5];
    const result1 = seededShuffle(input, 42);
    const result2 = seededShuffle(input, 99);
    expect(result1).not.toEqual(result2);
  });

  it("does not mutate the original array", () => {
    const input = [1, 2, 3, 4, 5];
    const copy = [...input];
    seededShuffle(input, 42);
    expect(input).toEqual(copy);
  });

  it("preserves all elements", () => {
    const input = [1, 2, 3, 4, 5];
    const result = seededShuffle(input, 42);
    expect(result.sort()).toEqual(input.sort());
  });

  it("works with string arrays", () => {
    const input = ["a", "b", "c", "d"];
    const result = seededShuffle(input, "seed");
    expect(result).toHaveLength(4);
    expect(result.sort()).toEqual(input.sort());
  });

  it("works with empty arrays", () => {
    expect(seededShuffle([], 42)).toEqual([]);
  });

  it("works with single-element arrays", () => {
    expect(seededShuffle([1], 42)).toEqual([1]);
  });
});

describe("getDailySeed", () => {
  it("returns a date-formatted string", () => {
    const seed = getDailySeed();
    expect(seed).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it("returns consistent seeds on the same day", () => {
    const seed1 = getDailySeed();
    const seed2 = getDailySeed();
    expect(seed1).toBe(seed2);
  });
});
