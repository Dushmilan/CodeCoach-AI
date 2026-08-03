import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { useWorkspaceMode, WorkspaceModeOptions } from './useWorkspaceMode';

const instances: MockResizeObserver[] = [];

class MockResizeObserver {
  callback: ResizeObserverCallback;
  elements: Element[];
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
    this.elements = [];
    instances.push(this);
  }
  observe(el: Element) {
    this.elements.push(el);
  }
  disconnect() {
    this.elements = [];
  }
  trigger(width: number) {
    const entry = {
      contentRect: { width },
      target: this.elements[0],
    } as unknown as ResizeObserverEntry;
    this.callback([entry], this as unknown as ResizeObserver);
  }
}

const originalRO = (globalThis as any).ResizeObserver;

function Harness({ attach = true, options }: { attach?: boolean; options?: WorkspaceModeOptions }) {
  const { ref, mode, width, isReady } = useWorkspaceMode(options);
  if (!attach) {
    return (
      <div>
        <span data-testid="mode">{mode}</span>
        <span data-testid="ready">{String(isReady)}</span>
      </div>
    );
  }
  return (
    <div ref={ref}>
      <span data-testid="mode">{mode}</span>
      <span data-testid="measured">{width}</span>
      <span data-testid="ready">{String(isReady)}</span>
    </div>
  );
}

const lastObserver = () => instances[instances.length - 1];

describe('useWorkspaceMode', () => {
  beforeEach(() => {
    instances.length = 0;
    (globalThis as any).ResizeObserver = MockResizeObserver;
  });

  afterEach(() => {
    (globalThis as any).ResizeObserver = originalRO;
  });

  it('starts wide and not ready when no element is attached', () => {
    render(<Harness attach={false} />);
    expect(screen.getByTestId('mode')).toHaveTextContent('wide');
    expect(screen.getByTestId('ready')).toHaveTextContent('false');
  });

  it('reports wide for widths above the compact threshold', () => {
    render(<Harness />);
    act(() => lastObserver().trigger(1200));
    expect(screen.getByTestId('mode')).toHaveTextContent('wide');
  });

  it('reports compact for widths between stacked and compact thresholds', () => {
    render(<Harness />);
    act(() => lastObserver().trigger(900));
    expect(screen.getByTestId('mode')).toHaveTextContent('compact');
  });

  it('reports stacked below the stacked threshold', () => {
    render(<Harness />);
    act(() => lastObserver().trigger(500));
    expect(screen.getByTestId('mode')).toHaveTextContent('stacked');
  });

  it('updates the mode on subsequent resizes', () => {
    render(<Harness />);
    act(() => lastObserver().trigger(1200));
    expect(screen.getByTestId('mode')).toHaveTextContent('wide');
    act(() => lastObserver().trigger(500));
    expect(screen.getByTestId('mode')).toHaveTextContent('stacked');
    act(() => lastObserver().trigger(900));
    expect(screen.getByTestId('mode')).toHaveTextContent('compact');
  });

  it('honors custom thresholds', () => {
    render(<Harness options={{ compactBelow: 1000, stackedBelow: 600 }} />);
    act(() => lastObserver().trigger(800));
    expect(screen.getByTestId('mode')).toHaveTextContent('compact');
    act(() => lastObserver().trigger(550));
    expect(screen.getByTestId('mode')).toHaveTextContent('stacked');
  });

  it('falls back to wide until a real width is measured (SSR safety)', () => {
    render(<Harness />);
    expect(screen.getByTestId('mode')).toHaveTextContent('wide');
  });

  it('measures on mount when ResizeObserver is unavailable (fallback)', () => {
    (globalThis as any).ResizeObserver = undefined;
    const { rerender } = render(<Harness />);
    expect(screen.getByTestId('ready')).toHaveTextContent('true');
    rerender(<Harness />);
    expect(screen.getByTestId('ready')).toHaveTextContent('true');
  });
});
