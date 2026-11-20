# life-in-git

My to-dos, shopping list, ideas, habits, reading list and favourite quotes live as plain text files in a **private git repository**. This public repository is the engine that keeps them running: a small command-line tool, the GitHub Action that files what I capture on my phone, and the instructions for the iPhone Shortcuts.

**Why git:**
- **Every change is a commit.** Nothing gets lost, and the history shows when I added or finished something.
- **It's free and reachable from anywhere:** phone, laptop, browser, or the GitHub app.
- **Plain text never locks me in.** Any AI agent can read and update it.

## How it works

```
iPhone Shortcut ("Capture: call the bank")
   │  creates an issue in the private repo, labelled e.g. inbox / todo / shopping / done / habit / quote
   ▼
GitHub Action in the private repo
   │  runs life.py from this repo: writes the line into the right file, commits, closes the issue
   ▼
private "life" repo:  inbox.md · todo.md · lists/ · habits/ · quotes.md · reviews/
   ▲
   │  laptop: `life add …`, `life done …`, or AI agents through git
   │  weekly: an agent sorts the inbox and proposes changes as a pull request
```

Phone captures go through issues instead of editing files directly. That way each capture is **one simple request**: there's no file version to fetch, and two captures arriving at the same moment don't conflict. The Action does the editing.

## What goes in it, and what doesn't

Private repositories are **not end-to-end encrypted**: GitHub can technically read them.

| In the repo | Not in the repo |
| --- | --- |
| Lists, ideas, to-dos, habits, reading, quotes | Health data, mood or diary |
| | Other people's messages |
| | Location |
| | Passwords |

The things in the second column belong somewhere local, or encrypted.

## Setup

1. **The data repository.** Create a private repository (mine is `life`) and copy the contents of [`template/`](template/) into it, including `.github/` and `.gitignore`. [`FORMAT.md`](FORMAT.md) describes every file.
2. **Commit identity.** Edit the two `git config` lines in `.github/workflows/file-captures.yml` to your name and your GitHub no-reply email, so captures count as your commits.
3. **Phone.** Follow [`shortcuts/README.md`](shortcuts/README.md): one fine-grained token, limited to the data repository, and four Shortcuts (Capture, Add to list, Done, Habit). Each takes two minutes.
4. **Laptop (optional).** Clone the data repository and run `python3 life.py --dir ~/life ls`. Use `--git` to pull, commit and push in one go, e.g. `python3 life.py --dir ~/life --git add "Book flights" --to todo`. A shell alias makes it `life add …`.
5. **Profile stats (optional).** Put `<!-- life:start --><!-- life:end -->` in your profile README. Then add a secret `PROFILE_TOKEN` to the data repository: a fine-grained token with *Contents: read and write* on your profile repository only. The daily Action then writes harmless counts and a quote of the day between the markers: tasks done this week, habit streaks.

## Command line

```
life.py add TEXT [--to inbox|todo|shopping|quote]
life.py done TEXT                 tick the first open to-do or shopping item containing TEXT
life.py habit NAME [VALUE]        log a habit for today
life.py ls [inbox|todo|shopping]
life.py quote                     a random quote
life.py stats [--days 7] [--markdown]
life.py profile README            update the profile snippet
life.py ingest --labels L --title T [--body B]   (used by the Action)
```

Standard library only, Python 3.10 or newer (CI tests 3.10 and 3.13). Times are Europe/Berlin unless `LIFE_TZ` says otherwise. Run the tests with `python3 -m unittest discover -s tests`.

## Limits worth knowing

- **Private Actions minutes:** each capture runs the Action for a few seconds, but GitHub bills private repositories by the minute. Dozens of captures a day can use a few hundred minutes a month, still inside the free allowance for most people.
- **Contribution graph:** captures and ticks are real actions, so they count. Commits made only to colour the graph would go against GitHub's terms, and this system doesn't make any.
- **Phone without signal:** a Shortcut can't reach GitHub offline. Capture again when you're back online.

## License

MIT
