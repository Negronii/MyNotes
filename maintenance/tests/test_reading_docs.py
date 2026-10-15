import hashlib
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


GENERATOR = Path(__file__).resolve().parents[1] / "build-reading-docs.py"
FENCE = chr(96) * 3


def write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def make_fixture(root: Path) -> Path:
    write(root / "maintenance/build-reading-docs.py", GENERATOR.read_text(encoding="utf-8"))
    write(
        root / "ai-engineering/index.md",
        """# AI Engineering

## Navigation
[Archive](../archive/old.md)

## Reading order / 阅读顺序
### Fundamentals
[Agent 基础 / Agent Fundamentals](AIagents/agent-fundamentals.md)
[空格路径 / Space Note](nested/notes%20with%20space.md)
""",
    )
    write(
        root / "frontend/index.md",
        """# Frontend

## Reading order / 阅读顺序
[Scope / 闭包](javascript/scope-and-closure.md)
""",
    )
    write(
        root / "engineering-foundations/index.md",
        """# Foundations

## Reading order / 阅读顺序
[HTTP / WebSockets](networking/http.md)
""",
    )
    body = (
        "# 可重复标题\n"
        "## 可重复标题\n"
        "### Title With /? Punctuation\n"
        "JavaScript internal slot syntax: `[[Prototype]]`.\n"
        'HTML example inline: `<meta name="viewport">` and literal <meta name="viewport">.\n'
        "\n"
        "[Named anchor](#legacy-target)\n"
        '<a name="legacy-target"></a>\n'
        "[Self article](agent-fundamentals.md)\n"
        "[Punctuation heading](#title-with--punctuation)\n"
        "[Peer note](../nested/notes%20with%20space.md#空间标题)\n"
        "[Peer chapter](../nested/notes%20with%20space.md)\n"
        "[Cross domain](../../frontend/javascript/scope-and-closure.md#scope-and-closure)\n"
        "[Archive](../archives/legacy.md#archive-heading)\n"
        "![Diagram](../assets/diagram%20one.png)\n"
        "[External](https://example.test/path#keep)\n"
        "Inline code: " + chr(96) + "[leave](missing-inline.md)" + chr(96) + "\n"
        + FENCE
        + "md\n[leave](missing-fenced.md)\n# leave this heading level alone\n"
        + FENCE
        + "\n"
    )
    write(root / "ai-engineering/AIagents/agent-fundamentals.md", body)
    write(
        root / "ai-engineering/nested/notes with space.md",
        "# 空间标题\n# A\n# A\n# A-1\n"
        "[A minus one](#a-1-1)\nBody\n",
    )
    write(root / "frontend/javascript/scope-and-closure.md", "# Scope and Closure\n## Scope\n")
    write(root / "engineering-foundations/networking/http.md", "# HTTP Protocol\n")
    write(root / "ai-engineering/archives/legacy.md", "# Archive Heading\n")
    write(root / "ai-engineering/assets/diagram one.png", "fixture image")
    return root / "maintenance/build-reading-docs.py"


class ReadingDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "vault"
        self.script = make_fixture(self.root)
        self.outside = Path(self.temp.name) / "elsewhere"
        self.outside.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def run_generator(self, *args):
        return subprocess.run(
            [sys.executable, str(self.script), *args],
            cwd=self.outside,
            text=True,
            capture_output=True,
        )

    def test_generates_deterministically_and_rewrites_supported_links(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)
        generated = self.root / "review/generated/ai-engineering.md"
        content = generated.read_text(encoding="utf-8")
        self.assertIn("## 1. Agent 基础 / Agent Fundamentals", content)
        self.assertIn(
            "[Self article](#1.%20Agent%20%E5%9F%BA%E7%A1%80%20/%20Agent%20Fundamentals)",
            content,
        )
        self.assertIn("[Punctuation heading](#Title%20With%20/?%20Punctuation)", content)
        self.assertIn("[Peer note](#%E7%A9%BA%E9%97%B4%E6%A0%87%E9%A2%98)", content)
        self.assertIn(
            "[Peer chapter](#2.%20%E7%A9%BA%E6%A0%BC%E8%B7%AF%E5%BE%84%20/%20Space%20Note)",
            content,
        )
        self.assertIn(
            "[Cross domain](../../frontend/javascript/scope-and-closure.md#scope-and-closure)",
            content,
        )
        self.assertIn(
            "[Archive](../../ai-engineering/archives/legacy.md#archive-heading)", content
        )
        self.assertIn("../../ai-engineering/assets/diagram%20one.png", content)
        self.assertIn("[External](https://example.test/path#keep)", content)
        tick = chr(96)
        self.assertIn(tick + "[leave](missing-inline.md)" + tick, content)
        code = FENCE + "md\n[leave](missing-fenced.md)\n# leave this heading level alone\n" + FENCE
        self.assertIn(code, content)
        self.assertIn("### 可重复标题", content)
        self.assertIn("#### 可重复标题", content)
        self.assertIn("[A minus one](#A-1)", content)
        self.assertIn("JavaScript internal slot syntax: `[[Prototype]]`.", content)
        self.assertIn(
            'HTML example inline: `<meta name="viewport">` and literal <meta name="viewport">.',
            content,
        )
        self.assertRegex(content, r"\[Named anchor\]\(#note-[0-9a-f]{12}-a1\)")
        self.assertRegex(content, r'<a name="note-[0-9a-f]{12}-a1"></a>')
        expected = {
            path.relative_to(self.root): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (self.root / "review/generated").glob("*.md")
        }
        second = self.run_generator()
        self.assertEqual(second.returncode, 0, second.stderr)
        actual = {
            path.relative_to(self.root): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (self.root / "review/generated").glob("*.md")
        }
        self.assertEqual(expected, actual)
        check = self.run_generator("--check")
        self.assertEqual(check.returncode, 0, check.stderr)

        generated.write_text(content + "\n[broken](#no-such-heading)\n", encoding="utf-8")
        broken = generated.read_bytes()
        check = self.run_generator("--check")
        self.assertNotEqual(check.returncode, 0)
        self.assertIn("generated link fragment does not exist", check.stderr)
        self.assertIn("stale", check.stderr)
        self.assertEqual(generated.read_bytes(), broken, "--check must not write")

    def test_check_rejects_gfm_or_mismatched_native_fragments(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)
        generated = self.root / "review/generated/ai-engineering.md"
        content = generated.read_text(encoding="utf-8")
        broken = content + (
            "\n[Old GFM fragment](#title-with--punctuation)\n"
            "[Encoded slash](#Title%20With%20%2F?%20Punctuation)\n"
            "[Encoded question](#Title%20With%20/%3F%20Punctuation)\n"
        )
        generated.write_text(broken, encoding="utf-8")

        check = self.run_generator("--check")
        self.assertNotEqual(check.returncode, 0)
        self.assertGreaterEqual(check.stderr.count("generated link fragment does not exist"), 3)
        self.assertIn("stale", check.stderr)

    def test_only_referenced_duplicate_native_headings_are_rejected(self):
        first = self.run_generator()
        self.assertEqual(first.returncode, 0, first.stderr)

        source = self.root / "ai-engineering/nested/notes with space.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "[Ambiguous A](#a-1)\n",
            encoding="utf-8",
        )
        second = self.run_generator()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("ambiguous native heading target 'A'", second.stderr)
        self.assertNotIn("fragment #a-1 does not exist", second.stderr)

    def test_reports_missing_duplicate_and_nonexistent_map_entries(self):
        index = self.root / "ai-engineering/index.md"
        index.write_text(
            """# AI Engineering

## Reading order / 阅读顺序
[First](AIagents/agent-fundamentals.md)
[Duplicate](AIagents/agent-fundamentals.md)
[Missing target](Nope.md)
""",
            encoding="utf-8",
        )
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("listed more than once", result.stderr)
        self.assertIn("map target does not exist", result.stderr)
        self.assertIn("missing from ai-engineering/index.md", result.stderr)
        self.assertFalse((self.root / "review/generated").exists())

    def test_reports_unresolved_source_fragment(self):
        source = self.root / "frontend/javascript/scope-and-closure.md"
        source.write_text("# Scope and Closure\n[Missing](#not-a-section)\n", encoding="utf-8")
        result = self.run_generator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fragment #not-a-section does not exist", result.stderr)
        self.assertFalse((self.root / "review/generated").exists())


if __name__ == "__main__":
    unittest.main()
