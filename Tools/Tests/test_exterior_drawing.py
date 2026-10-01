"""The exterior drawings agree with the data the ship is built from (author 1. 10. 2026: one source of data - the
drawing contains nothing that is not in the data and the data nothing that is not in the drawing; every kit part,
decal and light carries the ID it has in the data).

    python Tools/Tests/test_exterior_drawing.py      (plain Python + shapely; no matplotlib, no Blender, no Unreal)

Per ship with Design/Drawings/<Ship>_E01_starboard.json (written by Tools/Design/draw_exterior_sheet.py):
  1. every element of the build data has an ID (Tools/Design/assign_exterior_ids.py --check), the IDs are unique;
  2. the sheet was drawn from the current data (the digests in its sidecar);
  3. view A draws exactly the model's plates, zones, recesses, frame and parts seen from starboard, view B exactly
     its functional parts, greebles, lights, decals and trims; every drawn ID is labelled (in A, B or detail A);
  4. the schedules list every functional part, greeble, light, kit part, material, decal rule and change;
  5. the design data only changes or removes built elements, and its new IDs are not built ones;
  6. after the design the ship has as many RCS blocks as the spec's manoeuvring thrusters;
  7. every text decal on the starboard view reads upright; every library item exists;
  8. every built element in the schedules has a Czech purpose (design data "purpose") for the author;
  9. no part on the hull side lies under a proposed plate without a cut-out (plates are 30-40 mm proud), no
     lettering sits on a background of its own tone (critic round 2, 1. 10. 2026).
Prints EXTDRAW PASS|FAIL lines and EXTDRAW SUMMARY.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "Tools", "Design"))
failures = []


def check(name, ok, detail=""):
    print("EXTDRAW %s %s%s" % ("PASS" if ok else "FAIL", name, (" (%s)" % detail) if detail else ""))
    if not ok:
        failures.append(name)


def diff(a, b):
    a, b = set(a), set(b)
    out = []
    if a - b:
        out.append("only in the drawing: " + ", ".join(sorted(a - b)[:12]))
    if b - a:
        out.append("only in the data: " + ", ".join(sorted(b - a)[:12]))
    return "; ".join(out)


def test_ship(ship):
    import assign_exterior_ids
    import exterior_model as em

    base = os.path.join(REPO, "ArtSource", "Ships", ship)
    for path, kind in ((os.path.join(base, "HardSurface", "%s_hs.json" % ship), "recipe"),
                       (os.path.join(base, "%s_setup.json" % ship), "setup")):
        missing = assign_exterior_ids.process(path, kind, check=True)
        check("%s %s: every element has an id" % (ship, os.path.basename(path)), not missing, ", ".join(missing[:8]))
    try:
        m = em.Model(ship)
    except (KeyError, ValueError) as e:
        check("%s model builds (unique ids, library items, cuts)" % ship, False, str(e))
        return
    check("%s model builds (unique ids, library items, cuts)" % ship, True, "%d elements" % len(m.elements))

    side = json.load(open(os.path.join(base, "Design", "Drawings", "%s_E01_starboard.json" % ship), encoding="utf-8"))
    stale = [k for k, v in m.digests.items() if side["digests"].get(k) != v]
    check("%s E-01 drawn from the current data" % ship, not stale,
          ("redraw: python Tools/Design/draw_exterior_sheet.py %s (changed: %s)" % (ship, ", ".join(stale))) if stale else "")

    for view, cats in em.SHEET_E01.items():
        expected = {e.id for e in m.elements if e.sb and e.cat in cats}
        drawn = set(side["drawn"].get(view, []))
        check("%s E-01 view %s draws the model's %s" % (ship, view, "/".join(sorted(cats))), drawn == expected,
              diff(drawn, expected))
    drawn = set(side["drawn"].get("A", [])) | set(side["drawn"].get("B", []))
    labelled = set()
    for v in side["labelled"].values():
        labelled |= set(v)
    check("%s E-01 every drawn ID is labelled" % ship, drawn <= labelled, ", ".join(sorted(drawn - labelled)[:12]))

    sch = side["schedules"]
    lists = {
        "functional": {e.id for e in m.elements if e.cat in ("functional", "part") and not e.id.startswith("P-")},
        "greebles": {e.id for e in m.elements if e.cat == "greeble"},
        "lights": {e.id for e in m.elements if e.cat == "light"},
        "kit": {e.id for e in m.elements if e.cat == "kit"},
        "materials": {e.id for e in m.elements if e.cat == "material"},
        "rules": {e.id for e in m.elements if e.cat == "rule"},
        "decals": {e.id for e in m.elements if e.cat in ("decal", "trim") and e.sb},
        "changes": {e.id for e in m.elements if e.status in ("change", "remove") and e.cat not in ("decal", "trim")},
    }
    for k, ids in lists.items():
        check("%s E-01 schedule %s lists the data" % (ship, k), set(sch.get(k, [])) == ids, diff(sch.get(k, []), ids))

    scheduled_built = [e for e in m.elements if e.src != "design" and (
        e.cat in ("functional", "greeble", "light", "rule") or (e.cat == "part" and not e.id.startswith("P-"))
        or (e.cat in ("decal", "trim") and e.sb))]
    no_purpose = [e.id for e in scheduled_built if not (e.why or e.purpose)]
    check("%s every scheduled built element has a Czech purpose (design 'purpose')" % ship, not no_purpose,
          ", ".join(no_purpose[:12]))

    conflicts = m.conflicts()
    buried = ["%s (%s)" % (i, t) for i, items in conflicts.items() for k, t in items if k == "buried"]
    check("%s no part on the hull side lies under a proposed plate without a cut-out" % ship, not buried, "; ".join(buried[:6]))
    covered = ["%s (%s)" % (i, t) for i, items in conflicts.items() for k, t in items if k == "covered"]
    check("%s no lettering covered by a part" % ship, not covered, "; ".join(covered[:6]))
    ink = ["%s (%s)" % (i, t) for i, items in conflicts.items() for k, t in items if k == "ink"]
    check("%s no lettering on a background of its own tone" % ship, not ink, "; ".join(ink[:6]))

    built = {e.id for e in m.elements if e.src in ("recipe", "setup")}
    for c in m.design.get("changes", []):
        check("%s design change %s targets a built element" % (ship, c["id"]), c["id"] in built)
    new = [e.id for e in m.elements if e.src == "design" and e.cat not in ("material", "kit")]
    check("%s design IDs are new (not built)" % ship, not (set(new) & built), ", ".join(sorted(set(new) & built)))
    kits = {k["id"] for k in m.design["kit"]}
    bad_kit = [e.id for e in m.elements if e.kit and e.kit.startswith("XK") and e.kit not in kits]
    check("%s every XK kit part used exists" % ship, not bad_kit, ", ".join(bad_kit))
    bad_mat = [e.id for e in m.elements if e.material and e.material not in m.materials]
    check("%s every material zone used exists" % ship, not bad_mat, ", ".join(bad_mat))

    spec = m.spec_rcs()
    check("%s RCS blocks after the design = spec manoeuvring thrusters" % ship, spec is not None and m.rcs_blocks() == spec,
          "%d blocks, spec %s" % (m.rcs_blocks(), spec))

    lib = m.library["decals"]
    unknown = [e.id for e in m.elements if e.cat == "decal" and e.src == "recipe" and e.extra.get("item") not in lib]
    check("%s every decal item is in the library" % ship, not unknown, ", ".join(unknown))
    down = [e.id for e in m.elements if e.cat == "decal" and e.sb and e.extra.get("text") and e.extra.get("up")
            and e.extra["up"][1] <= 0.5 and e.status != "remove"]
    check("%s text decals on the starboard view read upright" % ship, not down, ", ".join(down))


def main():
    try:
        import shapely  # noqa: F401
    except ImportError:
        check("shapely installed (python -m pip install shapely)", False)
        print("EXTDRAW SUMMARY FAIL (1 failures)")
        return 1
    ships = 0
    for ship in sorted(os.listdir(os.path.join(REPO, "ArtSource", "Ships"))):
        if os.path.isfile(os.path.join(REPO, "ArtSource", "Ships", ship, "Design", "Drawings", "%s_E01_starboard.json" % ship)):
            ships += 1
            test_ship(ship)
    check("at least one ship has exterior drawings", ships > 0)
    print("EXTDRAW SUMMARY %s (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
