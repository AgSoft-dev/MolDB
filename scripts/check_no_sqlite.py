"""Fail if any given (or staged) file is a SQLite database.

Molecule databases are confidential and must never be committed, whatever
their file name. Used by .githooks/pre-commit and CI.

Usage:
    python scripts/check_no_sqlite.py            # check staged files
    python scripts/check_no_sqlite.py FILE ...   # check the given files
    python scripts/check_no_sqlite.py --all      # check all tracked files
"""
from __future__ import annotations
import subprocess
import sys

SQLITE_MAGIC = b"SQLite format 3\x00"


def git_files(*args: str) -> list[str]:
    out = subprocess.run(["git", *args, "-z"], capture_output=True, check=True).stdout
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def is_sqlite(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(len(SQLITE_MAGIC)) == SQLITE_MAGIC
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return False


def main(argv: list[str]) -> int:
    if argv == ["--all"]:
        files = git_files("ls-files")
    elif argv:
        files = argv
    else:
        files = git_files("diff", "--cached", "--name-only", "--diff-filter=ACMR")
    bad = [p for p in files if is_sqlite(p)]
    for p in bad:
        print(f"ERROR: {p} is a SQLite database. Molecule databases must not be committed.", file=sys.stderr)
    if bad:
        print("Unstage with: git rm --cached <file>", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
