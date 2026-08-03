import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AIPanelDrawer } from './AIPanelDrawer';

describe('AIPanelDrawer', () => {
  it('renders nothing when closed', () => {
    render(
      <AIPanelDrawer open={false} onClose={vi.fn()}>
        <div>drawer content</div>
      </AIPanelDrawer>,
    );
    expect(screen.queryByText('drawer content')).not.toBeInTheDocument();
  });

  it('renders children when open', () => {
    render(
      <AIPanelDrawer open onClose={vi.fn()}>
        <div>drawer content</div>
      </AIPanelDrawer>,
    );
    expect(screen.getByText('drawer content')).toBeInTheDocument();
  });

  it('renders as a dialog with an aria label', () => {
    render(
      <AIPanelDrawer open onClose={vi.fn()} label="Coach">
        <div>drawer content</div>
      </AIPanelDrawer>,
    );
    expect(screen.getByRole('dialog', { name: 'Coach' })).toBeInTheDocument();
  });

  it('closes when the backdrop is clicked', () => {
    const onClose = vi.fn();
    const { container } = render(
      <AIPanelDrawer open onClose={onClose}>
        <div>drawer content</div>
      </AIPanelDrawer>,
    );
    const backdrop = container.querySelector("[aria-hidden='true']");
    expect(backdrop).not.toBeNull();
    backdrop!.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    expect(onClose).toHaveBeenCalled();
  });
});
