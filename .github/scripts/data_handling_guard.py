#!/usr/bin/env python3
"""
Data-handling guard — a CI floor, not a substitute for reviewer judgment.

Checks changed files for:
1. Missing `Handling:` marking on substantive new/changed files.
2. Patterns associated with classified/protected markings that should
   never appear in this commercially hosted repository.
3. Obvious credential/secret leakage (API keys, private key headers, etc.).

Exits non-zero (failing the CI job) if any check fails.
"""
import re
import sys
from pathlib import Path

# This script necessarily contains the patterns it searches for, so it is
# excluded from the content scan (it is still reviewed like any other file).
SELF = ".github/scripts/data_handling_guard.py"

CLASSIFIED_PATTERNS = [
    r"\bTOP\s+SECRET\b",
    r"\bSECRET\b(?!\s*(key|token|manager))",  # allow "SECRET key/token/manager" as code terms
    r"\bPROTECTED\s*[ABC]\b",
    r"\bCLASSIFIED\b",
    r"\bNOFORN\b",
]

CREDENTIAL_PATTERNS = [
    r"-----BEGIN (RSA |EC |OPENSSH |PGP |DSA )?PRIVATE KEY-----",
    r"\bAKIA[0-9A-Z]{16}\b",  # AWS access key id shape
    r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",  # GitHub token shapes
    r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
    r"secret[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
]

# File types we don't require a Handling: marker on (config/build plumbing,
# not substantive content).
EXEMPT_SUFFIXES = {
    ".gitignore", ".yml", ".yaml", ".json", ".png", ".jpg", ".jpeg", ".svg",
    ".lock",
}
EXEMPT_NAMES = {"LICENSE", "NOTICE", ".gitignore"}
EXEMPT_DIRS = (".github/",)

HANDLING_RE = re.compile(r"Handling\s*:\**\s*\S", re.IGNORECASE)


def requires_handling_marker(path: str) -> bool:
    p = Path(path)
    if any(path.startswith(d) for d in EXEMPT_DIRS):
        return False
    if p.name in EXEMPT_NAMES:
        return False
    if p.suffix.lower() in EXEMPT_SUFFIXES:
        return False
    return p.suffix.lower() in {".md", ".py", ".ts", ".js", ".json5", ""}


def scan_file(path: str, errors: list[str]) -> None:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
    except (FileNotFoundError, IsADirectoryError):
        return

    if requires_handling_marker(path) and not HANDLING_RE.search(text):
        errors.append(f"{path}: missing a `Handling:` marker (see HANDLING.md)")

    if path == SELF:
        return

    for pat in CLASSIFIED_PATTERNS:
        if re.search(pat, text):
            errors.append(f"{path}: matched a disallowed classification pattern ({pat}) — this repo is Unclassified-working only")

    for pat in CREDENTIAL_PATTERNS:
        if re.search(pat, text):
            errors.append(f"{path}: matched a possible credential/secret pattern ({pat}) — remove before committing")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: data_handling_guard.py <changed_files_list.txt>")
        return 2

    changed_files_list = Path(sys.argv[1])
    if not changed_files_list.exists():
        print("No changed-files list found; nothing to check.")
        return 0

    files = [line.strip() for line in changed_files_list.read_text().splitlines() if line.strip()]
    errors: list[str] = []
    for f in files:
        if Path(f).is_file():
            scan_file(f, errors)

    if errors:
        print("Data-handling guard failed:\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Data-handling guard passed ({len(files)} file(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
