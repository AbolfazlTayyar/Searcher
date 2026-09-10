import { useState } from 'react';

import { useSearch } from './api/search';
import Filters from './components/Filters';
import ResultsList from './components/ResultsList';
import SearchBar from './components/SearchBar';

function App() {
  const [query, setQuery] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [skill, setSkill] = useState('');

  const { data, isLoading, isError } = useSearch({ q: query, jobTitle, skill });

  return (
    <div>
      <h1>Searcher</h1>
      <SearchBar onQueryChange={setQuery} />
      <Filters jobTitle={jobTitle} skill={skill} onJobTitleChange={setJobTitle} onSkillChange={setSkill} />
      <ResultsList data={data} isLoading={isLoading} isError={isError} />
    </div>
  );
}

export default App;
