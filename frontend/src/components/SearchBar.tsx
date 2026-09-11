/**
 * Free-text keyword input, debounced so typing doesn't fire a query per
 * keystroke. Presentational only — the parent owns the actual search state
 * and decides what to do with the debounced value.
 */

import { useState } from 'react';
import { useDebouncedCallback } from 'use-debounce';

const DEBOUNCE_MS = 300;

interface SearchBarProps {
  onQueryChange: (query: string) => void;
}

export default function SearchBar({ onQueryChange }: SearchBarProps) {
  const [value, setValue] = useState('');
  const debouncedOnQueryChange = useDebouncedCallback(onQueryChange, DEBOUNCE_MS);

  function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const next = event.target.value;
    setValue(next);
    debouncedOnQueryChange(next);
  }

  return (
    <input
      type="text"
      className="search-bar"
      value={value}
      onChange={handleChange}
      placeholder="Search by name, headline, skills..."
      aria-label="Search"
    />
  );
}
