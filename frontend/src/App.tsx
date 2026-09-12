import { useState } from 'react';

import { useSearch } from './api/search';
import Filters from './components/Filters';
import ResultsList from './components/ResultsList';
import SearchBar from './components/SearchBar';

function App() {
  const [query, setQuery] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [skill, setSkill] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useSearch({ q: query, jobTitle, skill, page });

  // A new keyword/filter invalidates whatever page the user was on, so each
  // setter resets to page 1 rather than leaving a stale page number applied
  // to a completely different result set.
  function handleQueryChange(value: string) {
    setQuery(value);
    setPage(1);
  }

  function handleJobTitleChange(value: string) {
    setJobTitle(value);
    setPage(1);
  }

  function handleSkillChange(value: string) {
    setSkill(value);
    setPage(1);
  }

  return (
    <div className="app">
      <header className="app__header">
        <h1 className="app__title">Searcher</h1>
        <p className="app__subtitle">LinkedIn profile index</p>
      </header>
      <SearchBar onQueryChange={handleQueryChange} />
      <Filters
        jobTitle={jobTitle}
        skill={skill}
        onJobTitleChange={handleJobTitleChange}
        onSkillChange={handleSkillChange}
      />
      <ResultsList data={data} isLoading={isLoading} isError={isError} onPageChange={setPage} />
    </div>
  );
}

export default App;
