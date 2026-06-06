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

This creates the standard PersonalOS structure, initializes Git, writes example data, and creates the first commit.

## Common Commands

```bash
python3 personal-execution-skill/scripts/personal_os.py daily ./my-personal-os
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "Follow up with Alice on budget" --type waiting
python3 personal-execution-skill/scripts/personal_os.py add-task ./my-personal-os "Generate monthly metrics report from CSV"
python3 personal-execution-skill/scripts/personal_os.py complete-task ./my-personal-os "Follow up with Alice"
python3 personal-execution-skill/scripts/personal_os.py weekly-review ./my-personal-os
python3 personal-execution-skill/scripts/personal_os.py project-review ./my-personal-os
```

## PersonalOS Standard Structure

See `SKILL.md` and `references/schema.md` for the canonical structure and file semantics.

## Notes

- The Skill follows Intent First classification. If a user explicitly names a task type, that type wins.
- Automation candidates are not added to manual todos. They are routed to `tasks/automation-candidates.md` with prompt, steps, expected artifacts, and acceptance criteria.
- Daily generation creates `dailies/YYYY-MM-DD.md` and should also create a new Codex project thread titled `日报 YYYY-MM-DD`.
- After each update, inspect `git diff` and make a commit when the change is accepted.
