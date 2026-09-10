import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchBar from './SearchBar';

describe('SearchBar', () => {
  it('calls onQueryChange with the typed value after the debounce delay', async () => {
    const user = userEvent.setup();
    const onQueryChange = vi.fn();

    render(<SearchBar onQueryChange={onQueryChange} />);

    const input = screen.getByLabelText('Search');
    await user.type(input, 'engineer');

    expect(input).toHaveValue('engineer');
    expect(onQueryChange).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(onQueryChange).toHaveBeenLastCalledWith('engineer');
    });
    expect(onQueryChange).toHaveBeenCalledTimes(1);
  });
});
