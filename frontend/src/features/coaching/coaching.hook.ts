'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { ChatMessage } from '@/types';
import { coachingService } from './coaching.service';
import { CoachingFeature, CoachingMode } from './coaching.types';
import { showToast } from '@/components/ui/Toast';

export function useCoaching(): CoachingFeature {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Serializes sends so messages can never interleave. Each send awaits the
  // previous one's completion before starting, so the chat stays ordered even
  // under rapid successive calls.
  const queueRef = useRef<Promise<void>>(Promise.resolve());
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const sendMessage = useCallback(
    async (
      message: string,
      mode: CoachingMode,
      problem: string,
      code: string,
      language: string,
      lessonContext?: string,
      difficulty?: string,
    ) => {
      const userMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        role: 'user',
        content: message || `${mode} requested`,
        timestamp: new Date(),
      };

      // Append the user message and show typing state immediately so the UI
      // is responsive. Only the service call itself is serialized through the
      // queue so assistant messages always land in send order.
      const chatHistory = messagesRef.current.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);
      setError(null);

      const run = queueRef.current.then(async () => {
        try {
          const data = await coachingService.getCoachResponse(
            problem,
            language,
            code,
            message,
            mode,
            difficulty || 'medium',
            lessonContext,
            chatHistory,
          );

          const assistantMessage: ChatMessage = {
            id: `${Date.now() + 1}-${Math.random().toString(36).slice(2, 7)}`,
            role: 'assistant',
            content: data.response,
            structured: data.structured,
            timestamp: new Date(),
          };

          if (mountedRef.current) {
            setMessages((prev) => [...prev, assistantMessage]);
          }
        } catch (err) {
          const errorMessage =
            err instanceof Error ? err.message : 'Failed to get coaching response';
          if (mountedRef.current) {
            setError(errorMessage);
            showToast(errorMessage, 'error');
          }
          console.error('Error getting coach response:', err);

          const errorAssistantMessage: ChatMessage = {
            id: `${Date.now() + 1}-${Math.random().toString(36).slice(2, 7)}`,
            role: 'assistant',
            content: 'Sorry, I encountered an error. Please try again.',
            timestamp: new Date(),
          };
          if (mountedRef.current) {
            setMessages((prev) => [...prev, errorAssistantMessage]);
          }
        } finally {
          if (mountedRef.current) {
            setIsTyping(false);
          }
        }
      });

      // Keep the queue rolling even if this send rejects.
      queueRef.current = run.catch(() => {});
      return run;
    },
    [],
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
  };
}
