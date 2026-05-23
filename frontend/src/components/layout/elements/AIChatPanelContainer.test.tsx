import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AIChatPanelContainer } from './AIChatPanelContainer';

describe('AIChatPanelContainer', () => {
  const defaultProps = {
    messages: [],
    onSendMessage: vi.fn(),
    isTyping: false,
    selectedQuestion: '1',
    currentCode: '',
    language: 'python' as const,
  };

  it('renders aside with AI Assistant Panel aria label', () => {
    render(<AIChatPanelContainer {...defaultProps} />);
    const aside = screen.getByRole('complementary', { name: 'AI Assistant Panel' });
    expect(aside).toBeInTheDocument();
  });

  it('passes messages to AIChatPanel', () => {
    const messages = [{ id: '1', role: 'user' as const, content: 'hello', timestamp: new Date() }];
    render(<AIChatPanelContainer {...defaultProps} messages={messages} />);
    expect(screen.getByText('hello')).toBeInTheDocument();
  });

  it('forwards isTyping to disable inputs', () => {
    render(<AIChatPanelContainer {...defaultProps} isTyping />);
    expect(screen.getByPlaceholderText('Ask a question or describe your approach...')).toBeDisabled();
  });
});
