import { describe, it, expect, vi, beforeEach } from "vitest";
import { CodeExecutionService } from "./code-execution.service";
import { HttpClient } from "@/lib/http-client";
import {
  CodeExecutionResult,
  SubmitResponse,
  TestCase,
} from "./code-execution.types";

function createMockHttp(): HttpClient {
  return {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  };
}

describe("CodeExecutionService", () => {
  let http: ReturnType<typeof createMockHttp>;
  let service: CodeExecutionService;

  beforeEach(() => {
    http = createMockHttp();
    service = new CodeExecutionService(http);
  });

  describe("runCode", () => {
    it("posts to /api/run/ with language, code, stdin, and version", async () => {
      const expected: CodeExecutionResult = {
        stdout: "Hello\n",
        stderr: "",
        exit_code: 0,
        runtime: 10,
      };
      vi.mocked(http.post).mockResolvedValue(expected);

      const result = await service.runCode(
        "python",
        'print("Hello")',
        "",
        "3.11.0",
      );

      expect(http.post).toHaveBeenCalledWith(
        "/api/run/",
        {
          language: "python",
          code: 'print("Hello")',
          stdin: "",
          version: "3.11.0",
        },
        { timeout: 45000 },
      );
      expect(result).toEqual(expected);
    });

    it("uses a 45s timeout so Piston slowness does not trip the 10s default", async () => {
      vi.mocked(http.post).mockResolvedValue({
        stdout: "",
        stderr: "",
        exit_code: 0,
      });

      await service.runCode("python", 'print("hi")');

      expect(http.post).toHaveBeenCalledWith(
        "/api/run/",
        expect.anything(),
        expect.objectContaining({ timeout: 45000 }),
      );
    });

    it("defaults stdin to empty string", async () => {
      vi.mocked(http.post).mockResolvedValue({
        stdout: "",
        stderr: "",
        exit_code: 0,
      });

      await service.runCode("python", 'print("hi")');

      expect(http.post).toHaveBeenCalledWith(
        "/api/run/",
        expect.objectContaining({ stdin: "" }),
        expect.objectContaining({ timeout: 45000 }),
      );
    });
  });

  describe("validateCode", () => {
    it("runs all test cases and returns validation response", async () => {
      const testCases: TestCase[] = [
        { input: "2", expected_output: "4" },
        { input: "3", expected_output: "9" },
      ];

      vi.mocked(http.post)
        .mockResolvedValueOnce({
          stdout: "4\n",
          stderr: "",
          exit_code: 0,
          runtime: 5,
        })
        .mockResolvedValueOnce({
          stdout: "8\n",
          stderr: "",
          exit_code: 0,
          runtime: 5,
        });

      const result = await service.validateCode(
        "python",
        "print(int(input())**2)",
        testCases,
      );

      expect(result.total_tests).toBe(2);
      expect(result.passed_tests).toBe(1);
      expect(result.results[0].passed).toBe(true);
      expect(result.results[1].passed).toBe(false);
    });

    it("runs test cases concurrently instead of sequentially", async () => {
      const testCases: TestCase[] = [
        { input: "1", expected_output: "1" },
        { input: "2", expected_output: "2" },
        { input: "3", expected_output: "3" },
      ];

      let resolveAll!: (v: unknown) => void;
      const gate = new Promise((resolve) => {
        resolveAll = resolve;
      });
      vi.mocked(http.post).mockImplementation(() => gate as Promise<never>);

      const pending = service.validateCode(
        "python",
        "print(input())",
        testCases,
      );
      // All three requests must be in flight before any resolves.
      await Promise.resolve();
      await Promise.resolve();
      expect(vi.mocked(http.post)).toHaveBeenCalledTimes(3);
      resolveAll({ stdout: "1\n", stderr: "", exit_code: 0 });
      const result = await pending;
      expect(result.total_tests).toBe(3);
    });

    it("handles execution errors gracefully", async () => {
      vi.mocked(http.post).mockRejectedValue(new Error("Piston unavailable"));

      const result = await service.validateCode("python", "bad code", [
        { input: "1", expected_output: "1" },
      ]);

      expect(result.total_tests).toBe(1);
      expect(result.passed_tests).toBe(0);
      expect(result.results[0].passed).toBe(false);
      expect(result.results[0].stderr).toContain("Piston unavailable");
    });
  });

  describe("submitCode", () => {
    it("posts to /api/submit/ with question_id, language, and code", async () => {
      const expected: SubmitResponse = {
        passed: true,
        total: 3,
        passed_count: 3,
        results: [
          {
            index: 1,
            passed: true,
            input: "1",
            expected: "1",
            actual: "1",
            hidden: false,
          },
          {
            index: 2,
            passed: true,
            input: "2",
            expected: "2",
            actual: "2",
            hidden: true,
          },
        ],
      };
      vi.mocked(http.post).mockResolvedValue(expected);

      const result = await service.submitCode(
        "two-sum",
        "python",
        "print(input())",
      );

      expect(http.post).toHaveBeenCalledWith(
        "/api/submit/",
        {
          question_id: "two-sum",
          language: "python",
          code: "print(input())",
        },
        { timeout: 60000 },
      );
      expect(result).toEqual(expected);
    });
  });
});
