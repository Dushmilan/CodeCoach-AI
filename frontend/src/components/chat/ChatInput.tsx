"use client";

import { Send } from "lucide-react";

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
  placeholder = "Ask a question or describe your approach...",
}: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="flex items-end gap-1.5">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="flex-1 min-h-[38px] max-h-[100px] px-3 py-2 text-sm bg-white/[0.03] ring-1 ring-white/5 rounded-lg focus:outline-none focus:ring-white/[0.08] text-foreground/80 placeholder:text-muted-foreground/40 resize-none transition-all"
        disabled={disabled}
      />
      <button
        onClick={onSend}
        disabled={disabled || !value.trim()}
        className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-md bg-white/[0.04] hover:bg-white/[0.08] active:bg-white/[0.12] disabled:opacity-30 disabled:pointer-events-none transition-all active:scale-[0.93]"
      >
        <Send className="h-3.5 w-3.5 text-muted-foreground/60" />
      </button>
    </div>
  );
}
