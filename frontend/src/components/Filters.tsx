/**
 * Job title and skill filter inputs. Presentational only — the parent owns
 * the filter state and decides how it feeds into the search query.
 *
 * `job_title`/`skill` are exact-match `.keyword` filters by design (see
 * CLAUDE.md's ES conventions), so typing a partial value like "manager"
 * alone returns zero results. Each field is a typeahead backed by
 * `GET /suggest`, surfacing the exact values that will actually match —
 * free typing without selecting a suggestion still works exactly as before.
 */

import { useState } from 'react';
import { useDebounce } from 'use-debounce';

import { useSuggest, type SuggestField } from '../api/suggest';

const SUGGEST_DEBOUNCE_MS = 200;

interface FilterTypeaheadProps {
  label: string;
  placeholder: string;
  ariaLabel: string;
  field: SuggestField;
  value: string;
  onChange: (value: string) => void;
}

function FilterTypeahead({
  label,
  placeholder,
  ariaLabel,
  field,
  value,
  onChange,
}: FilterTypeaheadProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [debouncedValue] = useDebounce(value, SUGGEST_DEBOUNCE_MS);
  const { data } = useSuggest(field, debouncedValue);
  const suggestions = data?.values ?? [];
  const showSuggestions = isOpen && suggestions.length > 0;

  function selectSuggestion(suggestion: string) {
    onChange(suggestion);
    setIsOpen(false);
  }

  return (
    <label className="filters__field">
      <span className="filters__label">{label}</span>
      <div className="filters__typeahead">
        <input
          type="text"
          className="filters__input"
          value={value}
          onChange={(event) => {
            onChange(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setIsOpen(false)}
          placeholder={placeholder}
          aria-label={ariaLabel}
          role="combobox"
          aria-expanded={showSuggestions}
          autoComplete="off"
        />
        {showSuggestions && (
          <ul className="filters__suggestions" role="listbox">
            {suggestions.map((suggestion) => (
              <li key={suggestion}>
                <button
                  type="button"
                  className="filters__suggestion"
                  // Fires before the input's onBlur, so the selection
                  // registers before the dropdown closes.
                  onMouseDown={(event) => {
                    event.preventDefault();
                    selectSuggestion(suggestion);
                  }}
                >
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </label>
  );
}

interface FiltersProps {
  jobTitle: string;
  skill: string;
  onJobTitleChange: (jobTitle: string) => void;
  onSkillChange: (skill: string) => void;
}

export default function Filters({
  jobTitle,
  skill,
  onJobTitleChange,
  onSkillChange,
}: FiltersProps) {
  return (
    <div className="filters">
      <FilterTypeahead
        label="Job title"
        placeholder="e.g. Software Engineer"
        ariaLabel="Job title filter"
        field="job_title"
        value={jobTitle}
        onChange={onJobTitleChange}
      />
      <FilterTypeahead
        label="Skill"
        placeholder="e.g. Python"
        ariaLabel="Skill filter"
        field="skill"
        value={skill}
        onChange={onSkillChange}
      />
    </div>
  );
}
