#!/usr/bin/env python3
"""Safely scan and update SKILL.md description fields."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import stat
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


FIELD_RE = re.compile(
    r"^(?P<indent>[ \t]*)description:(?P<rest>.*?)(?P<eol>\r?\n)?$"
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
BLOCK_HEADER_RE = re.compile(r"^[|>](?:[1-9][+-]?|[+-][1-9]?)?(?:\s+#.*)?$")
UNSAFE_PLAIN_PREFIXES = tuple("-?:,[]{}#&*!|>'\"%@`")
YAML_KEYWORDS = {
    "",
    "null",
    "~",
    "true",
    "false",
    "yes",
    "no",
    "on",
    "off",
}
PROJECT_SKILL_ROOTS = (
    "skills",
    ".agents/skills",
    ".codex/skills",
    ".claude/skills",
    ".opencode/skills",
    "agent/skills",
)
USER_SKILL_ROOTS = (
    ".agents/skills",
    ".codex/skills",
    ".claude/skills",
    ".cc-switch/skills",
    ".config/agents/skills",
    ".config/opencode/skills",
)


class SkillFileError(ValueError):
    """Raised when a SKILL.md cannot be handled safely."""


@dataclass(frozen=True)
class DescriptionField:
    start: int
    end: int
    indent: str
    rest: str
    eol: str
    style: str
    description: str
    block_indent: str | None = None


@dataclass(frozen=True)
class SkillDocument:
    path: Path
    text: str
    lines: list[str]
    field: DescriptionField


def line_without_eol(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    return line, ""


def frontmatter_bounds(lines: list[str]) -> tuple[int, int]:
    if not lines:
        raise SkillFileError("empty file")

    first, _ = line_without_eol(lines[0])
    if first != "---":
        raise SkillFileError("missing opening YAML frontmatter delimiter")

    for index in range(1, len(lines)):
        value, _ = line_without_eol(lines[index])
        if value in {"---", "..."}:
            return 1, index

    raise SkillFileError("missing closing YAML frontmatter delimiter")


def leading_indent(value: str) -> str:
    return value[: len(value) - len(value.lstrip(" \t"))]


def split_inline_comment(value: str) -> tuple[str, str]:
    quote: str | None = None
    escaped = False
    index = 0

    while index < len(value):
        char = value[index]
        if quote == '"':
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quote = None
            index += 1
            continue

        if quote == "'":
            if char == "'" and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            if char == "'":
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
        elif char == "#" and (index == 0 or value[index - 1].isspace()):
            comment_start = index
            while comment_start > 0 and value[comment_start - 1] in " \t":
                comment_start -= 1
            return value[:comment_start], value[comment_start:]
        index += 1

    return value, ""


def decode_inline_scalar(value: str) -> str:
    scalar, _ = split_inline_comment(value)
    scalar = scalar.strip()

    if len(scalar) >= 2 and scalar[0] == scalar[-1] == "'":
        return scalar[1:-1].replace("''", "'")

    if len(scalar) >= 2 and scalar[0] == scalar[-1] == '"':
        try:
            decoded = json.loads(scalar)
        except json.JSONDecodeError:
            return scalar[1:-1]
        if isinstance(decoded, str):
            return decoded

    return scalar


def decode_block_scalar(
    lines: list[str], start: int, end: int, style: str
) -> tuple[str, str]:
    content = lines[start:end]
    nonblank = [
        leading_indent(line_without_eol(line)[0])
        for line in content
        if line_without_eol(line)[0].strip()
    ]
    block_indent = min(nonblank, key=len) if nonblank else "  "
    values: list[str] = []

    for line in content:
        value, _ = line_without_eol(line)
        if value.startswith(block_indent):
            value = value[len(block_indent) :]
        values.append(value)

    if style == ">":
        return " ".join(part.strip() for part in values).strip(), block_indent
    return "\n".join(values).rstrip("\n"), block_indent


def parse_document(path: Path) -> SkillDocument:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeError) as error:
        raise SkillFileError(f"cannot read UTF-8 file: {error}") from error

    lines = text.splitlines(keepends=True)
    start, end = frontmatter_bounds(lines)
    matches: list[tuple[int, re.Match[str]]] = []

    for index in range(start, end):
        value, eol = line_without_eol(lines[index])
        match = FIELD_RE.match(value)
        if match and not match.group("indent"):
            match_data = FIELD_RE.match(value + eol)
            if match_data is not None:
                matches.append((index, match_data))

    if not matches:
        raise SkillFileError("missing top-level description field")
    if len(matches) > 1:
        raise SkillFileError("duplicate top-level description fields")

    field_start, match = matches[0]
    rest = match.group("rest")
    eol = match.group("eol") or ""
    stripped = rest.strip()

    if stripped and BLOCK_HEADER_RE.match(stripped):
        field_end = field_start + 1
        while field_end < end:
            value, _ = line_without_eol(lines[field_end])
            if value and not value[0].isspace():
                break
            field_end += 1
        style = stripped[0]
        description, block_indent = decode_block_scalar(
            lines, field_start + 1, field_end, style
        )
    else:
        field_end = field_start + 1
        style = "inline"
        description = decode_inline_scalar(rest)
        block_indent = None

    if not description:
        raise SkillFileError("description is empty")

    return SkillDocument(
        path=path,
        text=text,
        lines=lines,
        field=DescriptionField(
            start=field_start,
            end=field_end,
            indent=match.group("indent"),
            rest=rest,
            eol=eol,
            style=style,
            description=description,
            block_indent=block_indent,
        ),
    )


def discover_skill_files(target: Path) -> list[Path]:
    if target.is_file():
        if target.name != "SKILL.md":
            raise SkillFileError("target file must be named SKILL.md")
        return [target]
    if not target.is_dir():
        raise SkillFileError("target does not exist or is not a directory")

    ignored = {".git", "node_modules", "__pycache__"}
    return sorted(
        path
        for path in target.rglob("SKILL.md")
        if not any(part in ignored for part in path.parts)
    )


def discover_skill_roots(project_root: Path, home_root: Path) -> list[dict[str, object]]:
    project_root = project_root.resolve()
    home_root = home_root.resolve()
    specs: list[tuple[str, str, Path]] = []

    if (project_root / "SKILL.md").is_file():
        specs.append(("project", "当前项目技能", project_root))
    else:
        specs.extend(
            ("project", f"当前项目 {relative}", project_root / relative)
            for relative in PROJECT_SKILL_ROOTS
        )

    specs.extend(
        ("user", f"用户级 {relative}", home_root / relative)
        for relative in USER_SKILL_ROOTS
    )

    candidates: list[dict[str, object]] = []
    seen: set[Path] = set()
    for scope, label, path in specs:
        resolved = path.resolve()
        if resolved in seen or not resolved.is_dir():
            continue
        seen.add(resolved)
        scan_results, _ = scan_target(resolved)
        skill_count = len(scan_results)
        if not skill_count:
            continue
        candidates.append(
            {
                "path": str(resolved),
                "scope": scope,
                "label": label,
                "skills_found": skill_count,
                "translatable_descriptions": sum(
                    item.get("language_hint") == "no-cjk"
                    for item in scan_results
                ),
                "already_localized": sum(
                    item.get("language_hint") == "contains-cjk"
                    for item in scan_results
                ),
                "errors": sum(item["status"] == "error" for item in scan_results),
            }
        )

    candidates.sort(
        key=lambda item: (
            item["translatable_descriptions"] == 0,
            item["scope"] != "project",
        )
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = index
        candidate["recommended"] = index == 1

    return candidates


def relative_name(path: Path, target: Path) -> str:
    if target.is_file():
        return path.name
    return path.relative_to(target).as_posix()


def scan_target(target: Path) -> tuple[list[dict[str, object]], dict[str, SkillDocument]]:
    results: list[dict[str, object]] = []
    documents: dict[str, SkillDocument] = {}

    for path in discover_skill_files(target):
        relative = relative_name(path, target)
        try:
            document = parse_document(path)
        except SkillFileError as error:
            results.append(
                {
                    "path": relative,
                    "status": "error",
                    "error": str(error),
                }
            )
            continue

        documents[relative] = document
        results.append(
            {
                "path": relative,
                "status": "ok",
                "description": document.field.description,
                "language_hint": (
                    "contains-cjk"
                    if CJK_RE.search(document.field.description)
                    else "no-cjk"
                ),
                "format": (
                    "block-" + document.field.style
                    if document.field.style in {"|", ">"}
                    else "inline"
                ),
            }
        )

    return results, documents


def safe_plain_scalar(value: str) -> bool:
    lowered = value.casefold()
    return (
        "\n" not in value
        and "\r" not in value
        and not value.startswith(UNSAFE_PLAIN_PREFIXES)
        and ": " not in value
        and " #" not in value
        and value.strip() == value
        and lowered not in YAML_KEYWORDS
    )


def validate_translation(value: object) -> str:
    if not isinstance(value, str):
        raise SkillFileError("translation must be a string")
    if not value.strip():
        raise SkillFileError("translation must not be empty")
    if "\x00" in value:
        raise SkillFileError("translation must not contain NUL")
    if len(value) > 1024:
        raise SkillFileError("translation exceeds the 1024-character limit")
    return value


def encode_inline_translation(original_rest: str, translation: str) -> str:
    leading = original_rest[: len(original_rest) - len(original_rest.lstrip(" \t"))]
    value_with_comment = original_rest[len(leading) :]
    value, comment = split_inline_comment(value_with_comment)
    stripped = value.strip()
    trailing = value[len(value.rstrip(" \t")) :]

    if stripped.startswith("'") and stripped.endswith("'"):
        encoded = "'" + translation.replace("\n", " ").replace("'", "''") + "'"
    elif stripped.startswith('"') and stripped.endswith('"'):
        encoded = json.dumps(translation.replace("\n", " "), ensure_ascii=False)
    elif safe_plain_scalar(translation):
        encoded = translation
    else:
        encoded = json.dumps(translation.replace("\n", " "), ensure_ascii=False)

    return leading + encoded + trailing + comment


def replace_description(document: SkillDocument, translation: str) -> str:
    field = document.field
    lines = list(document.lines)

    if field.style == "inline":
        replacement = (
            f"{field.indent}description:"
            f"{encode_inline_translation(field.rest, translation)}"
            f"{field.eol}"
        )
        lines[field.start : field.end] = [replacement]
        return "".join(lines)

    header = lines[field.start]
    block_indent = field.block_indent or field.indent + "  "
    eol = field.eol or "\n"
    translated_lines = translation.splitlines() or [translation]
    block = [block_indent + line + eol for line in translated_lines]
    lines[field.start : field.end] = [header, *block]
    return "".join(lines)


def load_translations(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SkillFileError(f"cannot read translations JSON: {error}") from error

    if not isinstance(payload, dict):
        raise SkillFileError("translations JSON must be an object")

    translations: dict[str, str] = {}
    for key, value in payload.items():
        if not isinstance(key, str) or not key:
            raise SkillFileError("translation paths must be non-empty strings")
        translations[key] = validate_translation(value)
    return translations


def atomic_write(path: Path, text: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def unified_diff(path: str, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def print_json(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_discover(project_root: Path, home_root: Path) -> int:
    candidates = discover_skill_roots(project_root, home_root)
    print_json(
        {
            "project_root": str(project_root),
            "candidates": candidates,
            "manual_path_allowed": True,
            "message": (
                "请选择一个候选目录，或手工输入其他路径。"
                if candidates
                else "常见位置未发现技能，请手工输入其他路径。"
            ),
        }
    )
    return 0


def handle_scan(target: Path) -> int:
    results, _ = scan_target(target)
    print_json(
        {
            "target": str(target),
            "skills_found": len(results),
            "skills": results,
        }
    )
    return 1 if any(item["status"] == "error" for item in results) else 0


def handle_apply(target: Path, translations_path: Path, write: bool) -> int:
    scan_results, documents = scan_target(target)
    scan_errors = [item for item in scan_results if item["status"] == "error"]
    translations = load_translations(translations_path)
    unknown = sorted(set(translations) - set(documents))
    if unknown:
        raise SkillFileError(
            "translation path was not found or could not be parsed: "
            + ", ".join(unknown)
        )

    changes: list[dict[str, object]] = []
    for relative, translation in translations.items():
        document = documents[relative]
        updated = replace_description(document, translation)
        changed = updated != document.text
        if write and changed:
            atomic_write(document.path, updated)
        changes.append(
            {
                "path": relative,
                "changed": changed,
                "written": bool(write and changed),
                "original": document.field.description,
                "translated": translation,
                "diff": unified_diff(relative, document.text, updated),
            }
        )

    print_json(
        {
            "mode": "write" if write else "dry-run",
            "target": str(target),
            "changes": changes,
            "scan_errors": scan_errors,
        }
    )
    return 1 if scan_errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover, scan, or safely update SKILL.md description fields."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser(
        "discover", help="Find common project and user skill directories."
    )
    discover.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used to find project-local skill directories.",
    )
    discover.add_argument(
        "--home-root",
        type=Path,
        default=Path.home(),
        help=argparse.SUPPRESS,
    )

    scan = subparsers.add_parser("scan", help="List descriptions as JSON.")
    scan.add_argument("target", type=Path)

    apply = subparsers.add_parser(
        "apply", help="Preview or apply translations from a JSON mapping."
    )
    apply.add_argument("target", type=Path)
    apply.add_argument("--translations", type=Path, required=True)
    apply.add_argument(
        "--write",
        action="store_true",
        help="Write changes atomically. Without this flag, only emit a diff.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "discover":
            return handle_discover(
                args.project_root.resolve(), args.home_root.resolve()
            )
        if args.command == "scan":
            return handle_scan(args.target.resolve())
        return handle_apply(
            args.target.resolve(), args.translations.resolve(), args.write
        )
    except (OSError, SkillFileError) as error:
        print_json({"status": "error", "error": str(error)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
