#!/usr/bin/env python3
"""PersonalOS helper for personal-execution-skill."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "templates"

DIRS = [
    "dailies",
    "weekly-reviews",
    "projects",
    "tasks",
    "state",
    "logs",
    "templates",
]

TASK_TYPE_ALIASES = {
    "today": "today",
    "today task": "today",
    "今日任务": "today",
    "project": "project",
    "长期项目": "project",
    "scheduled": "scheduled",
    "scheduled task": "scheduled",
    "定时任务": "scheduled",
    "周期任务": "scheduled",
    "automation": "automation",
    "automation candidate": "automation",
    "codex 自动化任务": "automation",
    "waiting": "waiting",
    "blocked": "blocked",
    "archive": "archive",
    "归档记录": "archive",
    "habit": "habit",
    "习惯": "habit",
    "定式任务": "habit",
}


def today() -> dt.date:
    return dt.date.today()


def parse_date(value: str | None) -> dt.date:
    if not value:
        return today()
    return dt.date.fromisoformat(value)


def iso_week_start(value: str | None) -> dt.date:
    if value:
        day = dt.date.fromisoformat(value)
    else:
        day = today()
    return day - dt.timedelta(days=day.weekday())


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower()).strip("-")
    return slug[:80] or "untitled"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def ensure_repo(root: Path) -> None:
    if not root.exists():
        raise SystemExit(f"Repository does not exist: {root}")
    for dirname in ["dailies", "tasks", "state", "projects"]:
        if not (root / dirname).exists():
            raise SystemExit(f"Not a PersonalOS repository, missing {dirname}: {root}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content.rstrip() + "\n", encoding="utf-8")


def append(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read(path)
    spacer = "" if not existing or existing.endswith("\n") else "\n"
    path.write_text(existing + spacer + content.rstrip() + "\n", encoding="utf-8")


def render_template(name: str, **values: str) -> str:
    text = read(TEMPLATE_DIR / name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def checklist_items(text: str, checked: bool | None = None) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^\s*-\s+\[([ xX])\]\s+(.*)$", line)
        if not match:
            continue
        is_checked = match.group(1).lower() == "x"
        if checked is None or checked == is_checked:
            items.append(match.group(2).strip())
    return items


def bullet_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and "[ ]" not in stripped and "[x]" not in stripped.lower():
            lines.append(stripped[2:].strip())
    return lines


def copy_templates(root: Path) -> None:
    for template in TEMPLATE_DIR.glob("*.md"):
        write_new(root / "templates" / template.name, read(template))


def bootstrap(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for dirname in DIRS:
        (root / dirname).mkdir(parents=True, exist_ok=True)
    copy_templates(root)

    date = parse_date(args.date).isoformat()
    week_label = parse_date(args.date).strftime("%G-W%V")
    write_new(root / "README.md", repo_readme(root.name))
    write_new(root / "inbox.md", "# 收件箱\n\n- [ ] 分拣这条 PersonalOS 示例输入。\n")
    write_new(root / "tasks" / "today.md", "# 今日任务\n\n- [ ] 检查 PersonalOS 目录结构\n")
    write_new(root / "tasks" / "scheduled.md", "# 定时任务\n\n- [ ] 每周五做周复盘\n")
    write_new(root / "tasks" / "archive.md", "# 归档\n\n- 暂无归档记录。\n")
    write_new(root / "state" / "waiting.md", "# 等待中\n\n- [ ] Alice 确认 Q3 预算负责人 | 负责人: Alice | 开始: " + date + "\n")
    write_new(root / "state" / "blocked.md", "# 阻塞项\n\n- [ ] 示例数据看板因缺少 API token 暂停 | 开始: " + date + " | 解法: 获取 token\n")
    write_new(root / "state" / "habits.md", "# 习惯\n\n" + render_template("habit.md", habit_name="每日动态规划练习"))
    write_new(root / "state" / "stats.md", "# 统计\n\n- 已完成任务数: 0\n- 已创建自动化候选数: 1\n")
    write_new(root / "logs" / "execution-log.md", "# 执行日志\n\n- " + date + " 初始化 PersonalOS 仓库。\n")
    write_new(root / "projects" / "demo-project.md", render_template("project.md", project_name="示例项目", date=date))
    write_new(root / "tasks" / "automation-candidates.md", "# Automation Candidates\n\n" + render_template(
        "automation-candidate.md",
        date=date,
        title="生成每周指标报告",
        source_task="根据 CSV 导出生成每周指标摘要。",
        codex_prompt="检查 CSV 导出，计算环比指标，创建 Markdown 摘要，并附上验证说明。",
    ))
    write_new(root / "dailies" / f"{date}.md", render_daily(root, parse_date(args.date)))
    write_new(root / "weekly-reviews" / f"{week_label}.md", render_weekly(root, iso_week_start(args.date)))

    if not (root / ".git").exists():
        run(["git", "init"], cwd=root)
    run(["git", "add", "."], cwd=root)
    if run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode != 0:
        run(["git", "commit", "-m", "Bootstrap PersonalOS"], cwd=root)
    print(f"已初始化 PersonalOS: {root}")
    print_git_status(root)


def repo_readme(name: str) -> str:
    return f"""# {name}

