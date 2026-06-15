# State Protocol

Use the registry plus Markdown files as durable learning state. A project is portable when another Codex session can find the task in `assets/learning-projects.json` and infer the learner's state by reading the registered files.

## Registry

The registry lives at `assets/learning-projects.json`. It maps learning task names to state directories and file names.

Use this shape:

```json
{
  "version": 1,
  "projects": {
    "task-name": {
      "subject": "Subject",
      "state_dir": "/absolute/or/portable/path",
      "files": {
        "assistant": "learning-assistant.md",
        "knowledge_status": "knowledge-status.md",
        "weekly_plan": "weekly-plan.md",
        "question_log": "question-log.md",
        "archive": "learning-archive.md"
      },
      "aliases": ["optional-alias"],
      "updated_at": "YYYY-MM-DD"
    }
  }
}
```

Before operating on a learning task:

1. Look up the task name or alias in the registry.
2. If found and `state_dir` exists, use the registered files.
3. If found but `state_dir` does not exist on this computer, ask the learner for the current address and update the registry.
4. If not found, ask the learner for the address unless it was already provided.
5. Inspect that address. If it contains existing learning progress files, register those files and restore. Otherwise, register the address and create a new plan there.

Do not decide that a task is existing only because the current shell directory contains files. The registry is the first lookup. Directory inspection is used after a task address is known.

## Required Files

New projects should use these names:

- `learning-assistant.md`: operating rules, subject, schedule, completion phrases, external sync commands.
- `knowledge-status.md`: topic state table and current summary.
- `weekly-plan.md`: current week scope and ordering.
- `question-log.md`: learner questions, answer summaries, and follow-up teaching implications.
- `learning-archive.md`: historical decisions, route changes, and important completed sessions.

Existing projects may use subject-specific prefixes. Preserve their names.

When registering an existing project, record the actual file names in `files` instead of renaming them.

## Knowledge Status

Use this table shape for new projects:

```markdown
| Date | Topic | Status | Priority | Question Count | Source | Prerequisites | Completion Date | Notes |
|---|---|---|---:|---:|---|---|---|---|
```

Recommended summary fields above the table:

- Recent completion date.
- Current pending topic.
- Earliest pending topic.
- Current weekly plan file.
- Question log file.
- Learning route mode.

## Status Meanings

- `pending`: the topic has been sent and blocks new topics until confirmed complete.
- `done`: the learner confirmed completion.
- `planned`: the topic is in the current week but has not been sent.
- `backlog`: the topic is valuable later but not currently scheduled.

Use existing status labels if the project already defines them, but preserve the same semantics.

## Recovery Requirements

When restoring, infer from files:

- Subject and learning route.
- Active `pending` topic and earliest `pending`.
- Last completion date.
- Current week and stale weekly plans.
- All `planned`, `done`, and `backlog` topics.
- Question counts and recent weak spots.
- Prerequisite constraints.
- Completion phrases and external sync hooks.

If files conflict, prefer the most specific current-status fields in `knowledge-status.md`, then the topic table, then `weekly-plan.md`, then archive history.

If the registry points to file names that are missing but equivalent progress files exist in the state directory, preserve the existing files and update the registry after confirming the intended mapping.

## External Sync

Some projects record commands to update a habit or task system. Run those commands only when the project instructions say to do so and the learner has confirmed completion. If the command contains a date placeholder, replace it with the local current date in `YYYY-MM-DD`.
