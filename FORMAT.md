# Data format

Everything is Markdown or CSV, one item per line, so a person, a phone, a script and an AI can all read and write it.

| File | Holds | Line format |
| --- | --- | --- |
| `inbox.md` | Everything captured and not yet sorted | `- 2026-11-20 22:30 · call the bank` (optional detail lines indented two spaces below) |
| `todo.md` | All tasks, in one place | `- [ ] Update the CV PDF #homepage due:2026-11-30 added:2026-11-20` |
| | Finished tasks | `- [x] Update the CV PDF #homepage done:2026-11-22` |
| `projects/<name>.md` | Background, ideas and decisions for one project. Its tasks live in `todo.md` with `#<name>` | free Markdown |
| `lists/shopping.md` | Shopping | `- [ ] oat milk` / `- [x] oat milk` |
| `lists/reading.md` | Books and articles | sections *Want* · *Reading* · *Done*; `- Title — Author (added:2026-11-20)`, plus a one-line takeaway when done |
| `lists/watch.md`, `lists/wishlist.md`, `lists/places.md` | Films and series, things to maybe buy, places to go | `- item`, optional ` — note` |
| `habits/habits.md` | Which habits I track and what counts | a table |
| `habits/log.csv` | One row per habit tick, never edited | `date,habit,value`, e.g. `2026-11-20,gym,1` |
| `quotes.md` | Favourite quotes and sayings | `- Regret nothing.`, optional ` — who said it` |
| `reviews/2026-W47.md` | Weekly reviews | written by an agent, merged by me |
| `done.md` | The record of finished things, newest first | `- [x] …` |

## Tags

- `#project`: which project a task belongs to, matching `projects/<project>.md`.
- `@place`: where it can be done (`@uni`, `@home`, `@laptop`, `@phone`).
- `due:YYYY-MM-DD`, `added:YYYY-MM-DD`, `done:YYYY-MM-DD`: dates, always in this form.

## Phone captures (issue labels)

The Action reads the **first** matching label in this order and files the issue title (and body):

| Label | Effect |
| --- | --- |
| `done` | ticks the first open item in `todo.md`, then `lists/shopping.md`, whose text contains the title |
| `habit` | appends `today,<title>,<body or 1>` to `habits/log.csv` |
| `quote` | appends the title to `quotes.md` |
| `todo` | appends the title to `todo.md` as an open task |
| `shopping` | appends the title to `lists/shopping.md` |
| `inbox`, or no label | appends the title and body to `inbox.md` with the time |

Then it commits as the owner and closes the issue with a comment saying what it did. If something can't be filed (e.g. `done` matched nothing), the issue stays open with a comment saying why.
