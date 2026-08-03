import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PanelResizer } from './PanelResizer';

describe('PanelResizer', () => {
  const props = {
    boundary: 'description' as const,
    label: 'Resize panel',
    onMouseDown: vi.fn(),
    onResizeBy: vi.fn(),
  };

  it('renders a separator with aria label', () => {
    render(<PanelResizer {...props} />);
    expect(screen.getByRole('separator')).toBeInTheDocument();
    expect(screen.getByLabelText('Resize panel')).toBeInTheDocument();
  });

  it('calls onMouseDown on mousedown', () => {
    render(<PanelResizer {...props} />);
    fireEvent.mouseDown(screen.getByRole('separator'));
    expect(props.onMouseDown).toHaveBeenCalled();
  });

  it('calls onResizeBy with negative step on ArrowLeft', () => {
    render(<PanelResizer {...props} />);
    fireEvent.keyDown(screen.getByRole('separator'), { key: 'ArrowLeft' });
    expect(props.onResizeBy).toHaveBeenCalledWith('description', -16);
  });

  it('calls onResizeBy with positive step on ArrowRight', () => {
    render(<PanelResizer {...props} />);
    fireEvent.keyDown(screen.getByRole('separator'), { key: 'ArrowRight' });
    expect(props.onResizeBy).toHaveBeenCalledWith('description', 16);
  });
});
