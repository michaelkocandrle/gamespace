"""Geometry check of the ship under test, run through Blender headless (no Unreal needed).

    python Tools/Tests/test_ship_geometry.py [Ship]

Runs Tools/Blender/check_ship_geometry.py on ArtSource/Ships/<Ship>/<Ship>_HS_Game.blend (the assembled ship the
game imports) and fails on any of:
  - mirrored decals (mesh decals with a flipped UV frame, projected decals seen from behind)
  - floating parts (islands touching nothing)
  - penetrations (parts behind the cockpit's frame lining or outside the hull)
  - placeholder materials (no material, default material)
  - holes the player can see (the world through the ship from the eye and the interior shot cameras)
Must pass before every handover to the author (author 25. 9. 2026). Warnings (large plain faces) are printed,
not failed. Report and masks: Saved/GeoCheck/ (geocheck.json, holes_<view>.png; with GEOCHECK_DEBUG=1 also
holes_<view>_obj.png in random colours per object).
Prints "GEOTEST PASS" / "GEOTEST FAIL" lines and a summary.
"""

import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BLENDER = os.environ.get("BLENDER", r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
CATEGORIES = ("mirrored_decals", "floating", "penetrating", "placeholders", "holes")


def ship_under_test():
    # ship_under_test.py imports unreal; read its SHIP line instead
    src = open(os.path.join(REPO, "Tools", "Tests", "ship_under_test.py"), encoding="utf-8").read()
    m = re.search(r'^SHIP = "([^"]+)"', src, re.M)
    return m.group(1) if m else None


def main():
    ship = sys.argv[1] if len(sys.argv) > 1 else ship_under_test()
    if not ship:
        print("GEOTEST SKIP no ship model yet")
        return 0
    blend = os.path.join(REPO, "ArtSource", "Ships", ship, "%s_HS_Game.blend" % ship)
    if not os.path.isfile(blend):
        print("GEOTEST FAIL missing %s" % blend)
        return 1
    out = os.path.join(REPO, "Saved", "GeoCheck")
    report = os.path.join(out, "geocheck.json")
    if os.path.isfile(report):
        os.remove(report)
    run = subprocess.run([BLENDER, "-b", blend, "--python", os.path.join(REPO, "Tools", "Blender", "check_ship_geometry.py"),
                          "--", ship, out], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not os.path.isfile(report):
        print(run.stdout[-3000:])
        print(run.stderr[-3000:])
        print("GEOTEST FAIL the check wrote no report (exit %d)" % run.returncode)
        return 1
    r = json.load(open(report, encoding="utf-8"))
    failed = []
    for k in CATEGORIES:
        items = r.get(k, [])
        ok = not items
        print("GEOTEST %s %s (%d)" % ("PASS" if ok else "FAIL", k, len(items)))
        for it in items[:8]:
            print("    " + json.dumps(it))
        if not ok:
            failed.append(k)
    for w in r.get("warnings", []):
        print("GEOTEST WARN " + json.dumps(w))
    print("GEOTEST SUMMARY %s: %s" % (ship, "PASS" if not failed else "FAIL " + ", ".join(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
