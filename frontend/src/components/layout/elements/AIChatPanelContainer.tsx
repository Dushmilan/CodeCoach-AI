import React from 'react';
import { AIChatPanel } from '@/components/chat/AIChatPanel';
import { ChatMessage, Language } from '@/types';

interface AIChatPanelContainerProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: string) => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: Language;
}

export function AIChatPanelContainer({
  messages,
  onSendMessage,
  isTyping,
  selectedQuestion,
  currentCode,
  language,
}: AIChatPanelContainerProps) {
  return (
    <aside className="w-96 p-4 border-l" aria-label="AI Assistant Panel">
      <AIChatPanel
        messages={messages}
        onSendMessage={onSendMessage}
        isTyping={isTyping}
        selectedQuestion={selectedQuestion}
        currentCode={currentCode}
        language={language}
      />
    </aside>
  );
}