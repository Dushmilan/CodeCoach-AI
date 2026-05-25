'use client';

import { MessageSquare } from 'lucide-react';
import { ChatMessage } from '@/types';
import { StructuredResponse } from './StructuredResponse';
import { EmptyState } from '@/components/ui/EmptyState';

interface MessageListProps {
  messages: ChatMessage[];
  isTyping: boolean;
}

export function MessageList({ messages, isTyping }: MessageListProps) {
  if (messages.length === 0 && !isTyping) {
    return (
      <div className="flex-1 overflow-y-auto">
        <EmptyState
          icon={MessageSquare}
          title="Ask the AI Coach for help"
          description="Get hints, code reviews, explanations, or debugging help for any problem."
        />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-3">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          } animate-fade-up`}
          style={{ animationDelay: '0ms' }}
        >
          <div
            className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
              message.role === 'user'
                ? 'bg-primary/20 text-foreground ring-1 ring-primary/30'
                : 'bg-white/[0.03] text-foreground/80 ring-1 ring-white/5'
            }`}
          >
            {message.role === 'assistant' && message.structured ? (
              <StructuredResponse
                structured={message.structured}
                rawContent={message.content}
              />
            ) : (
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
            )}
            <div className="text-[10px] text-muted-foreground/40 mt-1.5 tracking-wide">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="flex justify-start animate-fade-up">
          <div className="rounded-2xl px-4 py-3 bg-white/[0.03] ring-1 ring-white/5">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce" />
              <div
                className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce"
                style={{ animationDelay: '0.1s' }}
              />
              <div
                className="w-1.5 h-1.5 bg-primary/60 rounded-full animate-bounce"
                style={{ animationDelay: '0.2s' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
