import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatInput } from './ChatInput';

describe('ChatInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    onSend: vi.fn(),
  };

  it('renders a textarea', () => {
    render(<ChatInput {...defaultProps} />);
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('renders a send button', () => {
    render(<ChatInput {...defaultProps} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('displays the current value', () => {
    render(<ChatInput {...defaultProps} value="Hello" />);
    expect(screen.getByRole('textbox')).toHaveValue('Hello');
  });

  it('calls onChange when typing', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} onChange={onChange} />);
    await user.type(screen.getByRole('textbox'), 'a');
    expect(onChange).toHaveBeenCalledWith('a');
  });

  it('calls onSend when Enter is pressed without Shift', async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} value="test" onSend={onSend} />);
    await user.click(screen.getByRole('textbox'));
    await user.keyboard('{Enter}');
    expect(onSend).toHaveBeenCalledOnce();
  });

  it('does not call onSend when Enter is pressed with Shift', async () => {
    const onSend = vi.fn();
    const user = userEvent.setup();
    render(<ChatInput {...defaultProps} value="test" onSend={onSend} />);
    await user.click(screen.getByRole('textbox'));
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    expect(onSend).not.toHaveBeenCalled();
  });

  it('disables the send button when value is empty', () => {
    render(<ChatInput {...defaultProps} value="" />);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('enables the send button when value is non-empty', () => {
    render(<ChatInput {...defaultProps} value="test" />);
    expect(screen.getByRole('button')).toBeEnabled();
  });

  it('disables textarea and button when disabled prop is true', () => {
    render(<ChatInput {...defaultProps} disabled />);
    expect(screen.getByRole('textbox')).toBeDisabled();
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('renders custom placeholder', () => {
    render(<ChatInput {...defaultProps} placeholder="Custom placeholder" />);
    expect(screen.getByRole('textbox')).toHaveAttribute('placeholder', 'Custom placeholder');
  });

  it('renders default placeholder when none provided', () => {
    render(<ChatInput {...defaultProps} />);
    expect(screen.getByRole('textbox')).toHaveAttribute(
      'placeholder',
      'Ask a question or describe your approach...'
    );
  });

  it('disables send button when disabled even with value', () => {
    render(<ChatInput {...defaultProps} value="test" disabled />);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
