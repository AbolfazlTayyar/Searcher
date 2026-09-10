/**
 * Typed client for `GET /search`, plus a TanStack Query hook wrapping it.
 */

import { useQuery } from '@tanstack/react-query';

import type { SearchResponse } from './types';

export interface SearchParams {
  q?: string;
  jobTitle?: string;
  skill?: string;
  page?: number;
  pageSize?: number;
}

/**
 * Calls `GET /search` with the given params and returns the parsed response.
 *
 * Empty/undefined param values are omitted from the query string entirely
 * (rather than sent as `""`) so the backend's "field not present" handling
 * applies uniformly instead of a route having to special-case blank strings.
 */
export async function fetchSearch(params: SearchParams): Promise<SearchResponse> {
  const query = new URLSearchParams();
  if (params.q) query.set('q', params.q);
  if (params.jobTitle) query.set('job_title', params.jobTitle);
  if (params.skill) query.set('skill', params.skill);
  if (params.page !== undefined) query.set('page', String(params.page));
  if (params.pageSize !== undefined) query.set('page_size', String(params.pageSize));

  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/search?${query.toString()}`);

  if (!response.ok) {
    throw new Error(`Search request failed with status ${response.status}`);
  }

  return (await response.json()) as SearchResponse;
}

/**
 * TanStack Query hook over `fetchSearch`, keyed on all search params so
 * changing keyword/filters/page triggers a refetch and distinct results
 * stay cached per combination.
 */
export function useSearch(params: SearchParams) {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => fetchSearch(params),
  });
}
