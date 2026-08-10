"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { ChatMessage, Language } from "@/types";
import { CoachingMode } from "@/features/coaching/coaching.types";
import { coachingService } from "@/features/coaching/coaching.service";
import {
  DebriefContext,
  DebriefExchangeInput,
  DebriefPhase,
  DebriefReport,
} from "./debrief.types";

export const TOTAL_ROUNDS = 3;
const OPENING_MESSAGE =
  "I just solved this problem. I'm the senior now — ask me anything you need to understand my solution.";
const NOT_SURE_MESSAGE = "I'm not sure how to explain that part — what should I focus on?";

interface UseDebriefOptions {
  messages: ChatMessage[];
  isTyping: boolean;
  sendMessage: (
    message: string,
    mode: CoachingMode,
    problem: string,
    code: string,
    language: Language,
  ) => Promise<void>;
}

export function useDebrief({
  messages,
  isTyping,
  sendMessage,
}: UseDebriefOptions) {
  const [phase, setPhase] = useState<DebriefPhase>("idle");
  const [context, setContext] = useState<DebriefContext | null>(null);
  const [round, setRound] = useState(0);
  const [reportLoading, setReportLoading] = useState(false);
  const [report, setReport] = useState<DebriefReport | null>(null);
  const [exchanges, setExchanges] = useState<DebriefExchangeInput[]>([]);
  const baselineRef = useRef(0);

  const openMissionComplete = useCallback((ctx: DebriefContext) => {
    setContext(ctx);
    setRound(0);
    setExchanges([]);
    setReport(null);
    setReportLoading(false);
    setPhase("mission-complete");
  }, []);

  const startDebrief = useCallback(async () => {
    if (!context) return;
    baselineRef.current = messages.length;
    setPhase("dialogue");
    await sendMessage(
      OPENING_MESSAGE,
      "senior",
      context.problem,
      context.code,
      context.language,
    );
  }, [context, messages.length, sendMessage]);

  const captureExchange = useCallback(
    (answer: string) => {
      if (!context) return;
      const question = currentQuestionRef.current || "Explain this part of your code.";
      setExchanges((prev) => [...prev, { question, answer }]);
    },
    [context],
  );

  const currentQuestionRef = useRef("");
  const currentQuestion = useMemo(() => {
    if (phase !== "dialogue" && phase !== "report") return "";
    for (let i = messages.length - 1; i >= baselineRef.current; i--) {
      if (messages[i]?.role === "assistant") {
        currentQuestionRef.current = sanitizeSeniorQuestion(messages[i].content);
        return currentQuestionRef.current;
      }
    }
    return "";
  }, [messages, phase]);

  const submitExplanation = useCallback(
    async (text: string) => {
      if (!context) return;
      const trimmed = text.trim();
      captureExchange(trimmed || "Here's how my solution works.");
      setRound((r) => r + 1);
      await sendMessage(
        trimmed || "Here's how my solution works.",
        "senior",
        context.problem,
        context.code,
        context.language,
      );
    },
    [context, sendMessage, captureExchange],
  );

  const submitNotSure = useCallback(async () => {
    if (!context) return;
    captureExchange(NOT_SURE_MESSAGE);
    setRound((r) => r + 1);
    await sendMessage(
      NOT_SURE_MESSAGE,
      "senior",
      context.problem,
      context.code,
      context.language,
    );
  }, [context, sendMessage, captureExchange]);

  const finishDebrief = useCallback(async () => {
    if (!context) return;
    setPhase("report");
    setReportLoading(true);
    try {
      const data = await coachingService.getDebriefReport(
        context.problem,
        context.language,
        context.code,
        exchanges,
      );
      setReport({
        summary: data.summary,
        exchanges:
          data.exchanges.length > 0
            ? data.exchanges
            : exchanges.map((ex) => ({
                ...ex,
                strengths: [],
                improvements: [],
                strongerAnswer: [],
              })),
        takeaway: data.takeaway,
      });
    } catch (err) {
      console.error("Failed to generate debrief report:", err);
      setReport({
        summary: "Your debrief is complete. Here's a quick summary of how it went.",
        exchanges: exchanges.map((ex) => ({
          ...ex,
          strengths: [],
          improvements: [],
          strongerAnswer: [],
        })),
        takeaway:
          "Teaching your code to someone else is the fastest way to find the gaps.",
      });
    } finally {
      setReportLoading(false);
    }
  }, [context, exchanges]);

  const closeDebrief = useCallback(() => {
    setPhase("idle");
    setContext(null);
    setReport(null);
    setExchanges([]);
  }, []);

  return {
    phase,
    context,
    currentQuestion,
    isTyping,
    reportLoading,
    round,
    totalRounds: TOTAL_ROUNDS,
    isLastRound: round >= TOTAL_ROUNDS,
    report,
    openMissionComplete,
    startDebrief,
    submitExplanation,
    submitNotSure,
    finishDebrief,
    closeDebrief,
  };
}

export function sanitizeSeniorQuestion(text: string): string {
  const trimmed = (text || "").trim();
  if (!trimmed) return "";
  const firstSentence = trimmed.split(/(?<=[?.])\s+/)[0]?.trim() || trimmed;
  return firstSentence;
}