这个仓库是一个 PersonalOS：用 Git 管理的个人执行系统，用于每日推进、长期项目、等待中/阻塞项、自动化候选、周复盘、执行日志和习惯维护。

## 运转循环

1. 把原始输入收进 `inbox.md`。
2. 在 `dailies/` 生成或更新当天日报。
3. 把事项路由到今日任务、项目、等待中、阻塞项、定时任务、自动化候选、归档或习惯。
4. 在原位置标记完成，并记录到 `logs/execution-log.md`。
5. 每周巡检项目，并提交确认后的变更。

## 核心目录

- `dailies/`: 每日计划与复盘。
- `weekly-reviews/`: 周复盘。
- `projects/`: 长期项目状态。
- `tasks/`: 今日、定时、自动化候选和归档台账。
- `state/`: 等待中、阻塞项、习惯和统计。
- `logs/`: 执行历史。
- `templates/`: 标准 Markdown 模板。
"""


def classify_task(text: str, explicit_type: str | None = None) -> str:
    if explicit_type:
        key = explicit_type.strip().lower()
        if key in TASK_TYPE_ALIASES:
            return TASK_TYPE_ALIASES[key]
        raise SystemExit(f"Unknown task type: {explicit_type}")
    lowered = text.lower()
    if re.search(r"\b(waiting|wait for|follow up|reply|approval|vendor|alice|bob)\b|等|等待|回复|审批", lowered):
        return "waiting"
    if re.search(r"\b(blocked|stuck|cannot|can't|missing|dependency|error|risk)\b|卡住|阻塞|缺少|风险", lowered):
        return "blocked"
    if re.search(r"\b(generate|write|draft|summari[sz]e|analy[sz]e|refactor|script|report|csv|code|codex|automate)\b|生成|脚本|自动化|报告|整理|分析", lowered):
        return "automation"
    if re.search(r"\b(every|daily|weekly|monthly|tomorrow|next week|schedule|recurring)\b|\d{4}-\d{2}-\d{2}|每天|每周|每月|定时|周期", lowered):
        return "scheduled"
    if re.search(r"\b(project|milestone|launch|build|research|strategy|roadmap)\b|项目|长期|里程碑|上线|调研|战略", lowered):
        return "project"
    if re.search(r"\b(archive|record|done|completed)\b|归档|记录", lowered):
        return "archive"
    return "today"


def add_task(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    date = parse_date(args.date)
    task_type = classify_task(args.task, args.type)
    if task_type == "today":
        add_today_task(root, args.task, date)
    elif task_type == "project":
        add_project_task(root, args.task, date)
    elif task_type == "scheduled":
        append(root / "tasks" / "scheduled.md", f"- [ ] {args.task} | 添加: {date.isoformat()}")
    elif task_type == "automation":
        add_automation_candidate(root, args.task, date)
    elif task_type == "waiting":
        append(root / "state" / "waiting.md", f"- [ ] {args.task} | 开始: {date.isoformat()}")
    elif task_type == "blocked":
        append(root / "state" / "blocked.md", f"- [ ] {args.task} | 开始: {date.isoformat()}")
    elif task_type == "archive":
        append(root / "tasks" / "archive.md", f"- {date.isoformat()} {args.task}")
    elif task_type == "habit":
        append(root / "state" / "habits.md", "\n" + render_template("habit.md", habit_name=args.task))
    print(f"已添加任务，类型为 {task_type}: {args.task}")
    print_diff(root)


def add_today_task(root: Path, task: str, date: dt.date) -> None:
    append(root / "tasks" / "today.md", f"- [ ] {task} | 添加: {date.isoformat()}")
    daily = root / "dailies" / f"{date.isoformat()}.md"
    if not daily.exists():
        daily.write_text(render_daily(root, date), encoding="utf-8")
    append_under_heading(daily, "今日新增任务", f"- [ ] {task}")
    append_under_heading(daily, "今日任务清单", f"- [ ] {task}")


def add_project_task(root: Path, task: str, date: dt.date) -> None:
    title = task.split(":", 1)[-1].strip() if ":" in task else task.strip()
    path = root / "projects" / f"{slugify(title)}.md"
    if not path.exists():
        path.write_text(render_template("project.md", project_name=title, date=date.isoformat()), encoding="utf-8")
    append_under_heading(path, "下一步行动", f"- [ ] {task}")
    replace_field(path, "最后更新", date.isoformat())


def add_automation_candidate(root: Path, task: str, date: dt.date) -> None:
    title = task[:60].strip()
    content = render_template(
        "automation-candidate.md",
        date=date.isoformat(),
        title=title,
        source_task=task,
        codex_prompt=f"端到端完成这个任务：{task}。检查相关文件，做必要修改，验证结果，并总结产出。",
    )
    append(root / "tasks" / "automation-candidates.md", "\n" + content)
    increment_stat(root / "state" / "stats.md", "已创建自动化候选数")


def append_under_heading(path: Path, heading: str, line: str) -> None:
    text = read(path)
    pattern = re.compile(rf"(^## {re.escape(heading)}\n)(.*?)(?=^## |\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        append(path, f"\n## {heading}\n\n{line}")
        return
    section = match.group(2).rstrip()
    replacement = match.group(1) + section + ("\n" if section else "") + line + "\n\n"
    path.write_text(text[:match.start()] + replacement + text[match.end():], encoding="utf-8")


def replace_field(path: Path, heading: str, value: str) -> None:
    text = read(path)
    pattern = re.compile(rf"(^## {re.escape(heading)}\n\n)(.*?)(?=\n## |\Z)", re.M | re.S)
    if pattern.search(text):
        text = pattern.sub(rf"\1{value}\n", text, count=1)
    else:
        text += f"\n## {heading}\n\n{value}\n"
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def increment_stat(path: Path, label: str) -> None:
    text = read(path)
    pattern = re.compile(rf"(- {re.escape(label)}: )(\d+)")
    if pattern.search(text):
        text = pattern.sub(lambda m: m.group(1) + str(int(m.group(2)) + 1), text, count=1)
    else:
        text = text.rstrip() + f"\n- {label}: 1\n"
    path.write_text(text, encoding="utf-8")


def daily(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    day = parse_date(args.date)
    path = root / "dailies" / f"{day.isoformat()}.md"
    if path.exists() and not args.force:
        print(f"日报已存在: {path}")
    else:
        path.write_text(render_daily(root, day), encoding="utf-8")
        print(f"已生成日报: {path}")
    print("\n--- 日报会话播报正文 ---")
    print(render_daily_announcement(path, root, day))
    print_diff(root)


def render_daily(root: Path, day: dt.date) -> str:
    yesterday_path = root / "dailies" / f"{(day - dt.timedelta(days=1)).isoformat()}.md"
    yesterday = read(yesterday_path)
    done = checklist_items(yesterday, checked=True) or ["还没有记录已完成事项。"]
    undone = checklist_items(yesterday, checked=False) or checklist_items(read(root / "tasks" / "today.md"), checked=False) or ["没有需要结转的未完成事项。"]
    waiting = checklist_items(read(root / "state" / "waiting.md"), checked=False) or bullet_lines(read(root / "state" / "waiting.md")) or ["当前没有等待中事项。"]
    blocked = checklist_items(read(root / "state" / "blocked.md"), checked=False) or bullet_lines(read(root / "state" / "blocked.md")) or ["当前没有阻塞项。"]
    projects = project_summaries(root)
    automations = checklist_items(read(root / "tasks" / "automation-candidates.md"), checked=False)
    suggestions = ["选择一个最重要的项目下一步行动。", "清空或路由收件箱里的新事项。"]
    if blocked and blocked[0] != "当前没有阻塞项。":
        suggestions.insert(0, "先处理影响最大的阻塞项。")
    if waiting and waiting[0] != "当前没有等待中事项。":
        suggestions.append("给最早的等待中事项发一条简短跟进。")
    if automations:
        suggestions.append("运行或细化一个 Codex 自动化候选。")
    return f"""# 日报 - {day.isoformat()}

