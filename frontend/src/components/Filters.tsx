/**
 * Job title and skill filter inputs. Presentational only — the parent owns
 * the filter state and decides how it feeds into the search query.
 */

interface FiltersProps {
  jobTitle: string;
  skill: string;
  onJobTitleChange: (jobTitle: string) => void;
  onSkillChange: (skill: string) => void;
}

export default function Filters({ jobTitle, skill, onJobTitleChange, onSkillChange }: FiltersProps) {
  return (
    <div>
      <label>
        Job title
        <input
          type="text"
          value={jobTitle}
          onChange={(event) => onJobTitleChange(event.target.value)}
          placeholder="e.g. Software Engineer"
          aria-label="Job title filter"
        />
      </label>
      <label>
        Skill
        <input
          type="text"
          value={skill}
          onChange={(event) => onSkillChange(event.target.value)}
          placeholder="e.g. Python"
          aria-label="Skill filter"
        />
      </label>
    </div>
  );
}
