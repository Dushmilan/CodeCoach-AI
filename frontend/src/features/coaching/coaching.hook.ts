"use client";

import { useState, useCallback, useRef } from 'react';
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

  const sendMessage = useCallback(
    async (
      message: string,
      mode: CoachingMode,
      problem: string,
      code: string,
      language: string,
      lessonContext?: string
    ) => {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
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

      try {
        const data = await coachingService.getCoachResponse(
          problem,
          language,
          code,
          message,
          mode,
          'medium',
          lessonContext,
          chatHistory
        );

        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          structured: data.structured,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to get coaching response';
        setError(errorMessage);
        showToast(errorMessage, 'error');
        console.error('Error getting coach response:', err);

        const errorAssistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorAssistantMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    []
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
