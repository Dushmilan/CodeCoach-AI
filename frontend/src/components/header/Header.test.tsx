import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

const mockSetTheme = vi.fn();
const mockSetApiKey = vi.fn();
const mockUseTheme = vi.hoisted(() => vi.fn());
const mockUseAuth = vi.hoisted(() => vi.fn(() => ({
  user: null, isAuthenticated: false, isLoading: false, logout: vi.fn(),
})));

vi.mock('next-themes', () => ({
  useTheme: mockUseTheme,
}));

vi.mock('@/providers', () => ({
  useAuth: mockUseAuth,
}));

vi.mock('@/hooks/use-settings', () => ({
  useSettings: vi.fn(() => ({
    apiKey: 'test-key',
    setApiKey: mockSetApiKey,
  })),
}));

vi.mock('@/components/settings/SettingsModal', () => ({
  SettingsModal: vi.fn(({ open, onClose, apiKey, onSave }: {
    open: boolean; onClose: () => void; apiKey: string; onSave: (k: string) => void;
  }) => (
    open ? <div role="dialog">Settings Modal {apiKey}</div> : null
  )),
}));

vi.mock('@/components/ui/icons', () => ({
  MoonIcon: () => <div data-testid="moon-icon" />,
  SunIcon: () => <div data-testid="sun-icon" />,
  SettingsIcon: () => <div data-testid="settings-icon" />,
  UserIcon: () => <div data-testid="user-icon" />,
  XIcon: () => <div data-testid="x-icon" />,
  GraduationCapIcon: () => <div data-testid="grad-icon" />,
}));

import { Header } from './Header';

describe('Header', () => {
  beforeEach(() => {
    mockUseTheme.mockReturnValue({ theme: 'dark', setTheme: mockSetTheme, resolvedTheme: 'dark' });
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: vi.fn() });
    vi.clearAllMocks();
  });

  it('renders the title', () => {
    render(<Header />);
    expect(screen.getByText('CodeCoach AI')).toBeInTheDocument();
  });

  it('renders settings button', () => {
    render(<Header />);
    expect(screen.getByTitle('Settings')).toBeInTheDocument();
  });

  it('shows sun icon when theme is dark', () => {
    render(<Header />);
    expect(screen.getByTestId('sun-icon')).toBeInTheDocument();
  });

  it('toggles theme when theme button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header />);
    const buttons = screen.getAllByRole('button');
    const themeButton = buttons.find(b => b.getAttribute('aria-label') === 'Toggle theme')!;
    await user.click(themeButton);
    expect(mockSetTheme).toHaveBeenCalledWith('light');
  });

  it('opens settings modal when settings button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header />);
    await user.click(screen.getByTitle('Settings'));
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Settings Modal test-key')).toBeInTheDocument();
  });

  it('shows moon icon when theme is light', () => {
    mockUseTheme.mockReturnValue({ theme: 'light', setTheme: mockSetTheme, resolvedTheme: 'light' });
    render(<Header />);
    expect(screen.getByTestId('moon-icon')).toBeInTheDocument();
  });
});
