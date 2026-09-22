import { HttpClient } from "@/lib/http-client";
import { FetchClient } from "@/lib/fetch-client";
import {
  CodeExecutionResult,
  SubmitResponse,
  TestCase,
  TestResult,
  ValidationResponse,
} from "./code-execution.types";

export class CodeExecutionService {
  constructor(private http: HttpClient) {}

  async runCode(
    language: string,
    code: string,
    stdin?: string,
    version?: string,
    questionId?: string,
  ): Promise<CodeExecutionResult> {
    return this.http.post<CodeExecutionResult>(
      "/api/run/",
      {
        language,
        code,
        stdin: stdin || "",
        version,
        // Question context is informational only — free runs are Redis-only
        // (#264) and never persist, so this cannot leak an attempt.
        question_id: questionId,
      },
      // Piston execution + cold-start latency exceeds the client's 10s
      // default; the backend is Redis-only so 45s is pure execution budget.
      { timeout: 45000 },
    );
  }

  async validateCode(
    language: string,
    code: string,
    testCases: TestCase[],
    questionId?: string,
  ): Promise<ValidationResponse> {
    // One request per case, all in flight at once (#264): the backend is
    // Redis-only so each call is ~Piston latency, and sequential awaits
    // multiplied that by N (the reported 35s for 3 cases).
    const settled = await Promise.all(
      testCases.map(async (tc) => {
        try {
          const execResult = await this.runCode(
            language,
            code,
            tc.input,
            undefined,
            questionId,
          );
          return { ok: true as const, execResult };
        } catch (err) {
          return { ok: false as const, err };
        }
      }),
    );

    const results: TestResult[] = [];
    let passedCount = 0;
    settled.forEach((s, i) => {
      const tc = testCases[i];
      if (!s.ok) {
        results.push({
          test_name: tc.description || `Test ${results.length + 1}`,
          passed: false,
          stdout: "",
          stderr:
            s.err instanceof Error ? s.err.message : "Execution failed",
        });
        return;
      }
      const actual = (s.execResult.stdout || "").trim();
      const expected = tc.expected_output.trim();
      const isPassed = compareJson(actual, expected);
      if (isPassed) passedCount++;
      results.push({
        test_name: tc.description || `Test ${results.length + 1}`,
        passed: isPassed,
        stdout: s.execResult.stdout || "",
        stderr: s.execResult.stderr || "",
      });
    });

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
  ): Promise<SubmitResponse> {
    return this.http.post<SubmitResponse>(
      "/api/submit/",
      {
        question_id: questionId,
        language,
        code,
      },
      // Grading runs the full suite server-side plus Postgres persists;
      // allowed to be slow, must never trip the client's 10s default.
      { timeout: 60000 },
    );
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
