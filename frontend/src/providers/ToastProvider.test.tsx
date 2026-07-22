import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { showToast } from '@/components/ui/Toast';
import { ToastContainer } from '@/components/ui/Toast';

describe('ToastProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('renders without crashing', () => {
    render(<ToastContainer />);
  });
});

describe('ToastContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it('renders nothing when no toasts', () => {
    const { container } = render(<ToastContainer />);
    expect(container.innerHTML).toBe('');
  });

  it('shows toast when showToast is called', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Test message', 'success');
    });
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('auto-dismisses toast after 4 seconds', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Auto dismiss', 'info');
    });
    expect(screen.getByText('Auto dismiss')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(screen.queryByText('Auto dismiss')).not.toBeInTheDocument();
  });

  it('dismisses toast on close button click', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('Dismiss me', 'error');
    });
    expect(screen.getByText('Dismiss me')).toBeInTheDocument();

    const closeButton = screen.getByRole('button');
    act(() => {
      closeButton.click();
    });
    expect(screen.queryByText('Dismiss me')).not.toBeInTheDocument();
  });

  it('shows multiple toasts', () => {
    render(<ToastContainer />);
    act(() => {
      showToast('First', 'success');
    });
    act(() => {
      showToast('Second', 'error');
    });
    expect(screen.getByText('First')).toBeInTheDocument();
    expect(screen.getByText('Second')).toBeInTheDocument();
  });
});
