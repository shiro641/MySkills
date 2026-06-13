# PersonalOS Schema

This file defines the canonical repository layout used by `personal-execution-skill`.

All newly generated user-facing Markdown content should be written in Chinese by default.

## Files

- `README.md`: repo purpose, operating loop, and conventions.
- `inbox.md`: unprocessed raw input.
- `dailies/YYYY-MM-DD.md`: one daily execution file per date.
- `weekly-reviews/YYYY-Www.md`: weekly review for ISO week.
- `projects/*.md`: one long-term project per file.
- `tasks/today.md`: today's execution ledger and completion surface.
- `state/schedule.md`: tasks with due dates, execution dates, reminder dates, or time-bound deadlines.
- `state/automation-candidates.md`: Codex automation candidates.
- `state/archive.md`: completed or historical records.
- `state/waiting.md`: external-owner Waiting items.
- `state/blocked.md`: blocked work and unblock criteria.
- `state/habits.md`: habit definitions and future completion records.
- `state/stats.md`: lightweight execution counters.
- `logs/execution-log.md`: dated task completion log.
- `templates/*.md`: reusable Markdown templates copied during bootstrap.

## Daily Required Sections

- 昨日完成
- 昨日未完成
- 等待中
- 阻塞项
- 长期项目进展
- 近3天需要处理任务
- 推荐任务
  - 推荐启动任务
  - 推荐启动 Habit
- 今日任务清单
  - Habit
  - 其他任务
- 今日新增任务
- 今日建议
- 今日复盘

## Project Required Fields

- 目标
- 当前阶段
- 启动状态
- 优先级
- 下一步行动
- 进展
- 里程碑
- 最后更新
- 等待中
- 阻塞项
- 子任务清单
- 复盘笔记

## Schedule Entry Required Fields

- 状态
- 启动
- 截止, required only when `启动 = 已启动`
- 优先级, required only when `启动 = 未启动`
- 完成
- 项目, when linked to a project
- 子任务, when linked to a project subtask

Schedule entries in `state/schedule.md` do not use checkbox markers. The `状态` field is the source of truth (`open`, `done`, etc.). Project subtask checklists may still use checkboxes as a project-local execution view.

## Automation Candidate Required Fields

- 来源任务
- 启动状态
- 优先级
- 为什么适合 Codex
- Codex Prompt
- 执行步骤
- 预期产物
- 验收标准
- 状态

## Habit Required Fields

- Habit
- 频率
- 自动加入日报
- 启动
- 优先级
- 完成记录
- 当前连续天数
- 完成率
