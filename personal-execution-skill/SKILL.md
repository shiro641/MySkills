---
name: personal-execution-skill
description: 
    Use this skill to manage a Git-backed Personal OS for planning and execution.
    Trigger when the user wants to create or update schedules, plans, tasks, habits, projects, project subtasks, project progress, milestones, daily reviews, learnings/insights, execution logs, or automation workflows.
    Also trigger when the user asks to split a long-term project, confirm a project checklist, update task content/type/time, complete a task with learnings, or sync project subtasks with scheduled tasks.
---

# Personal Execution Skill

Use this skill for a local Git repository that acts as a Personal Chief of Staff system. It manages daily execution, long-running projects, Waiting and Blocked items, automation candidates, weekly reviews, execution logs, and future habit loops.

默认使用中文生成所有面向用户的内容，包括日报、周复盘、项目模板、任务说明、自动化候选记录和最终回复。Markdown 文件仍然是标准载体，但正文标题和占位说明应为中文。

## High Priority Routing

If the user says any of the following, use this skill immediately instead of searching for an MCP tool or plugin:

- "调用 add task"
- "调用 add-task"
- "add task"
- "添加任务"
- "新增任务"
- "作为 habit"
- "作为惯例"
- "作为习惯"
- "后续我告诉你完成了，你帮我更新状态"
- "我完成了，帮我标记完成"
- "mark done"
- "complete task"
- "remove task"
- "删除任务"
- "移除任务"

`add-task`, `complete-task`, `remove-task`, and `habit` are script-backed capabilities in `scripts/personal_os.py`. They are not separate MCP tools, so `tool_search` may not find them.

## Quick Start

Prefer the bundled script for deterministic operations:

```bash
python3 <skill_dir>/scripts/personal_os.py bootstrap <target_repo>
python3 <skill_dir>/scripts/personal_os.py set-repo <target_repo>
python3 <skill_dir>/scripts/personal_os.py daily --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py add-task "task text" --type today
python3 <skill_dir>/scripts/personal_os.py add-task "task text" --type today --started
python3 <skill_dir>/scripts/personal_os.py add-task "project text" --type project
python3 <skill_dir>/scripts/personal_os.py add-task "task text" --type habit
python3 <skill_dir>/scripts/personal_os.py complete-task "task text，收获为xxx" --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py update-task "old task text" --new-task "new task text" --type scheduled --due-date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD --confirm 1
python3 <skill_dir>/scripts/personal_os.py update-project "project name" "当前进度50%，目前已完成xxx，收获为xxx" --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py plan-project "project name" --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py plan-project "project name" --date YYYY-MM-DD --started
python3 <skill_dir>/scripts/personal_os.py plan-project "project name" --date YYYY-MM-DD --confirm
python3 <skill_dir>/scripts/personal_os.py weekly-review --week-start YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py project-review
python3 <skill_dir>/scripts/personal_os.py backfill-started
```

Bootstrap records the user's PersonalOS repository path in the skill config at `<skill_dir>/state/config.json`. After bootstrap, later commands may omit `<target_repo>` and will use the recorded default repository. If the user has multiple PersonalOS repositories, pass the repository path explicitly.

For all core operations, especially `daily`, run the bundled script instead of manually drafting Markdown. Manual generation may invent generic productivity advice or time blocks that are not present in the user's PersonalOS data.

默认新增任务都是“未启动”。只有用户明确说“添加并启动”或等价意思时，才在脚本命令里加 `--started`。未启动任务没有截止日期，只有优先级；日报的执行清单与近期任务不应包含未启动任务，而应在“推荐任务”模块中展示。

Read `references/workflows.md` before manually editing repository content or when a user asks for nuanced classification. Read `references/schema.md` when creating or repairing files.

When generating a Daily, also create a new Codex chat thread in the current project and send the generated Daily to the user in that new thread. Use the Codex thread tools (`create_thread`, and `set_thread_title` when available). The script prints a `--- 日报会话播报正文 ---` section; use that exact section as the new thread's initial prompt whenever possible.

## When To Use

Use this skill when the user asks to:

- create or bootstrap a PersonalOS repository
- generate a daily task list or daily review
- add, classify, or route a task
- add a habit, routine, 惯例, 习惯, or 定式任务
- complete a task and update related records
- remove a task after listing candidate matches and receiving explicit confirmation
- generate a weekly review
- review long-term projects
- identify tasks suitable for Codex automation
- maintain Waiting, Blocked, Archive, Scheduled, or Habit records

## Capabilities And Triggers

