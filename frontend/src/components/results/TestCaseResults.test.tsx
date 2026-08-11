import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TestCaseResults } from "./TestCaseResults";
import { TestCaseResultView } from "@/features/code-execution/code-execution.types";

const passing: TestCaseResultView = {
  index: 1,
  passed: true,
  testName: "Test 1",
  input: '"dlrow"',
  expected: '"world"',
  actual: "world",
  hidden: false,
};

const failing: TestCaseResultView = {
  index: 2,
  passed: false,
  testName: "Test 2",
  input: "5",
  expected: "6",
  actual: "5",
  hidden: false,
};

const errored: TestCaseResultView = {
  index: 3,
  passed: false,
  testName: "Test 3",
  input: "1",
  expected: "1",
  actual: "",
  error: "IndexError: list index out of range",
  hidden: false,
};

const hidden: TestCaseResultView = {
  index: 4,
  passed: false,
  testName: "Test 4",
  input: "",
  expected: "",
  actual: "",
  hidden: true,
};

describe("TestCaseResults", () => {
  it("renders a summary banner with pass/fail counts", () => {
    render(<TestCaseResults results={[passing, failing]} />);
    expect(
      screen.getByRole("status", { name: "1 of 2 tests passed" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Test Results: 1/2 passed · 1 failed")).toBeInTheDocument();
  });

  it("renders an all-pass summary banner", () => {
    render(<TestCaseResults results={[passing]} />);
    expect(
      screen.getByRole("status", { name: "1 of 1 tests passed" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Test Results: 1/1 passed")).toBeInTheDocument();
  });

  it("renders input, expected, and actual values per test card", () => {
    render(<TestCaseResults results={[passing, failing]} />);
    expect(screen.getByText("Test 1")).toBeInTheDocument();
    expect(screen.getByText("Test 2")).toBeInTheDocument();
    // Value cells for the failing case
    expect(screen.getAllByText("Input").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Expected").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Actual").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("5").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("6").length).toBeGreaterThanOrEqual(1);
  });

  it("shows an amber error card instead of pass/fail for execution errors", () => {
    render(<TestCaseResults results={[errored]} />);
    expect(screen.getAllByText("Error").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getByText("IndexError: list index out of range"),
    ).toBeInTheDocument();
  });

  it("marks hidden test cases without leaking input/expected/actual", () => {
    render(<TestCaseResults results={[hidden]} />);
    expect(screen.getByText("Hidden test case")).toBeInTheDocument();
    expect(screen.queryByText("Input")).not.toBeInTheDocument();
  });

  it("renders whitespace-sensitive values in whitespace-pre-wrap cells", () => {
    const whitespace: TestCaseResultView = {
      index: 1,
      passed: false,
      testName: "Test 1",
      input: '"123  "',
      expected: '"123  "',
      actual: "123",
      hidden: false,
    };
    render(<TestCaseResults results={[whitespace]} />);
    const pres = document.querySelectorAll("pre");
    const texts = Array.from(pres).map((p) => p.textContent || "");
    // whitespace is preserved in the value cells
    expect(texts.some((t) => t === '"123  "')).toBe(true);
    expect(texts.some((t) => t === "123")).toBe(true);
    // all value cells use whitespace-pre-wrap
    pres.forEach((p) => expect(p.className).toContain("whitespace-pre-wrap"));
    pres.forEach((p) => expect(p.className).toContain("font-mono"));
  });

  it("supports a custom title", () => {
    render(<TestCaseResults results={[passing]} title="Validation" />);
    expect(screen.getByText("Validation: 1/1 passed")).toBeInTheDocument();
  });
});
