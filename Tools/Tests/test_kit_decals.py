"""The exterior kit's mesh decals (triangle budget rule A, author 1. 10. 2026; plain Python, Tools/Test.ps1 and CI):

    python Tools/Tests/test_kit_decals.py

Reads ArtSource/Ships/<Ship>/Export/<Ship>_decals.json, written by Tools/Blender/hs_assemble_ship.py (hs_decals.kit_check):
  1. every kit bolt the build asked for is laid as a decal (bolts_placed == bolts_wanted);
  2. no companion label (component labels such as REACTOR S1, handles, markers) lies within 0.3 m of a kit hatch or latch - the
     companion rules once dressed the kit's hatch latches with foreign labels (step b trial);
  3. two rebuilds in a row put the random decals (clusters, companions such as dirt streaks, coverage, panel lines) of the
     same element in the same place: every element key placed by both builds has the same item and point (1 cm: the
     hull's mesh noise moves a ray's hit by millimetres). The
     report keeps the previous build's placements ("random_prev"); skipped when there is none yet or the random rules'
     inputs (seed, rules) changed - then rebuild twice. A kit change once re-rolled the streak beside RAMP - STAND CLEAR.
A ship whose recipe has no exterior_kit.decal_detail is skipped. Prints KITDECAL PASS|FAIL lines and KITDECAL SUMMARY.
"""
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# "the same place": the hull's own mesh noise between two builds (WORKFLOW 9.6 ff, +-40 triangles) moves a ray's hit by
# up to ~8 mm along the ray (belly coverage, 2. 10. 2026); a re-rolled decal moves by decimetres or changes its item
TOL_M = 0.01


def check_rebuild(ship, rep):
    """Random decals of the same element in the same place after two rebuilds; returns the number of failures."""
    cur, prev = rep.get("random"), rep.get("random_prev")
    if not cur or not prev:
        print("KITDECAL SKIP %s random decals: no previous build to compare (rebuild once more)" % ship)
        return 0
    if cur["rules_hash"] != prev["rules_hash"]:
        print("KITDECAL SKIP %s random decals: seed or rules changed since the previous build (rebuild once more)" % ship)
        return 0
    a, b = cur["placed"], prev["placed"]
    common = sorted(set(a) & set(b))
    moved = []
    for k in common:
        ia, ib = a[k].split(), b[k].split()
        same = ia[0] == ib[0] and len(ia) == len(ib) and all(abs(float(u) - float(v)) <= TOL_M for u, v in zip(ia[1:], ib[1:]))
        if not same:
            moved.append(k)
    print("KITDECAL %s %s random decals stable over two rebuilds: %d common, %d moved, %d only now, %d only before%s" % (
        "PASS" if not moved else "FAIL", ship, len(common), len(moved), len(set(a) - set(b)), len(set(b) - set(a)),
        (" (" + ", ".join(moved[:5]) + ")") if moved else ""))
    return 1 if moved else 0


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
        failures += check_rebuild(ship, json.load(open(rep_path, encoding="utf-8")))
    print("KITDECAL SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
