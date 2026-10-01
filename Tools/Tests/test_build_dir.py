"""Tools/BuildDir.ps1: each checkout packages into its own folder (author 1. 10. 2026) - the main checkout
gamespace into Builds, a worktree gamespace-<name> into Builds_<name> (the second session: Builds_audit). Runs the
script from copies in a temporary folder laid out like C:\\gamespace.

    python Tools/Tests/test_build_dir.py      (Windows PowerShell or pwsh)

Prints BUILDDIR PASS|FAIL lines and BUILDDIR SUMMARY.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHELL = shutil.which("powershell") or shutil.which("pwsh")
failures = []


def check(name, ok, detail=""):
    print("BUILDDIR %s %s%s" % ("PASS" if ok else "FAIL", name, (" (%s)" % detail) if detail else ""))
    if not ok:
        failures.append(name)


def main():
    if not SHELL:
        check("PowerShell available", False)
        print("BUILDDIR SUMMARY FAIL (1 failures)")
        return 1
    root = tempfile.mkdtemp(prefix="builddir_")
    try:
        for checkout, expected in (("gamespace", "Builds"), ("gamespace-audit", "Builds_audit"),
                                   ("gamespace-kit", "Builds_kit")):
            tools = os.path.join(root, checkout, "Tools")
            os.makedirs(tools)
            shutil.copy(os.path.join(REPO, "Tools", "BuildDir.ps1"), tools)
            out = subprocess.run([SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                                  "& '%s'" % os.path.join(tools, "BuildDir.ps1")],
                                 capture_output=True, text=True, timeout=60).stdout.strip()
            want = os.path.join(root, expected, "Gamespace")
            check("%s packages into %s" % (checkout, expected), os.path.normcase(out) == os.path.normcase(want), out)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("BUILDDIR SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
