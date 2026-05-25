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
    <aside className="w-96 flex flex-col overflow-hidden p-1" aria-label="AI Assistant Panel">
      <div className="flex-1 flex flex-col rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5 p-1.5 overflow-hidden">
        <div className="flex-1 flex flex-col rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] overflow-hidden">
          <AIChatPanel
            messages={messages}
            onSendMessage={onSendMessage}
            isTyping={isTyping}
            selectedQuestion={selectedQuestion}
            currentCode={currentCode}
            language={language}
          />
        </div>
      </div>
    </aside>
  );
}