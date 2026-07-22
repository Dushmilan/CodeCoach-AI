import { describe, it, expect } from "vitest";
import { executeClientJS, formatClientJsOutput } from "./client-js-executor";
import { Question } from "@/types";

const passingCode = `function add(a, b) {
  return a + b;
}`;

const failingCode = `function add(a, b) {
  return a - b;
}`;

const errorCode = `function add(a, b) {
  throw new Error('runtime failure');
}`;

const question: Question = {
  id: "1",
  title: "Add",
  difficulty: "easy",
  category: "math",
  company_tags: [],
  description: "Add two numbers.",
  starter: { python: "", javascript: "function add(a, b) {}", java: "" },
  examples: [{ input: "1,2", output: "3" }],
  test_cases: [
    { input: "1\n2", expected_output: "3" },
    { input: "10\n20", expected_output: "30" },
    { input: "-1\n1", expected_output: "0" },
  ],
  hints: [],
  solution: "",
  time_complexity: "O(1)",
  space_complexity: "O(1)",
};

const questionWithVarStarter: Question = {
  ...question,
  starter: { python: "", javascript: "var add = function(a, b) {}", java: "" },
};

const questionWithConstStarter: Question = {
  ...question,
  starter: { python: "", javascript: "const add = (a, b) => {}", java: "" },
};

describe("executeClientJS", () => {
  it("returns allPassed=true when all tests pass", () => {
    const result = executeClientJS(passingCode, question);
    expect(result.allPassed).toBe(true);
    expect(result.results).toHaveLength(3);
    for (const r of result.results) {
      expect(r.passed).toBe(true);
    }
  });

  it("returns allPassed=false when tests fail", () => {
    const result = executeClientJS(failingCode, question);
    expect(result.allPassed).toBe(false);
    expect(result.results[0].passed).toBe(false);
  });

  it("captures console output in logs", () => {
    const code = `function add(a, b) {
      console.log('adding', a, b);
      return a + b;
    }`;
    const result = executeClientJS(code, question);
    expect(result.logs.length).toBeGreaterThan(0);
    expect(result.logs.some((l) => l.includes("adding"))).toBe(true);
  });

  it("handles runtime errors in user code", () => {
    const result = executeClientJS(errorCode, question);
    expect(result.results[0].error).toBe("runtime failure");
    expect(result.results[0].passed).toBe(false);
  });

  it("throws when function name cannot be determined", () => {
    const noFnQuestion: Question = {
      ...question,
      starter: { python: "", javascript: "", java: "" },
    };
    expect(() => executeClientJS("const x = 42;", noFnQuestion)).toThrow(
      "Could not identify the target function name",
    );
  });

  it("detects function name from starter with var pattern", () => {
    const result = executeClientJS(passingCode, questionWithVarStarter);
    expect(result.allPassed).toBe(true);
  });

  it("detects function name from starter with const pattern", () => {
    const result = executeClientJS(passingCode, questionWithConstStarter);
    expect(result.allPassed).toBe(true);
  });

  it("restores console.log after execution", () => {
    const originalLog = console.log;
    executeClientJS(passingCode, question);
    expect(console.log).toBe(originalLog);
  });

  it("restores console.error after execution", () => {
    const originalError = console.error;
    executeClientJS(passingCode, question);
    expect(console.error).toBe(originalError);
  });

  it("restores console.warn after execution", () => {
    const originalWarn = console.warn;
    executeClientJS(passingCode, question);
    expect(console.warn).toBe(originalWarn);
  });

  it("handles non-JSON expected_output gracefully", () => {
    const strQuestion: Question = {
      ...question,
      test_cases: [{ input: '"world"', expected_output: "Hello, world" }],
      starter: { python: "", javascript: "function greet(name) {}", java: "" },
    };
    const code = `function greet(name) { return "Hello, " + name; }`;
    const result = executeClientJS(code, strQuestion);
    // Should not throw on JSON.parse("Hello, world") — falls back to string comparison
    expect(result.results[0].passed).toBe(true);
  });

  it("handles expected_output that is a non-JSON string", () => {
    const strQuestion: Question = {
      ...question,
      test_cases: [{ input: "5", expected_output: "not a json string" }],
      starter: { python: "", javascript: "function foo(x) {}", java: "" },
    };
    const code = `function foo(x) { return "not a json string"; }`;
    const result = executeClientJS(code, strQuestion);
    expect(result.results[0].passed).toBe(true);
  });

  it("handles in-place (void) function that returns undefined", () => {
    const rotateQuestion: Question = {
      ...question,
      test_cases: [
        { input: "[[1,2],[3,4]]", expected_output: "[[3,1],[4,2]]" },
        { input: "[[1]]", expected_output: "[[1]]" },
      ],
      starter: {
        python: "",
        javascript: "function rotate(matrix) {}",
        java: "",
      },
    };
    const code = `function rotate(matrix) {
      for (let i = 0; i < matrix.length; i++) {
        for (let j = i + 1; j < matrix[i].length; j++) {
          [matrix[i][j], matrix[j][i]] = [matrix[j][i], matrix[i][j]];
        }
      }
      for (let i = 0; i < matrix.length; i++) {
        matrix[i].reverse();
      }
    }`;
    const result = executeClientJS(code, rotateQuestion);
    expect(result.results[0].passed).toBe(true);
    expect(result.results[1].passed).toBe(true);
    expect(result.allPassed).toBe(true);
  });

  it("uses parsedArgs[0] as actual when function returns undefined", () => {
    const mutateQuestion: Question = {
      ...question,
      test_cases: [{ input: "[1,2,3]", expected_output: "[1,2,3,4]" }],
      starter: { python: "", javascript: "function push(arr) {}", java: "" },
    };
    const code = `function push(arr) {
      arr.push(4);
    }`;
    const result = executeClientJS(code, mutateQuestion);
    expect(result.results[0].actual).toEqual([1, 2, 3, 4]);
  });
});

describe("formatClientJsOutput", () => {
  it("includes console output when logs exist", () => {
    const output = {
      logs: ["hello", "world"],
      results: [
        { index: 1, passed: true, input: "1", expected: "3", actual: 3 },
      ],
      allPassed: true,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain("Console Output");
    expect(formatted).toContain("hello");
  });

  it("formats test results with pass/fail status", () => {
    const output = {
      logs: [],
      results: [
        { index: 1, passed: true, input: "1", expected: "3", actual: 3 },
        { index: 2, passed: false, input: "2", expected: "4", actual: 2 },
      ],
      allPassed: false,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain("✅");
    expect(formatted).toContain("❌");
    expect(formatted).toContain("Test Case 1");
    expect(formatted).toContain("Test Case 2");
  });

  it("includes error message when result has error", () => {
    const output = {
      logs: [],
      results: [
        {
          index: 1,
          passed: false,
          input: "1",
          expected: "3",
          actual: null,
          error: "something broke",
        },
      ],
      allPassed: false,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain("something broke");
  });

  it("includes test labels", () => {
    const output = {
      logs: [],
      results: [
        { index: 1, passed: true, input: "1", expected: "3", actual: 3 },
      ],
      allPassed: true,
    };
    const formatted = formatClientJsOutput(output, question);
    expect(formatted).toContain("Test Results");
    expect(formatted).toContain("Input:");
    expect(formatted).toContain("Expected Output:");
    expect(formatted).toContain("Actual Output:");
  });
});
