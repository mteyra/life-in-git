#!/usr/bin/env python3
"""life: plain-text lists in a git repository, from the terminal, a phone or a bot.

Works on a "life" data repository laid out as described in FORMAT.md. Standard
library only; Python 3.9+.

Commands (run inside the data repo, or pass --dir):
    add TEXT [--to inbox|todo|shopping|quote]   capture something (default: inbox)
    done TEXT                                   tick the first open todo/shopping item containing TEXT
    habit NAME [VALUE]                          log a habit for today (value defaults to 1)
    ls [inbox|todo|shopping]                    show open items
    quote                                       a random quote
    stats [--days N] [--markdown]               counts for the last N days (JSON, or a profile snippet)
    profile README [--days N]                   put the snippet between <!-- life:start --> and <!-- life:end -->
    ingest --labels L --title T [--body B]      file a phone capture (used by the GitHub Action)

Options: --dir DIR (data repo, default $LIFE_DIR or .), --when ISO-TIME (default now),
         --git (pull before, then commit and push the change).
"""
import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

TZ_NAME = os.environ.get("LIFE_TZ", "Europe/Berlin")
FILES = {
    "inbox": "inbox.md",
    "todo": "todo.md",
    "shopping": "lists/shopping.md",
    "quote": "quotes.md",
    "habits": "habits/log.csv",
}
LABELS = ("done", "habit", "quote", "todo", "shopping", "inbox")  # first match wins
OPEN = re.compile(r"^- \[ \] (.*)$")
DONE = re.compile(r"^- \[x\] (.*)$", re.I)


class LifeError(Exception):
    pass


def local_time(when=None):
    tz = ZoneInfo(TZ_NAME) if ZoneInfo else None
    if not when:
        return dt.datetime.now(tz)
    parsed = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=tz)
    return parsed.astimezone(tz) if tz else parsed


def one_line(text):
    return " ".join(str(text).split())


def append_line(path, line):
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8")


def add(root, text, to="inbox", when=None, body=""):
    text = one_line(text)
    if not text:
        raise LifeError("nothing to add")
    now = local_time(when)
    if to == "inbox":
        line = f"- {now:%Y-%m-%d %H:%M} · {text}"
        extra = [f"  {one_line(part)}" for part in str(body or "").splitlines() if part.strip()]
        line = "\n".join([line] + extra)
    elif to == "todo":
        line = f"- [ ] {text} added:{now:%Y-%m-%d}"
    elif to == "shopping":
        line = f"- [ ] {text}"
    elif to == "quote":
        line = f"- {text}"
    else:
        raise LifeError(f"unknown list: {to}")
    path = Path(root) / FILES[to]
    append_line(path, line)
    return path, f"Added to {FILES[to]}: {text}"


def done(root, text, when=None):
    needle = one_line(text).lower()
    if not needle:
        raise LifeError("say which item is done")
    today = local_time(when).date().isoformat()
    for key in ("todo", "shopping"):
        path = Path(root) / FILES[key]
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = OPEN.match(line)
            if match and needle in match.group(1).lower():
                ticked = "- [x] " + match.group(1)
                if key == "todo":
                    ticked += f" done:{today}"
                lines[index] = ticked
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return path, f"Ticked in {FILES[key]}: {match.group(1)}"
    raise LifeError(f"no open todo or shopping item contains '{one_line(text)}'")


def habit(root, name, value="1", when=None):
    name = one_line(name).lower()
    if not name or "," in name:
        raise LifeError("habit names can't be empty or contain commas")
    value = one_line(value or "1").replace(",", ";")
    path = Path(root) / FILES["habits"]
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("date,habit,value\n", encoding="utf-8")
    append_line(path, f"{local_time(when):%Y-%m-%d},{name},{value}")
    return path, f"Logged habit: {name} ({value})"


def open_items(root, which):
    path = Path(root) / FILES[which]
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if which == "inbox":
        return [line[2:] for line in lines if line.startswith("- ")]
    return [OPEN.match(line).group(1) for line in lines if OPEN.match(line)]


def quotes(root):
    path = Path(root) / FILES["quote"]
    if not path.exists():
        return []
    return [line[2:].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]


def habit_rows(root):
    path = Path(root) / FILES["habits"]
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def stats(root, days=7, when=None):
    today = local_time(when).date()
    start = today - dt.timedelta(days=days - 1)
    todo_path = Path(root) / FILES["todo"]
    done_recent = 0
    if todo_path.exists():
        for line in todo_path.read_text(encoding="utf-8").splitlines():
            match = re.search(r"\bdone:(\d{4}-\d{2}-\d{2})\b", line)
            if DONE.match(line) and match and start <= dt.date.fromisoformat(match.group(1)) <= today:
                done_recent += 1
    habits = {}
    by_habit = {}
    for row in habit_rows(root):
        try:
            day = dt.date.fromisoformat(row["date"])
        except (KeyError, ValueError):
            continue
        by_habit.setdefault(row["habit"], set()).add(day)
    for name, dates in sorted(by_habit.items()):
        streak, day = 0, today if today in dates else today - dt.timedelta(days=1)
        while day in dates:
            streak, day = streak + 1, day - dt.timedelta(days=1)
        habits[name] = {"days": sum(start <= d <= today for d in dates), "streak": streak}
    all_quotes = quotes(root)
    return {
        "period_days": days,
        "until": today.isoformat(),
        "todos_done": done_recent,
        "todos_open": len(open_items(root, "todo")),
        "inbox": len(open_items(root, "inbox")),
        "habits": habits,
        "quote_of_the_day": all_quotes[today.toordinal() % len(all_quotes)] if all_quotes else None,
    }


