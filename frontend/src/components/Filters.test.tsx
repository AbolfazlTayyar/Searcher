import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Filters from './Filters';

describe('Filters', () => {
  it('calls onJobTitleChange with the typed value', async () => {
    const user = userEvent.setup();
    const onJobTitleChange = vi.fn();
    const onSkillChange = vi.fn();

    render(
      <Filters jobTitle="" skill="" onJobTitleChange={onJobTitleChange} onSkillChange={onSkillChange} />,
    );

    await user.type(screen.getByLabelText('Job title filter'), 'Engineer');

    expect(onJobTitleChange).toHaveBeenCalledTimes('Engineer'.length);
    expect(onJobTitleChange).toHaveBeenLastCalledWith('r');
    expect(onSkillChange).not.toHaveBeenCalled();
  });

  it('calls onSkillChange with the typed value', async () => {
    const user = userEvent.setup();
    const onJobTitleChange = vi.fn();
    const onSkillChange = vi.fn();

    render(
      <Filters jobTitle="" skill="" onJobTitleChange={onJobTitleChange} onSkillChange={onSkillChange} />,
    );

    await user.type(screen.getByLabelText('Skill filter'), 'Python');

    expect(onSkillChange).toHaveBeenCalledTimes('Python'.length);
    expect(onSkillChange).toHaveBeenLastCalledWith('n');
    expect(onJobTitleChange).not.toHaveBeenCalled();
  });

  it('reflects the current jobTitle and skill values', () => {
    render(
      <Filters jobTitle="Software Engineer" skill="Python" onJobTitleChange={vi.fn()} onSkillChange={vi.fn()} />,
    );

    expect(screen.getByLabelText('Job title filter')).toHaveValue('Software Engineer');
    expect(screen.getByLabelText('Skill filter')).toHaveValue('Python');
  });
});
