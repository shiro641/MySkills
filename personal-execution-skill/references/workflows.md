# PersonalOS Workflows

## File Modification Principles

- Read before write.
- Preserve user-authored text.
- Prefer appending dated entries over rewriting sections.
- Mark checkboxes complete instead of deleting them.
- If a match is ambiguous, add a completion log entry and mention uncertainty.
- Always show `git diff --stat` and a focused `git diff` after changes.

## Intent First

When adding a task, explicit user intent wins over classification. Examples:

- "Add as Waiting: Alice to send invoice" goes to `state/waiting.md`.
- "Make this a Codex automation task: produce the report" goes to `tasks/automation-candidates.md`.
- "Add a long-term project: relaunch website" creates or updates a project file.

Only classify automatically if no explicit type is present.

## Automation Detector

A task is a strong automation candidate when it can be completed by Codex using files, code, data, browser actions, docs, email drafts, or repeatable transformations. Do not place strong candidates into human task lists.

Automation records must include:

- Codex Prompt
- Execution Steps
- Expected Artifacts
- Acceptance Criteria

## Project Review Heuristics

- Stale: `Last Updated` is more than 14 days old.
- Stalled: no open next actions or progress says blocked/stalled.
- Risky: contains blocked items, waiting dependencies, overdue language, or high uncertainty.

## Weekly Review Sources

Read all Daily files in the ISO week, then summarize:

- completed checkboxes
- unfinished checkboxes
- Waiting and Blocked
- project changes
- automation candidates added or completed
- next-week suggestions
