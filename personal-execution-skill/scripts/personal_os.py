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
    write_new(root / "inbox.md", "# Inbox\n\n- [ ] Triage this PersonalOS demo input.\n")
    write_new(root / "tasks" / "today.md", "# Today Tasks\n\n- [ ] Review PersonalOS structure\n")
    write_new(root / "tasks" / "scheduled.md", "# Scheduled Tasks\n\n- [ ] Weekly review every Friday\n")
    write_new(root / "tasks" / "archive.md", "# Archive\n\n- No archived records yet.\n")
    write_new(root / "state" / "waiting.md", "# Waiting\n\n- [ ] Alice to confirm Q3 budget owner | Owner: Alice | Since: " + date + "\n")
    write_new(root / "state" / "blocked.md", "# Blocked\n\n- [ ] Demo analytics dashboard blocked by missing API token | Since: " + date + " | Unblock: obtain token\n")
    write_new(root / "state" / "habits.md", "# Habits\n\n" + render_template("habit.md", habit_name="Daily DP practice"))
    write_new(root / "state" / "stats.md", "# Stats\n\n- Tasks completed: 0\n- Automation candidates created: 1\n")
    write_new(root / "logs" / "execution-log.md", "# Execution Log\n\n- " + date + " Bootstrap PersonalOS repository.\n")
    write_new(root / "projects" / "demo-project.md", render_template("project.md", project_name="Demo Project", date=date))
    write_new(root / "tasks" / "automation-candidates.md", "# Automation Candidates\n\n" + render_template(
        "automation-candidate.md",
        date=date,
        title="Generate Weekly Metrics Report",
        source_task="Generate a weekly metrics summary from a CSV export.",
        codex_prompt="Inspect the CSV export, compute week-over-week metrics, create a Markdown summary, and include validation notes.",
    ))
    write_new(root / "dailies" / f"{date}.md", render_daily(root, parse_date(args.date)))
    write_new(root / "weekly-reviews" / f"{week_label}.md", render_weekly(root, iso_week_start(args.date)))

    if not (root / ".git").exists():
        run(["git", "init"], cwd=root)
    run(["git", "add", "."], cwd=root)
    if run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode != 0:
        run(["git", "commit", "-m", "Bootstrap PersonalOS"], cwd=root)
    print(f"Bootstrapped PersonalOS at {root}")
    print_git_status(root)


def repo_readme(name: str) -> str:
    return f"""# {name}

This repository is a PersonalOS: a Git-backed Personal Chief of Staff system for daily execution, long-term projects, Waiting and Blocked tracking, automation candidates, weekly reviews, execution logs, and future habit management.

## Operating Loop

1. Capture raw input in `inbox.md`.
2. Generate or update today's Daily in `dailies/`.
3. Route work into Today, Projects, Waiting, Blocked, Scheduled, Automation Candidates, Archive, or Habits.
4. Mark completed work in place and log it in `logs/execution-log.md`.
5. Review projects weekly and commit accepted changes.

## Core Folders

- `dailies/`: daily plans and reviews.
- `weekly-reviews/`: weekly summaries.
- `projects/`: long-term project state.
- `tasks/`: today, scheduled, automation, and archive ledgers.
- `state/`: waiting, blocked, habits, and stats.
- `logs/`: execution history.
- `templates/`: canonical Markdown templates.
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
        append(root / "tasks" / "scheduled.md", f"- [ ] {args.task} | Added: {date.isoformat()}")
    elif task_type == "automation":
        add_automation_candidate(root, args.task, date)
    elif task_type == "waiting":
        append(root / "state" / "waiting.md", f"- [ ] {args.task} | Since: {date.isoformat()}")
    elif task_type == "blocked":
        append(root / "state" / "blocked.md", f"- [ ] {args.task} | Since: {date.isoformat()}")
    elif task_type == "archive":
        append(root / "tasks" / "archive.md", f"- {date.isoformat()} {args.task}")
    elif task_type == "habit":
        append(root / "state" / "habits.md", "\n" + render_template("habit.md", habit_name=args.task))
    print(f"Added task as {task_type}: {args.task}")
    print_diff(root)


def add_today_task(root: Path, task: str, date: dt.date) -> None:
    append(root / "tasks" / "today.md", f"- [ ] {task} | Added: {date.isoformat()}")
    daily = root / "dailies" / f"{date.isoformat()}.md"
    if not daily.exists():
        daily.write_text(render_daily(root, date), encoding="utf-8")
    append_under_heading(daily, "Today New Tasks", f"- [ ] {task}")
    append_under_heading(daily, "Today Task List", f"- [ ] {task}")


def add_project_task(root: Path, task: str, date: dt.date) -> None:
    title = task.split(":", 1)[-1].strip() if ":" in task else task.strip()
    path = root / "projects" / f"{slugify(title)}.md"
    if not path.exists():
        path.write_text(render_template("project.md", project_name=title, date=date.isoformat()), encoding="utf-8")
    append_under_heading(path, "Next Actions", f"- [ ] {task}")
    replace_field(path, "Last Updated", date.isoformat())


def add_automation_candidate(root: Path, task: str, date: dt.date) -> None:
    title = task[:60].strip()
    content = render_template(
        "automation-candidate.md",
        date=date.isoformat(),
        title=title,
        source_task=task,
        codex_prompt=f"Complete this task end-to-end: {task}. Inspect relevant files, make necessary changes, validate results, and summarize outputs.",
    )
    append(root / "tasks" / "automation-candidates.md", "\n" + content)
    increment_stat(root / "state" / "stats.md", "Automation candidates created")


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
        print(f"Daily already exists: {path}")
    else:
        path.write_text(render_daily(root, day), encoding="utf-8")
        print(f"Generated Daily: {path}")
    print_diff(root)


def render_daily(root: Path, day: dt.date) -> str:
    yesterday_path = root / "dailies" / f"{(day - dt.timedelta(days=1)).isoformat()}.md"
    yesterday = read(yesterday_path)
    done = checklist_items(yesterday, checked=True) or ["No completed items recorded yet."]
    undone = checklist_items(yesterday, checked=False) or checklist_items(read(root / "tasks" / "today.md"), checked=False) or ["No unfinished items carried over yet."]
    waiting = checklist_items(read(root / "state" / "waiting.md"), checked=False) or bullet_lines(read(root / "state" / "waiting.md")) or ["No active waiting items."]
    blocked = checklist_items(read(root / "state" / "blocked.md"), checked=False) or bullet_lines(read(root / "state" / "blocked.md")) or ["No active blocked items."]
    projects = project_summaries(root)
    automations = checklist_items(read(root / "tasks" / "automation-candidates.md"), checked=False)
    suggestions = ["Select one important project next action.", "Clear or route new Inbox items."]
    if blocked and blocked[0] != "No active blocked items.":
        suggestions.insert(0, "Unblock the highest-impact blocked item.")
    if waiting and waiting[0] != "No active waiting items.":
        suggestions.append("Send one concise follow-up for the oldest Waiting item.")
    if automations:
        suggestions.append("Run or refine one Codex automation candidate.")
    return f"""# Daily - {day.isoformat()}

