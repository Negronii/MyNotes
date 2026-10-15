#!/usr/bin/env python3
"""Build the curated reading documents from the three domain reading maps."""

from __future__ import annotations

import argparse
import hashlib
import html
import posixpath
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = Path("review/generated")
DOMAINS = {
    "ai-engineering": "AI Engineering",
    "frontend": "Frontend",
    "engineering-foundations": "Engineering Foundations",
}
FENCE_CHAR = chr(96)
ATX_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)(.*?)(?:[ \t]+#+[ \t]*)?$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
MAP_ENTRY = re.compile(r"^\s*(?:(?:[-*+]\s+)|(?:\d+[.)]\s+))?\[([^\]]+)\]\((.*)\)\s*$")
HTML_TAG = re.compile(r"<[A-Za-z][^>]*>")
HTML_ATTR = re.compile(
    r"""(?i)\b(id|name|href|src)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))"""
)
REFERENCE_DEF = re.compile(r"^( {0,3}\[(?!\^)[^\]]+\]:[ \t]*)(<[^>]*>|[^\s]+)(.*)$")
WIKILINK = re.compile(r"!?(\[\[[^\]\n]+\]\])")
NATIVE_URI_RESERVED = ";,/?:@&=+$#"


@dataclass
class Issue:
    path: Path
    line: int
    message: str


@dataclass
class Heading:
    line_index: int
    underline_index: int | None
    level: int
    title: str
    slug: str
    output_native_title: str = ""


@dataclass
class ExplicitAnchor:
    line_index: int
    start: int
    end: int
    value: str
    output_id: str


@dataclass
class MapEntry:
    title: str
    target: Path
    line: int


@dataclass
class DomainPlan:
    name: str
    title: str
    map_path: Path
    entries: list[MapEntry] = field(default_factory=list)
    notes: list["SourceNote"] = field(default_factory=list)


@dataclass
class SourceNote:
    domain: str
    source_path: Path
    title: str
    content: str
    section_native_title: str = ""
    native_heading_counts: dict[str, int] = field(default_factory=dict)
    internal_prefix: str = ""
    lines: list[str] = field(default_factory=list)
    fenced: list[bool] = field(default_factory=list)
    headings: list[Heading] = field(default_factory=list)
    explicit_anchors: list[ExplicitAnchor] = field(default_factory=list)
    fragments: dict[str, str] = field(default_factory=dict)
    heading_by_line: dict[int, Heading] = field(default_factory=dict)
    underline_by_line: dict[int, Heading] = field(default_factory=dict)
    anchors_by_line: dict[int, list[ExplicitAnchor]] = field(default_factory=dict)


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def add_issue(issues: list[Issue], path: Path, line: int, message: str) -> None:
    issues.append(Issue(path, line, message))


def split_lines(content: str) -> list[str]:
    return content.splitlines(keepends=True)


def without_line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return line[:-2]
    if line.endswith("\n") or line.endswith("\r"):
        return line[:-1]
    return line


def line_ending(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    if line.endswith("\r"):
        return "\r"
    return "\n"


def fence_open(line: str) -> tuple[str, int] | None:
    plain = without_line_ending(line)
    spaces = len(plain) - len(plain.lstrip(" "))
    if spaces > 3:
        return None
    rest = plain[spaces:]
    if not rest or rest[0] not in (FENCE_CHAR, "~"):
        return None
    char = rest[0]
    count = len(rest) - len(rest.lstrip(char))
    return (char, count) if count >= 3 else None


def fence_close(line: str, marker: tuple[str, int]) -> bool:
    plain = without_line_ending(line)
    spaces = len(plain) - len(plain.lstrip(" "))
    if spaces > 3:
        return False
    rest = plain[spaces:]
    char, minimum = marker
    count = len(rest) - len(rest.lstrip(char))
    return count >= minimum and not rest[count:].strip()


def fenced_lines(lines: list[str]) -> list[bool]:
    result: list[bool] = []
    marker: tuple[str, int] | None = None
    for line in lines:
        if marker is None:
            opening = fence_open(line)
            result.append(opening is not None)
            if opening is not None:
                marker = opening
        else:
            result.append(True)
            if fence_close(line, marker):
                marker = None
    return result


def heading_title(markdown: str) -> str:
    text = html.unescape(markdown.strip())
    text = re.sub(r"!\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    tick = re.escape(FENCE_CHAR)
    text = re.sub(tick + r"([^" + tick + r"]*)" + tick, r"\1", text)
    text = re.sub(r"<[^>]*>", "", text)
    text = re.sub(r"(\*\*|__|~~)(\S.*?\S)\1", r"\2", text)
    text = re.sub(r"(?<!\w)([*_~])(\S.*?\S)\1(?!\w)", r"\2", text)
    return text.strip()


def native_title(markdown: str) -> str:
    """Return the plain heading text used by the tested Obsidian link policy."""
    return heading_title(markdown)


def encode_native_fragment(title: str) -> str:
    return quote(title, safe="-._~;/?:@&=+$,")


def decode_native_fragment(fragment: str) -> str:
    """Decode URI text while retaining percent escapes for reserved characters."""

    def preserve_reserved(match: re.Match[str]) -> str:
        if chr(int(match.group(1), 16)) in NATIVE_URI_RESERVED:
            return "%25" + match.group(1)
        return match.group(0)

    preserved = re.sub(r"%([0-9A-Fa-f]{2})", preserve_reserved, fragment)
    return unquote(preserved)


def github_slug(value: str) -> str:
    text = heading_title(value).lower()
    result: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if char == " ":
            result.append("-")
        elif char.isspace():
            continue
        elif char in "-_":
            result.append(char)
        elif category.startswith("P") or category.startswith("S"):
            continue
        else:
            result.append(char)
    slug = "".join(result)
    return slug or "section"


def allocate_slug(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 1
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def normalized_fragment(value: str) -> str:
    return github_slug(unquote(value).lstrip("#"))


def heading_records(lines: list[str], fenced: list[bool]) -> list[tuple[int, int | None, int, str]]:
    records: list[tuple[int, int | None, int, str]] = []
    index = 0
    while index < len(lines):
        if fenced[index]:
            index += 1
            continue
        plain = without_line_ending(lines[index])
        atx = ATX_HEADING.match(plain)
        if atx:
            records.append((index, None, len(atx.group(1)), atx.group(2).strip()))
            index += 1
            continue
        if index + 1 < len(lines) and not fenced[index + 1]:
            underline = SETEXT_UNDERLINE.match(without_line_ending(lines[index + 1]))
            if underline and plain.strip():
                level = 1 if underline.group(1).startswith("=") else 2
                records.append((index, index + 1, level, plain.strip()))
                index += 2
                continue
        index += 1
    return records


def html_attributes(line: str) -> list[tuple[str, int, int, str]]:
    found: list[tuple[str, int, int, str]] = []
    for tag in HTML_TAG.finditer(line):
        for attr in HTML_ATTR.finditer(tag.group(0)):
            name = attr.group(1).lower()
            if attr.group(2) is not None:
                value, start, end = attr.group(2), attr.start(2), attr.end(2)
            elif attr.group(3) is not None:
                value, start, end = attr.group(3), attr.start(3), attr.end(3)
            else:
                value, start, end = attr.group(4), attr.start(4), attr.end(4)
            found.append((name, tag.start() + start, tag.start() + end, value))
    return found


def html_anchor_attributes(line: str) -> list[tuple[str, int, int, str]]:
    found: list[tuple[str, int, int, str]] = []
    searchable = mask_inline_code(line)
    for tag in HTML_TAG.finditer(searchable):
        tag_name = re.match(r"<([A-Za-z][A-Za-z0-9:_-]*)\b", tag.group(0))
        if not tag_name:
            continue
        is_anchor = tag_name.group(1).lower() == "a"
        for name, start, end, value in html_attributes(tag.group(0)):
            if name == "id" or (name == "name" and is_anchor):
                found.append((name, tag.start() + start, tag.start() + end, value))
    return found


def source_anchor_names(content: str) -> set[str]:
    lines = split_lines(content)
    fenced = fenced_lines(lines)
    names: set[str] = set()
    for index, line in enumerate(lines):
        if fenced[index]:
            continue
        for _, _, _, value in html_anchor_attributes(without_line_ending(line)):
            names.add(normalized_fragment(value))
    used_slugs = set(names)
    for _, _, _, title in heading_records(lines, fenced):
        slug = allocate_slug(github_slug(title), used_slugs)
        names.add(normalized_fragment(slug))
    return names


def make_note(
    domain: str,
    source_path: Path,
    title: str,
    root: Path,
    issues: list[Issue],
) -> SourceNote | None:
    try:
        content = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        add_issue(issues, source_path, 0, f"cannot read UTF-8 Markdown: {exc}")
        return None
    note = SourceNote(domain, source_path.resolve(), title, content)
    note.lines = split_lines(content)
    note.fenced = fenced_lines(note.lines)
    relative = note.source_path.relative_to(root.resolve()).as_posix()
    digest = hashlib.sha256((domain + ":" + relative).encode("utf-8")).hexdigest()[:12]
    temporary_prefix = "note-" + digest
    note.internal_prefix = temporary_prefix

    used_slugs: set[str] = set()
    provisional: dict[str, str] = {}

    def register_fragment(value: str, output: str, line: int) -> None:
        key = normalized_fragment(value)
        if key in provisional and provisional[key] != output:
            add_issue(
                issues,
                source_path,
                line,
                f"ambiguous duplicate source anchor {value!r}; rename one heading or explicit HTML id",
            )
        else:
            provisional[key] = output

    for index, underline, level, title_text in heading_records(note.lines, note.fenced):
        source_slug = allocate_slug(github_slug(title_text), used_slugs)
        heading = Heading(index, underline, level, title_text, source_slug)
        note.headings.append(heading)
        register_fragment(source_slug, f"{temporary_prefix}-h{len(note.headings)}", index + 1)

    seen_explicit: set[str] = set()
    for index, line in enumerate(note.lines):
        if note.fenced[index]:
            continue
        for name, start, end, value in html_anchor_attributes(without_line_ending(line)):
            key = normalized_fragment(value)
            if key in seen_explicit:
                add_issue(issues, source_path, index + 1, f"duplicate explicit HTML anchor {value!r}")
            seen_explicit.add(key)
            output_id = f"{temporary_prefix}-a{len(note.explicit_anchors) + 1}"
            anchor = ExplicitAnchor(index, start, end, value, output_id)
            note.explicit_anchors.append(anchor)
            note.anchors_by_line.setdefault(index, []).append(anchor)
            register_fragment(value, output_id, index + 1)

    note.heading_by_line = {heading.line_index: heading for heading in note.headings}
    note.underline_by_line = {
        heading.underline_index: heading
        for heading in note.headings
        if heading.underline_index is not None
    }
    note.fragments = provisional
    return note


def assign_native_targets(plan: DomainPlan) -> None:
    plan_title = native_title(plan.title)
    heading_counts: dict[str, int] = {plan_title: 1}
    for index, note in enumerate(plan.notes, start=1):
        note.title = f"{index}. {note.title}"
        note.section_native_title = native_title(note.title)
        heading_counts[note.section_native_title] = heading_counts.get(note.section_native_title, 0) + 1
        for heading in note.headings:
            heading.output_native_title = native_title(heading.title)
            heading_counts[heading.output_native_title] = (
                heading_counts.get(heading.output_native_title, 0) + 1
            )
        for anchor in note.explicit_anchors:
            heading_counts[anchor.output_id] = heading_counts.get(anchor.output_id, 0) + 1
    for note in plan.notes:
        note.native_heading_counts = heading_counts


def parse_map(plan: DomainPlan, root: Path, issues: list[Issue]) -> None:
    if not plan.map_path.is_file():
        add_issue(issues, plan.map_path, 0, "required reading map is missing")
        return
    try:
        content = plan.map_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        add_issue(issues, plan.map_path, 0, f"cannot read UTF-8 Markdown: {exc}")
        return
    lines = split_lines(content)
    fenced = fenced_lines(lines)
    h2: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if fenced[index]:
            continue
        match = ATX_HEADING.match(without_line_ending(line))
        if match and len(match.group(1)) == 2:
            h2.append((index, match.group(2).strip()))
    matching = [row for row in h2 if row[1] == "Reading order / 阅读顺序"]
    if len(matching) != 1:
        add_issue(issues, plan.map_path, 0, "expected exactly one H2 titled 'Reading order / 阅读顺序'")
        return

    start = matching[0][0] + 1
    end = next((index for index, _ in h2 if index > matching[0][0]), len(lines))
    seen: dict[Path, int] = {}
    domain_root = plan.map_path.parent.resolve()
    for index in range(start, end):
        if fenced[index]:
            continue
        plain = without_line_ending(lines[index]).strip()
        if not plain:
            continue
        group = ATX_HEADING.match(plain)
        if group and len(group.group(1)) == 3 and group.group(2).strip():
            continue
        match = MAP_ENTRY.fullmatch(without_line_ending(lines[index]))
        if not match:
            add_issue(
                issues,
                plan.map_path,
                index + 1,
                "each nonblank reading-order line must be one complete Markdown article link; H3 headings may group entries",
            )
            continue
        title = match.group(1).strip()
        raw_target = match.group(2).strip()
        if raw_target.startswith("<") and raw_target.endswith(">"):
            raw_target = raw_target[1:-1]
        parsed = urlsplit(raw_target)
        if parsed.scheme or parsed.netloc or raw_target.startswith(("/", "\\")):
            add_issue(issues, plan.map_path, index + 1, "map targets must be relative paths")
            continue
        if parsed.query or parsed.fragment:
            add_issue(issues, plan.map_path, index + 1, "map targets must be .md paths without query or fragment")
            continue
        if not unquote(parsed.path).lower().endswith(".md"):
            add_issue(issues, plan.map_path, index + 1, "map target must end in .md")
            continue
        target = (domain_root / unquote(parsed.path)).resolve()
        try:
            relative_target = target.relative_to(domain_root)
        except ValueError:
            add_issue(issues, plan.map_path, index + 1, f"map target escapes this domain: {raw_target!r}")
            continue
        if excluded_source(relative_target):
            add_issue(
                issues,
                plan.map_path,
                index + 1,
                f"archives and skill metadata cannot be reading-order entries: {raw_target!r}",
            )
            continue
        if target in seen:
            add_issue(
                issues,
                plan.map_path,
                index + 1,
                f"article is listed more than once (first listed on line {seen[target]}): {raw_target!r}",
            )
            continue
        seen[target] = index + 1
        if not target.is_file():
            add_issue(issues, plan.map_path, index + 1, f"map target does not exist: {raw_target!r}")
            continue
        plan.entries.append(MapEntry(title, target, index + 1))

    source_files = {
        path.resolve()
        for path in plan.map_path.parent.rglob("*.md")
        if path.resolve() != plan.map_path.resolve() and path.is_file()
        and not excluded_source(path.relative_to(plan.map_path.parent))
    }
    mapped_files = {entry.target for entry in plan.entries}
    for missing in sorted(source_files - mapped_files, key=lambda item: item.as_posix().casefold()):
        add_issue(
            issues,
            missing,
            0,
            f"source Markdown is missing from {display_path(plan.map_path, root)}",
        )


def excluded_source(relative_path: Path) -> bool:
    parts = {part.casefold().replace("_", "-") for part in relative_path.parts}
    directories = {
        "archive",
        "archives",
        "skill",
        "skills",
        "source-snapshot",
        "source-snapshots",
    }
    return bool(parts & directories) or relative_path.name.casefold() == "skill.md"


def unescape_destination(value: str) -> str:
    return re.sub(r"\\([\\ ()])", r"\1", value)


def external_destination(value: str) -> bool:
    parsed = urlsplit(value)
    return bool(parsed.scheme or parsed.netloc)


def destination_parts(raw: str) -> tuple[str, str, str, bool]:
    value = raw.strip()
    angle = value.startswith("<") and ">" in value
    if angle:
        end = value.find(">")
        destination = value[1:end]
        tail = value[end + 1 :].strip()
        if tail and not (
            (tail.startswith('"') and tail.endswith('"'))
            or (tail.startswith("'") and tail.endswith("'"))
            or (tail.startswith("(") and tail.endswith(")"))
        ):
            raise ValueError("unsupported Markdown link title syntax")
    else:
        destination = value
        if value:
            title_match = re.match(r"^(.*?)[ \t]+(?:\".*\"|'.*'|\(.*\))$", value)
            if title_match:
                destination = title_match.group(1)
    destination = unescape_destination(destination)
    parsed = urlsplit(destination)
    return parsed.path, parsed.query, parsed.fragment, angle


def format_destination(value: str, angle: bool = False) -> str:
    if angle or any(char.isspace() for char in value):
        return "<" + value.replace(">", "%3E") + ">"
    return value


def relative_url(target: Path, start: Path) -> str:
    relative = posixpath.relpath(target.resolve().as_posix(), start.resolve().as_posix())
    return quote(relative, safe="/-._~")


def locate_destination(
    source: Path,
    raw_path: str,
    root: Path,
    issues: list[Issue],
    line: int,
    label: str,
) -> Path | None:
    if not raw_path:
        return source.resolve()
    if raw_path.startswith(("/", "\\")):
        add_issue(issues, source, line, f"absolute local link is unsupported: {label!r}")
        return None
    target = (source.parent / unquote(raw_path)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        add_issue(issues, source, line, f"local link escapes the workspace: {label!r}")
        return None
    if not target.exists():
        add_issue(issues, source, line, f"linked local file does not exist: {label!r}")
        return None
    return target


def make_rewriter(
    source: Path,
    output: Path,
    current_note: SourceNote | None,
    notes_by_path: dict[Path, SourceNote],
    root: Path,
    issues: list[Issue],
):
    def rewrite(raw: str, is_image: bool, line: int) -> str:
        if external_destination(raw.strip()):
            return raw
        try:
            raw_path, query, fragment, angle = destination_parts(raw)
        except ValueError as exc:
            add_issue(issues, source, line, f"unsupported Markdown link {raw!r}: {exc}")
            return raw
        target = locate_destination(source, raw_path, root, issues, line, raw)
        if target is None:
            return raw
        if is_image:
            suffix = ("?" + query) if query else ""
            if fragment:
                suffix += "#" + quote(fragment, safe="-._~")
            return format_destination(relative_url(target, output.parent) + suffix, angle)
        if target.suffix.lower() == ".md":
            if query:
                add_issue(issues, source, line, f"query strings on local Markdown links are unsupported: {raw!r}")
                return raw
            target_note = notes_by_path.get(target)
            anchor_target = None
            if fragment:
                if target_note:
                    anchor_target = target_note.fragments.get(normalized_fragment(fragment))
                else:
                    try:
                        anchor_names = source_anchor_names(target.read_text(encoding="utf-8"))
                    except (OSError, UnicodeError) as exc:
                        add_issue(issues, source, line, f"cannot inspect linked Markdown target: {exc}")
                        return raw
                    if normalized_fragment(fragment) not in anchor_names:
                        anchor_target = None
                    else:
                        anchor_target = fragment
                if anchor_target is None:
                    add_issue(
                        issues,
                        source,
                        line,
                        f"fragment #{fragment} does not exist in {display_path(target, root)}",
                    )
                    return raw
                if (
                    target_note
                    and current_note is not None
                    and target_note.domain == current_note.domain
                    and target_note.native_heading_counts.get(anchor_target, 0) > 1
                ):
                    add_issue(
                        issues,
                        source,
                        line,
                        f"ambiguous native heading target {anchor_target!r}; duplicate generated headings cannot be distinguished",
                    )
                    return raw
            if current_note is not None and target_note and target_note.domain == current_note.domain:
                target_title = anchor_target or target_note.section_native_title
                if not fragment and target_note.native_heading_counts.get(target_title, 0) > 1:
                    add_issue(
                        issues,
                        source,
                        line,
                        f"ambiguous native heading target {target_title!r}; duplicate generated headings cannot be distinguished",
                    )
                    return raw
                return "#" + encode_native_fragment(target_title)
            suffix = ("#" + quote(fragment, safe="-._~!$&'()*+,;=:@/")) if fragment else ""
            return format_destination(relative_url(target, output.parent) + suffix, angle)
        suffix = ("?" + query) if query else ""
        if fragment:
            suffix += "#" + quote(fragment, safe="-._~!$&'()*+,;=:@/")
        return format_destination(relative_url(target, output.parent) + suffix, angle)

    return rewrite


def find_closing(text: str, start: int, opener: str, closer: str) -> int | None:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def inline_code_end(text: str, start: int) -> int | None:
    count = 1
    while start + count < len(text) and text[start + count] == FENCE_CHAR:
        count += 1
    delimiter = FENCE_CHAR * count
    end = text.find(delimiter, start + count)
    return end + count if end >= 0 else None


def mask_inline_code(text: str) -> str:
    masked = list(text)
    cursor = 0
    while cursor < len(text):
        if text[cursor] == FENCE_CHAR:
            end = inline_code_end(text, cursor)
            if end is not None:
                masked[cursor:end] = " " * (end - cursor)
                cursor = end
                continue
        cursor += 1
    return "".join(masked)


def rewrite_markdown_links(
    line_text: str,
    line_no: int,
    rewrite,
    issues: list[Issue],
    source: Path,
) -> str:
    definition = REFERENCE_DEF.match(line_text)
    if definition:
        raw = definition.group(2)
        angle = raw.startswith("<") and raw.endswith(">")
        destination = raw[1:-1] if angle else raw
        new_destination = rewrite(destination, False, line_no)
        return definition.group(1) + format_destination(new_destination, angle) + definition.group(3)

    out: list[str] = []
    cursor = 0
    while cursor < len(line_text):
        if line_text[cursor] == FENCE_CHAR:
            end = inline_code_end(line_text, cursor)
            if end is not None:
                out.append(line_text[cursor:end])
                cursor = end
                continue
        image = line_text[cursor] == "!" and cursor + 1 < len(line_text) and line_text[cursor + 1] == "["
        bracket = cursor + 1 if image else cursor
        if line_text[bracket] == "[" and not (bracket > 0 and line_text[bracket - 1] == "\\"):
            close = find_closing(line_text, bracket, "[", "]")
            if close is not None and close + 1 < len(line_text) and line_text[close + 1] == "(":
                end = find_closing(line_text, close + 1, "(", ")")
                if end is not None:
                    inside = line_text[close + 2 : end]
                    try:
                        _, _, _, angle = destination_parts(inside)
                        original_value = inside.strip()
                        if angle:
                            close_angle = original_value.find(">")
                            destination = original_value[1:close_angle]
                            tail = original_value[close_angle + 1 :]
                        else:
                            title_match = re.match(
                                r"^(.*?)([ \t]+(?:\".*\"|'.*'|\(.*\)))$",
                                original_value,
                            )
                            if title_match:
                                destination, tail = title_match.group(1), title_match.group(2)
                            else:
                                destination, tail = original_value, ""
                        if not external_destination(destination.strip()):
                            destination = unescape_destination(destination)
                        updated = rewrite(destination, image, line_no)
                        out.append(line_text[cursor : close + 2])
                        out.append(format_destination(updated, angle) + tail)
                        out.append(")")
                        cursor = end + 1
                        continue
                    except ValueError as exc:
                        add_issue(issues, source, line_no, f"unsupported Markdown link: {exc}")
        out.append(line_text[cursor])
        cursor += 1
    return "".join(out)


def rewrite_html_links(line_text: str, line_no: int, rewrite, source: Path, issues: list[Issue]) -> str:
    replacements: list[tuple[int, int, str]] = []
    searchable = mask_inline_code(line_text)
    for tag in HTML_TAG.finditer(searchable):
        for attr in HTML_ATTR.finditer(tag.group(0)):
            name = attr.group(1).lower()
            if name not in ("href", "src"):
                continue
            if attr.group(2) is not None:
                start, end, value, quote_char = attr.start(2), attr.end(2), attr.group(2), '"'
            elif attr.group(3) is not None:
                start, end, value, quote_char = attr.start(3), attr.end(3), attr.group(3), "'"
            else:
                start, end, value, quote_char = attr.start(4), attr.end(4), attr.group(4), ""
            updated = rewrite(value, name == "src", line_no)
            if updated != value:
                if quote_char:
                    updated = updated.replace(quote_char, "%22" if quote_char == '"' else "%27")
                replacements.append((tag.start() + start, tag.start() + end, updated))
    for start, end, value in reversed(replacements):
        line_text = line_text[:start] + value + line_text[end:]
    return line_text


def rewrite_explicit_ids(line_text: str, anchors: list[ExplicitAnchor]) -> str:
    for anchor in reversed(anchors):
        line_text = line_text[: anchor.start] + anchor.output_id + line_text[anchor.end :]
    return line_text


def render_note(
    note: SourceNote,
    output: Path,
    notes_by_path: dict[Path, SourceNote],
    root: Path,
    issues: list[Issue],
) -> str:
    rewrite = make_rewriter(note.source_path, output, note, notes_by_path, root, issues)
    output_lines: list[str] = []
    for index, original in enumerate(note.lines):
        if note.fenced[index]:
            output_lines.append(original)
            continue
        heading = note.heading_by_line.get(index)
        if heading and heading.underline_index is not None:
            marker = "#" * min(6, heading.level + 2)
            heading_line = f"{marker} {heading.title}{line_ending(original)}"
            heading_line = rewrite_html_links(heading_line, index + 1, rewrite, note.source_path, issues)
            heading_line = rewrite_markdown_links(
                heading_line, index + 1, rewrite, issues, note.source_path
            )
            output_lines.append(heading_line)
            continue
        if index in note.underline_by_line:
            continue
        if heading:
            plain = without_line_ending(original)
            match = ATX_HEADING.match(plain)
            if match:
                marker = "#" * min(6, heading.level + 2)
                transformed = " " * (len(plain) - len(plain.lstrip(" "))) + marker + " " + match.group(2)
                original = transformed + line_ending(original)
        anchors = note.anchors_by_line.get(index)
        if anchors:
            original = rewrite_explicit_ids(original, anchors)
        rewritten = rewrite_html_links(original, index + 1, rewrite, note.source_path, issues)
        rewritten = rewrite_markdown_links(rewritten, index + 1, rewrite, issues, note.source_path)
        if WIKILINK.search(mask_inline_code(without_line_ending(original))):
            add_issue(
                issues,
                note.source_path,
                index + 1,
                "Obsidian wikilinks are unsupported in generated reading docs; use a Markdown link",
            )
        output_lines.append(rewritten)
    body = "".join(output_lines).strip("\r\n")
    return f"## {note.title}\n\n{body}\n"


def native_output_anchor_names(content: str) -> set[str]:
    lines = split_lines(content)
    fenced = fenced_lines(lines)
    names: set[str] = set()
    for index, line in enumerate(lines):
        if fenced[index]:
            continue
        for _, _, _, value in html_anchor_attributes(without_line_ending(line)):
            names.add(value)
    for _, _, _, title in heading_records(lines, fenced):
        names.add(native_title(title))
    return names


def parse_generated_links(path: Path, content: str, root: Path, issues: list[Issue]) -> None:
    lines = split_lines(content)
    fenced = fenced_lines(lines)
    anchors = native_output_anchor_names(content)
    for index, original in enumerate(lines):
        if fenced[index]:
            continue
        plain = without_line_ending(original)
        for name, _, _, value in html_attributes(mask_inline_code(plain)):
            if name == "href":
                validate_generated_destination(value, path, index + 1, anchors, root, issues)
            elif name == "src":
                validate_generated_destination(value, path, index + 1, anchors, root, issues, image=True)
        definition = REFERENCE_DEF.match(plain)
        if definition:
            raw = definition.group(2)
            destination = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
            validate_generated_destination(destination, path, index + 1, anchors, root, issues)

        def validate_only(raw: str, is_image: bool, line_no: int) -> str:
            validate_generated_destination(raw, path, line_no, anchors, root, issues, image=is_image)
            return raw

        rewrite_markdown_links(plain, index + 1, validate_only, issues, path)


def validate_generated_destination(
    raw: str,
    document: Path,
    line: int,
    anchors: set[str],
    root: Path,
    issues: list[Issue],
    image: bool = False,
) -> None:
    if external_destination(raw):
        return
    try:
        raw_path, _, fragment, _ = destination_parts(raw)
    except ValueError as exc:
        add_issue(issues, document, line, f"unsupported generated link {raw!r}: {exc}")
        return
    if not raw_path:
        if fragment and decode_native_fragment(fragment) not in anchors:
            add_issue(issues, document, line, f"generated link fragment does not exist: #{fragment}")
        return
    target = locate_destination(document, raw_path, root, issues, line, raw)
    if target is None or not fragment:
        return
    if target.suffix.lower() == ".md":
        resolved_target = target.resolve()
        generated_dir = (root / OUTPUT_DIR).resolve()
        try:
            resolved_target.relative_to(generated_dir)
            is_generated_target = True
        except ValueError:
            is_generated_target = False
        if resolved_target == document.resolve():
            target_anchors = anchors
            native_target = True
        elif is_generated_target:
            try:
                target_content = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                add_issue(issues, document, line, f"cannot inspect linked Markdown target: {exc}")
                return
            target_anchors = native_output_anchor_names(target_content)
            native_target = True
        else:
            try:
                target_anchors = source_anchor_names(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                add_issue(issues, document, line, f"cannot inspect linked Markdown target: {exc}")
                return
            native_target = False
        found = (
            decode_native_fragment(fragment) in target_anchors
            if native_target
            else normalized_fragment(fragment) in target_anchors
        )
        if not found:
            add_issue(
                issues,
                document,
                line,
                f"generated link fragment does not exist in {display_path(target, root)}: #{fragment}",
            )


def build(root: Path) -> tuple[dict[Path, str], list[Issue]]:
    issues: list[Issue] = []
    plans = [DomainPlan(name, title, root / name / "index.md") for name, title in DOMAINS.items()]
    for plan in plans:
        parse_map(plan, root, issues)

    notes_by_path: dict[Path, SourceNote] = {}
    for plan in plans:
        for entry in plan.entries:
            note = make_note(plan.name, entry.target, entry.title, root, issues)
            if note is not None:
                plan.notes.append(note)
                notes_by_path[note.source_path] = note
        assign_native_targets(plan)

    # Resolve source-heading references to their generated native heading titles.
    for note in notes_by_path.values():
        for key, target in list(note.fragments.items()):
            if target.startswith(note.internal_prefix + "-h"):
                try:
                    index = int(target.rsplit("-h", 1)[1]) - 1
                    note.fragments[key] = note.headings[index].output_native_title
                except (ValueError, IndexError):
                    pass

    expected: dict[Path, str] = {}
    for plan in plans:
        output = root / OUTPUT_DIR / f"{plan.name}.md"
        map_url = relative_url(plan.map_path, output.parent)
        provenance = (
            f"> Generated from the [{plan.name} reading map]({map_url}). "
            "Edit the map and its linked source notes. Internal section links use Obsidian heading fragments; "
            "source notes remain standard Markdown.\n\n"
        )
        pieces = [f"# {plan.title}\n\n", provenance]
        for note in plan.notes:
            pieces.append(render_note(note, output, notes_by_path, root, issues))
        expected[output] = "".join(pieces)
    return expected, issues


def check_existing_outputs(root: Path, expected: dict[Path, str] | None, issues: list[Issue]) -> None:
    output_dir = root / OUTPUT_DIR
    for name in DOMAINS:
        path = output_dir / f"{name}.md"
        if not path.is_file():
            add_issue(issues, path, 0, "generated document is missing; run the generator")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            add_issue(issues, path, 0, f"cannot read UTF-8 Markdown: {exc}")
            continue
        parse_generated_links(path, content, root, issues)
        if expected is not None and expected.get(path) != content:
            add_issue(issues, path, 0, "generated document is stale; run the generator")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate maps, source and generated links, and output freshness without writing",
    )
    args = parser.parse_args(argv)
    root = ROOT.resolve()
    expected, issues = build(root)
    if args.check:
        check_existing_outputs(root, expected if not issues else None, issues)
    elif not issues:
        for path, content in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="") as output_file:
                output_file.write(content)
        print(f"Generated {len(expected)} reading documents under {OUTPUT_DIR.as_posix()}/")

    if issues:
        for issue in issues:
            location = display_path(issue.path, root)
            prefix = f"{location}:{issue.line}" if issue.line else location
            print(f"{prefix}: {issue.message}", file=sys.stderr)
        return 1
    if args.check:
        print("Reading maps, source links, generated links, and outputs are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
