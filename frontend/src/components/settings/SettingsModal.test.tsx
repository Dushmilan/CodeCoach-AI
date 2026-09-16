import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { setAccessToken } from '@/lib/auth-session';
import { SettingsModal } from './SettingsModal';

describe('SettingsModal', () => {
  const defaultProps = {
    open: true,
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    setAccessToken(null);
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

  it('renders Privacy Policy button in the account section', async () => {
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} />);
    await user.click(screen.getByTestId('settings-tab-account'));
    expect(screen.getByRole('button', { name: /privacy policy/i })).toBeInTheDocument();
  });

  it('closes settings and navigates when Privacy Policy is clicked', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<SettingsModal {...defaultProps} onClose={onClose} />);
    await user.click(screen.getByTestId('settings-tab-account'));
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

  it('renders Sign out in the account section when authenticated and calls it on click', async () => {
    const onLogout = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <SettingsModal {...defaultProps} isAuthenticated onLogout={onLogout} onClose={onClose} />,
    );

    await user.click(screen.getByTestId('settings-tab-account'));
    const signOut = screen.getByRole('button', { name: /sign out/i });
    expect(signOut).toBeInTheDocument();
    await user.click(signOut);
    expect(onLogout).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('does not render Sign out when not authenticated', async () => {
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} />);
    await user.click(screen.getByTestId('settings-tab-account'));
    expect(screen.queryByRole('button', { name: /sign out/i })).toBeNull();
  });

  it('shows Groq coaching info with no plan UI', async () => {
    render(<SettingsModal {...defaultProps} />);
    expect(screen.getByText(/AI coaching powered by Groq/i)).toBeInTheDocument();
    expect(screen.queryByText('Your plan')).toBeNull();
    expect(screen.queryByText('Premium')).toBeNull();
  });

  it('renders a vertical settings nav with content pane', async () => {
    const user = userEvent.setup();
    render(<SettingsModal open onClose={() => {}} />);
    const tablist = screen.getByRole('tablist');
    expect(tablist).toHaveAttribute('aria-orientation', 'vertical');
    expect(screen.getByTestId('settings-tab-general')).toBeInTheDocument();
    expect(screen.queryByTestId('settings-tab-plan')).toBeNull();
    expect(screen.getByTestId('settings-tab-account')).toBeInTheDocument();
    expect(screen.getByRole('tabpanel')).toBeInTheDocument();
    // Groq info lives in the default General pane
    expect(screen.getByText(/AI coaching powered by Groq/i)).toBeInTheDocument();
    // Switch to Account pane — privacy + sign-out live there
    await user.click(screen.getByTestId('settings-tab-account'));
    expect(screen.getByRole('button', { name: /privacy policy/i })).toBeInTheDocument();
  });

  it('has no dashboard or skill-graph destinations inside settings', () => {
    render(<SettingsModal open onClose={() => {}} isAuthenticated />);
    expect(screen.queryByTestId('settings-tab-dashboard')).toBeNull();
    expect(screen.queryByTestId('settings-tab-skills')).toBeNull();
    expect(screen.queryByTestId('settings-dashboard-tab')).toBeNull();
    expect(screen.queryByTestId('settings-skills-tab')).toBeNull();
    expect(screen.queryByTestId('settings-dashboard-open')).toBeNull();
    expect(screen.queryByTestId('settings-skills-open')).toBeNull();
    expect(screen.queryByText(/skill graph/i)).toBeNull();
  });

  it('supports keyboard navigation between settings sections', async () => {
    const user = userEvent.setup();
    render(<SettingsModal open onClose={() => {}} />);
    const general = screen.getByTestId('settings-tab-general');
    general.focus();
    expect(general).toHaveFocus();
    await user.keyboard('{ArrowDown}');
    expect(screen.getByTestId('settings-tab-account')).toHaveFocus();
    await user.keyboard('{ArrowUp}');
    expect(screen.getByTestId('settings-tab-general')).toHaveFocus();
  });

  it('account pane holds privacy and sign out for authenticated users', async () => {
    const onLogout = vi.fn();
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <SettingsModal {...defaultProps} isAuthenticated onLogout={onLogout} onClose={onClose} />,
    );
    await user.click(screen.getByTestId('settings-tab-account'));
    const signOut = screen.getByRole('button', { name: /sign out/i });
    expect(signOut).toBeInTheDocument();
    await user.click(signOut);
    expect(onLogout).toHaveBeenCalledOnce();
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('guest account pane shows privacy without sign out', async () => {
    const user = userEvent.setup();
    render(<SettingsModal {...defaultProps} />);
    await user.click(screen.getByTestId('settings-tab-account'));
    expect(screen.getByRole('button', { name: /privacy policy/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /sign out/i })).toBeNull();
  });
});