- `bootstrap_personal_os`: "create PersonalOS", "bootstrap my Personal OS", "初始化 PersonalOS", "建立 Personal Chief of Staff 仓库"
- `set_default_repo`: "记录 PersonalOS 位置", "设置默认 PersonalOS 仓库", "我的 PersonalOS 在这里"
- `generate_daily`: "generate daily", "生成今日任务", "daily plan", "明天/今天的 Daily"
- `add_task`: "add task", "新增任务", "记一条 Waiting", "加入长期项目", "加入自动化候选"
- `add_project_task`: "添加长期任务", "添加长期项目", "作为 project", "作为长期任务", "加入长期项目"
- `add_habit`: "作为 habit", "作为惯例", "作为习惯", "后续告诉你完成时更新状态", "每天/每周带入"
- `complete_task`: "complete task", "完成任务", "mark done", "把 X 标记完成", "我完成了 X", "更新这个任务的状态"
- `update_task`: "更新任务", "修改任务", "把任务改成", "改截止日期", "改成 schedule/today/habit/project"
- `remove_task`: "remove task", "删除任务", "移除任务", "把 X 从任务里删掉"
- `update_project`: "更新项目进度", "当前进度", "目前已完成", "项目收获", "里程碑"
- `plan_project`: "拆分长期任务", "拆分项目", "长期任务清单", "子任务", "确认项目清单"
- `generate_weekly_review`: "weekly review", "周复盘", "生成本周总结"
- `project_review`: "review projects", "项目巡检", "哪些项目停滞/有风险"
- `automation_detector`: "能不能交给 Codex", "适合自动化吗", "automation candidate"
- `habit_manager`: "habit", "习惯", "每天/每周自动带入"

## Standard PersonalOS Structure

```text
PersonalOS/
├── README.md
├── inbox.md
├── dailies/
│   └── .gitkeep
├── weekly-reviews/
│   └── .gitkeep
├── projects/
│   └── .gitkeep
├── tasks/
│   └── today.md
├── state/
│   ├── schedule.md
│   ├── automation-candidates.md
│   ├── archive.md
│   ├── waiting.md
│   ├── blocked.md
│   ├── habits.md
│   └── stats.md
├── logs/
│   └── execution-log.md
└── templates/
    ├── daily.md
    ├── weekly-review.md
    ├── project.md
    ├── automation-candidate.md
    └── habit.md
```

## Operating Rules

1. Always read relevant files before editing: today's Daily, `inbox.md`, `tasks/today.md`, `state/*.md`, and relevant project files.
2. Never overwrite user content. Append, update checklist markers, or add dated sections.
3. Preserve Markdown headings and checkboxes.
4. Use Intent First for `add_task`: if the user explicitly says the type, honor it.
5. Only classify automatically when the user did not specify a type.
6. Do not add suitable Codex automation work to manual todos. Route it to `state/automation-candidates.md` with Codex Prompt, execution steps, expected artifacts, and acceptance criteria.
7. After modifications, show `git diff --stat` and a focused `git diff`.
8. At key points, suggest a commit. For bootstrap, create the initial commit automatically.
9. Prefer Chinese for generated content and user-facing summaries. Preserve existing user-authored language when editing old files unless the operation is regenerating a template/report.
10. For every `generate_daily` operation, after the Markdown file is created or found, create a separate chat thread under the current project and deliver the Daily there.
11. Never hand-write a Daily from scratch. Always run `scripts/personal_os.py daily`. Do not invent "today's most important output", "60 to 90 minute execution blocks", calendar assumptions, risks, meetings, or task items unless they come from PersonalOS files or the script output.

## Intent First Task Types

If explicitly specified, route exactly as requested:

- 今日任务 / Today Task -> today's Daily and `tasks/today.md`
- 长期项目 / Project -> `projects/<slug>.md`
- 定时任务 / 截止日期任务 / Scheduled Task -> `state/schedule.md`
- Codex 自动化任务 / Automation Candidate -> `state/automation-candidates.md`
- Waiting -> `state/waiting.md`
- Blocked -> `state/blocked.md`
- 归档记录 / Archive -> `state/archive.md`
- 习惯 / 定式任务 / Habit -> `state/habits.md`

## Automatic Classification

When intent is not explicit:

- Waiting: task depends on a named person, reply, approval, delivery, vendor, or external owner.
- Blocked: task cannot proceed because of missing access, decision, dependency, error, or unresolved risk.
- Scheduled Task: task has a clear due date, execution date, reminder date, or time-bound deadline. Store the date/deadline in `state/schedule.md` so it can be surfaced later.
- Habit: task describes a repeated behavior to cultivate or track over time, especially "daily", "weekly", "monthly", "每天", "每周", "每月", "定式", or "习惯", and should keep frequency, auto-include, completion log, streak, and completion rate in `state/habits.md`.
- Automation Candidate: task is file/code/data/document/email/search/report generation that Codex can likely execute end-to-end.
- Project: task implies a multi-step outcome lasting more than one day or mentions project, milestone, launch, build, research, design, strategy.
- Archive: task is explicitly a past record or completed log.
- Today Task: default for immediate human action.

