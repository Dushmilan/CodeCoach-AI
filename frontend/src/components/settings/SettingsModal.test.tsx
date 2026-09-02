import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SettingsModal } from './SettingsModal';

vi.mock('@/features/skill-graph/SkillGraphInline', () => ({
  SkillGraphInline: () => <div data-testid='skill-graph-inline' />,
}));

describe('SettingsModal', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
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

  it('shows the Groq-powered coaching info', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByText(/AI coaching powered by Groq/i)).toBeInTheDocument();
    expect(screen.getByText(/no setup required/i)).toBeInTheDocument();
  });

  it('renders Cancel and Done buttons', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /done/i })).toBeInTheDocument();
  });

  it('renders Privacy Policy button', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByRole('button', { name: /privacy policy/i })).toBeInTheDocument();
  });

  it('closes settings and navigates when Privacy Policy is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<SettingsModal {...defaultProps} onClose={onClose} />);
    await user.click(screen.getByRole('button', { name: /privacy policy/i }));

    expect(onClose).toHaveBeenCalled();
  });

  it('calls onClose when X button is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<SettingsModal {...defaultProps} onClose={onClose} />);
    const xButton = screen.getByRole('button', { name: /close/i });
    await user.click(xButton);
    expect(onClose).toHaveBeenCalled();
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

  it('calls onClose when Cancel is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when Done is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /done/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('renders Sign out when authenticated and calls it on click', async () => {
    const onLogout = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <SettingsModal {...defaultProps} isAuthenticated onLogout={onLogout} onClose={onClose} />,
    );

    const signOut = screen.getByRole('button', { name: /sign out/i });
    expect(signOut).toBeInTheDocument();
    await user.click(signOut);
    expect(onLogout).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not render Sign out when not authenticated', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.queryByRole('button', { name: /sign out/i })).toBeNull();
  });

  it('shows Free plan by default', () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByText('Your plan')).toBeInTheDocument();
    expect(screen.getByText('Free')).toBeInTheDocument();
  });

  it('shows Premium plan when plan is premium', () => {
    render(<SettingsModal {...defaultProps} plan="premium" />);
    expect(screen.getByText('Premium')).toBeInTheDocument();
  });
});
