import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useCodeExecution } from './code-execution.hook';

const mockRunCode = vi.fn();
const mockValidateCode = vi.fn();
const mockSubmitCode = vi.fn();

vi.mock('./code-execution.service', () => ({
  codeExecutionService: {
    runCode: (...args: unknown[]) => mockRunCode(...args),
    validateCode: (...args: unknown[]) => mockValidateCode(...args),
    submitCode: (...args: unknown[]) => mockSubmitCode(...args),
  },
}));

vi.mock('@/components/ui/Toast', () => ({
  showToast: vi.fn(),
}));

vi.mock('@/lib/client-js-executor', () => ({
  executeClientJS: vi.fn(),
  formatClientJsOutput: vi.fn(),
}));

describe('useCodeExecution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts with idle state', () => {
    const { result } = renderHook(() => useCodeExecution());
    expect(result.current.isRunning).toBe(false);
    expect(result.current.output).toBe('');
    expect(result.current.error).toBeNull();
    expect(result.current.lastResult).toBeNull();
  });

  it('runs code and sets output', async () => {
    mockRunCode.mockResolvedValue({ stdout: 'Hello World', stderr: '', exit_code: 0 });
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      await result.current.runCode('python', 'print("Hello World")');
    });

    expect(result.current.output).toBe('Hello World');
    expect(result.current.isRunning).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets error when runCode fails', async () => {
    mockRunCode.mockRejectedValue(new Error('Execution failed'));
    const { result } = renderHook(() => useCodeExecution());

    await act(async () => {
      try {
        await result.current.runCode('python', 'bad code');
      } catch { /* expected */ }
    });

    expect(result.current.isRunning).toBe(false);
    expect(result.current.error).toBe('Execution failed');
  });

  it('clears output when clearOutput is called', () => {
    const { result } = renderHook(() => useCodeExecution());
    act(() => { result.current.clearOutput(); });
    expect(result.current.output).toBe('');
  });

  it('clears error when clearError is called', () => {
    const { result } = renderHook(() => useCodeExecution());
    act(() => { result.current.clearError(); });
    expect(result.current.error).toBeNull();
  });
});
