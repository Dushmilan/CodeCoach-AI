'use client';

import { ChatMessage } from '@/types';
import { X } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { ChatInput } from './ChatInput';
import { MessageList } from './MessageList';
import { QuickActions } from './QuickActions';
import { UsageBar } from '@/features/usage/UsageBar';
import { UpgradeModal } from '@/features/usage/UpgradeModal';
import { useUsage } from '@/features/usage/usage.context';
import { CoachingMode } from '@/features/coaching/coaching.types';

interface AIChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: CoachingMode) => void;
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
  const { usage, limitReached, upgradeOpen, openUpgrade, closeUpgrade } = useUsage();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (limitReached) openUpgrade();
  }, [limitReached, openUpgrade]);

  const handleSendMessage = (message: string, mode: CoachingMode = 'freeform') => {
    const messageToSend = message.trim();
    if (messageToSend || mode !== 'freeform') {
      onSendMessage(messageToSend || '', mode);
      setInputValue('');
    }
  };

  const handleQuickAction = (mode: CoachingMode) => {
    handleSendMessage('', mode);
  };

  const inputExhausted = usage?.plan === 'free' && usage.daily_remaining <= 0;
  const inputDisabled = isTyping || inputExhausted;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.04]">
        <div>
          <h3 className="text-sm font-semibold tracking-wide text-foreground/80">AI COACH</h3>
          <p className="text-[11px] text-muted-foreground/60 mt-0.5 tracking-wide">
            Real-time coding assistance
          </p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/5 rounded-full transition-colors"
            aria-label="Close AI Panel"
          >
            <X className="h-4 w-4 text-muted-foreground/60" />
          </button>
        )}
      </div>

      <UsageBar usage={usage} onUpgrade={openUpgrade} />

      <MessageList messages={messages} isTyping={isTyping} />

      <div className="border-t border-white/[0.04] p-3">
        {inputExhausted && (
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="text-[11px] text-muted-foreground/60">
              You&apos;ve reached today&apos;s limit
            </span>
            <button onClick={openUpgrade} className="text-[11px] text-primary hover:underline">
              Upgrade
            </button>
          </div>
        )}
        <QuickActions onActionClick={handleQuickAction} disabled={isTyping || inputExhausted} />
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={() => handleSendMessage(inputValue)}
          disabled={inputDisabled}
        />
      </div>

      <UpgradeModal open={upgradeOpen} onClose={closeUpgrade} limit={usage?.daily_limit} />
    </div>
  );
}
