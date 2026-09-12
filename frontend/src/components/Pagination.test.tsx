import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Pagination from './Pagination';

describe('Pagination', () => {
  it('renders nothing when everything fits on one page', () => {
    const { container } = render(
      <Pagination page={1} pageSize={20} total={10} onPageChange={vi.fn()} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('disables Previous on the first page and Next on the last page', () => {
    render(<Pagination page={1} pageSize={20} total={31} onPageChange={vi.fn()} />);

    expect(screen.getByRole('button', { name: 'Previous' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Next' })).not.toBeDisabled();
  });

  it('calls onPageChange with the previous/next page number', () => {
    const onPageChange = vi.fn();
    render(<Pagination page={2} pageSize={20} total={45} onPageChange={onPageChange} />);

    screen.getByRole('button', { name: 'Next' }).click();
    expect(onPageChange).toHaveBeenCalledWith(3);

    screen.getByRole('button', { name: 'Previous' }).click();
    expect(onPageChange).toHaveBeenCalledWith(1);
  });
});
