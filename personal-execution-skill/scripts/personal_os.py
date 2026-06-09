#!/usr/bin/env python3
"""PersonalOS helper for personal-execution-skill."""

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from typing import Union


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "templates"
CONFIG_PATH = Path(os.environ.get("PERSONAL_OS_CONFIG", SKILL_DIR / "state" / "config.json"))


@dataclass(frozen=True)
class RemoveCandidate:
    id: int
    path: Path
    kind: str
    text: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class ProjectPlanItem:
    title: str
    due_date: dt.date
    action: str
    acceptance: str

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
    "截止日期任务": "scheduled",
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
    "周期任务": "habit",
    "惯例": "habit",
}


def today() -> dt.date:
    return dt.date.today()


def parse_date(value: Optional[str]) -> dt.date:
    if not value:
        return today()
    return dt.date.fromisoformat(value)


def iso_week_start(value: Optional[str]) -> dt.date:
    if value:
        day = dt.date.fromisoformat(value)
    else:
        day = today()
    return day - dt.timedelta(days=day.weekday())


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower()).strip("-")
    return slug[:80] or "untitled"


def run(cmd: list[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def read_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(read(CONFIG_PATH))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"PersonalOS config is not valid JSON: {CONFIG_PATH}\n{exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"PersonalOS config must be a JSON object: {CONFIG_PATH}")
    return {str(key): str(value) for key, value in data.items()}


def write_config(data: dict[str, str]) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def set_default_repo(root: Path) -> None:
    config = read_config()
    config["default_repo"] = str(root.resolve())
    config["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")
    write_config(config)


def resolve_repo(repo: Optional[str]) -> Path:
    if repo:
        root = Path(repo).expanduser().resolve()
    else:
        config = read_config()
        default_repo = config.get("default_repo")
        if not default_repo:
            raise SystemExit(
                "PersonalOS repository path was not provided and no default is configured.\n"
                "Run bootstrap first, or pass the repository path explicitly."
            )
        root = Path(default_repo).expanduser().resolve()
        print(f"使用默认 PersonalOS 仓库: {root}")
    ensure_repo(root)
    return root


def task_args(args: argparse.Namespace) -> tuple[Path, str]:
    if args.task is None:
        return resolve_repo(None), args.repo_or_task
    return resolve_repo(args.repo_or_task), args.task


def ensure_repo(root: Path) -> None:
    if not root.exists():
        raise SystemExit(f"Repository does not exist: {root}")
    for dirname in ["dailies", "tasks", "state", "projects"]:
        if not (root / dirname).exists():
            raise SystemExit(f"Not a PersonalOS repository, missing {dirname}: {root}")


def today_path(root: Path) -> Path:
    return root / "tasks" / "today.md"


def schedule_path(root: Path) -> Path:
    return root / "state" / "schedule.md"


def automation_path(root: Path) -> Path:
    return root / "state" / "automation-candidates.md"


def archive_path(root: Path) -> Path:
    return root / "state" / "archive.md"


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


def checklist_items(text: str, checked: Optional[bool] = None) -> list[str]:
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


def habit_items(root: Path, day: dt.date) -> list[tuple[str, bool]]:
    text = read(root / "state" / "habits.md")
    habits: list[tuple[str, bool]] = []
    for match in re.finditer(r"^##\s+(.+?)\n(.*?)(?=^##\s+|\Z)", text, re.M | re.S):
        title = match.group(1).strip()
        body = match.group(2)
        auto_match = re.search(r"^-\s*自动加入日报:\s*(.+?)\s*$", body, re.M)
        if not auto_match:
            continue
        auto_value = auto_match.group(1).strip().lower()
        if auto_value not in {"是", "true", "yes", "y", "1"}:
            continue
        habit_match = re.search(r"^-\s*Habit:\s*(.+?)\s*$", body, re.M)
        name = habit_match.group(1).strip() if habit_match else title
        completion_text = extract_completion_text(body)
        completed = day.isoformat() in re.findall(r"\d{4}-\d{2}-\d{2}", completion_text)
        habits.append((name, completed))
    return habits


def extract_completion_text(text: str) -> str:
    parts: list[str] = []
    inline_match = re.search(r"^-\s*完成记录:\s*(.*?)$", text, re.M)
    if inline_match:
        parts.append(inline_match.group(1))
    section_match = re.search(r"^###\s+完成记录\s*\n(.*?)(?=^###\s+|\Z)", text, re.M | re.S)
    if section_match:
        parts.append(section_match.group(1))
    return "\n".join(parts)


def habit_blocks(text: str) -> list[tuple[re.Match[str], str, str]]:
    blocks = []
    for match in re.finditer(r"^##\s+(.+?)\n(.*?)(?=^##\s+|\Z)", text, re.M | re.S):
        title = match.group(1).strip()
        body = match.group(2)
        habit_match = re.search(r"^-\s*Habit:\s*(.+?)\s*$", body, re.M)
        name = habit_match.group(1).strip() if habit_match else title
        blocks.append((match, title, name))
    return blocks


def matches_task_name(candidate: str, task: str) -> bool:
    left = normalize_match_text(candidate)
    right = normalize_match_text(task)
    return bool(left and right and (left in right or right in left))


def normalize_match_text(value: str) -> str:
    value = re.sub(r"\|.*$", "", value)
    value = re.sub(r"\s+", " ", value.strip().lower())
    return value


def strip_task_metadata(value: str) -> str:
    value = re.sub(r"\s*\|\s*.*$", "", value).strip()
    value = re.sub(r"^\s*-\s+\[[ xX]\]\s+", "", value).strip()
    value = re.sub(r"^\s*-\s+", "", value).strip()
    return value


def extract_learning(text: str, explicit_learning: Optional[str] = None) -> str:
    if explicit_learning:
        return explicit_learning.strip()
    patterns = [
        r"(?:收获(?:为|是|到|到了)|学到(?:了)?|学会(?:了)?|learned)\s*[：:，,]?\s*(.+)",
        r"(?:这次任务中|今天|本次)\s*(?:我)?(?:学到了|收获到了|收获了)\s*(.+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            value = match.group(1).strip()
            value = re.split(r"(?:，|。|\n)\s*(?:卡点|结转|下次|目前进度|当前进度)", value, maxsplit=1)[0].strip()
            return value.rstrip("。；;")
    return ""


def strip_learning_clause(text: str) -> str:
    markers = [
        "这次任务中我学到了",
        "这次任务中学到了",
        "今天我学到了",
        "今天学到了",
        "收获到了",
        "收获为",
        "收获是",
        "收获:",
        "收获：",
        "学到了",
        "learned",
    ]
    lowered = text.lower()
    indexes = [lowered.find(marker.lower()) for marker in markers if lowered.find(marker.lower()) >= 0]
    if not indexes:
        return text.strip()
    cut = min(indexes)
    return re.sub(r"[，,；;。:\s]+$", "", text[:cut]).strip()


def extract_progress(text: str, explicit_progress: Optional[str] = None) -> str:
    if explicit_progress:
        return explicit_progress.strip()
    match = re.search(r"(?:当前进度|进度|progress)\s*[：:为是]?\s*([0-9]{1,3}%|[0-9]{1,3}\s*percent)", text, re.I)
    return match.group(1).replace(" ", "") if match else ""


def extract_milestone(text: str, explicit_milestone: Optional[str] = None) -> str:
    if explicit_milestone:
        return explicit_milestone.strip()
    match = re.search(r"(?:目前已完成|已完成|当前完成|milestone)\s*[：:为是]?\s*(.+)", text, re.I)
    if not match:
        return ""
    value = match.group(1).strip()
    value = re.split(r"(?:，|。|\n)\s*(?:收获|学到|当前进度|进度|卡点|阻塞)", value, maxsplit=1)[0].strip()
    return value.rstrip("。；;")


def append_unique_line(path: Path, line: str) -> None:
    text = read(path)
    if line.strip() in {existing.strip() for existing in text.splitlines()}:
        return
    append(path, line)


def schedule_entry(task: str, due_date: dt.date, suffix: str = "") -> str:
    extra = suffix if not suffix or suffix.startswith(" | ") else f" | {suffix}"
    return f"- {task} | 状态: open | 截止: {due_date.isoformat()} | 完成: {extra}"


def ensure_daily(root: Path, day: dt.date) -> Path:
    path = root / "dailies" / f"{day.isoformat()}.md"
    if not path.exists():
        path.write_text(render_daily(root, day), encoding="utf-8")
    return path


def append_daily_learning(root: Path, day: dt.date, learning: str, source: str) -> None:
    learning = learning.strip()
    if not learning:
        return
    path = ensure_daily(root, day)
    line = f"  - [{source}] {learning}"
    text = read(path)
    if line.strip() in {existing.strip() for existing in text.splitlines()}:
        return
    pattern = re.compile(r"(^-\s*收获:\s*$)", re.M)
    if pattern.search(text):
        text = pattern.sub(rf"\1\n{line}", text, count=1)
        path.write_text(text, encoding="utf-8")
    else:
        append_under_heading(path, "今日复盘", f"- 收获:\n{line}")


def first_date_in_text(text: str) -> Optional[dt.date]:
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(0))
    except ValueError:
        return None


def task_due_date(text: str) -> Optional[dt.date]:
    return first_date_in_text(text)


def project_ref_from_line(line: str) -> str:
    match = re.search(r"\|\s*项目:\s*([^|]+)", line)
    return match.group(1).strip() if match else ""


def task_id_from_line(line: str) -> str:
    match = re.search(r"\|\s*子任务:\s*([^|]+)", line)
    return match.group(1).strip() if match else ""


def completion_dates(text: str) -> list[dt.date]:
    dates = []
    for raw in re.findall(r"\d{4}-\d{2}-\d{2}", extract_completion_text(text)):
        try:
            dates.append(dt.date.fromisoformat(raw))
        except ValueError:
            continue
    return sorted(set(dates))


def habit_period(frequency: str) -> str:
    lowered = frequency.lower()
    if re.search(r"weekly|每周|周", lowered):
        return "weekly"
    if re.search(r"monthly|每月|月", lowered):
        return "monthly"
    return "daily"


def habit_frequency(body: str) -> str:
    match = re.search(r"^-\s*频率:\s*(.*?)\s*$", body, re.M)
    return match.group(1).strip() if match else ""


def habit_streak(dates: list[dt.date], frequency: str) -> int:
    if not dates:
        return 0
    period = habit_period(frequency)
    if period == "daily":
        streak = 1
        current = dates[-1]
        for previous in reversed(dates[:-1]):
            if previous == current - dt.timedelta(days=1):
                streak += 1
                current = previous
            else:
                break
        return streak
    if period == "weekly":
        weeks = sorted({(day.isocalendar().year, day.isocalendar().week) for day in dates})
        streak = 1
        current_year, current_week = weeks[-1]
        current_monday = dt.date.fromisocalendar(current_year, current_week, 1)
        for year, week in reversed(weeks[:-1]):
            monday = dt.date.fromisocalendar(year, week, 1)
            if monday == current_monday - dt.timedelta(days=7):
                streak += 1
                current_monday = monday
            else:
                break
        return streak
    months = sorted({(day.year, day.month) for day in dates})
    streak = 1
    current_year, current_month = months[-1]
    for year, month in reversed(months[:-1]):
        previous_month = current_month - 1
        previous_year = current_year
        if previous_month == 0:
            previous_month = 12
            previous_year -= 1
        if (year, month) == (previous_year, previous_month):
            streak += 1
            current_year, current_month = year, month
        else:
            break
    return streak


def habit_completion_rate(dates: list[dt.date], frequency: str) -> str:
    if not dates:
        return "0%"
    period = habit_period(frequency)
    first = dates[0]
    last = dates[-1]
    if period == "weekly":
        first_monday = dt.date.fromisocalendar(first.isocalendar().year, first.isocalendar().week, 1)
        last_monday = dt.date.fromisocalendar(last.isocalendar().year, last.isocalendar().week, 1)
        total = ((last_monday - first_monday).days // 7) + 1
        done = len({(day.isocalendar().year, day.isocalendar().week) for day in dates})
    elif period == "monthly":
        total = (last.year - first.year) * 12 + last.month - first.month + 1
        done = len({(day.year, day.month) for day in dates})
    else:
        total = (last - first).days + 1
        done = len(dates)
    return f"{round(done / max(total, 1) * 100)}%"


def replace_bullet_field(text: str, label: str, value: str, before_heading: Optional[str] = None) -> str:
    pattern = re.compile(rf"^-\s*{re.escape(label)}:\s*.*$", re.M)
    line = f"- {label}: {value}"
    if pattern.search(text):
        return pattern.sub(line, text, count=1)
    if before_heading:
        heading_pattern = re.compile(rf"^###\s+{re.escape(before_heading)}\s*$", re.M)
        match = heading_pattern.search(text)
        if match:
            prefix = text[:match.start()].rstrip()
            suffix = text[match.start():]
            return prefix + "\n" + line + "\n\n" + suffix
    return text.rstrip() + "\n" + line + "\n"


def append_habit_completion(body: str, day: dt.date) -> tuple[str, bool]:
    dates = completion_dates(body)
    if day in dates:
        return body, False
    line = f"- {day.isoformat()} 已完成"
    section_pattern = re.compile(r"(^###\s+完成记录\s*\n)(.*?)(?=^###\s+|\Z)", re.M | re.S)
    match = section_pattern.search(body)
    if match:
        records = match.group(2).strip()
        if "还没有记录完成情况" in records and len(re.findall(r"\d{4}-\d{2}-\d{2}", records)) == 0:
            records = ""
        records = (records.rstrip() + "\n" + line).strip()
        body = body[:match.start()] + match.group(1) + records + "\n" + body[match.end():]
    else:
        body = body.rstrip() + "\n\n### 完成记录\n\n" + line + "\n"
    return body, True


def refresh_habit_metrics(body: str) -> str:
    frequency = habit_frequency(body)
    dates = completion_dates(body)
    body = replace_bullet_field(body, "当前连续天数", str(habit_streak(dates, frequency)), "完成记录")
    body = replace_bullet_field(body, "完成率", habit_completion_rate(dates, frequency), "完成记录")
    return body


def complete_habit(root: Path, task: str, day: dt.date) -> tuple[Optional[Path], bool, bool]:
    path = root / "state" / "habits.md"
    text = read(path)
    if not text:
        return None, False, False
    for match, title, name in habit_blocks(text):
        if not (matches_task_name(title, task) or matches_task_name(name, task)):
            continue
        body, added = append_habit_completion(match.group(2), day)
        body = refresh_habit_metrics(body)
        new_block = f"## {title}\n{body.rstrip()}\n"
        path.write_text(text[:match.start()] + new_block + text[match.end():], encoding="utf-8")
        refresh_habit_stats(root)
        return path, True, added
    return None, False, False


def refresh_habit_stats(root: Path) -> None:
    habits_text = read(root / "state" / "habits.md")
    blocks = habit_blocks(habits_text)
    auto_count = 0
    completion_count = 0
    latest: Optional[dt.date] = None
    for match, _title, _name in blocks:
        body = match.group(2)
        auto_match = re.search(r"^-\s*自动加入日报:\s*(.+?)\s*$", body, re.M)
        if auto_match and auto_match.group(1).strip().lower() in {"是", "true", "yes", "y", "1"}:
            auto_count += 1
        dates = completion_dates(body)
        completion_count += len(dates)
        if dates:
            latest = max(latest, dates[-1]) if latest else dates[-1]
    stats_path = root / "state" / "stats.md"
    set_stat(stats_path, "Habit 总数", len(blocks))
    set_stat(stats_path, "自动加入日报 Habit 数", auto_count)
    set_stat(stats_path, "Habit 完成次数", completion_count)
    set_stat(stats_path, "Habit 最近完成日期", latest.isoformat() if latest else "无")


def copy_templates(root: Path) -> None:
    for template in TEMPLATE_DIR.glob("*.md"):
        write_new(root / "templates" / template.name, read(template))


def keep_empty_dirs(root: Path) -> None:
    for dirname in ["dailies", "weekly-reviews", "projects"]:
        write_new(root / dirname / ".gitkeep", "")


def bootstrap(args: argparse.Namespace) -> None:
    root = Path(args.repo).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for dirname in DIRS:
        (root / dirname).mkdir(parents=True, exist_ok=True)
    copy_templates(root)
    keep_empty_dirs(root)

    date = parse_date(args.date).isoformat()
    write_new(root / "README.md", repo_readme(root.name))
    write_new(root / "inbox.md", "# 收件箱\n")
    write_new(today_path(root), "# 今日任务\n")
    write_new(schedule_path(root), "# 定时任务\n")
    write_new(archive_path(root), "# 归档\n")
    write_new(automation_path(root), "# Automation Candidates\n")
    write_new(root / "state" / "waiting.md", "# 等待中\n")
    write_new(root / "state" / "blocked.md", "# 阻塞项\n")
    write_new(root / "state" / "habits.md", "# 习惯\n")
    write_new(root / "state" / "stats.md", "# 统计\n\n- 已完成任务数: 0\n- 已创建自动化候选数: 0\n")
    write_new(root / "logs" / "execution-log.md", "# 执行日志\n\n- " + date + " 初始化 PersonalOS 仓库。\n")

    if not (root / ".git").exists():
        run(["git", "init"], cwd=root)
    run(["git", "add", "."], cwd=root)
    if run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode != 0:
        run(["git", "commit", "-m", "Bootstrap PersonalOS"], cwd=root)
    set_default_repo(root)
    print(f"已初始化 PersonalOS: {root}")
    print(f"已记录默认 PersonalOS 仓库: {root}")
    print(f"配置文件: {CONFIG_PATH}")
    print_git_status(root)


def set_repo(args: argparse.Namespace) -> None:
    root = Path(args.repo).expanduser().resolve()
    ensure_repo(root)
    set_default_repo(root)
    print(f"已记录默认 PersonalOS 仓库: {root}")
    print(f"配置文件: {CONFIG_PATH}")


def repo_readme(name: str) -> str:
    return f"""# {name}

这个仓库是一个 PersonalOS：用 Git 管理的个人执行系统，用于每日推进、长期项目、等待中/阻塞项、自动化候选、周复盘、执行日志和习惯维护。

## 运转循环

1. 把原始输入收进 `inbox.md`。
2. 在 `dailies/` 生成或更新当天日报。
3. 把事项路由到今日执行清单、项目、等待中、阻塞项、日程、自动化候选、归档或习惯。
4. 在原位置标记完成，并记录到 `logs/execution-log.md`。
5. 每周巡检项目，并提交确认后的变更。

## 核心目录

- `dailies/`: 每日计划与复盘。
- `weekly-reviews/`: 周复盘。
- `projects/`: 长期项目状态。
- `tasks/`: 今日执行清单与完成面。
- `state/`: 日程、自动化候选、归档、等待中、阻塞项、习惯和统计。
- `logs/`: 执行历史。
- `templates/`: 标准 Markdown 模板。
"""


def classify_task(text: str, explicit_type: Optional[str] = None) -> str:
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
    if re.search(r"\b(habit|routine|daily|weekly|monthly|every)\b|每天|每周|每月|每日|每个月|习惯|定式|惯例|周期", lowered):
        return "habit"
    if re.search(r"\b(due|deadline|by|tomorrow|next week|schedule|remind|reminder)\b|\d{4}-\d{2}-\d{2}|截止|到期|提醒|定时|日期|明天|下周", lowered):
        return "scheduled"
    if re.search(r"\b(project|milestone|launch|build|research|strategy|roadmap)\b|项目|长期|里程碑|上线|调研|战略", lowered):
        return "project"
    if re.search(r"\b(archive|record|done|completed)\b|归档|记录", lowered):
        return "archive"
    return "today"


def add_task(args: argparse.Namespace) -> None:
    root, task = task_args(args)
    date = parse_date(args.date)
    task_type = classify_task(task, args.type)
    if task_type == "today":
        add_today_task(root, task, date)
    elif task_type == "project":
        add_project_task(root, task, date)
        print_project_plan(task, build_project_plan(task, date, None))
        print("\n项目子任务清单尚未写入。确认无误后运行:")
        print(f"python3 {Path(__file__).resolve()} plan-project {quote_arg(task)} --date {date.isoformat()} --confirm")
    elif task_type == "scheduled":
        append(schedule_path(root), schedule_entry(task, date))
    elif task_type == "automation":
        add_automation_candidate(root, task, date)
    elif task_type == "waiting":
        append(root / "state" / "waiting.md", f"- [ ] {task} | 开始: {date.isoformat()}")
    elif task_type == "blocked":
        append(root / "state" / "blocked.md", f"- [ ] {task} | 开始: {date.isoformat()}")
    elif task_type == "archive":
        append(archive_path(root), f"- {date.isoformat()} {task}")
    elif task_type == "habit":
        append(root / "state" / "habits.md", "\n" + render_template("habit.md", habit_name=task))
        refresh_habit_stats(root)
    print(f"已添加任务，类型为 {task_type}: {task}")
    print_diff(root)


def add_today_task(root: Path, task: str, date: dt.date) -> None:
    append(today_path(root), f"- [ ] {task} | 添加: {date.isoformat()}")
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


def find_project_path(root: Path, project: str) -> Path:
    wanted_slug = slugify(project)
    direct = root / "projects" / f"{wanted_slug}.md"
    if direct.exists():
        return direct
    for path in sorted((root / "projects").glob("*.md")):
        text = read(path)
        title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
        if matches_task_name(title, project) or matches_task_name(path.stem, wanted_slug):
            return path
    return direct


def ensure_project(root: Path, project: str, date: dt.date) -> Path:
    path = find_project_path(root, project)
    if not path.exists():
        path.write_text(render_template("project.md", project_name=project.strip(), date=date.isoformat()), encoding="utf-8")
    return path


def update_project(args: argparse.Namespace) -> None:
    root = resolve_repo(args.repo)
    day = parse_date(args.date)
    update_text = args.update or ""
    path = ensure_project(root, args.project, day)
    progress = extract_progress(update_text, args.progress)
    milestone = extract_milestone(update_text, args.milestone)
    learning = extract_learning(update_text, args.learning)
    if progress:
        replace_field(path, "进展", progress)
    if milestone:
        remove_section_placeholders(path, "里程碑")
        append_under_heading(path, "里程碑", f"- {day.isoformat()} {milestone}")
        append_under_heading(path, "复盘笔记", f"- {day.isoformat()} 当前进展: {milestone}")
    if learning:
        append_under_heading(path, "复盘笔记", f"- {day.isoformat()} 收获: {learning}")
        append_daily_learning(root, day, learning, f"项目: {project_title(path)}")
    replace_field(path, "最后更新", day.isoformat())
    print(f"已更新项目: {path}")
    print_diff(root)


def project_title(path: Path) -> str:
    text = read(path)
    return text.splitlines()[0].lstrip("# ").strip() if text else path.stem


def plan_project(args: argparse.Namespace) -> None:
    root = resolve_repo(args.repo)
    start = parse_date(args.date)
    project = args.project.strip()
    items = build_project_plan(project, start, args.deadline)
    print_project_plan(project, items)
    if not args.confirm:
        print("\n尚未写入 PersonalOS。确认无误后运行:")
        print(
            f"python3 {Path(__file__).resolve()} plan-project {quote_arg(project)} "
            f"--date {start.isoformat()} --confirm"
        )
        return
    path = ensure_project(root, project, start)
    ensure_project_plan_section(path)
    remove_section_placeholders(path, "子任务清单")
    for index, item in enumerate(items, start=1):
        task_id = f"{slugify(project)}-{index}"
        checklist = (
            f"- [ ] {item.title} | 状态: open | 截止: {item.due_date.isoformat()} | "
            f"完成:  | 验收: {item.acceptance} | 子任务: {task_id}"
        )
        append_under_heading(path, "子任务清单", checklist)
        schedule_line = (
            f"- {item.title} | 状态: open | 截止: {item.due_date.isoformat()} | "
            f"完成:  | 项目: {project_title(path)} | 子任务: {task_id}"
        )
        append_unique_line(schedule_path(root), schedule_line)
    replace_field(path, "最后更新", start.isoformat())
    seed_next_actions_from_plan(path, items)
    seed_milestones_from_plan(path, items)
    print(f"已写入项目拆分并同步到 state/schedule.md: {path}")
    print_diff(root)


def build_project_plan(project: str, start: dt.date, deadline: Optional[str]) -> list[ProjectPlanItem]:
    end = parse_date(deadline) if deadline else start + dt.timedelta(days=28)
    if end <= start:
        end = start + dt.timedelta(days=28)
    return build_actionable_project_plan(project, start, end)


def build_actionable_project_plan(project: str, start: dt.date, end: dt.date) -> list[ProjectPlanItem]:
    lowered = project.lower()
    if any(keyword in project for keyword in ["阅读", "源码", "代码"]) or any(
        keyword in lowered for keyword in ["code", "cli", "sdk", "repo"]
    ):
        return build_code_reading_plan(project, start, end)
    if any(keyword in project for keyword in ["vpn", "代理"]) or "proxy" in lowered:
        return build_vpn_plan(project, start, end)
    return build_generic_actionable_plan(project, start, end)


def distribute_due_dates(start: dt.date, end: dt.date, steps: int, minimum_days: int = 1) -> list[dt.date]:
    if steps <= 0:
        return []
    span = max((end - start).days, steps * minimum_days)
    due_dates: list[dt.date] = []
    previous_offset = 0
    for index in range(steps):
        raw_offset = round(span * (index + 1) / steps)
        offset = max(previous_offset + minimum_days, raw_offset)
        previous_offset = offset
        due_dates.append(start + dt.timedelta(days=offset))
    return due_dates


def build_code_reading_plan(project: str, start: dt.date, end: dt.date) -> list[ProjectPlanItem]:
    due_dates = distribute_due_dates(start, end, 6)
    definitions = [
        (
            f"{project} - 明确阅读目标与范围",
            "写清这次阅读要回答的 2 个核心问题，并补一段不少于 5 行的范围说明，明确这轮先不看什么。",
            "形成一段可复用的目标说明，至少包含阅读目标、阅读范围和暂不覆盖内容。",
        ),
        (
            f"{project} - 找到程序入口与主调用链",
            "定位 CLI 启动入口、参数解析位置和命令注册位置，串出主调用链。",
            "整理出一条“启动入口 -> 命令分发 -> 执行模块”的文件路径链路。",
        ),
        (
            f"{project} - 梳理核心模块职责",
            "阅读核心目录，记录最重要的 5 到 8 个模块分别负责什么。",
            "形成一份模块职责清单，每个模块至少有一句用途说明。",
        ),
        (
            f"{project} - 深挖一个关键执行流程",
            "从“用户输入进入执行 / tool call 调度 / 线程状态组织”中选 1 个流程读透并写步骤说明。",
            "写出至少包含 5 个关键节点的流程说明，能讲清输入、分发、执行和结果回传。",
        ),
        (
            f"{project} - 做一次最小验证",
            "针对上一步的理解，实际跑一次相关命令、日志或调用链验证自己的判断。",
            "写下“原本理解 / 实际观察 / 修正后的理解”三段验证记录。",
        ),
        (
            f"{project} - 输出第一版阅读总结",
            "把零散笔记整理成一份可复用说明，沉淀目标、模块图、关键流程和未解问题。",
            "形成一篇阅读笔记 v1，至少包含目标、模块职责、关键流程、验证结果和未解问题五部分。",
        ),
    ]
    return [
        ProjectPlanItem(title, due_dates[index], action, acceptance)
        for index, (title, action, acceptance) in enumerate(definitions)
    ]


def build_vpn_plan(project: str, start: dt.date, end: dt.date) -> list[ProjectPlanItem]:
    due_dates = distribute_due_dates(start, end, 7)
    definitions = [
        (
            f"{project} - 明确目标、设备和约束",
            "写清代理主要给哪些设备使用、主要访问什么、优先级是什么，并补上预算边界。",
            "至少明确使用设备、目标用途、优先级和预算四项信息。",
        ),
        (
            f"{project} - 完成技术方案选型",
            "确定协议方案、服务器地区和客户端工具，并记录为什么选它。",
            "形成一份选型清单，并写出不选另外 1 到 2 个方案的原因。",
        ),
        (
            f"{project} - 准备服务器环境",
            "购买或确认 VPS，拿到 IP 和登录方式，并完成基础账户、密钥或端口安全设置。",
            "可以成功 SSH 登录，且已完成基础安全配置。",
        ),
        (
            f"{project} - 完成服务端部署",
            "安装代理服务并写好配置，确保服务端能正常启动。",
            "服务端进程可启动，配置文件已保存，重启后能恢复运行。",
        ),
        (
            f"{project} - 完成主力设备接入",
            "在至少 1 台常用设备上配置客户端并完成连接。",
            "至少 1 台主力设备能稳定连上，并能访问目标网站或服务。",
        ),
        (
            f"{project} - 做连通性与稳定性验证",
            "测试访问成功率、连接稳定性和基本速度表现，记录问题和修正项。",
            "连续使用半天到一天无明显断连，并记录至少 3 条验证结果。",
        ),
        (
            f"{project} - 沉淀维护文档",
            "记录续费信息、配置备份、重装步骤和常见故障处理。",
            "形成一份维护笔记，确保 1 周后重看也能独立复现部署。",
        ),
    ]
    return [
        ProjectPlanItem(title, due_dates[index], action, acceptance)
        for index, (title, action, acceptance) in enumerate(definitions)
    ]


def build_generic_actionable_plan(project: str, start: dt.date, end: dt.date) -> list[ProjectPlanItem]:
    due_dates = distribute_due_dates(start, end, 5)
    definitions = [
        (
            f"{project} - 明确目标与完成标准",
            "写清这个项目要解决什么问题、产出什么结果，以及这轮不做什么。",
            "形成一段目标说明，至少包含目标、范围和完成标准。",
        ),
        (
            f"{project} - 梳理现状与约束",
            "盘点现有资料、依赖、资源和已知约束，补齐缺口。",
            "形成一份现状清单，列出至少 3 个资源或约束点。",
        ),
        (
            f"{project} - 产出第一版最小可执行结果",
            "做出一个最小版本，不要停留在想法层面。",
            "产出一个可演示、可阅读或可运行的第一版结果。",
        ),
        (
            f"{project} - 验证风险与修正方案",
            "验证关键假设，记录风险、依赖和需要修正的地方。",
            "列出风险与修正项，并完成至少一轮验证。",
        ),
        (
            f"{project} - 整理交付物与复盘",
            "把过程材料和结论沉淀下来，便于后续继续推进。",
            "完成交付物整理，并写下复盘收获和下一步建议。",
        ),
    ]
    return [
        ProjectPlanItem(title, due_dates[index], action, acceptance)
        for index, (title, action, acceptance) in enumerate(definitions)
    ]


def print_project_plan(project: str, items: list[ProjectPlanItem]) -> None:
    print(f"# 项目拆分草案: {project}")
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item.title}")
        print(f"   - 截止时间: {item.due_date.isoformat()}")
        print(f"   - 动作: {item.action}")
        print(f"   - 验收标准: {item.acceptance}")


def seed_next_actions_from_plan(path: Path, items: list[ProjectPlanItem]) -> None:
    text = read(path)
    pattern = re.compile(r"(^## 下一步行动\n)(.*?)(?=^## |\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return
    body = match.group(2)
    if "定义下一个具体行动" not in body:
        return
    next_actions = "\n".join(f"- [ ] {item.title}" for item in items[:3]) + "\n\n"
    path.write_text(text[:match.start()] + match.group(1) + next_actions + text[match.end():], encoding="utf-8")


def seed_milestones_from_plan(path: Path, items: list[ProjectPlanItem]) -> None:
    text = read(path)
    pattern = re.compile(r"(^## 里程碑\n\n)(.*?)(?=\n## |\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return
    body = match.group(2).strip()
    if body not in {"- 暂无。", "- 暂无", "- 无。", "- 无"}:
        return
    milestone_lines = "\n".join(
        f"- {item.due_date.isoformat()} 前完成：{strip_task_metadata(item.title)}" for item in items[:3]
    )
    replacement = match.group(1) + milestone_lines + "\n"
    path.write_text(text[:match.start()] + replacement + text[match.end():], encoding="utf-8")


def ensure_project_plan_section(path: Path) -> None:
    text = read(path)
    if re.search(r"^## 子任务清单\s*$", text, re.M):
        return
    marker = re.search(r"^## 复盘笔记\s*$", text, re.M)
    if marker:
        text = text[:marker.start()] + "## 子任务清单\n\n" + text[marker.start():]
    else:
        text = text.rstrip() + "\n\n## 子任务清单\n"
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def remove_section_placeholders(path: Path, heading: str) -> None:
    text = read(path)
    pattern = re.compile(rf"(^## {re.escape(heading)}\n\n)(.*?)(?=\n## |\Z)", re.M | re.S)
    match = pattern.search(text)
    if not match:
        return
    lines = [
        line
        for line in match.group(2).splitlines()
        if line.strip() not in {"- 暂无。", "- 暂无", "- 无。", "- 无"}
    ]
    body = "\n".join(lines).strip()
    replacement = match.group(1) + (body + "\n\n" if body else "\n")
    path.write_text(text[:match.start()] + replacement + text[match.end():], encoding="utf-8")


def add_automation_candidate(root: Path, task: str, date: dt.date) -> None:
    title = task[:60].strip()
    content = render_template(
        "automation-candidate.md",
        date=date.isoformat(),
        title=title,
        source_task=task,
        codex_prompt=f"端到端完成这个任务：{task}。检查相关文件，做必要修改，验证结果，并总结产出。",
    )
    append(automation_path(root), "\n" + content)
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
        text = pattern.sub(lambda match: match.group(1) + value + "\n", text, count=1)
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


def set_stat(path: Path, label: str, value: Union[int, str]) -> None:
    text = read(path)
    pattern = re.compile(rf"(- {re.escape(label)}: ).*$", re.M)
    line_value = str(value)
    if pattern.search(text):
        text = pattern.sub(lambda m: m.group(1) + line_value, text, count=1)
    else:
        text = text.rstrip() + f"\n- {label}: {line_value}\n"
    path.write_text(text, encoding="utf-8")


def promote_scheduled_for_day(root: Path, day: dt.date) -> None:
    today_file = today_path(root)
    for line in read(schedule_path(root)).splitlines():
        if not is_open_schedule_line(line):
            continue
        due = task_due_date(line)
        if due != day:
            continue
        task = strip_task_metadata(line)
        append_unique_line(today_file, f"- [ ] {task} | 来源: scheduled | 日期: {day.isoformat()}")


def iter_schedule_lines(root: Path) -> list[str]:
    return read(schedule_path(root)).splitlines()


def iter_automation_text(root: Path) -> str:
    return read(automation_path(root))


def iter_archive_text(root: Path) -> str:
    return read(archive_path(root))


def daily(args: argparse.Namespace) -> None:
    root = resolve_repo(args.repo)
    day = parse_date(args.date)
    promote_scheduled_for_day(root, day)
    path = root / "dailies" / f"{day.isoformat()}.md"
    if path.exists() and not args.force:
        print(f"日报已存在: {path}")
    else:
        content = preserve_daily_review(render_daily(root, day), read(path))
        path.write_text(content, encoding="utf-8")
        print(f"已生成日报: {path}")
    print("\n--- 日报会话播报正文 ---")
    print(render_daily_announcement(path, root, day))
    print_diff(root)


def preserve_daily_review(new_content: str, old_content: str) -> str:
    old_review = extract_section(old_content, "今日复盘").strip()
    if not old_review:
        return new_content
    pattern = re.compile(r"(^## 今日复盘\n\n)(.*?)(?=\n## |\Z)", re.M | re.S)
    if not pattern.search(new_content):
        return new_content.rstrip() + f"\n\n## 今日复盘\n\n{old_review}\n"
    return pattern.sub(lambda match: match.group(1) + old_review + "\n", new_content, count=1)


def completed_task_key(task: str) -> str:
    return normalize_match_text(strip_task_metadata(task))


def completed_checklist_items_on_day(text: str, day: dt.date) -> list[str]:
    items: list[str] = []
    for line in text.splitlines():
        if "- [x]" not in line.lower():
            continue
        completed_match = re.search(r"\|\s*完成:\s*(\d{4}-\d{2}-\d{2})\b", line)
        if not completed_match or completed_match.group(1) != day.isoformat():
            continue
        task = strip_task_metadata(line)
        if task:
            items.append(task)
    return items


def habit_completed_items_on_day(root: Path, day: dt.date) -> list[str]:
    items: list[str] = []
    text = read(root / "state" / "habits.md")
    for match, title, name in habit_blocks(text):
        if day not in completion_dates(match.group(2)):
            continue
        items.append(name or title)
    return items


def unique_completed_tasks(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = completed_task_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def completed_tasks_on_day(root: Path, day: dt.date) -> list[str]:
    items: list[str] = []
    items.extend(habit_completed_items_on_day(root, day))
    items.extend(completed_checklist_items_on_day(read(schedule_path(root)), day))
    items.extend(completed_checklist_items_on_day(read(today_path(root)), day))
    for project_path in sorted((root / "projects").glob("*.md")):
        items.extend(completed_checklist_items_on_day(read(project_path), day))
    return unique_completed_tasks(items)


def render_daily(root: Path, day: dt.date) -> str:
    yesterday_path = root / "dailies" / f"{(day - dt.timedelta(days=1)).isoformat()}.md"
    yesterday = read(yesterday_path)
    done = completed_tasks_on_day(root, day - dt.timedelta(days=1)) or ["还没有记录已完成事项。"]
    yesterday_undone = normalize_task_list(checklist_items(yesterday, checked=False))
    today_open_tasks = normalize_task_list(checklist_items(read(today_path(root)), checked=False))
    undone = yesterday_undone or today_open_tasks or ["没有需要结转的未完成事项。"]
    waiting = checklist_items(read(root / "state" / "waiting.md"), checked=False) or bullet_lines(read(root / "state" / "waiting.md")) or ["当前没有等待中事项。"]
    blocked = checklist_items(read(root / "state" / "blocked.md"), checked=False) or bullet_lines(read(root / "state" / "blocked.md")) or ["当前没有阻塞项。"]
    projects = project_summaries(root)
    automations = checklist_items(iter_automation_text(root), checked=False)
    habits = habit_items(root, day)
    today_tasks = normalize_task_list([*yesterday_undone, *today_open_tasks])
    near_tasks = near_term_tasks(root, day)
    new_tasks = tasks_added_on(root, day)
    suggestions = render_daily_suggestions(
        near_tasks=near_tasks,
        today_tasks=today_tasks,
        waiting=waiting,
        blocked=blocked,
        projects=projects,
        automations=automations,
        habits=habits,
    )
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

## 近期需要处理的任务

{as_bullets(near_tasks or ["近期没有记录需要处理的任务。"])}

## 今日任务清单

### Habit

{as_habit_checklist(habits) or "- 暂无自动加入日报的 Habit。"}

### 其他任务

{as_checklist(today_tasks) or "- 暂无其他任务。"}

## 今日新增任务

{as_checklist(new_tasks) or "- 暂无。"}

## 今日建议

{as_bullets(suggestions)}

## 今日复盘

- 收获:
- 卡点:
- 结转:
"""


def normalize_task_list(items: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in items:
        task = strip_task_metadata(item)
        if not task or task.startswith("没有需要结转"):
            continue
        key = normalize_match_text(task)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(task)
    return normalized


def tasks_added_on(root: Path, day: dt.date) -> list[str]:
    tasks: list[str] = []
    seen: set[str] = set()
    marker = f"添加: {day.isoformat()}"
    for line in read(today_path(root)).splitlines():
        if not re.match(r"^\s*-\s+\[ \]\s+", line) or marker not in line:
            continue
        task = strip_task_metadata(line)
        key = normalize_match_text(task)
        if key in seen:
            continue
        seen.add(key)
        tasks.append(task)
    return tasks


def near_term_tasks(root: Path, day: dt.date) -> list[str]:
    start = day + dt.timedelta(days=1)
    end = day + dt.timedelta(days=3)
    items: list[tuple[dt.date, str]] = []
    seen: set[tuple[dt.date, str]] = set()
    for line in iter_schedule_lines(root):
        if not is_open_schedule_line(line):
            continue
        due = task_due_date(line)
        if not due or due < start:
            continue
        task = strip_task_metadata(line)
        key = (due, task)
        if key in seen:
            continue
        seen.add(key)
        items.append((due, task))
    items.sort(key=lambda item: (item[0], item[1]))
    selected = [(due, task) for due, task in items if due <= end]
    if len(selected) < 3:
        selected_keys = set(selected)
        for item in items:
            if item in selected_keys:
                continue
            selected.append(item)
            selected_keys.add(item)
            if len(selected) >= 3:
                break
    return [f"{due.isoformat()}：{task}" for due, task in selected]


def render_daily_suggestions(
    near_tasks: list[str],
    today_tasks: list[str],
    waiting: list[str],
    blocked: list[str],
    projects: list[str],
    automations: list[str],
    habits: list[tuple[str, bool]],
) -> list[str]:
    suggestions: list[str] = []
    active_blocked = [item for item in blocked if item != "当前没有阻塞项。"]
    active_waiting = [item for item in waiting if item != "当前没有等待中事项。"]
    open_habits = [name for name, completed in habits if not completed]

    if active_blocked:
        suggestions.append(f"先处理阻塞项“{short_task(active_blocked[0])}”，把卡点拆成一个可执行的解阻动作或明确需要谁来决策。")
    if near_tasks:
        suggestions.append(f"近期优先推进“{short_task(near_tasks[0])}”，先产出一个可验收的小结果，再处理低优先级事项。")
    if today_tasks:
        suggestions.append(f"今日其他任务从“{short_task(today_tasks[0])}”开始，建议先用 25 到 45 分钟完成第一步，避免只停留在待办列表里。")
    if open_habits:
        suggestions.append(f"Habit 还有 {len(open_habits)} 项未完成，建议把“{short_task(open_habits[0])}”安排到固定时段，完成后及时标记，保证连续记录不断。")
    if active_waiting:
        suggestions.append(f"等待中事项“{short_task(active_waiting[0])}”可以发一条简短跟进，确认对方下一步和预计时间。")
    if automations:
        suggestions.append(f"自动化候选里有 {len(automations)} 项开放任务，适合挑一项交给 Codex 拆步骤或直接执行，减少人工任务池压力。")
    if projects and not near_tasks:
        suggestions.append(f"长期项目当前没有近期明确截止项，建议从“{short_task(projects[0])}”反推出一个今天能完成的下一步。")
    if not suggestions:
        suggestions.append("今天任务池较轻，建议补充一个明确产出型任务，或做一次收件箱清理，把新事项路由到 Today、Scheduled、Project 或 Habit。")
    return suggestions[:5]


def short_task(value: str, limit: int = 48) -> str:
    value = strip_task_metadata(value)
    value = re.sub(r"^\d{4}-\d{2}-\d{2}[：:]\s*", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value if len(value) <= limit else value[:limit].rstrip() + "..."


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


def as_habit_checklist(items: list[tuple[str, bool]]) -> str:
    return "\n".join(f"- [{'x' if completed else ' '}] {name}" for name, completed in items)


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
    root, task = task_args(args)
    day = parse_date(args.date)
    learning = extract_learning(task, args.learning)
    task = strip_learning_clause(task)
    files = [
        root / "dailies" / f"{day.isoformat()}.md",
        today_path(root),
        root / "state" / "waiting.md",
        root / "state" / "blocked.md",
        schedule_path(root),
        automation_path(root),
    ]
    files.extend(sorted((root / "projects").glob("*.md")))
    changed = []
    needle = task.lower()
    for path in files:
        text = read(path)
        if not text:
            continue
        if path.name == "schedule.md":
            new_text, count = complete_schedule_text(text, task, day)
        else:
            new_text, count = re.subn(
                r"(^\s*-\s+\[ \]\s+.*" + re.escape(task) + r".*$)",
                lambda match: complete_line(match.group(1), day),
                text,
                flags=re.M | re.I,
            )
            if count == 0:
                new_text, count = mark_fuzzy(text, needle, day)
        if count:
            path.write_text(new_text, encoding="utf-8")
            changed.append(path)
            if path.name == "schedule.md":
                sync_completed_schedule_to_projects(root, new_text, task, day)
    habit_path, habit_matched, habit_added = complete_habit(root, task, day)
    if habit_path and habit_path not in changed:
        changed.append(habit_path)
    log_line = f"- {day.isoformat()} 已完成: {task}"
    if learning:
        log_line += f" | 收获: {learning}"
        append_daily_learning(root, day, learning, f"完成: {task}")
    append(root / "logs" / "execution-log.md", log_line)
    increment_stat(root / "state" / "stats.md", "已完成任务数")
    if habit_added:
        refresh_habit_stats(root)
    print("已在以下文件中标记完成:")
    for path in changed:
        print(f"- {path}")
    if not changed:
        print("- 没有找到匹配的未完成复选框；已仅记录完成日志。")
    elif habit_matched and not habit_added:
        print("- Habit 今天已经记录过完成，本次没有重复增加 Habit 完成次数。")
    print_diff(root)


def complete_line(line: str, day: dt.date) -> str:
    line = line.replace("[ ]", "[x]", 1)
    if re.search(r"\|\s*状态:\s*[^|]+", line):
        line = re.sub(r"\|\s*状态:\s*[^|]+", "| 状态: done ", line, count=1)
    elif "|" in line:
        line += " | 状态: done"
    if re.search(r"\|\s*完成:\s*[^|]*", line):
        line = re.sub(r"\|\s*完成:\s*[^|]*", f"| 完成: {day.isoformat()} ", line, count=1)
    elif "|" in line:
        line += f" | 完成: {day.isoformat()}"
    return normalize_metadata_spacing(line)


def complete_schedule_text(text: str, task: str, day: dt.date) -> tuple[str, int]:
    lines = text.splitlines()
    count = 0
    for i, line in enumerate(lines):
        if not is_open_schedule_line(line) or not matches_task_name(line, task):
            continue
        lines[i] = complete_line(line, day)
        count += 1
    return ("\n".join(lines) + "\n", count) if count else (text, 0)


def is_open_schedule_line(line: str) -> bool:
    return bool(re.match(r"^\s*-\s+", line)) and not re.search(r"\|\s*状态:\s*done\b", line, re.I)


def normalize_metadata_spacing(line: str) -> str:
    parts = [part.strip() for part in line.split("|")]
    return " | ".join(part for part in parts if part)


def mark_fuzzy(text: str, needle: str, day: dt.date) -> tuple[str, int]:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "- [ ]" in line and needle in line.lower():
            lines[i] = complete_line(line, day)
            return "\n".join(lines) + "\n", 1
    return text, 0


def sync_completed_schedule_to_projects(root: Path, schedule_text: str, task: str, day: dt.date) -> None:
    for line in schedule_text.splitlines():
        if not re.search(r"\|\s*状态:\s*done\b", line, re.I) or not matches_task_name(line, task):
            continue
        project = project_ref_from_line(line)
        task_id = task_id_from_line(line)
        if not project or not task_id:
            continue
        project_path = find_project_path(root, project)
        if project_path.exists():
            sync_project_subtask_complete(project_path, task_id, day)


def sync_project_subtask_complete(project_path: Path, task_id: str, day: dt.date) -> None:
    lines = []
    changed = False
    for line in read(project_path).splitlines():
        if task_id not in line or "- [ ]" not in line:
            lines.append(line)
            continue
        lines.append(complete_line(line, day))
        changed = True
    if changed:
        project_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def remove_task(args: argparse.Namespace) -> None:
    root, task = task_args(args)
    day = parse_date(args.date)
    candidates = find_remove_candidates(root, task, day)
    if not candidates:
        print(f"没有在当前任务池中找到匹配任务: {task}")
        return
    if not args.confirm:
        print_remove_candidates(candidates, task)
        print("\n请二次确认后再删除，例如:")
        print(f"python3 {Path(__file__).resolve()} remove-task {quote_arg(str(root))} {quote_arg(task)} --date {day.isoformat()} --confirm 1")
        print(f"python3 {Path(__file__).resolve()} remove-task {quote_arg(str(root))} {quote_arg(task)} --date {day.isoformat()} --confirm all")
        return
    selected = select_remove_candidates(candidates, args.confirm)
    if not selected:
        print(f"没有有效的确认编号: {args.confirm}")
        print_remove_candidates(candidates, task)
        return
    delete_remove_candidates(selected)
    refresh_habit_stats(root)
    print("已删除以下任务:")
    for candidate in selected:
        try:
            rel = candidate.path.relative_to(root)
        except ValueError:
            rel = candidate.path
        print(f"- [{candidate.id}] {candidate.kind} {rel}:{candidate.start_line} {candidate.text}")
    print_diff(root)


def find_remove_candidates(root: Path, query: str, day: dt.date) -> list[RemoveCandidate]:
    paths = current_task_pool_paths(root, day)
    candidates: list[RemoveCandidate] = []
    next_id = 1
    seen: set[tuple[Path, str, int, int]] = set()
    for path in paths:
        text = read(path)
        if not text:
            continue
        for kind, item_text, start, end in candidate_spans(path, text):
            if not matches_task_name(item_text, query):
                continue
            key = (path, kind, start, end)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(RemoveCandidate(next_id, path, kind, item_text.strip(), start, end))
            next_id += 1
    return candidates


def current_task_pool_paths(root: Path, day: dt.date) -> list[Path]:
    paths = [
        root / "dailies" / f"{day.isoformat()}.md",
        today_path(root),
        schedule_path(root),
        automation_path(root),
        archive_path(root),
        root / "state" / "waiting.md",
        root / "state" / "blocked.md",
        root / "state" / "habits.md",
    ]
    paths.extend(sorted((root / "projects").glob("*.md")))
    return paths


def candidate_spans(path: Path, text: str) -> list[tuple[str, str, int, int]]:
    candidates: list[tuple[str, str, int, int]] = []
    if path.name == "habits.md":
        candidates.extend(habit_remove_spans(text))
    if path.name == "automation-candidates.md":
        candidates.extend(automation_remove_spans(text))
    if path.parent.name == "projects":
        candidates.extend(project_remove_spans(path, text))
    candidates.extend(checklist_remove_spans(text))
    candidates.extend(list_item_remove_spans(text))
    return candidates


def checklist_remove_spans(text: str) -> list[tuple[str, str, int, int]]:
    spans = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*-\s+\[[ xX]\]\s+", line):
            cleaned = re.sub(r"^\s*-\s+\[[ xX]\]\s+", "", line).strip()
            spans.append(("checkbox", cleaned, line_no, line_no))
    return spans


def list_item_remove_spans(text: str) -> list[tuple[str, str, int, int]]:
    spans = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*-\s+\[[ xX]\]\s+", line):
            continue
        if not re.match(r"^\s*-\s+", line):
            continue
        cleaned = re.sub(r"^\s*-\s+", "", line).strip()
        spans.append(("list-item", cleaned, line_no, line_no))
    return spans


def habit_remove_spans(text: str) -> list[tuple[str, str, int, int]]:
    spans = []
    for match, title, name in habit_blocks(text):
        start = line_number_at(text, match.start())
        end = line_number_at(text, match.end())
        body = match.group(2).strip()
        searchable = "\n".join(part for part in [title, name, body] if part)
        spans.append(("habit", searchable, start, end))
    return spans


def automation_remove_spans(text: str) -> list[tuple[str, str, int, int]]:
    spans = []
    for match in re.finditer(r"^##\s+(.+?)\n(.*?)(?=^##\s+|\Z)", text, re.M | re.S):
        start = line_number_at(text, match.start())
        end = line_number_at(text, match.end())
        searchable = (match.group(1).strip() + "\n" + match.group(2).strip()).strip()
        spans.append(("automation-candidate", searchable, start, end))
    return spans


def project_remove_spans(path: Path, text: str) -> list[tuple[str, str, int, int]]:
    title = text.splitlines()[0].lstrip("# ").strip() if text else path.stem
    if not title:
        return []
    return [("project", title, 1, max(1, len(text.splitlines())))]


def line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def print_remove_candidates(candidates: list[RemoveCandidate], query: str) -> None:
    print(f"在当前任务池中找到 {len(candidates)} 个可能匹配: {query}")
    for candidate in candidates:
        print(f"[{candidate.id}] {candidate.kind} {candidate.path}:{candidate.start_line}")
        print(f"    {candidate.text.splitlines()[0]}")


def select_remove_candidates(candidates: list[RemoveCandidate], confirm: str) -> list[RemoveCandidate]:
    value = confirm.strip().lower()
    if value in {"all", "全部"}:
        return candidates
    ids: set[int] = set()
    for piece in re.split(r"[,，\s]+", value):
        if not piece:
            continue
        if not piece.isdigit():
            continue
        ids.add(int(piece))
    return [candidate for candidate in candidates if candidate.id in ids]


def delete_remove_candidates(candidates: list[RemoveCandidate]) -> None:
    by_path: dict[Path, list[RemoveCandidate]] = {}
    for candidate in candidates:
        by_path.setdefault(candidate.path, []).append(candidate)
    for path, path_candidates in by_path.items():
        if any(candidate.kind == "project" for candidate in path_candidates):
            path.unlink()
            continue
        text = read(path)
        lines = text.splitlines()
        for candidate in sorted(path_candidates, key=lambda item: item.start_line, reverse=True):
            sync_project_subtask_delete(path, lines[candidate.start_line - 1])
            start = candidate.start_line - 1
            end = candidate.end_line
            del lines[start:end]
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sync_project_subtask_delete(source_path: Path, line: str) -> None:
    if source_path.name != "schedule.md":
        return
    project = project_ref_from_line(line)
    task_id = task_id_from_line(line)
    if not project or not task_id:
        return
    root = source_path.parents[1]
    project_path = find_project_path(root, project)
    if not project_path.exists():
        return
    text = read(project_path)
    lines = [existing for existing in text.splitlines() if task_id not in existing]
    project_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def sync_project_subtask_update(source_path: Path, old_line: str, new_task: str, new_date: Optional[dt.date]) -> None:
    if source_path.name != "schedule.md":
        return
    project = project_ref_from_line(old_line)
    task_id = task_id_from_line(old_line)
    if not project or not task_id:
        return
    root = source_path.parents[1]
    project_path = find_project_path(root, project)
    if not project_path.exists():
        return
    text = read(project_path)
    lines = []
    updated = False
    for line in text.splitlines():
        if task_id not in line:
            lines.append(line)
            continue
        due = new_date.isoformat() if new_date else (task_due_date(line) or today()).isoformat()
        acceptance_match = re.search(r"\|\s*验收:\s*([^|]+)", line)
        acceptance = acceptance_match.group(1).strip() if acceptance_match else "按更新后的任务说明完成。"
        lines.append(f"- [ ] {new_task} | 截止: {due} | 验收: {acceptance} | 子任务: {task_id}")
        updated = True
    project_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    if not updated:
        due = new_date.isoformat() if new_date else today().isoformat()
        append_under_heading(project_path, "子任务清单", f"- [ ] {new_task} | 截止: {due} | 验收: 按更新后的任务说明完成。 | 子任务: {task_id}")


def update_task(args: argparse.Namespace) -> None:
    root, query = task_args(args)
    day = parse_date(args.date)
    candidates = find_remove_candidates(root, query, day)
    if not candidates:
        print(f"没有找到可更新的任务: {query}")
        return
    candidate = candidates[0]
    new_task = args.new_task or strip_task_metadata(candidate.text)
    new_type = classify_task(new_task, args.type) if args.type else source_task_type(candidate.path)
    new_date = parse_date(args.due_date) if args.due_date else task_due_date(candidate.text)
    old_line = read(candidate.path).splitlines()[candidate.start_line - 1]
    delete_remove_candidates([candidate])
    add_updated_task(root, new_task, new_type, new_date, day, old_line)
    if candidate.path.name == "schedule.md":
        sync_project_subtask_update(candidate.path, old_line, new_task, new_date)
    print(f"已更新任务: {query} -> {new_task} ({new_type})")
    print_diff(root)


def source_task_type(path: Path) -> str:
    if path.name == "today.md" or path.parent.name == "dailies":
        return "today"
    if path.name == "schedule.md":
        return "scheduled"
    if path.name == "habits.md":
        return "habit"
    if path.name == "waiting.md":
        return "waiting"
    if path.name == "blocked.md":
        return "blocked"
    if path.name == "automation-candidates.md":
        return "automation"
    if path.parent.name == "projects":
        return "project"
    return "today"


def add_updated_task(root: Path, task: str, task_type: str, due_date: Optional[dt.date], day: dt.date, old_line: str) -> None:
    if task_type == "today" and due_date and due_date != day:
        task_type = "scheduled"
    if task_type == "scheduled" and due_date == day:
        append_unique_line(today_path(root), f"- [ ] {task} | 来源: scheduled | 日期: {day.isoformat()}")
    if task_type == "today":
        add_today_task(root, task, day)
    elif task_type == "scheduled":
        date_text = due_date.isoformat() if due_date else day.isoformat()
        suffix = ""
        project = project_ref_from_line(old_line)
        task_id = task_id_from_line(old_line)
        if project:
            suffix += f" | 项目: {project}"
        if task_id:
            suffix += f" | 子任务: {task_id}"
        append_unique_line(schedule_path(root), schedule_entry(task, dt.date.fromisoformat(date_text), suffix))
    elif task_type == "habit":
        append(root / "state" / "habits.md", "\n" + render_template("habit.md", habit_name=task))
        refresh_habit_stats(root)
    elif task_type == "waiting":
        append_unique_line(root / "state" / "waiting.md", f"- [ ] {task} | 更新: {day.isoformat()}")
    elif task_type == "blocked":
        append_unique_line(root / "state" / "blocked.md", f"- [ ] {task} | 更新: {day.isoformat()}")
    elif task_type == "project":
        add_project_task(root, task, day)
    elif task_type == "automation":
        add_automation_candidate(root, task, day)
    else:
        append_unique_line(archive_path(root), f"- {day.isoformat()} {task}")


def quote_arg(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def weekly_review(args: argparse.Namespace) -> None:
    root = resolve_repo(args.repo)
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
    automation_count = len(re.findall(r"^## \d{4}-\d{2}-\d{2}", read(automation_path(root)), re.M))
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
    root = resolve_repo(args.repo)
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

    p = sub.add_parser("set-repo", help="Record the default PersonalOS repository path.")
    p.add_argument("repo")
    p.set_defaults(func=set_repo)

    p = sub.add_parser("daily", help="Generate a Daily file.")
    p.add_argument("repo", nargs="?")
    p.add_argument("--date")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=daily)

    p = sub.add_parser("add-task", help="Add and route a task using Intent First.")
    p.add_argument("repo_or_task")
    p.add_argument("task", nargs="?")
    p.add_argument("--type")
    p.add_argument("--date")
    p.set_defaults(func=add_task)

    p = sub.add_parser("complete-task", help="Complete a matching task.")
    p.add_argument("repo_or_task")
    p.add_argument("task", nargs="?")
    p.add_argument("--date")
    p.add_argument("--learning", help="Learning or insight to append to today's daily review.")
    p.set_defaults(func=complete_task)

    p = sub.add_parser("update-task", help="Update task content, type, or due date.")
    p.add_argument("repo_or_task")
    p.add_argument("task", nargs="?")
    p.add_argument("--new-task", help="Replacement task text.")
    p.add_argument("--type", help="Replacement task type.")
    p.add_argument("--due-date", help="Replacement due date for scheduled/today flow.")
    p.add_argument("--date")
    p.set_defaults(func=update_task)

    p = sub.add_parser("remove-task", help="Find matching tasks and remove confirmed candidates.")
    p.add_argument("repo_or_task")
    p.add_argument("task", nargs="?")
    p.add_argument("--date")
    p.add_argument("--confirm", help="Candidate id list such as 1,3, or all. Omit to list candidates only.")
    p.set_defaults(func=remove_task)

    p = sub.add_parser("update-project", help="Update project progress, milestones, and learnings.")
    p.add_argument("project")
    p.add_argument("update", nargs="?")
    p.add_argument("--repo")
    p.add_argument("--date")
    p.add_argument("--progress")
    p.add_argument("--milestone")
    p.add_argument("--learning")
    p.set_defaults(func=update_project)

    p = sub.add_parser("plan-project", help="Draft or confirm a project subtask plan.")
    p.add_argument("project")
    p.add_argument("--repo")
    p.add_argument("--date")
    p.add_argument("--deadline")
    p.add_argument("--confirm", action="store_true")
    p.set_defaults(func=plan_project)

    p = sub.add_parser("weekly-review", help="Generate a weekly review.")
    p.add_argument("repo", nargs="?")
    p.add_argument("--week-start")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=weekly_review)

    p = sub.add_parser("project-review", help="Review projects for stale, stalled, or risky state.")
    p.add_argument("repo", nargs="?")
    p.add_argument("--date")
    p.set_defaults(func=project_review)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
