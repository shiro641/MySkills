---
name: progressive-learning-coach
description: Create, restore, and operate file-backed progressive learning plans for any subject. Use when Codex needs to set up a new learning repository, continue an existing learning plan from Markdown progress files, generate weekly plans, send daily learning cards, answer learner questions while updating logs, mark lessons complete, reset a route to prerequisites, review learned topics, or preserve learning progress across computers and sessions.
---

# Progressive Learning Coach

## Core Principle

Treat the learning repository as the source of truth. If progress files exist, restore state from files before planning, teaching, updating progress, or answering learning-plan questions. Do not rely on conversation memory as the primary record.

Progressive learning is the teaching rule that outranks convenience: introduce one new learning goal at a time, and schedule prerequisites before advanced topics.

## Decision Flow

1. Identify the learning task name from the user's request, such as `rust`, `typescript`, or `english-writing`.
2. Read `assets/learning-projects.json` and look up that task.
3. If the task exists in the registry, use its configured state directory. If that path does not exist on this computer, ask the user for the current address and update the registry.
4. If the task is not in the registry, ask the user for the address where this learning task should live, unless the user already provided one.
5. Inspect the provided address:
   - If it already contains recognizable learning progress files, register the task and use Restore mode.
   - If it does not contain an existing learning plan, register the task and use Create mode.
6. Read `references/state-protocol.md` before creating, restoring, registering, or updating a learning plan.
7. Choose the workflow: weekly plan, daily card, learner question, completion confirmation, route reset, or review.
8. Update only the registry and project files required by that workflow, then summarize what changed.

## Workflows

Use `references/workflows.md` for the detailed workflow steps.

Supported workflows:

- **Create learning plan**: initialize a portable repository with the standard progress files.
- **Restore existing plan**: infer the current state from existing Markdown files.
- **Generate weekly plan**: carry over unfinished work and select ready topics.
- **Send daily learning card**: continue `pending` work or promote one ready `planned` topic.
- **Answer learner question**: answer at the learner's level and update question history.
- **Confirm completion**: mark the earliest `pending` topic as `done`.
- **Reset route**: move unsuitable advanced topics to `backlog` and rebuild prerequisites.
- **Review**: create short retrieval exercises from completed or high-question topics.

## Rules

- If any `pending` topic exists, do not send a new topic. Remind the learner to continue the earliest `pending`.
- Mark a topic `done` only after the learner clearly confirms completion.
- Preserve history. Append questions and archive notes instead of replacing older context.
- Raise priority for topics or prerequisites that appear repeatedly in learner questions.
- Keep advanced topics in `backlog` until their prerequisites are ready.
- If real source material contains several unlearned concepts, simplify it or split it before teaching.
- Run external habit or task sync commands only when the project instructions require it and completion is confirmed.
- Do not migrate existing file names or formats unless the user asks.

## Status Vocabulary

These default statuses are the core workflow vocabulary:

- `pending`: sent but not confirmed complete; blocks new topics.
- `done`: confirmed complete.
- `planned`: selected for the current week but not yet sent.
- `backlog`: useful later but not currently scheduled.

## Outputs

Daily learning cards should follow `references/teaching-card.md`:

1. Today's topic.
2. Why learn it now.
3. Core explanation.
4. Minimal example, case, sentence, code snippet, or source excerpt.
5. Explanation of the example.
6. Personalized reminder from `question-log.md`.
7. One simple exercise.
8. Completion instruction.

Weekly plans should include the selected topics, order, reason for each topic, carryover notes, and a reminder that new topics wait until the current `pending` topic is complete.

After file updates, briefly report the changed files and the restored or new current state.

## Resources

- `assets/learning-projects.json`: registry that maps learning task names to their state directories and progress files.
- `references/state-protocol.md`: file roles, table contracts, status meanings, recovery rules, and external sync handling.
- `references/workflows.md`: exact procedures for weekly planning, daily cards, questions, completion, reset, and review.
- `references/teaching-card.md`: daily card format, concept-density rules, and pending reminder format.
- `references/topic-selection.md`: priority signals, prerequisite handling, weekly size, and tie breakers.
- `assets/templates/`: Markdown templates for new learning repositories.

Read `references/state-protocol.md` before interpreting or modifying registry/project state. Read other references only when needed for the current workflow.

## Compatibility

The existing Rust daily practice project is a registered Restore-mode project, not a special case. Look up `rust` in `assets/learning-projects.json`, restore it from the configured files, preserve those names, and continue from their recorded state.

## Examples

- "Use this skill to continue my Rust learning plan" -> Restore mode, read the Rust progress files, and continue from the current `pending` or `planned` topic.
- "Create a TypeScript daily learning plan" -> Create mode, initialize a new learning repository with templates and a prerequisite-first weekly plan.
- "I finished today's lesson" -> Completion workflow, mark the earliest `pending` topic as `done` and run configured sync if present.