## Core Workflows

### bootstrap_personal_os

Run the script:

```bash
python3 <skill_dir>/scripts/personal_os.py bootstrap <target_repo>
```

It creates the standard structure, writes templates and empty factual ledgers, initializes Git, and commits. Bootstrap must not invent people, tasks, projects, habits, automation candidates, dailies, weekly reviews, or other user schedule data.

After bootstrap, record the initialized repository as the default PersonalOS location in `<skill_dir>/state/config.json`. This is user-private runtime state, not source-controlled skill content. In later commands, if the user does not provide a repository path, use the recorded default.

### set_default_repo

When the user already has a PersonalOS repository and wants this skill to remember its location, run:

```bash
python3 <skill_dir>/scripts/personal_os.py set-repo <target_repo>
```

The command validates that the target has the PersonalOS structure, then writes `<skill_dir>/state/config.json`. Use this before daily/add-task/complete-task when the repository was created outside the current session.

### generate_daily

1. Run `python3 <skill_dir>/scripts/personal_os.py daily --date YYYY-MM-DD` unless the user explicitly provides a different repository path.
2. Do not manually create or rewrite the Daily file before running the script.
3. Capture the script's `--- 日报会话播报正文 ---` section or read the generated Daily file and compose a concise Chinese announcement.
4. Create a new Codex thread in the current project, using the local project environment, with the announcement as the initial prompt. Title it `日报 YYYY-MM-DD` when thread-title tools are available.
5. Show diff and suggest commit.

The Daily content must stay grounded in PersonalOS files and script output. Avoid generic coaching phrases such as "今日重点是先定义今天唯一最重要的产出" or "安排一个 60 到 90 分钟的启动执行块" unless those exact ideas are already present in the user's files.
Daily files include a `近期需要处理的任务` section based on open Scheduled tasks. This section should exclude today's tasks, first list all tasks due from tomorrow through the next 3 days, and if that yields fewer than 3 tasks, fill the list with later open Scheduled tasks by nearest due date until it has up to 3 tasks. Place `今日建议` after `今日新增任务` but before `今日复盘`. Suggestions should be grounded in the generated Daily content, including near-term tasks, today's tasks, Habit status, Waiting, Blocked, projects, and automation candidates.

### add_task

1. Identify explicit user type first.
2. If no explicit type exists, classify using the automatic rules.
3. If automation candidate, write the automation record and do not add to manual todos.
4. Otherwise append to the correct file and today's Daily when applicable.
5. For Project tasks, create/update the project and automatically run the `plan-project` draft flow immediately. Show the proposed subtask plan to the user for confirmation. Do not write the subtask checklist or scheduled tasks until the user confirms and you run `plan-project --confirm`.
6. The `plan-project` draft should default to a confirmable checklist with concrete actions, due dates, and acceptance criteria. Avoid abstract phase-only skeletons unless they also name the specific action and deliverable.
7. Show diff and suggest commit.

For phrasing like "添加一个长期任务/长期项目" or "把 X 作为 project", classify it as an explicit Project request and run:

```bash
python3 <skill_dir>/scripts/personal_os.py add-task "project text" --type project
```

This creates or updates `projects/<slug>.md`, appends the project as a next action, and prints a project subtask plan draft. The draft is not written until the user confirms and `plan-project --confirm` is run.

For phrasing like "调用 add task，将这个单词的学习作为 habit，后续我告诉你我完成了的时候，你同时帮我更新一下我这个任务的状态", classify it as an explicit Habit request and run:

```bash
python3 <skill_dir>/scripts/personal_os.py add-task <target_repo> "这个单词的学习" --type habit
```

Tell the user that future completion messages such as "我完成了这个单词的学习" should use `complete-task` to update matching records and append the execution log.

If a default PersonalOS repository has already been recorded by bootstrap, the shorter form is preferred:

```bash
python3 <skill_dir>/scripts/personal_os.py add-task "这个单词的学习" --type habit
```

### complete_task

1. Read today's Daily and likely source files.
2. Mark matching open checkbox complete.
3. Update related project, Waiting, or Blocked status when a match exists.
4. If the completion message includes learning language such as `收获为...`, `学到了...`, `今天我学到了...`, or `learned...`, extract the concrete learning.
5. Append `logs/execution-log.md`; include the extracted learning when present.
6. Append the extracted learning under today's Daily `今日复盘 -> 收获`.
7. Update `state/stats.md` when possible.
8. Show diff and suggest commit.

