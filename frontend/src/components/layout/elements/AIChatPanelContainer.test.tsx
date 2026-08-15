import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AIChatPanelContainer } from './AIChatPanelContainer';

const mockUseAuth = vi.hoisted(() => vi.fn());

vi.mock('@/providers', () => ({ useAuth: mockUseAuth }));

describe('AIChatPanelContainer', () => {
  const defaultProps = {
    messages: [],
    onSendMessage: vi.fn(),
    isTyping: false,
    selectedQuestion: '1',
    currentCode: '',
    language: 'python' as const,
  };

  beforeEach(() => {
    mockUseAuth.mockReset();
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isHydrated: true,
    });
  });

  it('renders aside with AI Assistant Panel aria label', () => {
    render(<AIChatPanelContainer {...defaultProps} />);
    const aside = screen.getByRole('complementary', {
      name: 'AI Assistant Panel',
    });
    expect(aside).toBeInTheDocument();
  });

  it('passes messages to AIChatPanel', () => {
    const messages = [
      {
        id: '1',
        role: 'user' as const,
        content: 'hello',
        timestamp: new Date(),
      },
    ];
    render(<AIChatPanelContainer {...defaultProps} messages={messages} />);
    expect(screen.getByText('hello')).toBeInTheDocument();
  });

  it('forwards isTyping to disable inputs', () => {
    render(<AIChatPanelContainer {...defaultProps} isTyping />);
    expect(
      screen.getByPlaceholderText('Ask a question or describe your approach...'),
    ).toBeDisabled();
  });

  it('shows the chat panel for free users (quota-gated, not plan-gated)', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isHydrated: true,
    });
    render(<AIChatPanelContainer {...defaultProps} />);
    expect(
      screen.getByPlaceholderText('Ask a question or describe your approach...'),
    ).toBeInTheDocument();
    expect(screen.queryByText('AI Coach is a Premium feature')).toBeNull();
  });

  it('shows a sign-in prompt for unauthenticated users', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isHydrated: true,
    });
    render(<AIChatPanelContainer {...defaultProps} />);
    expect(screen.getByText('Sign in to use the AI Coach')).toBeInTheDocument();
    expect(screen.queryByPlaceholderText('Ask a question or describe your approach...')).toBeNull();
  });
});
