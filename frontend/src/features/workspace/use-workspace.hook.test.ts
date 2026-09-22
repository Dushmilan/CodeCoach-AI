import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import React from "react";
import { AuthContext } from "@/providers/AuthProvider";
import { useWorkspace } from "./use-workspace.hook";
import { workspaceService } from "./workspace.service";

vi.mock("./workspace.service", () => ({
  workspaceService: {
    getCode: vi.fn(),
    saveCode: vi.fn(),
    deleteCode: vi.fn(),
    getChat: vi.fn(),
    clearChat: vi.fn(),
  },
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(
    AuthContext.Provider,
    {
      value: {
        isAuthenticated: true,
        isHydrated: true,
        user: { id: "u1", username: "stu" },
      } as never,
    },
    children,
  );
}

describe("useWorkspace draft hydration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.getChat).mockResolvedValue({
      question_id: "q1",
      messages: [],
    });
  });

  it("applies the persisted draft and reports hasDraft", async () => {
    vi.mocked(workspaceService.getCode).mockResolvedValue({
      code: "draft-code",
      language: "python",
      updated_at: "now",
      question_id: "q1",
    });
    const setCurrentCode = vi.fn();

    const { result } = renderHook(
      () =>
        useWorkspace({
          questionId: "q1",
          language: "python",
          currentCode: "",
          setCurrentCode,
        }),
      { wrapper },
    );

    await waitFor(() =>
      expect(workspaceService.getCode).toHaveBeenCalledWith("q1", "python"),
    );
    await waitFor(() => expect(setCurrentCode).toHaveBeenCalledWith("draft-code"));
    expect(result.current.hasDraft).toBe(true);
  });

  it("reports no draft when the workspace is empty", async () => {
    vi.mocked(workspaceService.getCode).mockResolvedValue({
      code: "",
      language: "python",
      updated_at: null,
      question_id: "q1",
    });
    const setCurrentCode = vi.fn();

    const { result } = renderHook(
      () =>
        useWorkspace({
          questionId: "q1",
          language: "python",
          currentCode: "",
          setCurrentCode,
        }),
      { wrapper },
    );

    await waitFor(() =>
      expect(workspaceService.getCode).toHaveBeenCalledWith("q1", "python"),
    );
    await waitFor(() => expect(result.current.hasDraft).toBe(false));
  });

  it("deleteDraft clears the draft flag", async () => {
    vi.mocked(workspaceService.getCode).mockResolvedValue({
      code: "draft-code",
      language: "python",
      updated_at: "now",
      question_id: "q1",
    });
    vi.mocked(workspaceService.deleteCode).mockResolvedValue(undefined);
    const setCurrentCode = vi.fn();

    const { result } = renderHook(
      () =>
        useWorkspace({
          questionId: "q1",
          language: "python",
          currentCode: "draft-code",
          setCurrentCode,
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.hasDraft).toBe(true));
    await act(async () => {
      await result.current.deleteDraft();
    });
    expect(result.current.hasDraft).toBe(false);
  });
});
