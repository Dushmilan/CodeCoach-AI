import { SubmitResponse } from "@/features/code-execution/code-execution.types";
import { RescueCheckpoint } from "./rescue.types";

interface FlowTestCase {
  input: string;
  expected_output: string;
  description?: string;
  hidden?: boolean;
}

/**
 * Build the "solution flow map" checkpoint list from a question's test cases
 * and the latest submit result.
 *
 * The map renders a vertical flowchart: "Run without error" at the top,
 * one checkpoint per visible test case, then "Hidden cases" leading to solved.
 * The first failing test becomes the "You are HERE" checkpoint; every test
 * before it is passed and everything after is upcoming.
 */
export function buildRescueCheckpoints(
  testCases: FlowTestCase[],
  lastSubmitResult: SubmitResponse | null,
): RescueCheckpoint[] {
  const checkpoints: RescueCheckpoint[] = [];

  const resultsByIndex = new Map(
    (lastSubmitResult?.results ?? []).map((r) => [r.index, r]),
  );
  const anyExecuted = (lastSubmitResult?.results.length ?? 0) > 0;

  checkpoints.push({
    id: "run",
    label: "Run without error",
    state: anyExecuted ? "passed" : "current",
  });

  let foundCurrent = false;
  const visiblePositions: number[] = [];
  testCases.forEach((tc, originalIndex) => {
    if (tc.hidden) return;
    const position = originalIndex + 1;
    visiblePositions.push(position);
    const result = resultsByIndex.get(position);
    if (result) {
      const passed = result.passed;
      if (!passed && !foundCurrent) {
        checkpoints.push({
          id: `test-${position}`,
          label: tc.description || `Test ${position}`,
          state: "current",
          detail: `Expected: ${result.expected} · Got: ${result.actual}`,
        });
        foundCurrent = true;
      } else {
        checkpoints.push({
          id: `test-${position}`,
          label: tc.description || `Test ${position}`,
          state: passed ? "passed" : "upcoming",
        });
      }
    } else {
      checkpoints.push({
        id: `test-${position}`,
        label: tc.description || `Test ${position}`,
        state: foundCurrent ? "upcoming" : "current",
      });
      if (!foundCurrent) foundCurrent = true;
    }
  });

  const allVisiblePassed =
    visiblePositions.length === 0 ||
    visiblePositions.every((pos) => resultsByIndex.get(pos)?.passed);

  checkpoints.push({
    id: "hidden",
    label: "Hidden cases → Solved",
    state: allVisiblePassed && anyExecuted ? "current" : "upcoming",
  });

  return checkpoints;
}
