# iPhone Shortcuts

Four Shortcuts cover daily use. Each one is a single request to GitHub: it creates an issue in your private data repository, and the Action files it. Building one takes about two minutes in the Shortcuts app. Siri runs them by name ("Hey Siri, Capture").

Below, `OWNER/life` stands for your data repository (mine is `mteyra/life`).

## 1. The token (once)

1. On GitHub: **Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token**.
2. **Repository access:** *Only select repositories* → your data repository, and nothing else.
3. **Permissions:**
   - *Issues: Read and write* (to capture);
   - *Contents: Read-only* (to show lists on the phone).
4. **Expiration:** the longest offered. Put a reminder in your calendar a week before it ends.
5. Copy the token. It goes into the Shortcuts below and nowhere else. Anyone holding it can only touch this one repository.

## 2. "Capture" (to the inbox)

1. New Shortcut, named **Capture**.
2. **Ask for Input:** Text, prompt "Capture what?". (Siri lets you dictate.)
3. **Get Contents of URL:**
   - URL: `https://api.github.com/repos/OWNER/life/issues`
   - Method: **POST**
   - Headers:
     - `Authorization`: `Bearer <your token>`
     - `Accept`: `application/vnd.github+json`
   - Request body: **JSON**
     - `title` (Text) → *Provided Input*
     - `labels` (Array) → one Text item: `inbox`
4. **Show Notification:** "Captured".

## 3. "Add to list" (to-do, shopping, quote)

Same as Capture, plus one step at the top:
1. **Choose from Menu** with `todo`, `shopping` and `quote`.
2. In each branch, set a **Text** action to the chosen word.
3. Use that variable as the label. Rename the prompt to "Add what?".

## 4. "Done" (tick something off)

1. **Get Contents of URL:**
   - `https://api.github.com/repos/OWNER/life/contents/lists/shopping.md`
   - Method GET
   - Headers:
     - `Authorization`: `Bearer <token>`
     - `Accept`: `application/vnd.github.raw`
2. **Split Text** by New Lines.
3. **Filter**: keep the lines that begin with `- [ ] `.
4. **Replace Text:** replace `- [ ] ` with nothing.
5. **Choose from List** (allow multiple).
6. **Repeat with Each** chosen item: **Get Contents of URL**, a POST to `…/issues` exactly as in Capture, with title = *Repeat Item* and label `done`.

For to-dos, make a copy that reads `todo.md` instead.

## 5. "Habit" (log a habit)

1. **Choose from Menu** with your habits from `habits/habits.md` (e.g. `gym`, `read`, `stretch`).
2. POST to `…/issues`:
   - title = the habit;
   - label `habit`;
   - an optional `body` with a value (e.g. `20` pages).

Add it to the Home Screen or the Action Button for one-tap logging.

## Reading lists on the phone

Any list can be shown with the GET request from "Done", steps 1 and 2: use **Quick Look** or **Show Result** on the text. The GitHub mobile app also shows the files directly.

## If something doesn't arrive

- **Check the issues tab:** an open issue with a comment means the Action couldn't file it, and the comment says why.
- **No issue at all:** the token has expired, or it's missing *Issues: Read and write*.
