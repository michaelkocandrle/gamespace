"""The interior drawings agree with the data the ship is built from (dossier bod 4, author 1. 10. 2026: one source of
data - the drawing contains nothing that is not in the data and the data nothing that is not in the drawing; every kit
part, piece of furniture, door, decal and light carries the ID it has in the data).

    python Tools/Tests/test_interior_drawing.py      (plain Python; no FBX, no matplotlib, no Blender, no Unreal)

Per ship with Design/<Ship>_interior_design.json (Tools/Design/interior_model.py, draw_interior_sheet.py):
  1. every interior element has an ID (Tools/Design/assign_interior_ids.py --check): the layout's objects and doors,
     the kit parts (ids.kit [id, part] still matching the recipe's runs), the interior decals; the IDs are unique;
  2. every kit part used has a Czech purpose, every component its access and replacement, every door its leaf
     (built, proposed or none), every decal item used a Czech purpose; furniture from the kit builds a layout object;
  3. each room sheet (sidecar <Ship>_I*.json) was drawn from the current data (the digests of the interior's data);
  4. each view of a room sheet draws exactly the elements the model puts in it (interior_model.sheet_views) and
     labels every one; the schedules list every element of the room;
  5. the deck sheet (I-01, interior_model.deck_views) likewise, its tables list every room, door, piece of furniture,
     component and object.
Prints INTDRAW PASS|FAIL lines and INTDRAW SUMMARY.
"""
import glob
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "Tools", "Design"))
failures = []


def check(name, ok, detail=""):
    print("INTDRAW %s %s%s" % ("PASS" if ok else "FAIL", name, (" (%s)" % detail) if detail else ""))
    if not ok:
        failures.append(name)


def diff(a, b):
    a, b = set(a), set(b)
    out = []
    if a - b:
        out.append("only in the drawing: " + ", ".join(sorted(a - b)[:10]))
    if b - a:
        out.append("only in the data: " + ", ".join(sorted(b - a)[:10]))
    return "; ".join(out)


