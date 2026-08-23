import { AIChatPanelContainer } from '@/components/layout/elements';
import { ChatMessage, Language } from '@/types';
import { CoachingMode } from '@/features/coaching/coaching.types';

interface AICoachPaneProps {
  messages: ChatMessage[];
  onSendMessage: (message: string, mode: CoachingMode) => void;
  onClose: () => void;
  isTyping: boolean;
  selectedQuestion: string;
  currentCode: string;
  language: Language;
}

export function AICoachPane({
  messages,
  onSendMessage,
  onClose,
  isTyping,
  selectedQuestion,
  currentCode,
  language,
}: AICoachPaneProps) {
  return (
    <div className="h-full flex flex-col min-h-0">
      <AIChatPanelContainer
        messages={messages}
        onSendMessage={onSendMessage}
        onClose={onClose}
        isTyping={isTyping}
        selectedQuestion={selectedQuestion}
        currentCode={currentCode}
        language={language}
      />
    </div>
  );
}
