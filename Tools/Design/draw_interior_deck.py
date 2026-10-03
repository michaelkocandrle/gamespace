"""The deck sheet I-01 of a ship's interior drawings (dossier bod 4): the whole main deck at 1:20 in the kit's 0.3 m
grid with the ID of every kit part, piece of furniture, door, component and object, and a longitudinal section looking
to port - drawn from the parts as they are built, in the style of the room sheet I-04 (approved 1. 10. 2026).

    python Tools/Design/draw_interior_deck.py [Wayfarer] [--dpi 200]

Uses the room sheet's machinery (Tools/Design/draw_interior_sheet.py: geometry from the FBX in Git LFS, the interior
model's IDs and statuses, the legend, the title block). Writes ArtSource/Ships/<Ship>/Design/Drawings/<Ship>_I01_deck.png
and .json (the IDs drawn and labelled per view - Tools/Tests/test_interior_drawing.py) and a vector copy in
Saved/Drawings. What the views draw is interior_model.Model.deck_views.
"""
import argparse
import json
import os
import sys

import numpy as np
from matplotlib.patches import Circle, Polygon as MplPolygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw_exterior_sheet as ds  # noqa: E402
import draw_interior_sheet as dis  # noqa: E402
import interior_model as im  # noqa: E402
import mesh_draw as md  # noqa: E402
from draw_exterior_sheet import GREY, INK, STATUS_COL  # noqa: E402

S20 = dis.S20
SHEET = "I-01"
SECTION_Y = 0.3          # the longitudinal section: through every end-wall doorway (ramp, DR-HLD-TEC 0 … 1, the others ±0.5)
PLAN_HY = 2.75           # plan window: half height; the wall ID strips run just outside it
ROOM_SHEET = {"hold": "I-02", "tech": "I-03", "cabin": "I-04", "cockpit": "I-05"}
ZONE_CZ = {"cargo": "náklad", "engineering": "technika", "crew": "posádka", "command": "velení"}
LIGHTEN = 0.4            # the deck sheet's fills toward white: the floor's joints and the grid read over them (round 1)


def func_defaults(path, name):
    """The keyword defaults of a function in a script (ast: the Blender builders import bpy)."""
    import ast
    tree = ast.parse(open(path, encoding="utf-8").read())
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name)
    args = fn.args.args[-len(fn.args.defaults):]
    return {a.arg: ast.literal_eval(d) for a, d in zip(args, fn.args.defaults)}


def stairs_data(zc):
    """The cockpit's stairs as Tools/Blender/hs_interior.stairs builds them: n risers of zc / n up to the raised floor."""
    import math
    k = func_defaults(os.path.join(im.ROOT, "Tools", "Blender", "hs_interior.py"), "stairs")
    n = int(math.ceil(zc / k["rise_max"]))
    return dict(k, n=n, rise=zc / n, x_top=k["x0"] + (n - 1) * k["tread"])


