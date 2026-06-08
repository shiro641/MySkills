# personal-execution-skill

A reusable Codex Skill for creating and operating a local Git-backed Personal OS: a Personal Chief of Staff system for daily work, long-term projects, Waiting and Blocked items, automation candidates, weekly reviews, execution logs, and future habits.

默认生成中文内容。日报会同时写入 Markdown 文件，并由 Codex 在当前项目下新建一个聊天会话，把日报正文发送给用户。

## Install

Copy or symlink this directory into your Codex skills directory:

```bash
mkdir -p ~/.codex/skills
cp -R personal-execution-skill ~/.codex/skills/
```

Then ask Codex to use `personal-execution-skill`.

## Bootstrap A Repository

```bash
python3 personal-execution-skill/scripts/personal_os.py bootstrap ./my-personal-os
```

This creates the standard PersonalOS structure, initializes Git, writes empty factual ledgers, and creates the first commit. Bootstrap does not invent people, tasks, projects, habits, automation candidates, dailies, or weekly reviews.

Bootstrap also records `./my-personal-os` as the default PersonalOS repository in `personal-execution-skill/state/config.json`. Later commands can omit the repo path unless you want to target a different PersonalOS repository.

## Common Commands

```bash
python3 personal-execution-skill/scripts/personal_os.py daily ./my-personal-os
python3 personal-execution-skill/scripts/personal_os.py set-repo ./my-personal-os
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "等待对方回复预算确认" --type waiting
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "阅读 codecli 源码" --type project
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "学习这个单词" --type habit
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "Generate monthly metrics report from CSV"
python3 personal-execution-skill/scripts/personal_os.py complete-task ./my-personal-os "等待对方回复预算确认"
python3 personal-execution-skill/scripts/personal_os.py weekly-review ./my-personal-os
python3 personal-execution-skill/scripts/personal_os.py project-review ./my-personal-os
```

After bootstrap, these shorter forms also work:

```bash
python3 personal-execution-skill/scripts/personal_os.py daily
python3 personal-execution-skill/scripts/personal_os.py add-task "阅读 codecli 源码" --type project
python3 personal-execution-skill/scripts/personal_os.py add-task "学习这个单词" --type habit
python3 personal-execution-skill/scripts/personal_os.py complete-task "学习这个单词"
python3 personal-execution-skill/scripts/personal_os.py weekly-review
python3 personal-execution-skill/scripts/personal_os.py project-review
```

If the PersonalOS repository already exists somewhere else, record it first:

```bash
python3 personal-execution-skill/scripts/personal_os.py set-repo /path/to/personal-os
```

## PersonalOS Standard Structure

See `SKILL.md` and `references/schema.md` for the canonical structure and file semantics.

## Notes

- The Skill follows Intent First classification. If a user explicitly names a task type, that type wins.
- If a user says "调用 add task", "作为 habit", "作为惯例", or "完成时更新状态", use this skill's script workflow directly; these are not MCP tool names.
- Bootstrap records the user's default PersonalOS path in `state/config.json`; this runtime config should not be committed.
- Daily generation should run `scripts/personal_os.py daily`; do not hand-write a Daily or invent generic time-block advice.
- Automation candidates are not added to manual todos. They are routed to `tasks/automation-candidates.md` with prompt, steps, expected artifacts, and acceptance criteria.
- Daily generation creates `dailies/YYYY-MM-DD.md` and should also create a new Codex project thread titled `日报 YYYY-MM-DD`.
- After each update, inspect `git diff` and make a commit when the change is accepted.
