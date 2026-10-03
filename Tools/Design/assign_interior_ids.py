"""Gives every element of a ship's interior an ID (dossier bod 4, author 1. 10. 2026: the drawings and the build read
the same data, and every kit part, piece of furniture, door, decal and light carries the ID it has in the data).

    python Tools/Design/assign_interior_ids.py Wayfarer            # adds the missing IDs, prints what it added
    python Tools/Design/assign_interior_ids.py Wayfarer --check    # exit 1 when an element has no ID

The IDs live in Design/<Ship>_interior_design.json "ids", bound to the build data by a key the test checks, so the
build files the exterior drawings digest stay untouched (a recipe edit would make every exterior sheet stale):
  objects {layout object name: id}       <ROOM>-M-nn a ship component ("S1" in its name or under the floor), else
                                         <ROOM>-O-nn
  doors {layout door name: id}           DR-nn
  kit {wall_runs, run_parts}             [id, part] pairs parallel to the recipe's interior.kit_modules runs
                                         (interior_model.proposed_kit_ids: <ROOM>-W-<L|R><n>, <ROOM>-B-<A|F>,
                                         <ROOM>-C-<n>, <ROOM>-FL-<n>, furniture = its layout object's ID)
  decals {items [[item, id]], scatter [id], grab_bars [id]}   interior.decals: D-I-nn, D-I-R-SCATTER-nn,
                                         <ROOM>-O-GRAB-nn
  fittings [[type, id]]                  parallel to interior.kit.fittings: <ROOM>-O-<FIRE|RAIL|VENT|JBOX|COND>-nn
IDs already given are never changed; a pair whose key no longer matches the build data (a module swapped) is
replaced. <ROOM> is the room's code in "rooms". Lights and the kit parts' own decals take the ID of their part plus
the socket or decal item (interior_model.py).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))


def dump(o, ind=0, width=118):
    """JSON with dicts one key per line and short lists on one line (the design data stays readable in diffs)."""
    pad = " " * (ind + 1)
    if isinstance(o, dict):
        if not o:
            return "{}"
        return "{\n" + ",\n".join(pad + json.dumps(k, ensure_ascii=False) + ": " + dump(v, ind + 1, width)
                                  for k, v in o.items()) + "\n" + " " * ind + "}"
    if isinstance(o, list):
        flat = json.dumps(o, ensure_ascii=False)
        if len(flat) + ind <= width or all(not isinstance(v, (list, dict)) for v in o):
            return flat
        return "[\n" + ",\n".join(pad + dump(v, ind + 1, width) for v in o) + "\n" + " " * ind + "]"
    return json.dumps(o, ensure_ascii=False)


FITTING_CODE = {"extinguisher": "FIRE", "handrail": "RAIL", "vent": "VENT", "junction": "JBOX", "conduit": "COND"}


def _number(used, family):
    n = 1
    while "%s%02d" % (family, n) in used:
        n += 1
    return "%s%02d" % (family, n)


def assign(ship, check=False):
    import interior_model
    path = os.path.join(ROOT, "ArtSource", "Ships", ship, "Design", "%s_interior_design.json" % ship)
    design = json.load(open(path, encoding="utf-8"))
    ids = design.setdefault("ids", {})
    ids.setdefault("_comment", "The interior's IDs, bound to the build data (Tools/Design/assign_interior_ids.py): layout "
                               "objects and doors by name, kit parts as [id, part] parallel to interior.kit_modules, "
                               "interior decals as [item, id] parallel to interior.decals.items.")
    m = interior_model.Model(ship, strict=False)
    codes = design["rooms"]
    added = []
    used = set()

    def collect(v):
        if isinstance(v, str) and re.match(r"^[A-Z]{2,3}-", v):
            used.add(v)
        elif isinstance(v, (list, tuple)):
            for x in v:
                collect(x)
        elif isinstance(v, dict):
            for k, x in v.items():
                if not k.startswith("_"):
                    collect(x)
    collect({k: v for k, v in ids.items() if k != "_comment"})
    # layout objects and doors
    objs = ids.setdefault("objects", {})
    for o in m.layout["objects"]:
        if o["name"] not in objs:
            comp = bool(re.search(r"\bS\d\b", o["name"])) or o.get("below")
            objs[o["name"]] = _number(used, "%s-%s-" % (codes[o["room"]], "M" if comp else "O"))
            used.add(objs[o["name"]])
            added.append(objs[o["name"]])
    doors = ids.setdefault("doors", {})
    for d in m.layout["doors"]:
        if d["name"] not in doors:
            doors[d["name"]] = _number(used, "DR-")
            used.add(doors[d["name"]])
            added.append(doors[d["name"]])
    # kit parts: rebuild the parallel lists from the placements (existing IDs kept)
    m2 = interior_model.Model(ship, strict=False) if added else m
    new = dict((id(p), i) for p, i in interior_model.proposed_kit_ids(m2))
    kit = {}
    for kind in ("wall_runs", "run_parts"):
        runs = m2.mods.get(kind, [])
        kit[kind] = [[None] * len(r[3] if kind == "wall_runs" else r[2]) for r in runs]
    for p in m2.placements:
        ident = p.id or new[id(p)]
        if not p.id:
            added.append(ident)
        kit[p.run[0]][p.run[1]][p.index] = [ident, p.part]
    ids["kit"] = kit
    # interior decals, scatter rules, grab bars
    dec = m2.recipe["interior"].get("decals") or {}
    dids = ids.setdefault("decals", {})
    old = dids.get("items") or []
    items = []
    for i, it in enumerate(dec.get("items", [])):
        pair = old[i] if i < len(old) else None
        if pair and pair[0] == it["item"]:
            items.append(pair)
        else:
            ident = _number(used, "D-I-")
            used.add(ident)
            added.append(ident)
            items.append([it["item"], ident])
    dids["items"] = items
    for key, fam in (("scatter", "D-I-R-SCATTER-"), ("grab_bars", None)):
        lst = list(dids.get(key) or [])
        for i, entry in enumerate(dec.get(key, [])):
            if i < len(lst) and lst[i]:
                continue
            if fam is None:
                at = entry.get("at") or entry["from"]
                fam = "%s-O-GRAB-" % codes.get(m2.room_at(at[0], at[1]), "X")
            ident = _number(used, fam)
            used.add(ident)
            added.append(ident)
            lst.append(ident)
        dids[key] = lst[:len(dec.get(key, []))]
    # the ship's fittings (interior.kit.fittings): [type, id] parallel to the list, <ROOM>-O-<TYPE>-nn
    fits = (m2.recipe["interior"].get("kit") or {}).get("fittings", [])
    old = ids.get("fittings") or []
    lst = []
    for i, f in enumerate(fits):
        pair = old[i] if i < len(old) else None
        if pair and pair[0] == f["type"]:
            lst.append(pair)
            continue
        x = f["at"][0] if f.get("at") else f["x"][0]
        yw = f["at"][1] if f.get("at") else f["y"]
        code = codes.get(m2.room_at(x, yw - (0.1 if yw > 0 else -0.1)), "X")
        ident = _number(used, "%s-O-%s-" % (code, FITTING_CODE.get(f["type"], f["type"][:4].upper())))
        used.add(ident)
        added.append(ident)
        lst.append([f["type"], ident])
    ids["fittings"] = lst
    stale = m.stale_ids
    if not check and (added or stale):
        text = dump(design) + "\n"
        json.loads(text)
        open(path, "w", encoding="utf-8", newline="\n").write(text)
    return added, stale


def main(argv):
    ship = argv[0]
    check = "--check" in argv
    added, stale = assign(ship, check)
    print("ASSIGNINTIDS %s: %d %s%s" % (ship, len(added), "without id" if check else "added",
                                       (": " + ", ".join(added[:14]) + (" ..." if len(added) > 14 else "")) if added else ""))
    for s in stale:
        print("ASSIGNINTIDS stale: " + s)
    return 1 if (check and (added or stale)) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
