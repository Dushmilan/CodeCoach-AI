import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AIChatPanel } from '../../components/chat/AIChatPanel';

// Mock the CodeCoach context
const mockDispatch = jest.fn();
const mockState = {
  messages: [
    { id: '1', role: 'user', content: 'Hello' },
    { id: '2', role: 'assistant', content: 'Hi there!' },
  ],
  isLoading: false,
};

jest.mock('../../contexts/CodeCoachContext', () => ({
  useCodeCoach: () => ({
    state: mockState,
    dispatch: mockDispatch,
  }),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

describe('AIChatPanel', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'AI response' }),
    });
  });

  it('renders chat messages correctly', () => {
    render(<AIChatPanel />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });

  it('displays input field and send button', () => {
    render(<AIChatPanel />);
    
    expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('handles message input correctly', () => {
    render(<AIChatPanel />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    
    expect(input).toHaveValue('Test message');
  });

  it('sends message when send button is clicked', async () => {
    render(<AIChatPanel />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/questions'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Test message'),
        })
      );
    });
  });

  it('clears input after sending message', async () => {
    render(<AIChatPanel />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(input).toHaveValue('');
    });
  });

  it('handles Enter key press to send message', async () => {
    render(<AIChatPanel />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
  });
});