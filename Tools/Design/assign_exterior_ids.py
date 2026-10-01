"""Gives every element of a ship's build data an "id" (author 1. 10. 2026: the drawings and the build read the same
data, and every decal, light, functional part and greeble on a drawing carries the ID it has in the data).

    python Tools/Design/assign_exterior_ids.py Wayfarer            # adds the missing IDs, prints what it added
    python Tools/Design/assign_exterior_ids.py Wayfarer --check    # exit 1 when an element has no ID

IDs already in the data are never changed; a new element gets the next free number of its family:
  recipe (<Ship>_hs.json)   decals.items D-H-nn, decals.trim D-T-nn, decals.grime D-G-nn, decals.rules D-R-<RULE>,
                            lights.lenses / strips L-<NAME>, functional.items F-<KIND>-nn, functional.gun_mounts
                            F-GUNMOUNT-nn, parts.hull.greebles G-<KIND>-nn, parts.hull.zones Z-B-nn,
                            detail.hull_plates P-B-nn, detail.hull_recesses R-B-nn, detail.pod.plates P-POD-nn,
                            gear.gear_main / gear_nose F-GEAR-MAIN / F-GEAR-NOSE, pod sections P-POD-<NAME>,
                            pod greebles G-POD-<KIND>-nn, single parts (pod intake / exhaust / bay / pipe run,
                            gun, missile rack, nozzle, wing, fin, canopy frame) F-<NAME>, hull and pod skins
                            P-HULL / P-POD
  setup (<Ship>_setup.json) decals D-<NAME> (Name_R -> D-NAME-R)
The builders ignore the key (Tools/Blender/hs_*.py, Tools/Assets/import_ship.py).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json_ids  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GREEBLE = {"hatch_large": "HTL", "hatch": "HT", "vent": "VT", "sensor": "SN", "strip": "SP"}
FUNCTIONAL = {"connector": "CONN"}


def slug(s):
    return re.sub(r"[^A-Z0-9]+", "-", str(s).upper()).strip("-")


def recipe_targets(root):
    """[(object Node, family prefix or fixed id)] in a stable order."""
    out = []

    def lst(path, family):
        try:
            node = json_ids.at(root, path)
        except (KeyError, IndexError, TypeError):
            return
        for child in node.children:
            if isinstance(child.value, dict):
                out.append((child, family(child.value) if callable(family) else family))

    lst(["decals", "items"], "D-H-")
    lst(["decals", "trim"], "D-T-")
    lst(["decals", "grime"], "D-G-")
    rules = json_ids.at(root, ["decals", "rules"])
    for key, child in rules.children.items():
        if not key.startswith("_") and isinstance(child.value, dict):
            out.append((child, "=D-R-" + slug(key)))
    lst(["lights", "lenses"], lambda v: "=L-" + slug(v["name"]))
    lst(["lights", "strips"], lambda v: "=L-" + slug(v["name"]))
    lst(["functional", "items"], lambda v: "F-%s-" % FUNCTIONAL.get(v["kind"], slug(v["kind"])))
    lst(["functional", "gun_mounts"], "F-GUNMOUNT-")
    lst(["parts", "hull", "greebles"], lambda v: "G-%s-" % GREEBLE.get(v["part"], slug(v["part"])))
    lst(["parts", "hull", "zones"], "Z-B-")
    lst(["detail", "hull_plates"], "P-B-")
    lst(["detail", "hull_recesses"], "R-B-")
    lst(["detail", "pod", "plates"], "P-POD-")
    for key in ("gear_main", "gear_nose"):
        try:
            out.append((json_ids.at(root, ["gear", key]), "=F-" + slug(key.replace("gear_", "gear-"))))
        except KeyError:
            pass
    lst(["parts", "pod", "revolve", "sections"], lambda v: "=P-POD-" + slug(v["name"]))
    lst(["parts", "pod", "revolve", "greebles"], lambda v: "G-POD-%s-" % GREEBLE.get(v["part"], slug(v["part"])))
    for path, ident in ((["parts", "hull"], "P-HULL"), (["parts", "pod"], "P-POD"),
                        (["parts", "pod", "revolve", "intake"], "F-POD-INTAKE"),
                        (["parts", "pod", "revolve", "exhaust"], "F-POD-EXHAUST"),
                        (["detail", "pod", "bay"], "F-POD-BAY"), (["detail", "pod", "pipe_run"], "F-POD-PIPES"),
                        (["parts", "gun"], "F-GUN-S3"), (["parts", "missile_rack"], "F-MISSILE-S2"),
                        (["parts", "nozzle"], "F-NOZZLE"), (["wings", "wing"], "F-WING"), (["wings", "fin"], "F-FIN"),
                        (["canopy_frame"], "F-CANOPY-FRAME")):
        try:
            out.append((json_ids.at(root, path), "=" + ident))
        except KeyError:
            pass
    return out


def setup_targets(root):
    node = json_ids.at(root, ["decals"])
    return [(c, "=D-" + slug(c.value["name"])) for c in node.children
            if isinstance(c.value, dict) and not str(c.value.get("name", "")).startswith("_")]


def assign(text, targets):
    used = set()
    for node, _ in targets:
        if "id" in node.value:
            used.add(node.value["id"])
    added = []
    for node, family in targets:
        if "id" in node.value:
            continue
        if family.startswith("="):
            ident = family[1:]
        else:
            n = 1
            while "%s%02d" % (family, n) in used:
                n += 1
            ident = "%s%02d" % (family, n)
        if ident in used:
            raise SystemExit("duplicate id %s" % ident)
        used.add(ident)
        added.append((node, ident))
    return json_ids.insert_ids(text, added), [a[1] for a in added]


def process(path, kind, check):
    raw = open(path, "rb").read().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    root = json_ids.parse(text)
    targets = recipe_targets(root) if kind == "recipe" else setup_targets(root)
    new, added = assign(text, targets)
    if check:
        return added
    assert json_ids.parse(new).value is not None
    json.loads(new)
    if added:
        open(path, "wb").write((new.replace("\n", "\r\n") if crlf else new).encode("utf-8"))
    return added


def main(argv):
    ship = argv[0]
    check = "--check" in argv
    files = [(os.path.join(ROOT, "ArtSource", "Ships", ship, "HardSurface", "%s_hs.json" % ship), "recipe"),
             (os.path.join(ROOT, "ArtSource", "Ships", ship, "%s_setup.json" % ship), "setup")]
    missing = 0
    for path, kind in files:
        added = process(path, kind, check)
        missing += len(added)
        print("ASSIGNIDS %s %s: %d %s%s" % (kind, os.path.basename(path), len(added),
                                           "without id" if check else "added", (": " + ", ".join(added[:12]) + (" ..." if len(added) > 12 else "")) if added else ""))
    return 1 if (check and missing) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
