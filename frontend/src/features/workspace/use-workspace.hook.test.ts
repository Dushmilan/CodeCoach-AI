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

describe("useWorkspace chat hydration", () => {
  const messages: {
    role: "user" | "assistant";
    content: string;
    structured?: unknown;
    timestamp: string;
  }[] = [
    {
      role: "assistant",
      content: "Seeded coach reply",
      structured: { summary: "Seeded coach reply" },
      timestamp: "2026-09-23T00:00:00+00:00",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.getCode).mockResolvedValue({
      code: "",
      language: "python",
      updated_at: null,
      question_id: "q1",
    });
  });

  it("hydrates chat when the parent re-renders mid-flight (#284)", async () => {
    // #284 browser verification: pages pass an inline onHydrateChat arrow, so
    // every parent re-render creates a new callback identity. Chat hydration
    // must still land — the animation dual-pane lives in the hydrated history.
    let resolveGetChat!: (value: {
      question_id: string;
      messages: typeof messages;
    }) => void;
    vi.mocked(workspaceService.getChat).mockReturnValue(
      new Promise((resolve) => {
        resolveGetChat = resolve;
      }),
    );
    const setCurrentCode = vi.fn();
    const onHydrateA = vi.fn();
    const onHydrateB = vi.fn();
    const onHydrateC = vi.fn();

    const { rerender } = renderHook(
      ({ onHydrate }: { onHydrate: (m: typeof messages) => void }) =>
        useWorkspace({
          questionId: "q1",
          language: "python",
          currentCode: "",
          setCurrentCode,
          onHydrateChat: onHydrate,
        }),
      { wrapper, initialProps: { onHydrate: onHydrateA } },
    );

    await waitFor(() =>
      expect(workspaceService.getChat).toHaveBeenCalledWith("q1"),
    );
    // Parent re-renders with fresh callback identities while getChat is
    // pending — the page's inline arrow does this on every render.
    rerender({ onHydrate: onHydrateB });
    rerender({ onHydrate: onHydrateC });
    resolveGetChat({ question_id: "q1", messages });

    await waitFor(() => expect(onHydrateC).toHaveBeenCalledWith(messages));
    // One-shot dedupe must survive: no second fetch for the same key.
    expect(workspaceService.getChat).toHaveBeenCalledTimes(1);
  });

  it("does not hydrate a stale question's chat after the key changes", async () => {
    let resolveFirst!: (value: {
      question_id: string;
      messages: typeof messages;
    }) => void;
    vi.mocked(workspaceService.getChat).mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFirst = resolve;
      }),
    );
    const setCurrentCode = vi.fn();
    const onHydrate = vi.fn();

    const { rerender } = renderHook(
      ({ questionId }: { questionId: string }) =>
        useWorkspace({
          questionId,
          language: "python",
          currentCode: "",
          setCurrentCode,
          onHydrateChat: onHydrate,
        }),
      { wrapper, initialProps: { questionId: "q1" } },
    );
    await waitFor(() =>
      expect(workspaceService.getChat).toHaveBeenCalledWith("q1"),
    );
    // The user navigates before the response lands: q1's history must be
    // dropped, never painted into q2's panel.
    vi.mocked(workspaceService.getChat).mockResolvedValue({
      question_id: "q2",
      messages: [],
    });
    rerender({ questionId: "q2" });
    resolveFirst({ question_id: "q1", messages });

    await waitFor(() =>
      expect(workspaceService.getChat).toHaveBeenCalledWith("q2"),
    );
    expect(onHydrate).not.toHaveBeenCalled();
  });
});
