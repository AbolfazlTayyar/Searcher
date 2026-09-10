/**
 * Renders search results with explicit loading, error, and empty states so
 * the page never shows a silent blank screen while fetching or on a query
 * that matches nothing.
 */

import type { ProfileResult, SearchResponse } from '../api/types';

interface ResultsListProps {
  data: SearchResponse | undefined;
  isLoading: boolean;
  isError: boolean;
}

export default function ResultsList({ data, isLoading, isError }: ResultsListProps) {
  if (isLoading) {
    return <p>Loading results...</p>;
  }

  if (isError) {
    return <p role="alert">Something went wrong while searching. Please try again.</p>;
  }

  if (!data || data.results.length === 0) {
    return <p>No profiles match your search.</p>;
  }

  return (
    <div>
      <p>{data.total} result{data.total === 1 ? '' : 's'}</p>
      <ul>
        {data.results.map((profile, index) => (
          <ProfileCard key={index} profile={profile} />
        ))}
      </ul>
    </div>
  );
}

interface ProfileCardProps {
  profile: ProfileResult;
}

function ProfileCard({ profile }: ProfileCardProps) {
  return (
    <li>
      <strong>{profile.name ?? 'Unknown name'}</strong>
      {profile.job_title && <span> — {profile.job_title}</span>}
      {profile.industry && <span> ({profile.industry})</span>}
      {profile.location && <div>{profile.location}</div>}
      {profile.summary && <p>{profile.summary}</p>}
      {profile.skills.length > 0 && <p>Skills: {profile.skills.join(', ')}</p>}
    </li>
  );
}
