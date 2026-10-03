"""The exterior drawings agree with the data the ship is built from (author 1. 10. 2026: one source of data - the
drawing contains nothing that is not in the data and the data nothing that is not in the drawing; every kit part,
decal and light carries the ID it has in the data).

    python Tools/Tests/test_exterior_drawing.py      (plain Python + shapely; no matplotlib, no Blender, no Unreal)

Per ship with Design/Drawings/<Ship>_E01_starboard.json and _E02_schedules.json (Tools/Design/draw_exterior_sheet.py):
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
     lettering sits on a background of its own tone (critic round 2, 1. 10. 2026);
 10. the other views (E-03 from above, E-04 from below, E-05 from behind and ahead, E-06 port side; author
     1. 10. 2026: the rest of dossier point 3) each draw exactly the elements the model has in that view
     (exterior_views) and label every one; every view tag the model sets has geometry; the details of E-07 label
     their key parts; the port side's lettering reads upright.
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

    drawings = os.path.join(base, "Design", "Drawings")
    side = json.load(open(os.path.join(drawings, "%s_E01_starboard.json" % ship), encoding="utf-8"))
    tables_path = os.path.join(drawings, "%s_E02_schedules.json" % ship)
    check("%s E-02 (the tables) exists" % ship, os.path.isfile(tables_path))
    tables = json.load(open(tables_path, encoding="utf-8")) if os.path.isfile(tables_path) else {"digests": {}, "schedules": {}}
    stale = [k for k, v in m.digests.items() if side["digests"].get(k) != v or tables["digests"].get(k) != v]
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

    sch = {}
    for sc in (side.get("schedules", {}), tables["schedules"]):
        for k, v in sc.items():
            sch.setdefault(k, set()).update(v)
    lists = {
        "functional": {e.id for e in m.elements if e.cat in ("functional", "part") and not e.id.startswith("P-")},
        "greebles": {e.id for e in m.elements if e.cat == "greeble"},
        "lights": {e.id for e in m.elements if e.cat == "light"},
        "kit": {e.id for e in m.elements if e.cat == "kit"},
        "materials": {e.id for e in m.elements if e.cat == "material"},
        "rules": {e.id for e in m.elements if e.cat == "rule"},
        "decals": {e.id for e in m.elements if e.cat in ("decal", "trim")},
        "grime": {e.id for e in m.elements if e.cat == "grime"},
        "changes": {e.id for e in m.elements if e.status in ("change", "remove") and e.cat not in ("decal", "trim")},
    }
    for k, ids in lists.items():
        check("%s E-01 schedule %s lists the data" % (ship, k), set(sch.get(k, [])) == ids, diff(sch.get(k, []), ids))

    scheduled_built = [e for e in m.elements if e.src != "design" and (
        e.cat in ("functional", "greeble", "light", "rule") or (e.cat == "part" and not e.id.startswith("P-"))
        or e.cat in ("decal", "trim", "grime"))]
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

    check_views(ship, m, drawings)
    kit_path = os.path.join(base, "Design", "%s_exterior_kit.json" % ship)
    if os.path.isfile(kit_path):
        # the kit layout the Blender kit step builds (Tools/Design/exterior_kit_layout.py) is made from these data,
        # and it builds exactly the plates of the bands the design marks as built
        kit = json.load(open(kit_path, encoding="utf-8"))
        stale = [k for k, v in m.digests.items() if kit["digests"].get(k) != v]
        check("%s kit layout made from the current data" % ship, not stale,
              ("run python Tools/Design/exterior_kit_layout.py %s (changed: %s)" % (ship, ", ".join(stale))) if stale else "")
        built = {e.id for e in m.elements if e.cat == "panel" and e.status == "built"}
        # a small hatch rendered as mesh decals (recipe exterior_kit.decal_detail) is built as a decal with its ID
        laid = {p["id"] for p in kit["plates"]} | {d["id"] for d in kit.get("decals", []) if d["id"] in built}
        check("%s kit layout builds the built plates" % ship, laid == built, diff(laid, built))
        unknown = sorted({p["id"] for p in kit["plates"] + kit["frame"] + kit["parts"]} - set(m.by_id))
        check("%s kit layout IDs are in the data" % ship, not unknown, ", ".join(unknown))
    pc = m.views_model.plan_conflicts()
    check("%s roof from above: no part under a plate without a cut-out" % ship, not [c for c in pc if c[1] == "buried"],
          "; ".join("%s %s" % (i, t) for i, k, t in pc if k == "buried"))
    check("%s roof from above: no lettering on a plate of its own tone" % ship, not [c for c in pc if c[1] == "ink"],
          "; ".join("%s %s" % (i, t) for i, k, t in pc if k == "ink"))

    spec = m.spec_rcs()
    check("%s RCS blocks after the design = spec manoeuvring thrusters" % ship, spec is not None and m.rcs_blocks() == spec,
          "%d blocks, spec %s" % (m.rcs_blocks(), spec))

    lib = m.library["decals"]
    unknown = [e.id for e in m.elements if e.cat == "decal" and e.src == "recipe" and e.extra.get("item") not in lib]
    # and every glyph of the kit layout's texts (plate numbers pn_<glyph>; pn_K was missing, 3. 10. 2026: the build
    # stopped in hs_decals with a KeyError)
    if os.path.isfile(kit_path):
        for d in json.load(open(kit_path, encoding="utf-8")).get("decals", []):
            items = [d.get("prefix", "") + g for g in d["glyphs"]] if "glyphs" in d else [d.get("item")]
            unknown += ["%s (%s)" % (d["id"], i) for i in items if i and i not in lib]
    check("%s every decal item is in the library" % ship, not unknown, ", ".join(unknown))
    down = [e.id for e in m.elements if e.cat == "decal" and e.sb and e.extra.get("text") and e.extra.get("up")
            and e.extra["up"][1] <= 0.5 and e.status != "remove"]
    check("%s text decals on the starboard view read upright" % ship, not down, ", ".join(down))


# sheet: {view key in the sidecar: (model view, categories or None for all)}
VIEW_SHEETS = {
    "E03_top": {"TOP": ("TOP", None)},
    "E04_bottom": {"BOT": ("BOT", None)},
    "E05_ends": {"AFT": ("AFT", None), "FWD": ("FWD", None)},
    "E06_port": {"PA": ("PORT", "A"), "PB": ("PORT", "B")},
}
# E-07 / E-08 details: the parts each must label (author's list: nose with the canopy, ramp with its pistons and
# frame, main gear, gun mount; the pod from the side is E-01 detail A)
DETAIL_KEYS = {"E07_details": {"DB": {"F-CANOPY-FRAME", "Z-SEAL-CANOPY", "Z-B-01", "F-GEAR-NOSE"},
                               "DC": {"D-T-05", "F-RAMP-PISTON", "F-RAMP-FRAME", "L-RAMP", "P-B-07", "F-RAMP-TREAD",
                                      "F-RAMP-HINGE"},
                               "DF": {"F-POD-BAY", "F-FIN", "P-POD-BODY", "L-STROBE-FIN"}},
               "E08_details": {"DD": {"F-GEAR-MAIN"}, "DD-BOT": {"F-GEAR-MAIN", "D-H-27", "D-H-52"},
                               "DE": {"F-GUNMOUNT-01", "F-GUN-S3"}, "DE-A": {"F-GUNMOUNT-01", "F-GUN-S3", "F-WING"}}}


def check_views(ship, m, drawings):
    import exterior_model as em
    check("%s every view tag has geometry in that view" % ship, not m.views_missing,
          ", ".join("%s %s" % t for t in m.views_missing[:10]))
    for name, views in VIEW_SHEETS.items():
        path = os.path.join(drawings, "%s_%s.json" % (ship, name))
        if not os.path.isfile(path):
            check("%s %s exists" % (ship, name), False)
            continue
        side = json.load(open(path, encoding="utf-8"))
        stale = [k for k, v in m.digests.items() if side["digests"].get(k) != v]
        check("%s %s drawn from the current data" % (ship, name), not stale, ", ".join(stale))
        for key, (view, cats) in views.items():
            cs = em.SHEET_E01[cats] if cats else None
            expected = {e.id for e in m.elements if e.geo.get(view) and (cs is None or e.cat in cs)}
            drawn = set(side["drawn"].get(key, []))
            check("%s %s view %s draws the model's %s view" % (ship, name, key, view), drawn == expected,
                  diff(drawn, expected))
            labelled = set(side["labelled"].get(key, []))
            check("%s %s view %s labels every drawn ID" % (ship, name, key), drawn <= labelled,
                  ", ".join(sorted(drawn - labelled)[:12]))
    for name, keys in DETAIL_KEYS.items():
        path = os.path.join(drawings, "%s_%s.json" % (ship, name))
        if not os.path.isfile(path):
            check("%s %s exists" % (ship, name), False)
            continue
        det = json.load(open(path, encoding="utf-8"))
        stale = [k for k, v in m.digests.items() if det["digests"].get(k) != v]
        check("%s %s drawn from the current data" % (ship, name), not stale, ", ".join(stale))
        for key, must in keys.items():
            lab = set(det["labelled"].get(key, []))
            check("%s %s detail %s labels %s" % (ship, name, key, ", ".join(sorted(must))), must <= lab,
                  "missing " + ", ".join(sorted(must - lab)))
            check("%s %s detail %s labels what it draws" % (ship, name, key),
                  set(det["drawn"].get(key, [])) <= lab, ", ".join(sorted(set(det["drawn"].get(key, [])) - lab)[:8]))
    wrong = [i for i, ok in m.port_text_decals() if not ok]
    check("%s port lettering reads upright" % ship, not wrong, ", ".join(wrong))


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
