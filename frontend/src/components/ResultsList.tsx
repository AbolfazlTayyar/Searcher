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
    return <p className="results__status">Loading results...</p>;
  }

  if (isError) {
    return (
      <p className="results__status results__status--error" role="alert">
        Something went wrong while searching. Please try again.
      </p>
    );
  }

  if (!data || data.results.length === 0) {
    return <p className="results__status">No profiles match your search.</p>;
  }

  return (
    <div className="results">
      <p className="results__count">
        {data.total} result{data.total === 1 ? '' : 's'}
      </p>
      <ul className="results__list">
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
    <li className="profile-card">
      <div className="profile-card__name">{profile.name ?? 'Unknown name'}</div>
      {(profile.job_title || profile.industry) && (
        <div className="profile-card__meta">
          {profile.job_title}
          {profile.job_title && profile.industry && ' · '}
          {profile.industry}
        </div>
      )}
      {profile.location && <div className="profile-card__location">{profile.location}</div>}
      {profile.summary && <p className="profile-card__summary">{profile.summary}</p>}
      {profile.skills.length > 0 && (
        <p className="profile-card__skills">Skills: {profile.skills.join(', ')}</p>
      )}
    </li>
  );
}
