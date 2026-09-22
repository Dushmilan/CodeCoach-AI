import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import {
  CodeExecutionResult,
  SubmitResponse,
  TestCase,
  TestResult,
  ValidationResponse,
} from "./code-execution.types";

/** Client surface: questions persist attempts + moat writes, learn does not. */
export type ExecutionSurface = "questions" | "learn";

export class CodeExecutionService {
  constructor(private http: HttpClient) {}

  async runCode(
    language: string,
    code: string,
    stdin?: string,
    version?: string,
    questionId?: string,
    surface?: ExecutionSurface,
  ): Promise<CodeExecutionResult> {
    return this.http.post<CodeExecutionResult>("/api/run/", {
      language,
      code,
      stdin: stdin || "",
      version,
      // Question context enables mistake-memory capture of crashed runs.
      question_id: questionId,
      // Learn practice executes without persisting moat data.
      ...(surface ? { surface } : {}),
    });
  }

  async validateCode(
    language: string,
    code: string,
    testCases: TestCase[],
    questionId?: string,
    surface?: ExecutionSurface,
  ): Promise<ValidationResponse> {
    const results: TestResult[] = [];
    let passedCount = 0;

    for (const tc of testCases) {
      try {
        const execResult = await this.runCode(
          language,
          code,
          tc.input,
          undefined,
          questionId,
          surface,
        );
        const actual = (execResult.stdout || "").trim();
        const expected = tc.expected_output.trim();
        const isPassed = compareJson(actual, expected);
        if (isPassed) passedCount++;
        results.push({
          test_name: tc.description || `Test ${results.length + 1}`,
          passed: isPassed,
          stdout: execResult.stdout || "",
          stderr: execResult.stderr || "",
        });
      } catch (err) {
        results.push({
          test_name: tc.description || `Test ${results.length + 1}`,
          passed: false,
          stdout: "",
          stderr: err instanceof Error ? err.message : "Execution failed",
        });
      }
    }

    return {
      total_tests: testCases.length,
      passed_tests: passedCount,
      success_rate: testCases.length > 0 ? passedCount / testCases.length : 0,
      results,
      formatted_output: "",
    };
  }

  async submitCode(
    questionId: string,
    language: string,
    code: string,
    surface?: ExecutionSurface,
  ): Promise<SubmitResponse> {
    return this.http.post<SubmitResponse>("/api/submit/", {
      question_id: questionId,
      language,
      code,
      // Learn practice grades without persisting moat data.
      ...(surface ? { surface } : {}),
    });
  }
}

function compareJson(a: string, b: string): boolean {
  try {
    return JSON.stringify(JSON.parse(a)) === JSON.stringify(JSON.parse(b));
  } catch {
    return a === b;
  }
}

export const codeExecutionService = new CodeExecutionService(new FetchClient());
