"""The exterior kit's mesh decals (triangle budget rule A, author 1. 10. 2026; plain Python, Tools/Test.ps1 and CI):

    python Tools/Tests/test_kit_decals.py

Reads ArtSource/Ships/<Ship>/Export/<Ship>_decals.json, written by Tools/Blender/hs_assemble_ship.py (hs_decals.kit_check):
  1. every kit bolt the build asked for is laid as a decal (bolts_placed == bolts_wanted);
  2. no companion label (component labels such as REACTOR S1, handles, markers) lies within 0.3 m of a kit hatch or latch - the
     companion rules once dressed the kit's hatch latches with foreign labels (step b trial).
A ship whose recipe has no exterior_kit.decal_detail is skipped. Prints KITDECAL PASS|FAIL lines and KITDECAL SUMMARY.
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
        if not recipe.get("exterior_kit", {}).get("decal_detail"):
            continue
        ship = os.path.basename(recipe_path)[:-len("_hs.json")]
        rep_path = os.path.join(REPO, "ArtSource", "Ships", ship, "Export", "%s_decals.json" % ship)
        if not os.path.isfile(rep_path):
            print("KITDECAL FAIL %s has kit decals but no report (rebuild: hs_assemble_ship.py)" % ship)
            failures += 1
            continue
        kit = json.load(open(rep_path, encoding="utf-8"))["kit"]
        ok = kit["bolts_placed"] == kit["bolts_wanted"]
        failures += 0 if ok else 1
        print("KITDECAL %s %s kit bolts laid %d / %d" % ("PASS" if ok else "FAIL", ship, kit["bolts_placed"], kit["bolts_wanted"]))
        # what the companion rule hangs on hatches (labels, handle, red marker); a cap's chevron bracket belongs to the
        # cap (reports written before this filter moved into hs_decals.kit_check still list it)
        near = [n for n in kit["companion_items_near_kit"] if n not in ("chevrons_port", "streak_drip", "streak_short")]
        ok = not near
        failures += 0 if ok else 1
        print("KITDECAL %s %s no companion labels by kit decals (%d: %s)" % ("PASS" if ok else "FAIL", ship,
              len(near), ", ".join(near)))
    print("KITDECAL SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
