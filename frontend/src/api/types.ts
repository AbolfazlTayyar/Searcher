/**
 * TypeScript interfaces mirroring `backend/src/searcher/models.py`.
 *
 * Field names/types must match the Pydantic models exactly (optional
 * backend fields are modeled as `| null`, since FastAPI serializes Python
 * `None` to JSON `null`, not `undefined`).
 */

export interface ProfileResult {
  name: string | null;
  job_title: string | null;
  industry: string | null;
  skills: string[];
  summary: string | null;
  location: string | null;
}

export interface SearchResponse {
  results: ProfileResult[];
  total: number;
  page: number;
  page_size: number;
}

export interface SuggestResponse {
  values: string[];
}
