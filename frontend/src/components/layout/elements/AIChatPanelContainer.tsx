import React from 'react';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { ChatMessage, Language } from '@/types';

interface AIChatPanelContainerProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: string) => void;
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
  return (
    <aside className="h-full flex flex-col flex-none overflow-y-auto border-l border-white/[0.04]" aria-label="AI Assistant Panel">
      <AIChatPanel
        messages={messages}
        onSendMessage={onSendMessage}
        onClose={onClose}
        isTyping={isTyping}
        selectedQuestion={selectedQuestion}
        currentCode={currentCode}
        language={language}
      />
    </aside>
  );
}