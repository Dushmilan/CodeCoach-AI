import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@monaco-editor/react', () => ({
  default: vi.fn(({ value, onChange, language }: {
    value?: string; onChange?: (v: string | undefined) => void; language?: string;
  }) => (
    <textarea
      aria-label="code-editor"
      value={value || ''}
      data-language={language}
      onChange={(e) => onChange?.(e.target.value)}
    />
  )),
}));

import { CodeEditor } from './CodeEditor';

describe('CodeEditor', () => {
  const defaultProps = {
    language: 'python' as const,
    code: 'print("hello")',
    initialCode: '',
    onCodeChange: vi.fn(),
    onLanguageChange: vi.fn(),
    onRunCode: vi.fn(),
    onSubmitCode: vi.fn(),
    isRunning: false,
  };

  it('renders language selector', () => {
    render(<CodeEditor {...defaultProps} />);
    expect(screen.getByRole('combobox')).toHaveValue('python');
  });

  it('renders Reset, Run, and Submit buttons', () => {
    render(<CodeEditor {...defaultProps} />);
    expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /run/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('shows Running... text when isRunning is true', () => {
    render(<CodeEditor {...defaultProps} isRunning />);
    expect(screen.getByText('Running...')).toBeInTheDocument();
  });

  it('disables buttons when isRunning is true', () => {
    render(<CodeEditor {...defaultProps} isRunning />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it('calls onCodeChange when editor content changes', async () => {
    const onCodeChange = vi.fn();
    const user = userEvent.setup();
    render(<CodeEditor {...defaultProps} onCodeChange={onCodeChange} />);

    const editor = screen.getByRole('textbox', { name: 'code-editor' });
    await user.type(editor, 'x');
    expect(onCodeChange).toHaveBeenCalled();
  });

  it('calls onRunCode when Run is clicked', async () => {
    const onRunCode = vi.fn();
    const user = userEvent.setup();
    render(<CodeEditor {...defaultProps} onRunCode={onRunCode} />);

    await user.click(screen.getByRole('button', { name: /run/i }));
    expect(onRunCode).toHaveBeenCalledTimes(1);
  });

  it('calls onSubmitCode when Submit is clicked', async () => {
    const onSubmitCode = vi.fn();
    const user = userEvent.setup();
    render(<CodeEditor {...defaultProps} onSubmitCode={onSubmitCode} />);

    await user.click(screen.getByRole('button', { name: /submit/i }));
    expect(onSubmitCode).toHaveBeenCalledTimes(1);
  });

  it('calls onLanguageChange when language select changes', async () => {
    const onLanguageChange = vi.fn();
    const user = userEvent.setup();
    render(<CodeEditor {...defaultProps} onLanguageChange={onLanguageChange} />);

    await user.selectOptions(screen.getByRole('combobox'), 'javascript');
    expect(onLanguageChange).toHaveBeenCalledWith('javascript');
  });

  it('calls onCodeChange with empty when Reset is clicked', async () => {
    const onCodeChange = vi.fn();
    const user = userEvent.setup();
    render(<CodeEditor {...defaultProps} onCodeChange={onCodeChange} />);

    await user.click(screen.getByRole('button', { name: /reset/i }));
    expect(onCodeChange).toHaveBeenCalledWith('');
  });

  it('renders language options', () => {
    render(<CodeEditor {...defaultProps} />);
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(options[0]).toHaveTextContent('Python');
    expect(options[1]).toHaveTextContent('JavaScript');
    expect(options[2]).toHaveTextContent('Java');
  });
});
