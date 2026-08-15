import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/providers';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { CoachingMode } from '@/features/coaching/coaching.types';
import { ChatMessage, Language } from '@/types';

interface AIChatPanelContainerProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: CoachingMode) => void;
  onClose?: () => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: Language;
}

export function AIChatPanelContainer({
  messages,
  onSendMessage,
  onClose,
  isTyping,
  selectedQuestion,
  currentCode,
  language,
}: AIChatPanelContainerProps) {
  const { isAuthenticated, isHydrated } = useAuth();

  return (
    <aside
      className="h-full flex flex-col flex-none overflow-hidden border-l border-white/[0.04]"
      aria-label="AI Assistant Panel"
    >
      {isHydrated && !isAuthenticated ? (
        <div
          className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center"
          role="status"
          aria-label="Sign in required"
        >
          <p className="text-sm font-semibold text-foreground/80">Sign in to use the AI Coach</p>
          <p className="mt-1 text-xs text-muted-foreground/70 leading-relaxed">
            Get hints, reviews, and debugging help with your coding practice.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-white hover:opacity-90"
          >
            Sign in
          </Link>
        </div>
      ) : (
        <AIChatPanel
          messages={messages}
          onSendMessage={onSendMessage}
          onClose={onClose}
          isTyping={isTyping}
          selectedQuestion={selectedQuestion}
          currentCode={currentCode}
          language={language}
        />
      )}
    </aside>
  );
}
