'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/types';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { QuickActions } from './QuickActions';
import { Cross1Icon } from '@radix-ui/react-icons';

interface AIChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: string) => void;
  onClose?: () => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: string;
}

export function AIChatPanel({
  messages,
  onSendMessage,
  onClose,
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
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.04]">
        <div>
          <h3 className="text-sm font-semibold tracking-wide text-foreground/80">AI COACH</h3>
          <p className="text-[11px] text-muted-foreground/60 mt-0.5 tracking-wide">Real-time coding assistance</p>
        </div>
        {onClose && (
          <button 
            onClick={onClose}
            className="p-1 hover:bg-white/5 rounded-full transition-colors"
            aria-label="Close AI Panel"
          >
            <Cross1Icon className="h-4 w-4 text-muted-foreground/60" />
          </button>
        )}
      </div>

      <MessageList messages={messages} isTyping={isTyping} />

      <div className="border-t border-white/[0.04] p-3">
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