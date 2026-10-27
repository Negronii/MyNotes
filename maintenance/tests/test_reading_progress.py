import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROGRESS_SCRIPT = ROOT / "maintenance/sync-reading-progress.py"
GENERATOR = ROOT / "maintenance/build-reading-docs.py"


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_fixture(root: Path) -> Path:
    maintenance = root / "maintenance"
    maintenance.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GENERATOR, maintenance / "build-reading-docs.py")
    progress_script = shutil.copy2(PROGRESS_SCRIPT, maintenance / "sync-reading-progress.py")
    write(
        root / "ai-engineering/index.md",
        """# AI Engineering

## Reading order / 阅读顺序
[First title](notes/first.md)
[Second title](notes/second.md)
""",
    )
    write(
        root / "frontend/index.md",
        """# Frontend

## Reading order / 阅读顺序
[Third title](javascript/third.md)
""",
    )
    write(
        root / "engineering-foundations/index.md",
        """# Engineering Foundations

## Reading order / 阅读顺序
[Fourth title](networking/fourth.md)
""",
    )
    write(root / "ai-engineering/notes/first.md", "# First title\n")
    write(root / "ai-engineering/notes/second.md", "# Second title\n")
    write(root / "frontend/javascript/third.md", "# Third title\n")
    write(root / "engineering-foundations/networking/fourth.md", "# Fourth title\n")
    (root / "review").mkdir(parents=True, exist_ok=True)
    return progress_script


class ReadingProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.root = base / "vault"
        self.script = make_fixture(self.root)
        self.outside = base / "outside"
        self.outside.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    @property
    def progress(self) -> Path:
        return self.root / "review/reading-progress.md"

    def run_script(self, *args):
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.outside,
            text=True,
            capture_output=True,
        )

    def create_progress(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        return self.progress.read_text(encoding="utf-8")

    def test_sync_preserves_checked_paths_adds_unchecked_and_reorders_from_maps(self):
        content = self.create_progress()
        self.assertEqual(content.count("- [ ]"), 4)
        self.progress.write_text(content.replace("- [ ] 1.", "- [x] 1.", 1), encoding="utf-8")

        write(self.root / "ai-engineering/notes/new.md", "# New\n")
        write(
            self.root / "ai-engineering/index.md",
            """# AI Engineering

## Reading order / 阅读顺序
[Second title](notes/second.md)
[First title](notes/first.md)
[New title](notes/new.md)
""",
        )
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.progress.read_text(encoding="utf-8")
        self.assertIn("- [ ] 1. [Second title](../ai-engineering/notes/second.md)", content)
        self.assertIn("- [x] 2. [First title](../ai-engineering/notes/first.md)", content)
        self.assertIn("- [ ] 3. [New title](../ai-engineering/notes/new.md)", content)
        self.assertEqual(content.count("- [ ]"), 4)
        self.assertEqual(self.run_script("--check").returncode, 0)

    def test_sync_preserves_personal_text_outside_managed_region_verbatim(self):
        self.create_progress()
        personal_text = "\n## Personal follow-up\n- Revisit the retry boundary example.\n"
        with self.progress.open("a", encoding="utf-8", newline="") as output:
            output.write(personal_text)
        write(self.root / "frontend/javascript/new.md", "# New frontend note\n")
        write(
            self.root / "frontend/index.md",
            """# Frontend

## Reading order / 阅读顺序
[Third title](javascript/third.md)
[New frontend note](javascript/new.md)
""",
        )
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.progress.read_text(encoding="utf-8")
        self.assertTrue(content.endswith(personal_text))
        self.assertIn("- [ ] 4. [New frontend note](../frontend/javascript/new.md)", content)

    def test_sync_is_idempotent(self):
        self.create_progress()
        before = self.progress.stat()
        second = self.run_script()
        after = self.progress.stat()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("already synchronized", second.stdout)
        self.assertEqual(before.st_ino, after.st_ino)

    def test_check_and_status_accept_valid_manual_checkboxes(self):
        content = self.create_progress()
        self.progress.write_text(content.replace("- [ ] 1.", "- [x] 1.", 1), encoding="utf-8")
        check = self.run_script("--check")
        self.assertEqual(check.returncode, 0, check.stderr)
        status = self.run_script("--status")
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertIn("总计：1/4 已读（25.0%）", status.stdout)
        self.assertIn("AI Engineering：1/2 已读（50.0%）", status.stdout)
        self.assertIn("Frontend：0/1 已读（0.0%）", status.stdout)
        self.assertIn("Engineering Foundations：0/1 已读（0.0%）", status.stdout)

    def test_duplicate_path_and_bad_link_fail_without_writing(self):
        self.create_progress()
        original = self.progress.read_bytes()
        duplicate = original.replace(
            b"../ai-engineering/notes/second.md", b"../ai-engineering/notes/first.md"
        )
        self.progress.write_bytes(duplicate)
        before = self.progress.read_bytes()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("more than once", result.stderr)
        self.assertEqual(self.progress.read_bytes(), before)

        self.progress.write_bytes(original)
        bad_link = original.replace(b"../ai-engineering/notes/first.md", b"../ai-engineering/notes/missing.md")
        self.progress.write_bytes(bad_link)
        before = self.progress.read_bytes()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("snapshot", result.stderr)
        self.assertEqual(self.progress.read_bytes(), before)

    def test_removed_or_renamed_path_is_reported_without_dropping_state(self):
        self.create_progress()
        original = self.progress.read_bytes()
        old_note = self.root / "ai-engineering/notes/first.md"
        new_note = self.root / "ai-engineering/notes/renamed.md"
        old_note.rename(new_note)
        write(
            self.root / "ai-engineering/index.md",
            """# AI Engineering

## Reading order / 阅读顺序
[Renamed title](notes/renamed.md)
[Second title](notes/second.md)
""",
        )
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Possible removal or rename", result.stderr)
        self.assertEqual(self.progress.read_bytes(), original)

    def test_markers_free_text_and_illegal_checkbox_are_rejected_without_writes(self):
        valid = self.create_progress()
        mutations = [
            (valid.replace("<!-- MYNOTES:READING-PROGRESS:BEGIN -->\n", "", 1), "begin marker"),
            (
                valid.replace("<!-- MYNOTES:READING-PROGRESS:END -->", "<!-- MYNOTES:READING-PROGRESS:END -->\n<!-- MYNOTES:READING-PROGRESS:END -->", 1),
                "exactly one",
            ),
            (valid.replace("## AI Engineering\n", "free text\n## AI Engineering\n", 1), "free text"),
            (valid.replace("- [ ] 1.", "- [?] 1.", 1), "invalid checkbox row"),
        ]
        for mutated, message in mutations:
            with self.subTest(message=message):
                self.progress.write_text(mutated, encoding="utf-8")
                before = self.progress.read_bytes()
                result = self.run_script()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.progress.read_bytes(), before)

    def test_numbering_or_link_edit_is_rejected_without_writes(self):
        valid = self.create_progress()
        for mutated in (
            valid.replace("- [ ] 2.", "- [ ] 9.", 1),
            valid.replace("../ai-engineering/notes/first.md", "../ai-engineering/notes/second.md", 1),
        ):
            with self.subTest(mutated=mutated[-100:]):
                self.progress.write_text(mutated, encoding="utf-8")
                before = self.progress.read_bytes()
                result = self.run_script()
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(
                    "numbering is invalid" in result.stderr or "more than once" in result.stderr,
                    result.stderr,
                )
                self.assertEqual(self.progress.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
