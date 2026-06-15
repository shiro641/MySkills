# {{SUBJECT}} Knowledge Status

This file controls whether the assistant sends a new topic and records learning progress.

## Rules

- `pending`: sent but not confirmed complete.
- `done`: confirmed complete.
- `planned`: selected for the current week but not yet sent.
- `backlog`: useful later but not currently scheduled.
- If any `pending` exists, do not send a new topic.
- Every lesson should introduce only one new learning goal.
- Questions should increase the question count and may raise prerequisite priority.

## Current Status

- Recent completion date:
- Current pending:
- Earliest pending:
- Current weekly plan file: `weekly-plan.md`
- Question log file: `question-log.md`
- Learning route mode: Progressive from prerequisites

## Topic Records

| Date | Topic | Status | Priority | Question Count | Source | Prerequisites | Completion Date | Notes |
|---|---|---|---:|---:|---|---|---|---|
| {{START_DATE}} | {{FIRST_TOPIC}} | planned | 100 | 0 | {{SOURCE}} | {{PREREQUISITES}} |  | First topic |

## Priority Rules

- Basic, common, and prerequisite topics come first.
- Repeated questions raise priority for the topic or its prerequisites.
- Unfinished planned or pending topics carry over.
- Advanced topics stay in backlog until prerequisites are ready.