## Yesterday Done

{as_bullets(done)}

## Yesterday Unfinished

{as_bullets(undone)}

## Waiting

{as_bullets(waiting)}

## Blocked

{as_bullets(blocked)}

## Long-Term Project Progress

{as_bullets(projects or ["No project progress recorded yet."])}

## Today Suggestions

{as_bullets(suggestions)}

## Today Task List

{as_checklist([item for item in undone if not item.startswith("No unfinished")]) or "- [ ] Review Inbox"}

## Today New Tasks

- None yet.

## Today Review

- Wins:
- Friction:
- Carry forward:
"""


def as_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def as_checklist(items: list[str]) -> str:
    return "\n".join(f"- [ ] {item}" for item in items)


def project_summaries(root: Path) -> list[str]:
    summaries = []
    for path in sorted((root / "projects").glob("*.md")):
        text = read(path)
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        phase = extract_section(text, "Current Phase").strip().splitlines()[0] if extract_section(text, "Current Phase").strip() else "Unknown phase"
        progress = extract_section(text, "Progress").strip().splitlines()[0] if extract_section(text, "Progress").strip() else "Unknown progress"
        summaries.append(f"{title}: {phase}, {progress}")
    return summaries


def extract_section(text: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n\n(.*?)(?=\n## |\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


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
    append(root / "logs" / "execution-log.md", f"- {day.isoformat()} Completed: {args.task}")
    increment_stat(root / "state" / "stats.md", "Tasks completed")
    print("Completed task match in:")
    for path in changed:
        print(f"- {path}")
    if not changed:
        print("- No checkbox match found; logged completion only.")
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
        print(f"Weekly review already exists: {path}")
    else:
        path.write_text(content, encoding="utf-8")
        print(f"Generated Weekly Review {label}: {start} to {end}")
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
    waiting = checklist_items(read(root / "state" / "waiting.md"), checked=False) or ["No active waiting items."]
    blocked = checklist_items(read(root / "state" / "blocked.md"), checked=False) or ["No active blocked items."]
    projects = project_summaries(root) or ["No project progress recorded yet."]
    automation_count = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", read(root / "tasks" / "automation-candidates.md"), re.M))
    return f"""# Weekly Review - {label}

## This Week Completed

{as_bullets(completed or ["No completed items recorded yet."])}

## This Week Unfinished

{as_bullets(unfinished or ["No unfinished items recorded yet."])}

## Waiting Summary

{as_bullets(waiting)}

## Blocked Summary

{as_bullets(blocked)}

## Project Progress

{as_bullets(projects)}

## Automation Benefit

- Automation candidates in backlog: {automation_count}

## Next Week Suggestions

- Close or re-negotiate the oldest Waiting item.
- Pick one blocked item and define an unblock action.
- Move one project forward with a visible artifact.
"""


def project_review(args: argparse.Namespace) -> None:
    root = Path(args.repo).resolve()
    ensure_repo(root)
    now = parse_date(args.date)
    rows = []
    for path in sorted((root / "projects").glob("*.md")):
        text = read(path)
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        last_raw = extract_section(text, "Last Updated").strip().splitlines()
        last_date = parse_date(last_raw[0]) if last_raw else None
        next_actions = checklist_items(extract_section(text, "Next Actions"), checked=False)
        waiting = extract_section(text, "Waiting").lower()
        blocked = extract_section(text, "Blocked").lower()
        risks = []
        if last_date and (now - last_date).days > 14:
            risks.append("stale")
        if not next_actions:
            risks.append("stalled")
        if "none" not in blocked or "blocked" in text.lower() or "risk" in text.lower():
            risks.append("risk")
        if "none" not in waiting and waiting.strip():
            risks.append("waiting")
        suggestion = "Define one next action and update Last Updated." if risks else "Healthy; keep momentum."
        rows.append((title, ", ".join(sorted(set(risks))) or "healthy", suggestion))
    print("# Project Review")
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
    print("\nSuggested commit:")
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
