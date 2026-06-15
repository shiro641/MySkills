# {{SUBJECT}} Learning Assistant

This file defines the operating rules for this learning project. Always read this file before updating progress or sending lessons.

## Files

- `knowledge-status.md`: topic status, priorities, prerequisites, question counts, and completion dates.
- `weekly-plan.md`: current weekly scope and ordering.
- `question-log.md`: learner questions and answer summaries.
- `learning-archive.md`: historical decisions and completed learning sessions.

## Schedule

- Weekly planning: {{WEEKLY_SCHEDULE}}
- Daily learning: {{DAILY_SCHEDULE}}
- Timezone: {{TIMEZONE}}

## Completion

Treat these as completion confirmations: `finish learning`, `done`, `学完了`, `完成学习`, `记完了`, and clear equivalents.

When the learner confirms completion:

1. Mark the earliest `pending` topic as `done`.
2. Write the completion date.
3. Update the recent completion date.
4. Run external sync only if configured below.
5. Wait for the next daily trigger unless the learner asks for another topic.

## External Sync

{{EXTERNAL_SYNC}}

## Teaching Rule

Introduce only one new learning goal at a time. If a topic needs multiple unlearned prerequisites, split it and teach the prerequisites first.
