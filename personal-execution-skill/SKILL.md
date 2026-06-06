---
name: personal-execution-skill
description: Use this skill to create and operate a local Git-backed Personal OS for daily execution, projects, waiting/blocked tracking, automation candidates, weekly reviews, execution logs, and habit/routine management. Trigger when the user asks to use add task, call add-task, add a task, add a habit, make something a habit/routine/惯例/习惯/定式任务, mark something complete, update task status after completion, generate a daily plan, bootstrap a PersonalOS repository, review projects, detect Codex automation opportunities, or produce weekly reviews. This is a skill-backed script workflow, not an MCP tool.
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

`add-task`, `complete-task`, and `habit` are script-backed capabilities in `scripts/personal_os.py`. They are not separate MCP tools, so `tool_search` may not find them.

## Quick Start

Prefer the bundled script for deterministic operations:

```bash
python3 <skill_dir>/scripts/personal_os.py bootstrap <target_repo>
python3 <skill_dir>/scripts/personal_os.py set-repo <target_repo>
python3 <skill_dir>/scripts/personal_os.py daily --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py add-task "task text" --type today
python3 <skill_dir>/scripts/personal_os.py add-task "task text" --type habit
python3 <skill_dir>/scripts/personal_os.py complete-task "task text" --date YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py weekly-review --week-start YYYY-MM-DD
python3 <skill_dir>/scripts/personal_os.py project-review
```

Bootstrap records the user's PersonalOS repository path in the skill config at `<skill_dir>/state/config.json`. After bootstrap, later commands may omit `<target_repo>` and will use the recorded default repository. If the user has multiple PersonalOS repositories, pass the repository path explicitly.

Read `references/workflows.md` before manually editing repository content or when a user asks for nuanced classification. Read `references/schema.md` when creating or repairing files.

When generating a Daily, also create a new Codex chat thread in the current project and send the generated Daily to the user in that new thread. Use the Codex thread tools (`create_thread`, and `set_thread_title` when available). The script prints a `--- 日报会话播报正文 ---` section; use that exact section as the new thread's initial prompt whenever possible.

## When To Use

Use this skill when the user asks to:

- create or bootstrap a PersonalOS repository
- generate a daily task list or daily review
- add, classify, or route a task
- add a habit, routine, 惯例, 习惯, or 定式任务
- complete a task and update related records
- generate a weekly review
- review long-term projects
- identify tasks suitable for Codex automation
- maintain Waiting, Blocked, Archive, Scheduled, or Habit records

## Capabilities And Triggers

- `bootstrap_personal_os`: "create PersonalOS", "bootstrap my Personal OS", "初始化 PersonalOS", "建立 Personal Chief of Staff 仓库"
- `set_default_repo`: "记录 PersonalOS 位置", "设置默认 PersonalOS 仓库", "我的 PersonalOS 在这里"
- `generate_daily`: "generate daily", "生成今日任务", "daily plan", "明天/今天的 Daily"
- `add_task`: "add task", "新增任务", "记一条 Waiting", "加入长期项目", "加入自动化候选"
- `add_habit`: "作为 habit", "作为惯例", "作为习惯", "后续告诉你完成时更新状态", "每天/每周带入"
- `complete_task`: "complete task", "完成任务", "mark done", "把 X 标记完成", "我完成了 X", "更新这个任务的状态"
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
│   ├── today.md
│   ├── scheduled.md
│   ├── automation-candidates.md
│   └── archive.md
├── state/
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

1. Always read relevant files before editing: today's Daily, `inbox.md`, `tasks/*.md`, `state/waiting.md`, `state/blocked.md`, and relevant project files.
2. Never overwrite user content. Append, update checklist markers, or add dated sections.
3. Preserve Markdown headings and checkboxes.
4. Use Intent First for `add_task`: if the user explicitly says the type, honor it.
5. Only classify automatically when the user did not specify a type.
6. Do not add suitable Codex automation work to manual todos. Route it to `tasks/automation-candidates.md` with Codex Prompt, execution steps, expected artifacts, and acceptance criteria.
7. After modifications, show `git diff --stat` and a focused `git diff`.
8. At key points, suggest a commit. For bootstrap, create the initial commit automatically.
9. Prefer Chinese for generated content and user-facing summaries. Preserve existing user-authored language when editing old files unless the operation is regenerating a template/report.
10. For every `generate_daily` operation, after the Markdown file is created or found, create a separate chat thread under the current project and deliver the Daily there.

## Intent First Task Types

If explicitly specified, route exactly as requested:

- 今日任务 / Today Task -> today's Daily and `tasks/today.md`
- 长期项目 / Project -> `projects/<slug>.md`
- 定时任务 / 周期任务 / Scheduled Task -> `tasks/scheduled.md`
- Codex 自动化任务 / Automation Candidate -> `tasks/automation-candidates.md`
- Waiting -> `state/waiting.md`
- Blocked -> `state/blocked.md`
- 归档记录 / Archive -> `tasks/archive.md`
- 习惯 / 定式任务 / Habit -> `state/habits.md`

## Automatic Classification

When intent is not explicit:

- Waiting: task depends on a named person, reply, approval, delivery, vendor, or external owner.
- Blocked: task cannot proceed because of missing access, decision, dependency, error, or unresolved risk.
- Scheduled Task: task contains a date, recurrence, deadline, "every", "daily", "weekly", or "monthly".
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

1. Read yesterday's Daily if present.
2. Read `tasks/today.md`, `projects/*.md`, `state/waiting.md`, `state/blocked.md`, `inbox.md`, and `tasks/automation-candidates.md`.
3. Generate `dailies/YYYY-MM-DD.md` in Chinese with: yesterday done, yesterday unfinished, Waiting, Blocked, project progress, today's suggestions, task checklist, new tasks, and review.
4. Capture the script's `--- 日报会话播报正文 ---` section or read the generated Daily file and compose a concise Chinese announcement.
5. Create a new Codex thread in the current project, using the local project environment, with the announcement as the initial prompt. Title it `日报 YYYY-MM-DD` when a thread-title tool is available.
6. Show diff and suggest commit.

### add_task

1. Identify explicit user type first.
2. If no explicit type exists, classify using the automatic rules.
3. If automation candidate, write the automation record and do not add to manual todos.
4. Otherwise append to the correct file and today's Daily when applicable.
5. Show diff and suggest commit.

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
4. Append `logs/execution-log.md`.
5. Update `state/stats.md` when possible.
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

Habit support is reserved in `state/habits.md` and `templates/habit.md`. Treat habits as recurring tasks with frequency, auto-include setting, completion log, streak, and completion rate.

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
