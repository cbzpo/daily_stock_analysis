#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend source file size report (non-blocking).

Reports the largest Python source files and flags files that exceed the
suggested per-file size cap. This is an informational gate only: it helps
reviewers spot "god module" growth early (see architecture review P0/P1
follow-ups) and NEVER fails the build. Splitting an oversized file is always
done as a dedicated, behaviour-preserving refactor PR.

Usage:
    python scripts/check_file_sizes.py [--threshold LINES] [--top N]

Exit code is always 0; the report is advisory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Runtime backend code that ships in the package / Docker image. Tooling and
# one-off maintenance scripts under scripts/ are excluded.
_SCAN_DIRS = ("src", "api", "bot", "data_provider")
_SCAN_ROOT_FILES = ("main.py", "server.py")

DEFAULT_THRESHOLD = 1200
DEFAULT_TOP = 15


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _count_lines(path: Path) -> int:
    """Count physical lines, tolerating mixed encodings."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def collect_python_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for dirname in _SCAN_DIRS:
        base = root / dirname
        if base.is_dir():
            files.extend(p for p in base.rglob("*.py") if p.is_file())
    for filename in _SCAN_ROOT_FILES:
        candidate = root / filename
        if candidate.is_file():
            files.append(candidate)
    return files


def build_report(root: Path) -> Tuple[List[Tuple[int, Path]], int]:
    """Return ``(sized_files, total_files)`` sorted by line count descending."""
    files = collect_python_files(root)
    sized = [( _count_lines(path), path) for path in files]
    sized = [(lines, path) for lines, path in sized if lines > 0]
    sized.sort(key=lambda item: item[0], reverse=True)
    return sized, len(files)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report oversized backend Python source files (advisory, never fails).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Line count at which a file is flagged for splitting (default: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"How many largest files to list (default: {DEFAULT_TOP}).",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    sized, total_files = build_report(root)

    print("==> backend-gate: source file size report (advisory, non-blocking)")
    print(f"    scanned {total_files} Python files under: {', '.join(_SCAN_DIRS)} (+ {', '.join(_SCAN_ROOT_FILES)})")
    print(f"    suggested per-file cap: {args.threshold} lines")
    print()
    print(f"    top {min(args.top, len(sized))} largest files:")
    for lines, path in sized[: args.top]:
        rel = path.relative_to(root).as_posix()
        marker = "  [OVER CAP]" if lines > args.threshold else ""
        print(f"      {lines:>6}  {rel}{marker}")

    over_cap = [(lines, path) for lines, path in sized if lines > args.threshold]
    print()
    if over_cap:
        print(
            f"    NOTE: {len(over_cap)} file(s) exceed the suggested cap of "
            f"{args.threshold} lines. This is informational only; split such "
            "files in dedicated refactor PRs, not as drive-by changes."
        )
        for lines, path in over_cap:
            print(f"      - {path.relative_to(root).as_posix()} ({lines} lines)")
    else:
        print(f"    OK: no files exceed the suggested cap of {args.threshold} lines.")

    # Advisory gate: always succeed.
    return 0


if __name__ == "__main__":
    sys.exit(main())
