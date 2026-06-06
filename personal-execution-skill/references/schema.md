# PersonalOS Schema

This file defines the canonical repository layout used by `personal-execution-skill`.

## Files

- `README.md`: repo purpose, operating loop, and conventions.
- `inbox.md`: unprocessed raw input.
- `dailies/YYYY-MM-DD.md`: one daily execution file per date.
- `weekly-reviews/YYYY-Www.md`: weekly review for ISO week.
- `projects/*.md`: one long-term project per file.
- `tasks/today.md`: rolling today task ledger.
- `tasks/scheduled.md`: scheduled and recurring tasks.
- `tasks/automation-candidates.md`: Codex automation candidates.
- `tasks/archive.md`: completed or historical records.
- `state/waiting.md`: external-owner Waiting items.
- `state/blocked.md`: blocked work and unblock criteria.
- `state/habits.md`: habit definitions and future completion records.
- `state/stats.md`: lightweight execution counters.
- `logs/execution-log.md`: dated task completion log.
- `templates/*.md`: reusable Markdown templates copied during bootstrap.

## Daily Required Sections

- Yesterday Done
- Yesterday Unfinished
- Waiting
- Blocked
- Long-Term Project Progress
- Today Suggestions
- Today Task List
- Today New Tasks
- Today Review

## Project Required Fields

- Goal
- Current Phase
- Next Actions
- Progress
- Last Updated
- Waiting
- Blocked
- Review Notes

## Automation Candidate Required Fields

- Source Task
- Why Codex
- Codex Prompt
- Execution Steps
- Expected Artifacts
- Acceptance Criteria
- Status

## Habit Required Fields

- Habit
- Frequency
- Auto Include In Daily
- Completion Log
- Current Streak
- Completion Rate
