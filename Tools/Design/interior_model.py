"""The interior drawings' model (dossier bod 4, author 1. 10. 2026): every element of a ship's interior from the data
the ship is built from, with the ID it has in that data - the same principle as the exterior (exterior_model.py).

    python Tools/Design/interior_model.py [Wayfarer]        # prints the elements per room and the data check

Data (layout metres: x forward from the aft end, y to port, z from the deck):
  Design/<Ship>_layout.json          rooms, objects ("id"), doors ("id") - the approved deck plan with each purpose
  HardSurface/<Ship>_hs.json         interior.kit_modules (wall runs, run parts) and their IDs (kit_modules.ids, parallel
                                     to wall_runs / run_parts), interior.decals (items "id", scatter rules "id")
  <Ship>_setup.json                  the interior's projected decals (D-INT-*, Unreal centimetres in hull space)
  Export/<Ship>_lights.json          the lights the ship builds itself (int_N, fix_N - the fixture lights)
  ArtSource/Kit/Export/kit_manifest.json   kit parts: size, light sockets with their parameters, decal items
  Tools/Assets/kit_rooms.py          how the game lights the kit sockets (read with ast, as kit_rooms reads import_kit)
  Design/<Ship>_interior_design.json the Czech purposes of the kit parts, the door leaves, the components' access and
                                     everything proposed that is not built yet
Geometry (drawing only, never in the tests - the FBX files are in Git LFS): the kit parts' FBX placed as
Tools/Kit/kit_layout.py places them, the ship's own interior and hull FBX (ship space = layout + assemble.offset).
"""
import ast
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "Tools", "Kit"))
import kit_layout  # noqa: E402

KIT_EXPORT = os.path.join(ROOT, "ArtSource", "Kit", "Export")
CAT_OF_KIT = {"Wall": "wall", "Bulkhead": "bulkhead", "Ceiling": "ceiling", "Floor": "floor", "Furniture": "furniture",
              "Stair": "stair", "Portal": "portal", "Corner": "wall", "Door": "door"}
CAT_CZ = {"wall": "stěnový modul", "bulkhead": "přepážka s dveřmi", "ceiling": "stropní panel", "floor": "podlahová deska",
          "furniture": "nábytek", "object": "vybavení", "component": "komponenta lodi", "door": "dveře",
          "light": "světlo", "decal": "decal", "stair": "schody", "portal": "portál", "standin": "náhrada"}
STATUS_CZ = {"built": "postaveno", "proposed": "návrh", "change": "změna", "remove": "odstranit"}
SIDE_CZ = {"L": "levobok", "R": "pravobok"}


def file_digest(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read().replace(b"\r\n", b"\n")).hexdigest()[:12]


def lfs_oid(path):
    """The Git LFS object ID (sha256) of a file: read from its pointer when LFS did not fetch it (CI), else hashed."""
    try:
        with open(path, "rb") as f:
            head = f.read(200)
            if head.startswith(b"version https://git-lfs"):
                m = re.search(rb"oid sha256:([0-9a-f]{64})", head)
                return m.group(1).decode()[:12] if m else "?"
            h = hashlib.sha256(head)
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
            return h.hexdigest()[:12]
    except OSError:
        return "missing"


def is_lfs_pointer(path):
    try:
        with open(path, "rb") as f:
            return f.read(40).startswith(b"version https://git-lfs")
    except OSError:
        return True


def fmt(v, nd=2):
    """A Czech decimal with a real minus sign (ranges are written "a … b", so -1,80–-1,19 cannot happen)."""
    s = ("%." + str(nd) + "f") % v
    return s.replace(".", ",").replace("-", "\u2212")