def stats_markdown(data):
    lines = [f"**This week:** {data['todos_done']} tasks done · {data['todos_open']} open"]
    if data["habits"]:
        parts = [f"{name} {info['days']}/{data['period_days']}d" + (f" (🔥 {info['streak']})" if info["streak"] > 1 else "")
                 for name, info in data["habits"].items()]
        lines.append("**Habits:** " + " · ".join(parts))
    if data["quote_of_the_day"]:
        lines.append(f"> {data['quote_of_the_day']}")
    return "\n\n".join(lines)


def update_profile(readme, snippet):
    """Replace the text between the life markers in a profile README. Returns True if it changed."""
    path = Path(readme)
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"(<!-- life:start -->)(.*?)(<!-- life:end -->)", re.S)
    if not pattern.search(text):
        raise LifeError(f"{path} has no <!-- life:start --> ... <!-- life:end --> markers")
    new = pattern.sub(lambda m: f"{m.group(1)}\n{snippet}\n{m.group(3)}", text, count=1)
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True


def ingest(root, labels, title, body="", when=None):
    """File one phone capture (a GitHub issue) by its first known label."""
    names = [label.strip().lower() for label in str(labels or "").split(",") if label.strip()]
    kind = next((label for label in LABELS if label in names), "inbox")
    if kind == "done":
        return done(root, title, when)
    if kind == "habit":
        return habit(root, title, (body or "1").strip() or "1", when)
    return add(root, title, to=kind, when=when, body=body if kind == "inbox" else "")


def git(root, *args, check=True):
    return subprocess.run(["git", "-C", str(root), *args], check=check, capture_output=True, text=True)


def commit_and_push(root, path, message):
    git(root, "add", "--", str(Path(path).resolve().relative_to(Path(root).resolve())))
    if not git(root, "diff", "--cached", "--quiet", check=False).returncode:
        return
    git(root, "commit", "-q", "-m", message[:72])
    for _ in range(3):
        if git(root, "push", "-q", check=False).returncode == 0:
            return
        git(root, "pull", "-q", "--rebase", check=False)
    raise LifeError("push failed three times; the change is committed locally")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="life", description="Plain-text lists in a git repository.")
    parser.add_argument("--dir", default=os.environ.get("LIFE_DIR", "."), help="the data repository")
    parser.add_argument("--when", help="ISO time of the event (default: now)")
    parser.add_argument("--git", action="store_true", help="pull first, then commit and push the change")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("add"); p.add_argument("text", nargs="+"); p.add_argument("--to", default="inbox", choices=["inbox", "todo", "shopping", "quote"])
    p = sub.add_parser("done"); p.add_argument("text", nargs="+")
    p = sub.add_parser("habit"); p.add_argument("name"); p.add_argument("value", nargs="?", default="1")
    p = sub.add_parser("ls"); p.add_argument("which", nargs="?", default="todo", choices=["inbox", "todo", "shopping"])
    sub.add_parser("quote")
    p = sub.add_parser("stats"); p.add_argument("--days", type=int, default=7); p.add_argument("--markdown", action="store_true")
    p = sub.add_parser("profile"); p.add_argument("readme"); p.add_argument("--days", type=int, default=7)
    p = sub.add_parser("ingest"); p.add_argument("--labels", default=""); p.add_argument("--title", required=True); p.add_argument("--body", default="")
    args = parser.parse_args(argv)
    root = Path(args.dir)

    try:
        if args.command == "ls":
            for item in open_items(root, args.which):
                print(item)
            return 0
        if args.command == "quote":
            options = quotes(root)
            print(random.choice(options) if options else "No quotes yet.")
            return 0
        if args.command == "stats":
            data = stats(root, args.days, args.when)
            print(stats_markdown(data) if args.markdown else json.dumps(data, ensure_ascii=False, indent=2))
            return 0
        if args.command == "profile":
            changed = update_profile(args.readme, stats_markdown(stats(root, args.days, args.when)))
            print("Profile updated." if changed else "Profile unchanged.")
            return 0
        if args.git:
            git(root, "pull", "-q", "--rebase", check=False)
        if args.command == "add":
            path, message = add(root, " ".join(args.text), args.to, args.when)
        elif args.command == "done":
            path, message = done(root, " ".join(args.text), args.when)
        elif args.command == "habit":
            path, message = habit(root, args.name, args.value, args.when)
        else:
            path, message = ingest(root, args.labels, args.title, args.body, args.when)
        if args.git:
            commit_and_push(root, path, message)
        print(message)
        return 0
    except (LifeError, subprocess.CalledProcessError) as error:
        print(f"life: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
