# Rules for AI agents in this repository

These are the owner's personal lists. Formats are defined in [FORMAT.md](https://github.com/mteyra/life-in-git/blob/main/FORMAT.md); follow them exactly, because phone Shortcuts and scripts parse these files.

## Always

- **One item per line**, in the documented format. Dates are `YYYY-MM-DD`.
- **Never delete or rewrite history.** Tick tasks (`- [x] … done:YYYY-MM-DD`) instead of removing them; the weekly review moves them to `done.md`.
- **Tasks live only in `todo.md`.** Project files hold background, ideas and decisions, and link tasks by `#project` tag.
- **Keep sensitive things out.** Health or mood data, other people's messages, location, passwords and anything secret stay out of this repository, even though it's private. Say so if asked to add them.

## Changes

- **Single items** (add, tick): a direct commit is fine.
- **Anything bigger** (sorting the inbox, reorganizing, the weekly review): a branch and a pull request. The owner merges it, and merging is the approval.

## Weekly review (when asked, or on a schedule)

On a branch `review/YYYY-Www`:

1. **Inbox:** propose a destination for every line (a task, a list, a project file, or delete), and apply it.
2. **Finished tasks:** move ticked ones from `todo.md` to the top of `done.md`.
3. **Overdue and stale:** flag tasks with a `due:` in the past, and open tasks older than four weeks.
4. **Habits:** summarise the week from `habits/log.csv`, with streaks.
5. **The review:** write `reviews/YYYY-Www.md`: done, carried over, habits, and one suggestion for next week.
6. **Hand it over:** open a pull request titled "Weekly review YYYY-Www". Don't merge it yourself.
