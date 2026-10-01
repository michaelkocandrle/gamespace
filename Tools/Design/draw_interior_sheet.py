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
GRID_COL = "#6FA8DC"
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
FACE_CZ = {"L": "levobok", "F": "přední stěna", "R": "pravobok", "A": "zadní stěna"}
SHEETS = {"I-04": ("I04_cabin", "Interiér – kajuta: půdorys v mřížce kitu, strop, rozvinuté stěny, řez, světla, decaly")}
PLANNED = [("I-01", "Půdorys paluby v mřížce kitu 0,3 m (celá loď)"), ("I-02", "Nákladový prostor"),
           ("I-03", "Technická chodba s komponentami"), ("I-04", "Kajuta (tento list)"), ("I-05", "Kokpit"),
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
        """The kit part's paint decals as built (Kit_DecalPaint faces), identified by their UVs in the decal library:
        {element id: (centre, paper-independent quad points)} in layout metres, IDs as interior_model names them
        (the second copy of an item #2, in order along x, y, z)."""
        part = self.kit(p)
        lib = self.m.library
        sel = np.nonzero(part.mats == "Kit_DecalPaint")[0]
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
    def __init__(self, m, geo, rid, section_x):
        self.m, self.geo, self.rid, self.section_x = m, geo, rid, section_x
        self.room = m.rooms[rid]
        self.sh = ds.Sheet()
        self.d = ds.Drawer(self.sh, None)
        self.cols = colours(m)
        self.views = m.sheet_views(rid, section_x)
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
        self.decal_pos = {}
        for p in self.places:
            for ident, v in geo.kit_decals(p).items():
                self.decal_pos[ident] = v
        self.el = {e.id: e for e in m.elements}

    # ------------------------------------------------------------------ small helpers
    def mark(self, view, ident):
        self.drawn.setdefault(view, set()).add(ident)

    def lab(self, view, ident):
        self.d.labelled.setdefault(view, set()).add(ident)

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
            sh.t(X + r + 0.6, Y - r - 1.4, short + (" i" if e.extra.get("interior_only") else ""), 1.8, col, z=31.4,
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
            self.sh.t(X + r + 0.6, Y - r - 1.2, tag, 1.8, STATUS_COL[group[0].status], z=31.4, bg="white")
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
            c, pts = self.decal_pos[e.id]
            P = vw.paper(pts)
            for k in range(0, len(P), 3):
                self.sh.ax.add_patch(MplPolygon(P[k:k + 3], closed=True, fc=hexrgb(DECAL_FILL), ec="none", zorder=20))
            x0, y0 = P.min(0)
            x1, y1 = P.max(0)
            self.sh.rect(x0, y0, x1, y1, ec=DECAL_EDGE, lw=0.18, z=20.5)
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
        u0, v0 = self.x0 - 0.16, -2.55
        vw = md.View((1, 0, 0), (0, 1, 0), (0, 0, -1), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + 0.16 - u0) * s, oy + 5.1 * s)
        cut = ((0, 0, 1.2), (0, 0, -1))
        clip = ((self.x0 - 0.3, -2.7, -0.4), (self.x1 + 0.3, 2.7, 1.2))
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(sh.ax, vw, [self.hull], self.cols, clip=clip, cut=cut, window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        self.grid(vw, W)
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
                P0, P1 = vw.P((r[0], r[2], 0)), vw.P((r[1], r[3], 0))
                sh.rect(P0[0], P0[1], P1[0], P1[1], ec=STATUS_COL[e.status], lw=0.35, ls="--", z=25)
                sh.t((P0[0] + P1[0]) / 2, (P0[1] + P1[1]) / 2, "pod podlahou" if e.extra.get("below") else "",
                     1.8, STATUS_COL[e.status], ha="center", va="center", z=25.5)
            if e.cat == "door":
                self.door_plan(vw, e)
            reqs.append(self.req(view, ident, *vw.P(a), hidden=bool(e.extra.get("below"))))
        self.section_mark(vw, W)
        self.view_keys(vw)
        self.room_text(vw)
        return vw, W, reqs

    def anchor_plan(self, e):
        p = e.extra.get("placement")
        if p is not None:
            L = self.m.span(p)
            if e.cat in ("wall", "bulkhead"):
                x, y, _ = p.ue_to_layout(8.0, -L * 50.0, 0)
                return (x, y, 0)
            if e.cat == "furniture":
                dx = self.m.parts["SM_Kit_" + p.part]["dims_m"][0]
                x, y, _ = p.ue_to_layout(dx * 50.0, 0, 0)
                return (x, y, 0)
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
            self.sh.line([a, b], 0.25 if k % 4 == 0 else 0.1, GRID_COL, z=24, ls="-" if k % 4 == 0 else ":")
            if k % 4 == 0:
                self.sh.t(a[0], W[1] + 1.2, "+%s" % im.fmt(x - gx0, 1), 1.8, GRID_COL, ha="center", z=45)
            k += 1
            x = gx0 + k * g
        k = -int(half / g)
        while k * g <= half + 1e-6:
            y = k * g
            a, b = vw.P((gx0, y, 0)), vw.P((gx1, y, 0))
            self.sh.line([a, b], 0.25 if k % 4 == 0 else 0.1, GRID_COL, z=24, ls="-" if k % 4 == 0 else ":")
            if k % 4 == 0:
                self.sh.t(W[0] + 1.2, a[1] + 0.6, "%+.1f" % y if y else "osa", 1.8, GRID_COL, z=45)
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
        A, B = vw.P(a), vw.P(b)
        if st == "proposed":
            sh.line([A, B], 0.9, col, z=27)
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
        A, B = vw.P((x, -2.45, 0)), vw.P((x, 2.45, 0))
        sh.line([A, B], 0.35, INK, ls="-.", z=46)
        for P in (A, B):
            sh.ax.annotate("", xy=(P[0] + 6, P[1]), xytext=(P[0], P[1]), zorder=46, arrowprops=dict(
                arrowstyle="-|>", lw=0.35 * PT, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))
            sh.t(P[0] + 7.5, P[1] - 1.2, "R1", 3.0, weight="bold", z=46, bg="white")

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
        u0, v0 = self.x0 - 0.16, -2.55
        vw = md.View((1, 0, 0), (0, 1, 0), (0, 0, 1), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + 0.16 - u0) * s, oy + 5.1 * s)
        cut = ((0, 0, 1.95), (0, 0, 1))
        clip = ((self.x0 - 0.3, -2.7, 1.95), (self.x1 + 0.3, 2.7, 3.2))
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior], self.cols, clip=clip, cut=cut, window=W)
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
        self.room_text(vw)
        return vw, W, reqs

    def elevation(self, face, ox, oy, view):
        """One wall seen from the middle of the room: cut along the room's centre line (the floor and ceiling in
        section), the wall and everything on it beyond."""
        m, sh = self.m, self.sh
        s = S20
        cx = (self.x0 + self.x1) / 2
        hw = 1.92
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
        W = (ox, oy, ox + w * s, oy + 2.6 * s)
        _, tags = md.draw(sh.ax, vw, self.parts + self.ctx + [self.interior], self.cols, clip=clip, cut=cut, window=W)
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
                sh.t((A[0] + B[0]) / 2, yb + 3.6, ident, 2.4, STATUS_COL[e.status], ha="center", z=45)
                sh.t((A[0] + B[0]) / 2, yb + 0.6, p.part.split("_", 1)[1], 1.7, GREY, ha="center", z=45)
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
                X, Y = vw.P((x, y, 1.0))
                reqs.append(self.req(view, ident, X, Y))
        self.draw_lights(view, vw, [self.el[i] for i in sorted(self.views[view]) if self.el[i].cat == "light"], side=True)
        self.levels(vw, W)
        return vw, W, reqs

    def levels(self, vw, W):
        sh = self.sh
        for z, name in ((0.0, "±0,00"), (1.3, "+1,30 lišta"), (1.7, "+1,70 zkosení"), (2.3, "+2,30 strop")):
            _, Y = vw.P((0, 0, z))
            sh.line([(W[0] - 1.5, Y), (W[0], Y)], 0.18, INK, z=45)

    def level_labels(self, x, vw):
        sh = self.sh
        for z, name in ((0.0, "±0,00 paluba"), (1.3, "+1,30 lišta"), (1.7, "+1,70 zkosení"), (2.3, "+2,30 strop")):
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
        vw = md.View((0, -1, 0), (0, 0, 1), (1, 0, 0), ox, oy, s, -2.7, -1.2)
        W = (ox, oy, ox + 5.4 * s, oy + 4.7 * s)
        cut = ((x, 0, 0), (1, 0, 0))
        clip = ((x - 0.01, -2.8, -1.6), (self.x1 + 0.06, 2.8, 3.6))
        _, tags = md.draw(sh.ax, vw, self.parts + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(sh.ax, vw, [self.hull], self.cols, clip=((x - 0.01, -2.8, -2.0), (x + 0.01, 2.8, 4.0)), cut=cut,
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
                X, Y = vw.P(p.ue_to_layout(5.0, 0, 0.9))
                Y = vw.P((0, 0, 0.9))[1]
                X = vw.P((x, 1.93 if e.extra["side"] == "L" else -1.93, 0))[0]
            elif e.cat == "floor":
                X, Y = vw.P((x, 0.6, -0.02))
            elif e.cat == "ceiling":
                X, Y = vw.P((x, 0.6, 2.3))
            elif e.cat == "furniture":
                dims = m.parts["SM_Kit_" + p.part]["dims_m"]
                X, Y = vw.P((x, p.ue_to_layout(dims[0] * 60, 0, 0)[1], 1.5))
            elif e.extra.get("rect"):
                r = e.extra["rect"]
                X, Y = vw.P((x, (r[2] + r[3]) / 2, (e.extra["z"][0] + e.extra["z"][1]) / 2 if e.extra.get("z") else 0))
            else:
                continue
            reqs.append(self.req(view, ident, X, Y))
        # under-floor components beyond the cut (dashed)
        for e in m.in_room(self.rid, ("component",)):
            if e.extra.get("below") and e.extra.get("rect"):
                r, z = e.extra["rect"], e.extra["z"]
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
        self.zone_note = ("Řez R1: nad stropem (+2,30 … +%s) tmavá vrstva lodi nad kitem, kabelové trasy a světla stropu, "
                          "nosná konstrukce trupu; pod podlahou (±0,00 … %s) konstrukce podlahy kitu a lodi%s." % (
                              im.fmt(top), im.fmt(bot), ("; " + ", ".join(below)) if below else ""))

    def component_fit(self):
        """Every under-floor component of the room against the hull: its layout box's corners (y, z) at both ends
        of it (x) must lie inside the hull's cut there; a corner outside goes to the data check."""
        out = []
        for e in self.m.in_room(self.rid, ("component",)):
            if not (e.extra.get("below") and e.extra.get("rect") and e.extra.get("z")):
                continue
            r, z = e.extra["rect"], e.extra["z"]
            for x in (r[0] + 0.01, r[1] - 0.01):
                segs = md._slice(self.hull.verts, self.hull.tris, np.array((x, 0, 0.0)), np.array((1.0, 0, 0)))
                seg2 = [((a[1], a[2]), (b[1], b[2])) for a, b in segs if max(abs(a[1]), abs(b[1])) < 3.0]
                bad = [(y, zz) for y in (r[2], r[3]) for zz in z if not _inside_segs((y, zz), seg2)]
                if bad:
                    out.append((e.id, "%s (%s) leží zčásti mimo trup: při x %s roh %s (layout x %s, y %s, z %s)" % (
                        e.name, im.STATUS_CZ[e.status], im.fmt(x), ", ".join("y %s z %s" % (im.fmt(y), im.fmt(zz)) for y, zz in bad),
                        "%s … %s" % (im.fmt(r[0]), im.fmt(r[1])), "%s … %s" % (im.fmt(r[2]), im.fmt(r[3])),
                        "%s … %s" % (im.fmt(z[0]), im.fmt(z[1])))))
                    break
        return out

    def capsule(self, vw):
        """The walking character's capsule in the ship (APlayerCharacter::SetShipCapsule: 0.56 x 1.80 m) in the aisle
        and its eye at 1.65 m."""
        sh = self.sh
        cap_d, cap_h, eye = 0.56, 1.80, 1.65
        ya, yb = self.aisle()
        yc = (ya + yb) / 2
        A, B = vw.P((self.section_x, yc + cap_d / 2, 0)), vw.P((self.section_x, yc - cap_d / 2, cap_h))
        x0, x1 = min(A[0], B[0]), max(A[0], B[0])
        sh.ax.add_patch(FancyBboxPatch((x0, A[1]), x1 - x0, B[1] - A[1], boxstyle="round,pad=0,rounding_size=%.2f" % ((x1 - x0) / 2),
                                       fc="#DFF1E1", ec="#2E7D32", lw=0.35 * PT, zorder=47, alpha=0.9))
        _, Ye = vw.P((0, 0, eye))
        sh.line([(x0 - 2, Ye), (x1 + 2, Ye)], 0.25, "#2E7D32", z=47.5, ls="-.")
        sh.t(x1 + 2.5, Ye - 0.8, "oko 1,65", 2.0, "#2E7D32", z=47.5, bg="white")
        sh.t((x0 + x1) / 2, (A[1] + B[1]) / 2, "kapsle\n0,56 × 1,80", 2.0, "#2E7D32", ha="center", va="center", z=47.5)

    def aisle(self):
        """The clear aisle at the section: between the furniture fronts either side (or the wall faces)."""
        lo, hi = -1.9, 1.9
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
        z = 0.25
        A, B = vw.P((self.section_x, yb, z)), vw.P((self.section_x, ya, z))
        sh.ax.annotate("", xy=A, xytext=B, zorder=48, arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color="#2E7D32",
                                                                       mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t((A[0] + B[0]) / 2, A[1] + 0.8, "průchod %s (kit ≥ 0,90)" % im.fmt(yb - ya), 2.2, "#2E7D32", ha="center",
             z=48, bg="white")
        # clear height
        X = vw.P((self.section_x, ya + 0.12, 0))[0]
        P0, P1 = vw.P((0, 0, 0.0)), vw.P((0, 0, 2.3))
        sh.ax.annotate("", xy=(X, P0[1]), xytext=(X, P1[1]), zorder=48, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t(X - 0.8, (P0[1] + P1[1]) / 2, "světlá výška 2,30", 2.2, ha="right", va="center", rot=90, z=48, bg="white")
        for z, name in ((0.0, "±0,00 paluba"), (2.3, "+2,30 strop")):
            _, Y = vw.P((0, 0, z))
            sh.t(W[0] + 1.5, Y + 0.8, name, 2.0, z=48, bg="white")


def _inside_segs(p, segs):
    """Point in a closed outline given as segments (even-odd rule on a ray towards +z)."""
    y, z = p
    n = 0
    for (ay, az), (by, bz) in segs:
        if (ay <= y < by) or (by <= y < ay):
            if az + (y - ay) * (bz - az) / (by - ay) > z:
                n += 1
    return n % 2 == 1


# ---------------------------------------------------------------------- the I-04 sheet
def draw_room_sheet(m, geo, sheet, rid, section_x, dpi, out_dir):
    rs = RoomSheet(m, geo, rid, section_x)
    sh, d = rs.sh, rs.d
    ds.frame_and_zones(sh)
    W_ = sh.w
    # ------------------------------------------------ row 1: plan, ceiling plan, section
    yv = 541.0
    rs.title(34, 822, "PŮDORYS – ŘEZ VE VÝŠCE 1,20 m, MŘÍŽKA KITU 0,3 m")
    vwP, WP, reqP = rs.plan(52.0, yv)
    d.place_labels("PLAN", reqP, 34, WP[2] + 18, tiers_up=[803, 810.5], tiers_dn=[530, 522.5], split_y=vwP.P((0, 0, 0))[1],
                   bus_up=799.0, bus_dn=535.0)
    rs.title(355, 815.5 + 6.5, "STROP – POHLED ZESPODU (ZRCADLENĚ K PŮDORYSU)")
    vwC, WC, reqC = rs.rcp(372.0, yv)
    if reqC:
        d.place_labels("RCP", reqC, 355, WC[2] + 10, tiers_up=[803, 810.5], tiers_dn=[530, 522.5], split_y=vwC.P((0, 0, 0))[1],
                       bus_up=799.0, bus_dn=535.0)
    rs.title(690, 822, "ŘEZ R1 – x %s, POHLED K PŘÍDI" % im.fmt(section_x))
    vwS, WS, reqS = rs.section(698.0, 552.0)
    d.place_labels("SEC", reqS, 690, WS[2] + 12, tiers_up=[803, 810.5], tiers_dn=[541, 533.5],
                   split_y=vwS.P((0, 0, 1.0))[1], bus_up=799.0, bus_dn=546.0)
    # ------------------------------------------------ row 2: the walls developed
    rs.title(34, 505, "ROZVINUTÝ POHLED STĚN – ZE STŘEDU MÍSTNOSTI (1 levobok, 2 přední, 3 pravobok, 4 zadní)")
    x = 62.0
    ye = 335.0
    order = (("L", "EL-L", 1), ("F", "EL-F", 2), ("R", "EL-R", 3), ("A", "EL-A", 4))
    vws = []
    for face, view, num in order:
        vw, W, reqs = rs.elevation(face, x, ye, view)
        vws.append((face, view, num, vw, W, reqs))
        x = W[2] + 7.0
    for face, view, num, vw, W, reqs in vws:
        sh.ax.add_patch(Circle((W[0] + 4, W[3] + 13.5), 2.6, fc="white", ec=INK, lw=0.3 * PT, zorder=47))
        sh.t(W[0] + 4, W[3] + 13.5, str(num), 2.6, ha="center", va="center", weight="bold", z=47.5)
        sh.t(W[0] + 8, W[3] + 12.6, FACE_CZ[face], 2.6, weight="bold", z=47.5)
        d.place_labels(view, reqs, W[0], W[2], tiers_up=[W[3] + 19.5, W[3] + 26.0], tiers_dn=[W[1] - 13.0, W[1] - 19.5],
                       split_y=vw.P((0, 0, 1.15))[1], bus_up=W[3] + 16.0, bus_dn=W[1] - 9.0, size=2.3)
    rs.level_labels(30.0, vws[0][3])
    # ------------------------------------------------ legend, notes (right column)
    yl = legend(rs, 985.0, 822.0)
    key_plan(rs, 985.0, yl - 6.0)
    notes(rs, 985.0, 505.0)
    # ------------------------------------------------ row 3: schedules, data check, title block
    y = schedules(rs, 34.0, 306.0)
    light_summary(rs, 530.0, 306.0)
    check_box(rs, 800.0, 306.0)
    title_block(rs, 800.0, W_, sheet)
    return save(rs, sheet, dpi, out_dir)


def legend(rs, x, ytop):
    sh = rs.sh
    sh.t(x, ytop - 1, "LEGENDA", 3.8, weight="bold")
    y = ytop - 8
    sh.t(x, y, "Čáry", 2.8, weight="bold")
    y -= 5.0
    for lw, ls, col, txt in ((md.CUT_LW, "-", INK, "řez (plocha řezu: půdorys 1,20 m, R1, osa místnosti)"),
                             (md.OUTLINE_LW, "-", INK, "obrys za řezem"), (md.EDGE_LW, "-", INK, "hrana dílu"),
                             (0.35, "--", STATUS_COL["proposed"], "návrh (+), pod podlahou čárkovaně"),
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
        X = x + (i % 2) * 95
        Y = y - (i // 2) * 5.0
        sh.geom(box(X, Y - 1.2, X + 9, Y + 2.6), fc=hexrgb(rs.cols[k]), ec=INK, lw=0.18, z=5)
        sh.t(X + 11, Y, txt, 2.1)
        i += 1
    y -= ((i + 1) // 2) * 5.0 + 2.0
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
    sh.t(x + 10, y, "▲ v rohu = vrhá stín (hlavní světla); „i“ = svítí jen při chůzi interiérem", 2.1)
    y -= 4.4
    sh.t(x, y, "Štítek u symbolu = socket dílu; ID světla = ID dílu + / + socket (např. CAB-C-1/Down_0).", 2.1, GREY)
    y -= 6.0
    sh.t(x, y, "Ostatní", 2.8, weight="bold")
    y -= 5.4
    sh.ax.add_patch(MplPolygon([(x, y - 0.8), (x + 9, y - 0.8), (x + 9, y + 2.4), (x, y + 2.4)], closed=True,
                               fc=hexrgb(DECAL_FILL), ec=DECAL_EDGE, lw=0.2 * PT))
    sh.t(x + 11, y, "decal dílu kitu (z modelu); čárkovaně = promítaný decal lodi (D-INT)", 2.1)
    y -= 4.8
    sh.ax.annotate("", xy=(x + 9, y + 0.8), xytext=(x, y + 0.8), arrowprops=dict(arrowstyle="-|>", lw=0.3 * PT,
                                                                                  color=INK, mutation_scale=6))
    sh.t(x + 11, y, "posuvné křídlo dveří: kam se zasouvá (modře návrh)", 2.1)
    y -= 4.8
    sh.ax.add_patch(FancyBboxPatch((x + 2.5, y - 1.2), 4, 4, boxstyle="round,pad=0,rounding_size=2", fc="#DFF1E1",
                                   ec="#2E7D32", lw=0.3 * PT))
    sh.t(x + 11, y, "kapsle postavy v lodi 0,56 × 1,80 m, oko 1,65 m", 2.1)
    y -= 4.8
    for st in ("built", "proposed"):
        sh.line([(x, y + 0.8), (x + 9, y + 0.8)], 0.5, STATUS_COL[st])
        sh.t(x + 11, y, {"built": "postaveno (je v datech stavby)", "proposed": "+ návrh: v datech návrhu, zatím nepostaveno"}[st],
             2.1, STATUS_COL[st])
        y -= 4.4
    return y


def notes(rs, x, ytop):
    sh, m = rs.sh, rs.m
    sh.t(x, ytop - 3, "POZNÁMKY", 3.4, weight="bold")
    lines = [
        "1. Kreslí skript z postavené geometrie (FBX dílů kitu a lodi) a z dat; ID na výkresu = ID v datech.",
        "2. Souřadnice v metrech: x od zádi, y k levoboku, z od paluby; měřítko 1:20.",
        "3. ID dílů kitu: <místnost>-<druh>-<pořadí>: W stěna (L levobok, R pravobok, od zádi), B přepážka "
        "(A zadní, F přední), C strop, FL podlaha, U nábytek, M komponenta, DR dveře.",
        "4. Stěny: pohled ze středu místnosti, řez osou místnosti (podlaha a strop v řezu).",
        "5. Strop: pohled zespodu kreslený ve směru půdorysu (příď vpravo, levobok nahoře).",
        "6. Mřížka kitu začíná na začátku běhu stěn (x %s) a na ose lodi." % im.fmt(rs.grid_origin),
        "7. Karty špíny jsou jen v tabulce decalů (počet na díl).",
    ]
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(ds.wrap(sh, ln, 2.3, 186, 3)):
            sh.t(x + (0 if k == 0 else 4), y, part, 2.3)
            y -= 3.7
    y -= 2.5
    sh.t(x, y, "LISTY INTERIÉRU A KONCEPTŮ", 3.0, weight="bold")
    y -= 5
    for code, title in PLANNED:
        sh.t(x, y, code, 2.3, weight="bold")
        sh.t(x + 17, y, title, 2.3, INK if code in SHEETS else GREY)
        y -= 3.7
    return y


def schedules(rs, x, ytop):
    m, sh = rs.m, rs.sh
    room = rs.rid
    TS, RH = 2.5, 4.4
    els = [e for e in m.elements if (e.room == room or room in (e.extra.get("rooms") or ())) and e.status != "remove"]
    K = [e for e in els if e.kit and e.cat in ("wall", "bulkhead", "ceiling", "floor")]
    K.sort(key=lambda e: ({"wall": 0, "bulkhead": 1, "ceiling": 2, "floor": 3}[e.cat], e.id))
    cols = [("ID", 21, "left"), ("díl kitu", 41, "left"), ("umístění (m)", 52, "left", 2), ("tr.", 11, "right")]
    rows = [([e.id, e.kit, e.where, "%d" % e.extra["tris"]], STATUS_COL[e.status]) for e in K]
    y1 = ds.table(sh, x, ytop, "DÍLY KITU (stěny, přepážky, strop, podlaha)", cols, rows, size=TS, rowh=RH)
    sched = {"kit": {e.id for e in K}}
    # each kit part's purpose once
    xp = x + sum(c[1] for c in cols) + 5
    parts = {}
    for e in K:
        parts.setdefault(e.kit, []).append(e.id)
    colsP = [("díl kitu", 41, "left"), ("ks", 6, "right"), ("účel (co díl dělá)", 108, "left", 4)]
    rowsP = [([k, len(v), m.design["kit_purpose"].get(k, "")], INK) for k, v in sorted(parts.items())]
    yp = ds.table(sh, xp, ytop, "ÚČEL DÍLŮ KITU", colsP, rowsP, size=TS, rowh=RH)
    # furniture, doors, components
    F = [e for e in els if e.cat in ("furniture", "component", "object", "door")]
    F.sort(key=lambda e: ({"furniture": 0, "door": 1, "component": 2, "object": 3}[e.cat], e.id))
    colsF = [("ID", 24, "left"), ("prvek", 30, "left", 2), ("stav", 18, "left", 2), ("díl / provedení", 38, "left", 2),
             ("účel; u dveří pohyb a ovládání; u komponent výklenek, přístup a výměna", 170, "left", 5)]
    rowsF = []
    for e in F:
        if e.cat == "door":
            lf = e.extra.get("leaf") or {}
            what = "%s, šířka %s" % (lf.get("type", ""), im.fmt(e.extra["width"]))
            txt = "%s Pohyb: %s.%s" % (lf.get("purpose", ""), lf.get("motion") or "–",
                                       (" Ovládání: " + lf["operation"] + ".") if lf.get("operation") else "")
            st = {"built": "postaveno", "proposed": "otvor postaven, křídlo návrh", "none": "otvor bez křídla"}.get(lf.get("leaf"), "")
            col = STATUS_COL["proposed"] if lf.get("leaf") == "proposed" else INK
            rowsF.append(([e.id, e.name, st, what, txt], col))
        elif e.cat == "component":
            txt = "%s Výklenek: %s. Přístup: %s. Výměna: %s." % (e.purpose, e.extra.get("bay") or "–",
                                                                 e.extra.get("access") or "–", e.extra.get("replace") or "–")
            if e.extra.get("note"):
                txt += " Stav: " + e.extra["note"] + "."
            rowsF.append(([e.id, e.name, im.STATUS_CZ[e.status], "layout, pod podlahou" if e.extra.get("below") else "layout",
                           txt], STATUS_COL[e.status]))
        else:
            rowsF.append(([e.id, e.name, im.STATUS_CZ[e.status], e.kit or "loď", e.purpose], STATUS_COL[e.status]))
    y2 = ds.table(sh, x, min(y1, yp) - 4, "NÁBYTEK, DVEŘE, KOMPONENTY", colsF, rowsF, size=TS, rowh=RH)
    sched["furniture"] = {e.id for e in F}
    # lights grouped by socket and intensity
    L = [e for e in els if e.cat == "light"]
    groups = {}
    for e in L:
        sock = e.id.split("/")[-1] if "/" in e.id else e.id
        groups.setdefault((sock.split("_")[0], round(e.extra["cd"], 2), e.extra.get("role")), []).append(e)
    colsL = [("světla: ID dílu + socket", 70, "left", 3), ("ks", 7, "right"), ("typ", 31, "left"), ("barva", 26, "left"),
             ("cd", 12, "right"), ("stín", 9, "left"), ("int.", 8, "left"), ("účel", 34, "left", 2)]
    rowsL = []
    for (sock, cd, role), es in sorted(groups.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        e0 = es[0]
        hosts = sorted(e.id.split("/")[0] for e in es)
        ident = ", ".join(hosts) + (" /" + e0.id.split("/")[-1] if "/" in e0.id else "")
        rowsL.append(([ident, len(es), LIGHT_TYPE_CZ.get(e0.extra["type"], e0.extra["type"]) +
                       (" %d°" % e0.extra["cone"] if e0.extra.get("cone") else ""),
                       LIGHT_ROLE_CZ.get(role, "barva lodi"), ("%g" % cd).replace(".", ","),
                       "ano" if e0.extra.get("shadow") else "–", "ano" if e0.extra.get("interior_only") else "–",
                       SOCKET_CZ.get(sock, e0.purpose or sock)], INK))
    xl = x + 286
    y3 = ds.table(sh, xl, ytop, "SVĚTLA (%d)" % len(L), colsL, rowsL, size=TS, rowh=RH)
    sched["lights"] = {e.id for e in L}
    # decals: paint per element, grime counted per part
    D = [e for e in els if e.cat == "decal" and not e.extra.get("grime")]
    G = [e for e in els if e.cat == "decal" and e.extra.get("grime")]
    colsD = [("ID", 46, "left"), ("knihovna / textura", 33, "left"), ("velikost", 17, "left"), ("účel / text", 101, "left", 2)]

    def size(e):
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
    y4 = ds.table(sh, xl, y3 - 4, "DECALY A NÁPISY (%d + %d karet špíny)" % (len(D), len(G)), colsD, rowsD, size=TS, rowh=RH)
    sched["decals"] = {e.id for e in D} | {e.id for e in G}
    rs.schedules = sched
    return min(y2, y4)


def light_summary(rs, x, ytop):
    """The room's lights in numbers and the performance note (dossier bod 4: count per room, shadows, performance)."""
    m, sh = rs.m, rs.sh
    L = [e for e in m.elements if e.room == rs.rid and e.cat == "light"]
    r = rs.room["rect"]
    area = (r[1] - r[0]) * (r[3] - r[2])
    dens = len(L) / area
    rule = m.rules["lights"]["density_per_m2"].get({"crew": "living", "command": "cockpit", "cargo": "hold"}.get(rs.room["zone"], "living"))
    shadow = [e for e in L if e.extra.get("shadow")]
    inter = [e for e in L if e.extra.get("interior_only")]
    flight = [e for e in L if not e.extra.get("interior_only")]
    sh.t(x, ytop - 3.4, "SVĚTLA – SOUHRN A VÝKON", 3.2, weight="bold")
    lines = [
        "%d světel na %s m² podlahy = %s /m² (pravidlo kitu pro obytné místnosti %s–%s /m²)." % (
            len(L), im.fmt(area, 1), im.fmt(dens, 2), im.fmt(rule[0], 1), im.fmt(rule[1], 1)),
        "Stín vrhá %d (hlavní světla: %s); ostatní jen kontaktní stíny (kit_rooms.py)." % (
            len(shadow), ", ".join(sorted({e.id.split("/")[-1].split("_")[0] for e in shadow}))),
        "%d světel „i“ svítí jen při chůzi interiérem (MegaLights); za letu svítí %d (z nich %d se stínem)." % (
            len(inter), len(flight), len([e for e in flight if e.extra.get("shadow")])),
        "Intenzita = cd dílu × zóna kajuty 0,6 (osvětlení stěn ×0,6 navíc) × 1,1 (hra); viz tabulka.",
        "Výkon (CLAUDE.md, ship-interior): interiér je pixel-bound, stíny lokálních světel jsou drahé – každé nové světlo "
        "se měří v zabalené hře 1080p; optimalizace až na konci (autor 29. 9.).",
    ]
    if dens > rule[1]:
        lines.append("Hustota je nad pravidlem kitu: většinu tvoří lišty a osvětlení stěn (2 na modul obložení).")
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


def check_box(rs, x, ytop):
    m, sh = rs.m, rs.sh
    sh.t(x, ytop - 3.4, "KONTROLA DAT (model výkresu proti datům stavby a layoutu)", 3.2, weight="bold")
    y = ytop - 9
    room_ids = {e.id for e in m.elements if e.room == rs.rid}
    items = [(i, t) for i, t in m.checks if i in room_ids]
    extra = [(i, t) for i, t in (m.design.get("review_notes") or {}).items() if i in room_ids] + rs.component_fit()
    for e in m.in_room(rs.rid, ("component",)):
        if e.status == "proposed":
            extra.append((e.id, "%s: %s" % (e.name, e.extra.get("note"))))
    for ident, txt in items + extra:
        for k, ln in enumerate(ds.wrap(sh, "%s: %s" % (ident, txt), 2.3, 368, 3)):
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
    sh.t(x + 3, y1 - 20, SHEETS[sheet][1], 3.2)
    sh.t(x + 3, y1 - 25.5, "Kit Halcyon (paleta %s), postaveno z kitu 30. 9. 2026" % "Halcyon", 2.4)
    ya = y1 - 29
    sh.line([(x, ya), (x1, ya)], 0.25, z=50)
    cells = [("List", "%s (vzorový list)" % sheet), ("Revize", m.design["revision"]), ("Měřítko", "1:20"),
             ("Formát", "A0 na šířku"), ("Datum", m.design["date"]), ("Stav", "VZOR KE SCHVÁLENÍ STYLU")]
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
    for i, (k, v) in enumerate((("Kreslil", "Claude (skript draw_interior_sheet.py), %s" % m.design["date"]),
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
    sh.t(x + 2, yr - 8.2, "A  %s  vzorový list interiéru I-04 ke schválení stylu" % m.design["date"], 2.4)
    yd = yr - 11
    sh.line([(x, yd), (x1, yd)], 0.25, z=50)
    dg = m.digests
    sh.t(x + 2, yd - 4.2, "Data (sha1 částí pro interiér): " + " · ".join("%s %s" % (k, v) for k, v in dg.items()), 1.9)
    sh.t(x + 2, yd - 8.0, "Jeden zdroj dat: výkres obsahuje jen to, co je v datech, a data jen to, co je ve výkresu "
                          "(test Tools/Tests/test_interior_drawing.py).", 2.0)
    sh.t(x + 2, yd - 11.8, "Geometrie z FBX v Git LFS; ID, účely a návrhy v Design/%s_interior_design.json." % m.ship, 2.0)


def save(rs, sheet, dpi, out_dir):
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
        "labelled": {k: sorted(v) for k, v in rs.d.labelled.items()},
        "schedules": {k: sorted(v) for k, v in rs.schedules.items()},
        "checks": [list(c) for c in rs.checks],
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, ensure_ascii=False, indent=1)
    rs.sh.save(base + ".png", dpi, os.path.join(pdf_dir, os.path.basename(base) + ".pdf"))
    print("INTSHEET %s wrote %s.png (%d dpi) and .json, PDF in Saved/Drawings" % (sheet, os.path.relpath(base, im.ROOT), dpi))
    return base


def draw(ship="Wayfarer", dpi=200, out_dir=None, sheets=None):
    ds.setup_fonts()
    m = im.Model(ship)
    if not m.geometry_ready():
        raise SystemExit("the FBX files are Git LFS pointers here (git lfs pull): the interior sheets draw the built meshes")
    geo = Geo(m)
    out = []
    for sheet, (rid, sx) in (("I-04", ("cabin", 12.5)),):
        if sheets and sheet not in sheets:
            continue
        out.append(draw_room_sheet(m, geo, sheet, rid, sx, dpi, out_dir))
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