def kit_light_rules():
    """The constants Tools/Assets/kit_rooms.py lights the kit sockets with (and import_kit's colours)."""
    out = {}
    for fn, names in (("kit_rooms.py", ("SHIP_LIGHT_SCALE", "INTERIOR_ONLY_SOCKETS", "SHADOWED_SOCKETS",
                                        "SKIPPED_SOCKETS", "SOCKET_SCALE")),
                      ("import_kit.py", ("LIGHT_COLOURS",))):
        tree = ast.parse(open(os.path.join(ROOT, "Tools", "Assets", fn), encoding="utf-8").read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id in names:
                out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


class Element:
    def __init__(self, ident, cat, room, status="built", name="", purpose="", kit=None, where="", src="", **extra):
        self.id, self.cat, self.room, self.status = ident, cat, room, status
        self.name, self.purpose, self.kit, self.where, self.src = name, purpose, kit, where, src
        self.extra = extra

    def __repr__(self):
        return "<%s %s %s %s>" % (self.id, self.cat, self.room, self.status)


class Placement:
    """A kit part in the ship: the part, its pivot (layout metres) and yaw (Unreal degrees, kit_layout)."""

    def __init__(self, ident, part, x, y_ue, z, yaw, run, index):
        self.id, self.part, self.x, self.y_ue, self.z, self.yaw = ident, part, x, y_ue, z, yaw
        self.run, self.index = run, index           # ("wall_runs" | "run_parts", run number), index in the run

    @property
    def category(self):
        return self.part.split("_")[0]

    def to_layout(self, bx, by, bz=0.0):
        """Blender-local point(s) of the part (metres) to layout metres."""
        wx, wy = kit_layout.rotate(self.yaw, bx, -by)
        return self.x + wx, -(self.y_ue + wy), self.z + bz

    def dir_layout(self, dx_ue, dy_ue):
        """A direction in the part's Unreal frame to layout (x, y)."""
        wx, wy = kit_layout.rotate(self.yaw, dx_ue, dy_ue)
        return wx, -wy

    def ue_to_layout(self, lx_cm, ly_cm, lz_cm):
        wx, wy = kit_layout.rotate(self.yaw, lx_cm / 100.0, ly_cm / 100.0)
        return self.x + wx, -(self.y_ue + wy), self.z + lz_cm / 100.0


class Model:
    def __init__(self, ship="Wayfarer", strict=True):
        """strict=False stands in a placeholder for a missing ID (assign_interior_ids.py --check, the test)."""
        self.ship, self.strict = ship, strict
        base = os.path.join(ROOT, "ArtSource", "Ships", ship)
        self.paths = {
            "layout": os.path.join(base, "Design", "%s_layout.json" % ship),
            "recipe": os.path.join(base, "HardSurface", "%s_hs.json" % ship),
            "setup": os.path.join(base, "%s_setup.json" % ship),
            "lights": os.path.join(base, "Export", "%s_lights.json" % ship),
            "design": os.path.join(base, "Design", "%s_interior_design.json" % ship),
            "kit_manifest": os.path.join(KIT_EXPORT, "kit_manifest.json"),
            "kit_rules": os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"),
            "library": os.path.join(ROOT, "ArtSource", "Ships", "Shared", "Decals", "decal_library_index.json"),
            "kit_rooms": os.path.join(ROOT, "Tools", "Assets", "kit_rooms.py"),
        }
        load = lambda k: json.load(open(self.paths[k], encoding="utf-8"))     # noqa: E731
        self.layout, self.recipe, self.setup = load("layout"), load("recipe"), load("setup")
        self.lights_export = load("lights")["lights"]
        self.design = load("design")
        self.parts = load("kit_manifest")["parts"]
        self.rules = load("kit_rules")
        self.library = load("library")["decals"]
        self.ids = self.design.get("ids") or {}
        self.offset = self.recipe["assemble"]["offset"]
        self.mods = self.recipe["interior"]["kit_modules"]
        self.kit_rooms = kit_layout.active_rooms(self.recipe)
        self.light_rules = kit_light_rules()
        self.codes = self.design["rooms"]
        self.rooms = {}
        for r in self.layout["rooms"]:
            poly = r.get("poly") or [[r["rect"][0], r["rect"][2]], [r["rect"][1], r["rect"][2]],
                                     [r["rect"][1], r["rect"][3]], [r["rect"][0], r["rect"][3]]]
            self.rooms[r["id"]] = dict(r, poly=poly, code=self.codes[r["id"]], floor=r.get("floor_z", 0.0),
                                       kit=r["id"] in self.kit_rooms, poly_given=bool(r.get("poly")))
        self.elements = []
        self.checks = []                            # (id, Czech sentence) - the sheet's data check
        self.placements = self._placements()
        self._room_spaces()
        self._kit_elements()
        self._objects()
        self._doors()
        self._lights()
        self._setup_lights()
        self._decals()
        self._fittings()
        self._stairs()
        self.by_id = {}
        for e in self.elements:
            if e.id in self.by_id:
                raise ValueError("duplicate interior id %s" % e.id)
            self.by_id[e.id] = e
        self.digests = self._digests()

    # ------------------------------------------------------------------ helpers
    def _need_id(self, ident, what, name):
        """The ID the design data gives an element (ids.*); without one: a KeyError, or a placeholder when not strict
        (assign_interior_ids.py --check, the test)."""
        if ident:
            return ident
        if self.strict:
            raise KeyError("%s without id: %s (python Tools/Design/assign_interior_ids.py %s)" % (what, name, self.ship))
        self.missing = getattr(self, "missing", 0) + 1
        return "?%s-%d" % (what.replace(" ", "-"), self.missing)

    def _digests(self):
        """Digests of the data the interior drawings read - only the interior's part of each file, so a change to the
        exterior (the recipe's hull, the setup's hull decals) does not make the interior sheets stale, and the
        interior's IDs (kept in the interior design data) do not touch the exterior drawings' inputs."""
        used = {"SM_Kit_" + p.part for p in self.placements}
        items = sorted({e.extra.get("item") for e in self.elements if e.cat == "decal"} - {None})
        parts = {
            "layout": {k: self.layout.get(k) for k in ("decks", "rooms", "objects", "doors")},
            "interior": [self.recipe["interior"], self.recipe["assemble"]["offset"]],
            "setup": [d for d in self.setup["decals"] if isinstance(d, dict) and d.get("id") in self.by_id],
            "lights": [L for L in self.lights_export if ("L-" + L["name"].upper().replace("_", "-")) in self.by_id],
            "design": self.design,
            "kit": {k: self.parts[k] for k in sorted(used)},
            "library": {k: self.library.get(k) for k in items},
            "light_rules": self.light_rules,
        }
        return {k: hashlib.sha1(json.dumps(v, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
                for k, v in parts.items()}

    def geometry_digests(self):
        """The LFS object IDs of the meshes the sheets draw (information only: the ship's FBX change on every
        rebuild by a few triangles - Docs/CURRENT.md, build determinism)."""
        out = {}
        files = [self.ship_fbx(s) for s in ("", "_Interior", "_Canopy")] + sorted({self.kit_fbx(p.part) for p in self.placements})
        for f in files:
            out[os.path.basename(f)] = lfs_oid(f)
        return out

    def room_at(self, x, y):
        """The room at a point: its built space (_room_spaces) - a kit room reaches out to its walls' faces (the hold's
        liner at ±2.05 while the layout's rectangle is ±1.90: its signs on the liner were lost, critic of I-02)."""
        best = None
        for rid, r in self.rooms.items():
            if _inside((x, y), r.get("space") or r["poly"]):
                best = rid
        return best

    def _room_spaces(self):
        """Each kit room's space: its layout rectangle widened to its wall modules' faces plus 5 cm (what is on a face -
        a decal, a fitting - belongs to the room in front of it)."""
        for rid, r in self.rooms.items():
            ys = [abs(p.ue_to_layout(0, 0, 0)[1]) for p in self.placements
                  if p.category == "Wall" and self.placement_room(p) == rid]
            if ys and r.get("rect") and not r.get("poly_given"):
                x0, x1, y0, y1 = r["rect"]
                hw = max(max(ys) + 0.05, y1, -y0)
                r["space"] = [[x0, -hw], [x1, -hw], [x1, hw], [x0, hw]]
            r["faces_y"] = max(ys) if ys else None

    def room_faces(self, rid):
        """{L, R: the long walls' face y; A, F: the room's end x (bulkhead faces, else the layout's ends)}."""
        r = self.rooms[rid]
        out = {"A": r["rect"][0], "F": r["rect"][1]}
        if r.get("faces_y"):
            out["L"], out["R"] = r["faces_y"], -r["faces_y"]
        for p in self.placements:
            if p.category == "Bulkhead" and self.placement_room(p) == rid:
                x = p.ue_to_layout(0, 0, 0)[0]
                out["A" if p.dir_layout(1.0, 0.0)[0] > 0 else "F"] = x
        return out

    def object_faces(self, e):
        """The walls an object stands at (within 0.5 m of their face): its developed elevations show it."""
        rid = e.room
        if rid is None or not (e.extra.get("rect") or e.extra.get("pos")) or e.extra.get("below"):
            return set()
        r = e.extra.get("rect") or [e.extra["pos"][0]] * 2 + [e.extra["pos"][1]] * 2
        f = self.room_faces(rid)
        near = 0.5
        if "L" not in f:                         # a room the ship builds (no kit walls): its layout outline
            ys = [q[1] for q in self.rooms[rid]["poly"]]
            f["L"], f["R"], near = max(ys), min(ys), 0.6
        out = set()
        if "L" in f and f["L"] - r[3] < near:
            out.add("L")
        if "R" in f and r[2] - f["R"] < near:
            out.add("R")
        if r[0] - f["A"] < 0.5:
            out.add("A")
        if f["F"] - r[1] < 0.5:
            out.add("F")
        return out

    def room_code(self, rid):
        return self.codes.get(rid, "?")

    def hull_to_layout(self, loc_cm):
        """Unreal hull space (cm, y mirrored) to layout metres."""
        return (loc_cm[0] / 100.0 - self.offset[0], -loc_cm[1] / 100.0 - self.offset[1], loc_cm[2] / 100.0 - self.offset[2])

    # ------------------------------------------------------------------ kit parts
    def _placements(self):
        """The kit parts as kit_layout places them, each with its ID from the design data's ids.kit - [id, part]
        pairs parallel to the recipe's wall_runs / run_parts; a pair whose part is not the recipe's is out of date
        (the recipe changed: assign_interior_ids.py) and gives no ID."""
        ids = self.ids.get("kit") or {}
        out = []
        placed = kit_layout.layout_parts(self.mods, self.parts)
        k = 0
        self.stale_ids = []
        for kind in ("wall_runs", "run_parts"):
            runs = self.mods.get(kind, [])
            idl = ids.get(kind) or []
            for ri, run in enumerate(runs):
                names = run[3] if kind == "wall_runs" else run[2]
                run_ids = idl[ri] if ri < len(idl) else []
                for mi, name in enumerate(names):
                    m, (x, y_ue, z), yaw = placed[k]
                    k += 1
                    pair = run_ids[mi] if mi < len(run_ids) else None
                    ident = pair[0] if pair and pair[1] == name else None
                    if pair and pair[1] != name:
                        self.stale_ids.append("%s: %s in the ids, %s in the recipe" % (pair[0], pair[1], name))
                    p = Placement(ident, name, x, y_ue, z, yaw, (kind, ri), mi)
                    p.tag = self._need_id(ident, "kit part", "%s %s[%d][%d]" % (name, kind, ri, mi))
                    out.append(p)
        return out

    def placement_room(self, p):
        """The room a kit part serves: a wall module's or bulkhead's room is in front of its face (+X), a run part's
        under its middle."""
        L = self.span(p)
        if p.category in ("Wall", "Bulkhead", "Corner", "Door"):
            mx, my, _ = p.ue_to_layout(40.0, -L * 50.0, 0.0)
        elif p.category == "Furniture":
            mx, my, _ = p.ue_to_layout(20.0, 0.0, 0.0)
        else:
            mx, my, _ = p.ue_to_layout(L * 50.0, 0.0, 0.0)
        return self.room_at(mx, my)

    def span(self, p):
        """A part's length along its run: a wall module's length, a bulkhead's width across the section."""
        man = self.parts["SM_Kit_" + p.part]
        return man["dims_m"][1] if p.category == "Bulkhead" else man["length_m"]

    def side_of(self, p):
        """L (port) or R (starboard) for a wall module: the side its face looks away from."""
        fx, fy = p.dir_layout(1.0, 0.0)
        return "L" if fy < 0 else "R"

    def _kit_elements(self):
        purpose = self.design["kit_purpose"]
        for p in self.placements:
            rid = self.placement_room(p)
            cat = CAT_OF_KIT.get(p.category, p.category.lower())
            man = self.parts["SM_Kit_" + p.part]
            L = self.span(p)
            if cat == "furniture":
                obj = self.layout_object(p.id)
                name = obj["name"] if obj else p.part
                purp = obj.get("purpose", "") if obj else ""
            else:
                name = CAT_CZ.get(cat, cat)
                purp = purpose.get(p.part, "")
            where = self._where_kit(p, cat)
            self.elements.append(Element(p.tag, cat, rid, "built", name, purp, kit=p.part, where=where,
                                         src="kit_modules.%s[%d][%d]" % (p.run[0], p.run[1], p.index), placement=p,
                                         side=self.side_of(p) if cat == "wall" else None, length=L,
                                         dims=man["dims_m"], tris=man["tris"]))

    def _where_kit(self, p, cat):
        L = self.span(p)
        if cat in ("wall", "bulkhead"):
            a = p.ue_to_layout(0, 0, 0)
            b = p.ue_to_layout(0, -L * 100.0, 0)
            if abs(a[0] - b[0]) > 0.01:
                return "x %s … %s, líc y %s" % (fmt(min(a[0], b[0])), fmt(max(a[0], b[0])), fmt(a[1]))
            return "líc x %s, y %s … %s" % (fmt(a[0]), fmt(min(a[1], b[1])), fmt(max(a[1], b[1])))
        if cat == "furniture":
            return "x %s, y %s (střed zadní hrany)" % (fmt(p.x), fmt(-p.y_ue))
        a = p.ue_to_layout(0, 0, 0)
        b = p.ue_to_layout(L * 100.0, 0, 0)
        return "x %s … %s" % (fmt(min(a[0], b[0])), fmt(max(a[0], b[0])))

    def decal_purpose(self, item):
        """A decal library item's purpose in Czech (design data decal_items), else the library's English one."""
        return (self.design.get("decal_items") or {}).get(item) or self.library.get(item, {}).get("purpose", "")

    def object_id(self, o):
        """A layout object's ID: ids.objects in the design data, by the object's name (unique in the layout)."""
        return (self.ids.get("objects") or {}).get(o["name"])

    def layout_object(self, ident):
        return next((o for o in self.layout["objects"] if self.object_id(o) == ident), None)

    # ------------------------------------------------------------------ layout objects, components
    def _objects(self):
        kit_ids = {p.id for p in self.placements}
        keep = self.mods.get("keep") or {}
        comps = self.design.get("components", {})
        for o in self.layout["objects"]:
            ident = self._need_id(self.object_id(o), "layout object", o["name"])
            if ident in kit_ids:
                # the kit part built for this object (furniture): the kit element carries it; compare the boxes
                self._check_furniture(o, ident)
                continue
            rid = o["room"]
            kit_room = rid in self.kit_rooms and "objects" not in keep.get(rid, [])
            status = "proposed" if kit_room else "built"
            cat = "component" if ident.split("-")[1] == "M" else ("furniture" if ident.split("-")[1] == "U" else "object")
            c = comps.get(ident, {})
            built_note = c.get("built_as") or ("" if not kit_room else "ve schváleném layoutu, ve hře zatím nepostaveno")
            rect, z, where, src = o["rect"], o.get("z"), _rect_txt(o), "layout.objects"
            niche = self._bay_niche(c.get("bay"))
            if o.get("below") and status == "built" and not c.get("built_as"):
                built_note = "postaven poklop v podlaze nad ní (hs_interior.hatch, stejný obrys); jednotka pod podlahou se " \
                             "nemodeluje"
                c = dict(c, state_cz="poklop postaven, jednotka nemodelována")
            if niche is not None:
                # the component is built in its kit wall module's niche (Tools/Kit/kit_batch4.py, SOCKET_Component):
                # the kit before the layout (author 1. 10. 2026) - the niche is the component's box, the layout's goes
                # to the data check
                host, rect, z = niche
                status, src = "built", "%s SOCKET_Component" % host.part
                built_note = "postaveno ve výklenku stěnového modulu %s (%s)" % (host.tag, host.part)
                where = _rect_txt({"rect": rect, "z": z})
                self._check_niche(o, ident, rect, z, host)
            self.elements.append(Element(ident, cat, rid, status, o["name"], o.get("purpose", ""), where=where,
                                         src=src, rect=rect, z=z, below=o.get("below", False), layout_rect=o["rect"],
                                         layout_z=o.get("z"), access=c.get("access", ""), replace=c.get("replace", ""),
                                         bay=c.get("bay"), note=built_note, proposal=c.get("proposal"),
                                         state_cz=c.get("state_cz")))

    def _bay_niche(self, bay):
        """The niche of a component bay wall module (the kit part with SOCKET_Component) named by a component's bay:
        (placement, [x0, x1, y0, y1], [z0, z1]) in layout metres from kit_batch4's opening (BAY_HOLE in from both
        ends, SILL … HEAD) and depth (BAY_DEPTH behind the face, the LINER plates), else None."""
        p = next((q for q in self.placements if q.tag == bay), None)
        if p is None or "SOCKET_Component" not in self.parts["SM_Kit_" + p.part].get("sockets", {}):
            return None
        k = bay_constants()
        letter = p.part.rsplit("_", 1)[1]
        L = self.span(p)
        d = k["BAY_DEPTH"][letter] + k["LINER"]
        m = BAY_HOLE[letter]
        pts = [p.ue_to_layout(-a * 100.0, -u * 100.0, 0) for a in (0.0, d) for u in (m, L - m)]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        return p, [round(min(xs), 3), round(max(xs), 3), round(min(ys), 3), round(max(ys), 3)], [k["SILL"], k["HEAD"]]

    def _check_niche(self, o, ident, rect, z, host):
        r, oz = o["rect"], o.get("z") or [0, 0]
        d = max(abs(a - b) for a, b in zip(r + list(oz), rect + list(z)))
        if d > 0.015:
            self.checks.append((ident, "%s: v layoutu x %s … %s, y %s … %s, z %s … %s; postavený výklenek v %s x %s … %s, "
                                       "y %s … %s, z %s … %s (nejvíc %d mm; kit platí, layout opravit)" % (
                                           o["name"], fmt(r[0]), fmt(r[1]), fmt(r[2]), fmt(r[3]), fmt(oz[0]), fmt(oz[1]),
                                           host.tag, fmt(rect[0]), fmt(rect[1]), fmt(rect[2]), fmt(rect[3]), fmt(z[0]),
                                           fmt(z[1]), round(d * 1000))))

    def _check_furniture(self, o, ident):
        p = next(p for p in self.placements if p.id == ident)
        man = self.parts["SM_Kit_" + p.part]
        dx, dy, dz = man["dims_m"]
        corners = [p.ue_to_layout(a * 100.0, b * 100.0, 0) for a in (0.0, dx) for b in (-dy / 2, dy / 2)]
        xs, ys = [c[0] for c in corners], [c[1] for c in corners]
        kb = (min(xs), max(xs), min(ys), max(ys))
        r = o["rect"]
        d = max(abs(kb[0] - r[0]), abs(kb[1] - r[1]), abs(kb[2] - r[2]), abs(kb[3] - r[3]))
        if d > 0.015:
            self.checks.append((ident, "%s (%s): půdorys dílu x %s … %s, y %s … %s proti layoutu x %s … %s, y %s … %s "
                                         "(nejvíc %d mm)" % (o["name"], p.part, fmt(kb[0]), fmt(kb[1]), fmt(kb[2]),
                                                             fmt(kb[3]), fmt(r[0]), fmt(r[1]), fmt(r[2]), fmt(r[3]),
                                                             round(d * 1000))))
        z = o.get("z")
        if z and abs((z[1] - z[0]) - dz) > 0.05:
            self.checks.append((ident, "%s: výška dílu %s m proti layoutu z %s … %s (%s)" % (
                o["name"], fmt(dz), fmt(z[0]), fmt(z[1]), self.design.get("height_notes", {}).get(ident, "rozdíl"))))

    # ------------------------------------------------------------------ doors
    def _doors(self):
        leaves = self.design.get("doors", {})
        for d in self.layout["doors"]:
            ident = self._need_id((self.ids.get("doors") or {}).get(d["name"]), "layout door", d["name"])
            lf = leaves.get(ident, {})
            x, y = d["at"]
            rooms = sorted({self.room_at(x - 0.05, y), self.room_at(x + 0.05, y)} - {None}) if d["axis"] == "x" else \
                sorted({self.room_at(x, y - 0.05), self.room_at(x, y + 0.05)} - {None})
            self.elements.append(Element(ident, "door", rooms[0] if rooms else None, "built", d["name"],
                                         lf.get("purpose", ""), where="x %s, y %s, šířka %s" % (fmt(x), fmt(y), fmt(d["width"])),
                                         src="layout.doors", at=d["at"], axis=d["axis"], width=d["width"], rooms=rooms,
                                         leaf=lf))

    # ------------------------------------------------------------------ lights
    def _lights(self):
        R = self.light_rules
        zones = [z for z in self.mods.get("light_scale", []) if not isinstance(z, str)]

        def zone_k(xm, sname):
            z = next((z for z in zones if z[0] <= xm <= z[1]), None)
            if z is None:
                return 1.0
            extra = z[4] if len(z) > 4 else {}
            return z[2] * next((v for k, v in extra.items() if sname.startswith(k)), 1.0)

        for p in self.placements:
            man = self.parts["SM_Kit_" + p.part]
            for sname, sock in sorted(man["sockets"].items()):
                if not sname.startswith("SOCKET_Light") or (R["SKIPPED_SOCKETS"] and sname.startswith(R["SKIPPED_SOCKETS"])):
                    continue
                prm = sock.get("params") or {}
                lx, ly, lz = sock["location_ue_cm"]
                x, y, z = p.ue_to_layout(lx, ly, lz)
                k_cd = next((v for kk, v in R["SOCKET_SCALE"].items() if sname.startswith(kk)), 1.0)
                k_cd *= zone_k(p.x + kit_layout.rotate(p.yaw, lx, ly)[0] / 100.0, sname)
                cd = prm.get("cd", 1.0) * k_cd * R["SHIP_LIGHT_SCALE"]
                d = prm.get("dir_ue")
                dl = (p.dir_layout(d[0], d[1]) + (d[2],)) if d else None
                al = prm.get("along_ue", (0.0, -1.0, 0.0))
                along = p.dir_layout(al[0], al[1]) + (al[2],)
                short = sname[len("SOCKET_Light_"):]
                rid = self.room_at(x, y)
                self.elements.append(Element(
                    "%s/%s" % (p.tag, short), "light", rid, "built", short.split("_")[0], "", kit=p.part,
                    where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)), src="%s %s" % (p.part, sname),
                    pos=(x, y, z), type=prm.get("type", "point"), role=prm.get("role", "warm"), cd=cd,
                    cd_part=prm.get("cd", 1.0), cone=prm.get("cone_deg"), radius=prm.get("radius_m"), dir=dl,
                    width_cm=prm.get("width_cm"), along=along, shadow=sname.startswith(tuple(R["SHADOWED_SOCKETS"])),
                    interior_only=bool(prm.get("interior_only")) or sname.startswith(tuple(R["INTERIOR_ONLY_SOCKETS"])),
                    colour=tuple(c / 255.0 for c in R["LIGHT_COLOURS"].get(prm.get("role", "warm"), (255, 255, 255))),
                    host=p.tag))
        ceiling = self.rules["sections"]["L41"].get("ceiling", 2.3) + 0.05 if "L41" in self.rules["sections"] else 2.35
        for L in self.lights_export:
            x, y, z = L["location"]
            rid = self.room_at(x, y)
            if rid is None or not (-0.2 < z < 3.6) or (rid in self.kit_rooms and z > ceiling):
                continue                 # exterior lights (over a kit room's ceiling: the floods on the pods): exterior sheets
            ident = "L-" + L["name"].upper().replace("_", "-")
            self.elements.append(Element(
                ident, "light", rid, "built", L["name"].split("_")[0],
                {"fix": "světlo svítidla lodi (hs_fixture_lights: pás nebo lampa lodi)", "int": "světlo místnosti lodi (hs_interior)"}.get(
                    L["name"].split("_")[0], ""), where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)),
                src="%s_lights.json %s" % (self.ship, L["name"]), pos=(x, y, z), type=L["type"], role=None,
                cd=L["intensity_cd"], cone=L.get("cone_deg") if L["type"] == "spot" else None, radius=L.get("radius_m"),
                dir=tuple(L.get("direction") or (0, 0, -1)), shadow=False, interior_only=False,
                colour=tuple(L["color"]), host=None))

    def _setup_lights(self):
        """The cockpit lights the game makes from the ship's setup, not from the meshes: the pilot's light
        (ASpaceshipPawn::PlaceCockpitLights: the eye - the Cockpit socket - plus CockpitLightOffset, setup
        cockpit_light_intensity_cd) and one rect light per screen (UCockpitDisplayComponent: at the hull's Display_*
        sockets, display_light_intensity_cd x the screen's share of the display canvas, SpaceFlightHud.h). The C++
        defaults are read from the headers, the sockets from the exported hull."""
        src = os.path.join(ROOT, "Source", "gamespace")

        def const(header, pattern, n=1):
            t = open(os.path.join(src, header), encoding="utf-8").read()
            mt = re.search(pattern, t)
            return tuple(float(v) for v in mt.groups()) if n > 1 else float(mt.group(1))

        fbx = self.ship_fbx("")
        if not os.path.exists(fbx):
            return
        import fbx_mesh
        nulls = fbx_mesh.read(fbx)["nulls"]

        def lay(v):
            return tuple(float(a) - float(b) for a, b in zip(v, self.offset))

        eye = nulls.get("SOCKET_Cockpit")
        cd = self.setup.get("pawn", {}).get("cockpit_light_intensity_cd", 0.0)
        if cd > 0 and eye is not None:
            o = const("SpaceshipPawn.h", r"CockpitLightOffset = FVector\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", 3)
            col = const("SpaceshipPawn.h", r"CockpitLightColor = FLinearColor\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)", 3)
            reach = const("SpaceshipPawn.h", r"CockpitLightRadiusCm = ([\d.]+)f") / 100.0
            x, y, z = (a + b / 100.0 for a, b in zip(lay(eye), o))
            self.elements.append(Element(
                "L-SET-PILOT", "light", self.room_at(x, y), "built", "SET",
                "světlo pilota před obličejem nad deskou (nastavení lodi, bez stínu, dosah %s m)" % fmt(reach),
                where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)), src="setup pawn.cockpit_light_intensity_cd",
                pos=(x, y, z), type="point", role=None, cd=cd, cone=None, radius=None, dir=None, shadow=False,
                interior_only=False, colour=col, host=None, setup="pilot"))
        disp = (self.setup.get("components", {}).get("cockpit_displays") or {}).get("display_light_intensity_cd", 0.0)
        if disp > 0:
            hud = "SpaceFlightHud.h"
            dw, dh = const(hud, r"DisplayWidth = ([\d.]+)f"), const(hud, r"DisplayHeight = ([\d.]+)f")
            cw, th = const(hud, r"CentreWidth = ([\d.]+)f"), const(hud, r"CentreTopHeight = ([\d.]+)f")
            share = {"left": 1.0, "right": 1.0, "centre_top": cw / dw * th / dh, "centre_bottom": cw / dw * (dh - th) / dh}
            col = const("CockpitDisplayComponent.h", r"DisplayLightColor = FLinearColor\(([\d.]+)f, ([\d.]+)f, ([\d.]+)f\)", 3)
            size = const("CockpitDisplayComponent.h", r"DisplayLightSizeCm = FVector2D\(([\d.]+), ([\d.]+)\)", 2)
            wide = {"left": 1.0, "right": 1.0, "centre_top": cw / dw, "centre_bottom": cw / dw}
            for name, k in share.items():
                v = nulls.get("SOCKET_Display_" + name)
                if v is None:
                    continue
                x, y, z = lay(v)
                d = tuple(a - b for a, b in zip(lay(eye), (x, y, z))) if eye is not None else (-1.0, 0.0, 0.0)
                self.elements.append(Element(
                    "L-SET-DISP-" + name.upper().replace("_", "-"), "light", self.room_at(x, y), "built", "SET",
                    "záře obrazovky %s k oku pilota (nastavení lodi, %s × podíl plochy obrazovky %d %%, bez stínu)" % (
                        name.replace("_", " "), fmt(disp), round(100 * k)),
                    where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)), src="setup cockpit_displays.display_light_intensity_cd",
                    pos=(x, y, z), type="rect", role=None, cd=disp * k, cone=None, radius=None, dir=d, shadow=False,
                    interior_only=False, colour=col, host=None, width_cm=size[0] * wide[name], along=(0.0, 1.0, 0.0),
                    setup="display"))

    # ------------------------------------------------------------------ decals
    def _decals(self):
        for d in self.setup["decals"]:
            if not isinstance(d, dict) or "location" not in d:
                continue
            x, y, z = self.hull_to_layout(d["location"])
            rid = self.room_at(x, y)
            if rid is None or not (-0.2 < z < 3.6):
                continue
            active = kit_layout.decal_active(d, self.recipe)
            self.elements.append(Element(
                d["id"], "decal", rid, "built" if active else "remove", d["texture"],
                (self.design.get("purposes") or {}).get(d["id"], ""), where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)),
                src="setup.decals %s" % d["name"], pos=(x, y, z), item=d["texture"], size=(d["size"][1] / 100.0, d["size"][2] / 100.0),
                projected=True, note="" if active else "nápis staré procedurální místnosti %s, v kit místnosti se nestaví" % d.get("legacy_room")))
        dec = self.recipe["interior"].get("decals") or {}
        dids = self.ids.get("decals") or {}
        for i, it in enumerate(dec.get("items", [])):
            x, y, z = it["from"]
            pair = (dids.get("items") or [])[i] if i < len(dids.get("items") or []) else None
            ident = pair[1] if pair and pair[0] == it["item"] else None
            rid = self.room_at(x, y)
            built = rid not in self.kit_rooms
            lib = self.library.get(it["item"], {})
            self.elements.append(Element(
                self._need_id(ident, "interior decal", it["item"]), "decal", rid, "built" if built else "remove", it["item"],
                self.decal_purpose(it["item"]),
                where="x %s, y %s, z %s (paprsek)" % (fmt(x), fmt(y), fmt(z)), src="interior.decals.items", pos=(x, y, z),
                item=it["item"], size=tuple(lib.get("size_m", (0, 0))), ray=True, dir=ray_dir(it)))
        for i, sc in enumerate(dec.get("scatter", [])):
            sid = (dids.get("scatter") or [])[i] if i < len(dids.get("scatter") or []) else None
            xs = sc.get("x") or [0, 0]
            rid = self.room_at((xs[0] + xs[-1]) / 2, 0.0)
            self.elements.append(Element(self._need_id(sid, "decal scatter rule", str(i)), "decal", rid,
                                         "built" if rid not in self.kit_rooms else "remove", "rozsev",
                                         "servisní detail rozsetý po stěnách místností, které kit nestaví (%d položek, krok %s m, "
                                         "pravděpodobnost %d %%, x %s … %s, z %s … %s)" % (
                                             len(sc.get("items", [])), fmt(sc.get("step", 0)), round(100 * sc.get("prob", 1)),
                                             fmt(xs[0]), fmt(xs[-1]), fmt((sc.get("z") or [0, 0])[0]), fmt((sc.get("z") or [0, 0])[-1])),
                                         src="interior.decals.scatter[%d]" % i, item="scatter", rule=sc))
        for i, gb in enumerate(dec.get("grab_bars", [])):
            gid = (dids.get("grab_bars") or [])[i] if i < len(dids.get("grab_bars") or []) else None
            x, y, z = gb["at"]
            rid = self.room_at(x, y)
            self.elements.append(Element(self._need_id(gid, "grab bar", str(i)), "object", rid,
                                         "built" if rid not in self.kit_rooms else "remove", "madlo",
                                         "madlo u kabiny: opora při vstávání z křesla a při výstupu po schodech",
                                         where="x %s, y %s, z %s" % (fmt(x), fmt(y), fmt(z)), src="interior.decals.grab_bars[%d]" % i,
                                         pos=(x, y, z)))
        for p in self.placements:
            man = self.parts["SM_Kit_" + p.part]
            seen = {}
            for item in man.get("decal_items", []):
                seen[item] = seen.get(item, 0) + 1
                ident = "%s/%s" % (p.tag, item) + ("#%d" % seen[item] if seen[item] > 1 else "")
                lib = self.library.get(item, {})
                self.elements.append(Element(
                    ident, "decal", self.placement_room(p), "built", item,
                    "karta špíny" if item.startswith("grime") else self.decal_purpose(item), kit=p.part,
                    src="%s decal_items" % p.part, item=item, size=tuple(lib.get("size_m", (0, 0))), host=p.tag,
                    grime=item.startswith("grime")))

    # ------------------------------------------------------------------ fittings
    def _fittings(self):
        """The ship's own equipment on the walls (recipe interior.kit.fittings, hs_interior_kit.fittings): built in a
        room the kit does not build, or kept in one ("keep": the extinguisher by the hold's door); IDs in ids.fittings
        as [type, id] parallel to the list, Czech purposes in the design data's fitting_purpose."""
        fits = (self.recipe["interior"].get("kit") or {}).get("fittings", [])
        fids = self.ids.get("fittings") or []
        purp = self.design.get("fitting_purpose") or {}
        for i, f in enumerate(fits):
            pair = fids[i] if i < len(fids) else None
            ident = self._need_id(pair[1] if pair and pair[0] == f["type"] else None, "fitting", f["type"])
            x = f["at"][0] if f.get("at") else f["x"][0]
            x1 = f["at"][0] if f.get("at") else f["x"][-1]
            yw = f["at"][1] if f.get("at") else f["y"]
            rid = self.room_at((x + x1) / 2, yw - (0.1 if yw > 0 else -0.1))
            built = rid not in self.kit_rooms or f.get("keep")
            side = 1 if yw > 0 else -1
            depth = FITTING_DEPTH.get(f["type"], 0.1)
            z0, z1 = FITTING_Z.get(f["type"], (f.get("z", 1.0) - 0.1, f.get("z", 1.0) + 0.1))
            rect = [min(x, x1) - 0.1, max(x, x1) + 0.1] + sorted((yw, yw - side * depth))
            self.elements.append(Element(
                ident, "object", rid, "built" if built else "remove", FITTING_CZ.get(f["type"], f["type"]),
                purp.get(f["type"], ""), where="x %s, líc y %s, z %s … %s" % (
                    fmt((x + x1) / 2), fmt(yw), fmt(z0), fmt(z1)), src="interior.kit.fittings[%d]" % i, rect=rect,
                z=[z0, z1], fitting=f["type"],
                note="" if built else "vybavení lodi v místnosti, kterou staví kit: nestaví se"))

    def _stairs(self):
        """The stairs up to a raised room (the cockpit, Tools/Blender/hs_interior.stairs - its defaults read with ast,
        the riser count from the room's floor): an object with its ID in ids.stairs."""
        for rid, r in self.rooms.items():
            fl = r.get("floor") or 0.0
            if not fl:
                continue
            k = func_defaults(os.path.join(ROOT, "Tools", "Blender", "hs_interior.py"), "stairs")
            n = int(math.ceil(fl / k["rise_max"]))
            x1 = k["x0"] + (n - 1) * k["tread"] + 0.04
            ident = self._need_id((self.ids.get("stairs") or {}).get(rid), "stairs", rid)
            self.elements.append(Element(
                ident, "object", rid, "built", "schody", self.design.get("stairs_purpose", {}).get(rid, ""),
                where="x %s … %s, y ±%s, %d × %s / stupeň %s" % (fmt(k["x0"]), fmt(x1), fmt(k["half_w"]), n, fmt(fl / n, 3),
                                                              fmt(k["tread"])),
                src="hs_interior.stairs", rect=[k["x0"], x1, -k["half_w"], k["half_w"]], z=[0.0, fl], stairs=dict(k, n=n, rise=fl / n)))

    # ------------------------------------------------------------------ queries
    def in_room(self, rid, cats=None):
        return [e for e in self.elements if e.room == rid and (cats is None or e.cat in cats)]

    def decal_frame(self, e):
        """A projected decal (setup): centre, normal (out of the surface), the two in-plane half axes (layout
        metres) from its Unreal rotator [pitch, yaw, roll] and half size [depth, width, height] cm."""
        d = next(x for x in self.setup["decals"] if isinstance(x, dict) and x.get("id") == e.id)
        pitch, yaw, roll = (list(d.get("rotation", [0, 0, 0])) + [0, 0, 0])[:3]
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cr, sr = math.cos(math.radians(roll)), math.sin(math.radians(roll))
        X = (cp * cy, cp * sy, sp)                                         # FRotationMatrix
        Y = (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp)
        Z = (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
        lay = lambda v: (v[0], -v[1], v[2])                                   # noqa: E731  (Unreal y mirrored)
        s = d["size"]
        hy = tuple(c * s[1] / 100.0 for c in lay(Y))
        hz = tuple(c * s[2] / 100.0 for c in lay(Z))
        return e.extra["pos"], lay(X), hy, hz

    def face_of(self, e):
        """Where in its room an element is drawn: L / R the long walls (port, starboard), A / F the end walls
        (aft, forward), FLOOR (the plan) or CEIL (the ceiling plan)."""
        if e.cat == "wall":
            return e.extra["side"]
        p = e.extra.get("placement")
        if e.cat == "bulkhead":
            return "A" if p.dir_layout(1.0, 0.0)[0] > 0 else "F"
        if e.cat == "furniture" and p is not None:
            return "R" if p.dir_layout(1.0, 0.0)[1] > 0 else "L"
        if e.cat in ("floor", "component", "object", "furniture"):
            return "FLOOR"
        if e.cat == "ceiling":
            return "CEIL"
        host = self.by_id.get(e.extra.get("host")) if e.extra.get("host") else None
        if host is not None:
            return self.face_of(host)
        if e.cat == "door":
            if e.extra["axis"] == "y":
                return "R" if e.extra["at"][1] < 0 else "L"
            return None                          # an end wall: A in the room ahead of it, F in the room behind
        if e.cat == "decal" and e.extra.get("ray") and e.extra.get("dir"):
            dx, dy, dz = e.extra["dir"]
            if abs(dz) >= max(abs(dx), abs(dy)):
                return "FLOOR" if dz < 0 else "CEIL"
            if abs(dy) >= abs(dx):
                return "L" if dy > 0 else "R"
            return "F" if dx > 0 else "A"
        if e.cat == "decal" and e.extra.get("projected"):
            pos, n, _, _ = self.decal_frame(e)
            if abs(n[2]) > 0.7:
                return "FLOOR" if pos[2] < 1.0 else "CEIL"
            if abs(n[0]) > abs(n[1]):
                r = self.rooms[e.room]["rect"]
                return "A" if pos[0] < (r[0] + r[1]) / 2 else "F"
            return "L" if pos[1] > 0 else "R"
        if e.cat == "light":
            fl = self.rooms[e.room].get("floor", 0.0) or 0.0
            if e.extra["pos"][2] < fl - 0.1:
                return "FLOOR"                   # under a raised floor: the stairs' nosing lights, seen in plan
            if e.extra["pos"][2] >= fl + (2.0 if not fl else 1.3):      # a raised room: under its canopy
                return "CEIL"
            x, y, _ = e.extra["pos"]
            r = self.rooms[e.room]["rect"]
            dists = {"L": r[3] - y, "R": y - r[2], "A": x - r[0], "F": r[1] - x}
            return min(dists, key=dists.get)
        return None

    def door_face(self, e, rid):
        """An end-wall door seen from room rid: A when the door is at the room's aft end, else F."""
        if e.extra["axis"] == "y":
            return self.face_of(e)
        r = self.rooms[rid]["rect"]
        return "A" if abs(e.extra["at"][0] - r[0]) < abs(e.extra["at"][0] - r[1]) else "F"

    def x_range(self, e):
        """The element's extent along the ship (layout x), or None."""
        p = e.extra.get("placement")
        if p is not None:
            man = self.parts["SM_Kit_" + p.part]
            if e.cat in ("wall", "bulkhead"):
                pts = [p.ue_to_layout(a, b, 0) for a in (0.0, 15.0) for b in (0.0, -self.span(p) * 100.0)]
            elif e.cat == "furniture":
                dx, dy, _ = man["dims_m"]
                pts = [p.ue_to_layout(a * 100.0, b * 100.0, 0) for a in (0.0, dx) for b in (-dy / 2, dy / 2)]
            else:
                pts = [p.ue_to_layout(a, 0, 0) for a in (0.0, man["length_m"] * 100.0)]
            xs = [q[0] for q in pts]
            return min(xs), max(xs)
        if e.extra.get("rect"):
            return e.extra["rect"][0], e.extra["rect"][1]
        return None

    def sheet_views(self, rid, section_x, aft=False):
        """The IDs each view of a room's sheet draws and labels - the rule the drawing follows and the test checks:
        PLAN the kit parts, furniture, doors, components and objects, the floor's decals; RCP the ceiling and its
        lights; EL-L / EL-F / EL-R / EL-A the walls seen from the room (port, forward, starboard, aft) with what is
        on them - furniture, doors, decals, lights; SEC what the cross section at section_x cuts (layout objects and
        components as their boxes) and the under-floor components ahead of it. Grime cards are in the schedules only."""
        views = {k: set() for k in ("PLAN", "RCP", "EL-L", "EL-F", "EL-R", "EL-A", "SEC")}
        for e in self.elements:
            if not (e.room == rid or rid in (e.extra.get("rooms") or ())) or e.status == "remove" or e.extra.get("grime"):
                continue
            face = self.door_face(e, rid) if e.cat == "door" else self.face_of(e)
            if e.cat in ("wall", "bulkhead", "floor", "furniture", "door", "component", "object"):
                views["PLAN"].add(e.id)
            if e.cat == "ceiling":
                views["RCP"].add(e.id)
            if e.cat in ("wall", "bulkhead", "furniture", "door", "light", "decal") and face in ("L", "F", "R", "A"):
                views["EL-" + face].add(e.id)
            if e.cat == "object":
                for f in self.object_faces(e):
                    views["EL-" + f].add(e.id)
            if e.cat in ("light", "decal") and face == "CEIL":
                views["RCP"].add(e.id)
            if e.cat in ("light", "decal") and face == "FLOOR":
                views["PLAN"].add(e.id)
            xr = self.x_range(e)
            if e.cat in ("wall", "floor", "ceiling", "furniture", "component", "object") and xr and                     xr[0] - 1e-6 <= section_x <= xr[1] + 1e-6:
                views["SEC"].add(e.id)
            if e.cat == "component" and e.extra.get("below") and xr and \
                    ((xr[0] <= section_x + 1e-6) if aft else (xr[1] >= section_x - 1e-6)):
                views["SEC"].add(e.id)                      # what is under the floor ahead: dashed beyond the cut
        return views

    def y_range(self, e):
        """The element's extent across the ship (layout y), or None."""
        p = e.extra.get("placement")
        if p is not None:
            man = self.parts["SM_Kit_" + p.part]
            if e.cat in ("wall", "bulkhead"):
                pts = [p.ue_to_layout(a, b, 0) for a in (0.0, 15.0) for b in (0.0, -self.span(p) * 100.0)]
            elif e.cat == "furniture":
                dx, dy, _ = man["dims_m"]
                pts = [p.ue_to_layout(a * 100.0, b * 100.0, 0) for a in (0.0, dx) for b in (-dy / 2, dy / 2)]
            else:
                hw = man["dims_m"][1] / 2
                pts = [p.ue_to_layout(0, b * 100.0, 0) for b in (-hw, hw)]
            ys = [q[1] for q in pts]
            return min(ys), max(ys)
        if e.cat == "door":
            y, w = e.extra["at"][1], e.extra["width"]
            return (y - w / 2, y + w / 2) if e.extra["axis"] == "x" else (y, y)
        if e.extra.get("rect"):
            return e.extra["rect"][2], e.extra["rect"][3]
        if e.extra.get("pos"):
            return e.extra["pos"][1], e.extra["pos"][1]
        return None

    def deck_views(self, section_y):
        """The IDs each view of the deck sheet (I-01) draws and labels - the rule the drawing follows and the test
        checks: PLAN every kit part on the floor plan and in the walls (walls, bulkheads, floors), the furniture, doors,
        components and objects of every room; LSEC the longitudinal section at y = section_y looking to port: the
        ceilings and bulkheads it cuts, the port walls beyond it, the doors in the bulkheads it passes and the
        furniture, components and objects that reach beyond it; DECALS (I-07) and LIGHTS (I-08) every decal and light
        of the rooms (grime cards in the tables only)."""
        views = {"PLAN": set(), "LSEC": set(), "DECALS": set(), "LIGHTS": set()}
        for e in self.elements:
            if e.room is None or e.status == "remove" or e.extra.get("grime"):
                continue
            if e.cat == "decal" and e.extra.get("item") != "scatter":
                views["DECALS"].add(e.id)              # I-07: every sign and decal of a room, in plan by its host or place
            if e.cat == "light":
                views["LIGHTS"].add(e.id)              # I-08: every light of a room, in plan
            if e.cat in ("wall", "bulkhead", "floor", "furniture", "door", "component", "object"):
                views["PLAN"].add(e.id)
            yr = self.y_range(e)
            if e.cat in ("ceiling", "bulkhead") or (e.cat == "wall" and e.extra.get("side") == "L") or \
                    (e.cat == "door" and e.extra["axis"] == "x" and yr[0] <= section_y <= yr[1]) or \
                    (e.cat in ("furniture", "component", "object") and yr and yr[1] > section_y):
                views["LSEC"].add(e.id)
        return views

    def room_placements(self, rid):
        return [p for p in self.placements if self.placement_room(p) == rid]

    def kit_fbx(self, part):
        return os.path.join(KIT_EXPORT, "SM_Kit_%s.fbx" % part)

    def ship_fbx(self, which=""):
        return os.path.join(ROOT, "ArtSource", "Ships", self.ship, "Export", "SM_Ship_%s%s.fbx" % (self.ship, which))

    def geometry_ready(self):
        return not is_lfs_pointer(self.ship_fbx("_Interior")) and not is_lfs_pointer(self.kit_fbx(self.placements[0].part))


# the component bays' openings: in from both ends of the module (Tools/Kit/kit_batch4.py bay_power / bay_cooler / bay_shield:
# hole = (0.1, L - 0.1, SILL, HEAD), the cooler's 0.09)
BAY_HOLE = {"A": 0.1, "B": 0.09, "C": 0.1}
_BAY_K = {}


def bay_constants():
    """BAY_DEPTH, LINER, SILL, HEAD of the kit's component bays (Tools/Kit/kit_batch4.py, read with ast: it imports
    Blender)."""
    if not _BAY_K:
        tree = ast.parse(open(os.path.join(ROOT, "Tools", "Kit", "kit_batch4.py"), encoding="utf-8").read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)                     and node.targets[0].id in ("BAY_DEPTH", "LINER", "SILL", "HEAD"):
                _BAY_K[node.targets[0].id] = ast.literal_eval(node.value)
    return _BAY_K


# the fittings' extent off the wall and their height (Tools/Blender/hs_interior_kit.fittings)
FITTING_CZ = {"extinguisher": "hasicí přístroj", "handrail": "madlo", "vent": "větrací mřížka", "junction": "rozvodná skříňka",
              "conduit": "kabelová chránička"}
FITTING_DEPTH = {"extinguisher": 0.17, "handrail": 0.09, "vent": 0.03, "junction": 0.14, "conduit": 0.05}
FITTING_Z = {"extinguisher": (0.5, 1.1), "vent": (0.12, 0.32)}


def ray_dir(it):
    """An interior decal's ray (interior.decals.items: "dir", or "to" from "from"), normalised."""
    d = it.get("dir") or [b - a for a, b in zip(it["from"], it["to"])]
    n = math.sqrt(sum(c * c for c in d)) or 1.0
    return tuple(c / n for c in d)


def func_defaults(path, name):
    """The keyword defaults of a function in a script (ast: the Blender builders import bpy)."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    args = fn.args.args[-len(fn.args.defaults):]
    return {a.arg: ast.literal_eval(d) for a, d in zip(args, fn.args.defaults)}


def _inside(p, poly):
    x, y = p
    n = 0
    for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
        if (ay <= y < by) or (by <= y < ay):
            if ax + (y - ay) * (bx - ax) / (by - ay) > x:
                n += 1
    return n % 2 == 1


def _rect_txt(o):
    r = o["rect"]
    s = "x %s … %s, y %s … %s" % (fmt(r[0]), fmt(r[1]), fmt(r[2]), fmt(r[3]))
    if o.get("z"):
        s += ", z %s … %s" % (fmt(o["z"][0]), fmt(o["z"][1]))
    return s


# ---------------------------------------------------------------------- IDs for new data (assign_interior_ids.py)
def proposed_kit_ids(model):
    """[(placement, id)] for kit parts without an ID: <ROOM>-W-<L|R><n> wall modules from aft, <ROOM>-B-<A|F> a
    room's aft and forward bulkhead faces, <ROOM>-C-<n> ceilings and <ROOM>-FL-<n> floors from aft, furniture the ID of
    the layout object it builds (its rect holds the part's pivot), else <ROOM>-U-<nn>."""
    out = []
    used = {p.id for p in model.placements if p.id}
    for p in model.placements:
        if p.id:
            continue
        rid = model.placement_room(p)
        code = model.room_code(rid)
        cat = CAT_OF_KIT.get(p.category, p.category.lower())
        if cat == "wall":
            side = model.side_of(p)
            same = [q for q in model.placements if CAT_OF_KIT.get(q.category) == "wall" and model.placement_room(q) == rid
                    and model.side_of(q) == side]
            same.sort(key=lambda q: min(q.ue_to_layout(0, 0, 0)[0], q.ue_to_layout(0, -model.span(q) * 100, 0)[0]))
            ident = "%s-W-%s%d" % (code, side, same.index(p) + 1)
        elif cat == "bulkhead":
            fx, _ = p.dir_layout(1.0, 0.0)
            ident = "%s-B-%s" % (code, "A" if fx > 0 else "F")
        elif cat in ("ceiling", "floor"):
            pre = {"ceiling": "C", "floor": "FL"}[cat]
            same = [q for q in model.placements if CAT_OF_KIT.get(q.category) == cat and model.placement_room(q) == rid]
            same.sort(key=lambda q: q.ue_to_layout(0, 0, 0)[0])
            ident = "%s-%s-%d" % (code, pre, same.index(p) + 1)
        elif cat == "furniture":
            x, y = p.x, -p.y_ue
            obj = next((o for o in model.layout["objects"] if model.object_id(o) and o["room"] == rid and
                        o["rect"][0] - 0.02 <= x <= o["rect"][1] + 0.02 and o["rect"][2] - 0.02 <= y <= o["rect"][3] + 0.02), None)
            if obj:
                ident = model.object_id(obj)
            else:
                n = 1
                while "%s-U-%02d" % (code, n) in used:
                    n += 1
                ident = "%s-U-%02d" % (code, n)
        else:
            n = 1
            while "%s-%s-%02d" % (code, cat[:2].upper(), n) in used:
                n += 1
            ident = "%s-%s-%02d" % (code, cat[:2].upper(), n)
        if ident in used:
            raise SystemExit("duplicate kit id %s" % ident)
        used.add(ident)
        out.append((p, ident))
    return out


def main(argv):
    ship = argv[0] if argv else "Wayfarer"
    m = Model(ship)
    for rid, r in m.rooms.items():
        es = m.in_room(rid)
        cats = {}
        for e in es:
            cats[e.cat] = cats.get(e.cat, 0) + 1
        print("INTMODEL %s (%s, %s): %s" % (rid, r["code"], "kit" if r["kit"] else "ship", ", ".join("%s %d" % kv for kv in sorted(cats.items()))))
    print("INTMODEL %d elements, %d without a room" % (len(m.elements), len([e for e in m.elements if e.room is None])))
    for ident, txt in m.checks:
        print("INTMODEL check %s: %s" % (ident, txt))


if __name__ == "__main__":
    main(sys.argv[1:])
