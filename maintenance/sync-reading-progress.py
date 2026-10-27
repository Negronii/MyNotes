#!/usr/bin/env python3
"""Synchronize a round-specific checklist from the canonical reading maps."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PROGRESS_PATH = Path("review/reading-progress.md")
BEGIN_MARKER = "<!-- MYNOTES:READING-PROGRESS:BEGIN -->"
END_MARKER = "<!-- MYNOTES:READING-PROGRESS:END -->"
SNAPSHOT_PREFIX = "<!-- MYNOTES:READING-PROGRESS:SNAPSHOT sha256="
SNAPSHOT_RE = re.compile(r"^<!-- MYNOTES:READING-PROGRESS:SNAPSHOT sha256=([0-9a-f]{64}) -->$")
ROW_RE = re.compile(r"^- \[([ xX])\] ([1-9][0-9]*)\. \[((?:\\.|[^\]])+)\]\(([^()\s]+)\)$")


class ProgressError(Exception):
    """A safe-to-report validation error that must not modify the progress page."""


@dataclass(frozen=True)
class CanonicalEntry:
    domain: str
    title: str
    path: str
    link: str


@dataclass(frozen=True)
class ProgressRow:
    domain: str
    title: str
    path: str
    link: str
    number: int
    checked: bool


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    newline: str
    end_has_newline: bool
    inner: str


def load_reading_docs():
    """Load the canonical map parser, registering it for dataclass introspection."""
    generator_path = ROOT / "maintenance/build-reading-docs.py"
    spec = importlib.util.spec_from_file_location("mynotes_build_reading_docs", generator_path)
    if spec is None or spec.loader is None:
        raise ProgressError(f"cannot load canonical reading-map parser: {generator_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_canonical_entries(root: Path) -> tuple[object, list[CanonicalEntry]]:
    module = load_reading_docs()
    plans = [
        module.DomainPlan(name, title, root / name / "index.md")
        for name, title in module.DOMAINS.items()
    ]
    issues = []
    for plan in plans:
        module.parse_map(plan, root, issues)
    if issues:
        messages = []
        for issue in issues:
            location = module.display_path(issue.path, root)
            prefix = f"{location}:{issue.line}" if issue.line else location
            messages.append(f"{prefix}: {issue.message}")
        raise ProgressError("canonical reading maps are invalid:\n  " + "\n  ".join(messages))

    entries: list[CanonicalEntry] = []
    seen: set[str] = set()
    for plan in plans:
        for entry in plan.entries:
            try:
                relative = entry.target.resolve().relative_to(root.resolve()).as_posix()
            except ValueError as exc:
                raise ProgressError(f"map target escapes repository root: {entry.target}") from exc
            if relative in seen:
                raise ProgressError(f"canonical path appears more than once across maps: {relative}")
            seen.add(relative)
            entries.append(
                CanonicalEntry(
                    domain=plan.name,
                    title=entry.title,
                    path=relative,
                    link=canonical_link(relative),
                )
            )
    return module, entries


def canonical_link(repository_path: str) -> str:
    """Return the one accepted link from review/reading-progress.md to a note."""
    return quote("../" + repository_path, safe="/-._~")


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def unescape_label(value: str) -> str:
    return re.sub(r"\\(.)", r"\1", value)


def snapshot_digest(rows: list[ProgressRow], domains: list[str]) -> str:
    payload = {
        "domains": domains,
        "rows": [
            {"domain": row.domain, "number": row.number, "title": row.title, "path": row.path}
            for row in rows
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_domain_order(module: object) -> list[str]:
    return list(module.DOMAINS)


def canonical_domain_titles(module: object) -> dict[str, str]:
    return dict(module.DOMAINS)


def row_payload(entries: list[CanonicalEntry], checked_paths: set[str], module: object) -> list[str]:
    lines: list[str] = []
    rows: list[ProgressRow] = []
    number = 0
    titles = canonical_domain_titles(module)
    entries_by_domain = {domain: [] for domain in source_domain_order(module)}
    for entry in entries:
        entries_by_domain[entry.domain].append(entry)
    for domain in source_domain_order(module):
        lines.append(f"## {titles[domain]}")
        lines.append("")
        for entry in entries_by_domain[domain]:
            number += 1
            checked = entry.path in checked_paths
            checkbox = "x" if checked else " "
            lines.append(
                f"- [{checkbox}] {number}. [{escape_label(entry.title)}]({entry.link})"
            )
            rows.append(
                ProgressRow(
                    entry.domain,
                    entry.title,
                    entry.path,
                    entry.link,
                    number,
                    checked,
                )
            )
    digest = snapshot_digest(rows, source_domain_order(module))
    return [f"{SNAPSHOT_PREFIX}{digest} -->", *lines]


def render_region(
    entries: list[CanonicalEntry],
    checked_paths: set[str],
    newline: str,
    end_has_newline: bool,
    module: object,
) -> str:
    body = row_payload(entries, checked_paths, module)
    result = newline.join([BEGIN_MARKER, *body, END_MARKER])
    return result + (newline if end_has_newline else "")


def split_lines_with_offsets(content: str) -> list[tuple[int, int, str, str]]:
    """Return (start, end, text, ending) for each line without newline normalization."""
    lines: list[tuple[int, int, str, str]] = []
    offset = 0
    for chunk in content.splitlines(keepends=True):
        if chunk.endswith("\r\n"):
            text, ending = chunk[:-2], "\r\n"
        elif chunk.endswith("\n") or chunk.endswith("\r"):
            text, ending = chunk[:-1], chunk[-1:]
        else:
            text, ending = chunk, ""
        end = offset + len(chunk)
        lines.append((offset, end, text, ending))
        offset = end
    return lines


def locate_region(content: str) -> Region:
    lines = split_lines_with_offsets(content)
    begins = [row for row in lines if row[2] == BEGIN_MARKER]
    ends = [row for row in lines if row[2] == END_MARKER]
    if content.count(BEGIN_MARKER) != 1 or len(begins) != 1:
        raise ProgressError("progress file must contain exactly one standalone begin marker")
    if content.count(END_MARKER) != 1 or len(ends) != 1:
        raise ProgressError("progress file must contain exactly one standalone end marker")
    begin = begins[0]
    end = ends[0]
    if begin[0] >= end[0]:
        raise ProgressError("progress markers are missing, duplicated, or out of order")
    if not begin[3]:
        raise ProgressError("begin marker must be followed by a newline and managed content")
    return Region(
        start=begin[0],
        end=end[1],
        newline=begin[3],
        end_has_newline=bool(end[3]),
        inner=content[begin[1] : end[0]],
    )


def path_from_link(raw_link: str, root: Path) -> tuple[str, str]:
    parsed = urlsplit(raw_link)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ProgressError(f"progress link must be a local canonical Markdown path: {raw_link!r}")
    if raw_link.startswith(("/", "\\")) or not parsed.path:
        raise ProgressError(f"progress link must be a relative canonical Markdown path: {raw_link!r}")
    decoded = unquote(parsed.path)
    if "\\" in decoded:
        raise ProgressError(f"progress link contains a noncanonical path separator: {raw_link!r}")
    target = (root / PROGRESS_PATH.parent / decoded).resolve()
    try:
        repository_path = target.relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ProgressError(f"progress link escapes repository root: {raw_link!r}") from exc
    if not repository_path.lower().endswith(".md"):
        raise ProgressError(f"progress link must target a Markdown note: {raw_link!r}")
    if canonical_link(repository_path) != raw_link:
        raise ProgressError(f"progress link was edited or is not canonical: {raw_link!r}")
    return repository_path, canonical_link(repository_path)


def parse_region(region: Region, root: Path, module: object) -> list[ProgressRow]:
    lines = region.inner.splitlines()
    if not lines:
        raise ProgressError("managed progress block is empty")
    digest_match = SNAPSHOT_RE.fullmatch(lines[0])
    if digest_match is None:
        raise ProgressError("managed progress block has a missing or malformed snapshot line")
    expected_domains = source_domain_order(module)
    domain_titles = canonical_domain_titles(module)
    domain_by_title = {title: name for name, title in domain_titles.items()}
    current_domain: str | None = None
    domain_cursor = 0
    heading_may_have_blank = False
    rows: list[ProgressRow] = []
    paths: set[str] = set()
    expected_number = 1
    for line_number, line in enumerate(lines[1:], start=2):
        if line == "" and heading_may_have_blank:
            heading_may_have_blank = False
            continue
        if line.startswith("## "):
            title = line[3:]
            domain = domain_by_title.get(title)
            if domain is None:
                raise ProgressError(f"managed progress block has an unexpected domain heading: {line!r}")
            if domain_cursor >= len(expected_domains) or domain != expected_domains[domain_cursor]:
                raise ProgressError("managed progress domain headings must follow DOMAINS order exactly once")
            current_domain = domain
            domain_cursor += 1
            heading_may_have_blank = True
            continue
        heading_may_have_blank = False
        match = ROW_RE.fullmatch(line)
        if match is None:
            raise ProgressError(
                f"managed progress block contains free text or an invalid checkbox row at inner line {line_number}"
            )
        if current_domain is None:
            raise ProgressError("a progress checkbox appears before its domain heading")
        marker, raw_number, raw_title, raw_link = match.groups()
        number = int(raw_number)
        if number != expected_number:
            raise ProgressError(
                f"progress numbering is invalid at item {expected_number}: found {number}"
            )
        expected_number += 1
        repository_path, link = path_from_link(raw_link, root)
        if repository_path in paths:
            raise ProgressError(f"managed progress block lists a path more than once: {repository_path}")
        if not repository_path.startswith(current_domain + "/"):
            raise ProgressError(
                f"progress path {repository_path!r} is grouped under the wrong domain {current_domain!r}"
            )
        paths.add(repository_path)
        rows.append(
            ProgressRow(
                current_domain,
                unescape_label(raw_title),
                repository_path,
                link,
                number,
                marker.lower() == "x",
            )
        )
    if domain_cursor != len(expected_domains):
        raise ProgressError("managed progress block is missing one or more domain headings")
    actual_digest = snapshot_digest(rows, expected_domains)
    if actual_digest != digest_match.group(1):
        raise ProgressError(
            "managed progress rows do not match their snapshot; only checkbox states may be edited"
        )
    return rows


def validate_against_current(rows: list[ProgressRow], entries: list[CanonicalEntry], *, allow_map_updates: bool) -> None:
    current_by_path = {entry.path: entry for entry in entries}
    for row in rows:
        if row.path not in current_by_path:
            raise ProgressError(
                f"progress path is no longer in the canonical reading maps: {row.path}. "
                "Possible removal or rename; no state was discarded. Review the old path and resolve it deliberately."
            )
        entry = current_by_path[row.path]
        if row.domain != entry.domain:
            raise ProgressError(
                f"progress path moved between domains: {row.path}. Review the old and new entries deliberately."
            )
        if not allow_map_updates and row.title != entry.title:
            raise ProgressError(f"progress title differs from canonical map for {row.path}; run sync")

    if allow_map_updates:
        # The signature protects the existing rows. New canonical entries are allowed and receive unchecked state.
        return
    expected = [(entry.domain, entry.path, entry.title) for entry in entries]
    actual = [(row.domain, row.path, row.title) for row in rows]
    if actual != expected:
        raise ProgressError("progress page is out of date with the canonical maps; run sync")


def verify_rendered(content: str, root: Path, module: object, entries: list[CanonicalEntry]) -> None:
    region = locate_region(content)
    rows = parse_region(region, root, module)
    validate_against_current(rows, entries, allow_map_updates=False)


def read_text_preserving_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as source:
        return source.read()


def initial_content(entries: list[CanonicalEntry]) -> str:
    intro = (
        "# 本轮复习进度 / Reading Progress\n\n"
        "本轮已读状态由下方清单记录：未勾选表示本轮尚未读，勾选表示本轮已读。首次创建时全部未勾选。"
        "勾选不代表已经掌握，也不表示笔记是最新版本。\n\n"
        "清单顺序来自三个领域地图的 Reading order / 阅读顺序。地图新增或重排后运行同步；同步会保留已有勾选。"
        "开始新一轮前请先备份本页，再手动取消所有勾选。\n\n"
        "个人待追问内容可写在下方受管区域之外；同步会逐字保留区域外内容。\n"
        "若笔记路径被重命名或移除，请先将本页备份到仓库外，移走本页后运行同步生成新清单，再对照备份手动恢复勾选与个人笔记；不要直接修改受管区域内的路径。\n"
    )
    module = load_reading_docs()
    body = render_region(entries, set(), "\n", True, module)
    content = intro + body
    verify_rendered(content, ROOT, module, entries)
    return content


def atomic_replace(path: Path, content: str) -> None:
    original_mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temp_name)
    try:
        os.chmod(temporary, original_mode)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def sync(root: Path, module: object, entries: list[CanonicalEntry]) -> int:
    path = root / PROGRESS_PATH
    if not path.exists():
        content = initial_content(entries)
        # Validate the exact initial bytes before the first write.
        verify_rendered(content, root, module, entries)
        atomic_replace(path, content)
        print(f"Created {PROGRESS_PATH.as_posix()} with all items unchecked.")
        return 0

    try:
        original = read_text_preserving_newlines(path)
    except (OSError, UnicodeError) as exc:
        raise ProgressError(f"cannot read progress file as UTF-8: {exc}") from exc
    region = locate_region(original)
    rows = parse_region(region, root, module)
    validate_against_current(rows, entries, allow_map_updates=True)
    checked_paths = {row.path for row in rows if row.checked}
    replacement = render_region(entries, checked_paths, region.newline, region.end_has_newline, module)
    updated = original[: region.start] + replacement + original[region.end :]
    # Re-parse and compare the fully rendered output before touching the file.
    verify_rendered(updated, root, module, entries)
    if updated != original:
        atomic_replace(path, updated)
        print(f"Synchronized {PROGRESS_PATH.as_posix()} from canonical reading maps.")
    else:
        print(f"{PROGRESS_PATH.as_posix()} is already synchronized.")
    return 0


def check(root: Path, module: object, entries: list[CanonicalEntry]) -> list[ProgressRow]:
    path = root / PROGRESS_PATH
    if not path.is_file():
        raise ProgressError(f"{PROGRESS_PATH.as_posix()} is missing; run the script without --check")
    try:
        content = read_text_preserving_newlines(path)
    except (OSError, UnicodeError) as exc:
        raise ProgressError(f"cannot read progress file as UTF-8: {exc}") from exc
    region = locate_region(content)
    rows = parse_region(region, root, module)
    validate_against_current(rows, entries, allow_map_updates=False)
    return rows


def print_status(rows: list[ProgressRow], entries: list[CanonicalEntry], module: object) -> None:
    checked = {row.path for row in rows if row.checked}
    total_checked = len(checked)
    total = len(entries)
    percent = (100 * total_checked / total) if total else 0.0
    print(f"总计：{total_checked}/{total} 已读（{percent:.1f}%）")
    for domain, title in module.DOMAINS.items():
        domain_entries = [entry for entry in entries if entry.domain == domain]
        domain_checked = sum(entry.path in checked for entry in domain_entries)
        domain_total = len(domain_entries)
        domain_percent = (100 * domain_checked / domain_total) if domain_total else 0.0
        print(f"{title}：{domain_checked}/{domain_total} 已读（{domain_percent:.1f}%）")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="validate progress structure and map parity without writing")
    mode.add_argument("--status", action="store_true", help="validate first, then print current-round read counts")
    args = parser.parse_args(argv)
    try:
        module, entries = read_canonical_entries(ROOT.resolve())
        if args.check:
            check(ROOT.resolve(), module, entries)
            print("Reading progress structure, order, numbering, links, titles, and map coverage are valid.")
            return 0
        if args.status:
            rows = check(ROOT.resolve(), module, entries)
            print_status(rows, entries, module)
            return 0
        return sync(ROOT.resolve(), module, entries)
    except (ProgressError, OSError, UnicodeError) as exc:
        print(f"reading progress: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
