#!/usr/bin/env python3
"""Validate this skill's structure, local links, and evaluation fixtures."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def load_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        raw, body = text[4:].split("\n---\n", 1)
    except ValueError as error:
        raise ValueError("SKILL.md frontmatter is not closed") from error
    metadata: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body


def validate_evals(root: Path, errors: list[str]) -> None:
    required = {
        "activation.json": {"id", "query", "should_trigger", "reason"},
        "behavior.json": {"id", "input", "expected", "forbidden", "grader"},
    }
    for filename, fields in required.items():
        path = root / "evals" / filename
        if not path.is_file():
            errors.append(f"missing evaluation fixture: {path.relative_to(root)}")
            continue
        try:
            cases = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"invalid JSON in {path.relative_to(root)}: {error}")
            continue
        if not isinstance(cases, list) or not cases:
            errors.append(f"{path.relative_to(root)} must contain a non-empty array")
            continue
        seen: set[str] = set()
        for index, case in enumerate(cases, start=1):
            if not isinstance(case, dict):
                errors.append(f"{path.relative_to(root)} case {index} must be an object")
                continue
            missing = fields - case.keys()
            if missing:
                errors.append(
                    f"{path.relative_to(root)} case {index} missing: {', '.join(sorted(missing))}"
                )
            case_id = case.get("id")
            if not isinstance(case_id, str) or not case_id:
                errors.append(f"{path.relative_to(root)} case {index} needs a non-empty id")
            elif case_id in seen:
                errors.append(f"duplicate id in {path.relative_to(root)}: {case_id}")
            else:
                seen.add(case_id)
            if filename == "activation.json" and not isinstance(case.get("should_trigger"), bool):
                errors.append(f"{path.relative_to(root)} case {index} should_trigger must be boolean")
            if filename == "behavior.json":
                for field in ("expected", "forbidden"):
                    if not isinstance(case.get(field), list):
                        errors.append(f"{path.relative_to(root)} case {index} {field} must be an array")


def validate_links(root: Path, errors: list[str]) -> None:
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            clean = target.split("#", 1)[0]
            if not clean or clean.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / clean).resolve()
            if not resolved.exists():
                errors.append(f"broken link in {path.relative_to(root)}: {target}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", nargs="?", default=".", type=Path)
    args = parser.parse_args()
    root = args.skill_dir.resolve()
    skill = root / "SKILL.md"
    errors: list[str] = []

    if not skill.is_file():
        errors.append("missing SKILL.md")
    else:
        try:
            metadata, body = load_frontmatter(skill)
        except (OSError, ValueError) as error:
            errors.append(str(error))
        else:
            if set(metadata) != {"name", "description"}:
                errors.append("frontmatter must contain only name and description")
            name = metadata.get("name", "")
            description = metadata.get("description", "")
            if not NAME_RE.fullmatch(name):
                errors.append("name must be 1-64 lowercase letters, digits, or hyphens")
            if name and root.name != name:
                errors.append(f"folder name {root.name!r} does not match skill name {name!r}")
            if not description or len(description) > 1024:
                errors.append("description must contain 1-1024 characters")
            body_lines = len(body.splitlines())
            if body_lines >= 500:
                errors.append(f"SKILL.md body must stay under 500 lines; found {body_lines}")

    if not (root / "agents" / "openai.yaml").is_file():
        errors.append("missing recommended agents/openai.yaml")
    validate_links(root, errors)
    validate_evals(root, errors)

    if errors:
        print("skill validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    reference_count = len(list((root / "references").glob("*.md")))
    print(f"skill validation passed: {reference_count} references, 2 evaluation fixtures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
