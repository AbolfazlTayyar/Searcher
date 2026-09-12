import { type ReactNode, useState } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Filters from './Filters';

function renderWithQueryClient(ui: ReactNode) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

/** Controlled `Filters` wrapper -- `jobTitle`/`skill` actually update as the user types. */
function ControlledFilters() {
  const [jobTitle, setJobTitle] = useState('');
  const [skill, setSkill] = useState('');
  return (
    <Filters
      jobTitle={jobTitle}
      skill={skill}
      onJobTitleChange={setJobTitle}
      onSkillChange={setSkill}
    />
  );
}

describe('Filters', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ values: [] }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls onJobTitleChange with the typed value', async () => {
    const user = userEvent.setup();
    const onJobTitleChange = vi.fn();
    const onSkillChange = vi.fn();

    renderWithQueryClient(
      <Filters
        jobTitle=""
        skill=""
        onJobTitleChange={onJobTitleChange}
        onSkillChange={onSkillChange}
      />,
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

    renderWithQueryClient(
      <Filters
        jobTitle=""
        skill=""
        onJobTitleChange={onJobTitleChange}
        onSkillChange={onSkillChange}
      />,
    );

    await user.type(screen.getByLabelText('Skill filter'), 'Python');

    expect(onSkillChange).toHaveBeenCalledTimes('Python'.length);
    expect(onSkillChange).toHaveBeenLastCalledWith('n');
    expect(onJobTitleChange).not.toHaveBeenCalled();
  });

  it('reflects the current jobTitle and skill values', () => {
    renderWithQueryClient(
      <Filters
        jobTitle="Software Engineer"
        skill="Python"
        onJobTitleChange={vi.fn()}
        onSkillChange={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Job title filter')).toHaveValue('Software Engineer');
    expect(screen.getByLabelText('Skill filter')).toHaveValue('Python');
  });

  it('fetches suggestions from GET /suggest after typing settles', async () => {
    const user = userEvent.setup();

    renderWithQueryClient(<ControlledFilters />);

    await user.type(screen.getByLabelText('Job title filter'), 'manager');

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/suggest\?field=job_title&prefix=manager$/),
      );
    });
  });

  it('selecting a suggestion sets the filter to the exact value', async () => {
    (fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ values: ['recruiting manager', 'it business analysis manager'] }),
    });
    const user = userEvent.setup();
    const onJobTitleChange = vi.fn();

    renderWithQueryClient(
      <Filters
        jobTitle="manager"
        skill=""
        onJobTitleChange={onJobTitleChange}
        onSkillChange={vi.fn()}
      />,
    );

    const input = screen.getByLabelText('Job title filter');
    await user.click(input);

    const suggestion = await screen.findByRole('button', { name: 'recruiting manager' });
    await user.click(suggestion);

    expect(onJobTitleChange).toHaveBeenLastCalledWith('recruiting manager');
  });
});
