import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProblemFlowMap } from "./ProblemFlowMap";
import { buildRescueCheckpoints } from "@/features/rescue/rescue.checkpoints";
import { SubmitResponse } from "@/features/code-execution/code-execution.types";

const testCases = [
  { input: "1", expected_output: "2", description: "Sample A" },
  { input: "3", expected_output: "4", description: "Sample B" },
  { input: "5", expected_output: "6", hidden: true },
];

describe("ProblemFlowMap", () => {
  it("renders nothing when closed", () => {
    const { container } = render(
      <ProblemFlowMap
        open={false}
        checkpoints={buildRescueCheckpoints(testCases, null)}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders all checkpoint labels", () => {
    const checkpoints = buildRescueCheckpoints(testCases, null);
    render(<ProblemFlowMap checkpoints={checkpoints} />);
    expect(screen.getByText("Solution Flow Map")).toBeInTheDocument();
    expect(screen.getByText("Run without error")).toBeInTheDocument();
    expect(screen.getByText("Sample A")).toBeInTheDocument();
    expect(screen.getByText("Sample B")).toBeInTheDocument();
    expect(screen.getByText("Hidden cases → Solved")).toBeInTheDocument();
  });

  it("marks the first failing test as 'You are here'", () => {
    const submit: SubmitResponse = {
      passed: false,
      total: 2,
      passed_count: 1,
      results: [
        { index: 1, passed: true, input: "1", expected: "2", actual: "2", hidden: false },
        { index: 2, passed: false, input: "3", expected: "4", actual: "9", hidden: false },
      ],
    };
    const checkpoints = buildRescueCheckpoints(testCases, submit);
    render(<ProblemFlowMap checkpoints={checkpoints} />);
    // The second visible test is current and labelled "You are here"
    const here = screen.getByText("You are here").closest("div");
    expect(here?.textContent).toContain("Sample B");
    expect(screen.getByText(/Expected: 4 · Got: 9/)).toBeInTheDocument();
  });

  it("positions the map at hidden cases when all visible pass", () => {
    const submit: SubmitResponse = {
      passed: false,
      total: 3,
      passed_count: 2,
      results: [
        { index: 1, passed: true, input: "1", expected: "2", actual: "2", hidden: false },
        { index: 2, passed: true, input: "3", expected: "4", actual: "4", hidden: false },
        { index: 3, passed: false, input: "5", expected: "6", actual: "x", hidden: true },
      ],
    };
    const checkpoints = buildRescueCheckpoints(testCases, submit);
    const current = checkpoints.find((c) => c.state === "current");
    expect(current?.label).toBe("Hidden cases → Solved");
  });
});