def test_ship(ship):
    import assign_interior_ids
    import interior_model as im

    added, stale = assign_interior_ids.assign(ship, check=True)
    check("%s every interior element has an id" % ship, not added and not stale,
          "; ".join(added[:8] + stale[:4]) + (" - python Tools/Design/assign_interior_ids.py %s" % ship if added or stale else ""))
    try:
        m = im.Model(ship)
    except (KeyError, ValueError) as e:
        check("%s interior model builds (ids unique)" % ship, False, str(e))
        return
    check("%s interior model builds (ids unique)" % ship, True, "%d elements" % len(m.elements))

    used = sorted({p.part for p in m.placements if p.category != "Furniture"})
    missing = [p for p in used if not m.design["kit_purpose"].get(p)]
    check("%s every kit part used has a Czech purpose (furniture: its layout object's)" % ship, not missing, ", ".join(missing))
    comps = [e for e in m.elements if e.cat == "component"]
    bad = [e.id for e in comps if not (e.extra.get("access") and e.extra.get("replace"))]
    check("%s every component has its access and replacement" % ship, not bad, ", ".join(bad))
    doors = [e for e in m.elements if e.cat == "door"]
    bad = [e.id for e in doors if (e.extra.get("leaf") or {}).get("leaf") not in ("built", "proposed", "none")]
    check("%s every door has its leaf (built, proposed or none)" % ship, not bad, ", ".join(bad))
    items = sorted({e.extra["item"] for e in m.elements if e.cat == "decal" and e.extra.get("item") and not e.extra.get("grime")
                    and not e.extra.get("projected") and e.extra["item"] != "scatter"})
    bad = [i for i in items if not (m.design.get("decal_items") or {}).get(i)]
    check("%s every decal item used has a Czech purpose" % ship, not bad, ", ".join(bad))
    bad = [e.id for e in m.elements if e.cat == "decal" and e.extra.get("projected") and e.status != "remove"
           and not (m.design.get("purposes") or {}).get(e.id)]
    check("%s every projected interior decal has a Czech purpose" % ship, not bad, ", ".join(bad))
    furn = [e for e in m.elements if e.cat == "furniture" and e.kit]
    bad = [e.id for e in furn if m.layout_object(e.id) is None or not m.layout_object(e.id).get("purpose")]
    check("%s every kit furniture builds a layout object with a purpose" % ship, not bad, ", ".join(bad))

    drawings = os.path.join(REPO, "ArtSource", "Ships", ship, "Design", "Drawings")
    sheets = sorted(glob.glob(os.path.join(drawings, "%s_I[0-9][0-9]_*.json" % ship)))
    check("%s has interior sheets" % ship, bool(sheets))
    for path in sheets:
        side = json.load(open(path, encoding="utf-8"))
        name = side["sheet"]
        stale_d = [k for k, v in m.digests.items() if side["digests"].get(k) != v]
        check("%s %s drawn from the current data" % (ship, name), not stale_d,
              (("redraw: python Tools/Design/draw_interior_deck.py %s (changed: %s)" % (ship, ", ".join(stale_d))) if side.get("deck") else
               "redraw: python Tools/Design/draw_interior_sheet.py %s --sheets %s (changed: %s)" % (ship, name, ", ".join(stale_d)))
              if stale_d else "")
        if side.get("deck"):
            test_deck_sheet(m, ship, name, side)
            continue
        if not side.get("room"):
            continue
        views = m.sheet_views(side["room"], side["section_x"])
        for view, expected in views.items():
            drawn = set(side["drawn"].get(view, []))
            check("%s %s view %s draws the model's elements" % (ship, name, view), drawn == expected, diff(drawn, expected))
            lab = set(side["labelled"].get(view, []))
            check("%s %s view %s labels everything it draws" % (ship, name, view), drawn <= lab,
                  ", ".join(sorted(drawn - lab)[:10]))
        room = side["room"]
        els = {e.id for e in m.elements if (e.room == room or room in (e.extra.get("rooms") or ())) and e.status != "remove"}
        listed = set().union(*[set(v) for v in side["schedules"].values()]) if side["schedules"] else set()
        check("%s %s schedules list every element of the room" % (ship, name), els <= listed,
              ", ".join(sorted(els - listed)[:10]))


def test_deck_sheet(m, ship, name, side):
    """The deck sheet (I-01): each view draws exactly what interior_model.deck_views puts in it and labels it all; the
    tables list every room, every door and every piece of furniture, component and object the plan shows."""
    views = m.deck_views(side["section_y"])
    for view, expected in views.items():
        drawn = set(side["drawn"].get(view, []))
        check("%s %s view %s draws the model's elements" % (ship, name, view), drawn == expected, diff(drawn, expected))
        lab = set(side["labelled"].get(view, []))
        check("%s %s view %s labels everything it draws" % (ship, name, view), drawn <= lab, ", ".join(sorted(drawn - lab)[:10]))
    sch = side["schedules"]
    check("%s %s lists every room" % (ship, name), set(sch.get("rooms", [])) == set(m.rooms), diff(sch.get("rooms", []), m.rooms))
    doors = {e.id for e in m.elements if e.cat == "door"}
    check("%s %s lists every door" % (ship, name), set(sch.get("doors", [])) == doors, diff(sch.get("doors", []), doors))
    items = {i for i in views["PLAN"] if m.by_id[i].cat in ("furniture", "component", "object")}
    check("%s %s lists the plan's furniture, components and objects" % (ship, name), set(sch.get("items", [])) == items,
          diff(sch.get("items", []), items))


def main():
    root = os.path.join(REPO, "ArtSource", "Ships")
    ships = sorted(s for s in os.listdir(root)
                   if os.path.isfile(os.path.join(root, s, "Design", "%s_interior_design.json" % s)))
    for ship in ships:
        test_ship(ship)
    print("INTDRAW SUMMARY %s (%d ships, %d failures)" % ("FAIL" if failures else "PASS", len(ships), len(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
