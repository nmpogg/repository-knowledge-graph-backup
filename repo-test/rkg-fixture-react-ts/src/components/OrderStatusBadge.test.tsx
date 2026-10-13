import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { OrderStatusBadge } from './OrderStatusBadge';

describe('OrderStatusBadge', () => {
  it('renders the status with its semantic class', () => {
    render(<OrderStatusBadge status="shipped" />);
    expect(screen.getByText('shipped')).toHaveClass('status--shipped');
  });
});
