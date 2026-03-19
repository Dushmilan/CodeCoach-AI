'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Lightbulb, Clock, Target, BookOpen, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ChatMessage } from '@/types';

interface AIChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: string) => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: string;
}

const quickActions = [
  { id: 'hint', label: 'Hint', icon: Lightbulb, mode: 'hint' },
  { id: 'complexity', label: 'Complexity', icon: Clock, mode: 'complexity' },
  { id: 'optimal', label: 'Optimal', icon: Target, mode: 'optimal' },
  { id: 'explain', label: 'Explain', icon: BookOpen, mode: 'explain' },
  { id: 'edge', label: 'Edge Cases', icon: AlertTriangle, mode: 'edge' },
];

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  return (
    <div className="flex flex-col h-full bg-card rounded-lg border border-border">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold">AI Coach</h3>
        <p className="text-sm text-muted-foreground">Get real-time coding assistance</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}
            >
              <div className="whitespace-pre-wrap text-sm">{message.content}</div>
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
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-border p-4">
        <div className="flex flex-wrap gap-2 mb-3">
          {quickActions.map((action) => (
            <Button
              key={action.id}
              variant="outline"
              size="sm"
              onClick={() => handleQuickAction(action.mode)}
              disabled={isTyping}
              className="text-xs"
            >
              <action.icon className="h-3 w-3 mr-1" />
              {action.label}
            </Button>
          ))}
        </div>

        <div className="flex items-end space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or describe your approach..."
            className="flex-1 min-h-[40px] max-h-[120px] px-3 py-2 text-sm bg-secondary border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            disabled={isTyping}
          />
          <Button
            size="sm"
            onClick={() => handleSendMessage(inputValue)}
            disabled={isTyping || !inputValue.trim()}
            className="bg-primary hover:bg-primary/90"
          >
            <Send className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </div>
  );
}