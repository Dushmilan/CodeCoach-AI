"use client";

import { useState, useCallback, useRef } from "react";
import { ChatMessage } from "@/types";
import { coachingService } from "./coaching.service";
import { CoachingFeature, CoachingMode } from "./coaching.types";
import { showToast } from "@/components/ui/Toast";
import { useUsage } from "@/features/usage/usage.context";

function isRateLimited(err: unknown): boolean {
  return (
    err instanceof Error &&
    "status" in err &&
    (err as { status?: number }).status === 429
  );
}

export function useCoaching(): CoachingFeature {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    limitReached,
    refreshUsage,
    markLimitReached,
    clearLimitReached,
  } = useUsage();

  const sendMessage = useCallback(
    async (
      message: string,
      mode: CoachingMode,
      problem: string,
      code: string,
      language: string,
      lessonContext?: string,
      difficulty?: string,
      initialCode?: string,
    ) => {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: message || `${mode} requested`,
        timestamp: new Date(),
      };

      const historyBeforeNew = messagesRef.current;

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);
      setError(null);

      const chatHistory = historyBeforeNew.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const handleSend = async () => {
        try {
          const data = await coachingService.getCoachResponse(
            problem,
            language,
            code,
            message,
            mode,
            difficulty || "medium",
            lessonContext,
            chatHistory,
            initialCode,
          );

          const assistantMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: data.response,
            structured: data.structured,
            timestamp: new Date(),
          };

          clearLimitReached();
          refreshUsage();
          setMessages((prev) => [...prev, assistantMessage]);
        } catch (err) {
          const errorMessage =
            err instanceof Error
              ? err.message
              : "Failed to get coaching response";
          if (isRateLimited(err)) {
            markLimitReached();
            refreshUsage();
            setError("You've reached your daily AI message limit.");
            showToast("Daily AI message limit reached", "info");
          } else {
            setError(errorMessage);
            showToast(errorMessage, "error");
          }
          console.error("Error getting coach response:", err);

          const errorAssistantMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: isRateLimited(err)
              ? "You've reached your daily AI message limit. Upgrade to Pro for unlimited access."
              : "Sorry, I encountered an error. Please try again.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorAssistantMessage]);
        } finally {
          setIsTyping(false);
        }
      };

      return handleSend();
    },
    [clearLimitReached, markLimitReached, refreshUsage],
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    isTyping,
    error,
    sendMessage,
    clearMessages,
    clearError,
    limitReached,
    clearLimitReached,
  };
}
