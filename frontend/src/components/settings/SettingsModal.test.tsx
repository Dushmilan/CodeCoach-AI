import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SettingsModal } from './SettingsModal';
import { ToastContainer } from '@/components/ui/Toast';

describe('SettingsModal', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
    apiKey: '',
    onSave: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns null when open is false', () => {
    const { container } = render(<SettingsModal {...defaultProps} open={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders modal when open is true', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByText('SETTINGS')).toBeInTheDocument();
  });

  it('shows API key input', () => {
    render(<SettingsModal {...defaultProps} apiKey="nvapi-test" />);
    const input = screen.getByPlaceholderText('nvapi-...');
    expect(input).toHaveValue('nvapi-test');
  });

  it('renders Cancel and Save buttons', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('calls onSave with trimmed value when Save is clicked', async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} onSave={onSave} />);

    const input = screen.getByPlaceholderText('nvapi-...');
    await user.type(input, 'nvapi-key-123');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(onSave).toHaveBeenCalledWith('nvapi-key-123');
  });

  it('shows toast confirmation after save', async () => {
    const user = userEvent.setup();
    render(
      <>
        <SettingsModal {...defaultProps} />
        <ToastContainer />
      </>
    );

    const input = screen.getByPlaceholderText('nvapi-...');
    await user.type(input, 'nvapi-abc');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(screen.getByText(/api key saved/i)).toBeInTheDocument();
  });

  it('toggles password visibility', async () => {
    const user = userEvent.setup();
    const { container } = render(<SettingsModal {...defaultProps} apiKey="nvapi-secret" />);

    const input = screen.getByPlaceholderText('nvapi-...');
    expect(input).toHaveAttribute('type', 'password');

    const buttons = container.querySelectorAll('button');
    const toggleBtn = Array.from(buttons).find(b => b.innerHTML.includes('lucide-eye'));
    await user.click(toggleBtn!);
    expect(input).toHaveAttribute('type', 'text');
  });

  it('calls onClose when backdrop is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    const { container } = render(<SettingsModal {...defaultProps} onClose={onClose} />);

    const backdrop = container.querySelector('.fixed.inset-0 > div') as HTMLElement;
    expect(backdrop).toBeInTheDocument();
    await user.click(backdrop);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when X button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    const { container } = render(<SettingsModal {...defaultProps} onClose={onClose} />);

    const buttons = container.querySelectorAll('button');
    const xButton = Array.from(buttons).find(b => b.innerHTML.includes('lucide-x'));
    await user.click(xButton!);
    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when Cancel is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not show toast before save', () => {
    render(
      <>
        <SettingsModal {...defaultProps} />
        <ToastContainer />
      </>
    );

    expect(screen.queryByText(/api key saved/i)).not.toBeInTheDocument();
  });
});
