import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useCodeExecution } from "./code-execution.hook";
import { HttpError } from "@/lib/fetch-client";
import { showToast } from "@/components/ui/Toast";
import { executeClientJS } from "@/lib/client-js-executor";

const mockRunCode = vi.fn();
const mockValidateCode = vi.fn();
const mockSubmitCode = vi.fn();

vi.mock("./code-execution.service", () => ({
  codeExecutionService: {
    runCode: (...args: unknown[]) => mockRunCode(...args),
    validateCode: (...args: unknown[]) => mockValidateCode(...args),
    submitCode: (...args: unknown[]) => mockSubmitCode(...args),
  },
}));

vi.mock("@/components/ui/Toast", () => ({
  showToast: vi.fn(),
}));

vi.mock("@/lib/client-js-executor", () => ({
  executeClientJS: vi.fn(),
  formatClientJsOutput: vi.fn(),
}));

describe("useCodeExecution", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with idle state", () => {
    const { result } = renderHook(() => useCodeExecution());
    expect(result.current.isRunning).toBe(false);
    expect(result.current.output).toBe("");
    expect(result.current.error).toBeNull();
    expect(result.current.lastResult).toBeNull();
  });

  it("runs code and sets output", async () => {
    mockRunCode.mockResolvedValue({
      stdout: "Hello World",
      stderr: "",
      exit_code: 0,
    });
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      await result.current.runCode("python", 'print("Hello World")');
    });

    expect(result.current.output).toBe("Hello World");
    expect(result.current.isRunning).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("sets error when runCode fails", async () => {
    mockRunCode.mockRejectedValue(new Error("Execution failed"));
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.runCode("python", "bad code");
      } catch {
        /* expected */
      }
    });

    expect(result.current.isRunning).toBe(false);
    expect(result.current.error).toBe("Execution failed");
  });

  it("clears output when clearOutput is called", () => {
    const { result } = renderHook(() => useCodeExecution());
    act(() => {
      result.current.clearOutput();
    });
    expect(result.current.output).toBe("");
  });

  it("clears error when clearError is called", () => {
    const { result } = renderHook(() => useCodeExecution());
    act(() => {
      result.current.clearError();
    });
    expect(result.current.error).toBeNull();
  });

  it("runCode surfaces server detail in inline error and toast", async () => {
    mockRunCode.mockRejectedValue(
      new HttpError(
        "Request failed: 400 Bad Request",
        400,
        JSON.stringify({ detail: "Piston runtime unavailable" }),
      ),
    );
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.runCode("python", "bad code");
      } catch {
        /* expected */
      }
    });

    expect(result.current.error).toBe("Piston runtime unavailable");
    expect(showToast).toHaveBeenCalledWith(
      "Piston runtime unavailable",
      "error",
    );
  });

  it("validateCode surfaces server detail in inline error and toast", async () => {
    mockValidateCode.mockRejectedValue(
      new HttpError(
        "Request failed: 500 Internal Server Error",
        500,
        JSON.stringify({ detail: "Piston execution timed out" }),
      ),
    );
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.validateCode("python", "code", [
          { input: "1", expected_output: "1" },
        ]);
      } catch {
        /* expected */
      }
    });

    expect(result.current.error).toBe("Piston execution timed out");
    expect(showToast).toHaveBeenCalledWith(
      "Piston execution timed out",
      "error",
    );
  });

  it("submitCode surfaces server detail in inline error and toast", async () => {
    mockSubmitCode.mockRejectedValue(
      new HttpError(
        "Request failed: 429 Too Many Requests",
        429,
        JSON.stringify({ detail: "Rate limit exceeded, try again later" }),
      ),
    );
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.submitCode("q1", "python", "code");
      } catch {
        /* expected */
      }
    });

    expect(result.current.error).toBe("Rate limit exceeded, try again later");
    expect(showToast).toHaveBeenCalledWith(
      "Rate limit exceeded, try again later",
      "error",
    );
  });

  it("runLocalJavaScript surfaces server detail in inline error and toast", async () => {
    vi.mocked(executeClientJS).mockRejectedValue(
      new HttpError(
        "Request failed: 400 Bad Request",
        400,
        JSON.stringify({ detail: "Unsupported language version" }),
      ),
    );
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.runLocalJavaScript("code", {
          id: "q1",
        } as never);
      } catch {
        /* expected */
      }
    });

    expect(result.current.error).toBe("Unsupported language version");
    expect(showToast).toHaveBeenCalledWith(
      "Unsupported language version",
      "error",
    );
  });

  it("runCode preserves fallback for non-Error rejections", async () => {
    mockRunCode.mockRejectedValue(null);
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.runCode("python", "bad code");
      } catch {
        /* expected */
      }
    });

    expect(result.current.error).toBe("Failed to run code");
    expect(showToast).toHaveBeenCalledWith("Failed to run code", "error");
  });
});
