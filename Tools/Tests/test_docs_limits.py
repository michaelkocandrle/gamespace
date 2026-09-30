"""Size limits of the documents every session reads (plain Python, runs in Tools/Test.ps1 and CI):

    python Tools/Tests/test_docs_limits.py

- Docs/CURRENT.md, the one file of current state, a SessionStart hook puts it into every session: at most 80 lines
  (author, 30. 9. 2026). Longer means history or detail that belongs in a commit, a review or ARCHITECTURE.md.
Prints DOCTEST PASS|FAIL lines and DOCTEST SUMMARY; exit code 1 on a failure.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIMITS = [("Docs/CURRENT.md", 80)]


def main():
    failures = 0
    for path, limit in LIMITS:
        with open(os.path.join(REPO, path), encoding="utf-8") as f:
            count = len(f.read().splitlines())
        ok = count <= limit
        failures += 0 if ok else 1
        print("DOCTEST %s %s has %d lines (limit %d)" % ("PASS" if ok else "FAIL", path, count, limit))
    print("DOCTEST SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
