#!/usr/bin/env python3
"""sovereign-guard.py — no-fly-list CI guard for the sovereignty stack.

Scans the tree for forbidden patterns (React scaffold, CRA configs, npm
phone-home). Fails the build on any hit. Skips its own scar/ and guard/
directories so it never flags its own records. Also skips frontend/,
external/, scripts/, and docs/ — archived or non-authoritative trees
that are not part of the active runtime.
"""
import os
import re
import sys

NO_FLY = [
    (r"from\s+['\"]react['\"]", "React named import"),
    (r"import\s+React\b", "React default import"),
    (r"react-scripts", "CRA react-scripts dependency"),
    (r"create-react-app", "CRA scaffold command"),
    (r"@types/react", "React type definitions"),
    (r"react-dom", "React DOM runtime"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", "scar", "guard", ".venv", "venv",
             "frontend", "external", "scripts", "docs"}


def scan(root):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            try:
                text = open(path, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for pattern, label in NO_FLY:
                for m in re.finditer(pattern, text):
                    line = text[: m.start()].count("\n") + 1
                    hits.append((path, line, label, m.group(0)))
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    hits = scan(root)
    if hits:
        print("FAIL — no-fly violations found:")
        for path, line, label, match in hits:
            print(f"  {path}:{line} [{label}] match={match!r}")
        sys.exit(1)
    print("PASS — no no-fly violations.")
    sys.exit(0)


if __name__ == "main__":
    main()
