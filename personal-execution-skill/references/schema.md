# PersonalOS Schema

This file defines the canonical repository layout used by `personal-execution-skill`.

All newly generated user-facing Markdown content should be written in Chinese by default.

## Files

- `README.md`: repo purpose, operating loop, and conventions.
- `inbox.md`: unprocessed raw input.
- `dailies/YYYY-MM-DD.md`: one daily execution file per date.
- `weekly-reviews/YYYY-Www.md`: weekly review for ISO week.
- `projects/*.md`: one long-term project per file.
- `tasks/today.md`: rolling today task ledger.
- `tasks/scheduled.md`: scheduled and recurring tasks.
- `tasks/automation-candidates.md`: Codex automation candidates.
- `tasks/archive.md`: completed or historical records.
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
- 今日建议
- 今日任务清单
- 今日新增任务
- 今日复盘

## Project Required Fields

- 目标
- 当前阶段
- 下一步行动
- 进展
- 最后更新
- 等待中
- 阻塞项
- 复盘笔记

## Automation Candidate Required Fields

- 来源任务
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
- 完成记录
- 当前连续天数
- 完成率
