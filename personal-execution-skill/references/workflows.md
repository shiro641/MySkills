# PersonalOS Workflows

默认用中文生成新的日报、周复盘、项目记录、自动化候选和面向用户的总结。

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
- 执行步骤
- 预期产物
- 验收标准

## Project Review Heuristics

- 停滞: `最后更新` 超过 14 天。
- 缺少下一步: 没有开放的下一步行动，或进展显示阻塞/停顿。
- 有风险: 包含阻塞项、等待依赖、逾期表达或高不确定性。

## Weekly Review Sources

Read all Daily files in the ISO week, then summarize:

- completed checkboxes
- unfinished checkboxes
- Waiting and Blocked
- project changes
- automation candidates added or completed
- next-week suggestions

## Daily Thread Announcement

Every Daily generation has two outputs:

- A Markdown file at `dailies/YYYY-MM-DD.md`.
- A separate Codex chat thread in the current project where the Daily is delivered to the user in Chinese.

Use the script output section headed `--- 日报会话播报正文 ---` as the initial prompt for the new thread. If that section is unavailable, read the generated Daily file and send its contents with a short Chinese opening line. Title the thread `日报 YYYY-MM-DD` when thread-title tools are available.
