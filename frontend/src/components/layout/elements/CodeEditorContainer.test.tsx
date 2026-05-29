import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('@/components/editor/CodeEditor', () => ({
  CodeEditor: vi.fn(({ language, code, onCodeChange, onLanguageChange, onRunCode, onSubmitCode, isRunning }: {
    language: string; code: string; onCodeChange: (c: string) => void;
    onLanguageChange: (l: string) => void; onRunCode: () => void;
    onSubmitCode: () => void; isRunning: boolean;
  }) => (
    <div data-testid="mock-code-editor" data-language={language} data-code={code} data-is-running={String(isRunning)}>
      Mock Editor
    </div>
  )),
}));

import { CodeEditorContainer } from './CodeEditorContainer';

describe('CodeEditorContainer', () => {
  const defaultProps = {
    language: 'python' as const,
    currentCode: 'print("hi")',
    isRunning: false,
    output: '',
    error: '',
    onCodeChange: vi.fn(),
    onLanguageChange: vi.fn(),
    onRunCode: vi.fn(),
    onSubmitCode: vi.fn(),
  };

  it('renders CodeEditor with correct props', () => {
    render(<CodeEditorContainer {...defaultProps} />);
    const editor = screen.getByTestId('mock-code-editor');
    expect(editor).toBeInTheDocument();
    expect(editor).toHaveAttribute('data-language', 'python');
    expect(editor).toHaveAttribute('data-code', 'print("hi")');
    expect(editor).toHaveAttribute('data-is-running', 'false');
  });

  it('does not show output panel when there is no output or error', () => {
    render(<CodeEditorContainer {...defaultProps} />);
    expect(screen.queryByText('OUTPUT')).not.toBeInTheDocument();
  });

  it('shows output panel when output exists', () => {
    render(<CodeEditorContainer {...defaultProps} output="Hello, World!" />);
    expect(screen.getByText('Output')).toBeInTheDocument();
    expect(screen.getByText('Hello, World!')).toBeInTheDocument();
  });

  it('shows output panel when error exists', () => {
    render(<CodeEditorContainer {...defaultProps} error="SyntaxError" />);
    expect(screen.getByText('Output')).toBeInTheDocument();
    expect(screen.getByText('SyntaxError')).toBeInTheDocument();
  });

  it('renders error text in red color class', () => {
    render(<CodeEditorContainer {...defaultProps} error="SyntaxError" />);
    const container = screen.getByText('SyntaxError').parentElement;
    expect(container?.className).toContain('text-red-500');
  });

  it('renders output text in default color', () => {
    render(<CodeEditorContainer {...defaultProps} output="Hello" />);
    const container = screen.getByText('Hello').parentElement;
    expect(container?.className).toContain('text-foreground/80');
  });

  it('collapses output panel when collapse button is clicked', async () => {
    const user = userEvent.setup();
    render(<CodeEditorContainer {...defaultProps} output="Hello" />);

    const collapseBtn = screen.getByRole('button', { name: /collapse output/i });
    await user.click(collapseBtn);

    expect(screen.getByRole('button', { name: /expand output/i })).toBeInTheDocument();
    expect(screen.queryByText('Hello')).not.toBeInTheDocument();
  });

  it('expands output panel when expand button is clicked', async () => {
    const user = userEvent.setup();
    render(<CodeEditorContainer {...defaultProps} output="Hello" />);

    await user.click(screen.getByRole('button', { name: /collapse output/i }));
    await user.click(screen.getByRole('button', { name: /expand output/i }));

    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('renders resize handle when output is visible', () => {
    render(<CodeEditorContainer {...defaultProps} output="Hello" />);
    expect(document.querySelector('[class*="cursor-row-resize"]')).toBeTruthy();
  });

  it('forwards isRunning to CodeEditor', () => {
    render(<CodeEditorContainer {...defaultProps} isRunning />);
    const editor = screen.getByTestId('mock-code-editor');
    expect(editor).toHaveAttribute('data-is-running', 'true');
  });
});
