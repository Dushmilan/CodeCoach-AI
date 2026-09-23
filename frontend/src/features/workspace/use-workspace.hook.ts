"use client";

import { useCallback, useContext, useEffect, useRef, useState } from "react";
import { Language } from "@/types";
import { AuthContext } from "@/providers/AuthProvider";
import { workspaceService } from "./workspace.service";

interface UseWorkspaceOptions {
  questionId: string | null;
  language: Language;
  currentCode: string;
  setCurrentCode: (code: string) => void;
  onHydrateChat?: (messages: { role: "user" | "assistant"; content: string; structured?: unknown; timestamp: string }[]) => void;
}

/**
 * Hydrates draft code from Redis and debounces saves.
 * No-op when unauthenticated (per spec).
 */
export function useWorkspace({
  questionId,
  language,
  currentCode,
  setCurrentCode,
  onHydrateChat,
}: UseWorkspaceOptions) {
  const auth = useContext(AuthContext);
  const isAuthenticated = auth?.isAuthenticated ?? false;

  const hydratedRef = useRef<string | null>(null);
  const lastSavedRef = useRef<string>("");
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Pages pass an inline onHydrateChat arrow whose identity changes every
  // render. Keep it in a ref so the one-shot hydration below never re-runs
  // (or cancels its in-flight getChat) on a mere callback identity change —
  // the animation dual-pane (#284) lives in that hydrated history.
  const onHydrateChatRef = useRef(onHydrateChat);
  // True once a persisted draft was applied for the current key. Pages use
  // this so starter code never clobbers a hydrated draft on re-render.
  const [hasDraft, setHasDraft] = useState(false);

  useEffect(() => {
    onHydrateChatRef.current = onHydrateChat;
  });

  // Reset the guard BEFORE the hydration effect runs in the same commit, so
  // the key it sets is never wiped (which would defeat the one-shot dedupe
  // and let every later render re-fetch). A question change still resets.
  useEffect(() => {
    hydratedRef.current = null;
    setHasDraft(false);
  }, [questionId]);

  // Hydrate code + chat on question/language change
  useEffect(() => {
    if (!questionId || !isAuthenticated) return;
    const key = `${questionId}:${language}`;
    if (hydratedRef.current === key) return;
    hydratedRef.current = key;
    setHasDraft(false);
    let cancelled = false;
    workspaceService
      .getCode(questionId, language)
      .then((res) => {
        if (cancelled) return;
        if (res.code) {
          lastSavedRef.current = res.code;
          setCurrentCode(res.code);
          setHasDraft(true);
        }
      })
      .catch(() => {});
    if (onHydrateChatRef.current) {
      workspaceService
        .getChat(questionId)
        .then((res) => {
          if (cancelled) return;
          if (res.messages?.length)
            onHydrateChatRef.current?.(res.messages as never);
        })
        .catch(() => {});
    }
    return () => {
      cancelled = true;
    };
  }, [questionId, language, isAuthenticated, setCurrentCode]);

  const scheduleSave = useCallback(
    (code: string) => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
      debounceTimer.current = setTimeout(() => {
        if (!questionId || !isAuthenticated) return;
        if (code === lastSavedRef.current) return;
        lastSavedRef.current = code;
        workspaceService.saveCode(questionId, language, code).catch(() => {});
      }, 800);
    },
    [questionId, language, isAuthenticated]
  );

  useEffect(() => {
    if (!questionId || !isAuthenticated) return;
    if (hydratedRef.current !== `${questionId}:${language}`) return;
    scheduleSave(currentCode);
    return () => {
      if (debounceTimer.current) clearTimeout(debounceTimer.current);
    };
  }, [currentCode, questionId, language, isAuthenticated, scheduleSave]);

  const deleteDraft = useCallback(async () => {
    if (!questionId || !isAuthenticated) return;
    try {
      await workspaceService.deleteCode(questionId, language);
      lastSavedRef.current = "";
      setHasDraft(false);
    } catch {}
  }, [questionId, language, isAuthenticated]);

  const clearChat = useCallback(async () => {
    if (!questionId || !isAuthenticated) return;
    try {
      await workspaceService.clearChat(questionId);
    } catch {}
  }, [questionId, isAuthenticated]);

  return { deleteDraft, clearChat, hasDraft };
}
