'use client';

import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = 'Ask a question or describe your approach...',
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex items-end gap-2">
      <div className="flex-1 rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full min-h-[38px] max-h-[100px] px-3 py-2 text-sm bg-transparent rounded-[calc(1rem-0.125rem)] focus:outline-none text-foreground/80 placeholder:text-muted-foreground/40 resize-none"
          disabled={disabled}
        />
      </div>
      <button
        onClick={onSend}
        disabled={disabled || !value.trim()}
        className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-40 disabled:pointer-events-none transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] active:scale-[0.93]"
      >
        <Send className="h-3.5 w-3.5" strokeWidth={1.5} />
      </button>
    </div>
  );
}
