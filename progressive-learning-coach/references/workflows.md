# Workflows

## Weekly Plan

1. Resolve the learning task through `assets/learning-projects.json`.
2. Restore state from the registered project files.
3. Carry over unfinished `pending` and `planned` topics.
4. Select 3 to 5 topics by default, or fewer if the remaining week has fewer realistic study days.
5. Sort by prerequisite readiness, foundation value, common use, question count, and carryover.
6. Keep advanced topics in `backlog` when prerequisites are missing.
7. Update the registered weekly plan file.
8. Tell the learner the week scope, order, carryovers, and why each topic matters.

## Daily Learning Card

1. Resolve the learning task through `assets/learning-projects.json`.
2. Restore state from the registered project files.
3. If any `pending` exists, do not send a new topic. Remind the learner to continue the earliest `pending`.
4. If no `pending` exists, select the highest-priority ready `planned` topic from the current week.
5. Mark that topic `pending` in the registered knowledge status and weekly plan files.
6. Draft the card using `teaching-card.md`.
7. Include completion phrases from the project instructions.

## Learner Question

1. Resolve the learning task through `assets/learning-projects.json`.
2. Identify the current topic, usually the earliest `pending`.
3. Answer the question directly at the learner's current level.
4. Append the question, answer summary, and follow-up implications to the registered question log.
5. Increment the topic's question count.
6. If the question reveals a weak prerequisite, increase that prerequisite's priority or add it to `backlog`.
7. Do not mark the topic complete unless the learner clearly confirms completion.

## Completion Confirmation

1. Resolve the learning task through `assets/learning-projects.json`.
2. Confirm the learner expressed completion with a phrase such as `finish learning`, `done`, `学完了`, `完成学习`, `记完了`, or a project-specific equivalent.
3. Mark only the earliest `pending` topic as `done`.
4. Write the completion date.
5. Update recent completion summary fields.
6. Run external sync commands only if the project instructions require them.
7. Do not immediately send the next topic unless the learner explicitly asks.

## Register Existing Plan

1. Ask for the learning task name and state directory if either is missing.
2. Inspect the directory for learning progress files.
3. Map the semantic file roles to the actual file names.
4. Add or update the task entry in `assets/learning-projects.json`.
5. Restore state from the registered files.

## Create Learning Plan

1. Ask for the learning task name and state directory if either is missing.
2. Create the directory if needed.
3. Initialize the standard files from `assets/templates/`.
4. Add or update the task entry in `assets/learning-projects.json`.
5. Initialize git when creating a new standalone repository.

## Route Reset

1. Preserve history.
2. Move unsuitable advanced `pending` and `planned` topics to `backlog`.
3. Add or prioritize prerequisite topics.
4. Update the learning route mode.
5. Generate a smaller, prerequisite-first weekly plan.

## Review Planning

Use review when the learner asks to review, when question count is high, or when old `done` topics are prerequisites for upcoming work. Prefer short retrieval exercises over re-teaching full lessons.
