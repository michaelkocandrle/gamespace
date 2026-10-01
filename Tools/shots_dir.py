"""Where the screenshots live (author 1. 10. 2026: off drive C, they were 20 GB under Saved/Shots).

The root is, in this order: the environment variable GAMESPACE_SHOTS_DIR, D:/gamespace-shots when drive D exists,
else <repo>/Saved/Shots (a clone without drive D). Tools/ShotsDir.ps1 answers the same for PowerShell.

Reviews and other files in git name a picture by a logical path, "shots:<set>/<file>", so they work on any
machine; the old form "Saved/Shots/<set>/<file>" is still understood.

    python Tools/shots_dir.py                      # prints the root
    from shots_dir import resolve; resolve("shots:20261001_014523_wayfarer_exterior_review/01_day_chase_rear.png")
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFIX = "shots:"
LEGACY = ("Saved/Shots/", "Saved\\Shots\\")


def root():
    env = os.environ.get("GAMESPACE_SHOTS_DIR")
    if env:
        return env
    if os.path.isdir("D:/"):
        return "D:/gamespace-shots"
    return os.path.join(REPO, "Saved", "Shots")


def resolve(path):
    """A logical or legacy shots path to a file path; any other path is returned as it is (relative to the repo)."""
    rest = None
    if path.startswith(PREFIX):
        rest = path[len(PREFIX):]
    else:
        for legacy in LEGACY:
            if path.startswith(legacy):
                rest = path[len(legacy):]
    if rest is None:
        return path if os.path.isabs(path) else os.path.join(REPO, path)
    first = os.path.join(root(), rest)
    if os.path.exists(first):
        return first
    old = os.path.join(REPO, "Saved", "Shots", rest)      # a set taken before the move, not yet moved
    return old if os.path.exists(old) else first


def logical(path):
    """A file under the shots root as "shots:<set>/<file>" (for review.json)."""
    rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root()))
    return PREFIX + rel.replace("\\", "/")


if __name__ == "__main__":
    print(root() if len(sys.argv) < 2 else resolve(sys.argv[1]))