## 昨日完成

{as_bullets(done)}

## 昨日未完成

{as_bullets(undone)}

## 等待中

{as_bullets(waiting)}

## 阻塞项

{as_bullets(blocked)}

## 长期项目进展

{as_bullets(projects or ["还没有记录项目进展。"])}

## 今日建议

{as_bullets(suggestions)}

## 今日任务清单

{as_checklist([item for item in undone if not item.startswith("没有需要结转")]) or "- [ ] 检查收件箱"}

## 今日新增任务

- 暂无。

## 今日复盘

- 收获:
- 卡点:
- 结转:
"""


def render_daily_announcement(path: Path, root: Path, day: dt.date) -> str:
    content = read(path) or render_daily(root, day)
    return (
        f"这是 {day.isoformat()} 的中文日报，已同步写入 `{path}`。\n\n"
        f"{content.strip()}\n\n"
        "你可以直接在这个会话里继续追加今日任务、标记完成事项，或让我把某个自动化候选拆成可执行步骤。"
    )


def as_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def as_checklist(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items)


def project_summaries(root: Path) -> list[str]:
    summaries = []
    for path in sorted((root / "projects").glob("*.md")):
        text = read(path)
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        phase_text = extract_section_any(text, ["当前阶段", "Current Phase"]).strip()
        progress_text = extract_section_any(text, ["进展", "Progress"]).strip()
        phase = phase_text.splitlines()[0] if phase_text else "阶段未知"
        progress = progress_text.splitlines()[0] if progress_text else "进展未知"
        summaries.append(f"{title}: {phase}, {progress}")
    return summaries


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def extract_section_any(text: str, headings: list[str]) -> str:
    for heading in headings:
        value = extract_section(text, heading)
        if value:
            return value
    return ""


def complete_task(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    day = parse_date(args.date)
    files = [
        root / "dailies" / f"{day.isoformat()}.md",
        root / "tasks" / "today.md",
        root / "state" / "waiting.md",
        root / "state" / "blocked.md",
        root / "tasks" / "scheduled.md",
        root / "tasks" / "automation-candidates.md",
    ] + sorted((root / "projects").glob("*.md"))
    changed = []
    needle = args.task.lower()
    for path in files:
        text = read(path)
        if not text:
            continue
        new_text, count = re.subn(r"(^\s*-\s+\[ \]\s+.*" + re.escape(args.task) + r".*$)", mark_done, text, flags=re.M | re.I)
        if count == 0:
            new_text, count = mark_fuzzy(text, needle)
        if count:
            path.write_text(new_text, encoding="utf-8")
            changed.append(path)
    append(root / "logs" / "execution-log.md", f"- {day.isoformat()} 已完成: {args.task}")
    increment_stat(root / "state" / "stats.md", "已完成任务数")
    print("已在以下文件中标记完成:")
    for path in changed:
        print(f"- {path}")
    if not changed:
        print("- 没有找到匹配的未完成复选框；已仅记录完成日志。")
    print_diff(root)


def mark_done(match: re.Match[str]) -> str:
    return match.group(1).replace("[ ]", "[x]", 1)


def mark_fuzzy(text: str, needle: str) -> tuple[str, int]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "- [ ]" in line and needle in line.lower():
            lines[i] = line.replace("[ ]", "[x]", 1)
            return "\n".join(lines) + "\n", 1
    return text, 0


def weekly_review(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    start = iso_week_start(args.week_start)
    end = start + dt.timedelta(days=6)
    label = start.strftime("%G-W%V")
    content = render_weekly(root, start)
    path = root / "weekly-reviews" / f"{label}.md"
    if path.exists() and not args.force:
        print(f"周复盘已存在: {path}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"已生成周复盘 {label}: {start} 至 {end}")
    print_diff(root)


def render_weekly(root: Path, start: dt.date) -> str:
    days = [start + dt.timedelta(days=i) for i in range(7)]
    texts = [read(root / "dailies" / f"{day.isoformat()}.md") for day in days]
    completed = []
    unfinished = []
    for text in texts:
        completed.extend(checklist_items(text, checked=True))
        unfinished.extend(checklist_items(text, checked=False))
    label = start.strftime("%G-W%V")
    waiting = checklist_items(read(root / "state" / "waiting.md"), checked=False) or ["当前没有等待中事项。"]
    blocked = checklist_items(read(root / "state" / "blocked.md"), checked=False) or ["当前没有阻塞项。"]
    projects = project_summaries(root) or ["还没有记录项目进展。"]
    automation_count = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", read(root / "tasks" / "automation-candidates.md"), re.M))
    return f"""# 周复盘 - {label}

