import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import life  # noqa: E402

WHEN = "2026-11-20T21:30:00Z"  # 22:30 in Berlin


class LifeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")

    def test_inbox_gets_local_timestamp_and_body(self):
        life.add(self.root, "call   the bank", when=WHEN, body="about the card\n\n")
        self.assertEqual(self.read("inbox.md"), "- 2026-11-20 22:30 · call the bank\n  about the card\n")

    def test_todo_and_shopping_and_quote_formats(self):
        life.add(self.root, "Update CV", to="todo", when=WHEN)
        life.add(self.root, "milk", to="shopping", when=WHEN)
        life.add(self.root, "Regret nothing.", to="quote", when=WHEN)
        self.assertEqual(self.read("todo.md"), "- [ ] Update CV added:2026-11-20\n")
        self.assertEqual(self.read("lists/shopping.md"), "- [ ] milk\n")
        self.assertEqual(self.read("quotes.md"), "- Regret nothing.\n")

    def test_done_ticks_first_match_in_todo_then_shopping(self):
        (self.root / "todo.md").write_text("# Todo\n- [x] old cv done:2026-11-01\n- [ ] Update CV PDF #homepage\n")
        (self.root / "lists").mkdir()
        (self.root / "lists/shopping.md").write_text("- [ ] Oat milk\n")
        life.done(self.root, "cv", when=WHEN)
        life.done(self.root, "OAT", when=WHEN)
        self.assertIn("- [x] Update CV PDF #homepage done:2026-11-20", self.read("todo.md"))
        self.assertEqual(self.read("lists/shopping.md"), "- [x] Oat milk\n")
        with self.assertRaises(life.LifeError):
            life.done(self.root, "nothing like this", when=WHEN)

    def test_habit_log_and_stats(self):
        for day in ("2026-11-18", "2026-11-19", "2026-11-20"):
            life.habit(self.root, "Gym", when=f"{day}T10:00:00+01:00")
        life.habit(self.root, "read", "20 pages", when="2026-11-10T10:00:00+01:00")
        self.assertTrue(self.read("habits/log.csv").startswith("date,habit,value\n2026-11-18,gym,1\n"))
        (self.root / "todo.md").write_text("- [x] a done:2026-11-19\n- [x] b done:2026-10-01\n- [ ] c\n")
        (self.root / "quotes.md").write_text("- One.\n- Two.\n")
        data = life.stats(self.root, 7, when=WHEN)
        self.assertEqual((data["todos_done"], data["todos_open"]), (1, 1))
        self.assertEqual(data["habits"]["gym"], {"days": 3, "streak": 3})
        self.assertEqual(data["habits"]["read"], {"days": 0, "streak": 0})
        self.assertIn(data["quote_of_the_day"], ("One.", "Two."))
        self.assertIn("1 tasks done", life.stats_markdown(data))

    def test_ingest_routes_by_label(self):
        life.ingest(self.root, "shopping", "eggs", when=WHEN)
        life.ingest(self.root, "habit", "gym", body="", when=WHEN)
        life.ingest(self.root, "", "an idea", body="more detail", when=WHEN)
        life.ingest(self.root, "done,shopping", "eggs", when=WHEN)
        self.assertEqual(self.read("lists/shopping.md"), "- [x] eggs\n")
        self.assertIn("2026-11-20,gym,1", self.read("habits/log.csv"))
        self.assertIn("· an idea\n  more detail", self.read("inbox.md"))

    def test_git_mode_commits_only_the_changed_file(self):
        remote = self.root / "remote.git"
        work = self.root / "work"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remote)], check=True)
        subprocess.run(["git", "clone", "-q", str(remote), str(work)], check=True, capture_output=True)
        for key, value in (("user.name", "Test"), ("user.email", "t@example.org")):
            subprocess.run(["git", "-C", str(work), "config", key, value], check=True)
        (work / "stray.txt").write_text("not mine")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(life.main(["--dir", str(work), "--git", "--when", WHEN, "add", "test", "idea"]), 0)
        log = subprocess.run(["git", "-C", str(remote), "log", "--name-only", "--format=%s"], capture_output=True, text=True).stdout
        self.assertIn("Added to inbox.md: test idea", log)
        self.assertIn("inbox.md", log)
        self.assertNotIn("stray.txt", log)

    def test_profile_snippet_replaces_only_between_markers(self):
        readme = self.root / "README.md"
        readme.write_text("Hi\n<!-- life:start -->\nold\n<!-- life:end -->\nBye\n")
        (self.root / "quotes.md").write_text("- Regret nothing.\n")
        with contextlib.redirect_stdout(io.StringIO()):
            life.main(["--dir", str(self.root), "--when", WHEN, "profile", str(readme)])
        text = readme.read_text()
        self.assertTrue(text.startswith("Hi\n<!-- life:start -->\n**This week:**"))
        self.assertIn("> Regret nothing.\n<!-- life:end -->\nBye\n", text)
        self.assertFalse(life.update_profile(readme, life.stats_markdown(life.stats(self.root, 7, WHEN))))
        readme.write_text("no markers")
        with self.assertRaises(life.LifeError):
            life.update_profile(readme, "x")

    def test_cli_stats_json(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            life.main(["--dir", str(self.root), "--when", WHEN, "stats"])
        self.assertEqual(json.loads(out.getvalue())["todos_open"], 0)


if __name__ == "__main__":
    unittest.main()
