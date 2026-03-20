'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/types';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { QuickActions } from './QuickActions';

interface AIChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: string) => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: string;
}

export function AIChatPanel({
  messages,
  onSendMessage,
  isTyping,
  selectedQuestion,
  currentCode,
  language,
}: AIChatPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (message: string, mode: string = 'freeform') => {
    const messageToSend = message.trim();
    if (messageToSend || mode !== 'freeform') {
      onSendMessage(messageToSend || '', mode);
      setInputValue('');
    }
  };

  const handleQuickAction = (mode: string) => {
    handleSendMessage('', mode);
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold">AI Coach</h3>
        <p className="text-sm text-muted-foreground">Get real-time coding assistance</p>
      </div>

      <MessageList messages={messages} isTyping={isTyping} />

      <div className="border-t border-border p-4">
        <QuickActions onActionClick={handleQuickAction} disabled={isTyping} />
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={() => handleSendMessage(inputValue)}
          disabled={isTyping}
        />
      </div>
    </div>
  );
}