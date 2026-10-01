"""Triangle budget of each ship's main exterior mesh (author 1. 10. 2026, Docs/Reviews/2026-10-01_wayfarer_triangle_budget.md;
plain Python, runs in Tools/Test.ps1 and CI):

    python Tools/Tests/test_triangle_budget.py

Reads ArtSource/Ships/<Ship>/Export/<Ship>_budget.json, written by Tools/Blender/hs_assemble_ship.py from the recipe's
"budget" block (HSBUDGET). The total over "error" (the exporter's limit, 1 M) fails; over "warn" (700 k) is a warning,
like a part over its "max" (the part then eats the reserve). A ship whose recipe has a budget but no report fails
(rebuild it). Prints BUDGET PASS|WARN|FAIL lines and BUDGET SUMMARY; exit code 1 on a failure.
"""
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    failures = 0
    for recipe_path in sorted(glob.glob(os.path.join(REPO, "ArtSource", "Ships", "*", "HardSurface", "*_hs.json"))):
        recipe = json.load(open(recipe_path, encoding="utf-8"))
        if not recipe.get("budget"):
            continue
        ship = os.path.basename(recipe_path)[:-len("_hs.json")]
        rep_path = os.path.join(REPO, "ArtSource", "Ships", ship, "Export", "%s_budget.json" % ship)
        if not os.path.isfile(rep_path):
            print("BUDGET FAIL %s has a budget but no report (rebuild: hs_assemble_ship.py writes %s)"
                  % (ship, os.path.relpath(rep_path, REPO)))
            failures += 1
            continue
        rep = json.load(open(rep_path, encoding="utf-8"))
        spec = recipe["budget"]
        total = rep["total"]
        if total > spec["error"]:
            print("BUDGET FAIL %s main mesh %d triangles, over the limit %d" % (ship, total, spec["error"]))
            failures += 1
        elif total > spec["warn"]:
            print("BUDGET WARN %s main mesh %d triangles, over the budget %d" % (ship, total, spec["warn"]))
        else:
            print("BUDGET PASS %s main mesh %d triangles (budget %d)" % (ship, total, spec["total"]))
        for p in spec["parts"]:
            got = rep["parts"].get(p["name"], {}).get("tris", 0)
            print("BUDGET %s %s %s %d / %d" % ("PASS" if got <= p["max"] else "WARN", ship, p["name"], got, p["max"]))
        print("BUDGET INFO %s other %d (from the reserve)" % (ship, rep["parts"].get("other", {}).get("tris", 0)))
    print("BUDGET SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
