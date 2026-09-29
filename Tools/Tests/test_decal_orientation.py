"""Orientation of every projected marking in the ships' setups (<Ship>_setup.json "decals"), without a picture:
text that reads backwards got through one commit unnoticed (the Wayfarer's REACTOR, CAUTION and COOLER, 28. 9. 2026 -
author 29. 9.: "a test that guards the decals' orientation in the setup").

    python Tools/Tests/test_decal_orientation.py      (plain Python; also runs inside the editor's Python)

Two rules per marking (import_ship.add_decal_component places them; M_Ship_Decal maps the texture):
  1. The viewer side: a decal projects along its component's -X, so X points away from the surface towards whoever
     reads it - into the room that holds an interior marking (Int_*, the room from <Ship>_layout.json), away from the
     ship's centre for a hull marking. Backwards it projects into the wall behind, or reads from the far side.
  2. The mirror: a rotation cannot mirror, so with X towards the viewer only the flips decide. In M_Ship_Decal the
     texture reads the right way round with exactly one of flip_u / flip_v set (U·V = -1: ENGINEERING, COCKPIT, EXIT,
     the hull names); none or both read mirrored (REACTOR / COOLER before the fix). A marking that reads the same
     mirrored (hazard stripes) says "symmetric": true.
The flips must be written in the setup: build_decal_instances sets DecalFlipU/V only when the setup has them, so a
missing flip keeps whatever an older instance held - until the instance is made anew (test_ship_import compares).
Prints DECALTEST PASS|FAIL lines and DECALTEST SUMMARY.
"""
import json
import math
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHIPS = os.path.join(REPO, "ArtSource", "Ships")
failures = []


def check(name, ok, detail=""):
    print("DECALTEST %s %s%s" % ("PASS" if ok else "FAIL", name, (" (%s)" % detail) if detail else ""))
    if not ok:
        failures.append(name)


def x_axis(rotation):
    """The component's X in ship space from the setup's [pitch, yaw, roll] (degrees; import_ship's order)."""
    pitch, yaw = (list(rotation) + [0.0, 0.0, 0.0])[:2]
    p, y = math.radians(pitch), math.radians(yaw)
    return (math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p))


def flip_sign(spec, key):
    return -1 if float(spec.get(key, 0.0)) >= 0.5 else 1


def to_layout(loc_cm, offset):
    """Ship space (Unreal cm, +Y to starboard) to layout metres (x forward, y to port, z from the deck)."""
    return (loc_cm[0] / 100.0 - offset[0], -loc_cm[1] / 100.0 - offset[1], loc_cm[2] / 100.0 - offset[2])


def room_of(rooms, p):
    for r in rooms:
        x0, x1, y0, y1 = r["rect"]
        if x0 - 0.02 <= p[0] <= x1 + 0.02 and y0 - 0.02 <= p[1] <= y1 + 0.02:
            return r
    return None


def main():
    ships = 0
    for ship in sorted(os.listdir(SHIPS)):
        setup_path = os.path.join(SHIPS, ship, "%s_setup.json" % ship)
        if not os.path.isfile(setup_path):
            continue
        setup = json.load(open(setup_path, encoding="utf-8"))
        decals = setup.get("decals") or []
        if not decals:
            continue
        ships += 1
        layout_path = os.path.join(SHIPS, ship, "Design", "%s_layout.json" % ship)
        recipe_path = os.path.join(SHIPS, ship, "HardSurface", "%s_hs.json" % ship)
        rooms, offset = [], None
        if os.path.isfile(layout_path) and os.path.isfile(recipe_path):
            rooms = json.load(open(layout_path, encoding="utf-8")).get("rooms", [])
            recipe = json.load(open(recipe_path, encoding="utf-8"))
            offset = recipe.get("assemble", {}).get("offset")
            # a kit room as wide as its hull liner (kit_modules.width): the labels on the liner lie in it
            mods = (recipe.get("interior") or {}).get("kit_modules") or {}
            if mods.get("enabled", True):
                widths = {r: w for r, w in (mods.get("width") or {}).items() if r in mods.get("rooms", [])}
                rooms = [dict(r, rect=[r["rect"][0], r["rect"][1], -widths[r["id"]] / 2, widths[r["id"]] / 2]) if r["id"] in widths else r
                         for r in rooms]
        for d in decals:
            name = "%s %s" % (ship, d["name"])
            X = x_axis(d.get("rotation", [0.0, 0.0, 0.0]))
            loc = d["location"]
            # rule 1: towards the viewer
            if d["name"].startswith("Int_"):
                if offset is None or not rooms:
                    check("%s: the viewer's room is known" % name, False, "no layout or recipe offset")
                    continue
                p = to_layout(loc, offset)
                room = room_of(rooms, p)
                if room is None:
                    check("%s: lies in a room of the layout" % name, False, "layout point %.2f, %.2f" % (p[0], p[1]))
                    continue
                x0, x1, y0, y1 = room["rect"]
                # the room's middle at eye height, in ship space (Unreal cm)
                cx, cy, cz = (x0 + x1) / 2 + offset[0], -((y0 + y1) / 2 + offset[1]), 1.1 + offset[2]
                to_viewer = (cx * 100.0 - loc[0], cy * 100.0 - loc[1], cz * 100.0 - loc[2])
                where = "room %s" % room["id"]
            else:
                to_viewer = (loc[0], loc[1], loc[2])        # away from the ship's centre (its origin)
                where = "outside"
            facing = sum(a * b for a, b in zip(X, to_viewer))
            check("%s: X towards the viewer (%s)" % (name, where), facing > 0.0,
                  "X %.2f %.2f %.2f" % X)
            # rule 2: the mirror
            if d.get("symmetric"):
                continue
            product = flip_sign(d, "flip_u") * flip_sign(d, "flip_v")
            check("%s: reads the right way round (one of flip_u / flip_v)" % name, product == -1,
                  "flip_u %s, flip_v %s" % (d.get("flip_u", "missing"), d.get("flip_v", "missing")))
    check("setups with markings checked (%d)" % ships, ships > 0)
    print("DECALTEST SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    return 1 if failures else 0


if __name__ == "__main__" or __name__ == "test_decal_orientation":
    main()