class DeckSheet(dis.RoomSheet):
    """The room sheet's helpers over the whole deck: every kit part, the ship's interior and hull."""

    def __init__(self, m, geo, section_y):
        self.m, self.geo, self.rid, self.section_x, self.section_y = m, geo, None, None, section_y
        deck = m.layout["decks"]["main"]
        self.deck = deck
        xs = [p[0] for p in deck["outline"]]
        ys = [p[1] for p in deck["outline"]]
        self.x0, self.x1, self.y0, self.y1 = min(xs), max(xs), min(ys), max(ys)
        self.room = {"name": deck.get("title", "paluba"), "rect": [self.x0, self.x1, self.y0, self.y1], "zone": "crew"}
        self.sh = ds.Sheet()
        self.d = ds.Drawer(self.sh, None)
        self.cols = {k: (None if v is None else tuple(c + (1.0 - c) * LIGHTEN for c in v))
                     for k, v in dis.colours(m).items()}
        self.views = m.deck_views(section_y)
        self.drawn = {k: set() for k in self.views}
        self.places = m.placements
        self.parts = [geo.kit(p) for p in self.places]
        self.ctx = []
        self.interior = geo.ship("_Interior")
        self.hull = geo.ship("")
        self.canopy = geo.ship("_Canopy")                 # the glass and its frame: cut with the hull
        self.el = {e.id: e for e in m.elements}
        self.ship_mats = set(np.unique(self.interior.mats).tolist())
        self.script = "draw_interior_deck.py"
        self.schedules = {}
        self.cockpit_x = min(r["rect"][0] for rid, r in m.rooms.items() if r.get("floor", 0.0) > 0.0)
        self.cockpit_floor = max(r.get("floor", 0.0) for r in m.rooms.values())
        self.stairs = stairs_data(self.cockpit_floor)
        self.cockpit_room = next(rid for rid, r in m.rooms.items() if r.get("floor", 0.0) > 0.0)

    # ------------------------------------------------------------------ plan
    def plan(self, ox, oy, view="PLAN"):
        """The deck cut 1.2 m over each room's floor (the cockpit's floor is raised: its cut is 1.2 m over it), the kit
        grid of each kit room, the wall modules' IDs in strips along the port (top) and starboard (bottom) edges."""
        m, sh = self.m, self.sh
        s = S20
        u0, v0 = self.x0 - 0.6, -PLAN_HY
        vw = md.View((1, 0, 0), (0, 1, 0), (0, 0, -1), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + 0.35 - u0) * s, oy + 2 * PLAN_HY * s)
        xc, zc = self.cockpit_x, self.cockpit_floor + 1.2
        drawn = set()
        for cut, clip in ((((0, 0, 1.2), (0, 0, -1)), ((u0, -2.8, -0.4), (xc, 2.8, 1.2))),
                          (((0, 0, zc), (0, 0, -1)), ((xc, -2.8, -0.4), (self.x1 + 0.6, 2.8, zc)))):
            _, tags = md.draw(sh.ax, vw, self.parts + [self.interior], self.cols, clip=clip, cut=cut, window=W)
            drawn |= tags
            md.draw(sh.ax, vw, [self.hull, self.canopy], self.cols, clip=clip, cut=cut, window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        self.WP = W
        self.grids(vw)
        P = vw.P((xc, 0, 0))
        sh.line([(P[0], W[1] + 1), (P[0], W[3] - 1)], 0.25, INK, ls=(0, (24, 5, 3, 5)), z=46)
        for Y0, d_ in ((W[1] + 1, 1), (W[3] - 1, -1)):
            sh.line([(P[0], Y0), (P[0], Y0 + d_ * 8)], 0.7, INK, z=46)
        sh.t(P[0] + 1.0, W[3] - 6.5, "lomený řez: od x %s kokpit ve výšce +%s (1,20 nad jeho podlahou +%s)" % (
            im.fmt(xc), im.fmt(zc), im.fmt(self.cockpit_floor)), 2.4, INK, z=46, bg="white")
        self.layout_rooms(vw)
        self.stairs_plan(vw)
        self.stand_ins(vw)
        self.breaks(vw, W)
        reqs = []
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            if e.extra.get("placement") is not None and ident not in drawn:
                continue
            self.mark(view, ident)
            if e.cat == "wall":
                self.wall_strip(vw, e)
                continue
            if e.cat == "floor":
                p = e.extra["placement"]
                X, Y = vw.P(p.ue_to_layout(m.span(p) * 50.0, 0, 0)[:2] + (0,))
                self.boxed(X, Y - 0.15 * s, ident, 2.1, STATUS_COL[e.status])
                self.boxed(X, Y - 0.15 * s - 3.0, p.part.split("_", 1)[1], 1.8, GREY)
                self.lab(view, ident)
                continue
            if e.cat in ("component", "object") and e.extra.get("rect"):
                r = e.extra["rect"]
                self.previous(vw, e, lambda rr, zz: (vw.P((rr[0], rr[2], 0)), vw.P((rr[1], rr[3], 0))))
                A, B = vw.P((r[0], r[2], 0)), vw.P((r[1], r[3], 0))
                sh.rect(A[0], A[1], B[0], B[1], ec=STATUS_COL[e.status], lw=0.35, ls="--", z=25)
            if e.cat == "door":
                self.door_plan(vw, e)
            a = self.anchor_plan(e)
            if a is None:
                continue
            text = (ident + " · " + e.kit.split("_", 1)[1]) if e.kit and e.cat in ("bulkhead", "furniture") else None
            reqs.append(self.req(view, ident, *vw.P(a), hidden=bool(e.extra.get("below")), text=text))
        for rid, r in m.rooms.items():
            pts = r["poly"]
            cx = sum(q[0] for q in pts) / len(pts)
            X, Y = vw.P((cx, 0.62, 0))
            sh.t(X, Y, "%s  %s" % (r["code"], r["name"].upper()), 3.2, weight="bold", ha="center", z=46, bg="white")
            sh.t(X, Y - 4.6, "podrobně list %s" % ROOM_SHEET.get(rid, "–"), 2.3, INK, ha="center", z=46, bg="white")
        self.section_line(vw, W)
        self.plan_chains(vw, W)
        self.cross_chains(vw)
        return vw, W, reqs

    def layout_rooms(self, vw):
        """The layout's room outlines, thin dash-dot: where the built faces differ (the data check) it shows."""
        for rid, r in self.m.rooms.items():
            pts = [vw.P((q[0], q[1], 0)) for q in r["poly"]]
            self.sh.line(pts + pts[:1], 0.18, "#7A7A7A", ls=(0, (6, 1.5, 1, 1.5)), z=26)

    def stairs_plan(self, vw):
        """The cockpit's stairs (hs_interior.stairs): risers ticked, the arrow up with the count and the rise, the
        flight's width and its ends."""
        sh, st = self.sh, self.stairs
        hw = st["half_w"]
        for i in range(st["n"]):
            x = st["x0"] + i * st["tread"]
            sh.line([vw.P((x, -hw, 0)), vw.P((x, hw, 0))], 0.2, INK, z=27)
        A, B = vw.P((st["x0"] + 0.03, -0.12, 0)), vw.P((st["x_top"] + 0.05, -0.12, 0))
        sh.ax.annotate("", xy=B, xytext=A, zorder=28, arrowprops=dict(arrowstyle="-|>", lw=0.45 * ds.PT, color=INK,
                                                                      mutation_scale=9, shrinkA=0, shrinkB=0))
        X, Y = vw.P((st["x0"] + 0.02, 0.1, 0))
        import math
        pitch = math.degrees(math.atan2(st["rise"], st["tread"]))
        sh.t(X, Y, "nahoru %d × %s, stupeň %s, sklon %d°" % (st["n"], im.fmt(st["rise"], 3), im.fmt(st["tread"]),
                                                              round(pitch)), 2.2, z=46, bg="white")
        self.chain(vw, "y", st["x0"] + 0.4, [-hw, hw])
        self.chain(vw, "x", -hw - 0.12, [st["x0"], st["x_top"] + 0.04])

    def stand_ins(self, vw):
        """The stand-in floor strips under the portals (interior.kit_modules.stand_in_floor: the kit has no 0.3 m W
        floor plate yet)."""
        for x0, x1 in self.m.mods.get("stand_in_floor") or []:
            X, Y = vw.P(((x0 + x1) / 2, -0.95, 0))
            self.sh.t(X, Y, "náhradní pás podlahy", 1.9, GREY, ha="center", rot=90, z=46, bg="white")

    def breaks(self, vw, W):
        """Break lines where the window cuts the hull (aft of the ramp's hinge, ahead of the cockpit) and where it goes
        on: the hull from x 0.0 (the engines' nozzles further aft) to the nose, drawn whole on E-01 to E-08."""
        sh = self.sh
        hx = self.hull.verts[:, 0]
        for X, txt, ha in ((W[0] + 3.0, "trup pokračuje k zádi (od x %s, E-01)" % im.fmt(float(hx.min()), 1), "left"),
                           (W[2] - 3.0, "příď pokračuje (do x %s, E-01)" % im.fmt(float(hx.max()), 1), "right")):
            Y0, Y1 = W[1] + 25, W[3] - 25
            pts = [(X, Y0), (X, (Y0 + Y1) / 2 - 3), (X - 2, (Y0 + Y1) / 2 - 1), (X + 2, (Y0 + Y1) / 2 + 1),
                   (X, (Y0 + Y1) / 2 + 3), (X, Y1)]
            sh.line(pts, 0.25, INK, z=46)
            sh.t(X + (1.5 if ha == "left" else -1.5), Y0 - 4.0, txt, 2.1, ha=ha, z=46, bg="white")

    def cross_chains(self, vw):
        """Across each kit room at its aft end: the wall faces and the doorway in the aft end wall."""
        m = self.m
        for rid, r in m.rooms.items():
            walls = m.in_room(rid, ("wall",))
            if not walls:
                continue
            fy = max(abs(e.extra["placement"].ue_to_layout(0, 0, 0)[1]) for e in walls)
            xa = min(m.x_range(e)[0] for e in walls)
            ys = [-fy, fy]
            for e in m.elements:
                if e.cat == "door" and e.extra["axis"] == "x" and abs(e.extra["at"][0] - r["rect"][0]) < 0.05:
                    ys += [e.extra["at"][1] - e.extra["width"] / 2, e.extra["at"][1] + e.extra["width"] / 2]
            self.chain(vw, "y", xa + 0.32, ys)

    def wall_strip(self, vw, e):
        """A wall module's ID in the strip along its side of the plan (port top, starboard bottom), its joints ticked
        down to the strip and a thin line to the module's face."""
        sh = self.sh
        p = e.extra["placement"]
        L = self.m.span(p)
        a, b = p.ue_to_layout(0, 0, 0), p.ue_to_layout(0, -L * 100, 0)
        sgn = 1 if e.extra["side"] == "L" else -1
        W = self.WP
        Y = W[3] + 2.6 if sgn > 0 else W[1] - 2.6
        A, B = (vw.P((a[0], 0, 0))[0], Y), (vw.P((b[0], 0, 0))[0], Y)
        for P in (A, B):
            sh.line([(P[0], P[1] - 2.4), (P[0], P[1] + 2.4)], 0.18, INK, z=45)
        F = vw.P(((a[0] + b[0]) / 2, a[1], 0))
        M = ((A[0] + B[0]) / 2, W[3] if sgn > 0 else W[1])
        sh.line([M, F], 0.1, GREY, z=45)
        self.boxed(M[0], Y - 0.9, e.id, 2.1, STATUS_COL[e.status])
        self.boxed(M[0], Y + (2.6 if sgn > 0 else -4.4), p.part.split("_", 1)[1], 1.8, GREY)
        self.lab("PLAN", e.id)

    def grids(self, vw):
        """Each kit room's 0.3 m plan grid: x from the start of the room's wall runs, y from the centre line out to the
        room's wall faces (kit_rules.json grid.plan); the origin marked."""
        g = self.m.rules["grid"]["plan"]
        self.grid_rows = []
        for rid, r in self.m.rooms.items():
            walls = [p for p in self.places if p.category == "Wall" and self.m.placement_room(p) == rid]
            if not walls:
                continue
            gx0 = min(min(p.ue_to_layout(0, 0, 0)[0], p.ue_to_layout(0, -self.m.span(p) * 100, 0)[0]) for p in walls)
            gx1 = max(max(p.ue_to_layout(0, 0, 0)[0], p.ue_to_layout(0, -self.m.span(p) * 100, 0)[0]) for p in walls)
            half = max(abs(p.ue_to_layout(0, 0, 0)[1]) for p in walls)
            k = 0
            x = gx0
            while x <= gx1 + 1e-6:
                A, B = vw.P((x, -half, 0)), vw.P((x, half, 0))
                self.sh.line([A, B], 0.35 if k % 4 == 0 else 0.08, dis.GRID_COL, z=24)
                k += 1
                x = gx0 + k * g
            k = -int(half / g + 1e-6)
            while k * g <= half + 1e-6:
                A, B = vw.P((gx0, k * g, 0)), vw.P((gx1, k * g, 0))
                self.sh.line([A, B], 0.35 if k % 4 == 0 else 0.08, dis.GRID_COL, z=24)
                k += 1
            O = vw.P((gx0, -half, 0))
            self.sh.ax.add_patch(Circle(O, 1.0, fc=dis.GRID_COL, ec="white", lw=0.15 * ds.PT, zorder=45))
            self.sh.t(O[0] + 1.4, O[1] + 1.2, "0 mřížky %s" % r["code"], 2.1, dis.GRID_COL, z=45, bg="white")
            self.grid_rows.append((rid, gx0, gx1, half, len(walls)))

    def section_line(self, vw, W):
        sh = self.sh
        y = self.section_y
        A, B = vw.P((self.x0 - 0.45, y, 0)), vw.P((self.x1 + 0.2, y, 0))
        sh.line([A, B], 0.25, INK, ls=(0, (24, 5, 3, 5)), z=46)
        for P, d_ in ((A, 1), (B, -1)):
            sh.line([P, (P[0] + d_ * 8, P[1])], 0.7, INK, z=46)
        for P in (A, B):
            sh.ax.annotate("", xy=(P[0], P[1] + 6), xytext=P, zorder=46, arrowprops=dict(
                arrowstyle="-|>", lw=0.35 * ds.PT, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0))
            sh.t(P[0] + 1.2, P[1] + 2.0, "A", 3.0, weight="bold", z=46, bg="white")

    def plan_chains(self, vw, W):
        """Over the plan: the rooms of the layout and the built end faces (bulkheads; the ramp's hinge and the cockpit's
        nose at the layout's ends), each piece dimensioned."""
        m = self.m
        rooms = sorted({v for r in m.rooms.values() for v in (r["rect"][0], r["rect"][1])})
        faces = sorted({round(p.ue_to_layout(0, 0, 0)[0], 3) for p in self.places if p.category == "Bulkhead"}
                       | {self.x0, self.x1})
        self.chain(vw, "x", PLAN_HY + 0.2, faces, label="líce přepážek (konce: závěs rampy, špička kokpitu)")
        self.chain(vw, "x", PLAN_HY + 0.42, rooms, label="místnosti (layout)")
        self.chain(vw, "x", PLAN_HY + 0.64, [self.x0, self.x1], label="paluba")
        self.faces_x = faces

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

    # ------------------------------------------------------------------ longitudinal section
    def lsec(self, ox, oy, view="LSEC"):
        """Section A at y = section_y looking to port: the kit parts, the ship's interior and the hull cut, the port
        side beyond; ceilings' IDs in a strip over the section, the port walls' under it; levels."""
        m, sh = self.m, self.sh
        s = S20
        y = self.section_y
        u0, v0 = self.x0 - 0.6, -1.0
        vw = md.View((1, 0, 0), (0, 0, 1), (0, 1, 0), ox, oy, s, u0, v0)
        W = (ox, oy, ox + (self.x1 + 0.35 - u0) * s, oy + (3.5 - v0) * s)
        cut = ((0, y, 0), (0, 1, 0))
        clip = ((u0, y - 0.01, -1.0), (self.x1 + 0.6, 2.8, 3.6))
        _, tags = md.draw(sh.ax, vw, self.parts + [self.interior], self.cols, clip=clip, cut=cut, window=W)
        md.draw(sh.ax, vw, [self.hull, self.canopy], self.cols, clip=((u0, y - 0.01, -1.2), (self.x1 + 0.6, y + 0.01, 3.8)),
                cut=cut, window=W, fill=False)
        sh.rect(*W, ec=INK, lw=0.25, z=44)
        reqs = []
        for ident in sorted(self.views[view]):
            e = self.el[ident]
            p = e.extra.get("placement")
            if p is not None and ident not in tags:
                continue
            self.mark(view, ident)
            if e.cat in ("ceiling", "wall"):
                L = m.span(p)
                xa, xb = p.ue_to_layout(0, 0, 0)[0], p.ue_to_layout(L * 100 if e.cat == "ceiling" else 0, -L * 100 if e.cat == "wall" else 0, 0)[0]
                Y = W[3] + 2.4 if e.cat == "ceiling" else W[1] - 2.6
                A, B = (vw.P((xa, 0, 0))[0], Y), (vw.P((xb, 0, 0))[0], Y)
                for P in (A, B):
                    sh.line([(P[0], P[1] - 2.4), (P[0], P[1] + 2.4)], 0.18, INK, z=45)
                self.boxed((A[0] + B[0]) / 2, Y - 0.9, ident, 2.0, STATUS_COL[e.status])
                self.boxed((A[0] + B[0]) / 2, Y + (2.6 if e.cat == "ceiling" else -4.2), p.part.split("_", 1)[1], 1.8, GREY)
                self.lab(view, ident)
                continue
            if e.cat == "bulkhead":
                X, Y = vw.P((p.ue_to_layout(0, 0, 0)[0], y, 2.15))
            elif e.cat == "door":
                X, Y = vw.P((e.extra["at"][0], y, 1.0))
            elif e.cat == "furniture":
                xr = m.x_range(e)
                X, Y = vw.P(((xr[0] + xr[1]) / 2, y, 1.1))
            elif e.extra.get("rect"):
                r, z = e.extra["rect"], e.extra.get("z") or (0.0, 0.0)
                A, B = vw.P((r[0], y, z[0])), vw.P((r[1], y, z[1]))          # the layout's z are over the main deck
                if e.cat == "component" or e.extra.get("below"):
                    sh.rect(min(A[0], B[0]), min(A[1], B[1]), max(A[0], B[0]), max(A[1], B[1]), ec=STATUS_COL[e.status],
                            lw=0.35, ls="--", z=46)
                # the leader to what is seen: a box standing on a floor at its foot (the cargo grid's rails, the seat's
                # cushion), one under the floor at its middle
                za = (z[0] + z[1]) / 2 if e.extra.get("below") else (z[0] + 0.03 if z[0] < 0.05 else z[0] + min(0.45, (z[1] - z[0]) / 2))
                X, Y = (A[0] + B[0]) / 2, vw.P((0, 0, za))[1]
            elif e.extra.get("pos"):
                X, Y = vw.P(e.extra["pos"])
            else:
                continue
            reqs.append(self.req(view, ident, X, Y, hidden=bool(e.extra.get("below"))))
        for z, name in ((0.0, "±0,00 paluba"), (2.3, "+2,30 strop v layoutu")):
            _, Y = vw.P((0, 0, z))
            sh.line([(W[0] - 1.5, Y), (W[0] + 2.0, Y)], 0.25, INK, z=45)
            sh.t(W[0] + 2.6, Y + 0.6, name, 2.0, z=46, bg="white")
        X, Y = vw.P((self.cockpit_x + 0.05, y, self.cockpit_floor))
        sh.line([(X, Y), (X + 4.0, Y)], 0.25, INK, z=45)
        sh.t(X + 4.6, Y + 0.6, "+%s podlaha kokpitu" % im.fmt(self.cockpit_floor), 2.0, z=46, bg="white")
        for rid, r in m.rooms.items():
            cx = (r["rect"][0] + r["rect"][1]) / 2
            X, Y = vw.P((cx, y, r.get("floor", 0.0) + (2.0 if not r.get("floor") else 0.75)))
            sh.t(X, Y, r["code"], 3.0, weight="bold", ha="center", z=46, bg="white")
        P = vw.P((self.x0 + 0.1, y, -0.42))
        sh.t(P[0] + 60.0, P[1], "pod podlahou: komponenty z layoutu čárkovaně, jinak jen trup", 2.1, GREY, z=46, bg="white")
        reqs += self.lsec_heights(vw, W)
        self.breaks(vw, W)
        return vw, W, reqs

    def lsec_heights(self, vw, W):
        """Section A's heights: the hull's roof and belly over the centre line at each room, the stairs' flight, the
        cockpit's clear height from the built geometry, the doorway heights the data has; the ramp lowered (the layout's
        cutaway line); the ship's dark layer over the hold's ceiling."""
        m, sh, st = self.m, self.sh, self.stairs
        y = self.section_y
        segs = md._slice(self.hull.verts, self.hull.tris, np.array((0, y, 0.0)), np.array((0, 1.0, 0)))
        csegs = md._slice(self.canopy.verts, self.canopy.tris, np.array((0, y, 0.0)), np.array((0, 1.0, 0)))
        for rid, r in m.rooms.items():                     # the hull over and under each room's middle
            cx = (r["rect"][0] + r["rect"][1]) / 2 + (0.6 if rid == "cockpit" else 0.0)
            zs = [a[2] + (b[2] - a[2]) * (cx - a[0]) / (b[0] - a[0]) for a, b in segs + csegs
                  if (a[0] - cx) * (b[0] - cx) <= 0 and abs(b[0] - a[0]) > 1e-6]
            if r["kit"] and getattr(self, "clear", {}).get(rid) is None:
                self.clear = getattr(self, "clear", {})
                self.clear[rid] = self.clear_height((r["rect"][0] + r["rect"][1]) / 2, r.get("floor", 0.0))
            ch = getattr(self, "clear", {}).get(rid) if r["kit"] else None
            if ch:                                       # the ceiling as built (the layout's clear height is 2.30)
                X, Y = vw.P((cx - 0.9, y, r.get("floor", 0.0) + ch))
                sh.ax.add_patch(MplPolygon([(X, Y), (X - 1.0, Y - 1.6), (X + 1.0, Y - 1.6)], closed=True, fc=INK,
                                           ec="none", zorder=47))
                sh.t(X + 1.6, Y - 3.4, "+%s strop" % im.fmt(r.get("floor", 0.0) + ch), 2.0, z=47, bg="white")
            for zz in (max(zs), min(zs)) if zs else ():
                X, Y = vw.P((cx, y, zz))
                sh.ax.add_patch(MplPolygon([(X, Y), (X - 1.0, Y + 1.6 * (1 if zz > 1 else -1)),
                                            (X + 1.0, Y + 1.6 * (1 if zz > 1 else -1))], closed=True, fc=INK, ec="none", zorder=47))
                sh.t(X + 1.6, Y + (1.0 if zz > 1 else -3.2), ("+" if zz > 0 else "") + im.fmt(zz), 2.0, z=47, bg="white")
        # the stairs: their rise and the cockpit's floor
        X = vw.P((st["x0"] - 0.12, y, 0))[0]
        self.dim((X, vw.P((0, 0, 0.0))[1]), (X, vw.P((0, 0, self.cockpit_floor))[1]),
                 "%d × %s = %s" % (st["n"], im.fmt(st["rise"], 3), im.fmt(self.cockpit_floor)))
        # the cockpit's clear height behind the seat (top of the stairs) from the geometry
        seat = next((e for e in m.in_room(self.cockpit_room, ("furniture", "object")) if e.extra.get("rect")
                     and abs((e.extra["rect"][2] + e.extra["rect"][3]) / 2) < 0.1), None)
        xe = seat.extra["rect"][0] if seat else st["x_top"] + 0.4          # the standing area: the stairs' top to the seat
        xs = list(np.linspace(st["x_top"] + 0.04, xe, 12))
        h = self.clear_height(None, self.cockpit_floor, xs=xs)
        self.cockpit_clear = (st["x_top"] + 0.04, xe, h, self.clear_at)
        if h:
            X = vw.P((self.clear_at[1], y, 0))[0]
            self.dim((X, vw.P((0, 0, self.cockpit_floor))[1]), (X, vw.P((0, 0, self.cockpit_floor + h))[1]),
                     "sv. výška %s (pás y ±0,30)" % im.fmt(h), col="#2E7D32")
        # doorway heights in the data (the leaves' h)
        for e in m.elements:
            lf = e.extra.get("leaf") or {}
            if e.cat == "door" and lf.get("h") and e.extra["axis"] == "x":
                X = vw.P((e.extra["at"][0] + 0.12, y, 0))[0]
                self.dim((X, vw.P((0, 0, 0))[1]), (X, vw.P((0, 0, lf["h"]))[1]), "otvor %s" % im.fmt(lf["h"]))
        # the ramp lowered (layout cutaway: the hinge at the deck's aft end and its foot on the ground)
        out = []
        for ln in (m.layout.get("cutaway") or {}).get("lines", []):
            if ln.get("kind") != "door":
                continue
            P0, P1 = (vw.P((q[0], y, q[1])) for q in ln["pts"][:2])
            k = (W[0] + 1.0 - P0[0]) / (P1[0] - P0[0]) if P1[0] < W[0] else 1.0
            P1 = (P0[0] + (P1[0] - P0[0]) * k, P0[1] + (P1[1] - P0[1]) * k)
            sh.line([P0, P1], 0.5, STATUS_COL["built"], ls=(0, (4, 1.5)), z=47)
            q = ln["pts"][1]
            out.append({"id": "#ramp", "text": "DR-RAMP dole: %s, pata x %s, z %s (za rámem)" % (
                ln.get("label", ""), im.fmt(q[0]), im.fmt(q[1])), "anchor": ((P0[0] + P1[0]) / 2,
                        (P0[1] + P1[1]) / 2), "col": GREY, "z": 0, "hidden": False})
        # the ship's dark inner layer over the hold's ceiling (hs_interior): an opening in it over x 4.4 - 5.6
        X, Y = vw.P((5.0, y, 2.55))
        out.append({"id": "#dark", "text": "otvor ve tmavé vrstvě lodi nad stropem (nad kitem, hráč ho nevidí)",
                    "anchor": (X, Y), "col": GREY, "z": Y, "hidden": False})
        return out


# ---------------------------------------------------------------------- the sheet
def draw_deck_sheet(m, geo, dpi, out_dir):
    rs = DeckSheet(m, geo, SECTION_Y)
    sh, d = rs.sh, rs.d
    ds.frame_and_zones(sh)
    rs.title(34, 822, "PŮDORYS HLAVNÍ PALUBY – ŘEZ 1,20 m NAD PODLAHOU, MŘÍŽKA KITU 0,3 m")
    vwP, WP, reqP = rs.plan(50.0, 490.0)
    d.place_labels("PLAN", reqP, 34, WP[2] + 4, tiers_up=[806, 813], tiers_dn=[474.5, 468], split_y=vwP.P((0, 0.0, 0))[1],
                   bus_up=802.0, bus_dn=480.0)
    rs.title(34, 457, "ŘEZ A – y %s, POHLED K LEVOBOKU" % im.fmt(SECTION_Y))
    vwS, WS, reqS = rs.lsec(50.0, 198.0)
    d.place_labels("LSEC", reqS, 34, WS[2] + 4, tiers_up=[437, 443.5], tiers_dn=[183.5, 177],
                   split_y=vwS.P((0, 0, 0.9))[1], bus_up=WS[3] + 8.0, bus_dn=WS[1] - 9.0)
    # right column: legend, notes, the data check
    x = 1030.0
    y = legend(rs, x, 822.0)
    y = notes(rs, x, y - 6.0)
    y = parts_table(rs, x, y - 4.0)
    # bottom: rooms and doors; components and objects; the grids; the title block
    yb = 168.0
    y1 = rooms_table(rs, 34.0, yb)
    doors_table(rs, 34.0, y1 - 4.0)
    items_table(rs, 600.0, yb)
    grid_table(rs, 800.0, yb)
    check_box(rs, x, y - 5.0)
    dis.title_block(rs, 800.0, sh.w, SHEET)
    return save(rs, dpi, out_dir)


def room_box(rs, rid):
    """A room's length, width and area: a kit room between its built faces (end walls: bulkheads, else the layout's
    end - the ramp's hinge), the ship's cockpit from the layout's outline."""
    m = rs.m
    r = m.rooms[rid]
    walls = m.in_room(rid, ("wall",))
    if not walls:
        poly = r["poly"]
        area = abs(sum(a_[0] * b_[1] - b_[0] * a_[1] for a_, b_ in zip(poly, poly[1:] + poly[:1]))) / 2
        ys = [q[1] for q in poly]
        return r["rect"][1] - r["rect"][0], max(ys) - min(ys), area, "obrys layoutu"
    fy = max(abs(e.extra["placement"].ue_to_layout(0, 0, 0)[1]) for e in walls)
    ends = sorted(e.extra["placement"].ue_to_layout(0, 0, 0)[0] for e in m.in_room(rid, ("bulkhead",)))
    x0 = ends[0] if len(ends) == 2 else r["rect"][0]
    x1 = ends[-1] if ends and ends[-1] > (r["rect"][0] + r["rect"][1]) / 2 else r["rect"][1]
    return x1 - x0, 2 * fy, (x1 - x0) * 2 * fy, "mezi líci"


def purpose_heights(r):
    """The heights a raised room's purpose text gives ("(0,35 m)") that differ from its built floor."""
    import re
    floor = r.get("floor", 0.0)
    if not floor:
        return []
    said = [float(v.replace(",", ".")) for v in re.findall(r"(\d+,\d+) m", r.get("purpose", ""))]
    return said if said and all(abs(v - floor) > 0.01 for v in said) else []


def rooms_table(rs, x, ytop):
    m = rs.m
    cols = [("kód", 11, "left"), ("místnost", 29, "left"), ("zóna", 17, "left"), ("x od … do (layout)", 28, "left"),
            ("délka", 11, "right"), ("šířka", 11, "right"), ("plocha m²", 15, "right"), ("základ", 19, "left"),
            ("sv. výška (geometrie)", 31, "right", 2), ("stavba", 22, "left"),
            ("díly kitu: stěny / přepážky / strop / podlaha / nábytek", 52, "left", 2), ("účel (layout)", 302, "left", 2)]
    rows = []
    rs.clear = getattr(rs, "clear", {})
    flags = {rid for rid, r in m.rooms.items() if purpose_heights(r)}
    for rid, r in m.rooms.items():
        L, Wd, A, basis = room_box(rs, rid)
        floor = r.get("floor", 0.0)
        if rid == getattr(rs, "cockpit_room", None) and getattr(rs, "cockpit_clear", None):
            xa, xb, h, at = rs.cockpit_clear
            ht = "%s nad +%s (x %s … %s, y ±0,30; nejníž x %s: žebro kabiny)" % (im.fmt(h), im.fmt(floor), im.fmt(xa),
                                                                                im.fmt(xb), im.fmt(at[1]))
        else:
            h = rs.clear_height((r["rect"][0] + r["rect"][1]) / 2, floor)
            ht = im.fmt(h) if h else "–"
        rs.clear[rid] = h
        cnt = [len(m.in_room(rid, (c,))) for c in ("wall", "bulkhead", "ceiling", "floor")]
        cnt.append(len([e for e in m.in_room(rid, ("furniture",)) if e.kit]))
        rows.append(([r["code"], r["name"], ZONE_CZ.get(r.get("zone"), r.get("zone", "")),
                      "%s … %s" % (im.fmt(r["rect"][0]), im.fmt(r["rect"][1])), im.fmt(L), im.fmt(Wd), im.fmt(A, 1), basis,
                      ht, ("z kitu" + ("" if cnt[3] else ", podlaha lodi")) if r["kit"] else "trup lodi",
                      " / ".join(str(c) for c in cnt) if r["kit"] else "–",
                      r.get("purpose", "") + (" [k opravě: výška, viz kontrola dat]" if rid in flags else "")],
                     INK))
    rs.schedules["rooms"] = set(m.rooms)
    return ds.table(rs.sh, x, ytop, "MÍSTNOSTI", cols, rows, size=2.4, rowh=4.3)


def doors_table(rs, x, ytop):
    m = rs.m
    D = sorted((e for e in m.elements if e.cat == "door"), key=lambda e: e.extra["at"][0])
    cols = [("ID", 22, "left"), ("dveře", 40, "left"), ("mezi", 22, "left"), ("poloha (m)", 40, "left"), ("šířka", 11, "right"),
            ("provedení", 33, "left", 2), ("stav", 34, "left", 2), ("pohyb", 154, "left", 2)]
    rows = []
    for e in D:
        lf = e.extra.get("leaf") or {}
        st = {"built": "postaveno", "proposed": "otvor postaven, křídlo návrh", "none": "otvor bez křídla"}.get(lf.get("leaf"), "")
        rows.append(([e.id, e.name, " / ".join(m.room_code(r) for r in e.extra.get("rooms") or ()),
                      "x %s, y %s, osa %s" % (im.fmt(e.extra["at"][0]), im.fmt(e.extra["at"][1]), e.extra["axis"]),
                      im.fmt(e.extra["width"]), lf.get("type", ""), st, lf.get("motion", "")],
                     STATUS_COL["proposed"] if lf.get("leaf") == "proposed" else INK))
    rs.schedules["doors"] = {e.id for e in D}
    return ds.table(rs.sh, x, ytop, "DVEŘE (layout, křídla z dat návrhu)", cols, rows, size=2.4, rowh=4.3)


def items_table(rs, x, ytop):
    """The furniture, components and objects the plan labels: what each ID is and the sheet that details it."""
    m = rs.m
    ids = sorted((i for i in rs.views["PLAN"] if rs.el[i].cat in ("furniture", "component", "object")),
                 key=lambda i: (list(m.rooms).index(rs.el[i].room), {"furniture": 0, "component": 1, "object": 2}[rs.el[i].cat], i))
    cols = [("ID", 30, "left"), ("prvek", 52, "left", 2), ("stav", 14, "left"), ("list", 10, "left")]
    rows = [([i, rs.el[i].name + (" (pod podlahou)" if rs.el[i].extra.get("below") else ""), im.STATUS_CZ[rs.el[i].status],
              ROOM_SHEET.get(rs.el[i].room, "")], STATUS_COL[rs.el[i].status]) for i in ids]
    rs.schedules["items"] = set(ids)
    return ds.table(rs.sh, x, ytop, "NÁBYTEK, KOMPONENTY, OBJEKTY", cols, rows, size=2.3, rowh=4.0)


def grid_table(rs, x, ytop):
    """Where each kit room's grid starts and how it sits against the hold's (the first room's): the deck has no common
    grid - every room's runs start at its own aft face."""
    m = rs.m
    g = m.rules["grid"]["plan"]
    base = rs.grid_rows[0][1] if rs.grid_rows else 0.0
    cols = [("místnost", 17, "left"), ("0 mřížky x", 19, "right"), ("běhy x", 26, "left"), ("líc stěn y", 17, "right"),
            ("moduly", 13, "right"), ("proti HLD", 34, "left")]
    rows = []
    rs.grid_offsets = []
    for rid, gx0, gx1, half, n in sorted(rs.grid_rows, key=lambda r: r[1]):
        off = (gx0 - base) % g
        off = min(off, g - off)
        rs.grid_offsets.append((rid, gx0, off))
        rows.append(([m.room_code(rid), im.fmt(gx0), "%s … %s" % (im.fmt(gx0), im.fmt(gx1)), "±" + im.fmt(half), str(n),
                      "na mřížce" if off < 0.002 else "posun %d mm" % round(off * 1000)], INK))
    return ds.table(rs.sh, x, ytop, "MŘÍŽKA KITU 0,3 m PO MÍSTNOSTECH", cols, rows, size=2.3, rowh=4.0)


def legend(rs, x, ytop):
    """The deck sheet's legend: its lines and symbols only (no lights or decals here, fills are the materials' tints as
    on the room sheets)."""
    sh = rs.sh
    sh.t(x, ytop - 1, "LEGENDA", 3.8, weight="bold")
    y = ytop - 8
    items = [((md.CUT_LW, "-", INK), "řez (půdorys 1,20 m nad podlahou, řez A)"),
             ((md.OUTLINE_LW, "-", INK), "obrys a hrany dílů za řezem"),
             ((0.35, "--", INK), "obálka objektu / komponenty z layoutu (postaveno)"),
             ((0.35, "--", STATUS_COL["proposed"]), "+ návrh (data návrhu, nepostaveno)"),
             ((0.4, "--", STATUS_COL["remove"]), "dřívější poloha (přesun, šipka k nové)"),
             ((0.18, (0, (6, 1.5, 1, 1.5)), "#7A7A7A"), "obrys místnosti v layoutu"),
             ((0.35, ":", dis.GRID_COL), "mřížka kitu 0,3 m (plná po 1,2 m)"),
             ((0.25, (0, (24, 5, 3, 5)), INK), "rovina řezu A, lom řezu u kokpitu (silné konce)"),
             ((0.3, "-", "#2E7D32"), "zelená kóta: světlá výška, průchod (kapsle postavy)")]
    for (lw, ls, col), txt in items:
        sh.line([(x, y + 0.8), (x + 12, y + 0.8)], lw, col, ls=ls)
        sh.t(x + 15, y, txt, 2.2)
        y -= 4.3
    sh.t(x, y, "„pod podlahou“ = pod palubou; odkaz tečkovaně", 2.2, GREY)
    y -= 4.3
    sh.ax.annotate("", xy=(x + 12, y + 0.8), xytext=(x, y + 0.8), arrowprops=dict(arrowstyle="-|>", lw=0.3 * ds.PT,
                                                                                   color=INK, mutation_scale=6))
    sh.t(x + 15, y, "posuvné křídlo: kam se zasouvá; schody: nahoru", 2.2)
    y -= 4.3
    sh.t(x, y, "výplň = odstín materiálu dílu (barvy: listy místností)", 2.2, GREY)
    return y - 2.0


def notes(rs, x, ytop):
    sh = rs.sh
    sh.t(x, ytop - 3, "POZNÁMKY", 3.4, weight="bold")
    lines = [
        "1. Kreslí skript z postavené geometrie (FBX dílů kitu a lodi) a z dat; ID na výkresu = ID v datech.",
        "2. Souřadnice v metrech: x od zádi (závěs rampy x %s), y k levoboku, z od paluby; měřítko 1:20." % im.fmt(rs.x0),
        "3. Klíč ID: místnost (HLD náklad, TEC chodba, CAB kajuta, CPT kokpit) - druh - pořadí: W stěna (L levobok, "
        "R pravobok, od zádi), B přepážka (A zadní, F přední), C strop, FL podlaha, U nábytek, M komponenta, O objekt "
        "lodi; DR dveře. Pod ID šedě díl kitu.",
        "3a. ID stěn jsou v pásech podél půdorysu (levobok nahoře, pravobok dole), stropů a stěn levoboku nad a pod "
        "řezem A; ostatní na odkazech.",
        "4. Mřížka kitu má v každé místnosti vlastní počátek (začátek běhu stěn), viz tabulka mřížky.",
        "5. Světla a decaly jsou na listech místností a na I-07, I-08.",
        "6. Kokpit staví loď (hs_cockpit), ne kit: jen geometrie, nábytek a komponenty z layoutu.",
    ]
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(ds.wrap(sh, ln, 2.2, 140, 4)):
            sh.t(x + (0 if k == 0 else 3), y, part, 2.2)
            y -= 3.5
    y -= 2.5
    sh.t(x, y, "LISTY INTERIÉRU A KONCEPTŮ", 3.0, weight="bold")
    sh.t(x + 75, y, "šedě = zatím nenakresleno", 2.0, GREY)
    y -= 5
    for code, title in dis.PLANNED:
        for k, part in enumerate(ds.wrap(sh, title.replace(" (tento list)", ""), 2.2, 120, 2)):
            if k == 0:
                sh.t(x, y, code, 2.2, weight="bold" if code == SHEET else "normal")
            sh.t(x + 20, y, part, 2.2, INK if code in dis.SHEETS else GREY)
            y -= 3.5
    return y


def parts_table(rs, x, ytop):
    """Each kit part used on the deck once: how many, in which rooms, its Czech purpose (design data kit_purpose)."""
    m = rs.m
    parts = {}
    for e in m.elements:
        if e.kit and e.cat in ("wall", "bulkhead", "ceiling", "floor", "furniture"):
            parts.setdefault(e.kit, []).append(e)
    cols = [("díl kitu", 34, "left"), ("ks", 5, "right"), ("ID", 32, "left", 4), ("účel", 74, "left", 5)]
    rows = [([k, len(v), ", ".join(sorted(e.id for e in v)),
              m.design["kit_purpose"].get(k) or (v[0].purpose if v[0].cat == "furniture" else "")], INK)
            for k, v in sorted(parts.items())]
    rs.schedules["kit_parts"] = {e.id for v in parts.values() for e in v}
    return ds.table(rs.sh, x, ytop, "DÍLY KITU (ID dílů v pásech a u desek)", cols, rows, size=2.1, rowh=3.8)


# the data check's verdicts: intent, fix (where) or the author's decision
VERDICT = {"intent": "záměr", "fix": "k opravě", "author": "čeká na autora"}


def check_box(rs, x, ytop, width=140.0):
    """The deck's data check: the rooms of the layout against the built faces, the grids against each other, the model's
    checks of every room (furniture against the layout) and the under-floor components against the hull."""
    m, sh = rs.m, rs.sh
    sh.t(x, ytop - 3.4, "KONTROLA DAT", 3.2, weight="bold")
    import re
    out = []
    for rid, r in m.rooms.items():
        walls = m.in_room(rid, ("wall",))
        if walls:
            fy = max(abs(e.extra["placement"].ue_to_layout(0, 0, 0)[1]) for e in walls)
            if abs(fy - r["rect"][3]) > 0.015:
                bays = [e for e in m.in_room(rid, ("component",)) if str(e.src).endswith("SOCKET_Component")]
                out.append((m.room_code(rid), "%s: líce stěn y ±%s, obdélník layoutu ±%s (%+d mm na stranu)%s" % (
                    r["name"], im.fmt(fy), im.fmt(r["rect"][3]), round((fy - r["rect"][3]) * 1000),
                    " – za stěnami výklenky komponent" if bays else " – layout podle kitu (hlavní session: otisky E-01 až E-08)"),
                    "intent" if bays else "fix"))
        floor = r.get("floor", 0.0)
        said = purpose_heights(r)
        if said:
            if True:
                out.append((m.room_code(rid), "účel v layoutu uvádí %s m, postavená podlaha je +%s (hs cockpit._raise) – "
                                              "opravit text v layoutu (hlavní session)" % (
                                                  ", ".join(im.fmt(v) for v in said), im.fmt(floor)), "fix"))
    faces = rs.faces_x
    for a, b in zip(faces, faces[1:]):
        if 0.015 < b - a < 0.6:
            out.append(("#", "mezi líci přepážek x %s a %s je %d mm (portál, tloušťky přepážek)" % (im.fmt(a), im.fmt(b),
                                                                                                  round((b - a) * 1000)), "intent"))
    for rid, gx0, off in rs.grid_offsets:
        if off >= 0.002:
            out.append((m.room_code(rid), "mřížka %s (od x %s) je proti mřížce nákladu posunutá o %d mm (každý běh stěn "
                                          "začíná u svého líce)" % (m.room_code(rid), im.fmt(gx0), round(off * 1000)), "intent"))
    out += [(i, t, "fix" if "layout opravit" in t else "author") for i, t in m.checks]
    for rid in m.rooms:
        rs.rid = rid
        out += [(i, t, "author") for i, t in rs.component_fit()]
    rs.rid = None
    y = ytop - 9
    for ident, txt, verdict in out:
        head = "[%s] " % VERDICT[verdict] + ("" if ident == "#" else ident + ": ")
        for k, ln in enumerate(ds.wrap(sh, head + txt, 2.2, width, 6)):
            sh.t(x + (0 if k == 0 else 3), y, ("• " if k == 0 else "") + ln, 2.2,
                 STATUS_COL["remove"] if verdict == "fix" and k == 0 else INK)
            y -= 3.4
    rs.checks = [(i, t) for i, t, _ in out]
    return y


def save(rs, dpi, out_dir):
    m = rs.m
    out_dir = out_dir or os.path.join(im.ROOT, "ArtSource", "Ships", m.ship, "Design", "Drawings")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "%s_%s" % (m.ship, dis.SHEETS[SHEET][0]))
    pdf_dir = os.path.join(im.ROOT, "Saved", "Drawings")
    os.makedirs(pdf_dir, exist_ok=True)
    side = {
        "_comment": "Written by Tools/Design/draw_interior_deck.py: the IDs this sheet draws and labels per view and lists "
                    "per schedule, with the digests of the data it was drawn from (Tools/Tests/test_interior_drawing.py).",
        "sheet": SHEET, "ship": m.ship, "room": None, "deck": "main", "section_y": rs.section_y, "digests": m.digests,
        "geometry": m.geometry_digests(),
        "drawn": {k: sorted(v) for k, v in rs.drawn.items()},
        "labelled": {k: sorted(i for i in v if not i.startswith("#")) for k, v in rs.d.labelled.items()},
        "schedules": {k: sorted(v) for k, v in rs.schedules.items()},
        "checks": [list(c) for c in rs.checks],
    }
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, ensure_ascii=False, indent=1)
    rs.sh.save(base + ".png", dpi, os.path.join(pdf_dir, os.path.basename(base) + ".pdf"))
    print("INTSHEET %s wrote %s.png (%d dpi) and .json, PDF in Saved/Drawings" % (SHEET, os.path.relpath(base, im.ROOT), dpi))
    return base


def draw(ship="Wayfarer", dpi=200, out_dir=None):
    ds.setup_fonts()
    m = im.Model(ship)
    if not m.geometry_ready():
        raise SystemExit("the FBX files are Git LFS pointers here (git lfs pull): the interior sheets draw the built meshes")
    rs_geo = dis.Geo(m)
    return draw_deck_sheet(m, rs_geo, dpi, out_dir)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ship", nargs="?", default="Wayfarer")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args(argv)
    draw(a.ship, a.dpi)


if __name__ == "__main__":
    main()
