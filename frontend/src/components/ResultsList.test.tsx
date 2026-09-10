import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import ResultsList from './ResultsList';
import type { SearchResponse } from '../api/types';

const sampleData: SearchResponse = {
  results: [
    {
      name: 'Ada Lovelace',
      job_title: 'Software Engineer',
      industry: 'Technology',
      skills: ['Python', 'Mathematics'],
      summary: 'Pioneer of computing.',
      location: 'London',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
};

describe('ResultsList', () => {
  it('shows a loading state while fetching', () => {
    render(<ResultsList data={undefined} isLoading={true} isError={false} />);

    expect(screen.getByText('Loading results...')).toBeInTheDocument();
  });

  it('shows an error state when the search fails', () => {
    render(<ResultsList data={undefined} isLoading={false} isError={true} />);

    expect(screen.getByRole('alert')).toHaveTextContent(
      'Something went wrong while searching. Please try again.',
    );
  });

  it('shows the empty state when given an empty result list', () => {
    const emptyData: SearchResponse = { results: [], total: 0, page: 1, page_size: 20 };

    render(<ResultsList data={emptyData} isLoading={false} isError={false} />);

    expect(screen.getByText('No profiles match your search.')).toBeInTheDocument();
  });

  it('renders results and their profile details', () => {
    render(<ResultsList data={sampleData} isLoading={false} isError={false} />);

    expect(screen.getByText('1 result')).toBeInTheDocument();
    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument();
    expect(screen.getByText(/Software Engineer/)).toBeInTheDocument();
    expect(screen.getByText(/Technology/)).toBeInTheDocument();
    expect(screen.getByText('London')).toBeInTheDocument();
    expect(screen.getByText('Pioneer of computing.')).toBeInTheDocument();
    expect(screen.getByText('Skills: Python, Mathematics')).toBeInTheDocument();
  });
});
