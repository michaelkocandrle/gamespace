"""Interior design drawings of a ship (dossier bod 4, author 1. 10. 2026), drawn from the parts as they are built:
the kit parts' FBX placed as the game places them (Tools/Kit/kit_layout.py), the ship's own interior and hull FBX,
with every element's ID, status and purpose from the interior model (Tools/Design/interior_model.py). The same
sheet language as the exterior (draw_exterior_sheet.py: frame, title block, leader labels, status colours).

    python Tools/Design/draw_interior_sheet.py [Wayfarer] [--dpi 200] [--sheets I-04]

A room sheet (I-04 the cabin, the sample for the author's approval of the style): the plan cut at 1.2 m on the kit's
0.3 m grid, the reflected ceiling plan with its lights, the room's four walls developed in one strip as seen from
inside, a cross section with the character's capsule, the legend, the room's schedules (kit parts, furniture, doors,
components, lights, decals), the data check and the title block. Writes ArtSource/Ships/<Ship>/Design/Drawings/
<Ship>_I04_cabin.png and .json (the IDs drawn and labelled per view - Tools/Tests/test_interior_drawing.py) and a
vector copy in Saved/Drawings. Needs the FBX files from Git LFS (not in CI; the test reads only the sidecar).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon as MplPolygon
from shapely.geometry import box

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw_exterior_sheet as ds  # noqa: E402
import fbx_mesh  # noqa: E402
import interior_model as im  # noqa: E402
import mesh_draw as md  # noqa: E402
from draw_exterior_sheet import GREY, INK, LIGHT, PT, STATUS_COL, STATUS_MARK, TITLE_MM  # noqa: E402

S20 = 1000.0 / 20.0
PLAN_MX, PLAN_HY = 0.32, 2.66          # plan window: margin along x, half height (room for the dimension chains)
GRID_COL = "#3F7FBF"
DECAL_FILL = (0.91, 0.86, 0.97)
DECAL_EDGE = "#7B4FB0"
LIGHT_FILL = {"warm": "#F2B35C", "cool": "#5AA9F0", "work": "#F7D27A", "neutral": "#E9DCC6", "signal": "#F06A2A"}
LIGHT_ROLE_CZ = {"warm": "teplá bílá", "cool": "studená modrá", "work": "pracovní bílá", "neutral": "neutrální bílá",
                 "signal": "signální oranžová"}
LIGHT_TYPE_CZ = {"spot": "bodovka (kužel)", "point": "bodové", "rect": "lineární (pás)"}
SOCKET_CZ = {"Cove": "římsa stěny", "Wash": "osvětlení stěny", "Down": "pracovní světlo dolů", "Halo": "svatozář stropu",
             "Scallop": "bodovka na stěnu", "Linear": "lineární světlo stropu", "Berth": "světlo pod policí",
             "Reading": "lampička", "Suit": "světlo ve skříni", "Bay": "světlo výdejníku", "Seat": "světlo nad sedátkem",
             "Status": "stavové světlo dveří", "Door": "světlo nad dveřmi", "Reveal": "světlo ostění",
             "Emitter": "prstenec emitoru", "Channel": "světlo kanálu", "Linear_0": "lineární"}
SHIP_GLOW_CZ = {"int_light": "teplý pás", "int_glow": "studený pás (UI)", "int_accent_glow": "oranžový akcent"}
SHIP_LIGHT_CZ = {"L-FIX": "světlo svítícího pásu nebo lampy lodi", "L-FIX-stair": "náběžná hrana schodu",
                 "L-INT": "světlo místnosti lodi (konzole, nohy, deska, kabina)",
                 "L-SET": "z nastavení lodi: světlo pilota, záře obrazovek"}
FACE_CZ = {"L": "levobok", "F": "přední stěna", "R": "pravobok", "A": "zadní stěna"}
SHEETS = {"I-01": ("I01_deck", "Interiér – hlavní paluba: půdorys v mřížce kitu 0,3 m s ID dílů, podélný řez, místnosti"),
          "I-02": ("I02_hold", "Interiér – nákladový prostor: půdorys v mřížce kitu, strop, rozvinuté stěny, řez, světla"),
          "I-03": ("I03_tech", "Interiér – technická chodba: půdorys, strop, rozvinuté stěny, řez, komponenty, světla"),
          "I-04": ("I04_cabin", "Interiér – kajuta: půdorys v mřížce kitu, strop, rozvinuté stěny, řez, světla, decaly"),
          "I-06": ("I06_sections", "Interiér – průřezy s kapslí postavy: rampa, náklad, chodba, kajuta, kokpit; průchodnost"),
          "I-05": ("I05_cockpit", "Interiér – kokpit: půdorys se schody, kabina zespodu, rozvinuté stěny, řez, oko pilota, světla")}
# the title block's cells per sheet: I-04 the sample approved as the style (author 1. 10. 2026), the rest drawn in it
SHEET_META = {"I-04": {"list": "I-04 (vzorový list)", "state": "VZOR KE SCHVÁLENÍ STYLU",
                       "revs": ["A  1. 10. 2026  vzorový list interiéru I-04 ke schválení stylu"]}}
SHEET_META_DEFAULT = {"date": "2. 10. 2026", "rev": "A", "state": "KE SCHVÁLENÍ AUTOREM", "revs": ["A  {date}  první vydání ve stylu I-04 (schválen 1. 10. 2026)"]}
PLANNED = [("I-01", "Půdorys paluby v mřížce kitu 0,3 m (celá loď)"), ("I-02", "Nákladový prostor"),
           ("I-03", "Technická chodba s komponentami"), ("I-04", "Kajuta"), ("I-05", "Kokpit"),
           ("I-06", "Průřezy s kapslí postavy (rampa, náklad, chodba, kajuta, kokpit)"),
           ("I-07", "Plán nápisů a decalů"), ("I-08", "Plán světel a výkon"),
           ("I-09", "Rozpisy dveří, nábytku a komponent"), ("K-01…K-05", "Koncepty (dossier bod 6)")]


# ---------------------------------------------------------------------- colours
def colours(m):
    """Material name -> drawing tint: the kit's slot roles in the ship's palette, the ship's own materials from its
    recipe; decal materials are drawn from the data (overlays), grime is not drawn."""
    pal = m.rules["palettes"]["Halcyon"]
    lin = dict(pal)
    lin.update({"Kit_Rubber": (0.03, 0.03, 0.032), "Kit_Plastic": (0.05, 0.05, 0.055), "Kit_Trim": (0.15, 0.15, 0.15),
                "Kit_Seal": (0.02, 0.02, 0.022), "Kit_GlowDim": (0.45, 0.42, 0.38), "Kit_Fabric": (0.08, 0.095, 0.12),
                "Kit_Cushion": (0.1, 0.1, 0.1), "Kit_Glass": (0.55, 0.65, 0.7), "Kit_Screen": (0.12, 0.35, 0.6)})
    out = {}
    for k, c in lin.items():
        glow = "Glow" in k or k == "Kit_Screen"
        out[k] = md.tint(c, 0.62 if glow else (0.62 if k == "Kit_Signal" else 0.4))
    out["Kit_DecalPaint"] = DECAL_FILL
    out["Kit_DecalGrime"] = None
    for key, mat in m.recipe["materials"].items():
        if key.startswith("_") or not isinstance(mat, dict):
            continue
        name = "M_Ship_%s_%s" % (m.ship, mat["slot"])
        c = mat.get("emit") if mat.get("emit") and max(mat["colour"]) < 0.2 else mat["colour"]
        out[name] = md.tint(c, 0.62 if mat.get("emit") else 0.4)
    for n in ("Decal", "DecalAO", "DecalPaint", "Trim", "TrimAO", "DecalGrime"):
        out["M_Ship_%s_%s" % (m.ship, n)] = None
    out["M_Ship_%s_DecalPaint" % m.ship] = DECAL_FILL
    return out


def kit_constants(fn, names):
    """Module-level constants of a kit builder (Tools/Kit/<fn>), read with ast: the builders import Blender."""
    import ast
    tree = ast.parse(open(os.path.join(im.ROOT, "Tools", "Kit", fn), encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in names:
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


def hexrgb(c):
    return "#%02X%02X%02X" % tuple(int(round(255 * v)) for v in c[:3])


# ---------------------------------------------------------------------- geometry
class Geo:
    """The built meshes in layout metres, as mesh_draw parts, cached."""

    def __init__(self, m):
        self.m = m
        self._kit = {}
        self._ship = {}

    def kit(self, p):
        if p.tag not in self._kit:
            mesh = fbx_mesh.read(self.m.kit_fbx(p.part))["meshes"][0]
            X, Y, Z = p.to_layout(mesh.verts[:, 0], mesh.verts[:, 1], mesh.verts[:, 2])
            mats = np.array(mesh.materials)[np.minimum(mesh.mat, len(mesh.materials) - 1)]
            part = md.Part(p.tag, np.stack([X, Y, Z], -1), mesh.tris, mats)
            part.uv = mesh.uv
            self._kit[p.tag] = part
        return self._kit[p.tag]

    def ship(self, which, box_=None):
        """The ship's own mesh (which: "" hull, "_Interior") in layout metres, optionally only the triangles whose
        centre lies in box_ ((lo), (hi))."""
        key = (which, None if box_ is None else tuple(map(tuple, box_)))
        if key not in self._ship:
            mesh = fbx_mesh.read(self.m.ship_fbx(which))["meshes"][0]
            V = mesh.verts - np.asarray(self.m.offset)
            T = mesh.tris
            mats = np.array(mesh.materials)[np.minimum(mesh.mat, len(mesh.materials) - 1)]
            if box_ is not None:
                cen = V[T].mean(axis=1)
                lo, hi = (np.asarray(a) for a in box_)
                keep = np.all((cen >= lo) & (cen <= hi), axis=1)
                T, mats = T[keep], mats[keep]
            self._ship[key] = md.Part("ship" + which, V, T, mats)
        return self._ship[key]

    def kit_decals(self, p):
        """The kit part's decals as built (Kit_DecalPaint faces, and the structural ones' normal-only Kit_Decal faces -
        rivet rows in the component bays, I-03), identified by their UVs in the decal library:
        {element id: (centre, paper-independent quad points)} in layout metres, IDs as interior_model names them
        (the second copy of an item #2, in order along x, y, z)."""
        part = self.kit(p)
        lib = self.m.library
        sel = np.nonzero((part.mats == "Kit_DecalPaint") | (part.mats == "Kit_Decal"))[0]
        if not len(sel):
            return {}
        uvc = part.uv[sel].mean(axis=1)
        groups = {}
        for ti, (u, v) in zip(sel, uvc):
            item = next((k for k, d in lib.items() if d["uv"][0] <= u <= d["uv"][2] and d["uv"][1] <= v <= d["uv"][3]), None)
            if item is None:
                continue
            pts = part.verts[part.tris[ti]]
            c = pts.mean(axis=0)
            for g in groups.setdefault(item, []):
                if np.linalg.norm(g["c"] - c) < 0.25:
                    g["pts"].append(pts)
                    g["c"] = np.concatenate(g["pts"]).mean(axis=0)
                    break
            else:
                groups[item].append({"c": c, "pts": [pts]})
        out = {}
        for item, gs in groups.items():
            gs.sort(key=lambda g: (round(g["c"][0], 2), round(g["c"][1], 2), round(g["c"][2], 2)))
            for k, g in enumerate(gs):
                ident = "%s/%s" % (p.tag, item) + ("#%d" % (k + 1) if k else "")
                out[ident] = (g["c"], np.concatenate(g["pts"]))
        return out


# ---------------------------------------------------------------------- the room sheet
class RoomSheet:
    def __init__(self, m, geo, rid, section_x, aft=False, sheet=None):
        self.m, self.geo, self.rid, self.section_x, self.aft = m, geo, rid, section_x, aft
        self.room = m.rooms[rid]
        self.sh = sheet or ds.Sheet()
        self.d = ds.Drawer(self.sh, None)
        self.cols = colours(m)
        self.views = m.sheet_views(rid, section_x, aft=aft)
        self.drawn = {k: set() for k in self.views}
        self.places = m.room_placements(rid)
        r = self.room["rect"]
        self.x0, self.x1, self.y0, self.y1 = r
        # neighbours' faces that close the room (the corridor's forward face behind the aft bulkhead)
        self.parts = [geo.kit(p) for p in self.places]
        self.ctx = [geo.kit(p) for p in m.placements if p not in self.places and
                    self.x0 - 0.35 <= p.x <= self.x1 + 0.35 and m.placement_room(p) != rid]
        # whole meshes: a box on the triangles' centres dropped the hull's long belly panels from the cuts
        self.interior = geo.ship("_Interior")
        self.hull = geo.ship("")
        self.canopy = geo.ship("_Canopy")
        self.fz = self.room.get("floor", 0.0) or 0.0      # the room's floor over the deck (the cockpit: +1.15)
        self.decal_pos = {}
        for p in self.places:
            for ident, v in geo.kit_decals(p).items():
                self.decal_pos[ident] = v
        for e in m.in_room(rid, ("decal",)):
            if e.extra.get("ray") and e.extra.get("dir") and e.status != "remove":
                q = self.ray_decal(e)
                if q is not None:
                    self.decal_pos[e.id] = q
        self.el = {e.id: e for e in m.elements}
        cen = self.interior.verts[self.interior.tris].mean(axis=1)
        inside = (cen[:, 0] > self.x0 - 0.3) & (cen[:, 0] < self.x1 + 0.3)
        self.ship_mats = set(np.unique(self.interior.mats[inside]).tolist())

    def clear_height(self, x, floor, band=0.3, xs=None):
        """The clear height over a floor from every built mesh (kit parts, the ship's interior, the hull, the canopy and
        its frame): the lowest face cut by the planes x = const (x, or each of xs) within band of the centre line,
        0.6 m or more over the floor (round 2 of I-01: the canopy's ribs hang lower than its glass)."""
        best = None
        for xx in (xs or [x]):
            for part in self.parts + [self.interior, self.hull, self.canopy]:
                lo, hi = part.verts.min(0), part.verts.max(0)
                if not (lo[0] - 0.01 <= xx <= hi[0] + 0.01):
                    continue
                for a, b in md._slice(part.verts, part.tris, np.array((xx, 0, 0.0)), np.array((1.0, 0, 0))):
                    # the segment clipped to the band (a rib's underside crosses it from one side to the other)
                    pts = [q for q in (a, b) if abs(q[1]) <= band]
                    if abs(b[1] - a[1]) > 1e-9:
                        for yb in (-band, band):
                            t = (yb - a[1]) / (b[1] - a[1])
                            if 0.0 < t < 1.0:
                                pts.append(a + t * (b - a))
                    for q in pts:
                        if q[2] > floor + 0.6 and (best is None or q[2] < best[0]):
                            best = (float(q[2]), xx, float(q[1]))
        if best is None:
            return None
        self.clear_at = best
        return best[0] - floor

    def ray_decal(self, e):
        """Where an interior decal cast by a ray lands (interior.decals.items: from a point along dir, as hs_interior_decals
        places it): the nearest hit on the ship's interior, a quad of the library item's size facing the ray."""
        o = np.asarray(e.extra["pos"], dtype=float)
        d = np.asarray(e.extra["dir"], dtype=float)
        V, T = self.interior.verts, self.interior.tris
        a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        lo, hi = np.minimum(o, o + 3.0 * d) - 0.05, np.maximum(o, o + 3.0 * d) + 0.05
        near = np.all((np.minimum(np.minimum(a, b), c) <= hi) & (np.maximum(np.maximum(a, b), c) >= lo), axis=1)
        a, b, c = a[near], b[near], c[near]
        e1, e2 = b - a, c - a
        pv = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, pv)
        ok = np.abs(det) > 1e-9
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        tv = o - a
        u = np.einsum("ij,ij->i", tv, pv) * inv
        qv = np.cross(tv, e1)
        v = (qv @ d) * inv
        t = np.einsum("ij,ij->i", e2, qv) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4)
        if not hit.any():
            return None
        tt = float(t[hit].min())
        h = o + d * tt
        n = -d / np.linalg.norm(d)
        ax = np.array((1.0, 0, 0)) if abs(n[2]) > 0.7 else np.cross((0, 0, 1.0), n)
        ax = ax / np.linalg.norm(ax)
        ay = np.cross(n, ax)
        w, hh = (e.extra.get("size") or (0.1, 0.05))[:2]
        pts = np.array([h + sx * ax * w / 2 + sy * ay * hh / 2 + n * 0.002 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        return h, pts

    # ------------------------------------------------------------------ small helpers
    def mark(self, view, ident):
        self.drawn.setdefault(view, set()).add(ident)

    def lab(self, view, ident):
        self.d.labelled.setdefault(view, set()).add(ident)

    def boxed(self, x, y, text, size, col):
        """Centred text on a white box wide enough to break the leaders that pass it (verification round of I-04)."""
        self.sh.ax.text(x, y, text, fontsize=size * PT, color=col, ha="center", va="baseline", zorder=45,
                        bbox=dict(boxstyle="square,pad=0.35", fc="white", ec="none"))

    def title(self, x, y, text, scale="1 : 20"):
        self.sh.t(x, y, text, TITLE_MM, weight="bold")
        self.sh.t(x + self.sh.width(text, TITLE_MM) + 10, y, scale, TITLE_MM)

    def req(self, view, ident, X, Y, hidden=False, text=None):
        e = self.el.get(ident)
        st = e.status if e else "built"
        return {"id": ident, "text": text or (ident + ((" " + STATUS_MARK[st]) if STATUS_MARK[st] else "")),
                "anchor": (X, Y), "col": STATUS_COL[st], "z": Y, "hidden": hidden}

    def lamp(self, X, Y, e, fr_dir=None, tag=True, size=1.25):
        """A light symbol in the light's colour: spot = circle with a cross (and its aim in a side view), point =
        circle, rect = a bar along its width; a filled corner triangle = casts shadows; i = only under the interior
        lighting."""
        sh = self.sh
        col = STATUS_COL[e.status]
        role = e.extra.get("role")
        fill = LIGHT_FILL.get(role) if role else hexrgb(md.tint(e.extra["colour"], 0.75))
        t = e.extra["type"]
        r = size
        if t == "rect" and fr_dir is not None:
            (ax_, ay_), half = fr_dir
            a = (X - ax_ * half, Y - ay_ * half)
            b = (X + ax_ * half, Y + ay_ * half)
            sh.line([a, b], 1.3, col, z=31, cap="round")
            sh.line([a, b], 0.9, fill, z=31.1, cap="round")
        else:
            sh.ax.add_patch(Circle((X, Y), r, fc=fill, ec=col, lw=0.22 * PT, zorder=31))
            if t == "spot":
                sh.line([(X - r * 0.7, Y - r * 0.7), (X + r * 0.7, Y + r * 0.7)], 0.18, col, z=31.2)
                sh.line([(X - r * 0.7, Y + r * 0.7), (X + r * 0.7, Y - r * 0.7)], 0.18, col, z=31.2)
        if e.extra.get("shadow"):
            sh.ax.add_patch(MplPolygon([(X + r * 0.9, Y + r * 0.9), (X + r * 2.0, Y + r * 0.9), (X + r * 0.9, Y + r * 2.0)],
                                       closed=True, fc=INK, ec="none", zorder=31.3))
        if tag:
            short = e.id.split("/")[-1].split("_")[0] if "/" in e.id else e.id
            if t == "rect" and fr_dir is not None:
                (ax_, ay_), half = fr_dir
                X, Y = X + ax_ * half * 0.55, Y + ay_ * half * 0.55
            tags = self.__dict__.setdefault("_tags", [])
            while any(abs(X - a) < 6 and abs(Y - b) < 2.4 for a, b in tags):
                Y -= 2.6                                          # a tag on the same spot (Door / Reveal over a door)
            tags.append((X, Y))
            sh.t(X + r + 0.6, Y - r - 1.4, short + (" i" if e.extra.get("interior_only") else ""), 2.0, col, z=31.4,
                 bg="white")

    def draw_lights(self, view, vw, lights, side=False):
        """The view's lights: a bar along a linear light's width, a symbol for the others; symbols closer than 2.5 mm
        (the ceiling's down-light and its halo share a spot) as one symbol with rings round it and one tag."""
        s = vw.s
        pts = []
        for e in lights:
            X, Y = vw.P(e.extra["pos"])
            self.mark(view, e.id)
            self.lab(view, e.id)
            if e.extra["type"] == "rect" and e.extra.get("width_cm"):
                a = np.asarray(e.extra.get("along") or (0, 1, 0), dtype=float)
                au, av = a @ vw.u, a @ vw.v
                n = math.hypot(au, av)
                if n > 0.3:
                    self.lamp(X, Y, e, ((au / n, av / n), e.extra["width_cm"] / 200.0 * s * n))
                    continue
            pts.append((X, Y, e))
        used = [False] * len(pts)
        for i, (X, Y, e) in enumerate(pts):
            if used[i]:
                continue
            group = [e]
            for j in range(i + 1, len(pts)):
                if not used[j] and math.hypot(pts[j][0] - X, pts[j][1] - Y) < 2.5:
                    used[j] = True
                    group.append(pts[j][2])
            group.sort(key=lambda g: {"spot": 0, "point": 1}.get(g.extra["type"], 2))
            for k, g in enumerate(group[1:], 1):
                fill = LIGHT_FILL.get(g.extra.get("role")) or hexrgb(md.tint(g.extra["colour"], 0.75))
                self.sh.ax.add_patch(Circle((X, Y), 1.25 + 0.9 * k, fc="none", ec=fill, lw=0.7 * PT, zorder=30.8 - k * 0.01))
                self.sh.ax.add_patch(Circle((X, Y), 1.25 + 0.9 * k + 0.4, fc="none", ec=STATUS_COL[g.status], lw=0.12 * PT,
                                            zorder=30.9))
            self.lamp(X, Y, group[0], tag=False)
            tag = " · ".join(g.id.split("/")[-1].split("_")[0] + (" i" if g.extra.get("interior_only") else "")
                             for g in group)
            r = 1.25 + 0.9 * (len(group) - 1)
            tags = self.__dict__.setdefault("_tags", [])
            ty = Y
            while any(abs(X - a_) < 12 and abs(ty - b_) < 2.6 for a_, b_ in tags):
                ty -= 2.8                                          # two tags on the same spot: one under the other
            tags.append((X, ty))
            if ty != Y:
                self.sh.line([(X, Y), (X + r + 0.6, ty - r - 0.4)], 0.1, STATUS_COL[group[0].status], z=31.3)
            self.sh.t(X + r + 0.6, ty - r - 1.2, tag, 2.0, STATUS_COL[group[0].status], z=31.4, bg="white")
            if side:
                for g in group:
                    self.aim(vw, X, Y, g)

    def aim(self, view, X, Y, e):
        """A spot's aim in a side view (elevation, section): the cone's two edges."""
        d = e.extra.get("dir")
        if e.extra["type"] != "spot":
            return
        d = np.asarray(d if d is not None else (0, 0, -1), dtype=float)
        u, v = d @ view.u, d @ view.v
        n = math.hypot(u, v)
        if n < 0.2:
            return
        u, v = u / n, v / n
        half = math.radians((e.extra.get("cone") or 40) / 2)
        for s in (-1, 1):
            c, si = math.cos(s * half), math.sin(s * half)
            du, dv = u * c - v * si, u * si + v * c
            self.sh.line([(X + du * 1.4, Y + dv * 1.4), (X + du * 6.5, Y + dv * 6.5)], 0.13, STATUS_COL[e.status], z=30.5)

    def decal_overlay(self, view, e, vw):
        """A decal: the built quad (kit decals, from the FBX) or the projected box (setup) in violet, its
        reading direction for lettering."""
        if e.id in self.decal_pos:
            # the decal's own faces are in the views (violet where nothing stands in front of them); over them only
            # its frame, dashed - a decal behind a shelf shows as a frame (verification round of I-04)
            c, pts = self.decal_pos[e.id]
            P = vw.paper(pts)
            x0, y0 = P.min(0)
            x1, y1 = P.max(0)
            self.sh.rect(x0 - 0.2, y0 - 0.2, x1 + 0.2, y1 + 0.2, ec=DECAL_EDGE, lw=0.18, ls="--", z=20.5)
            return vw.P(c)
        if e.extra.get("projected"):
            pos, n, hy, hz = self.m.decal_frame(e)
            pos, hy, hz = (np.asarray(a) for a in (pos, hy, hz))
            quad = [pos - hy - hz, pos + hy - hz, pos + hy + hz, pos - hy + hz]
            P = vw.paper(np.asarray(quad))
            self.sh.ax.add_patch(MplPolygon(P, closed=True, fc=hexrgb(DECAL_FILL), ec=DECAL_EDGE, lw=0.2 * PT,
                                            ls=(0, (2.0, 1.0)), zorder=20))
            return vw.P(pos)
        return None

    # ------------------------------------------------------------------ views
    def plan(self, ox, oy, view="PLAN"):
        """The plan cut at 1.2 m above the deck, looking down; the kit grid over the floor."""
        m, sh = self.m, self.sh
        s = S20
        u0, v0 = self.x0 - PLAN_MX, -PLAN_HY
        vw = md.View((1, 0, 0), (0, 1, 0), (0, 0, -1), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + PLAN_MX - u0) * s, oy + 2 * PLAN_HY * s)
        cut = ((0, 0, self.fz + 1.2), (0, 0, -1))
        clip = ((self.x0 - 0.45, -2.8, -0.4), (self.x1 + 0.45, 2.8, self.fz + 1.2))
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(sh.ax, vw, [self.hull, self.canopy], self.cols, clip=clip, cut=cut, window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        if any(p.category == "Wall" for p in self.places):
            self.grid(vw, W)
        else:
            self.grid_origin = None
        reqs = []
        self.draw_lights(view, vw, [self.el[i] for i in sorted(self.views[view]) if self.el[i].cat == "light"])
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            a = self.anchor_plan(e)
            if a is None or e.cat == "light" or (e.extra.get("placement") is not None and ident not in tags):
                continue
            if e.cat == "decal":
                if self.decal_overlay(view, e, vw) is None:
                    continue
            self.mark(view, ident)
            if e.cat in ("component", "object") and e.extra.get("rect"):
                r = e.extra["rect"]
                self.previous(vw, e, lambda rr, zz: (vw.P((rr[0], rr[2], 0)), vw.P((rr[1], rr[3], 0))))
                self.proposal(vw, e, lambda rr, zz: (vw.P((rr[0], rr[2], 0)), vw.P((rr[1], rr[3], 0))))
                P0, P1 = vw.P((r[0], r[2], 0)), vw.P((r[1], r[3], 0))
                sh.rect(P0[0], P0[1], P1[0], P1[1], ec=STATUS_COL[e.status], lw=0.35, ls="--", z=25)
                if e.extra.get("below"):
                    sh.t(min(P0[0], P1[0]) + 1.0, max(P0[1], P1[1]) - 3.0, "pod podlahou", 2.0, STATUS_COL[e.status],
                         z=25.5, bg="white")
            if e.cat == "door":
                self.door_plan(vw, e)
            reqs.append(self.req(view, ident, *vw.P(a), hidden=bool(e.extra.get("below"))))
        self.section_mark(vw, W)
        self.view_keys(vw)
        self.room_text(vw)
        self.plan_dims(vw)
        self.door_approach(vw)
        reqs += self.plan_services(vw)
        if self.fz:
            self.stairs_plan(vw)
            eye = (m.recipe["assemble"]["sockets"].get("Cockpit") or {}).get("location")
            if eye:
                E = vw.P((eye[0], eye[1], 0))
                sh.ax.add_patch(Circle(E, 1.3, fc="white", ec="#2E7D32", lw=0.4 * PT, zorder=47))
                sh.ax.add_patch(Circle(E, 0.5, fc="#2E7D32", ec="none", zorder=47.1))
                sh.t(E[0] + 1.8, E[1] - 3.2, "oko pilota", 2.1, "#2E7D32", z=47.2, bg="white")
        return vw, W, reqs

    def plan_services(self, vw):
        """In plan: the cuts of the bay details (A, B, C), each bay component's envelope when it is pulled out into the
        corridor (its replacement), the service channel under a floor grating (the part's purpose)."""
        m, sh = self.m, self.sh
        out = []
        if self.rid == "tech":
            for n, e in enumerate(bay_modules(self)):
                r = e.extra["rect"]
                host = self.el[e.extra["bay"]]
                face = host.extra["placement"].ue_to_layout(0, 0, 0)[1]
                sgn = 1 if face > 0 else -1
                xc = (r[0] + r[1]) / 2
                A, B = vw.P((xc, face - sgn * 0.35, 0)), vw.P((xc, face + sgn * 0.75, 0))
                sh.line([A, B], 0.3, INK, ls=(0, (6, 1.5, 1, 1.5)), z=46)
                sh.t(B[0] + 1.0, B[1] - 1.0 * sgn, "DET. " + "ABC"[n], 2.4, weight="bold", z=46, bg="white")
            for e in m.in_room(self.rid, ("component",)):
                if not str(e.src).endswith("SOCKET_Component"):
                    continue
                r = e.extra["rect"]
                host = self.el[e.extra["bay"]]
                face = host.extra["placement"].ue_to_layout(0, 0, 0)[1]
                dep = r[3] - r[2]
                ya, yb = (face - dep, face) if face > 0 else (face, face + dep)
                P0, P1 = vw.P((r[0], ya, 0)), vw.P((r[1], yb, 0))
                sh.rect(min(P0[0], P1[0]), min(P0[1], P1[1]), max(P0[0], P1[0]), max(P0[1], P1[1]), ec=GREY, lw=0.25,
                        ls=(0, (1.5, 1.0)), z=26)
                X, Y = vw.P(((r[0] + r[1]) / 2, (ya + yb) / 2, 0))
                out.append({"id": "#pull-" + e.id, "text": "%s vysunutý" % e.id.split("-", 2)[-1], "anchor": (X, Y),
                            "col": GREY, "z": Y, "hidden": False})
        for p in self.places:
            if p.category == "Floor" and "Grille" in p.part:
                dz = m.parts["SM_Kit_" + p.part]["dims_m"][2]
                X, Y = vw.P(p.ue_to_layout(m.span(p) * 50.0, -25.0, 0)[:2] + (0,))
                out.append({"id": "#channel", "text": "kanál pod roštem %s m" % im.fmt(dz), "anchor": (X, Y), "col": GREY,
                            "z": Y, "hidden": True})
        return out

    def door_approach(self, vw):
        """The way into an end wall's doorway past what stands in front of it (the hold's cargo grid before
        DR-HLD-TEC): the clear depth between the object's box and the face, the capsule 0.56 m there; under 0.56 the
        data check says so."""
        m, sh = self.m, self.sh
        f = m.room_faces(self.rid)
        self.approach = []
        for e in m.elements:
            if e.cat != "door" or e.extra["axis"] != "x" or self.rid not in (e.extra.get("rooms") or ()):
                continue
            end = m.door_face(e, self.rid)
            xf = f[end]
            y, w = e.extra["at"][1], e.extra["width"]
            for o in m.in_room(self.rid, ("object",)):
                r, z = o.extra.get("rect"), o.extra.get("z")
                if not r or not z or o.status == "remove" or o.extra.get("below") or z[0] > 1.0 or r[3] < y - w / 2                         or r[2] > y + w / 2:
                    continue
                gap = (xf - r[1]) if end == "F" else (r[0] - xf)
                if not 0 < gap < 1.0:
                    continue
                xa, xb = (r[1], xf) if end == "F" else (xf, r[0])
                # the door's edge on the side away from the object and the object's corner on the way to it
                upper = (r[2] + r[3]) / 2 < y
                edge = y + w / 2 if upper else y - w / 2
                cy = r[3] if upper else r[2]
                cx = r[1] if end == "F" else r[0]
                jx = self.jamb_x(e, edge, end, xf)
                diag = float(np.hypot(jx - cx, edge - cy))
                self.chain(vw, "x", cy - (0.12 if upper else -0.12), [xa, xb])
                A, B = vw.P((cx, cy, 0)), vw.P((jx, edge, 0))
                sh.line([A, B], 0.3, "#2E7D32", z=47.4)
                sh.t((A[0] + B[0]) / 2 + 1.0, (A[1] + B[1]) / 2 - 3.0, "%s šikmo" % im.fmt(diag), 2.1, "#2E7D32", z=47.5,
                     bg="white")
                X, Y = (A[0] + B[0]) / 2, (A[1] + B[1]) / 2
                rad = 0.28 * vw.s
                sh.ax.add_patch(Circle((X, Y), rad, fc="none", ec="#2E7D32", lw=0.35 * PT, zorder=47))
                ok = diag >= 0.56
                sh.t(X - rad - 1.0, Y + rad + 0.6, "kapsle Ø 0,56 šikmo: %s" % (
                    ("projde, rezerva %d mm" % round((diag - 0.56) * 1000)) if ok else "neprojde o %d mm" % round((0.56 - diag) * 1000)),
                     2.1, "#2E7D32" if ok else STATUS_COL["remove"], ha="right", z=47.5, bg="white")
                self.approach.append((e.id, "cesta z uličky do %s vede šikmo mezi rohem %s (%s; x %s, y %s) a ostěním dveří "
                                            "(x %s z postaveného dílu, y %s): %s m – kapsle 0,56 m %s; podél přepážky před "
                                            "mřížkou zbývá %s m%s" % (
                                                e.id, o.id, o.name, im.fmt(cx), im.fmt(cy), im.fmt(jx), im.fmt(edge),
                                                im.fmt(diag), ("projde (rezerva %d mm)" % round((diag - 0.56) * 1000)) if ok
                                                else "neprojde, je-li mřížka plná", im.fmt(gap),
                                                " (kapsle tudy neprojde)" if gap < 0.56 else "")))

    def approach_stats(self):
        """{door id: (depth along the end wall, the diagonal past the object's corner)} as door_approach computes them."""
        m = self.m
        f = m.room_faces(self.rid)
        out = {}
        for e in m.elements:
            if e.cat != "door" or e.extra["axis"] != "x" or self.rid not in (e.extra.get("rooms") or ()):
                continue
            end = m.door_face(e, self.rid)
            xf = f[end]
            y, w = e.extra["at"][1], e.extra["width"]
            for o in m.in_room(self.rid, ("object",)):
                r, z = o.extra.get("rect"), o.extra.get("z")
                if not r or not z or o.status == "remove" or o.extra.get("below") or z[0] > 1.0 or r[3] < y - w / 2 \
                        or r[2] > y + w / 2:
                    continue
                gap = (xf - r[1]) if end == "F" else (r[0] - xf)
                if not 0 < gap < 1.0:
                    continue
                upper = (r[2] + r[3]) / 2 < y
                edge = y + w / 2 if upper else y - w / 2
                cy = r[3] if upper else r[2]
                cx = r[1] if end == "F" else r[0]
                jx = self.jamb_x(e, edge, end, xf)
                out[e.id] = (gap, float(np.hypot(jx - cx, edge - cy)))
        return out

    def jamb_x(self, door, edge, end, xf):
        """The jamb's front at a doorway's edge from the built bulkhead part (its verts within 0.12 m of the edge, at
        0.2 … 1.8 m): the most aft (an F door) or forward point; else the face."""
        best = xf
        for p in self.places:
            if p.category != "Bulkhead":
                continue
            V = self.geo.kit(p).verts
            sel = (np.abs(V[:, 1] - edge) < 0.12) & (V[:, 2] > 0.2) & (V[:, 2] < 1.8) & (np.abs(V[:, 0] - xf) < 0.3)
            if sel.any():
                best = float(V[sel, 0].min()) if end == "F" else float(V[sel, 0].max())
        return best

    # ------------------------------------------------------------------ dimensions
    def dim(self, A, B, text, size=2.2, col=INK, z=48):
        """One dimension between paper points A and B (horizontal or vertical): arrows, the value over it (left of a
        vertical one, turned)."""
        sh = self.sh
        sh.ax.annotate("", xy=A, xytext=B, zorder=z, arrowprops=dict(arrowstyle="<|-|>", lw=0.16 * PT, color=col,
                                                                      mutation_scale=3.2, shrinkA=0, shrinkB=0))
        if abs(A[1] - B[1]) < 1e-6:
            L = abs(B[0] - A[0])
            w = sh.width(text, size)
            X = (A[0] + B[0]) / 2 if w + 1.0 < L else max(A[0], B[0]) + 1.0 + w / 2
            sh.t(X, A[1] + 0.6, text, size, col, ha="center", z=z, bg="white")
        else:
            L = abs(B[1] - A[1])
            w = sh.width(text, size)
            Y = (A[1] + B[1]) / 2 if w + 1.0 < L else max(A[1], B[1]) + 1.0 + w / 2
            sh.t(A[0] - 0.6, Y, text, size, col, ha="right", va="center", rot=90, z=z, bg="white")

    def chain(self, vw, axis, at, values, feature=None, label=None, size=2.2):
        """A dimension chain in a view: along x (axis "x", the line at y = at) or y (at x = at) through the sorted
        values, each piece dimensioned; thin extension lines from the feature coordinate (the other axis) to the line."""
        sh = self.sh
        vs = []
        for v in sorted(values):                 # parts that touch (locker | hygiene cell: 7 mm apart) share a point
            if not vs or v - vs[-1] > 0.015:
                vs.append(v)
        pts = [vw.P((v, at, 0)) if axis == "x" else vw.P((at, v, 0)) for v in vs]
        for v, P in zip(vs, pts):
            if feature is not None:
                F = vw.P((v, feature, 0)) if axis == "x" else vw.P((feature, v, 0))
                if axis == "x":
                    sgn = 1 if P[1] > F[1] else -1
                    sh.line([F, (P[0], P[1] + sgn * 1.2)], 0.1, GREY, z=47)
                else:
                    sgn = 1 if P[0] > F[0] else -1
                    sh.line([F, (P[0] + sgn * 1.2, P[1])], 0.1, GREY, z=47)
            if axis == "x":
                sh.line([(P[0] - 0.8, P[1] - 0.8), (P[0] + 0.8, P[1] + 0.8)], 0.25, INK, z=48)
            else:
                sh.line([(P[0] - 0.8, P[1] - 0.8), (P[0] + 0.8, P[1] + 0.8)], 0.25, INK, z=48)
        for (va, A), (vb, B) in zip(zip(vs, pts), zip(vs[1:], pts[1:])):
            self.dim(A, B, im.fmt(vb - va), size)
        if label:
            P = pts[0]
            if axis == "x":
                sh.t(P[0] - 1.5, P[1] - 0.9, label, 2.0, GREY, ha="right", z=48, bg="white")
            else:
                sh.t(P[0] + 0.9, P[1] - 1.5, label, 2.0, GREY, ha="center", va="top", z=48, bg="white", rot=90)

    def faces(self):
        """The room's end faces (the bulkheads' faces) and the liner faces of its long walls, from the kit parts."""
        ends = sorted(p.ue_to_layout(0, 0, 0)[0] for p in self.places if p.category == "Bulkhead")
        sides = sorted({round(p.ue_to_layout(0, 0, 0)[1], 3) for p in self.places if p.category == "Wall"})
        if len(ends) == 1:                  # an open end (the hold's ramp): the room's end in the layout
            ends = sorted(ends + [self.x0 if ends[0] > (self.x0 + self.x1) / 2 else self.x1])
        return ends, sides

    def plan_dims(self, vw):
        """Dimension chains round the plan: furniture along each long wall and the room's length between the
        bulkhead faces (top: port, bottom: starboard); the room's width and the end doors at both ends."""
        m = self.m
        ends, sides = self.faces()
        if not sides and self.room.get("poly"):       # a room the ship builds: its layout outline, furniture, the door
            ys = [q[1] for q in self.room["poly"]]
            xs = [self.x0, self.x1]
            for e in m.in_room(self.rid, ("furniture", "object")):
                if e.extra.get("rect") and abs((e.extra["rect"][2] + e.extra["rect"][3]) / 2) < 0.2:
                    xs += e.extra["rect"][:2]
            self.chain(vw, "x", 2.42, xs, label="obrys layoutu, prvky v ose")
            yy = [min(ys), max(ys)]
            for e in m.elements:
                if e.cat == "door" and e.extra["axis"] == "x" and self.rid in (e.extra.get("rooms") or ()):
                    yy += [e.extra["at"][1] - e.extra["width"] / 2, e.extra["at"][1] + e.extra["width"] / 2]
            self.chain(vw, "y", self.x0 - 0.12, yy)
            return
        if len(ends) < 2 or len(sides) < 2:
            return
        yl, yr = sides[-1], sides[0]
        for side, y_in, y_out, yf in (("L", 2.42, 2.57, yl), ("R", -2.42, -2.57, yr)):
            xs = [ends[0], ends[-1]]
            for e in m.in_room(self.rid, ("furniture",)):
                if e.extra.get("placement") is not None and m.face_of(e) == side:
                    xs += list(m.x_range(e))
            if len(xs) > 2:                     # the furniture along the wall; without any the outer chain says it all
                self.chain(vw, "x", y_in, xs, feature=yf)
            self.chain(vw, "x", y_out, ends, label="líc přepážek" if side == "L" else None)
        for x_in, x_out, end in ((self.x0 - 0.12, self.x0 - 0.25, "A"), (self.x1 + 0.12, self.x1 + 0.25, "F")):
            ys = [yr, yl]
            for e in m.elements:
                if e.cat == "door" and e.extra["axis"] == "x" and self.rid in (e.extra.get("rooms") or ()) \
                        and m.door_face(e, self.rid) == end:
                    ys += [e.extra["at"][1] - e.extra["width"] / 2, e.extra["at"][1] + e.extra["width"] / 2]
            self.chain(vw, "y", x_in, ys)
            self.chain(vw, "y", x_out, [yr, yl], label="líc obložení" if end == "A" else None)
        # the doors in the long walls (the hygiene cell's): their width in front of them
        for e in m.elements:
            if e.cat == "door" and e.extra["axis"] == "y" and self.rid in (e.extra.get("rooms") or ()):
                x, y = e.extra["at"]
                yy = y + (0.1 if y < 0 else -0.1)
                self.chain(vw, "x", yy, [x - e.extra["width"] / 2, x + e.extra["width"] / 2])

    def anchor_plan(self, e):
        p = e.extra.get("placement")
        if p is not None:
            L = self.m.span(p)
            if e.cat in ("wall", "bulkhead"):
                x, y, _ = p.ue_to_layout(8.0, -L * 50.0, 0)
                return (x, y, 0)
            if e.cat == "furniture":
                dx, dy, _ = self.m.parts["SM_Kit_" + p.part]["dims_m"]
                pts = [p.ue_to_layout(dx * 55.0, b * dy * 100.0, 0) for b in (-0.5, 0.5)]
                a, b = sorted(pts, key=lambda q: q[0])
                return (a[0] + (b[0] - a[0]) * 0.28, a[1] + (b[1] - a[1]) * 0.28, 0)
            x, y, _ = p.ue_to_layout(L * 50.0, 0, 0)
            return (x, y + (0.35 if p.index % 2 else -0.35), 0)
        if e.cat == "door":
            x, y = e.extra["at"]
            return (x, y, 0)
        if e.extra.get("rect"):
            r = e.extra["rect"]
            return ((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, 0)
        if e.extra.get("pos"):
            return e.extra["pos"]
        return None

    def grid(self, vw, W):
        """The kit's 0.3 m plan grid over the room: x from the start of the room's wall runs, y from the centre line
        (kit_rules.json grid.plan; the sections are symmetric about the centre line)."""
        g = self.m.rules["grid"]["plan"]
        walls = [p for p in self.places if p.category == "Wall"]
        gx0 = min(min(p.ue_to_layout(0, 0, 0)[0], p.ue_to_layout(0, -self.m.span(p) * 100, 0)[0]) for p in walls)
        gx1 = max(max(p.ue_to_layout(0, 0, 0)[0], p.ue_to_layout(0, -self.m.span(p) * 100, 0)[0]) for p in walls)
        half = max(abs(p.ue_to_layout(0, 0, 0)[1]) for p in walls)
        self.grid_origin = gx0
        k = 0
        x = gx0
        while x <= gx1 + 1e-6:
            a, b = vw.P((x, -half, 0)), vw.P((x, half, 0))
            self.sh.line([a, b], 0.3 if k % 4 == 0 else 0.12, GRID_COL, z=24)
            if k % 4 == 0:
                self.sh.t(a[0], W[1] + 1.2, ("+0,0 = x %s" % im.fmt(gx0)) if k == 0 else "+%s" % im.fmt(x - gx0, 1), 2.1,
                          GRID_COL, ha="left" if k == 0 else "center", z=45, bg="white")
            k += 1
            x = gx0 + k * g
        k = -int(half / g)
        while k * g <= half + 1e-6:
            y = k * g
            a, b = vw.P((gx0, y, 0)), vw.P((gx1, y, 0))
            self.sh.line([a, b], 0.3 if k % 4 == 0 else 0.12, GRID_COL, z=24)
            if k % 4 == 0:
                self.sh.t(vw.P((gx0, 0, 0))[0] + 0.8, a[1] + 0.6, ("%+.1f" % y).replace(".", ",") if y else "osa", 2.0,
                          GRID_COL, z=45, bg="white")
            k += 1

    def door_plan(self, vw, e):
        """A doorway's leaf: built (black) or proposed (blue), its closed position and its slide."""
        sh = self.sh
        lf = e.extra.get("leaf") or {}
        x, y = e.extra["at"]
        w = e.extra["width"]
        st = {"built": "built", "proposed": "proposed"}.get(lf.get("leaf"), None)
        if st is None:
            return
        col = STATUS_COL[st]
        if e.extra["axis"] == "x":
            a, b = (x, y - w / 2, 0), (x, y + w / 2, 0)
            along = np.array((0, 1, 0))
        else:
            a, b = (x - w / 2, y, 0), (x + w / 2, y, 0)
            along = np.array((1, 0, 0))
        if lf.get("x") is not None:                 # the leaf in a pocket inside the bulkhead: closed in its plane
            a, b = (lf["x"],) + tuple(a[1:]), (lf["x"],) + tuple(b[1:])
        A, B = vw.P(a), vw.P(b)
        if st == "proposed":
            sh.line([A, B], 0.9, col, z=27)
            for (o0, o1) in lf.get("open") or []:
                t = lf.get("t", 0.03)
                sgn = -1 if lf.get("side") == "aft" else 1
                xa, xb = sorted((x + sgn * 0.005, x + sgn * (0.005 + t)))
                if lf.get("x") is not None:          # in a pocket inside the bulkhead
                    xa, xb = lf["x"] - t / 2, lf["x"] + t / 2
                P0, P1 = vw.P((xa, o0, 0)), vw.P((xb, o1, 0))
                sh.rect(min(P0[0], P1[0]) - 0.3, min(P0[1], P1[1]), max(P0[0], P1[0]) + 0.3, max(P0[1], P1[1]),
                        ec=col, lw=0.3, ls="--", z=27.5)
        if lf.get("type") == "rampa":
            # a ramp: hinged at the deck's end, it folds down and out (the deck sheet's section A draws it lowered)
            sgn = -1 if x <= (self.x0 + self.x1) / 2 else 1
            H0, H1 = vw.P((x, y - w / 2, 0)), vw.P((x, y + w / 2, 0))
            sh.line([H0, H1], 0.6, INK, ls=(0, (8, 2, 2, 2)), z=46)              # the hinge line
            for yy in (y - w / 4, y + w / 4):
                A, B = vw.P((x - sgn * 0.3, yy, 0)), vw.P((x + sgn * 0.28, yy, 0))
                sh.ax.annotate("", xy=B, xytext=A, zorder=46, arrowprops=dict(arrowstyle="-|>", lw=0.7 * PT, color=INK,
                                                                              mutation_scale=14, shrinkA=0, shrinkB=0))
            T = vw.P((x - sgn * 0.42, y, 0))
            sh.t(T[0], T[1], "závěs rampy: sklápí se ven a dolů (22°)", 2.2, rot=90, ha="center", va="center", z=46,
                 bg="white")
            return
        slide = lf.get("slide")
        if lf.get("slide_part") is not None and lf.get("kit"):
            p = next(p for p in self.places if p.part == lf["kit"])
            slide = self._part_dir(p, lf["slide_part"])
        # the arrow 0.18 m off the doorway into this room, so it does not sit on the leaf's line
        rc = np.array(((self.x0 + self.x1) / 2, 0.0, 0.0))
        here = np.array((x, y, 0.0))
        off = np.array((1.0, 0.0, 0.0)) if e.extra["axis"] == "x" else np.array((0.0, 1.0, 0.0))
        off = off * (1 if (rc - here) @ off > 0 else -1) * 0.18
        C = vw.P(here + off)
        if slide is not None and any(slide):
            v = np.array((slide[0], slide[1], 0.0))
            tip = vw.P(here + off + v * w * 0.55)
            sh.ax.annotate("", xy=tip, xytext=C, zorder=28, arrowprops=dict(arrowstyle="-|>", lw=0.45 * PT, color=col,
                                                                            mutation_scale=10, shrinkA=0, shrinkB=0))
        elif lf.get("type", "").startswith("posuvné dvoukřídlé"):
            for sgn in (-1, 1):
                tip = vw.P(here + off + along * sgn * w * 0.5)
                sh.ax.annotate("", xy=tip, xytext=C, zorder=28, arrowprops=dict(
                    arrowstyle="-|>", lw=0.35 * PT, color=col, mutation_scale=7, shrinkA=0, shrinkB=0))

    @staticmethod
    def _part_dir(p, d):
        """A direction in the part's Blender frame (x front, y along) to layout (x, y)."""
        return p.dir_layout(d[0], -d[1])

    def section_mark(self, vw, W):
        sh = self.sh
        x = self.section_x
        A, B = vw.P((x, -2.25, 0)), vw.P((x, 2.25, 0))      # inside the dimension chains (at y ±2.42 and ±2.57)
        sh.line([A, B], 0.35, INK, ls="-.", z=46)
        for P in (A, B):
            sh.ax.annotate("", xy=(P[0] + 6, P[1]), xytext=(P[0], P[1]), zorder=46, arrowprops=dict(
                arrowstyle="-|>", lw=0.35 * PT, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))
            sh.t(P[0] + 7.5, P[1] - 1.2, "R1", 3.0, weight="bold", z=46, bg="white")
            sh.t(P[0] + 14.5, P[1] - 1.2, "x %s" % im.fmt(x), 2.2, z=46, bg="white")

    def view_keys(self, vw):
        """The developed elevations' keys: numbered arrows at each wall, looking at it from the room."""
        sh = self.sh
        cx = (self.x0 + self.x1) / 2
        for num, face, (x, y), (dx, dy) in ((1, "L", (cx - 0.55, 0.55), (0, 1)), (2, "F", (self.x1 - 0.65, -0.2), (1, 0)),
                                            (3, "R", (cx - 0.55, -0.45), (0, -1)), (4, "A", (self.x0 + 0.65, -0.2), (-1, 0))):
            P = vw.P((x, y, 0))
            T = (P[0] + dx * 5.5, P[1] + dy * 5.5)
            sh.ax.add_patch(Circle(P, 2.6, fc="white", ec=INK, lw=0.3 * PT, zorder=47))
            sh.t(P[0], P[1], str(num), 2.6, ha="center", va="center", weight="bold", z=47.5)
            sh.ax.annotate("", xy=T, xytext=(P[0] + dx * 2.6, P[1] + dy * 2.6), zorder=47, arrowprops=dict(
                arrowstyle="-|>", lw=0.3 * PT, color=INK, mutation_scale=6, shrinkA=0, shrinkB=0))

    def room_text(self, vw):
        X, Y = vw.P(((self.x0 + self.x1) / 2 + 0.1, -0.02, 0))
        self.sh.t(X, Y, self.room["name"].upper(), 3.2, weight="bold", ha="center", z=46, bg="white")

    def rcp(self, ox, oy, view="RCP"):
        """The reflected ceiling plan: the ceiling seen from below, drawn in the plan's orientation (bow right,
        port up) - the ceiling panels with their lights."""
        m, sh = self.m, self.sh
        s = S20
        u0, v0 = self.x0 - PLAN_MX, -PLAN_HY
        vw = md.View((1, 0, 0), (0, 1, 0), (0, 0, 1), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + PLAN_MX - u0) * s, oy + 2 * PLAN_HY * s)
        zc = self.fz + (1.95 if not self.fz else 1.3)          # a raised room: its canopy over the pilot from below
        cut = ((0, 0, zc), (0, 0, 1))
        clip = ((self.x0 - 0.3, -2.7, zc), (self.x1 + 0.3, 2.7, max(3.2, self.fz + 2.6)))
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior, self.canopy], self.cols, clip=clip, cut=cut,
                          window=W)
        md.draw(sh.ax, vw, [self.hull], self.cols, clip=clip, cut=cut, window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        reqs = []
        self.draw_lights(view, vw, [self.el[i] for i in sorted(self.views[view]) if self.el[i].cat == "light"])
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            if e.cat == "light" or (e.extra.get("placement") is not None and ident not in tags):
                continue
            if e.cat != "decal":
                self.mark(view, ident)
            if e.cat == "ceiling":
                p = e.extra["placement"]
                L = m.span(p)
                X, Y = vw.P((p.ue_to_layout(L * 50.0, 0, 0)[0], -0.62, 0))
                sh.t(X, Y, ident, 2.4, STATUS_COL[e.status], ha="center", va="center", z=40, bg="white")
                self.lab(view, ident)
                continue
            if e.cat == "decal":
                a = self.decal_overlay(view, e, vw)
                if a:
                    self.mark(view, ident)
                    reqs.append(self.req(view, ident, *a))
        reqs += self.rcp_context(vw)
        reqs += self.rcp_gaps(vw)
        self.room_text(vw)
        return vw, W, reqs

    def rcp_gaps(self, vw):
        """What the ceiling plan shows where the kit has no ceiling: the strip at the room's end before the first panel
        (the hold: over the ramp's first 0.6 m the hull closes in - the ramp frame's header beam, built by the ship) and
        the ship's dark layer over the ceiling."""
        m = self.m
        out = []
        ceil = sorted((p for p in self.places if p.category == "Ceiling"), key=lambda p: p.x)
        ramp = any(e.cat == "door" and (e.extra.get("leaf") or {}).get("type") == "rampa" and self.rid in (e.extra.get("rooms") or ())
                   for e in m.elements)
        if ceil and ceil[0].x - self.x0 > 0.1:
            X, Y = vw.P(((self.x0 + ceil[0].x) / 2, 0.9, 0))
            out.append({"id": "#nopanel", "text": "x %s … %s bez stropního panelu kitu%s" % (
                im.fmt(self.x0), im.fmt(ceil[0].x), ": trup se nad rampou snižuje, nadpraží rámu rampy (loď)" if ramp else ""),
                        "anchor": (X, Y), "col": GREY, "z": Y, "hidden": False})
        return out

    def rcp_context(self, vw):
        """Labels for what the ceiling panels of a hull liner room carry besides their lights (kit_batch2.services:
        the ladder tray and the pipe pair under the ceiling, the T ribs on the panel joints) and the walls' coves -
        parts of the kit modules, labelled grey with the modules they belong to."""
        out = []
        ceil = [p for p in self.places if p.category == "Ceiling"
                and self.m.parts["SM_Kit_" + p.part]["section"].startswith("L")]       # kit_batch2.services: L only
        if not ceil:
            return out
        k = kit_constants("kit_batch2.py", ("SVC_TRAY", "SVC_PIPES", "SVC_Z"))
        ids = ", ".join(sorted(p.tag for p in ceil))
        p0 = sorted(ceil, key=lambda p: p.x)[0]
        L0 = self.m.span(p0)
        ty = (k["SVC_TRAY"][0] + k["SVC_TRAY"][1]) / 2
        py = (k["SVC_PIPES"][0][0] + k["SVC_PIPES"][1][0]) / 2
        for ident, text, pt in (("#tray", "kabelový žebřík pod stropem (součást %s)" % ids, (p0.x + L0 * 0.22, ty, 2.13)),
                                ("#pipes", "dvojice potrubí s barevným pruhem (součást %s)" % ids, (p0.x + L0 * 0.62, py, 2.13)),
                                ("#rib", "žebro (T profil) na spoji stropních panelů", (p0.x + L0, -0.3, 2.3))):
            X, Y = vw.P(pt)
            out.append({"id": ident, "text": text, "anchor": (X, Y), "col": GREY, "z": Y, "hidden": False})
        cove = next((e for e in self.m.elements if e.room == self.rid and e.cat == "light" and e.id.endswith("/Cove_0")
                     and self.m.face_of(e) == "L"), None)
        if cove is not None:
            X, Y = vw.P(cove.extra["pos"])
            out.append({"id": "#cove", "text": "římsa obložení se světlem Cove (stěny W-L, W-R)", "anchor": (X, Y),
                        "col": GREY, "z": Y, "hidden": False})
        return out

    def elevation(self, face, ox, oy, view):
        """One wall seen from the middle of the room: cut along the room's centre line (the floor and ceiling in
        section), the wall and everything on it beyond."""
        m, sh = self.m, self.sh
        s = S20
        cx = (self.x0 + self.x1) / 2
        sides = self.faces()[1]
        hw = (max(abs(v) for v in sides) if sides else 1.9) + 0.02
        if face == "L":
            u, d, u0, w = (1, 0, 0), (0, 1, 0), self.x0 - 0.05, self.x1 - self.x0 + 0.1
            cut, clip = ((0, 0, 0), (0, 1, 0)), ((self.x0 - 0.2, 0.0, -0.3), (self.x1 + 0.2, 2.6, 2.6))
        elif face == "R":
            u, d, u0, w = (-1, 0, 0), (0, -1, 0), -(self.x1 + 0.05), self.x1 - self.x0 + 0.1
            cut, clip = ((0, 0, 0), (0, -1, 0)), ((self.x0 - 0.2, -2.6, -0.3), (self.x1 + 0.2, 0.0, 2.6))
        elif face == "F":
            u, d, u0, w = (0, -1, 0), (1, 0, 0), -hw, 2 * hw
            cut, clip = ((cx, 0, 0), (1, 0, 0)), ((cx, -2.6, -0.3), (self.x1 + 0.25, 2.6, 2.6))
        else:
            u, d, u0, w = (0, 1, 0), (-1, 0, 0), -hw, 2 * hw
            cut, clip = ((cx, 0, 0), (-1, 0, 0)), ((self.x0 - 0.25, -2.6, -0.3), (cx, 2.6, 2.6))
        vw = md.View(u, (0, 0, 1), d, ox, oy, s, u0, -0.15)
        clip = (clip[0][:2] + (-0.3,), clip[1][:2] + (self.fz + 2.6,))
        W = (ox, oy, ox + w * s, oy + (self.fz + 2.6) * s)
        fade = {p.tag for p in self.places if p.category == "Furniture"} if face in ("F", "A") else None
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior] + ([self.canopy] if self.fz else []),
                          self.cols, clip=clip, cut=cut, window=W, fade=fade)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        reqs = []
        # module IDs over the wall, joints ticked
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            if e.cat == "light" or (e.extra.get("placement") is not None and ident not in tags):
                continue
            if e.cat != "decal":
                self.mark(view, ident)
            if e.cat == "wall":
                p = e.extra["placement"]
                L = m.span(p)
                A, B = vw.P(p.ue_to_layout(0, 0, 245)), vw.P(p.ue_to_layout(0, -L * 100, 245))
                yb = W[3] + 1.2
                for P in (A, B):
                    sh.line([(P[0], W[3]), (P[0], yb + 7.0)], 0.18, INK, z=45)
                # on white over the leaders that pass down to the wall (critic of I-04, round 1)
                self.boxed((A[0] + B[0]) / 2, yb + 3.6, ident, 2.4, STATUS_COL[e.status])
                self.boxed((A[0] + B[0]) / 2, yb + 0.6, p.part.split("_", 1)[1], 2.0, GREY)
                self.lab(view, ident)
                # the module's length under the wall
                yd = W[1] - 4.0
                sh.ax.annotate("", xy=(A[0], yd), xytext=(B[0], yd), zorder=45, arrowprops=dict(
                    arrowstyle="<|-|>", lw=0.15 * PT, color=INK, mutation_scale=3.5, shrinkA=0, shrinkB=0))
                for P in (A, B):
                    sh.line([(P[0], W[1]), (P[0], yd - 1.5)], 0.13, INK, z=45)
                sh.t((A[0] + B[0]) / 2, yd + 0.6, im.fmt(L, 1), 2.2, ha="center", z=45, bg="white")
            elif e.cat == "bulkhead":
                X = (W[0] + W[2]) / 2
                sh.t(X, W[3] + 2.8, ident + "  (" + e.kit + ")", 2.4, STATUS_COL[e.status], ha="center", z=45)
                self.lab(view, ident)
            elif e.cat == "light":
                continue
            elif e.cat == "decal":
                a = self.decal_overlay(view, e, vw)
                if a:
                    self.mark(view, ident)
                    reqs.append(self.req(view, ident, *a))
            elif e.cat == "furniture":
                p = e.extra["placement"]
                dims = m.parts["SM_Kit_" + p.part]["dims_m"]
                X, Y = vw.P(p.ue_to_layout(dims[0] * 100, 0, min(dims[2], 1.2) * 75))
                reqs.append(self.req(view, ident, X, Y))
            elif e.cat == "door":
                x, y = e.extra["at"]
                X, Y = vw.P((x, y, self.fz + 1.0))
                reqs.append(self.req(view, ident, X, Y))
            elif e.cat == "object":
                if e.extra.get("rect") and e.extra.get("z") and e.src == "layout.objects":
                    r_, z_ = e.extra["rect"], e.extra["z"]          # its envelope from the layout, as in the section
                    if face in ("L", "R"):
                        Q0, Q1 = vw.P((r_[0], 0, z_[0])), vw.P((r_[1], 0, z_[1]))
                    else:
                        Q0, Q1 = vw.P((0, r_[2], z_[0])), vw.P((0, r_[3], z_[1]))
                    sh.rect(min(Q0[0], Q1[0]), min(Q0[1], Q1[1]), max(Q0[0], Q1[0]), max(Q0[1], Q1[1]),
                            ec=STATUS_COL[e.status], lw=0.3, ls="--", z=46)
                if e.extra.get("rect"):
                    r, z = e.extra["rect"], e.extra.get("z") or (0.0, 1.0)
                else:                                # a point object (a grab bar)
                    q = e.extra["pos"]
                    r, z = [q[0], q[0], q[1], q[1]], (q[2], q[2])
                f = self.m.room_faces(self.rid)
                pt = ((r[0] + r[1]) / 2, f.get(face, 0.0) if face in ("L", "R") else (r[2] + r[3]) / 2,
                      (z[0] + z[1]) / 2)
                if face in ("A", "F"):
                    pt = (f[face], pt[1], pt[2])
                reqs.append(self.req(view, ident, *vw.P(pt)))
        self.draw_lights(view, vw, [self.el[i] for i in sorted(self.views[view]) if self.el[i].cat == "light"], side=True)
        self.levels(vw, W, labels=face != "L")
        reqs += self.leaves_elevation(vw, face, view)
        if face in ("F", "A"):
            # furniture standing in front of the end wall: named grey, so it does not read as part of the bulkhead
            for e in m.in_room(self.rid, ("furniture",)):
                xr = m.x_range(e)
                p = e.extra.get("placement")
                if p is None or not xr or not (xr[1] > cx if face == "F" else xr[0] < cx):
                    continue
                dims = m.parts["SM_Kit_" + p.part]["dims_m"]
                x = min(max((xr[0] + xr[1]) / 2, cx + 0.05), self.x1) if face == "F" else max(min((xr[0] + xr[1]) / 2, cx - 0.05), self.x0)
                yc = p.ue_to_layout(dims[0] * 50, 0, 0)[1]
                X, Y = vw.P((x, yc, min(dims[2], 1.8) * 0.55))
                reqs.append({"id": "#ctx-" + e.id, "text": "%s (před stěnou)" % e.id, "anchor": (X, Y), "col": GREY,
                             "z": Y, "hidden": False})
        return vw, W, reqs

    def leaves_elevation(self, vw, face, view):
        """A proposed sliding leaf in an end-wall view: its open position dashed (behind the face when it runs on the
        far side)."""
        out = []
        for e in self.m.elements:
            if e.cat != "door" or e.extra["axis"] != "x" or self.rid not in (e.extra.get("rooms") or ()):
                continue
            if self.m.door_face(e, self.rid) != face:
                continue
            lf = e.extra.get("leaf") or {}
            if lf.get("leaf") != "proposed":
                continue
            x = lf.get("x", e.extra["at"][0])
            h = lf.get("h", 2.05)
            for (o0, o1) in lf.get("open") or []:
                P0, P1 = vw.P((x, o0, 0.0)), vw.P((x, o1, h))
                self.sh.rect(min(P0[0], P1[0]), min(P0[1], P1[1]), max(P0[0], P1[0]), max(P0[1], P1[1]),
                             ec=STATUS_COL["proposed"], lw=0.3, ls="--", z=46)
            if lf.get("open"):
                P = vw.P((x, (lf["open"][0][0] + lf["open"][0][1]) / 2, h * 0.75))
                n = len(lf["open"])
                out.append({"id": "#leaf-" + e.id, "text": "%s %s + (návrh, %s)" % (
                    e.id, "%d křídla" % n if n > 1 else "křídlo", lf.get("side_cz", "")),
                            "anchor": P, "col": STATUS_COL["proposed"], "z": P[1], "hidden": True})
        return out

    def profile(self):
        """The room's wall section (kit_rules.json sections: the walls' section, the liner L at its room width L41 /
        L38 by the ceiling parts): vertical_to, slope_rise (the chamfer's horizontal inset is 0.75 x rise), ceiling."""
        rules = self.m.rules["sections"]
        secs = [self.m.parts["SM_Kit_" + p.part].get("section") for p in self.places if p.category == "Wall"]
        cl = [self.m.parts["SM_Kit_" + p.part].get("section") for p in self.places if p.category == "Ceiling"]
        key = next((c for c in cl if c in rules), None) if secs and secs[0] == "L" else (secs[0] if secs else None)
        return rules.get(key) or rules.get(secs[0] if secs else "W") or rules["W"]

    def level_list(self):
        """The heights the walls are built to: deck, the rail at 1.30 (the liner's, one line through the ship), the
        chamfer's start and end, the ceiling."""
        if not any(p.category == "Wall" for p in self.places):
            out = [(0.0, "paluba"), (self.fz, "podlaha místnosti")] if self.fz else [(0.0, "paluba")]
            eye = (self.m.recipe["assemble"]["sockets"].get("Cockpit") or {}).get("location")
            if eye and self.x0 <= eye[0] <= self.x1:
                out.append((eye[2], "oko pilota v sedě"))
            ch = getattr(self, "clear_top", None)
            if ch:
                out.append((ch, "nejnižší nad pochozí plochou"))
            return out
        pr = self.profile()
        vt, top = pr["vertical_to"], pr["vertical_to"] + pr["slope_rise"]
        out = [(0.0, "paluba")]
        if vt > 1.31:
            out.append((1.3, "lišta"))
            out.append((vt, "začátek zkosení"))
        else:
            out.append((vt, "lišta, začátek zkosení"))
        out.append((top, "konec zkosení, římsa"))
        out.append((pr["ceiling"], "strop"))
        return out

    def wall_y(self, z, face):
        """The wall's face at height z (the section's chamfer: 3:4, inset 0.75 x rise from vertical_to)."""
        pr = self.profile()
        dz = min(max(z - pr["vertical_to"], 0.0), pr["slope_rise"])
        return (abs(face) - 0.75 * dz) * (1 if face > 0 else -1)

    def levels(self, vw, W, labels=False):
        """Level ticks at the view's left edge; labels inside the view when the strip's own labels are far away."""
        sh = self.sh
        for z, _ in self.level_list():
            if not (-0.1 <= z <= self.fz + 2.5):
                continue
            name = ("+" if z else "±") + im.fmt(z)
            _, Y = vw.P((0, 0, z))
            sh.line([(W[0] - 1.5, Y), (W[0], Y)], 0.18, INK, z=45)
            if labels:
                sh.ax.add_patch(MplPolygon([(W[0] + 1.6, Y), (W[0] + 0.6, Y + 1.3), (W[0] + 2.6, Y + 1.3)], closed=True,
                                           fc=INK, ec="none", zorder=46))
                sh.t(W[0] + 3.2, Y + 0.5, name, 2.0, z=46, bg="white")

    def level_labels(self, x, vw):
        sh = self.sh
        for z, nm in self.level_list():
            if not (-0.1 <= z <= self.fz + 2.5):
                continue
            name = ("+" if z else "±") + im.fmt(z) + " " + nm
            _, Y = vw.P((0, 0, z))
            sh.line([(x, Y), (x + 26, Y)], 0.18, INK, z=45)
            sh.ax.add_patch(MplPolygon([(x + 1, Y), (x - 0.2, Y + 1.6), (x + 2.2, Y + 1.6)], closed=True, fc=INK,
                                       ec="none", zorder=45))
            sh.t(x + 3, Y + 0.8, name, 2.2, z=45)

    def section(self, ox, oy, view="SEC"):
        """Cross section R1 looking forward (port on the left): the hull and the interior cut at section_x, the
        room beyond, the character's capsule in the aisle, heights, what is under the floor and over the ceiling."""
        m, sh = self.m, self.sh
        s = S20
        x = self.section_x
        if self.aft:                     # looking aft (the ramp's opening): port on the right
            vw = md.View((0, 1, 0), (0, 0, 1), (-1, 0, 0), ox, oy, s, -2.7, -1.2)
            cut = ((x, 0, 0), (-1, 0, 0))
            clip = ((self.x0 - 1.2, -2.8, -1.6), (x + 0.01, 2.8, 3.6))
        else:
            vw = md.View((0, -1, 0), (0, 0, 1), (1, 0, 0), ox, oy, s, -2.7, -1.2)
            cut = ((x, 0, 0), (1, 0, 0))
            clip = ((x - 0.01, -2.8, -1.6), (self.x1 + 0.06, 2.8, 3.6))
        W = (ox, oy, ox + 5.4 * s, oy + 4.7 * s)
        _, tags = md.draw(sh.ax, vw, self.parts + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(sh.ax, vw, [self.hull, self.canopy], self.cols, clip=((x - 0.01, -2.8, -2.0), (x + 0.01, 2.8, 4.0)), cut=cut,
                window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        reqs = []
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            p = e.extra.get("placement")
            if p is not None and ident not in tags:
                continue
            self.mark(view, ident)
            if e.cat == "wall":
                face = p.ue_to_layout(0, 0, 0)[1]
                Y = vw.P((0, 0, 1.45))[1]
                X = vw.P((x, face + (0.03 if face > 0 else -0.03), 0))[0]
            elif e.cat == "floor":
                X, Y = vw.P((x, -0.45, -0.02))
            elif e.cat == "ceiling":
                X, Y = vw.P((x, 0.75, 2.3))
            elif e.cat == "furniture":
                dims = m.parts["SM_Kit_" + p.part]["dims_m"]
                X, Y = vw.P((x, p.ue_to_layout(dims[0] * 60, 0, 0)[1], 1.5))
            elif e.extra.get("rect"):
                r = e.extra["rect"]
                X, Y = vw.P((x, (r[2] + r[3]) / 2, (e.extra["z"][0] + e.extra["z"][1]) / 2 if e.extra.get("z") else 0))
            else:
                continue
            reqs.append(self.req(view, ident, X, Y))
        # layout boxes in the section, dashed: under-floor components ahead of the cut (beyond it, looking forward)
        # and the components and objects the cut passes through (their envelopes: the hold's cargo, the bays' units)
        for e in m.in_room(self.rid, ("component", "object")):
            r, z = e.extra.get("rect"), e.extra.get("z")
            if not r or not z or e.status == "remove":
                continue
            ahead = (r[0] <= x + 1e-6) if self.aft else (r[1] >= x - 1e-6)
            if (e.extra.get("below") and ahead) or (not e.extra.get("below") and r[0] <= x <= r[1]):
                self.previous(vw, e, lambda rr, zz: (vw.P((x, rr[2], zz[0])), vw.P((x, rr[3], zz[1]))))
                self.proposal(vw, e, lambda rr, zz: (vw.P((x, rr[2], zz[0])), vw.P((x, rr[3], zz[1]))))
                A, B = vw.P((x, r[2], z[0])), vw.P((x, r[3], z[1]))
                sh.rect(min(A[0], B[0]), min(A[1], B[1]), max(A[0], B[0]), max(A[1], B[1]), ec=STATUS_COL[e.status],
                        lw=0.35, ls="--", z=46)
                if e.id not in self.views[view]:
                    reqs.append(self.req(view, e.id, (A[0] + B[0]) / 2, (A[1] + B[1]) / 2, hidden=True))
                    self.mark(view, e.id)
        self.capsule(vw)
        self.section_dims(vw, W)
        self.section_zones(vw, W)
        return vw, W, reqs

    def section_zones(self, vw, W):
        """What is over the ceiling and under the floor at the section: the hull's cut near the centre line gives the
        roof and the belly; dimensioned on the port side outside the hull, named in a note."""
        sh = self.sh
        x = self.section_x
        segs = md._slice(self.hull.verts, self.hull.tris, np.array((x, 0, 0.0)), np.array((1.0, 0, 0)))
        zs = []                                            # the hull's cut where it crosses the centre line
        for a, b in segs:
            if (a[1] <= 0 <= b[1] or b[1] <= 0 <= a[1]) and abs(a[1] - b[1]) > 1e-6:
                zs.append(a[2] + (b[2] - a[2]) * (0 - a[1]) / (b[1] - a[1]))
        if not zs:
            return
        top, bot = max(zs), min(zs)
        if self.fz:                          # a raised room under its canopy: only what is under its floor
            yd = 2.62
            A, B = vw.P((x, yd, bot)), vw.P((x, yd, self.fz))
            sh.ax.annotate("", xy=A, xytext=B, zorder=48, arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color=INK,
                                                                           mutation_scale=4, shrinkA=0, shrinkB=0))
            sh.t(A[0] - 0.8, (A[1] + B[1]) / 2, "pod podlahou %s" % im.fmt(self.fz - bot), 2.1, ha="right", va="center",
                 rot=90, z=48, bg="white")
            below = ["%s %s (%s)" % (e.id, e.name, im.STATUS_CZ[e.status]) for e in self.m.in_room(self.rid, ("component",))
                     if e.extra.get("below")]
            self.zone_note = ("Řez R1: podlaha místnosti +%s nad palubou, pod ní (do %s) prostor nad břichem lodi – trup, "
                              "konstrukce ani rozvody nejsou modelované%s; nad hlavou kabina (sklo a rám, výkresy E-01, E-07)." % (
                                  im.fmt(self.fz), im.fmt(bot), ("; v layoutu: " + ", ".join(below)) if below else ""))
            return
        ceil = 2.3
        yd = 2.62                                         # left of the hull (port)
        Xd = vw.P((x, yd, 0))[0]
        for (za, zb, txt) in ((ceil, top, "nad stropem %s" % im.fmt(top - ceil)), (bot, 0.0, "pod podlahou %s" % im.fmt(-bot))):
            A, B = vw.P((x, yd, za)), vw.P((x, yd, zb))
            sh.ax.annotate("", xy=A, xytext=B, zorder=48, arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color=INK,
                                                                           mutation_scale=4, shrinkA=0, shrinkB=0))
            for z in (za, zb):
                P = vw.P((x, yd, z))
                sh.line([(P[0] - 1.5, P[1]), (P[0] + 6, P[1])], 0.13, INK, z=48)
            sh.t(Xd - 0.8, (A[1] + B[1]) / 2, txt, 2.1, ha="right", va="center", rot=90, z=48, bg="white")
        for z, name in ((top, "%s trup (střecha)" % ("+" + im.fmt(top))), (bot, "%s trup (břicho)" % im.fmt(bot))):
            P = vw.P((x, -0.9, z))
            sh.t(P[0], P[1] + (1.2 if z > 1 else -3.6), name, 2.0, ha="center", z=48, bg="white")
        below = ["%s %s (%s)" % (e.id, e.name, im.STATUS_CZ[e.status]) for e in self.m.in_room(self.rid, ("component",))
                 if e.extra.get("below")]
        self.zone_note = ("Řez R1: nad stropem (+2,30 … +%s) tmavá vrstva lodi nad kitem a trup, pod stropem kabelový žebřík "
                          "a potrubí stropních panelů; pod podlahou (±0,00 … %s) jen %s a trup – "
                          "konstrukce ani rozvody tu nejsou modelované%s." % (
                              im.fmt(top), im.fmt(bot),
                              ("podlahová deska kitu (6,5 cm)" + ("; pod roštem %s servisní kanál %s m (dvě potrubí, "
                                                                     "kabelový svazek, pásek Channel)" % (
                                  next(p.tag for p in self.places if "Grille" in p.part),
                                  im.fmt(self.m.parts["SM_Kit_" + next(p.part for p in self.places if "Grille" in p.part)]["dims_m"][2]))
                                                                     if any("Grille" in p.part for p in self.places) else ""))
                              if any(p.category == "Floor" for p in self.places)
                              else "podlaha lodi z desek 0,6 m (kit zatím podlahu této místnosti nemá) s poklopy nad komponentami",
                              ("; v layoutu: " + ", ".join(below)) if below else ""))

    def detail_view(self, view, title, scale, ox, oy, u, v, d, u0, u1, v0, v1, cut, clip):
        """A detail window at 1:scale: the built parts cut by the plane, the window framed, the title over it."""
        s = 1000.0 / scale
        if u1 < u0:
            u0, u1 = u1, u0
        vw = md.View(u, v, d, ox, oy, s, u0, v0)
        W = (ox, oy, ox + (u1 - u0) * s, oy + (v1 - v0) * s)
        md.draw(self.sh.ax, vw, self.parts + self.ctx + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(self.sh.ax, vw, [self.hull], self.cols, clip=clip, cut=cut, window=W, fill=False)
        self.sh.rect(*W, ec=INK, lw=0.35, z=44)
        self.sh.t(ox, W[3] + 21.0, title, 3.0, weight="bold")
        self.sh.t(ox + self.sh.width(title, 3.0) + 6, W[3] + 21.0, "1 : %d" % scale, 3.0)
        self.drawn.setdefault(view, set())
        return vw, W

    def detail_items(self, view, vw, items):
        """Leader requests for a detail's items: (ID or #note, text, layout point); IDs count as drawn and labelled."""
        reqs = []
        for ident, text, pt in items:
            X, Y = vw.P(pt)
            if not ident.startswith("#"):
                self.mark(view, ident)
            e = self.el.get(ident)
            col = STATUS_COL[e.status] if e is not None else GREY
            reqs.append({"id": ident, "text": text, "anchor": (X, Y), "col": col, "z": Y, "hidden": False})
        return reqs

    def component_fit(self):
        """Every under-floor component of the room against the hull: its layout box's corners (y, z) at both ends
        of it (x) must lie inside the hull's cut there; a corner outside goes to the data check."""
        out = []
        for e in self.m.in_room(self.rid, ("component",)):
            if not (e.extra.get("below") and e.extra.get("rect") and e.extra.get("z")):
                continue
            r, z = e.extra["rect"], e.extra["z"]
            for x in (r[0] + 0.01, r[1] - 0.01):
                segs = hull_main_segs(md._slice(self.hull.verts, self.hull.tris, np.array((x, 0, 0.0)), np.array((1.0, 0, 0))))
                seg2 = [((a[1], a[2]), (b[1], b[2])) for a, b in segs if max(abs(a[1]), abs(b[1])) < 3.0]
                bad = [(y, zz) for y in (r[2], r[3]) for zz in z if not _inside_segs((y, zz), seg2)]
                if bad:
                    out.append((e.id, "%s (%s) leží zčásti mimo trup: při x %s roh %s (layout x %s, y %s, z %s)" % (
                        e.name, im.STATUS_CZ[e.status], im.fmt(x), ", ".join("y %s z %s" % (im.fmt(y), im.fmt(zz)) for y, zz in bad),
                        "%s … %s" % (im.fmt(r[0]), im.fmt(r[1])), "%s … %s" % (im.fmt(r[2]), im.fmt(r[3])),
                        "%s … %s" % (im.fmt(z[0]), im.fmt(z[1])))))
                    break
        return out

    def previous(self, vw, e, corners):
        """A moved element's previous position (design data components.<id>.previous): red dashed, a dashed blue
        arrow from its middle to the new one - the exterior's convention for a change."""
        prev = (self.m.design.get("components") or {}).get(e.id, {}).get("previous")
        if not prev:
            return
        z = prev.get("z") or e.extra.get("z") or [0, 0]
        A0, B0 = corners(prev["rect"], z)
        A1, B1 = corners(e.extra["rect"], e.extra.get("z") or z)
        self.sh.rect(min(A0[0], B0[0]), min(A0[1], B0[1]), max(A0[0], B0[0]), max(A0[1], B0[1]), ec=STATUS_COL["remove"],
                     lw=0.3, ls="--", z=24.5)
        c0 = ((A0[0] + B0[0]) / 2, (A0[1] + B0[1]) / 2)
        c1 = ((A1[0] + B1[0]) / 2, (A1[1] + B1[1]) / 2)
        if math.hypot(c1[0] - c0[0], c1[1] - c0[1]) > 1.0:
            self.sh.ax.annotate("", xy=c1, xytext=c0, zorder=26, arrowprops=dict(
                arrowstyle="-|>", lw=0.3 * PT, color=STATUS_COL["proposed"], mutation_scale=6, linestyle=(0, (2.5, 1.5)),
                shrinkA=0, shrinkB=0))
            self.sh.t(min(A0[0], B0[0]) + 0.8, min(A0[1], B0[1]) + 0.8, prev.get("label", "dřív"), 1.9, STATUS_COL["remove"],
                      z=26, bg="white")

    def proposal(self, vw, e, corners):
        """A proposed new position of an element (design data components.<id>.proposal): blue dashed (+) with a dashed
        arrow from the current one - the exterior's convention for a change."""
        pr = e.extra.get("proposal")
        if not pr:
            return
        z = pr.get("z") or e.extra.get("z") or [0, 0]
        A0, B0 = corners(e.extra["rect"], e.extra.get("z") or z)
        A1, B1 = corners(pr["rect"], z)
        col = STATUS_COL["proposed"]
        self.sh.rect(min(A1[0], B1[0]), min(A1[1], B1[1]), max(A1[0], B1[0]), max(A1[1], B1[1]), ec=col, lw=0.35,
                     ls="--", z=25.5)
        c0 = ((A0[0] + B0[0]) / 2, (A0[1] + B0[1]) / 2)
        c1 = ((A1[0] + B1[0]) / 2, (A1[1] + B1[1]) / 2)
        if math.hypot(c1[0] - c0[0], c1[1] - c0[1]) > 0.8:
            self.sh.ax.annotate("", xy=c1, xytext=c0, zorder=26, arrowprops=dict(
                arrowstyle="-|>", lw=0.3 * PT, color=col, mutation_scale=6, linestyle=(0, (2.5, 1.5)), shrinkA=0, shrinkB=0))
        self.sh.t(min(A1[0], B1[0]) + 0.8, min(A1[1], B1[1]) + 0.8, pr.get("label", "návrh") + " +", 2.1, col, z=26,
                  bg="white")

    def leaf_checks(self):
        """A proposed sliding leaf on this room's end wall, checked on both sides of the wall (the side in the data and
        the other one as the alternative): the built parts on the wall's face in its travel (the frame, the grab bar,
        the status light - how far they stand out, so how far off the face the leaf must run), the lights and signs in
        its way, and the room's wall chamfer at the leaf's height (that side's section profile)."""
        m = self.m
        out = []
        for e in m.elements:
            lf = e.extra.get("leaf") or {}
            if e.cat != "door" or lf.get("leaf") != "proposed" or not lf.get("open") or lf.get("side") not in ("aft", "fore") \
                    or self.rid not in (e.extra.get("rooms") or ()):
                continue
            x = e.extra["at"][0]
            if not ((x > (self.x0 + self.x1) / 2) == (lf.get("side") == "aft")):
                continue                                  # the leaf's side in the data is the other room's sheet
            h = lf.get("h", 2.05)
            for side in ("aft", "fore"):
                rid = m.room_at(x - 0.1, e.extra["at"][1]) if side == "aft" else m.room_at(x + 0.1, e.extra["at"][1])
                if rid is None:
                    continue
                other = RoomSheet(m, self.geo, rid, x, sheet=self.sh) if rid != self.rid else self
                tag = "%s strana (%s)" % ("v datech" if side == lf.get("side") else "varianta", m.rooms[rid]["name"].lower())
                sides = other.faces()[1]
                pr = other.profile()
                for o0, o1 in lf["open"]:
                    lo, hi = min(o0, o1), max(o0, o1)
                    msgs = []
                    if len(sides) >= 2:
                        face = sides[-1] if hi > 0 else sides[0]
                        yo = max(abs(o0), abs(o1))
                        ytop = abs(other.wall_y(h, face))
                        if ytop < yo - 0.005:
                            msgs.append("zkosení stěn (líc ±%s, od +%s) zasahuje od +%s, v horní hraně o %s m" % (
                                im.fmt(abs(face)), im.fmt(pr["vertical_to"]),
                                im.fmt(pr["vertical_to"] + (abs(face) - yo) / 0.75), im.fmt(yo - ytop)))
                    proud = 0.0                            # the built parts on the face: how far they stand out
                    for p in other.places:
                        if p.category != "Bulkhead" or abs(p.ue_to_layout(0, 0, 0)[0] - x) > 0.12:
                            continue
                        V = self.geo.kit(p).verts
                        fx = p.ue_to_layout(0, 0, 0)[0]
                        sgn = -1 if side == "aft" else 1
                        sel = (V[:, 1] >= lo) & (V[:, 1] <= hi) & (V[:, 2] > 0.05) & (V[:, 2] < h) & ((V[:, 0] - fx) * sgn > 0)
                        if sel.any():
                            proud = max(proud, float(((V[sel, 0] - fx) * sgn).max()))
                    if proud > 0.005:
                        msgs.append("díly na líci (rám, madlo, stavové světlo) vystupují až %d mm – křídlo musí jet aspoň "
                                    "%d mm od líce" % (round(proud * 1000), round(proud * 1000) + 10))
                    hits = [q.id for q in m.elements if q.room == rid and q.cat in ("light", "decal") and q.extra.get("pos")
                            and abs(q.extra["pos"][0] - x) < 0.15 and lo <= q.extra["pos"][1] <= hi and q.extra["pos"][2] < h]
                    if hits:
                        msgs.append("na dráze jsou %s – přesunout" % ", ".join(sorted(hits)))
                    out.append((e.id, "křídlo y %s … %s, výška %s, %s: %s" % (
                        im.fmt(o0), im.fmt(o1), im.fmt(h), tag, "; ".join(msgs) if msgs else "volno")))
        if out:
            out.append(("#", "K rozhodnutí autora: dvoukřídlé posuvné dveře 1,00 m se na straně chodby (průřez W) pod "
                             "zkosení nevejdou (užší křídla by zúžila otvor pod 0,90 m pravidla kitu); na straně kajuty "
                             "(obložení L, zkosení od +1,70) se vejdou, pokud pojedou odsazeně od dílů na líci a nápisy "
                             "a světla na dráze se přesunou."))
        return out

    def decal_boxes(self):
        """Every decal of the room on a wall with its centre and extent along x and z (kit decals from the built quads,
        projected ones from the setup)."""
        out = {}
        for ident, (c, pts) in self.decal_pos.items():
            if ident in self.el and self.el[ident].room == self.rid:
                out[ident] = (c, pts[:, 0].min(), pts[:, 0].max(), pts[:, 2].min(), pts[:, 2].max())
        for e in self.m.in_room(self.rid, ("decal",)):
            if e.extra.get("projected") and e.status != "remove":
                pos, n, hy, hz = self.m.decal_frame(e)
                q = np.array([np.asarray(pos) + a * np.asarray(hy) + b * np.asarray(hz) for a in (-1, 1) for b in (-1, 1)])
                out[e.id] = (np.asarray(pos), q[:, 0].min(), q[:, 0].max(), q[:, 2].min(), q[:, 2].max())
        return out

    def hidden_decals(self):
        """A sign behind something standing in front of the wall (a layout object's box), and two signs over each other
        on the same wall."""
        out = []
        boxes = self.decal_boxes()
        for ident, (c, xa, xb, za, zb) in sorted(boxes.items()):
            for o in self.m.in_room(self.rid, ("object",)):
                r, z = o.extra.get("rect"), o.extra.get("z")
                if not r or not z or o.status == "remove" or o.extra.get("below"):
                    continue
                if r[0] <= c[0] <= r[1] and z[0] <= c[2] <= z[1] and (min(abs(c[1] - r[2]), abs(c[1] - r[3])) < 0.6):
                    cargo = "náklad" in o.name.lower() or "mřížka" in o.name.lower()
                    out.append((ident, "decal x %s, z %s je za %s %s (%s) – %s" % (
                        im.fmt(c[0]), im.fmt(c[2]), "obálkou" if cargo else "objektem", o.id, o.name,
                        "při plné mřížce zakrytý nákladem; posunout nad 1,25 m nebo za konec mřížky" if cargo
                        else "ve hře není vidět; přesunout nebo díl bez něj")))
        keys = sorted(boxes)
        for i, a_ in enumerate(keys):
            ca, xa0, xa1, za0, za1 = boxes[a_]
            for b_ in keys[i + 1:]:
                cb, xb0, xb1, zb0, zb1 = boxes[b_]
                if abs(ca[1] - cb[1]) < 0.1 and min(xa1, xb1) - max(xa0, xb0) > 0.02 and min(za1, zb1) - max(za0, zb0) > 0.02:
                    out.append((a_, "decal leží přes %s (překryv %d × %d mm) – jeden posunout" % (
                        b_, round((min(xa1, xb1) - max(xa0, xb0)) * 1000), round((min(za1, zb1) - max(za0, zb0)) * 1000))))
        return out

    def built_area(self):
        """The room's floor between its built faces (end walls: bulkheads, else the layout's end; long walls: the wall
        modules' faces), else the layout's rectangle."""
        ends, sides = self.faces()
        r = self.room["rect"]
        if not sides and self.room.get("poly"):
            poly = self.room["poly"]
            return abs(sum(a_[0] * b_[1] - b_[0] * a_[1] for a_, b_ in zip(poly, poly[1:] + poly[:1]))) / 2
        L = (ends[-1] - ends[0]) if len(ends) >= 2 else r[1] - r[0]
        Wd = (sides[-1] - sides[0]) if len(sides) >= 2 else r[3] - r[2]
        return L * Wd

    def eye_marks(self, vws):
        """The seated pilot's eye (the recipe's Cockpit socket) in the side views and the steepest line down over the dash
        it still sees past (the dash's far top edge, from the layout)."""
        eye = (self.m.recipe["assemble"]["sockets"].get("Cockpit") or {}).get("location")
        dash = next((e for e in self.m.in_room(self.rid, ("object",)) if e.extra.get("rect") and e.extra.get("z")
                     and abs(e.extra["rect"][2] + e.extra["rect"][3]) < 0.1 and e.extra["rect"][0] > (eye or [0])[0]), None)
        if not eye:
            return
        import math
        for face, view, num, vw, W, reqs in vws:
            if face not in ("L", "R"):
                continue
            E = vw.P((eye[0], 0, eye[2]))
            self.sh.ax.add_patch(Circle(E, 1.3, fc="white", ec="#2E7D32", lw=0.4 * PT, zorder=47))
            self.sh.ax.add_patch(Circle(E, 0.5, fc="#2E7D32", ec="none", zorder=47.1))
            self.sh.t(E[0] + 1.8, E[1] + 1.2, "oko pilota v sedě (+%s)" % im.fmt(eye[2]), 2.1, "#2E7D32", z=47.2, bg="white")
            if dash:
                r, z = dash.extra["rect"], dash.extra["z"]
                tip = (r[1], 0, z[1])
                ang = math.degrees(math.atan2(eye[2] - z[1], r[1] - eye[0]))
                far = (eye[0] + 2.2, 0, eye[2] - 2.2 * (eye[2] - z[1]) / (r[1] - eye[0]))
                P1 = vw.P(far)
                self.sh.line([E, P1], 0.25, "#2E7D32", ls=(0, (6, 2)), z=47)
                T = vw.P(tip)
                self.sh.t(T[0], T[1] + 2.5, "výhled dolů přes desku %d°" % round(ang), 2.1, "#2E7D32", ha="center", z=47.2,
                          bg="white")

    def stairs_plan(self, vw):
        """A raised room's stairs (its object from hs_interior.stairs): the risers, the arrow up with the rise and tread,
        the landing from the top step to the seat (the capsule 0.56 m against it)."""
        st = next((e for e in self.m.in_room(self.rid, ("object",)) if e.extra.get("stairs")), None)
        if st is None:
            return
        k = st.extra["stairs"]
        import math
        for i in range(k["n"]):
            x = k["x0"] + i * k["tread"]
            self.sh.line([vw.P((x, -k["half_w"], 0)), vw.P((x, k["half_w"], 0))], 0.25, INK, z=27)
        x_top = k["x0"] + (k["n"] - 1) * k["tread"]
        A, B = vw.P((k["x0"] + 0.03, -0.15, 0)), vw.P((x_top + 0.05, -0.15, 0))
        self.sh.ax.annotate("", xy=B, xytext=A, zorder=28, arrowprops=dict(arrowstyle="-|>", lw=0.5 * PT, color=INK,
                                                                          mutation_scale=10, shrinkA=0, shrinkB=0))
        X, Y = vw.P((k["x0"] + 0.02, 0.12, 0))
        self.sh.t(X, Y, "nahoru %d × %s, stupeň %s, sklon %d°" % (k["n"], im.fmt(k["rise"], 3), im.fmt(k["tread"]),
                                                                   round(math.degrees(math.atan2(k["rise"], k["tread"])))),
                  2.2, z=46, bg="white")
        seat = next((e for e in self.m.in_room(self.rid, ("furniture",)) if e.extra.get("rect")), None)
        if seat is not None:
            land = seat.extra["rect"][0] - (x_top + 0.04)
            self.chain(vw, "x", -0.62, [x_top + 0.04, seat.extra["rect"][0]])
            self.landing = land

    def capsule(self, vw):
        """The walking character's capsule in the ship (APlayerCharacter::SetShipCapsule: 0.56 x 1.80 m) in the aisle
        and its eye at 1.65 m."""
        sh = self.sh
        cap_d, cap_h, eye = 0.56, 1.80, 1.65
        ya, yb = self.aisle()
        yc = (ya + yb) / 2
        A, B = vw.P((self.section_x, yc + cap_d / 2, self.fz)), vw.P((self.section_x, yc - cap_d / 2, self.fz + cap_h))
        x0, x1 = min(A[0], B[0]), max(A[0], B[0])
        sh.ax.add_patch(FancyBboxPatch((x0, A[1]), x1 - x0, B[1] - A[1], boxstyle="round,pad=0,rounding_size=%.2f" % ((x1 - x0) / 2),
                                       fc="#DFF1E1", ec="#2E7D32", lw=0.35 * PT, zorder=47, alpha=0.9))
        _, Ye = vw.P((0, 0, self.fz + eye))
        sh.line([(x0 - 2, Ye), (x1 + 2, Ye)], 0.25, "#2E7D32", z=47.5, ls="-.")
        sh.t(x1 + 2.5, Ye - 0.8, "oko 1,65", 2.0, "#2E7D32", z=47.5, bg="white")
        sh.t((x0 + x1) / 2, (A[1] + B[1]) / 2, "kapsle\n0,56 × 1,80", 2.0, "#2E7D32", ha="center", va="center", z=47.5)

    def aisle(self):
        """The clear aisle at the section: between the furniture fronts either side (or the wall faces); a layout
        object standing on the floor across the section (the hold's cargo grid) narrows it too."""
        sides = self.faces()[1]
        lo, hi = (sides[0], sides[-1]) if len(sides) >= 2 else (-1.9, 1.9)
        if getattr(self, "aft", False):          # looking aft at the room's end: its doorway (the ramp) is the way out
            for e in self.m.elements:
                if e.cat == "door" and e.extra["axis"] == "x" and self.rid in (e.extra.get("rooms") or ())                         and self.x0 - 0.05 <= e.extra["at"][0] <= self.section_x:
                    lo = max(lo, e.extra["at"][1] - e.extra["width"] / 2)
                    hi = min(hi, e.extra["at"][1] + e.extra["width"] / 2)
        for e in self.m.in_room(self.rid, ("object", "component")):
            r, z = e.extra.get("rect"), e.extra.get("z")
            if not r or not z or e.status == "remove" or e.extra.get("below") or z[0] - self.fz > 1.0                     or not (r[0] <= self.section_x <= r[1]):
                continue
            if r[2] + r[3] < 0:
                lo = max(lo, r[3])
            else:
                hi = min(hi, r[2])
        for e in self.m.in_room(self.rid, ("furniture",)):
            xr = self.m.x_range(e)
            p = e.extra.get("placement")
            if p is None or not xr or not (xr[0] - 0.3 <= self.section_x <= xr[1] + 0.3):
                continue
            dims = self.m.parts["SM_Kit_" + p.part]["dims_m"]
            fy = p.ue_to_layout(dims[0] * 100, 0, 0)[1]
            if fy > 0:
                hi = min(hi, fy)
            else:
                lo = max(lo, fy)
        return lo, hi

    def section_dims(self, vw, W):
        sh = self.sh
        ya, yb = self.aisle()
        z = self.fz + 0.25
        A, B = vw.P((self.section_x, yb, z)), vw.P((self.section_x, ya, z))
        sh.ax.annotate("", xy=A, xytext=B, zorder=48, arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color="#2E7D32",
                                                                       mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t((A[0] + B[0]) / 2, A[1] + 0.8, "průchod %s u podlahy (kit ≥ 0,90; mezi líci, nábytkem a obálkami)" % im.fmt(yb - ya),
             2.2, "#2E7D32", ha="center", z=48, bg="white")
        self.sec_stats = {"aisle": yb - ya}
        # the width at the capsule's head (1.80) between the chamfers, where the walls narrow the room
        sides = self.faces()[1]
        if len(sides) >= 2:
            zh = 1.8
            yl, yr = self.wall_y(zh, sides[-1]), self.wall_y(zh, sides[0])
            if (yl - yr) < (sides[-1] - sides[0]) - 0.01:
                A, B = vw.P((self.section_x, yl, zh)), vw.P((self.section_x, yr, zh))
                sh.ax.annotate("", xy=A, xytext=B, zorder=48, arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT,
                                                                               color="#2E7D32", mutation_scale=4, shrinkA=0, shrinkB=0))
                sh.t((A[0] + B[0]) / 2 + 12, A[1] + 0.8, "%s ve výšce 1,80 (mezi zkoseními)" % im.fmt(yl - yr), 2.2,
                     "#2E7D32", ha="center", z=48, bg="white")
                self.sec_stats["w180"] = yl - yr
        # clear height under the flat ceiling, on the centre line (a room without kit ceilings: from the built meshes over
        # its floor in the band y ±0.30 at the section)
        if getattr(self, "aft", False):          # the doorway's head at the room's end (the ramp frame's header beam)
            h = self.clear_height(self.x0 + 0.08, self.fz)
            ceil, txt = (self.fz + h if h else self.profile()["ceiling"]), "světlá výška %s u otvoru (pás y ±0,30)"
        elif any(p.category == "Ceiling" for p in self.places):
            ceil, txt = self.profile()["ceiling"], "světlá výška %s (v ose)"
            h = self.clear_height(self.section_x, self.fz)
            if h and self.fz + h < ceil - 0.02:
                ceil, txt = self.fz + h, "světlá výška %s (v ose, pod stropním dílem kitu)"
        else:
            h = self.clear_height(self.section_x, self.fz)
            ceil, txt = (self.fz + h if h else self.fz + 2.0), "světlá výška %s (pás y ±0,30)"
            self.clear_top = ceil
        self.sec_stats["clear"] = ceil - self.fz
        X = vw.P((self.section_x, 0.0, 0))[0] - 9.0
        P0, P1 = vw.P((0, 0, self.fz)), vw.P((0, 0, ceil))
        sh.ax.annotate("", xy=(X, P0[1]), xytext=(X, P1[1]), zorder=48, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t(X - 0.8, (P0[1] + P1[1]) / 2, txt % im.fmt(ceil - self.fz), 2.2, ha="right", va="center", rot=90,
             z=48, bg="white")
        for z, nm in self.level_list():
            _, Y = vw.P((0, 0, z))
            sh.line([(W[0], Y), (W[0] + 1.2, Y)], 0.18, INK, z=48)
            sh.t(W[0] + 1.5, Y + 0.8, ("+" if z else "±") + im.fmt(z) + " " + nm, 2.0, z=48, bg="white")
        # the room between the liner faces (under the floor, where the section is empty) and the hull outside
        ends, sides = self.faces()
        if len(sides) >= 2:
            yr, yl = sides[0], sides[-1]
            A, B = vw.P((self.section_x, yl, -0.2)), vw.P((self.section_x, yr, -0.2))
            for y_ in (yl, yr):
                F = vw.P((self.section_x, y_, 0.0))
                sh.line([F, (F[0], A[1] - 1.2)], 0.1, GREY, z=47)
            self.dim(A, B, "%s mezi líci obložení" % im.fmt(yl - yr))
        segs = md._slice(self.hull.verts, self.hull.tris, np.array((self.section_x, 0, 0.0)), np.array((1.0, 0, 0)))
        pts = [p_ for p_ in hull_loop_points(segs) if 0.0 <= p_[2] <= 2.6]
        if pts:
            ymax = max(p_[1] for p_ in pts)
            ymin = min(p_[1] for p_ in pts)
            zt = 3.38
            A, B = vw.P((self.section_x, ymax, zt)), vw.P((self.section_x, ymin, zt))
            for p_ in (max(pts, key=lambda q: q[1]), min(pts, key=lambda q: q[1])):
                F = vw.P(p_)
                sh.line([F, (F[0], A[1] + 1.2)], 0.1, GREY, z=47)
            self.dim(A, B, "%s trup vně (bez křídel a gondol)" % im.fmt(ymax - ymin))
        P = vw.P((self.section_x, -0.75, -0.42))
        sh.t(P[0], P[1], "pod podlahou nemodelováno: jen trup", 2.0, GREY, ha="center", z=48, bg="white")


def hull_main_segs(segs):
    """The cut's segments of the hull's own skin only (the outlines that cross the centre line, hull_loop_points): an
    even-odd test over every outline (plates, gear bays inside) takes a point inside two of them as outside."""
    pts = hull_loop_points(segs)
    keep = {(round(float(p_[1]), 4), round(float(p_[2]), 4)) for p_ in pts}
    return [(a, b) for a, b in segs if (round(float(a[1]), 4), round(float(a[2]), 4)) in keep]


def hull_loop_points(segs):
    """The points of the hull's own skin in a cross section: the cut's segments joined into outlines at shared ends
    (1 mm), only the outlines that cross the centre line - so the wing roots, the gondolas' pylons and the plates on
    the skin (separate outlines) do not count in the hull's width."""
    parent = {}

    def find(k):
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    key = lambda p_: (round(float(p_[1]), 3), round(float(p_[2]), 3))      # noqa: E731
    for a, b in segs:
        ra, rb = find(key(a)), find(key(b))
        if ra != rb:
            parent[ra] = rb
    cross = {find(key(a)) for a, b in segs if a[1] * b[1] <= 0}
    return [p_ for a, b in segs if find(key(a)) in cross for p_ in (a, b)]


def _inside_segs(p, segs):
    """Point in the hull's outline given as segments (even-odd rule on a ray towards -z: the belly is closed, the roof
    over the cockpit is open where the canopy's glass is another mesh)."""
    y, z = p
    n = 0
    for (ay, az), (by, bz) in segs:
        if (ay <= y < by) or (by <= y < ay):
            if az + (y - ay) * (bz - az) / (by - ay) < z:
                n += 1
    return n % 2 == 1


# ---------------------------------------------------------------------- the I-04 sheet
def views_row(rs, rcp_x=362.0, sec_x=698.0, yv=535.0):
    """Row 1 of a room sheet: the plan, the reflected ceiling plan and the cross section R1 with their labels."""
    d = rs.d
    rs.title(34, 822, "PŮDORYS – ŘEZ VE VÝŠCE 1,20 m, MŘÍŽKA KITU 0,3 m" if not rs.fz else
             "PŮDORYS – ŘEZ 1,20 m NAD PODLAHOU (+%s), SCHODY POD NÍ" % im.fmt(rs.fz + 1.2))
    if rs.room.get("purpose"):
        rs.sh.t(34, 816.0, ds.wrap(rs.sh, "Účel: " + rs.room["purpose"], 2.2, rcp_x - 60, 1)[0], 2.2, GREY)
    vwP, WP, reqP = rs.plan(50.0, yv)
    d.place_labels("PLAN", reqP, 34, max(WP[2] + 14, rcp_x - 16), tiers_up=[806, 813], tiers_dn=[524, 516.5], split_y=vwP.P((0, 0, 0))[1],
                   bus_up=803.5, bus_dn=529.0)
    rs.title(rcp_x - 10, 822, "STROP – POHLED ZESPODU, ORIENTACE JAKO PŮDORYS" if not rs.fz else
             "KABINA – POHLED ZESPODU (ŘEZ +%s), ORIENTACE JAKO PŮDORYS" % im.fmt(rs.fz + 1.3))
    vwC, WC, reqC = rs.rcp(rcp_x, yv)
    if reqC:
        d.place_labels("RCP", reqC, rcp_x - 12, WC[2] + 10, tiers_up=[806, 813], tiers_dn=[524, 516.5],
                       split_y=vwC.P((0, 0, 0))[1], bus_up=803.5, bus_dn=529.0)
    rs.title(sec_x - 8, 822, "ŘEZ R1 – x %s, POHLED K PŘÍDI" % im.fmt(rs.section_x))
    vwS, WS, reqS = rs.section(sec_x, yv + 17.0)
    d.place_labels("SEC", reqS, sec_x - 8, WS[2] + 12, tiers_up=[803, 810.5], tiers_dn=[541, 533.5],
                   split_y=vwS.P((0, 0, 1.0))[1], bus_up=799.0, bus_dn=546.0)
    return WP, WC, WS


def walls_row(rs, order, x, ye):
    """The developed walls in one strip from x (order: (face, view, number)): numbered, named, labelled."""
    sh, d = rs.sh, rs.d
    vws = []
    for face, view, num in order:
        vw, W, reqs = rs.elevation(face, x, ye, view)
        vws.append((face, view, num, vw, W, reqs))
        x = W[2] + 7.0
    for face, view, num, vw, W, reqs in vws:
        sh.ax.add_patch(Circle((W[0] + 4, W[3] + 13.5), 2.6, fc="white", ec=INK, lw=0.3 * PT, zorder=47))
        sh.t(W[0] + 4, W[3] + 13.5, str(num), 2.6, ha="center", va="center", weight="bold", z=47.5)
        sh.t(W[0] + 8, W[3] + 12.6, FACE_CZ[face], 2.6, weight="bold", z=47.5)
        if face in ("F", "A"):                     # which side is which on an end wall seen from the room
            left, right = ("levobok", "pravobok") if face == "F" else ("pravobok", "levobok")
            sh.t(W[0] + 1.0, W[1] + 1.2, "← " + left, 2.0, GREY, z=47.5, bg="white")
            sh.t(W[2] - 1.0, W[1] + 1.2, right + " →", 2.0, GREY, ha="right", z=47.5, bg="white")
        d.place_labels(view, reqs, W[0], W[2], tiers_up=[W[3] + 19.5, W[3] + 25.5, W[3] + 31.5],
                       tiers_dn=[W[1] - 13.0, W[1] - 19.0], split_y=vw.P((0, 0, 1.15))[1], bus_up=W[3] + 16.0,
                       bus_dn=W[1] - 9.0, size=2.3)
    rs.level_labels(30.0, vws[0][3])
    return vws


WALLS = (("L", "EL-L", 1), ("F", "EL-F", 2), ("R", "EL-R", 3), ("A", "EL-A", 4))
WALLS_TITLE = "ROZVINUTÝ POHLED STĚN – ZE STŘEDU MÍSTNOSTI (1 levobok, 2 přední, 3 pravobok, 4 zadní)"


def draw_room_sheet(m, geo, sheet, rid, section_x, dpi, out_dir, rcp_x=362.0, sec_x=698.0, ye=335.0, ytab=306.0):
    """A room on one A0 sheet (I-04 the cabin, I-03): plan, ceiling, section; the four walls in one strip; legend,
    key plan, notes; schedules, light summary, data check, details, title block."""
    rs = RoomSheet(m, geo, rid, section_x)
    rs.sheet = sheet
    sh = rs.sh
    ds.frame_and_zones(sh)
    views_row(rs, rcp_x, sec_x)
    rs.title(34, 505, WALLS_TITLE)
    vws = walls_row(rs, WALLS, 62.0, ye)
    if rs.fz:
        rs.eye_marks(vws)
    yl = legend(rs, 985.0, 822.0)
    key_plan(rs, 985.0, yl - 6.0)
    notes(rs, 985.0, 505.0)
    if rs.fz:                       # a raised room's lower table row: the decals under the light summary
        schedules(rs, 34.0, ytab, decals_at=(530.0, light_summary(rs, 530.0, ytab) - 8.0))
    else:
        schedules(rs, 34.0, ytab)
        light_summary(rs, 530.0, ytab)
    check_box(rs, 800.0, ytab, width=188.0)
    details(rs)
    if rs.rid == "tech":
        bay_details(rs)
    title_block(rs, 800.0, sh.w, sheet)
    return save(rs, sheet, dpi, out_dir)


def draw_long_room_sheet(m, geo, sheet, rid, section_x, dpi, out_dir):
    """A long room (I-02 the hold, 7.2 m: its four walls at 1:20 are 1.2 m of paper) on two A0 sheets: 1/2 the
    views - plan, ceiling, section; the walls in two strips (port + forward, starboard + aft); key plan and notes;
    2/2 the legend, schedules, light summary and data check. One sidecar for both."""
    rs = RoomSheet(m, geo, rid, section_x)
    rs.sheet = sheet
    sh = rs.sh
    ds.frame_and_zones(sh)
    rs.page = (1, 2)
    views_row(rs, rcp_x=466.0, sec_x=884.0)
    rs.title(34, 505, WALLS_TITLE)
    walls_row(rs, WALLS[:2], 62.0, 333.0)
    walls_row(rs, WALLS[2:], 62.0, 143.0)
    legend(rs, 985.0, 505.0)
    yk = key_plan(rs, 680.0, 505.0)
    yn = notes(rs, 680.0, yk - 4.0, width=290.0)
    check_box(rs, 680.0, yn - 4.0, width=290.0)
    sh.t(985.0, 130.0, "Tabulky dílů, nábytku, světel a decalů a souhrn světel: list %s (2/2)." % sheet, 2.4, weight="bold")
    title_block(rs, 800.0, sh.w, sheet)
    page1 = rs.sh
    # ------------------------------------------------ 2/2
    rs.sh = ds.Sheet(841.0, 594.0)                     # the tables fill an A1, not an A0 (round 1 of I-02)
    rs.d.sh = rs.sh
    sh = rs.sh
    ds.frame_and_zones(sh)
    rs.page = (2, 2)
    schedules(rs, 34.0, sh.h - 19.0)
    light_summary(rs, 530.0, sh.h - 19.0)
    sh.t(530.0, sh.h - 200.0, "Pohledy místnosti, legenda a kontrola dat: list %s (1/2, A0)." % sheet, 2.6, weight="bold")
    title_block(rs, sh.w - 389.0, sh.w, sheet)
    return save(rs, sheet, dpi, out_dir, pages=[page1, sh])


LEGEND_OTHER = ("decal", "fade", "leaf", "capsule", "move")


# I-06: the cross sections with the character's capsule - (sheet view, room, x, looking aft, title)
SECTIONS = [("SEC-RAMP", "hold", 1.3, True, "RAMPA – x 1,30, POHLED K ZÁDI (OTVOR RAMPY)"),
            ("SEC-HLD", "hold", 6.4, False, "NÁKLAD – x 6,40, POHLED K PŘÍDI"),
            ("SEC-TEC", "tech", 9.0, False, "TECHNICKÁ CHODBA – x 9,00, POHLED K PŘÍDI"),
            ("SEC-CAB", "cabin", 13.7, False, "KAJUTA – x 13,70, POHLED K PŘÍDI"),
            ("SEC-CPT", "cockpit", 16.4, False, "KOKPIT – x 16,40, POHLED K PŘÍDI (ZA SCHODY)")]


def narrow_places(m, geo, sh, x, ytop):
    """The narrow places of the walk through the ship from the room sheets' data: the doorways (width, height), the way
    past the hold's cargo grid into DR-HLD-TEC (the diagonal, I-02), the cockpit's stairs and its landing."""
    rows = []
    hold = RoomSheet(m, geo, "hold", 6.4, sheet=sh)
    stats = hold.approach_stats()
    for e in sorted((e for e in m.elements if e.cat == "door" and e.extra["axis"] == "x"), key=lambda e: e.extra["at"][0]):
        lf = e.extra.get("leaf") or {}
        h = lf.get("h")
        w = e.extra["width"]
        note = lf.get("type", "")
        if e.id in stats:
            gap, diag = stats[e.id]
            note += "; z uličky šikmo kolem rohu mřížky %s m (podél přepážky %s m)" % (im.fmt(diag), im.fmt(gap))
            w = min(w, diag)
        rows.append(([e.id, e.name, im.fmt(e.extra["width"]), im.fmt(h) if h else "–", im.fmt(w - 0.56),
                      "projde" if w >= 0.56 else "neprojde", note], INK if w >= 0.56 else STATUS_COL["remove"]))
    for rid, r in m.rooms.items():
        st = next((e for e in m.in_room(rid, ("object",)) if e.extra.get("stairs")), None)
        if st is None:
            continue
        k = st.extra["stairs"]
        seat = next((e for e in m.in_room(rid, ("furniture",)) if e.extra.get("rect")), None)
        land = seat.extra["rect"][0] - (k["x0"] + (k["n"] - 1) * k["tread"] + 0.04) if seat else None
        rows.append(([st.id, "schody do %s" % r["name"].lower(), im.fmt(2 * k["half_w"]), "–", im.fmt(2 * k["half_w"] - 0.56),
                      "projde", "%d × %s, stupeň %s (lodní schody)" % (k["n"], im.fmt(k["rise"], 3), im.fmt(k["tread"]))], INK))
        if land is not None:
            rows.append(([r["code"] + " plošina", "horní stupeň → křeslo", im.fmt(land), "–", im.fmt(land - 0.56),
                          "čeká na autora" if land < 0.56 else "projde",
                          "postava stojí na horním stupni a usedá zezadu – ověřit ve hře"],
                         STATUS_COL["remove"] if land < 0.56 else INK))
    cols = [("místo", 26, "left"), ("co", 40, "left"), ("šířka", 12, "right"), ("výška", 12, "right"),
            ("rezerva", 14, "right"), ("kapsle", 22, "left"), ("poznámka", 120, "left", 2)]
    return ds.table(sh, x, ytop, "ÚZKÁ MÍSTA TRASY (dveře, schody, plošina)", cols, rows, size=2.3, rowh=4.3)


def draw_sections_sheet(m, geo, sheet, dpi, out_dir):
    """I-06: the five cross sections of the walk through the ship at 1:20 with the capsule 0.56 x 1.80 m, the clear
    width at the floor and at 1.80 m, the clear height, what is under the floor; a table of the clearances. Each section
    is the room sheet's section R1 (the same code and data), drawn on one sheet."""
    sh = ds.Sheet()
    ds.frame_and_zones(sh)
    first = None
    rows = []
    pos = [(50.0, 540.0), (380.0, 540.0), (710.0, 540.0), (50.0, 190.0), (380.0, 190.0)]
    for (view, rid, x, aft, title), (ox, oy) in zip(SECTIONS, pos):
        rs = RoomSheet(m, geo, rid, x, aft=aft, sheet=sh)
        rs.views = {view: rs.views["SEC"]}
        if first is None:
            first = rs
            first.all_drawn, first.all_labelled = {}, {}
        rs.title(ox - 16, oy + 4.7 * S20 + 33, title)
        vw, W, reqs = rs.section(ox, oy, view=view)
        rs.d.place_labels(view, reqs, W[0] - 14, W[2] + 14, tiers_up=[W[3] + 9.0, W[3] + 15.5], tiers_dn=[W[1] - 8.0, W[1] - 14.5],
                          split_y=vw.P((0, 0, rs.fz + 1.0))[1], bus_up=W[3] + 4.5, bus_dn=W[1] - 3.5, size=2.2)
        first.all_drawn[view] = rs.drawn.get(view, set())
        first.all_labelled[view] = rs.d.labelled.get(view, set())
        st = getattr(rs, "sec_stats", {})
        aisle, w180, clear = st.get("aisle"), st.get("w180"), st.get("clear")
        if aft and aisle:                      # the ramp's opening: its width all the way up
            w180 = aisle
        ok = (aisle or 0) >= 0.56 and (clear or 0) >= 1.80 and (w180 is None or w180 >= 0.56)
        res = "%s / %s" % (im.fmt(min(aisle, w180 or aisle) - 0.56), im.fmt(clear - 1.80)) if aisle and clear else "–"
        rows.append(([view.split("-")[1], rs.room["name"], im.fmt(x), "k zádi" if aft else "k přídi",
                      im.fmt(aisle) if aisle else "–", im.fmt(w180) if w180 else "bez zkosení",
                      im.fmt(clear) if clear else "–", res, "projde" if ok else "neprojde"], INK if ok else STATUS_COL["remove"]))
        if rid == "cockpit":
            seat = next((e for e in m.in_room(rid, ("furniture",)) if e.extra.get("rect")), None)
            if seat and seat.extra["rect"][0] < x + 0.28:
                sh.t(ox, oy - 26.0, "Kapsle v řezu sahá %d mm do obálky křesla %s (od x %s): ke křeslu se jde z horní hrany "
                                    "schodů a usedá se zezadu." % (round((x + 0.28 - seat.extra["rect"][0]) * 1000), seat.id,
                                                                   im.fmt(seat.extra["rect"][0])), 2.2, STATUS_COL["remove"])
    rs = first
    rs.sheet = sheet
    rs.drawn, rs.d.labelled = rs.all_drawn, rs.all_labelled
    cols = [("řez", 13, "left"), ("místnost", 32, "left"), ("x", 12, "right"), ("pohled", 15, "left"),
            ("průchod u podlahy", 24, "right"), ("šířka ve 1,80", 20, "right"), ("světlá výška", 19, "right"),
            ("rezerva š / v", 20, "right"), ("kapsle 0,56 × 1,80", 26, "left")]
    yT = ds.table(sh, 710.0, 430.0, "PRŮCHODNOST V ŘEZECH (z postavené geometrie a dat)", cols, rows, size=2.4, rowh=4.6)
    narrow_places(m, geo, sh, 710.0, yT - 8.0)
    sh.t(710.0, 225.0, "Průchod u podlahy: mezi líci stěn, čely nábytku a obálkami objektů z layoutu v řezu.", 2.2, GREY)
    sh.t(710.0, 220.5, "Šířka ve 1,80: mezi zkoseními stěn podle profilu průřezu (kit_rules.json sections).", 2.2, GREY)
    sh.t(710.0, 216.0, "Světlá výška: rovný strop kitu, nebo nejnižší postavená plocha v pásu y ±0,30 (kokpit, otvor rampy).",
         2.2, GREY)
    sh.t(710.0, 211.5, "Řez rampou: průchod = otvor rampy (2,60), výška = nadpraží rámu rampy.", 2.2, GREY)
    legend(rs, 985.0, 822.0, lights=False, other=("capsule", "move"))
    rs.schedules = {"sections": {v for v, *_ in SECTIONS}}
    rs.checks = []
    title_block(rs, 800.0, sh.w, sheet)
    side_extra = {"sections": [[v, r, x, a] for v, r, x, a, _ in SECTIONS]}
    return save(rs, sheet, dpi, out_dir, extra=side_extra)


def legend(rs, x, ytop, ncol=2, col_w=95.0, lights=True, other=LEGEND_OTHER,
           cut_text="řez (plocha řezu: půdorys 1,20 m, R1, osa místnosti)"):
    """The legend; ncol / col_w lay the swatches out (one narrow column on the deck sheet I-01), lights and other pick
    the sections a sheet needs (the deck sheet draws no lights and decals)."""
    sh = rs.sh
    sh.t(x, ytop - 1, "LEGENDA", 3.8, weight="bold")
    y = ytop - 8
    sh.t(x, y, "Čáry", 2.8, weight="bold")
    y -= 5.0
    for lw, ls, col, txt in ((md.CUT_LW, "-", INK, cut_text),
                             (md.OUTLINE_LW, "-", INK, "obrys za řezem"), (md.EDGE_LW, "-", INK, "hrana dílu"),
                             (0.35, "--", INK, "obálka objektu z layoutu, výklenek komponenty v kitu (postaveno)"),
                             (0.35, "--", STATUS_COL["proposed"], "+ návrh (data návrhu, nepostaveno)"),
                             (0.25, ":", GRID_COL, "mřížka kitu 0,3 m (plná po 1,2 m)")):
        sh.line([(x, y + 0.8), (x + 12, y + 0.8)], lw, col, ls=ls)
        sh.t(x + 15, y, txt, 2.2)
        y -= 4.2
    y -= 1.5
    sh.t(x, y, "Materiály (odstín výplně = barva materiálu zesvětlená)", 2.8, weight="bold")
    y -= 5.4
    used = set()
    for p in rs.parts:
        used |= set(np.unique(p.mats).tolist())
    names = {"Kit_Primary": "lak – tmavý grafit (stěny, dvířka)", "Kit_Structure": "konstrukční kov (rámy, žebra)",
             "Kit_Accent": "krémový akcent", "Kit_Signal": "signální oranžová (madla, hrany)", "Kit_Rubber": "pryž",
             "Kit_Plastic": "plast", "Kit_Seal": "těsnění, spáry", "Kit_Trim": "trim (lišty)", "Kit_Fabric": "látka",
             "Kit_Cushion": "polstr", "Kit_GlowWarm": "teplé světlo", "Kit_GlowCool": "studené světlo (UI)",
             "Kit_GlowSignal": "signální světlo", "Kit_GlowDim": "tlumené světlo", "Kit_DecalPaint": "decal (nápis)"}
    i = 0
    for k, txt in names.items():
        if k not in used or rs.cols.get(k) is None:
            continue
        X = x + (i % ncol) * col_w
        Y = y - (i // ncol) * 5.0
        sh.geom(box(X, Y - 1.2, X + 9, Y + 2.6), fc=hexrgb(rs.cols[k]), ec=INK, lw=0.18, z=5)
        sh.t(X + 11, Y, txt, 2.1)
        i += 1
    y -= -(-i // ncol) * 5.0 + 1.0
    ship = {"IntDark": "tmavá vrstva lodi (vnitřní plášť, nad stropem)", "IntWall": "stěna lodi", "IntFloor": "podlaha lodi",
            "IntPanel": "panel lodi", "IntTrim": "trim lodi", "Accent": "akcent lodi (oranžová)"}
    j = 0
    for k, txt in ship.items():
        name = "M_Ship_%s_%s" % (rs.m.ship, k)
        if rs.cols.get(name) is None or name not in rs.ship_mats:
            continue
        X = x + (j % ncol) * col_w
        Y = y - (j // ncol) * 5.0
        sh.geom(box(X, Y - 1.2, X + 9, Y + 2.6), fc=hexrgb(rs.cols[name]), ec=INK, lw=0.18, z=5)
        sh.t(X + 11, Y, txt, 2.1)
        j += 1
    y -= -(-j // ncol) * 5.0 + 1.0
    sh.line([(x, y + 0.8), (x + 9, y + 0.8)], md.CUT_LW, INK)
    sh.t(x + 11, y, "trup v řezu (z modelu lodi, výkresy exteriéru E-01 až E-08)", 2.1)
    y -= 6.0
    if lights:
        sh.t(x, y, "Světla (barva symbolu = barva světla)", 2.8, weight="bold")
        y -= 5.6
        demo = [("spot", "work", "bodovka (kužel; v pohledu směr)"), ("point", "neutral", "bodové světlo"),
                ("rect", "warm", "lineární pás (délka = šířka zdroje)"), ("point", "cool", "studené (UI, výklenky)")]
        for k, (t, role, txt) in enumerate(demo):
            X = x + (k % 2) * 95
            Y = y - (k // 2) * 6.0
            e = im.Element("x", "light", None, "built", "", "", type=t, role=role, colour=(1, 1, 1))
            rs.lamp(X + 4, Y + 0.8, e, ((1.0, 0.0), 4.0) if t == "rect" else None, tag=False)
            sh.t(X + 10, Y, txt, 2.1)
        y -= 12.5
        e = im.Element("x", "light", None, "built", "", "", type="point", role="warm", colour=(1, 1, 1), shadow=True)
        rs.lamp(x + 4, y + 0.8, e, tag=False)
        sh.t(x + 10, y, "▲ v rohu = vrhá stín (hlavní světla); „i“ = jen při chůzi interiérem (MegaLights: světla a stíny paprskem)", 2.1)
        y -= 4.4
        sh.t(x, y, "Štítek u symbolu = socket dílu; ID světla = ID dílu + / + socket (např. CAB-C-1/Down_0).", 2.1, GREY)
        y -= 3.8
        sh.t(x, y, "cd = svítivost v kandelách (tabulka světel).", 2.1, GREY)
        y -= 6.0
    if other:
        sh.t(x, y, "Ostatní", 2.8, weight="bold")
        y -= 5.4
    if "decal" in other:
        sh.ax.add_patch(MplPolygon([(x, y - 0.8), (x + 9, y - 0.8), (x + 9, y + 2.4), (x, y + 2.4)], closed=True,
                                   fc=hexrgb(DECAL_FILL), ec=DECAL_EDGE, lw=0.2 * PT))
        sh.t(x + 11, y, "decal: výplň = jeho viditelná část z modelu; čárkovaný rámeček = poloha (i za předmětem); D-INT = promítaný", 2.1)
        y -= 4.8
    if "fade" in other:
        sh.geom(box(x, y - 1.2, x + 9, y + 2.6), fc="#E4E4E4", ec="#9A9A9A", lw=0.18, z=5)
        sh.t(x + 11, y, "světlejší = nábytek před čelní stěnou (pohledy 2 a 4)", 2.1)
        y -= 4.8
    if "leaf" in other:
        sh.ax.annotate("", xy=(x + 9, y + 0.8), xytext=(x, y + 0.8), arrowprops=dict(arrowstyle="-|>", lw=0.3 * PT,
                                                                                      color=INK, mutation_scale=6))
        sh.t(x + 11, y, "posuvné křídlo dveří: kam se zasouvá (modře návrh)", 2.1)
        y -= 4.8
    if "capsule" in other:
        sh.ax.add_patch(FancyBboxPatch((x + 2.5, y - 1.2), 4, 4, boxstyle="round,pad=0,rounding_size=2", fc="#DFF1E1",
                                       ec="#2E7D32", lw=0.3 * PT))
        sh.t(x + 11, y, "kapsle postavy v lodi 0,56 × 1,80 m, oko 1,65 m", 2.1)
        y -= 4.8
    if "move" in other:
        sh.line([(x, y + 0.8), (x + 4.5, y + 0.8)], 0.4, STATUS_COL["remove"], ls="--")
        sh.ax.annotate("", xy=(x + 9, y + 0.8), xytext=(x + 4.6, y + 0.8), zorder=20, arrowprops=dict(
            arrowstyle="-|>", lw=0.25 * PT, color=STATUS_COL["proposed"], mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t(x + 11, y, "přesun: dřívější poloha červeně čárkovaně, šipka k nové (modře)", 2.1)
        y -= 4.8
    for st in ("built", "proposed"):
        sh.line([(x, y + 0.8), (x + 9, y + 0.8)], 0.5, STATUS_COL[st])
        sh.t(x + 11, y, {"built": "postaveno (je v datech stavby)", "proposed": "+ návrh: v datech návrhu, zatím nepostaveno"}[st],
             2.1, STATUS_COL[st])
        y -= 4.4
    return y


def notes(rs, x, ytop, width=186.0):
    sh, m = rs.sh, rs.m
    sh.t(x, ytop - 3, "POZNÁMKY", 3.4, weight="bold")
    lines = [
        "1. Kreslí skript z postavené geometrie (FBX dílů kitu a lodi) a z dat; ID na výkresu = ID v datech.",
        "2. Souřadnice v metrech: x od zádi, y k levoboku, z od paluby; měřítko 1:20.",
        "3. ID: <místnost>-<druh>-<pořadí>: W stěna (L levobok, R pravobok, od zádi), B přepážka (A zadní, F přední), "
        "C strop, FL podlaha, U nábytek, M komponenta, O objekt nebo vybavení lodi, DR dveře; D-INT promítaný nápis, "
        "D-I nápis interiéru lodi; světlo a decal dílu = ID dílu / socket nebo položka; L-FIX světlo svítícího pásu "
        "nebo lampy lodi, L-INT světlo místnosti lodi.",
        "4. Stěny: pohled ze středu místnosti, řez osou místnosti (podlaha a strop v řezu).",
        "5. Strop: pohled zespodu, orientace jako půdorys (příď vpravo, levobok nahoře); světla stěn (Cove, Wash) jsou "
        "v pohledech stěn.",
        ("6. Mřížka kitu začíná na začátku běhu stěn (x %s) a na ose lodi." % im.fmt(rs.grid_origin)) if rs.grid_origin
        is not None else "6. Místnost staví loď (hs_interior, hs_cockpit), ne kit: bez mřížky a dílů kitu.",
        "7. Karty špíny jsou jen v tabulce decalů (počet na díl).",
    ]
    if any(str(e.src).endswith("SOCKET_Component") for e in m.in_room(rs.rid, ("component",))):
        lines.append("8. Šedě tečkovaně v půdorysu: komponenta vysunutá z výklenku do chodby (výměna); DET. A–C = řezy "
                     "detailů výklenků.")
    if any(p.category == "Floor" and "Grille" in p.part for p in rs.places):
        lines.append("9. Pod roštem podlahy servisní kanál: dvě potrubí a kabelový svazek na podpěrách, tlumený pásek.")
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(ds.wrap(sh, ln, 2.3, width, 3)):
            sh.t(x + (0 if k == 0 else 4), y, part, 2.3)
            y -= 3.7
    y -= 2.5
    sh.t(x, y, "LISTY INTERIÉRU A KONCEPTŮ", 3.0, weight="bold")
    y -= 5
    for code, title in PLANNED:
        sh.t(x, y, code, 2.3, weight="bold")
        here = code == getattr(rs, "sheet", None)
        sh.t(x + 17, y, title + (" (tento list)" if here else ""), 2.3, INK if code in SHEETS else GREY,
             weight="bold" if here else "normal")
        y -= 3.7
    return y


def schedules(rs, x, ytop, decals_at=None):
    m, sh = rs.m, rs.sh
    room = rs.rid
    TS, RH = 2.5, 4.4
    els = [e for e in m.elements if (e.room == room or room in (e.extra.get("rooms") or ())) and e.status != "remove"]
    K = [e for e in els if e.kit and e.cat in ("wall", "bulkhead", "ceiling", "floor", "cockpit")]
    K.sort(key=lambda e: ({"wall": 0, "bulkhead": 1, "ceiling": 2, "floor": 3, "cockpit": 4}[e.cat], e.id))
    cols = [("ID", 21, "left"), ("díl kitu", 41, "left"), ("umístění (m)", 52, "left", 2), ("trojúh.", 11, "right")]
    rows = [([e.id, e.kit, e.where, "%d" % e.extra["tris"]], STATUS_COL[e.status]) for e in K]
    if not K:                                   # a room the ship builds (the cockpit)
        sh.t(x, ytop - 3.4, "DÍLY KITU: žádné – místnost staví loď (hs_interior, hs_cockpit)", 3.4, weight="bold")
        y1 = ytop - 8.0
    else:
        y1 = ds.table(sh, x, ytop, "DÍLY KITU (stěny, přepážky, strop, podlaha, kokpit)", cols, rows, size=TS, rowh=RH)
    sched = {"kit": {e.id for e in K}}
    # each kit part's purpose once
    xp = x + sum(c[1] for c in cols) + 5
    parts = {}
    for e in K:
        parts.setdefault(e.kit, []).append(e.id)
    colsP = [("díl kitu", 41, "left"), ("ks", 6, "right"), ("účel (co díl dělá)", 108, "left", 4)]
    rowsP = [([k, len(v), m.design["kit_purpose"].get(k, "")], INK) for k, v in sorted(parts.items())]
    yp = ds.table(sh, xp, ytop, "ÚČEL DÍLŮ KITU", colsP, rowsP, size=TS, rowh=RH) if K else y1
    # furniture, doors, components
    F = [e for e in els if e.cat in ("furniture", "component", "object", "door")]
    F.sort(key=lambda e: ({"furniture": 0, "door": 1, "component": 2, "object": 3}[e.cat], e.id))
    colsF = [("ID", 24, "left"), ("prvek", 27, "left", 2), ("stav", 22, "left", 3), ("umístění (m)", 44, "left", 3),
             ("díl / provedení", 33, "left", 2), ("účel; u dveří pohyb a ovládání; u komponent výklenek, přístup a výměna",
                                                  130, "left", 6)]

    def place(e):
        p_ = e.extra.get("placement")
        if p_ is not None:
            fy = p_.dir_layout(1.0, 0.0)[1]
            return "%s, na podlaze, čelem k %s" % (e.where.replace(" (střed zadní hrany)", ""),
                                                    "levoboku" if fy > 0 else "pravoboku") + " (střed zadní hrany)"
        return e.where
    rowsF = []
    for e in F:
        if e.cat == "door":
            lf = e.extra.get("leaf") or {}
            what = "%s, šířka %s" % (lf.get("type", ""), im.fmt(e.extra["width"]))
            txt = "%s Pohyb: %s.%s" % (lf.get("purpose", ""), lf.get("motion") or "–",
                                       (" Ovládání: " + lf["operation"] + ".") if lf.get("operation") else "")
            st = {"built": "postaveno", "proposed": "otvor postaven, křídlo návrh", "none": "otvor bez křídla"}.get(lf.get("leaf"), "")
            col = STATUS_COL["proposed"] if lf.get("leaf") == "proposed" else INK
            rowsF.append(([e.id, e.name, st, place(e), what, txt], col))
        elif e.cat == "component":
            txt = "%s Výklenek: %s. Přístup: %s. Výměna: %s." % (e.purpose, e.extra.get("bay") or "–",
                                                                 e.extra.get("access") or "–", e.extra.get("replace") or "–")
            if e.extra.get("note"):
                txt += " Stav: " + e.extra["note"] + "."
            rowsF.append(([e.id, e.name, e.extra.get("state_cz") or im.STATUS_CZ[e.status], place(e),
                           "pod podlahou" if e.extra.get("below") else ("výklenek stěnového modulu" if e.extra.get("bay")
                                                                        else "layout"), txt], STATUS_COL[e.status]))
        else:
            rowsF.append(([e.id, e.name, im.STATUS_CZ[e.status], place(e), e.kit or "loď", e.purpose], STATUS_COL[e.status]))
    y2 = ds.table(sh, x, min(y1, yp) - 4, "NÁBYTEK, DVEŘE, KOMPONENTY", colsF, rowsF, size=TS, rowh=RH)
    sched["furniture"] = {e.id for e in F}
    # lights grouped by socket and intensity
    L = [e for e in els if e.cat == "light"]
    groups = {}
    fixmats = (m.recipe["interior"].get("fixture_lights") or {}).get("materials", {})

    def ship_kind(e):
        """A ship light (L-FIX: one per glowing strip or lamp, L-INT: the room's own) by its glow material's colour."""
        c = np.asarray(e.extra["colour"][:3])
        best = min(fixmats.items(), key=lambda kv: float(np.sum((np.asarray(kv[1]["color"]) - c) ** 2)), default=(None, None))[0]
        return SHIP_GLOW_CZ.get(best, "barva lodi")
    for e in L:
        if e.id.startswith("L-"):
            kind = e.id.split("-")[1]
            below = kind == "FIX" and e.extra["pos"][2] < rs.fz - 0.1
            c = e.extra["colour"]
            cls = ship_kind(e) if kind == "FIX" else ("studená bílá" if c[2] > c[0] else "teplá bílá")
            if kind == "SET":                    # the setup's lights (pilot, screens): one row, their cd as a range
                groups.setdefault(("L-SET", -1.0, "studená bílá / modrá"), []).append(e)
                continue
            groups.setdefault(("L-" + kind + ("-stair" if below else ""), round(e.extra["cd"], 2), cls), []).append(e)
            continue
        sock = e.id.split("/")[-1] if "/" in e.id else e.id
        groups.setdefault((sock.split("_")[0], round(e.extra["cd"], 2), e.extra.get("role")), []).append(e)
    colsL = [("světla: ID dílu + socket", 70, "left", 3), ("ks", 7, "right"), ("typ", 31, "left"), ("barva", 26, "left"),
             ("cd", 12, "right"), ("stín", 9, "left"), ("int.", 8, "left"), ("účel", 34, "left", 3)]
    rowsL = []
    for (sock, cd, role), es in sorted(groups.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        e0 = es[0]
        hosts = sorted({e.id.split("/")[0] for e in es})
        socks = sorted({e.id.split("/")[-1] for e in es if "/" in e.id})
        ident = ", ".join(hosts) + ((" / " + ", ".join(socks)) if socks else "")
        if sock == "L-SET":
            ident = "L-SET: pilot, %d obrazovky" % (len(es) - 1)
        elif sock.startswith("L-"):
            nums = sorted(int(e.id.rsplit("-", 1)[1]) for e in es)
            ident = "%s-%s" % (sock[:5], ", ".join(str(n) for n in nums))
        rowsL.append(([ident, len(es), " + ".join(sorted({LIGHT_TYPE_CZ.get(e.extra["type"], e.extra["type"]) for e in es})) +
                       (" %d°" % e0.extra["cone"] if e0.extra.get("cone") else ""),
                       LIGHT_ROLE_CZ.get(role, role or "barva lodi"),
                       ("%g" % cd).replace(".", ",") if cd >= 0 else "%s…%s" % (
                           im.fmt(min(e.extra["cd"] for e in es), 1), im.fmt(max(e.extra["cd"] for e in es), 0)),
                       "ano" if e0.extra.get("shadow") else "–", "ano" if e0.extra.get("interior_only") else "–",
                       ("světlo výklenku (svítí na komponentu)" if sock == "Bay" and (e0.kit or "").startswith("Wall_ComponentBay")
                        else SHIP_LIGHT_CZ.get(sock) or SOCKET_CZ.get(sock, e0.purpose or sock))], INK))
    xl = x + 286
    y3 = ds.table(sh, xl, ytop, "SVĚTLA (%d)" % len(L), colsL, rowsL, size=TS, rowh=RH)
    sched["lights"] = {e.id for e in L}
    # decals: paint per element, grime counted per part
    D = [e for e in els if e.cat == "decal" and not e.extra.get("grime")]
    G = [e for e in els if e.cat == "decal" and e.extra.get("grime")]
    colsD = [("ID", 46, "left"), ("knihovna / textura", 33, "left"), ("osazeno", 17, "left"), ("účel / text", 101, "left", 5)]

    def size(e):
        if e.id in rs.decal_pos:                    # as built: the quad's extent along its own two axes
            pts = rs.decal_pos[e.id][1]
            q = pts - pts.mean(axis=0)
            _, sv, vt = np.linalg.svd(q, full_matrices=False)
            ext = [float(np.ptp(q @ vt[k])) for k in (0, 1)]
            return "%d×%d cm" % (round(ext[0] * 100), round(ext[1] * 100))
        s_ = e.extra.get("size")
        if e.extra.get("projected"):
            d_ = next(v for v in m.setup["decals"] if isinstance(v, dict) and v.get("id") == e.id)
            return "%d×%d cm" % (round(2 * d_["size"][2]), round(2 * d_["size"][1]))
        return "%d×%d cm" % (round(s_[0] * 100), round(s_[1] * 100)) if s_ and s_[0] else ""
    rowsD = [([e.id, e.extra.get("item", ""), size(e), e.purpose or e.extra.get("note", "")], STATUS_COL[e.status])
             for e in sorted(D, key=lambda e: (not e.id.startswith("D-"), e.id))]
    gcount = {}
    for e in G:
        gcount.setdefault(e.extra["host"], []).append(e.extra["item"])
    rowsD.append((["karty špíny (%d)" % len(G), "grime_*", "", "; ".join("%s %d×" % (h, len(v)) for h, v in sorted(gcount.items()))],
                  GREY))
    y4 = ds.table(sh, *(decals_at or (xl, y3 - 4)), "DECALY A NÁPISY (%d + %d karet špíny)" % (len(D), len(G)), colsD, rowsD, size=TS, rowh=RH)
    sched["decals"] = {e.id for e in D} | {e.id for e in G}
    rs.schedules = sched
    return min(y2, y4)


def intensity_line(m, rid):
    """How the game gets a light's candelas from the kit's (kit_rooms.py): the socket's own scale, the room's light zone
    and the ship's scale - the formula the light table's values follow."""
    R = m.light_rules
    zones = [z for z in m.mods.get("light_scale", []) if not isinstance(z, str) and z[3] == rid]
    parts = ["cd dílu"]
    for k, v in sorted(R["SOCKET_SCALE"].items()):
        parts.append("%s ×%s (kit_rooms)" % (k.replace("SOCKET_Light_", ""), im.fmt(v, 1)))
    for z in zones:
        parts.append("zóna místnosti ×%s" % im.fmt(z[2], 1))
        for k, v in (z[4] if len(z) > 4 else {}).items():
            parts.append("%s ×%s navíc" % (k.replace("SOCKET_Light_", ""), im.fmt(v, 1)))
    parts.append("hra ×%s" % im.fmt(R["SHIP_LIGHT_SCALE"], 1))
    if not any(e.kit for e in m.in_room(rid, ("light",))):        # a room the ship lights (the cockpit)
        fm = (m.recipe["interior"].get("fixture_lights") or {}).get("materials", {})
        return ("Intenzita světel lodi je z exportu stavby (Export/%s_lights.json): L-FIX = jedno světlo na úsek svítícího "
                "pásu nebo lampu (%s), L-INT = světla místnosti z receptu (hs_interior)." % (
                    m.ship, ", ".join("%s %s cd/m" % (SHIP_GLOW_CZ.get(k, k), im.fmt(v.get("cd_per_m", 0), 2))
                                      for k, v in fm.items())))
    return "Intenzita v tabulce = " + " × ".join(parts) + example_line(m, rid)


def example_line(m, rid):
    """One of the room's kit lights worked through the formula (a wall wash where there is one), from its own data."""
    R = m.light_rules
    L = [e for e in m.in_room(rid, ("light",)) if e.kit]
    e = next((e for e in L if "/Wash" in e.id), L[0] if L else None)
    if e is None:
        return "."
    sname = "SOCKET_Light_" + e.id.split("/")[-1]
    fs = [e.extra["cd_part"]]
    fs += [v for k, v in R["SOCKET_SCALE"].items() if sname.startswith(k)][:1]
    p = e.extra.get("placement") or next(q for q in m.placements if q.tag == e.extra["host"])
    for z in m.mods.get("light_scale", []):
        if not isinstance(z, str) and z[0] <= e.extra["pos"][0] <= z[1]:
            fs.append(z[2])
            fs += [v for k, v in (z[4] if len(z) > 4 else {}).items() if sname.startswith(k)][:1]
            break
    fs.append(R["SHIP_LIGHT_SCALE"])
    return " (např. %s: %s = %s cd)." % (e.id, " × ".join(im.fmt(f, 2).rstrip("0").rstrip(",") for f in fs),
                                         im.fmt(e.extra["cd"], 2))


RULE_CZ = {"living": "obytné místnosti", "cockpit": "kokpit", "hold": "nákladový prostor"}


def light_summary(rs, x, ytop):
    """The room's lights in numbers and the performance note (dossier bod 4: count per room, shadows, performance)."""
    m, sh = rs.m, rs.sh
    L = [e for e in m.elements if e.room == rs.rid and e.cat == "light"]
    area = rs.built_area()
    dens = len(L) / area
    rule_key = {"crew": "living", "command": "cockpit", "cargo": "hold"}.get(rs.room["zone"])
    rule_note = ""
    if rule_key is None:                            # the kit has no rule for the room's zone: compare with living
        rule_key, rule_note = "living", " – kit nemá pravidlo pro technické prostory, srovnání s obytnými"
    rule = m.rules["lights"]["density_per_m2"][rule_key]
    shadow = [e for e in L if e.extra.get("shadow")]
    inter = [e for e in L if e.extra.get("interior_only")]
    flight = [e for e in L if not e.extra.get("interior_only")]
    sh.t(x, ytop - 3.4, "SVĚTLA – SOUHRN A VÝKON", 3.2, weight="bold")
    lines = [
        "%d světel na %s m² postavené podlahy (mezi líci) = %s /m² (pravidlo kitu pro %s %s–%s /m²%s)." % (
            len(L), im.fmt(area, 1), im.fmt(dens, 2), RULE_CZ[rule_key], im.fmt(rule[0], 1), im.fmt(rule[1], 1), rule_note),
        ("Stín vrhá %d (hlavní světla: %s); ostatní mají jen krátké kontaktní stíny." % (
            len(shadow), ", ".join(sorted({e.id.split("/")[-1].split("_")[0] for e in shadow})))) if shadow else
        "Žádné světlo nevrhá stín (světla lodi mají jen krátké kontaktní stíny).",
        "%d světel „i“ svítí jen při chůzi lodí pěšky; za letu svítí %d (z nich %d se stínem)." % (
            len(inter), len(flight), len([e for e in flight if e.extra.get("shadow")])),
        intensity_line(m, rs.rid),
        "cd = svítivost v kandelách; „i“ = světlo, které hra zapíná jen při chůzi lodí (za letu je vypnuté, šetří výkon).",
        "Výkon: cenu interiéru určuje počet osvětlených pixelů a stíny světel – každé nové světlo se měří v zabalené hře "
        "v 1080p; optimalizace až na konci (autor 29. 9.).",
    ]
    if dens > rule[1]:
        walls = [e for e in L if e.id.split("/")[-1].split("_")[0] in ("Cove", "Wash")]
        lines.append("Hustota je nad pravidlem kitu: %d z %d světel jsou lišty a osvětlení stěn (Cove, Wash: 2 na stěnový "
                     "modul)." % (len(walls), len(L)))
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(ds.wrap(sh, ln, 2.5, 255, 3)):
            sh.t(x + (0 if k == 0 else 3), y, ("• " if k == 0 else "") + part, 2.5)
            y -= 4.0
    rs.light_lines = lines
    y -= 3
    if getattr(rs, "zone_note", None):
        sh.t(x, y - 3.4, "POD PODLAHOU A NAD STROPEM", 3.2, weight="bold")
        y -= 9
        for k, part in enumerate(ds.wrap(sh, rs.zone_note, 2.5, 255, 6)):
            sh.t(x, y, part, 2.5)
            y -= 4.0
    return y


def key_plan(rs, x, ytop):
    """Where the room is in the ship: the deck outline and the rooms of the layout, this room hatched (1:125)."""
    m, sh = rs.m, rs.sh
    s = 1000.0 / 125.0
    deck = m.layout["decks"]["main"]["outline"]
    xs = [p[0] for p in deck]
    x0 = min(xs) - 1.2
    sh.t(x, ytop - 3.4, "KLÍČOVÝ PLÁN", 3.2, weight="bold")
    sh.t(x + 32, ytop - 3.4, "1 : 125", 3.2)
    oy = ytop - 10 - 4.6 * s
    P = lambda px, py: (x + (px - x0) * s, oy + py * s)                       # noqa: E731
    ext = m.layout.get("exterior", {}).get("top") or []
    for part in ext:
        if part.get("kind") in ("hull", "engine") and part.get("poly"):
            pts = [P(*q) for q in part["poly"]]
            sh.ax.add_patch(MplPolygon(pts, closed=True, fc="#F4F4F4", ec=GREY, lw=0.15 * PT, zorder=5))
            if part.get("mirror"):
                sh.ax.add_patch(MplPolygon([P(q[0], -q[1]) for q in part["poly"]], closed=True, fc="#F4F4F4", ec=GREY,
                                           lw=0.15 * PT, zorder=5))
    sh.ax.add_patch(MplPolygon([P(*q) for q in deck], closed=True, fc="white", ec=INK, lw=0.3 * PT, zorder=6))
    for rid, r in m.rooms.items():
        pts = [P(*q) for q in r["poly"]]
        here = rid == rs.rid
        sh.ax.add_patch(MplPolygon(pts, closed=True, fc="#DCE9F7" if here else "none", ec=INK, lw=(0.4 if here else 0.15) * PT,
                                   hatch="////" if here else None, zorder=7))
        cx = sum(q[0] for q in pts) / len(pts)
        cy = sum(q[1] for q in pts) / len(pts)
        sh.t(cx, cy - 1.0, r["code"], 2.2, weight="bold" if here else "normal", ha="center", z=8, bg="white" if here else None)
    sh.t(x, oy - 4.6 * s - 4, "příď vpravo, levobok nahoře; vyšrafovaná místnost je na tomto listu", 2.0, GREY)
    return oy - 4.6 * s - 8


# the hygiene cell's door in the part's frame (Tools/Kit/kit_furniture.hygiene: the front at x 1.0, the doorway
# half width 0.4, the leaf's fields 12 mm proud, the hazard band 18-58 mm in from the +Y edge, the pull 80-140 mm)
HYG_FRONT, HYG_DW = 1.0, 0.4


def bay_modules(rs):
    """The components built in the room's bay modules, one per kind (the coolers are alike: the port one)."""
    m = rs.m
    comps = [e for e in m.in_room(rs.rid, ("component",)) if e.extra.get("bay") and str(e.src).endswith("SOCKET_Component")]
    comps.sort(key=lambda e: (-e.extra["rect"][2], e.extra["rect"][0]))
    out, kinds = [], set()
    for e in comps:
        kind = rs.el[e.extra["bay"]].kit
        if kind in kinds:
            continue
        kinds.add(kind)
        out.append(e)
    return out


def bay_details(rs, x0=592.0, oy=336.0):
    """The component bays of a room (the technical corridor, I-03) in cross section 1:10 (author 1. 10. 2026: details
    where the 1:20 views run together): one per kind of bay module - the niche behind the wall face (depth, sill, head
    from Tools/Kit/kit_batch4.py), the component in it, its access and how it comes out. In the second row right of
    the walls (round 1 of I-03: in the first row detail B ran over the legend)."""
    m, sh, d = rs.m, rs.sh, rs.d
    k = im.bay_constants()
    x = x0
    rs.detail_marks = []
    for n, e in enumerate(bay_modules(rs)):
        r, z = e.extra["rect"], e.extra["z"]
        host = rs.el[e.extra["bay"]]
        xc = (r[0] + r[1]) / 2
        face = host.extra["placement"].ue_to_layout(0, 0, 0)[1]
        sgn = 1 if face > 0 else -1
        letter = "ABC"[n]
        ya, yb = face - sgn * 0.3, face + sgn * 0.68               # 0.3 into the corridor, 0.68 behind the face
        u0, u1 = sorted((-ya, -yb))
        view = "DET-" + letter
        title = "DETAIL %s – %s (%s), ŘEZ x %s" % (letter, e.name.upper(), host.id, im.fmt(xc))
        vw, W = rs.detail_view(view, title, 10, x, oy, (0, -1, 0), (0, 0, 1), (1, 0, 0), u0, u1, -0.1, 1.45,
                               ((xc, 0, 0), (1, 0, 0)), ((xc - 0.01, -2.8, -0.3), (xc + 0.5, 2.8, 2.6)))
        rs.detail_marks.append((letter, xc, face, sgn))
        depth = k["BAY_DEPTH"][host.kit.rsplit("_", 1)[1]]
        back = face + sgn * (depth + k["LINER"])
        items = [(host.id, "%s (%s)" % (host.id, host.kit), (xc, face - sgn * 0.01, 1.3)),
                 (e.id, "%s %s – ve výklenku" % (e.id, e.name), (xc, (face + back) / 2, (z[0] + z[1]) / 2)),
                 ("#sill", "práh výklenku: komponenta vyjíždí přes něj do chodby", (xc, face + sgn * 0.08, z[0])),
                 ("#access", "přístup: " + (e.extra.get("access") or "–"), (xc, face - sgn * 0.005, z[1] - 0.12))]
        reqs = rs.detail_items(view, vw, items)
        Xf, Xb = vw.P((xc, face, 0))[0], vw.P((xc, back, 0))[0]
        Yd = vw.P((xc, 0, z[1] + 0.1))[1]
        rs.dim((min(Xf, Xb), Yd), (max(Xf, Xb), Yd), "%s světlá (%s s obložením)" % (im.fmt(depth), im.fmt(abs(back - face))))
        Xd = vw.P((xc, face - sgn * 0.2, 0))[0]
        for za, zb in ((0.0, z[0]), (z[0], z[1])):
            rs.dim((Xd, vw.P((xc, 0, za))[1]), (Xd, vw.P((xc, 0, zb))[1]), im.fmt(zb - za))
        for zz in (0.0, z[0], z[1]):
            Y = vw.P((xc, 0, zz))[1]
            sh.line([(Xd - 1.2, Y), (Xd + 3.0, Y)], 0.2, INK, z=48)
            sh.t(Xd + 3.6, Y + 0.6, ("+" if zz else "±") + im.fmt(zz), 2.0, z=48, bg="white")
        A, B = vw.P((xc, (face + back) / 2, z[0] + 0.2)), vw.P((xc, face - sgn * 0.26, z[0] + 0.2))
        sh.ax.annotate("", xy=B, xytext=A, zorder=48, arrowprops=dict(arrowstyle="-|>", lw=0.45 * PT, color=INK,
                                                                      mutation_scale=10, shrinkA=0, shrinkB=0))
        for j, ln in enumerate(ds.wrap(sh, "výměna: " + (e.extra.get("replace") or "–"), 2.0, W[2] - W[0] - 2, 3)):
            sh.t(W[0] + 1.0, W[1] + 6.0 - j * 2.8, ln, 2.0, z=48, bg="white")
        d.place_labels(view, reqs, W[0] - 2, W[2] + 2, tiers_up=[W[3] + 8.0, W[3] + 14.0], tiers_dn=[W[1] - 6.0, W[1] - 12.0],
                       split_y=vw.P((0, 0, 0.7))[1], bus_up=W[3] + 4.0, bus_dn=W[1] - 3.0, size=2.2)
        x = W[2] + 16.0
    return x


def details(rs):
    """Details where the 1:20 views run together (author 1. 10. 2026, as E-07 / E-08 for the exterior): A the hull
    liner's top - chamfer, cable tray, cove and wash lights, ceiling edge - in section 1:5; B the hygiene cell's sliding
    door in plan 1:5 (which way it opens, its seal and pocket). Labels above A only (the title block is under it)."""
    m, sh, d = rs.m, rs.sh, rs.d
    sec = m.rules["sections"]["L38"]
    # ---- A: section through the starboard liner's plain 0.6 m module ahead of the galley, looking forward
    wall = next((e for e in m.in_room(rs.rid, ("wall",)) if e.extra.get("side") == "R" and e.kit.endswith("06L_A")), None)
    if wall is not None:
        xa, xb = m.x_range(wall)
        x = (xa + xb) / 2
        face = wall.extra["placement"].ue_to_layout(0, 0, 0)[1]
        top = sec["vertical_to"] + sec["slope_rise"]
        vw, W = rs.detail_view("DET-A", "DETAIL A – ŘÍMSA A ZKOSENÍ OBLOŽENÍ, ŘEZ x %s K PŘÍDI" % im.fmt(x), 5, 1004.0, 118.0,
                               (0, -1, 0), (0, 0, 1), (1, 0, 0), -(face + 0.55), -(face - 0.25), 1.62, 2.42,
                               ((x, 0, 0), (1, 0, 0)), ((x - 0.01, -2.8, 1.0), (x + 0.4, 2.8, 2.6)))
        items = [(wall.id, "%s (%s)" % (wall.id, wall.kit), (x, face + 0.01, 1.66))]
        lights = [e for e in m.in_room(rs.rid, ("light",)) if e.extra.get("host") == wall.id]
        for e in lights:
            sock = e.id.split("/")[-1]
            items.append((e.id, "%s – %s" % (sock, SOCKET_CZ.get(sock.split("_")[0], "")), (x, e.extra["pos"][1], e.extra["pos"][2])))
        for e in lights:                    # the strips seen end on: a symbol with the aim of the light
            X, Y = vw.P((x, e.extra["pos"][1], e.extra["pos"][2]))
            rs.lamp(X, Y, e, None, tag=False, size=1.6)
            dl = e.extra.get("dir")
            if dl is not None:
                du, dv = np.array(dl) @ vw.u, np.array(dl) @ vw.v
                n = math.hypot(du, dv)
                if n > 0.2:
                    sh.ax.annotate("", xy=(X + du / n * 9, Y + dv / n * 9), xytext=(X + du / n * 2, Y + dv / n * 2), zorder=47,
                                   arrowprops=dict(arrowstyle="-|>", lw=0.25 * PT, color=GREY, mutation_scale=5,
                                                   shrinkA=0, shrinkB=0))
        ceil = next((e for e in m.in_room(rs.rid, ("ceiling",)) if m.x_range(e)[0] <= x <= m.x_range(e)[1]), None)
        if ceil is not None:
            items.append((ceil.id, "%s (okraj stropu)" % ceil.id, (x, face + 0.5, sec["ceiling"])))
        items.append(("#tray", "kabelový žlab na zkosení (součást %s)" % wall.id,
                      (x, face + 0.7 * 0.75 * sec["slope_rise"], sec["vertical_to"] + 0.7 * sec["slope_rise"])))
        reqs = rs.detail_items("DET-A", vw, items)
        # the section's numbers from kit_rules.json sections.L38: the vertical wall, the chamfer, the cove, the ceiling
        Xd = vw.P((x, face - 0.18, 0))[0]
        zs = [sec["vertical_to"], top, sec["cove_to"]]
        for za, zb in zip(zs, zs[1:]):
            rs.dim((Xd, vw.P((x, 0, za))[1]), (Xd, vw.P((x, 0, zb))[1]), im.fmt(zb - za))
        for z in zs:
            Y = vw.P((x, 0, z))[1]
            sh.line([(Xd - 1.2, Y), (Xd + 3.0, Y)], 0.2, INK, z=48)
            sh.t(Xd + 3.6, Y + 0.6, "+" + im.fmt(z), 2.0, z=48, bg="white")
        A = vw.P((x, face, top + 0.04))
        B = vw.P((x, face + 0.75 * sec["slope_rise"], top + 0.04))
        rs.dim(A, B, "%s zkosení" % im.fmt(0.75 * sec["slope_rise"], 3))
        d.place_labels("DET-A", reqs, W[0] - 6, W[2] + 4, tiers_up=[W[3] + 8.0, W[3] + 14.0], tiers_dn=[W[1] - 6.0],
                       split_y=W[1] - 200.0, bus_up=W[3] + 4.0, bus_dn=W[1] - 3.0, size=2.2)
    # ---- B: the hygiene cell's door in plan at 1.0 m
    hyg = next((e for e in m.in_room(rs.rid, ("furniture",)) if e.kit and "Hygiene" in e.kit), None)
    door = next((e for e in m.elements if e.cat == "door" and e.extra["axis"] == "y" and rs.rid in (e.extra.get("rooms") or ())), None)
    if hyg is not None and door is not None:
        p = hyg.extra["placement"]
        dx, dy = door.extra["at"]
        vw, W = rs.detail_view("DET-B", "DETAIL B – DVEŘE HYGIENICKÉ BUŇKY, PŮDORYS V 1,00 m", 5, 542.0, 132.0,
                               (1, 0, 0), (0, 1, 0), (0, 0, -1), dx - 0.6, dx + 0.6, dy - 0.2, dy + 0.18,
                               ((0, 0, 1.0), (0, 0, -1)), ((dx - 0.8, dy - 0.6, -0.1), (dx + 0.8, dy + 0.5, 1.0)))

        def P(bx, by):                      # the part's frame (Blender axes) to layout at the cut's height
            return p.to_layout(bx, by, 1.0)
        items = [(door.id, "%s – posuvné, otevírá se k přídi" % door.id, P(HYG_FRONT + 0.03, 0.0)),
                 (hyg.id, "%s (%s)" % (hyg.id, hyg.kit), P(HYG_FRONT - 0.1, -0.5)),
                 ("#seal", "těsnění na zárubni, kam křídlo dojede", P(HYG_FRONT - 0.001, HYG_DW - 0.003)),
                 ("#pocket", "ústí kapsy: křídlo zajíždí do čelní stěny", P(HYG_FRONT - 0.02, -HYG_DW + 0.004)),
                 ("#band", "výstražný pruh na náběžné hraně", P(HYG_FRONT + 0.006, HYG_DW - 0.038)),
                 ("#pull", "madlo", P(HYG_FRONT + 0.006, HYG_DW - 0.11))]
        reqs = rs.detail_items("DET-B", vw, items)
        a, b = P(HYG_FRONT + 0.06, HYG_DW), P(HYG_FRONT + 0.06, -HYG_DW)
        rs.chain(vw, "x", a[1], [a[0], b[0]])
        tail = vw.P(P(HYG_FRONT + 0.12, HYG_DW - 0.06))
        tip = vw.P(P(HYG_FRONT + 0.12, -HYG_DW + 0.06))
        sh.ax.annotate("", xy=tip, xytext=tail, zorder=48, arrowprops=dict(arrowstyle="-|>", lw=0.45 * PT, color=INK,
                                                                          mutation_scale=10, shrinkA=0, shrinkB=0))
        sh.t((tip[0] + tail[0]) / 2, tip[1] + 1.2, "otevírání → příď", 2.2, ha="center", z=48, bg="white")
        d.place_labels("DET-B", reqs, W[0] - 2, W[2] + 2, tiers_up=[W[3] + 8.0, W[3] + 14.0], tiers_dn=[W[1] - 8.0, W[1] - 14.0],
                       split_y=vw.P(P(HYG_FRONT, 0.0))[1] + 0.5, bus_up=W[3] + 4.0, bus_dn=W[1] - 4.0, size=2.2)


def check_box(rs, x, ytop, width=368.0):
    m, sh = rs.m, rs.sh
    sh.t(x, ytop - 3.4, "KONTROLA DAT (model výkresu proti datům stavby a layoutu)", 3.2, weight="bold")
    y = ytop - 9
    room_ids = {e.id for e in m.elements if e.room == rs.rid}
    items = [(i, t) for i, t in m.checks if i in room_ids]
    extra = [(i, t) for i, t in (m.design.get("review_notes") or {}).items() if i in room_ids] + rs.component_fit()
    extra += getattr(rs, "approach", [])
    extra += rs.leaf_checks()
    if getattr(rs, "landing", None) is not None and rs.landing < 0.56:
        extra.append((rs.room["code"], "plošina mezi horním stupněm a křeslem má %s m (kapsle 0,56 m): postava stojí na "
                                       "horním stupni a usedá zezadu – ověřit ve hře" % im.fmt(rs.landing)))
    fb = (m.recipe["interior"].get("cockpit") or {}).get("footwell_back_x")
    for e in m.in_room(rs.rid, ("component",)):
        r = e.extra.get("rect")
        if fb and r and e.extra.get("below") and r[0] > fb:
            extra.append((e.id, "poklop (x %s … %s) leží za koncovou stěnou prostoru pro nohy (x %s) pod přístrojovou "
                                "deskou – z kokpitu nepřístupný; návrh: servisní panel v čele prostoru pro nohy (x %s), "
                                "výměna dopředu" % (im.fmt(r[0]), im.fmt(r[1]), im.fmt(fb), im.fmt(fb))))
    import re as _re
    said = _re.findall(r"ulička (\d+,\d+) m", rs.room.get("purpose", ""))
    if said and getattr(rs, "sec_stats", {}).get("aisle"):
        built = rs.sec_stats["aisle"]
        if abs(float(said[0].replace(",", ".")) - built) > 0.05:
            extra.append((rs.room["code"], "účel v layoutu uvádí uličku %s m, postavená je %s m (řez R1: mezi lícem "
                                           "obložení a obálkou mřížky) – navrhovaný text: „ulička %s m“; opraví hlavní "
                                           "session (layout čtou i výkresy exteriéru)" % (said[0], im.fmt(built), im.fmt(built))))
    floor = rs.room.get("floor", 0.0) or 0.0
    if floor:                                     # the purpose text against the built floor (the layout: "0,35 m")
        import re
        said = [float(v.replace(",", ".")) for v in re.findall(r"(\d+,\d+) m", rs.room.get("purpose", ""))]
        if said and all(abs(v - floor) > 0.01 for v in said):
            extra.append((rs.room["code"], "účel v layoutu uvádí %s m, postavená podlaha je +%s – opravit text v layoutu "
                                           "(hlavní session: otisky E-01 až E-08)" % (", ".join(im.fmt(v) for v in said), im.fmt(floor))))
    extra += rs.hidden_decals()
    for e in m.in_room(rs.rid, ("component",)):
        pr = e.extra.get("proposal")
        if pr:
            extra.append((e.id, "%s (čeká na autora): %s … %s, y %s … %s – %s" % (
                pr.get("label", "návrh"), im.fmt(pr["rect"][0]), im.fmt(pr["rect"][1]), im.fmt(pr["rect"][2]),
                im.fmt(pr["rect"][3]), pr.get("why", ""))))
    for e in m.in_room(rs.rid, ("component",)):
        if e.status == "proposed":
            extra.append((e.id, "%s: %s" % (e.name, e.extra.get("note"))))
    for ident, txt in items + extra:
        for k, ln in enumerate(ds.wrap(sh, "%s: %s" % (ident, txt), 2.3, width, 4)):
            sh.t(x + (0 if k == 0 else 3), y, ("• " if k == 0 else "") + ln, 2.3)
            y -= 3.7
    rs.checks = items + extra
    return y


def title_block(rs, x, W, sheet):
    sh, m = rs.sh, rs.m
    x1 = W - 10
    y0, y1 = 10, 114
    sh.rect(x, y0, x1, y1, ec=INK, lw=0.5, z=50)
    sh.t(x + 3, y1 - 6, "GAMESPACE  ·  HALCYON FREIGHTWORKS", 2.5, GREY)
    sh.t(x + 3, y1 - 13, "WAYFARER – návrh interiéru (dossier bod 4)", 4.8, weight="bold")
    sh.t(x + 3, y1 - 20, SHEETS[sheet][1] if not (getattr(rs, "page", None) and rs.page[0] == 2) else
         SHEETS[sheet][1].split(":")[0] + ": tabulky dílů, nábytku, světel a decalů; souhrn světel", 3.2)
    sh.t(x + 3, y1 - 25.5, "Kit Halcyon (paleta Halcyon), postaveno z kitu 30. 9. 2026" if any(
        p.category == "Wall" for p in getattr(rs, "places", [])) or getattr(rs, "rid", None) is None else
        "Staví loď (hs_interior, hs_cockpit), z kitu jen paleta Halcyon", 2.4)
    ya = y1 - 29
    sh.line([(x, ya), (x1, ya)], 0.25, z=50)
    meta = SHEET_META.get(sheet, SHEET_META_DEFAULT)
    page = getattr(rs, "page", None)
    tables = bool(page and page[0] == 2)
    cells = [("List", meta.get("list", sheet) + (" (%d/%d)" % page if page else "")), ("Revize", meta.get("rev", m.design["revision"])),
             ("Měřítko", meta.get("scale") or ("–" if tables else "1:20")), ("Formát", "A0 na šířku" if sh.w > 1000 else "A1 na šířku"), ("Datum", meta.get("date", m.design["date"])), ("Stav", meta["state"])]
    cw = (x1 - x) / 3
    for i, (k, v) in enumerate(cells):
        cx = x + (i % 3) * cw
        cy = ya - (i // 3) * 12
        sh.t(cx + 2, cy - 3.8, k, 2.0, GREY)
        sh.t(cx + 2, cy - 9.4, v, 2.8, STATUS_COL["proposed"] if i == 5 else INK, weight="bold")
        if i % 3:
            sh.line([(cx, cy), (cx, cy - 12)], 0.25, z=50)
    yb = ya - 24
    sh.line([(x, yb), (x1, yb)], 0.25, z=50)
    for i, (k, v) in enumerate((("Kreslil", "Claude (skript %s), %s" % (getattr(rs, "script", "draw_interior_sheet.py"), meta.get("date", m.design["date"]))),
                                ("Kontroloval", "kritik technických výkresů"),
                                ("Schválil", "autor: styl ________ ; obsah ________"))):
        cx = x + i * cw
        sh.t(cx + 2, yb - 3.8, k, 2.0, GREY)
        for j, ln in enumerate(ds.wrap(sh, v, 2.3, cw - 4, 2)):
            sh.t(cx + 2, yb - 8.4 - j * 3.0, ln, 2.3)
        if i:
            sh.line([(cx, yb), (cx, yb - 14)], 0.25, z=50)
    yr = yb - 14
    sh.line([(x, yr), (x1, yr)], 0.25, z=50)
    sh.t(x + 2, yr - 3.8, "Revize", 2.0, GREY)
    sh.t(x + 2, yr - 8.2, meta["revs"][-1].format(date=meta.get("date", m.design["date"])), 2.4)
    yd = yr - 11
    sh.line([(x, yd), (x1, yd)], 0.25, z=50)
    dg = m.digests
    sh.t(x + 2, yd - 4.2, "Data (sha1 částí pro interiér): " + " · ".join("%s %s" % (k, v) for k, v in dg.items()), 1.9)
    sh.t(x + 2, yd - 8.0, "Jeden zdroj dat: výkres obsahuje jen to, co je v datech, a data jen to, co je ve výkresu "
                          "(test Tools/Tests/test_interior_drawing.py).", 2.0)
    sh.t(x + 2, yd - 11.8, "Geometrie z FBX v Git LFS; ID, účely a návrhy v Design/%s_interior_design.json." % m.ship, 2.0)


def save(rs, sheet, dpi, out_dir, pages=None, extra=None):
    """The sheet's PNG (pages: one PNG per page, <base>_1.png …) and PDF, and its sidecar JSON."""
    m = rs.m
    out_dir = out_dir or os.path.join(im.ROOT, "ArtSource", "Ships", m.ship, "Design", "Drawings")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "%s_%s" % (m.ship, SHEETS[sheet][0]))
    pdf_dir = os.path.join(im.ROOT, "Saved", "Drawings")
    os.makedirs(pdf_dir, exist_ok=True)
    side = {
        "_comment": "Written by Tools/Design/draw_interior_sheet.py: the IDs this sheet draws and labels per view and "
                    "lists per schedule, with the digests of the data it was drawn from (Tools/Tests/test_interior_drawing.py).",
        "sheet": sheet, "ship": m.ship, "room": rs.rid, "section_x": rs.section_x, "digests": m.digests,
        "geometry": m.geometry_digests(),
        "drawn": {k: sorted(v) for k, v in rs.drawn.items()},
        "labelled": {k: sorted(i for i in v if not i.startswith("#")) for k, v in rs.d.labelled.items()},
        "schedules": {k: sorted(v) for k, v in rs.schedules.items()},
        "checks": [list(c) for c in rs.checks],
    }
    if pages:
        side["pages"] = ["%s_%d.png" % (os.path.basename(base), i + 1) for i in range(len(pages))]
    if extra:
        side.update(extra)
        side["room"] = None
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, ensure_ascii=False, indent=1)
    for i, sh in enumerate(pages or [rs.sh]):
        suf = "_%d" % (i + 1) if pages else ""
        sh.save(base + suf + ".png", dpi, os.path.join(pdf_dir, os.path.basename(base) + suf + ".pdf"))
    print("INTSHEET %s wrote %s.png (%d dpi) and .json, PDF in Saved/Drawings" % (sheet, os.path.relpath(base, im.ROOT), dpi))
    return base


def draw(ship="Wayfarer", dpi=200, out_dir=None, sheets=None):
    ds.setup_fonts()
    m = im.Model(ship)
    if not m.geometry_ready():
        raise SystemExit("the FBX files are Git LFS pointers here (git lfs pull): the interior sheets draw the built meshes")
    geo = Geo(m)
    out = []
    # R1: the hold through the fuel tank and the cargo grid; the corridor through the reactor and the shield generator;
    # the cabin through the life support's middle (its layout v2, author 1. 10. 2026), the berth and the galley unit;
    # the cockpit through its standing area between the stairs' top and the seat (the capsule, the seat beyond)
    if not sheets or "I-06" in sheets:
        out.append(draw_sections_sheet(m, geo, "I-06", dpi, out_dir))
    for sheet, (rid, sx, kind) in (("I-02", ("hold", 6.4, "long")), ("I-03", ("tech", 9.0, "small")),
                                   ("I-04", ("cabin", 13.7, "room")), ("I-05", ("cockpit", 16.4, "room"))):
        if sheets and sheet not in sheets:
            continue
        if kind == "long":
            out.append(draw_long_room_sheet(m, geo, sheet, rid, sx, dpi, out_dir))
        elif kind == "small":
            out.append(draw_room_sheet(m, geo, sheet, rid, sx, dpi, out_dir, rcp_x=232.0, sec_x=420.0))
        else:
            raised = m.rooms[rid].get("floor") or 0.0
            out.append(draw_room_sheet(m, geo, sheet, rid, sx, dpi, out_dir, ye=335.0 - raised * S20 if raised else 335.0,
                                       ytab=306.0 - raised * S20 if raised else 306.0))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ship", nargs="?", default="Wayfarer")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--sheets", nargs="*")
    a = ap.parse_args(argv)
    draw(a.ship, a.dpi, sheets=a.sheets)


if __name__ == "__main__":
    main()
