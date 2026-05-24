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
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === 'user' ? 'justify-end' : 'justify-start'
          }`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2 ${
              message.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary text-secondary-foreground'
            }`}
          >
            {message.role === 'assistant' && message.structured ? (
              <StructuredResponse
                structured={message.structured}
                rawContent={message.content}
              />
            ) : (
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>
            )}
            <div className="text-xs opacity-70 mt-1">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}

      {isTyping && (
        <div className="flex justify-start">
          <div className="bg-secondary text-secondary-foreground rounded-lg px-4 py-2">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
              <div
                className="w-2 h-2 bg-primary rounded-full animate-bounce"
                style={{ animationDelay: '0.1s' }}
              />
              <div
                className="w-2 h-2 bg-primary rounded-full animate-bounce"
                style={{ animationDelay: '0.2s' }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
