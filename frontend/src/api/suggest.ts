/**
 * Typed client for `GET /suggest`, plus a TanStack Query hook wrapping it.
 *
 * Exists so `Filters.tsx` can steer users toward a value that will actually
 * match `job_title`/`skill`'s exact-match `.keyword` filters (see
 * `backend/src/searcher/search_service.py::suggest_values`).
 */

import { useQuery } from '@tanstack/react-query';

import type { SuggestResponse } from './types';

export type SuggestField = 'job_title' | 'skill';

export async function fetchSuggest(field: SuggestField, prefix: string): Promise<SuggestResponse> {
  const query = new URLSearchParams({ field, prefix });
  const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/suggest?${query.toString()}`);

  if (!response.ok) {
    throw new Error(`Suggest request failed with status ${response.status}`);
  }

  return (await response.json()) as SuggestResponse;
}

/**
 * Disabled while `prefix` is empty -- the backend rejects an empty prefix,
 * and there's nothing to suggest for a blank filter anyway.
 */
export function useSuggest(field: SuggestField, prefix: string) {
  return useQuery({
    queryKey: ['suggest', field, prefix],
    queryFn: () => fetchSuggest(field, prefix),
    enabled: prefix.length > 0,
  });
}