### update_task

Use this workflow when the user wants to change task content, type, or time.

```bash
python3 <skill_dir>/scripts/personal_os.py update-task "old task text" --new-task "new task text" --type scheduled --due-date YYYY-MM-DD
```

- Changing a Today task to a future due date moves it to `state/schedule.md`.
- Changing a Scheduled task to today's date also adds it to `tasks/today.md` so Daily generation can surface it.
- Daily generation also promotes scheduled tasks whose due date is today into `tasks/today.md`.
- When a Scheduled task is linked to a project subtask (`项目:` and `子任务:` metadata), updates or removals sync the project `子任务清单`.

### update_project

Use this workflow when the user reports project progress, milestones, or learnings:

```bash
python3 <skill_dir>/scripts/personal_os.py update-project "project name" "当前进度50%，目前已完成xxx，收获为xxx" --date YYYY-MM-DD
```

The script updates the project `进展`, appends dated `里程碑` and `复盘笔记`, refreshes `最后更新`, and writes extracted learning into today's Daily `今日复盘 -> 收获`.

### plan_project

Use this workflow for long-term project/task decomposition.

When `add-task` creates or updates a Project, it must automatically execute this draft step right away. Treat the draft checklist as part of the project creation response, not as a separate optional follow-up.

1. Draft first, without writing:

```bash
python3 <skill_dir>/scripts/personal_os.py plan-project "project name" --date YYYY-MM-DD
```

2. Send the checklist to the user for confirmation or modification. The default checklist should be concrete enough that the user can directly confirm it:
   - each item should be a task someone can start immediately
   - each item should include a due date
   - each item should include a clear acceptance criterion
   - when the project type is inferable from the title, prefer a domain-relevant breakdown over a generic stage skeleton
3. After the user confirms, write the checklist into the project and add each subtask to `state/schedule.md`:

```bash
python3 <skill_dir>/scripts/personal_os.py plan-project "project name" --date YYYY-MM-DD --confirm
```

Each generated scheduled subtask carries `项目:` and `子任务:` metadata so later `update-task` or confirmed `remove-task` operations can synchronize the project checklist.
Schedule entries should carry `状态: open`, `截止: YYYY-MM-DD`, and `完成:`. Do not use `[ ]` / `[x]` checkbox markers inside `state/schedule.md`; `状态` is the source of truth there. When completed, update `state/schedule.md` to `状态: done` and `完成: YYYY-MM-DD`, and update the linked project subtask checklist to `[x]`, `状态: done`, and `完成: YYYY-MM-DD`.

### remove_task

Use this workflow when the user says "remove xxx task", "删除任务 xxx", "移除任务 xxx", or asks to delete a task from the current task pool.

1. Run the script without `--confirm` first:

```bash
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD
```

2. Show the numbered candidate list to the user. Candidates can come from today's Daily, `tasks/today.md`, `state/schedule.md`, `state/automation-candidates.md`, `state/archive.md`, `state/waiting.md`, `state/blocked.md`, `state/habits.md`, and `projects/*.md`.
3. Do not delete anything until the user explicitly confirms one or more candidate numbers, or confirms all candidates.
4. After confirmation, run:

```bash
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD --confirm 1
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD --confirm 1,3
python3 <skill_dir>/scripts/personal_os.py remove-task "task text" --date YYYY-MM-DD --confirm all
```

5. For checkbox tasks, delete the matching line. For Habit records and automation candidate records, delete the whole matched block. For a project candidate, delete the project file only when the confirmed candidate is the project itself.
6. Show diff and suggest commit.

### generate_weekly_review

1. Read Daily files for the week, project files, Waiting, Blocked, and automation candidates.
2. Create `weekly-reviews/YYYY-Www.md`.
3. Include completed work, unfinished work, Waiting summary, Blocked summary, project progress, automation benefit, and next-week suggestions.
4. Show diff and suggest commit.

### project_review

1. Read all `projects/*.md`.
2. Identify stale projects, stalled projects, and risky projects.
3. Update project review notes or report recommendations to the user.

### habit_manager

Habit support is reserved in `state/habits.md` and `templates/habit.md`. Treat habits as repeated behaviors with frequency, auto-include setting, completion log, streak, and completion rate. Do not route a habit to `state/schedule.md` merely because it repeats; use Scheduled only when the item is anchored to a due date, execution date, or reminder date.

## Validation

After any operation:

```bash
git -C <target_repo> status --short
git -C <target_repo> diff --stat
git -C <target_repo> diff
```

For script health:

```bash
python3 <skill_dir>/scripts/personal_os.py --help
```
