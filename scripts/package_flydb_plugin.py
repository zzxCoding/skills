#!/usr/bin/env python3
"""Materialize only the four Flydb skills; --check detects release drift."""

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("flydb", "flydb-cli-release", "flydb-migration-scripts", "flydb-multi-environment")
TARGET = ROOT / "plugins" / "flydb-skills" / "skills"


def files(directory):
    result = {}
    for item in directory.rglob("*"):
        if item.is_symlink():
            raise ValueError(f"Symlinks are not supported: {item}")
        if item.is_file() and item.name != ".DS_Store" and "__pycache__" not in item.parts:
            result[item.relative_to(directory)] = item.read_bytes()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = {}
    for name in NAMES:
        source = ROOT / "skills" / name
        if not (source / "SKILL.md").is_file():
            raise ValueError(f"Missing skill: {source}")
        expected.update({Path(name) / key: value for key, value in files(source).items()})
    actual = files(TARGET) if TARGET.exists() else {}
    drift = sorted(str(key) for key in expected.keys() | actual.keys()
                   if expected.get(key) != actual.get(key))
    if args.check:
        if drift:
            print("Plugin content drift:\n" + "\n".join(drift))
            return 1
        print(f"Plugin matches all four source skills ({len(expected)} files).")
        return 0
    if TARGET.exists():
        shutil.rmtree(TARGET)
    for key, value in expected.items():
        destination = TARGET / key
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(value)
    print(f"Packaged four Flydb skills ({len(expected)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