## 本周完成

{as_bullets(completed or ["还没有记录已完成事项。"])}

## 本周未完成

{as_bullets(unfinished or ["还没有记录未完成事项。"])}

## 等待中汇总

{as_bullets(waiting)}

## 阻塞项汇总

{as_bullets(blocked)}

## 项目进展

{as_bullets(projects)}

## 自动化收益

- 当前自动化候选数: {automation_count}

## 下周建议

- 关闭或重新约定最早的等待中事项。
- 选择一个阻塞项，并定义清晰的解阻动作。
- 推进一个项目，产出一个可见成果。
"""


def project_review(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    now = parse_date(args.date)
    rows = []
    for path in sorted((root / "projects").glob("*.md")):
        text = read(path)
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        last_raw = extract_section_any(text, ["最后更新", "Last Updated"]).strip().splitlines()
        last_date = parse_date(last_raw[0]) if last_raw else None
        next_actions = checklist_items(extract_section_any(text, ["下一步行动", "Next Actions"]), checked=False)
        waiting = extract_section_any(text, ["等待中", "Waiting"]).lower()
        blocked = extract_section_any(text, ["阻塞项", "Blocked"]).lower()
        risks = []
        if last_date and (now - last_date).days > 14:
            risks.append("停滞")
        if not next_actions:
            risks.append("缺少下一步")
        if ("none" not in blocked and "无" not in blocked) or "blocked" in text.lower() or "risk" in text.lower() or "风险" in text:
            risks.append("有风险")
        if "none" not in waiting and "无" not in waiting and waiting.strip():
            risks.append("等待中")
        suggestion = "定义一个下一步行动，并更新最后更新时间。" if risks else "状态健康，保持推进。"
        rows.append((title, ", ".join(sorted(set(risks))) or "健康", suggestion))
    print("# 项目巡检")
    for title, status, suggestion in rows:
        print(f"- {title}: {status}. {suggestion}")


def print_git_status(root: Path) -> None:
    status = run(["git", "status", "--short"], cwd=root, check=False).stdout.strip()
    print("git status --short:")
    print(status or "(clean)")


def print_diff(root: Path) -> None:
    print("\n--- git status --short ---")
    print(run(["git", "status", "--short"], cwd=root, check=False).stdout.rstrip() or "(clean)")
    print("\n--- git diff --stat ---")
    print(run(["git", "diff", "--stat"], cwd=root, check=False).stdout.rstrip() or "(no diff)")
    print("\n--- git diff ---")
    print(run(["git", "diff"], cwd=root, check=False).stdout.rstrip() or "(no diff)")
    print("\n建议提交:")
    print("git add . && git commit -m \"Update PersonalOS\"")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate a Git-backed PersonalOS repository.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("bootstrap", help="Create a new PersonalOS repository.")
    p.add_argument("repo")
    p.add_argument("--date")
    p.set_defaults(func=bootstrap)

    p = sub.add_parser("daily", help="Generate a Daily file.")
    p.add_argument("repo")
    p.add_argument("--date")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=daily)

    p = sub.add_parser("add-task", help="Add and route a task using Intent First.")
    p.add_argument("repo")
    p.add_argument("task")
    p.add_argument("--type")
    p.add_argument("--date")
    p.set_defaults(func=add_task)

    p = sub.add_parser("complete-task", help="Complete a matching task.")
    p.add_argument("repo")
    p.add_argument("task")
    p.add_argument("--date")
    p.set_defaults(func=complete_task)

    p = sub.add_parser("weekly-review", help="Generate a weekly review.")
    p.add_argument("repo")
    p.add_argument("--week-start")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=weekly_review)

    p = sub.add_parser("project-review", help="Review projects for stale, stalled, or risky state.")
    p.add_argument("repo")
    p.add_argument("--date")
    p.set_defaults(func=project_review)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
