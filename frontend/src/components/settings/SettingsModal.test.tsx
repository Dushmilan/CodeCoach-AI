import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '@/mocks/server';
import { setAccessToken } from '@/lib/auth-session';
import { SettingsModal } from './SettingsModal';

const graphPayload = {
  skills: [
    {
      skill_slug: 'arrays',
      name: 'Arrays',
      mastery_score: 0.5,
      confidence: 0.7,
      status: 'learning',
      trend: 'improving',
      evidence_count: 3,
      recent_error_count: 0,
      last_seen_at: null,
      last_reviewed_at: null,
    },
    {
      skill_slug: 'hash-maps',
      name: 'Hash Maps',
      mastery_score: 0.2,
      confidence: 0.4,
      status: 'new',
      trend: 'stable',
      evidence_count: 1,
      recent_error_count: 0,
      last_seen_at: null,
      last_reviewed_at: null,
    },
  ],
  edges: [{ source: 'arrays', target: 'hash-maps', relation: 'prerequisite' }],
};

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

  it('has no duplicate dashboard tab — skills is the single dashboard entry', () => {
    render(<SettingsModal open onClose={() => {}} isAuthenticated />);
    expect(screen.queryByTestId('settings-tab-dashboard')).toBeNull();
    expect(screen.queryByTestId('settings-dashboard-tab')).toBeNull();
    expect(screen.queryByTestId('settings-dashboard-open')).toBeNull();
    expect(screen.getByTestId('settings-tab-skills')).toBeInTheDocument();
  });

  it('exposes exactly one dashboard entry point from the skills tab', async () => {
    setAccessToken('test-token');
    server.use(
      http.get('/api/skills/me/skills', () => HttpResponse.json(graphPayload)),
    );
    render(<SettingsModal open onClose={() => {}} isAuthenticated />);
    fireEvent.click(screen.getByTestId('settings-tab-skills'));
    expect(await screen.findByTestId('settings-skills-tab')).toBeInTheDocument();
    expect(screen.getByTestId('settings-skills-open')).toHaveTextContent('Open Dashboard');
    expect(screen.queryByTestId('settings-dashboard-open')).toBeNull();
  });

  it('gear skills tab renders the SVG graph', async () => {
    setAccessToken('test-token');
    server.use(
      http.get('/api/skills/me/skills', () => HttpResponse.json(graphPayload)),
    );
    render(<SettingsModal open onClose={() => {}} isAuthenticated />);
    fireEvent.click(screen.getByTestId('settings-tab-skills'));
    const graph = await screen.findByTestId('skill-graph');
    expect(graph).toBeInTheDocument();
    expect(screen.getByTestId('settings-skills-open')).toBeInTheDocument();
    expect(graph.querySelectorAll('[data-testid="skill-graph-node"]').length).toBeGreaterThan(0);
  });

  it('guest skills tab shows preview, never mounts the live skill graph', async () => {
    server.use(
      http.get('/api/skills/me/skills', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    );
    render(<SettingsModal open onClose={() => {}} />);
    fireEvent.click(screen.getByTestId('settings-tab-skills'));
    expect(await screen.findByTestId('settings-skills-tab')).toBeInTheDocument();
    expect(await screen.findByText(/preview — sign in to track progress/i)).toBeInTheDocument();
    expect(screen.queryByTestId('skill-graph')).toBeNull();
  });
});
