"""Exterior design drawings of a ship (dossier bod 3), drawn from the exterior model (Tools/Design/exterior_model.py:
the same data the ship is built from; author 1. 10. 2026). Sheet E-01: starboard side on A0 at 1:30 -
view A plates and material zones, view B functional parts, lights and decals, detail A (pod with nozzle) at 1:20,
legend, schedules, changes and the title block.

    python Tools/Design/draw_exterior_sheet.py [Wayfarer] [--dpi 200]

Writes ArtSource/Ships/<Ship>/Design/Drawings/<Ship>_E01_starboard.png and .json (the IDs drawn and labelled per
view and schedule, with the data digests; Tools/Tests/test_exterior_drawing.py compares it with the model) and a
vector copy Saved/Drawings/<Ship>_E01_starboard.pdf. Sheets E-03 to E-07 (other views, details): draw_exterior_views.py.
Status colours: built black, proposed blue (+), change blue (Δ, the built position red dashed), remove red (×).
"""
import argparse
import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.patches import Circle, PathPatch, Polygon as MplPolygon  # noqa: E402
from matplotlib.path import Path  # noqa: E402
from matplotlib.patheffects import withStroke  # noqa: E402
from matplotlib.textpath import TextToPath  # noqa: E402
from shapely.affinity import affine_transform  # noqa: E402
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box  # noqa: E402
from shapely.ops import polylabel  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import exterior_model as em  # noqa: E402

PT = 72.0 / 25.4                       # points per millimetre
TEXT2PATH = TextToPath()
INK = "#1B1B1B"
GREY = "#8C8C8C"
LIGHT = "#C9C9C9"
STATUS_COL = {"built": INK, "proposed": "#1565C0", "change": "#1565C0", "remove": "#C62828"}
STATUS_MARK = {"built": "", "proposed": "+", "change": "Δ", "remove": "×"}
STATUS_CZ = {"built": "postaveno", "proposed": "návrh", "change": "změna", "remove": "odstranit"}
SOLID_CZ = {"hull": "trup", "pod": "gondola", "fin": "ploutev", "wing": "křídlo", "gun": "zbraň",
            "missile_rack": "raketnice", "gear_main": "podvozek", "gear_nose": "podvozek"}
SOLID_ACC = {"hull": "trup", "pod": "gondolu", "fin": "ploutev", "wing": "křídlo", "gun": "zbraň",
             "missile_rack": "raketnici", "gear_main": "podvozek", "gear_nose": "podvozek"}
FONT = "Bahnschrift"
V1_CATS = em.SHEET_E01["A"]
V2_CATS = em.SHEET_E01["B"]
SCALE = 1000.0 / 30.0                 # 1:30, mm on paper per metre
DSCALE = 1000.0 / 20.0                # detail 1:20
DETAIL_WIN = (-0.75, -0.05, 6.15, 3.55)
LABEL_MM = 2.5                         # leader labels
PANEL_MM = 2.4                         # plate IDs inside the plates
TABLE_MM = 2.5                         # schedules (ISO 3098 minimum, critic round 2)
TITLE_MM = 5.0


def setup_fonts():
    for f in ("bahnschrift.ttf", "segoeui.ttf", "seguisym.ttf"):
        p = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", f)
        if os.path.exists(p):
            font_manager.fontManager.addfont(p)
    matplotlib.rcParams.update({"font.family": [FONT, "Segoe UI", "Segoe UI Symbol"], "lines.scale_dashes": False, "hatch.linewidth": 0.35,
                                "pdf.fonttype": 42, "svg.fonttype": "none", "path.simplify": False})


def lum(hexcol):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def to_path(g):
    verts, codes = [], []
    polys = [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior] + list(p.interiors):
            cs = list(ring.coords)
            if len(cs) < 3:
                continue
            verts += cs
            codes += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
    return Path(verts, codes) if verts else None


def lines_of(g):
    if g.is_empty:
        return []
    if isinstance(g, LineString):
        return [list(g.coords)]
    if isinstance(g, MultiLineString):
        return [list(x.coords) for x in g.geoms]
    if isinstance(g, Polygon):
        return [list(g.exterior.coords)] + [list(i.coords) for i in g.interiors]
    out = []
    for x in getattr(g, "geoms", []):
        out += lines_of(x)
    return out


class Sheet:
    def __init__(self, w=1189.0, h=841.0):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w / 25.4, h / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(0, h)
        self.ax.set_aspect("equal")
        self.ax.axis("off")
        self.fig.patch.set_facecolor("white")
        self.boxes = []                         # placed label boxes (x0, y0, x1, y1)

    _props = {}

    def width(self, s, size, weight="normal"):
        """Text width in mm from the font's metrics (FreeType; a TextPath's extents took minutes for a sheet)."""
        prop = self._props.get(size)
        if prop is None:
            prop = self._props[size] = FontProperties(family=[FONT, "Segoe UI", "Segoe UI Symbol"], size=size * PT)
        w, _, _ = TEXT2PATH.get_text_width_height_descent(s, prop, ismath=False)
        return w / PT

    def t(self, x, y, s, size=2.5, color=INK, ha="left", va="baseline", weight="normal", rot=0, z=30, bg=None):
        """Text; "bold" strokes the outline (Bahnschrift is one variable font file, matplotlib has no bold of it)."""
        kw = dict(fontsize=size * PT, color=color, ha=ha, va=va, rotation=rot, zorder=z)
        if bg:
            kw["bbox"] = dict(boxstyle="square,pad=0.12", fc=bg, ec="none")
        if weight == "bold":
            kw["path_effects"] = [withStroke(linewidth=size * 0.09 * PT, foreground=color)]
        return self.ax.text(x, y, s, **kw)

    def line(self, pts, lw=0.25, color=INK, ls="-", z=10, cap="butt"):
        xs, ys = zip(*pts)
        dashes = {"--": (0, (4.0, 2.2)), "-.": (0, (6.0, 1.6, 1.2, 1.6)), ":": (0, (1.2, 1.4))}.get(ls)
        kw = dict(lw=lw * PT, color=color, zorder=z, solid_capstyle=cap, dash_capstyle=cap)
        if dashes:
            kw["linestyle"] = dashes
        self.ax.plot(xs, ys, **kw)

    def geom(self, g, fc="none", ec=INK, lw=0.25, hatch=None, hatch_col=None, ls="-", z=5, alpha=1.0):
        if g is None or g.is_empty:
            return
        if isinstance(g, (LineString, MultiLineString)):
            for ln in lines_of(g):
                self.line(ln, lw, ec, ls, z)
            return
        path = to_path(g)
        if path is None:
            return
        if fc != "none" or hatch:
            self.ax.add_patch(PathPatch(path, fc=fc, ec=hatch_col or ec, lw=0, hatch=hatch or None, zorder=z, alpha=alpha))
        if ec != "none" and lw > 0:
            dashes = {"--": (0, (4.0, 2.2)), "-.": (0, (6.0, 1.6, 1.2, 1.6)), ":": (0, (1.2, 1.4))}.get(ls)
            self.ax.add_patch(PathPatch(path, fc="none", ec=ec, lw=lw * PT, zorder=z + 0.1,
                                        linestyle=dashes if dashes else "solid", joinstyle="miter"))

    def rect(self, x0, y0, x1, y1, **kw):
        self.geom(box(x0, y0, x1, y1), **kw)

    def save(self, png, dpi, pdf=None):
        self.fig.savefig(png, dpi=dpi, facecolor="white")
        if pdf:
            self.fig.savefig(pdf, facecolor="white")
        plt.close(self.fig)


class Frame:
    """Model metres (x, z) to paper millimetres; an optional window (model coordinates) clips everything. flip
    mirrors the view left-right (the port side drawn from the starboard coordinates, exterior_views)."""

    def __init__(self, ox, oy, s, win=None, flip=False):
        self.ox, self.oy, self.s, self.win, self.flip = ox, oy, s, win, flip
        self.winbox = box(*win) if win else None
        self.sx = -s if flip else s

    def P(self, x, z):
        return (self.ox + x * self.sx, self.oy + z * self.s)

    def vec(self, u, w):
        """A direction (reading up, a light's aim) on paper."""
        return (-u if self.flip else u, w)

    def g(self, geom):
        if geom is None or geom.is_empty:
            return geom
        if self.winbox is not None:
            geom = geom.intersection(self.winbox)
        return affine_transform(geom, [self.sx, 0, 0, self.s, self.ox, self.oy])

    def inside(self, x, z):
        return self.winbox is None or self.winbox.contains(Point(x, z))


class Drawer:
    def __init__(self, sheet, model):
        self.sh, self.m = sheet, model
        self.drawn = {}
        self.labelled = {}
        self.roof_side = {}

    # ------------------------------------------------------------------ helpers
    def matstyle(self, mid):
        d = self.m.materials[mid]["draw"]
        fill = d["fill"]
        hc = "#5A5A5A" if lum(fill) > 0.45 else "#D0D0D0"
        return fill, d.get("hatch") or None, hc

    def fillmat(self, fr, geom, mid, z=3, ec="none", lw=0.0, ls="-"):
        fill, hatch, hc = self.matstyle(mid)
        self.sh.geom(fr.g(geom), fc=fill, ec=ec, lw=lw, hatch=hatch, hatch_col=hc, z=z, ls=ls)

    def vis(self, solid):
        return self.m.solids[solid]["visible"]

    def mark(self, view, el):
        self.drawn.setdefault(view, set()).add(el.id)

    # ------------------------------------------------------------------ view A: plates and materials
    def view_materials(self, fr, view, label_ids=None, label_pod_plates=False):
        m = self.m
        sh = self.sh
        reqs = []
        # hull skin and what is painted on it
        hull_vis = self.vis("hull")
        skin = m.by_id["P-HULL"]
        self.fillmat(fr, hull_vis, skin.material, z=2)
        self.mark(view, skin)
        for e in m.elements:
            if not e.sb or e.sb["solid"] != "hull" or e.cat not in ("zone", "recess", "plate") or e.status == "remove":
                continue
            zo = 5.5 if e.extra.get("on_panels") else (3 if e.cat != "plate" else 4)
            self.fillmat(fr, e.sb["shape"].intersection(hull_vis), e.material, z=zo,
                         ec=STATUS_COL[e.status] if e.cat == "plate" else "none", lw=0.25)
            self.mark(view, e)
        self.fillmat(fr, m.canopy.intersection(hull_vis), "MZ-GLASS", z=3)
        for e in m.elements:
            if e.sb and e.cat == "zone" and e.extra.get("ghost") is not None:
                self.sh.geom(fr.g(e.extra["ghost"]), ec=STATUS_COL["remove"], lw=0.35, ls="--", z=8.5)
                g, n = e.extra["ghost"].bounds, e.sb["shape"].bounds
                if fr.inside(g[0], g[1]):
                    A = fr.P(g[0], (g[1] + g[3]) / 2)
                    B = fr.P(n[0], (n[1] + n[3]) / 2)
                    self.sh.ax.annotate("", xy=B, xytext=A, zorder=12, arrowprops=dict(
                        arrowstyle="-|>", lw=0.25 * PT, color=STATUS_COL["change"], mutation_scale=5,
                        linestyle=(0, (2.5, 1.5)), shrinkA=0, shrinkB=0))
        # grille bays read as dark recesses (labelled in view B)
        for e in m.elements:
            if e.sb and e.cat == "functional" and e.data.get("kind") == "grille":
                self.fillmat(fr, e.sb["shape"].intersection(hull_vis), "MZ-DARK", z=3)
        # panels with bolts (heavy plates), then the frame
        for e in m.elements:
            if e.cat != "panel" or not e.sb:
                continue
            shp = e.sb["shape"].intersection(hull_vis)
            self.mark(view, e)
            if shp.is_empty:
                continue
            self.fillmat(fr, shp, e.material, z=5, ec=STATUS_COL[e.status], lw=0.3)
            kit = m.kit[e.kit]
            if "bolt_pitch" in kit:
                self.bolts(fr, e.sb["shape"], shp, kit)
        for e in m.elements:
            if e.cat == "frame" and e.sb:
                shp = e.sb["shape"].intersection(hull_vis)
                fill, hatch, hc = self.matstyle(e.material)
                sh.geom(fr.g(shp), fc="#5E646B", ec=STATUS_COL[e.status], lw=0.18, z=6)
                self.mark(view, e)
        # built plates that the panels replace
        for e in m.elements:
            if e.sb and e.cat == "plate" and e.status == "remove" and e.sb["solid"] == "hull":
                sh.geom(fr.g(e.sb["shape"]), ec=STATUS_COL["remove"], lw=0.3, ls="--", z=8)
                self.cross(fr, e.sb["shape"])
                self.mark(view, e)
        # pod
        pod_vis = self.vis("pod")
        self.fillmat(fr, pod_vis, m.by_id["P-POD"].material, z=2)
        self.mark(view, m.by_id["P-POD"])
        for e in m.elements:
            if not e.sb or e.sb["solid"] != "pod":
                continue
            if e.cat == "section":
                shp = e.sb["shape"].intersection(pod_vis)
                if e.data["kind"] == "ring":
                    self.fillmat(fr, shp, e.material, z=3)
                for ln in e.extra.get("seams", []):
                    sh.geom(fr.g(ln.intersection(pod_vis)), ec="#6B6B6B", lw=0.18, z=4)
                self.mark(view, e)
            elif e.cat == "plate":
                self.fillmat(fr, e.sb["shape"].intersection(pod_vis), e.material, z=5, ec=STATUS_COL[e.status], lw=0.3)
                self.mark(view, e)
            elif e.id in ("F-POD-EXHAUST", "F-POD-INTAKE", "F-POD-BAY"):
                self.fillmat(fr, e.sb["shape"].intersection(pod_vis), e.material, z=4)
        # fin: box, leading edge, rudder
        fin = m.by_id["F-FIN"]
        fin_vis = self.vis("fin")
        self.fillmat(fr, fin_vis, fin.material, z=2)
        self.mark(view, fin)
        le, rud = self.fin_parts()
        self.fillmat(fr, le.intersection(fin_vis), "MZ-DARK", z=3)
        sh.geom(fr.g(rud.intersection(fin_vis).boundary), ec="#4A4A4A", lw=0.18, z=4)
        for name, ident in (("wing", "F-WING"), ("gun", "F-GUN-S3"), ("missile_rack", "F-MISSILE-S2")):
            e = m.by_id[ident]
            self.fillmat(fr, self.vis(name), e.material, z=2)
            self.mark(view, e)
        for name in ("gear_main", "gear_nose"):
            v = self.vis(name)
            self.fillmat(fr, v.intersection(box(-5, -1.45, 25, 10)), "MZ-METAL", z=2)
            self.fillmat(fr, v.intersection(box(-5, -5, 25, -1.45)), "MZ-RUBBER", z=2)
        cf = m.by_id["F-CANOPY-FRAME"]
        self.fillmat(fr, cf.sb["shape"].intersection(hull_vis), "MZ-PAINT1", z=4, ec=INK, lw=0.18)
        self.outlines(fr, lw=0.5)
        # faint context: the parts of view B
        for e in m.elements:
            if e.sb and e.cat in ("functional", "greeble") and e.sb["kind"] == "area" and e.data.get("kind") != "grille" \
                    and e.status != "remove" \
                    and e.id not in ("F-POD-EXHAUST", "F-POD-INTAKE", "F-POD-BAY", "F-CANOPY-FRAME") and e.cat != "part" \
                    and not e.id.startswith("F-GEAR") and not e.id.startswith("F-GUNMOUNT"):
                if not e.sb["hidden"]:
                    sh.geom(fr.g(e.sb["shape"].intersection(self.vis(e.sb["solid"]))), ec="#777777", lw=0.13, z=7)
        # labels
        for e in m.elements:
            if not e.sb or e.cat not in V1_CATS or (label_ids is not None and e.id not in label_ids):
                continue
            if e.cat == "panel":
                continue
            if e.cat == "plate" and e.sb["solid"] == "pod" and fr.winbox is None and not label_pod_plates:
                continue                                    # pod armour: detail A
            reqs.append(self.req(fr, e))
        return reqs

    def bolts(self, fr, full, shp, kit):
        x0, z0, x1, z1 = full.bounds
        pitch, edge, r = kit["bolt_pitch"], kit["bolt_edge"], kit["bolt_d"] / 2
        pts = []
        x = x0 + edge
        while x <= x1 - edge + 1e-6:
            cut = LineString([(x, z0 - 1), (x, z1 + 1)]).intersection(full)
            if not cut.is_empty:
                b = cut.bounds
                if b[3] - b[1] > 2 * edge + 0.05:
                    pts += [(x, b[1] + edge), (x, b[3] - edge)]
            x += pitch
        for p in pts:
            if shp.contains(Point(p)):
                X, Y = fr.P(*p)
                if fr.inside(*p):
                    self.sh.ax.add_patch(Circle((X, Y), r * fr.s, fc="#3F3F3F", ec="none", zorder=7))

    def fin_parts(self):
        m = self.m
        poly = m.side["fin"]
        z0 = min(p[1] for p in poly)
        z1 = max(p[1] for p in poly)
        cfg = m.recipe["wings"]["fin"]
        le_pts_a, le_pts_b, rud_a, rud_b = [], [], [], []
        f0, f1 = cfg["flap"]["span"]
        c0 = cfg["flap"]["chord"]
        n = 20
        for k in range(n + 1):
            z = z0 + (z1 - z0) * k / n
            zz = min(max(z, z0 + 1e-6), z1 - 1e-6)
            sp = em.span_at([(p[1], p[0]) for p in poly], zz)       # x extent at height z
            xa, xb = sp
            c = xb - xa
            le_pts_a.append((xb - cfg["le"] * c, z))
            le_pts_b.append((xb, z))
            fz = (z - z0) / (z1 - z0)
            if f0 <= fz <= f1:
                rud_a.append((xa, z))
                rud_b.append((xa + (1 - c0) * c, z))
        le = Polygon(le_pts_a + le_pts_b[::-1]).buffer(0)
        rud = Polygon(rud_a + rud_b[::-1]).buffer(0)
        return le, rud

    def outlines(self, fr, lw=0.5):
        for name, s in self.m.solids.items():
            self.sh.geom(fr.g(s["visible"]), ec=INK, lw=lw, z=9)

    # ------------------------------------------------------------------ view B: functional parts, lights, decals
    def view_items(self, fr, view, skip_label=None, only=None, context_fill=True):
        m, sh = self.m, self.sh
        reqs = []
        # context: solids and the panel layout, light
        for name, s in m.solids.items():
            sh.geom(fr.g(s["visible"]), fc="#FFFFFF", ec="none", z=1)
        for e in m.elements:
            if e.sb and e.cat in ("panel", "frame") :
                sh.geom(fr.g(e.sb["shape"].intersection(self.vis("hull"))), ec=LIGHT, lw=0.13, z=2,
                        fc="#F1F1F1" if e.cat == "frame" else "none")
            elif e.sb and e.cat == "section":
                for ln in e.extra.get("seams", []):
                    sh.geom(fr.g(ln.intersection(self.vis("pod"))), ec=LIGHT, lw=0.13, z=2)
                if e.data["kind"] == "ring":
                    sh.geom(fr.g(e.sb["shape"].intersection(self.vis("pod"))), ec=LIGHT, lw=0.13, z=2)
        sh.geom(fr.g(m.canopy.intersection(self.vis("hull"))), fc="#EEF3F7", ec=GREY, lw=0.18, z=2)
        le, rud = self.fin_parts()
        sh.geom(fr.g(rud.intersection(self.vis("fin")).boundary), ec=LIGHT, lw=0.13, z=2)
        self.outlines(fr, lw=0.5)
        order = {"trim": 3, "decal": 4, "greeble": 5, "functional": 6, "light": 8}
        items = [e for e in m.elements if e.sb and e.cat in V2_CATS and (only is None or only(e))]
        items.sort(key=lambda e: (order[e.cat], e.sb["depth"]))
        for e in items:
            self.mark(view, e)
            self.item(fr, e)
            if skip_label and skip_label(e):
                continue
            reqs.append(self.req(fr, e))
        return reqs

    def item(self, fr, e):
        sh = self.sh
        col = STATUS_COL[e.status]
        shp = e.sb["shape"]
        hidden = e.sb["hidden"]
        ls = "--" if hidden or e.status == "remove" else "-"
        solid_vis = self.vis(e.sb["solid"])
        if e.extra.get("ghost") is not None:
            g = e.extra["ghost"]
            sh.geom(fr.g(g), ec=STATUS_COL["remove"], lw=0.25, ls="--", z=11)
            a = g.centroid
            b = e.sb["anchor"]
            if a.distance(Point(b)) > 0.15 and fr.inside(a.x, a.y) and fr.inside(*b):
                A, B = fr.P(a.x, a.y), fr.P(*b)
                sh.ax.annotate("", xy=B, xytext=A, zorder=12,
                               arrowprops=dict(arrowstyle="-|>", lw=0.2 * PT, color=STATUS_COL["change"],
                                               mutation_scale=4, linestyle=(0, (2.5, 1.5)), shrinkA=0, shrinkB=2))
        if e.cat == "light":
            self.light(fr, e)
            return
        if e.cat == "trim":
            sh.geom(fr.g(shp), ec=col, lw=0.35, ls="-." if not hidden else "--", z=6)
            return
        if e.cat == "decal":
            fc = "none" if hidden or e.status == "remove" else "#F3ECFA"
            clip = hidden or e.sb["kind"] != "area"
            sh.geom(fr.g(shp if clip else shp.intersection(solid_vis.buffer(0.01))), fc=fc, ec=col, lw=0.2, ls=ls, z=7)
            if e.extra.get("setup") and not hidden:
                self.decal_text(fr, e)
            for pt, up in e.extra.get("marks") or []:
                self.reading_arrow(fr, pt, up, STATUS_COL[e.status])
            if e.status == "remove":
                self.cross(fr, shp)
            return
        # hardware
        mat = e.material or "MZ-PAINT1"
        fill, hatch, hc = self.matstyle(mat)
        fill = fill if lum(fill) > 0.55 else "#C8CCD1"
        g = shp if hidden or e.sb["kind"] != "area" else shp.intersection(solid_vis.buffer(0.01))
        removed = e.status == "remove"
        sh.geom(fr.g(g), fc="none" if hidden or removed else fill, ec=col, lw=0.3, ls=ls,
                z=(8 if e.cat == "functional" else 7) + (1.5 if removed else 0))
        if not hidden and e.sb["kind"] == "area" and e.sb.get("vis_frac", 1.0) < 0.97:
            sh.geom(fr.g(shp.difference(solid_vis)), ec=col, lw=0.2, ls="--", z=12)
        if not removed:
            self.glyph(fr, e, hidden)
        if e.status == "remove":
            self.cross(fr, shp)

    def cross(self, fr, shp):
        """A removed part: a small red cross in its upper left corner (the dashed outline shows the part), so a new
        part in the same place does not read as removed (critic of the views, round 1)."""
        for part in parts_of(shp):
            x0, z0, x1, z1 = part.bounds
            if not (fr.inside(x0, z0) and fr.inside(x1, z1)):
                continue
            g = fr.g(part)
            X0, Y0, X1, Y1 = g.bounds
            r = min(1.3, (X1 - X0) / 3, (Y1 - Y0) / 3)
            cx, cy = X0 + r + 0.3, Y1 - r - 0.3
            for a, b in (((cx - r, cy - r), (cx + r, cy + r)), ((cx - r, cy + r), (cx + r, cy - r))):
                self.sh.line([a, b], 0.35, STATUS_COL["remove"], z=13)

    def glyph(self, fr, e, hidden):
        """The kind's symbol in each copy of the part (a view from above shows both sides' copies)."""
        for part in parts_of(e.sb["shape"]):
            self.glyph_one(fr, e, hidden, part.bounds)

    def glyph_one(self, fr, e, hidden, bounds):
        sh = self.sh
        col = STATUS_COL[e.status]
        x0, z0, x1, z1 = bounds
        kind = e.data.get("kind") or e.data.get("part")
        if not fr.inside((x0 + x1) / 2, (z0 + z1) / 2):
            return
        lw = 0.13
        if kind == "rcs" and e.sb["kind"] == "area":
            w = x1 - x0
            for k in (-1, 1):
                X, Y = fr.P((x0 + x1) / 2 + k * w * 0.22, (z0 + z1) / 2)
                sh.ax.add_patch(Circle((X, Y), min(w, z1 - z0) * 0.18 * fr.s, fc="#6E6E6E", ec=col, lw=lw * PT, zorder=9))
        elif kind in ("grille", "vent"):
            n = 5 if kind == "grille" else 6
            for k in range(1, n + 1):
                z = z0 + (z1 - z0) * k / (n + 1)
                sh.line([fr.P(x0 + 0.03, z), fr.P(x1 - 0.03, z)], lw, col if kind == "vent" else "#E0E0E0", z=9)
            if kind == "grille":
                sh.geom(fr.g(box(x0, z0, x1, z1)), fc="#4D5258", ec=col, lw=0.3, z=8.5,
                        ls="--" if hidden else "-")
                for k in range(1, n + 1):
                    z = z0 + (z1 - z0) * k / (n + 1)
                    sh.line([fr.P(x0 + 0.04, z), fr.P(x1 - 0.04, z)], 0.25, "#D8D8D8", z=9)
        elif kind in ("hatch", "hatch_large"):
            i = 0.06 if kind == "hatch_large" else 0.05
            sh.geom(fr.g(box(x0 + i, z0 + i, x1 - i, z1 - i)), ec=col, lw=lw, ls="--" if hidden else "-", z=9)
        elif kind == "sensor":
            X, Y = fr.P((x0 + x1) / 2 + (x1 - x0) * 0.2, (z0 + z1) / 2)
            sh.ax.add_patch(Circle((X, Y), 0.025 * fr.s, fc="none", ec=col, lw=lw * PT, zorder=9))
        elif kind == "connector":
            X, Y = fr.P((x0 + x1) / 2, (z0 + z1) / 2)
            sh.ax.add_patch(Circle((X, Y), 0.045 * fr.s, fc="#DCE0E5", ec=col, lw=lw * PT, zorder=9))

    def light(self, fr, e):
        sh = self.sh
        col = STATUS_COL[e.status]
        c = em.LIGHT_RGB.get(e.extra.get("color"), "#FFFFFF")
        shp = e.sb["shape"]
        hidden = e.sb["hidden"]
        if e.extra.get("strip"):
            for ln in lines_of(fr.g(shp)):
                sh.line(ln, 1.1, col, z=10, ls="--" if hidden else "-")
                sh.line(ln, 0.75, c, z=10.1)
            if e.extra.get("light"):
                a = e.sb["anchor"]
                if fr.inside(*a):
                    X, Y = fr.P(*a)
                    self.lamp(X, Y + 1.8, c, col, e.extra["light"])
            return
        sh.geom(fr.g(shp), fc=c, ec=col, lw=0.25, z=10, ls="--" if hidden else "-")
        pts = [e.sb["anchor"]] if e.sb["kind"] != "area" or len(parts_of(shp)) == 1 else \
            [(p.centroid.x, p.centroid.y) for p in parts_of(shp)]
        for a in pts:
            if fr.inside(*a):
                X, Y = fr.P(*a)
                self.lamp(X, Y, c, col, e.extra.get("light"), lens_only=not e.extra.get("light"), fr=fr)

    def lamp(self, X, Y, c, col, light, lens_only=False, fr=None):
        """Light symbol: a lens only = small open diamond; a point light = circle with a cross; a spot = circle and
        a cone; a flashing light = star."""
        sh = self.sh
        r = 1.5
        if lens_only:
            sh.ax.add_patch(MplPolygon([(X - r * 0.8, Y), (X, Y + r * 0.8), (X + r * 0.8, Y), (X, Y - r * 0.8)],
                                       closed=True, fc=c, ec=col, lw=0.25 * PT, zorder=14))
            return
        if light.get("flash_hz"):
            pts = []
            for k in range(10):
                rr = r * 1.25 if k % 2 == 0 else r * 0.5
                a = math.pi / 2 + k * math.pi / 5
                pts.append((X + rr * math.cos(a), Y + rr * math.sin(a)))
            sh.ax.add_patch(MplPolygon(pts, closed=True, fc=c, ec=col, lw=0.25 * PT, zorder=14))
            return
        sh.ax.add_patch(Circle((X, Y), r, fc=c, ec=col, lw=0.25 * PT, zorder=14))
        sh.line([(X - r * 0.7, Y - r * 0.7), (X + r * 0.7, Y + r * 0.7)], 0.2, col, z=14.1)
        sh.line([(X - r * 0.7, Y + r * 0.7), (X + r * 0.7, Y - r * 0.7)], 0.2, col, z=14.1)
        if light.get("type") == "spot":
            d = light.get("cone_deg", 40)
            ang = -90 if light.get("aim_down_deg") else -150
            if fr is not None and fr.flip:
                ang = -180 - ang
            for s in (-1, 1):
                a = math.radians(ang + s * d / 2)
                sh.line([(X + r * math.cos(a), Y + r * math.sin(a)), (X + 3.6 * r * math.cos(a), Y + 3.6 * r * math.sin(a))],
                        0.18, col, z=14)

    def decal_text(self, fr, e):
        x0, z0, x1, z1 = e.sb["shape"].bounds
        if not (fr.inside(x0, z0) and fr.inside(x1, z1)):
            return
        X0, Y0 = fr.P(x0, z0)
        X1, Y1 = fr.P(x1, z1)
        up = fr.vec(*e.extra.get("up", (0, 1)))
        s = BIG_DECAL_CZ.get(e.extra["item"], e.extra["item"].replace("D_Big_", "").replace("_", " "))
        if abs(X1 - X0) > 12:
            self.sh.t((X0 + X1) / 2, (Y0 + Y1) / 2, s, 1.6, STATUS_COL[e.status], ha="center", va="center", z=12)
        # the reading "up" of the marking (Tools/Tests/test_decal_orientation.py rule 3)
        cx, cy = max(X0, X1) - 1.8, (Y0 + Y1) / 2
        L = 1.6
        self.sh.ax.annotate("", xy=(cx + up[0] * L, cy + up[1] * L), xytext=(cx - up[0] * L, cy - up[1] * L), zorder=13,
                            arrowprops=dict(arrowstyle="-|>", lw=0.18 * PT, color=STATUS_COL[e.status], mutation_scale=3.5,
                                            shrinkA=0, shrinkB=0))

    def reading_arrow(self, fr, pt, up, col):
        """Which way a lettered marking reads (its up), at one copy."""
        if not fr.inside(*pt):
            return
        cx, cy = fr.P(*pt)
        u = fr.vec(*up)
        L = 1.6
        self.sh.ax.annotate("", xy=(cx + u[0] * L, cy + u[1] * L), xytext=(cx - u[0] * L, cy - u[1] * L), zorder=13,
                            arrowprops=dict(arrowstyle="-|>", lw=0.18 * PT, color=col, mutation_scale=3.5,
                                            shrinkA=0, shrinkB=0))

    # ------------------------------------------------------------------ any view in one drawing (exterior_views)
    def view_any(self, fr, view, label_filter=None):
        """A view from above, below, behind or ahead (Model.use_view(view) first): the solids in their materials,
        zones, plates, recesses, the proposed plates and frame, pod sections, then every part, light, decal and
        trim of the view; returns the label requests (plates inside their outline: panel_labels)."""
        m, sh = self.m, self.sh
        reqs = []
        part_of = {"hull": "P-HULL", "pod": "P-POD", "wing": "F-WING", "fin": "F-FIN", "gun": "F-GUN-S3",
                   "missile_rack": "F-MISSILE-S2", "gear_main": "F-GEAR-MAIN", "gear_nose": "F-GEAR-NOSE"}
        for name, s_ in m.solids.items():
            el = m.by_id[part_of[name]]
            if name.startswith("gear"):
                # from below the extended leg shows its pad's rubber sole
                self.fillmat(fr, s_["visible"], "MZ-RUBBER" if view.startswith("BOT") or view == "DD-BOT" else "MZ-METAL", z=2)
            else:
                self.fillmat(fr, s_["visible"], el.material or s_["material"], z=2)
            if el.sb:
                self.mark(view, el)
        hull_vis = self.vis("hull")
        self.fillmat(fr, m.canopy.intersection(hull_vis), "MZ-GLASS", z=3)
        self.wing_parts(fr, view)
        vm = m.views_model
        if view == "AFT":
            sh.geom(fr.g(vm.aft_wall), ec=GREY, lw=0.25, z=4)
            sh.geom(fr.g(vm.ramp), ec=GREY, lw=0.2, ls="--", z=4)
        for e in m.elements:
            if not e.sb or e.cat not in ("zone", "recess", "plate") or e.status == "remove":
                continue
            solid_vis = self.vis(e.sb["solid"])
            zo = 5.5 if e.extra.get("on_panels") else (3 if e.cat != "plate" else 4)
            self.fillmat(fr, e.sb["shape"].intersection(solid_vis), e.material, z=zo,
                         ec=STATUS_COL[e.status] if e.cat == "plate" else "none", lw=0.25)
            self.mark(view, e)
        for e in m.elements:
            if e.sb and e.cat == "functional" and e.data.get("kind") == "grille":
                self.fillmat(fr, e.sb["shape"].intersection(hull_vis), "MZ-DARK", z=3)
        for e in m.elements:
            if e.cat == "panel" and e.sb:
                shp = e.sb["shape"].intersection(hull_vis)
                self.mark(view, e)
                if not shp.is_empty:
                    self.fillmat(fr, shp, e.material, z=5, ec=STATUS_COL[e.status], lw=0.3)
            elif e.cat == "frame" and e.sb:
                sh.geom(fr.g(e.sb["shape"].intersection(hull_vis)), fc="#5E646B", ec=STATUS_COL[e.status], lw=0.18, z=6)
                self.mark(view, e)
        for e in m.elements:
            if e.sb and e.cat == "plate" and e.status == "remove":
                sh.geom(fr.g(e.sb["shape"]), ec=STATUS_COL["remove"], lw=0.3, ls="--", z=8)
                self.cross(fr, e.sb["shape"])
                self.mark(view, e)
        pod_vis = self.vis("pod")
        for e in m.elements:
            if not e.sb or e.sb["solid"] != "pod":
                continue
            if e.cat == "section":
                if e.data["kind"] == "ring":
                    self.fillmat(fr, e.sb["shape"].intersection(pod_vis), e.material, z=3)
                for ln in e.extra.get("seams") or []:
                    sh.geom(fr.g(ln.intersection(pod_vis)), ec="#6B6B6B", lw=0.18, z=4)
                self.mark(view, e)
            elif e.cat == "plate":
                self.fillmat(fr, e.sb["shape"].intersection(pod_vis), e.material, z=5, ec=STATUS_COL[e.status], lw=0.3)
                self.mark(view, e)
            elif e.id in ("F-POD-EXHAUST", "F-POD-INTAKE", "F-POD-BAY", "F-NOZZLE"):
                self.fillmat(fr, e.sb["shape"].intersection(pod_vis), "MZ-METAL" if e.id == "F-NOZZLE" else e.material, z=4)
                self.mark(view, e)
        self.outlines(fr, lw=0.5)
        order = {"trim": 3, "decal": 4, "greeble": 5, "functional": 6, "light": 8}
        items = [e for e in m.elements if e.sb and e.cat in order]
        items.sort(key=lambda e: (order[e.cat], e.sb["depth"]))
        for e in items:
            self.mark(view, e)
            if e.id in ("F-POD-EXHAUST", "F-POD-INTAKE", "F-POD-BAY", "F-NOZZLE"):
                continue
            self.item(fr, e)
        for e in m.elements:
            if not e.sb or e.cat == "panel" or e.cat in ("material", "kit", "rule"):
                continue
            if label_filter is not None and not label_filter(e):
                continue
            reqs.append(self.req(fr, e))
        return reqs

    def wing_parts(self, fr, view):
        """Leading edge (dark) and flap outline of the wings and fins seen from above or below: the chord fractions
        of the recipe (wings.wing / wings.fin: le, flap span and chord) over the plan outline."""
        if view not in ("TOP", "BOT"):
            return
        m = self.m
        for name in ("wing", "fin"):
            cfg = m.recipe["wings"][name]
            poly = m.top[name]
            ys = [p[1] for p in poly]
            y0, y1 = min(ys), max(ys)
            le_a, le_b, fa, fb = [], [], [], []
            n = 24
            for k in range(n + 1):
                y = y0 + (y1 - y0) * k / n
                yy = min(max(y, y0 + 1e-6), y1 - 1e-6)
                xa, xb = em.span_at([(p[1], p[0]) for p in poly], yy)
                c = xb - xa
                le_a.append((xb - cfg["le"] * c, y))
                le_b.append((xb, y))
                f = (y - y0) / (y1 - y0) if name == "wing" else 0.5
                if name == "wing" and cfg["flap"]["span"][0] <= f <= cfg["flap"]["span"][1]:
                    fa.append((xa, y))
                    fb.append((xa + (1 - cfg["flap"]["chord"]) * c, y))
            for sgn in (1, -1):
                def put(pts):
                    g = Polygon([(x, sgn * y) for x, y in pts]).buffer(0)
                    return m.views_model.paper(view, g)
                vis = self.vis(name)
                le = put(le_a + le_b[::-1])
                self.fillmat(fr, le.intersection(vis), "MZ-DARK", z=3)
                if fa:
                    self.sh.geom(fr.g(put(fa + fb[::-1]).intersection(vis).boundary), ec="#4A4A4A", lw=0.18, z=4)

    # ------------------------------------------------------------------ labels
    def req(self, fr, e):
        a = e.sb["anchor"]
        if fr.winbox is not None and not fr.winbox.contains(Point(a)):
            # a detail window: point at the copy (or the part) inside the window
            part = e.sb["shape"].intersection(fr.winbox.buffer(-0.01))
            if not part.is_empty:
                p_ = em.largest(em.polys_only(part)) if part.area > 0 else part
                p_ = p_.representative_point() if not p_.is_empty else part.representative_point()
                a = (p_.x, p_.y)
        x0, z0, x1, z1 = e.sb["shape"].bounds
        if e.sb["kind"] == "area" and e.extra.get("setup") and x1 - x0 > 0.5 and not fr.flip:
            a = (x1 - 0.12, z1 - 0.03)
        elif e.sb["kind"] == "area" and e.status == "remove" and e.cat not in ("plate",):
            a = (x0 + 0.03, z1 - 0.03)
        txt = e.id + ((" " + STATUS_MARK[e.status]) if STATUS_MARK[e.status] else "")
        return {"id": e.id, "text": txt, "anchor": fr.P(*a), "col": STATUS_COL[e.status], "z": a[1],
                "hidden": e.sb["hidden"]}

    @staticmethod
    def spread(desired, widths, lo, hi, gap=2.5):
        """1D label layout keeping the order: left edges as close as possible to the desired ones without overlap
        (clusters of touching labels sit at the mean of their members' wishes, clamped to [lo, hi])."""
        clusters = []                                   # [start, [indices], total width]
        for i, d in enumerate(desired):
            clusters.append([d, [i], widths[i]])
            while True:
                c = clusters[-1]
                offs, acc = [], 0.0
                for k in c[1]:
                    offs.append(acc)
                    acc += widths[k] + gap
                c[2] = acc - gap
                c[0] = sum(desired[k] - o for k, o in zip(c[1], offs)) / len(c[1])
                c[0] = min(max(c[0], lo), hi - c[2])
                if len(clusters) > 1 and clusters[-2][0] + clusters[-2][2] + gap > c[0]:
                    prev = clusters[-2]
                    prev[1] += c[1]
                    clusters.pop()
                    continue
                break
        out = [0.0] * len(desired)
        for start, idx, _ in clusters:
            acc = start
            for k in idx:
                out[k] = acc
                acc += widths[k] + gap
        return out

    def place_labels(self, view, reqs, x_lo, x_hi, tiers_up, tiers_dn, split_y, size=LABEL_MM, bus_up=None, bus_dn=None):
        """Labels in rows above and below a view: sorted by the anchor's x and spread along a row without overlap
        (as few rows as fit, dealt round-robin, so leaders cross as little as possible); labels whose parts lie on
        the same spot share one label and leader; the leader runs from the label to a dot on the part."""
        sh = self.sh
        merged = []
        for r in sorted(reqs, key=lambda r: (r["anchor"][0], r["anchor"][1])):
            m = next((q for q in merged if q["col"] == r["col"] and abs(q["anchor"][0] - r["anchor"][0]) < 1.5
                      and abs(q["anchor"][1] - r["anchor"][1]) < 1.5), None)
            if m:
                m["text"] += ", " + r["text"]
                m["ids"].append(r["id"])
            else:
                merged.append(dict(r, ids=[r["id"]]))
        ups = sorted([r for r in merged if r["anchor"][1] >= split_y], key=lambda r: r["anchor"][0])
        dns = sorted([r for r in merged if r["anchor"][1] < split_y], key=lambda r: r["anchor"][0])
        placed = []
        for group, tiers, up in ((ups, tiers_up, True), (dns, tiers_dn, False)):
            n = len(tiers)
            total = sum(sh.width(r["text"], size) + 3.0 for r in group)
            n_used = max(1, min(n, int(math.ceil(total / (0.92 * (x_hi - x_lo)))) or 1))
            for ti in range(n_used):
                members = group[ti::n_used]
                ws = [sh.width(r["text"], size) + 1.4 for r in members]
                xs = self.spread([r["anchor"][0] - w / 2 for r, w in zip(members, ws)], ws, x_lo, x_hi, gap=size)
                ty = tiers[ti]
                h = size * 1.15
                for r, x, w in zip(members, xs, ws):
                    placed.append((r, (x, ty - h * 0.3, x + w, ty + h * 0.95), up))
        last = {True: -1e9, False: -1e9}
        for r, bx, up in sorted(placed, key=lambda t: (t[2], t[0]["anchor"][0])):
            x0, y0, x1, y1 = bx
            sh.t(x0 + 0.7, y0 + 0.3 * (y1 - y0) / 1.25, r["text"], size, r["col"], z=40, bg="white")
            ax_, ay_ = r["anchor"]
            lx = min(max(ax_, x0 + 1.0), x1 - 1.0)
            ly = y0 - 0.2 if up else y1 + 0.2
            bus = bus_up if up else bus_dn
            ls = ":" if r["hidden"] else "-"
            if bus is None:
                sh.line([(lx, ly), (ax_, ay_)], 0.13, r["col"], z=35, ls=ls)
            else:
                vx = max(ax_, last[up] + 1.5)           # parallel drops at least 1.5 mm apart
                last[up] = vx
                sh.line([(ax_, ay_), (vx, ay_), (vx, bus), (lx, ly)], 0.13, r["col"], z=35, ls=ls)
            sh.ax.add_patch(Circle((ax_, ay_), 0.5, fc=r["col"], ec="white", lw=0.1 * PT, zorder=36))
            for i in r["ids"]:
                self.labelled.setdefault(view, set()).add(i)

    def hidden_panel_reqs(self, fr, ids):
        """Leader labels with a dotted leader for plates hidden in this view (behind a nearer body)."""
        out = []
        for i in ids:
            e = self.m.by_id[i]
            a = e.sb["shape"].representative_point()
            out.append({"id": i, "text": i, "anchor": fr.P(a.x, a.y), "col": STATUS_COL[e.status], "z": a.y,
                        "hidden": True})
        return out

    def panel_labels(self, fr, view, size=PANEL_MM):
        """Each plate's ID inside its visible part where the text fits (pole of inaccessibility, then the
        representative point); otherwise a leader label request. Returns (hidden IDs, leader requests)."""
        sh = self.sh
        hidden, reqs = [], []
        for e in self.m.elements:
            if e.cat != "panel" or not e.sb:
                continue
            if e.data.get("band") == "R" and self.m.view in ("SB", "PORT"):
                # seen from the side only as a strip along the roof edge: named in a note, drawn on E-03
                self.roof_side.setdefault(view, []).append(e.id)
                self.labelled.setdefault(view, set()).add(e.id)
                continue
            shp = em.polys_only(e.sb["shape"].intersection(self.vis("hull")))
            if shp.is_empty or shp.area < 0.02:
                hidden.append(e.id)
                continue
            part = em.largest(shp)
            w = (sh.width(e.id, size) + 1.2) / fr.s
            h = size * 1.3 / fr.s
            spot = None
            for p in (polylabel(part, 0.005), part.representative_point(), part.centroid):
                if part.contains(box(p.x - w / 2, p.y - h / 2, p.x + w / 2, p.y + h / 2)):
                    spot = p
                    break
            if spot is None:
                a = part.representative_point()
                reqs.append({"id": e.id, "text": e.id, "anchor": fr.P(a.x, a.y),
                             "col": STATUS_COL[e.status], "z": a.y, "hidden": False})
                continue
            X, Y = fr.P(spot.x, spot.y)
            sh.t(X, Y, e.id, size, STATUS_COL[e.status], ha="center", va="center", z=20, bg="white")
            self.labelled.setdefault(view, set()).add(e.id)
        return hidden, reqs


# ---------------------------------------------------------------------- sheet furniture
BIG_DECAL_CZ = {"D_Big_Wayfarer": "WAYFARER", "D_Big_Registration": "registrace", "D_Big_Logo": "logo Halcyon",
                "D_Big_Hazard_Exhaust": "výstraha výfuku", "D_Big_Hazard_Ramp": "výstraha rampy"}


def roof_note(ids):
    """The roof plates seen from the side (a strip along the roof edge) named in one sentence."""
    if not ids:
        return ""
    return "Desky hřbetu %s–%s (z boku jen pruh na hraně střechy) popisuje E-03." % (min(ids), max(ids))


def parts_of(g):
    """The polygons (or lines) of a geometry, one per copy."""
    if g is None or g.is_empty:
        return []
    if hasattr(g, "geoms"):
        return [p for p in g.geoms if not p.is_empty]
    return [g]


def wrap(sh, text, size, width, max_lines=1):
    """Text broken into at most max_lines lines of the width (mm); a cut-off end gets an ellipsis."""
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if not cur or sh.width(t, size) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    cut = len(lines) > max_lines
    lines = lines[:max_lines] or [""]
    if cut:
        lines[-1] += " …"
    for i, ln in enumerate(lines):
        while ln and sh.width(ln, size) > width:
            ln = ln[:-3] + "…" if len(ln) > 3 else ""
        lines[i] = ln
    return lines


def table(sh, x, ytop, title, cols, rows, size=TABLE_MM, rowh=4.4, title_size=3.4):
    """cols [(header, width mm, align[, lines])], rows [[cell, ...], colour]: the ID and the "stav" / "akce" cells
    take the row's colour, a column with lines > 1 breaks its text over up to that many lines. Returns the y below."""
    stav = [k for k, c in enumerate(cols) if c[0] in ("stav", "akce")]
    sh.t(x, ytop - title_size, title, title_size, weight="bold")
    y = ytop - title_size - 2.4
    W = sum(c[1] for c in cols)
    sh.line([(x, y), (x + W, y)], 0.35)
    cx = x
    for c in cols:
        h, w, al = c[:3]
        sh.t(cx + (0.8 if al == "left" else w - 0.8), y - rowh + 1.1, h, size * 0.9, GREY,
             ha="left" if al == "left" else "right")
        cx += w
    y -= rowh
    sh.line([(x, y), (x + W, y)], 0.25)
    line_h = size * 1.3
    for cells, col in rows:
        cl = [wrap(sh, cell, size, c[1] - 1.6, c[3] if len(c) > 3 else 1) for c, cell in zip(cols, cells)]
        n = max(len(v) for v in cl)
        cx = x
        for k, (c, lines) in enumerate(zip(cols, cl)):
            for i, ln in enumerate(lines):
                sh.t(cx + (0.8 if c[2] == "left" else c[1] - 0.8), y - rowh + 1.1 - i * line_h, ln, size,
                     col if (k == 0 or k in stav) else INK, ha="left" if c[2] == "left" else "right")
            cx += c[1]
        y -= rowh + (n - 1) * line_h
        sh.line([(x, y), (x + W, y)], 0.1, "#D5D5D5")
    sh.line([(x, y), (x + W, y)], 0.25)
    return y


def light_desc(e):
    L = e.extra.get("light")
    if not L:
        return "svítící pás bez zdroje" if e.extra.get("strip") else "jen čočka (bez zdroje)"
    s = "%s %g cd" % ({"point": "bodové", "spot": "reflektor"}.get(L["type"], L["type"]), L["intensity_cd"])
    if L.get("cone_deg"):
        s += ", kužel %g°" % L["cone_deg"]
    if L.get("flash_hz"):
        s += ", záblesk %g Hz" % L["flash_hz"]
    return s


COLOR_CZ = {"red": "červená", "green": "zelená", "white": "bílá", "amber": "jantarová", "strip": "studená bílá",
            "warm": "teplá bílá"}
LIGHT_TYPE_CZ = {"nav": "polohové", "tail": "koncové", "marker_pod": "obrysové", "marker_hull": "obrysové",
                 "flood": "světlomet", "pod_run": "obrysový pás", "bay_glow": "pracovní pás", "hull_run_low": "obrysový pás",
                 "hull_run_canopy": "obrysový pás", "belly_run": "obrysový pás"}
VIEW_SHORT = {"SB": "B", "PORT": "L", "TOP": "H", "BOT": "S", "AFT": "Z", "FWD": "Č", "GAP": "M"}


def frame_and_zones(sh):
    W, H = sh.w, sh.h
    sh.rect(20, 10, W - 10, H - 10, ec=INK, lw=0.7, z=50)
    sh.rect(10, 5, W - 5, H - 5, ec=INK, lw=0.25, z=50)
    for k in range(1, 12):
        x = 20 + (W - 30) * k / 12
        sh.line([(x, H - 10), (x, H - 5)], 0.25)
        sh.line([(x, 10), (x, 5)], 0.25)
    for k in range(12):
        x = 20 + (W - 30) * (k + 0.5) / 12
        sh.t(x, H - 8.6, str(k + 1), 2.5, GREY, ha="center")
    for k in range(1, 8):
        y = 10 + (H - 20) * k / 8
        sh.line([(20, y), (15, y)], 0.25)
    for k in range(8):
        y = 10 + (H - 20) * (k + 0.5) / 8
        sh.t(16.5, y, "ABCDEFGH"[7 - k], 2.5, GREY, ha="center", va="center")


def detail_callout(sh, fr, label_up=True):
    """The window of detail A drawn on a view: a dash-dot rectangle and its name."""
    X0, Y0 = fr.P(DETAIL_WIN[0], DETAIL_WIN[1])
    X1, Y1 = fr.P(DETAIL_WIN[2], DETAIL_WIN[3])
    sh.rect(X0, Y0, X1, Y1, ec=INK, lw=0.35, ls="-.", z=45)
    sh.t(X0 + 1.5, Y1 - 4.6 if label_up else Y0 + 1.5, "DETAIL A (1:20)", 3.0, weight="bold", z=46, bg="white")


def metre_ticks(sh, fr):
    for x in range(0, 22):
        X, Y = fr.P(x, -1.6)
        sh.line([(X, Y), (X, Y - 1.5)], 0.18, GREY)
        if x % 2 == 0:
            sh.t(X, Y - 4.6, "%d" % x, 2.2, GREY, ha="center")
    gx0, gy0 = fr.P(-0.6, -1.6)
    gx1, _ = fr.P(21.1, -1.6)
    sh.line([(gx0, gy0), (gx1, gy0)], 0.25, GREY, ls="-.")


SHEETS = {"E-01": ("E01_starboard", "Exteriér – pravobok: desky, materiály, funkční prvky, světla, decaly"),
          "E-02": ("E02_schedules", "Exteriér – tabulky: funkční prvky, poklopy, světla, decaly, kit, změny, kontrola dat"),
          "E-03": ("E03_top", "Exteriér – shora: hřbet, zkosení, křídla, gondoly, světla, decaly"),
          "E-04": ("E04_bottom", "Exteriér – zespodu: břicho, podvozek, raketnice, světla, decaly"),
          "E-05": ("E05_ends", "Exteriér – zezadu a zepředu: zadní stěna s rampou, čelo, tryska a sání"),
          "E-06": ("E06_port", "Exteriér – levobok: zrcadlo pravoboku a kontrola nápisů levé strany"),
          "E-07": ("E07_details", "Exteriér – detaily: příď s kabinou, zadní stěna s rampou, gondola shora"),
          "E-08": ("E08_details", "Exteriér – detaily: hlavní podvozek (části, kóty), koncový držák zbraně s řezem")}


def save_sheet(sh, m, d, sheet, dpi, out_dir, extra=None):
    """PNG (and a vector PDF in Saved/Drawings) plus the sidecar: the IDs drawn and labelled per view and listed per
    schedule, with the digests of the data the sheet was drawn from (Tools/Tests/test_exterior_drawing.py)."""
    out_dir = out_dir or os.path.join(em.ROOT, "ArtSource", "Ships", m.ship, "Design", "Drawings")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "%s_%s" % (m.ship, SHEETS[sheet][0]))
    pdf_dir = os.path.join(em.ROOT, "Saved", "Drawings")
    os.makedirs(pdf_dir, exist_ok=True)
    sidecar = {
        "_comment": "Written by Tools/Design/draw_exterior_sheet.py: the IDs this sheet draws and labels per view and "
                    "lists per schedule, with the digests of the data it was drawn from (Tools/Tests/test_exterior_drawing.py).",
        "sheet": sheet, "ship": m.ship, "digests": m.digests,
        "drawn": {k: sorted(v) for k, v in d.drawn.items()},
        "labelled": {k: sorted(v) for k, v in d.labelled.items()},
        "schedules": {k: sorted(v) for k, v in SCHEDULED.items()},
    }
    sidecar.update(extra or {})
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(sidecar, f, ensure_ascii=False, indent=1)
    sh.save(base + ".png", dpi, os.path.join(pdf_dir, os.path.basename(base) + ".pdf"))
    print("EXTSHEET %s wrote %s.png (%d dpi) and .json, PDF in Saved/Drawings" % (sheet, os.path.relpath(base, em.ROOT), dpi))
    return base


def draw(ship="Wayfarer", dpi=200, out_dir=None, sheets=None):
    import draw_exterior_views as dv
    setup_fonts()
    m = em.Model(ship)
    out = []
    for sheet, fn in (("E-01", draw_e01), ("E-02", draw_e02), ("E-03", dv.draw_e03), ("E-04", dv.draw_e04),
                      ("E-05", dv.draw_e05), ("E-06", dv.draw_e06), ("E-07", dv.draw_e07), ("E-08", dv.draw_e08)):
        if sheets and sheet not in sheets:
            continue
        SCHEDULED.clear()
        m.use_view("SB")
        out.append(fn(m, dpi, out_dir))
    m.use_view("SB")
    return out


def draw_e01(m, dpi, out_dir):
    """E-01: the starboard views A (plates, materials) and B (functional parts, lights, decals), detail A, the
    legend, sections R1/R2, the chosen concept and the notes; the tables are on E-02 (author 1. 10. 2026)."""
    sh = Sheet()
    d = Drawer(sh, m)
    W, H = sh.w, sh.h
    frame_and_zones(sh)
    x_left = 34.0
    X0 = x_left + 12.0 + 0.75 * SCALE                # paper x of model x 0 (levels to the left)
    x_hi = 786.0
    win = box(*DETAIL_WIN)

    def in_detail(e):
        return e.sb["solid"] in ("pod", "fin") and win.contains(Point(e.sb["anchor"]))

    # ---------------------------------------------------------------- view A
    zA = 768.0 - 3.81 * SCALE
    frA = Frame(X0, zA, SCALE)
    sh.t(x_left, 822, "A   PRAVOBOK – DESKY A MATERIÁLOVÉ ZÓNY", TITLE_MM, weight="bold")
    sh.t(x_left + 175, 822, "1 : 30", TITLE_MM)
    reqsA = d.view_materials(frA, "A")
    stations_and_dims(sh, frA, m)
    hiddenA, panel_reqs = d.panel_labels(frA, "A")
    reqsA += panel_reqs + section_mark(sh, frA, m) + panel_number_sample(sh, frA, m)
    detail_callout(sh, frA)
    d.place_labels("A", reqsA, x_left, x_hi, tiers_up=[797, 806.5], tiers_dn=[558, 549], split_y=zA + 1.4 * SCALE,
                   bus_up=789.0, bus_dn=564.5)
    sh.t(x_left, 541, "Desky v poli za gondolou a ploutví, v tomto pohledu skryté: " + ", ".join(hiddenA) + ". "
         + roof_note(d.roof_side.get("A", [])), 2.5, STATUS_COL["proposed"])
    for i in hiddenA:
        d.labelled.setdefault("A", set()).add(i)
    # ---------------------------------------------------------------- view B
    zB = 486.0 - 3.81 * SCALE
    frB = Frame(X0, zB, SCALE)
    sh.t(x_left, 531, "B   PRAVOBOK – FUNKČNÍ PRVKY, SVĚTLA A DECALY", TITLE_MM, weight="bold")
    sh.t(x_left + 175, 531, "1 : 30", TITLE_MM)
    reqsB = d.view_items(frB, "B", skip_label=in_detail)
    metre_ticks(sh, frB)
    levels(sh, frB)
    detail_callout(sh, frB)
    X0b, _ = frB.P(DETAIL_WIN[0], 0)
    sh.t(X0b + 1.5, frB.P(0, DETAIL_WIN[1])[1] + 1.5, "prvky gondoly a ploutve popisuje detail A", 2.2, z=46, bg="white")
    d.place_labels("B", reqsB, x_left, x_hi, tiers_up=[503, 512.5, 522], tiers_dn=[287, 277.5, 268], split_y=zB + 1.25 * SCALE,
                   bus_up=495.0, bus_dn=296.0)
    # ---------------------------------------------------------------- detail A (pod, 1:20)
    dx_left = 800.0
    frD = Frame(dx_left - DETAIL_WIN[0] * DSCALE, 596.0 - DETAIL_WIN[1] * DSCALE, DSCALE, DETAIL_WIN)
    sh.t(dx_left, 822, "DETAIL A – GONDOLA S TRYSKOU A PLOUTEV", TITLE_MM, weight="bold")
    sh.t(dx_left + 150, 822, "1 : 20", TITLE_MM)
    reqsD = d.view_materials(frD, "D", label_ids={e.id for e in m.elements if e.sb and e.sb["solid"] in ("pod", "fin")})
    reqsD += d.view_items(frD, "D", skip_label=lambda e: not in_detail(e), only=lambda e: win.intersects(e.sb["shape"]))
    X0d, Y0d = frD.P(DETAIL_WIN[0], DETAIL_WIN[1])
    X1d, Y1d = frD.P(DETAIL_WIN[2], DETAIL_WIN[3])
    sh.rect(X0d, Y0d, X1d, Y1d, ec=INK, lw=0.35, z=44)
    keep = {e.id for e in m.elements if e.sb and (e.sb["solid"] in ("pod", "fin")) and win.contains(Point(e.sb["anchor"]))}
    seen = set()
    reqsD = [r for r in reqsD if r["id"] in keep and not (r["id"] in seen or seen.add(r["id"]))]
    detail_dims(sh, frD, m, Y0d)
    d.place_labels("D", reqsD, dx_left, W - 14, tiers_up=[Y1d + 7, Y1d + 15, Y1d + 23],
                   tiers_dn=[Y0d - 17, Y0d - 25, Y0d - 33], split_y=frD.P(0, POD_SPLIT)[1], bus_up=Y1d + 3.0, bus_dn=Y0d - 11.0)
    # ---------------------------------------------------------------- legend, sections, concept, notes
    legend(sh, m, x_left, 258)
    section(sh, m, 440.0, 258.0, "R1", "XK-PLATE", "U")
    section(sh, m, 440.0, 208.0, "R2", "XK-PLATE-H", "L")
    concept_strip(sh, m, dx_left, 548.0, width=375.0)
    notes(sh, m, dx_left, 400.0)
    title_block(sh, m, dx_left, W, "E-01")
    return save_sheet(sh, m, d, "E-01", dpi, out_dir)


def draw_e02(m, dpi, out_dir):
    """E-02: every schedule of the exterior - functional parts, greebles, lights, kit, decals, decal rules, the
    changes to the built ship and the drawing model's data check."""
    sh = Sheet()
    d = Drawer(sh, m)
    W, H = sh.w, sh.h
    frame_and_zones(sh)
    sh.t(34, 822, "TABULKY EXTERIÉRU – WAYFARER", TITLE_MM, weight="bold")
    sh.t(34, 815.5, "Prvky všech pohledů (sloupec „pohled“: B pravobok, L levobok, H shora, S zespodu, Z zezadu, "
                   "Č zepředu, M mezera gondola–trup); výkresy pohledů na listech E-01 a E-03 až E-07. "
                   "✓ = schváleno autorem %s." % m.design["approved"]["date"],
         2.5, GREY)
    schedules(sh, d, m, 34.0, 808.0)
    yc = changes_box(sh, m, 800.0, 808.0)
    rules_table(sh, m, 800.0, yc - 4)
    title_block(sh, m, 800.0, W, "E-02")
    return save_sheet(sh, m, d, "E-02", dpi, out_dir)


def notes(sh, m, x, ytop):
    """General notes and the list of the exterior sheets."""
    sh.t(x, ytop - 3, "POZNÁMKY", 3.4, weight="bold")
    lines = [
        "1. Kreslí skript z dat stavby a dat návrhu (jeden zdroj dat); ID na výkresu = ID v datech.",
        "2. Souřadnice v metrech: x od zádi, y k levoboku, z od paluby; tloušťky v mm.",
        "3. Zrcadlené prvky mají jedno ID pro oba boky; ks v tabulkách = na celé lodi.",
        "4. Stav: černě postaveno, modře návrh (+) a změna (Δ, stará poloha červeně čárkovaně), červeně odstranit (×).",
        "5. Prvky gondoly a ploutve popisuje detail A; tabulky všech prvků jsou na listu E-02.",
        "6. Po schválení výkresů se exteriérový kit a pilot staví z dat návrhu (Design/%s_exterior_design.json)." % m.ship,
    ]
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(wrap(sh, ln, 2.5, 372, 2)):
            sh.t(x + (0 if k == 0 else 4), y, part, 2.5)
            y -= 4.0
    y -= 2
    sh.t(x, y, "LISTY EXTERIÉRU", 3.0, weight="bold")
    y -= 5
    for code, (_, title) in SHEETS.items():
        sh.t(x, y, code, 2.5, weight="bold")
        sh.t(x + 14, y, title, 2.5)
        y -= 4.0
    return y


POD_SPLIT = 1.35
SCHEDULED = {}


def stations_and_dims(sh, fr, m):
    """Frame stations (the hull seams) with the bay numbers the panel IDs use, levels and the main dimensions."""
    p = m.panel_spec
    st = [p["ends"][0]] + m.seams + [p["ends"][1]]
    ytop = fr.P(0, 3.81)[1] + 6
    for x in m.seams:
        X, Y = fr.P(x, m.z_of(x, 1.0))
        sh.line([(X, Y + 1), (X, ytop + 1.5)], 0.13, GREY, ls=":")
        sh.t(X, ytop + 2.4, ("%.1f" % x).replace(".", ","), 2.2, GREY, ha="center")
    for i in range(1, len(st)):
        X, _ = fr.P((st[i - 1] + st[i]) / 2, 0)
        sh.ax.add_patch(Circle((X, ytop - 1.4), 2.3, fc="white", ec=STATUS_COL["proposed"], lw=0.18 * PT, zorder=30))
        sh.t(X, ytop - 1.4, "%02d" % i, 2.1, STATUS_COL["proposed"], ha="center", va="center", z=31)
    sh.t(fr.P(-0.72, 0)[0], ytop - 2.2, "pole", 2.2, STATUS_COL["proposed"], ha="right")
    sh.t(fr.P(-0.72, 0)[0], ytop + 2.4, "příčky x", 2.2, GREY, ha="right")
    for b in p["bands"]:
        v = (b["v"][0] + b["v"][1]) / 2
        _, Y = fr.P(20.85, m.z_of(20.0, v))
        A = fr.P(19.0, m.z_of(19.0, v))
        sh.t(fr.P(21.35, 0)[0], Y, b["band"], 3.0, STATUS_COL["proposed"], ha="left", va="center", weight="bold")
        sh.line([(fr.P(21.3, 0)[0], Y), A], 0.13, STATUS_COL["proposed"])
    levels(sh, fr)
    metre_ticks(sh, fr)
    y = fr.P(0, -1.6)[1] - 11.0
    dim_h(sh, fr.P(-0.5, 0)[0], fr.P(21.0, 0)[0], y, "21,50 (gondola -0,50 … příď 21,00)", fr.P(-0.5, 0.25)[1], fr.P(21.0, 0.7)[1])
    dim_h(sh, fr.P(0.0, 0)[0], fr.P(21.0, 0)[0], y - 7.5, "21,00 trup", fr.P(0, -0.35)[1], fr.P(21.0, 0.7)[1])
    xr = fr.P(21.0, 0)[0] + 16
    dim_v(sh, xr, fr.P(0, -1.6)[1], fr.P(0, 3.3)[1], "4,90 (zem … střecha kabiny)", fr.P(17.6, -1.6)[0], fr.P(16.0, 3.3)[0])


def levels(sh, fr):
    """Height levels left of the view: deck, ground (gear down) and the roof, metres from the deck."""
    k = -1 if fr.flip else 1
    for z, name in ((0.0, "±0,00 paluba"), (-1.6, "-1,60 zem"), (3.3, "+3,30 střecha kabiny, špička ploutve")):
        X, Y = fr.P(-0.75, z)
        sh.line([(X - 12 * k, Y), (X + k, Y)], 0.18, INK)
        # the level mark at the line's outer end, the text after it (the mark sat on the text, 1. 10. 2026)
        sh.ax.add_patch(MplPolygon([(X - 11 * k, Y), (X - 12.2 * k, Y + 1.6), (X - 9.8 * k, Y + 1.6)], closed=True,
                                   fc=INK, ec="none", zorder=20))
        sh.t(X - 9 * k, Y + 0.8, name, 2.2, ha="left" if k > 0 else "right")


def section_mark(sh, fr, m):
    """Cutting planes of sections R1 (upper side band, XK-PLATE) and R2 (lower side band, XK-PLATE-H) across a rib."""
    for name, x, z in (("R1", R1_X, 2.1), ("R2", R2_X, 0.55)):
        cutting_plane(sh, fr, name, x, z)
    return []


def cutting_plane(sh, fr, name, x, z):
    A, B = fr.P(x - 0.45, z), fr.P(x + 0.45, z)
    sh.line([A, B], 0.25, INK, ls="-.", z=21)
    for P_ in (A, B):
        sh.line([(P_[0] - 2.5 if P_ is A else P_[0], P_[1]), (P_[0] if P_ is A else P_[0] + 2.5, P_[1])], 0.7, INK, z=21)
        sh.ax.annotate("", xy=(P_[0], P_[1] - 3.2), xytext=(P_[0], P_[1]), zorder=21,
                       arrowprops=dict(arrowstyle="-|>", lw=0.25 * PT, color=INK, mutation_scale=5, shrinkA=0, shrinkB=0))
        sh.t(P_[0] + (-3.2 if P_ is A else 1.2), P_[1] + 0.8, name, 2.6, weight="bold", z=22, bg="white")


def panel_number_sample(sh, fr, m):
    """D-R-PANEL-NUMBERS (proposed rule): the plate's number in its lower aft corner, 3,4 cm letters, here on one."""
    e = m.by_id.get("P-S-L10")
    rule = m.by_id.get("D-R-PANEL-NUMBERS")
    if not e or not rule:
        return []
    x0, z0, x1, z1 = e.sb["shape"].bounds
    cut = LineString([(x0 + 0.06, z0 - 1), (x0 + 0.06, z1 + 1)]).intersection(e.sb["shape"])
    zb = cut.bounds[1] if not cut.is_empty else z0
    X, Y = fr.P(x0 + 0.04, zb + 0.04)
    sh.t(X, Y, "L10", 0.034 * fr.s / 0.72, STATUS_COL["proposed"], z=23)
    return [{"id": rule.id, "text": rule.id + " + (vzor)", "anchor": (X + 1.0, Y + 0.6), "col": STATUS_COL["proposed"],
             "z": zb, "hidden": False}]


def detail_dims(sh, fr, m, Y0d):
    """Detail A: the pod's length and its ring bands as a chain dimension under the frame, the fin tip level."""
    rev = m.recipe["parts"]["pod"]["revolve"]
    xs = [rev["sections"][0]["x"][0]]
    for s in rev["sections"]:
        xs.append(s["x"][1])
    y = Y0d - 6.0
    ybot = fr.P(0, POD_CY_DRAW - 0.95)[1]
    for x in xs:
        X, _ = fr.P(x, 0)
        sh.line([(X, max(ybot - 1, Y0d)), (X, y - 1.8)], 0.13, INK, z=20)
    for a, b in zip(xs, xs[1:]):
        Xa, Xb = fr.P(a, 0)[0], fr.P(b, 0)[0]
        sh.ax.annotate("", xy=(Xa, y), xytext=(Xb, y), zorder=20, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t((Xa + Xb) / 2, y + 0.8, ("%.2f" % (b - a)).replace(".", ","), 2.2, ha="center", bg="white", z=21)
    sh.t(fr.P(xs[-1], 0)[0] + 2, y - 0.8, "gondola %s (x %s … %s)" % (("%.2f" % (xs[-1] - xs[0])).replace(".", ","),
                                                                      em.fmt(xs[0]), em.fmt(xs[-1])), 2.2)
    # fin tip level
    ztip = max(p[1] for p in m.side["fin"])
    X, Y = fr.P(2.35, ztip)
    sh.line([(X, Y), (X + 22, Y)], 0.18, INK, z=20)
    sh.ax.add_patch(MplPolygon([(X + 18, Y), (X + 16.8, Y + 1.6), (X + 19.2, Y + 1.6)], closed=True, fc=INK, ec="none", zorder=20))
    sh.t(X + 20.5, Y + 0.8, "+%s špička ploutve" % em.fmt(ztip), 2.2, z=21, bg="white")


POD_CY_DRAW = em.POD_CY
R1_X = 11.6                            # station of the rib that section R1 cuts (upper side band)
R2_X = 12.8                            # and section R2 (lower side band)


def dim_h(sh, xa, xb, y, text, ya, yb):
    sh.line([(xa, ya - 1), (xa, y - 1.5)], 0.13)
    sh.line([(xb, yb - 1), (xb, y - 1.5)], 0.13)
    sh.ax.annotate("", xy=(xa, y), xytext=(xb, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color=INK,
                                                                    mutation_scale=4, shrinkA=0, shrinkB=0), zorder=20)
    sh.t((xa + xb) / 2, y + 0.8, text, 2.5, ha="center", bg="white")


def dim_v(sh, x, ya, yb, text, xa, xb):
    sh.line([(xa + 1, ya), (x + 1.5, ya)], 0.13)
    sh.line([(xb + 1, yb), (x + 1.5, yb)], 0.13)
    sh.ax.annotate("", xy=(x, ya), xytext=(x, yb), arrowprops=dict(arrowstyle="<|-|>", lw=0.18 * PT, color=INK,
                                                                    mutation_scale=4, shrinkA=0, shrinkB=0), zorder=20)
    sh.t(x - 0.8, (ya + yb) / 2, text, 2.5, ha="right", va="center", rot=90, bg="white")


def legend(sh, m, x, ytop):
    sh.t(x, ytop - 1, "LEGENDA", 3.8, weight="bold")
    y = ytop - 8
    sh.t(x, y, "Materiálové zóny (koncept B + C)", 2.8, weight="bold")
    y -= 5.6
    d = Drawer(sh, m)
    for mat in m.design["materials"]:
        fill, hatch, hc = d.matstyle(mat["id"])
        sh.geom(box(x, y - 1.3, x + 12, y + 3.3), fc=fill, ec=INK, lw=0.18, hatch=hatch, hatch_col=hc, z=5)
        sh.t(x + 14, y, mat["id"], 2.2, STATUS_COL[mat["status"]])
        sh.t(x + 42, y, mat["name"], 2.2, weight="bold")
        sh.t(x + 76, y, ("slot %s" % mat["recipe"]) + (" (hotový)" if mat["status"] == "built" else " (nový)"), 2.0, GREY)
        for i, ln in enumerate(wrap(sh, mat["what"], 2.0, 130, 2)):
            sh.t(x + 108, y + 0.9 - i * 2.6, ln, 2.0)
        SCHEDULED.setdefault("materials", set()).add(mat["id"])
        y -= 6.4
    y -= 1.6
    sh.t(x, y, "Pásy desek na boku: P-S-<pás><pole>, pole = mezi příčkami (čísla nad pohledem A)", 2.8, weight="bold")
    y -= 5.0
    for b in m.panel_spec["bands"]:
        k = m.kit[b["kit"]]
        sh.t(x, y, b["band"], 2.6, STATUS_COL["proposed"], weight="bold")
        sh.t(x + 5, y, "%s: v %s až %s výšky průřezu, na příčce %s z %s … %s" % (
            b["name"], exact(b["v"][0]), exact(b["v"][1]), em.fmt(R1_X), em.fmt(m.z_of(R1_X, b["v"][0])),
            em.fmt(m.z_of(R1_X, b["v"][1]))), 2.3)
        sh.t(x + 150, y, "%s, %s" % (k["id"], b["material"]), 2.3, STATUS_COL["proposed"])
        y -= 4.4
    roof = m.design["panels"].get("roof")
    if roof:
        k = m.kit[roof["kit"]]
        sh.t(x, y, roof["band"], 2.6, STATUS_COL["proposed"], weight="bold")
        sh.t(x + 5, y, "%s: od osy (páteř ± %s) přes hranu střechy k v %s, x %s–%s; P-S-RL / RP <pole> vlevo / vpravo" % (
            roof["name"], em.fmt(roof["spine_gap"]), exact(roof["v_edge"]), em.fmt(roof["x"][0]), em.fmt(roof["x"][1])), 2.3)
        sh.t(x + 150, y, "%s, %s" % (k["id"], roof["material"]), 2.3, STATUS_COL["proposed"])
        y -= 4.4
    y -= 1.8
    sh.t(x, y, "Stav prvku", 2.8, weight="bold")
    y -= 5.0
    rows = (("built", "postaveno (je v datech stavby)"), ("proposed", "+ návrh (data návrhu, zatím nepostaveno)"),
            ("change", "Δ změna postaveného: stará poloha červeně čárkovaně, šipka k nové"),
            ("remove", "× odstranit (postavené, návrh ho ruší)"))
    for st, txt in rows:
        if st == "change":
            sh.line([(x, y + 0.8), (x + 4.5, y + 0.8)], 0.5, STATUS_COL["remove"], ls="--")
            sh.ax.annotate("", xy=(x + 7, y + 0.8), xytext=(x + 4.6, y + 0.8), zorder=20, arrowprops=dict(
                arrowstyle="-|>", lw=0.25 * PT, color=STATUS_COL["change"], mutation_scale=4, shrinkA=0, shrinkB=0))
            sh.line([(x + 7.2, y + 0.8), (x + 12, y + 0.8)], 0.5, STATUS_COL["change"])
        else:
            sh.line([(x, y + 0.8), (x + 12, y + 0.8)], 0.5, STATUS_COL[st], ls="--" if st == "remove" else "-")
        sh.t(x + 15, y, txt, 2.2, STATUS_COL[st])
        y -= 4.4
    sh.line([(x, y + 0.8), (x + 12, y + 0.8)], 0.3, INK, ls="--")
    sh.t(x + 15, y, "čárkovaně: skryté za bližším dílem; tečkovaná odkazová čára = skrytý prvek", 2.2)
    y -= 4.4
    sh.t(x + 15, y, "kit poklopy (G) leží vždy na trupu; ostatní prvky „z boku“ na nejbližším dílu (kontrola dat)", 2.2)
    y -= 5.6
    sh.t(x, y, "Značky", 2.8, weight="bold")
    y -= 5.6
    items = [("lens", "čočka bez zdroje"), ("point", "bodové světlo"), ("spot", "reflektor (kužel)"),
             ("flash", "záblesk"), ("strip", "světelný pás"), ("decal", "decal (rámeček = velikost z knihovny)")]
    for i, (k, txt) in enumerate(items):
        X = x + (i % 3) * 76
        Y = y - (i // 3) * 7
        if k == "lens":
            d.lamp(X + 3, Y + 0.8, "#F2A100", INK, None, lens_only=True)
        elif k == "point":
            d.lamp(X + 3, Y + 0.8, "#2E9E44", INK, {"type": "point"})
        elif k == "spot":
            d.lamp(X + 3, Y + 1.6, "#FFFFFF", INK, {"type": "spot", "cone_deg": 40, "aim_down_deg": 30})
        elif k == "flash":
            d.lamp(X + 3, Y + 0.8, "#FFFFFF", STATUS_COL["proposed"], {"type": "point", "flash_hz": 1})
        elif k == "strip":
            sh.line([(X, Y + 0.8), (X + 7, Y + 0.8)], 1.1, INK)
            sh.line([(X, Y + 0.8), (X + 7, Y + 0.8)], 0.75, "#8FD3FF")
        else:
            sh.geom(box(X, Y - 0.6, X + 7, Y + 2.2), fc="#F3ECFA", ec=INK, lw=0.2)
        sh.t(X + 9, Y, txt, 2.2)
    y -= 13
    sh.t(x, y, "Zrcadlené prvky mají jedno ID pro oba boky (ks = na celé lodi). Rozměry v metrech, tloušťky v mm;", 2.2, GREY)
    y -= 3.6
    sh.t(x, y, "x od zádi, z od paluby. Pohled v tabulkách: B bok, H hřbet, S spodek, Z záď, M mezera gondola–trup.", 2.2, GREY)
    return y - 4


def exact(v):
    return ("%.3f" % v).rstrip("0").rstrip(".").replace(".", ",")


def section(sh, m, x, ytop, name, kit_id, band):
    """Section through two side plates of a kit either side of a rib (XK-RIB), 1:5 - the kit's own numbers:
    thickness, bevel, gap to the rib, rib width and height, the bolts' centrelines."""
    s = 1000.0 / 5.0
    plate, rib, p = m.kit[kit_id], m.kit["XK-RIB"], m.panel_spec
    t, bev, rw, rh, gap = plate["t"], plate["bevel"], rib["w"], rib["h"], p["gap"]
    rib_x = R1_X if name == "R1" else R2_X
    sh.t(x, ytop - 3, "ŘEZ %s – %s %s, PÁS %s  1 : 5" % (name, kit_id, plate["name"].upper(), band), 2.8, weight="bold")
    cx, y0 = x + 70, ytop - 24.0
    half = 0.32
    sh.geom(box(cx - half * s, y0 - 4, cx + half * s, y0), fc="#7E848B", ec=INK, lw=0.25, hatch="x", hatch_col="#D0D0D0", z=5)
    sh.geom(box(cx - rw / 2 * s, y0, cx + rw / 2 * s, y0 + rh * s), fc="#5E646B", ec=STATUS_COL["proposed"], lw=0.3, z=6)
    for sgn in (-1, 1):
        e0 = cx + sgn * (rw / 2 + gap) * s
        e1 = cx + sgn * half * s
        pts = [(e0, y0), (e1, y0), (e1, y0 + t * s), (e0 + sgn * bev * s, y0 + t * s), (e0, y0 + (t - bev) * s)]
        sh.geom(Polygon(pts), fc="#F2EDE3", ec=STATUS_COL["proposed"], lw=0.35, z=6)
        if "bolt_edge" in plate:                      # bolt centreline at bolt_edge from the plate edge
            bx = e0 + sgn * plate["bolt_edge"] * s
            sh.line([(bx, y0 - 3), (bx, y0 + t * s + 2.5)], 0.18, INK, ls="-.", z=7)
            r = plate["bolt_d"] / 2 * s
            sh.line([(bx - r, y0 + t * s), (bx + r, y0 + t * s)], 0.6, INK, z=7)
    st = [p["ends"][0]] + m.seams + [p["ends"][1]]
    i = st.index(rib_x)
    sh.t(cx - half * s, y0 + t * s + 7, "%s (P-S-%s%02d)" % (kit_id, band, i), 2.3, STATUS_COL["proposed"])
    sh.t(cx + 9, y0 + t * s + 7, "%s (P-S-%s%02d)" % (kit_id, band, i + 1), 2.3, STATUS_COL["proposed"])
    sh.t(cx - half * s, y0 - 7.5, "plášť P-HULL (MZ-GUNMETAL), žebro XK-RIB na příčce %s" % em.fmt(rib_x), 2.3)

    def dim(xa, xb, yy, text):
        sh.ax.annotate("", xy=(xa, yy), xytext=(xb, yy), zorder=20, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=3.5, shrinkA=0, shrinkB=0))
        sh.t((xa + xb) / 2, yy + 0.7, text, 2.3, ha="center", z=21)

    yy = y0 + t * s + 3.2
    dim(cx - rw / 2 * s, cx + rw / 2 * s, yy, "%d" % round(rw * 1000))
    dim(cx + rw / 2 * s, cx + (rw / 2 + gap) * s, yy, "%d" % round(gap * 1000))
    dim(cx - (rw / 2 + gap) * s, cx - rw / 2 * s, yy, "%d" % round(gap * 1000))
    xv = cx - half * s - 3
    sh.ax.annotate("", xy=(xv, y0), xytext=(xv, y0 + t * s), zorder=20, arrowprops=dict(
        arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=3.5, shrinkA=0, shrinkB=0))
    sh.t(xv - 1.2, y0 + t * s / 2 - 0.8, "%d" % round(t * 1000), 2.3, ha="right")
    txt = "žebro %d mm nad pláštěm, zkosení %d mm" % (round(rh * 1000), round(bev * 1000))
    if "bolt_d" in plate:
        txt += "; šrouby Ø %d po %d mm, %d mm od hrany" % (round(plate["bolt_d"] * 1000), round(plate["bolt_pitch"] * 1000),
                                                           round(plate["bolt_edge"] * 1000))
    sh.t(cx - half * s, y0 - 11.5, txt + " (mm)", 2.3)


def concept_strip(sh, m, x, ytop, width=135.0):
    """The author's chosen surface concept (design data "concept"): the images the panel layout follows."""
    from PIL import Image
    c = m.design["concept"]
    sh.t(x, ytop - 3, "Koncept %s (%s)" % (c["id"], c["decided"]), 2.8, weight="bold")
    files = c["files"]
    gap = 4.0
    wimg = (width - gap * (len(files) - 1)) / len(files)
    y1 = ytop - 6.5
    for i, f in enumerate(files):
        im = Image.open(os.path.join(em.ROOT, f)).convert("RGB")
        im = im.crop((0, 0, im.width, im.height // 2))
        im.thumbnail((900, 900))
        h = wimg * im.height / im.width
        x0 = x + i * (wimg + gap)
        sh.ax.imshow(im, extent=(x0, x0 + wimg, y1 - h, y1), zorder=5, interpolation="lanczos")
        sh.rect(x0, y1 - h, x0 + wimg, y1, ec=INK, lw=0.18, z=6)
        tag = os.path.basename(f).split("_")[1]
        for k, ln in enumerate(wrap(sh, "%s: %s" % (tag, c["take_" + tag]), 2.3, wimg, 4)):
            sh.t(x0, y1 - h - 3.6 - k * 3.1, ln, 2.3)
    sh.ax.set_xlim(0, sh.w)
    sh.ax.set_ylim(0, sh.h)


def stav(e):
    """The status for a table, with a tick when the author approved the change (design data "approved")."""
    return STATUS_CZ[e.status] + (" ✓" if getattr(e, "approved", False) else "")


def views(e):
    return "".join(VIEW_SHORT[v] for v in ("SB", "PORT", "TOP", "BOT", "AFT", "FWD", "GAP") if v in e.views)


def schedules(sh, d, m, x, ytop):
    status = stav

    def note(e):
        return e.why or e.purpose or e.what

    F = [e for e in m.elements if e.cat in ("functional", "part") and not e.id.startswith("P-")]
    G = [e for e in m.elements if e.cat == "greeble"]
    L = [e for e in m.elements if e.cat == "light"]
    R = [e for e in m.elements if e.cat == "rule"]
    K = [e for e in m.elements if e.cat == "kit"]
    cols = [("ID", 29, "left"), ("prvek", 29, "left", 2), ("umístění", 36, "left", 2), ("ks", 7, "right"),
            ("stav", 18, "left"), ("pohled", 12, "left"), ("účel / poznámka", 45, "left", 5)]

    def grouped(items):
        """Consecutive removed items with the same reason share one row (all their IDs stay listed)."""
        rows, i = [], 0
        while i < len(items):
            e = items[i]
            j = i
            if e.status == "remove":
                while j + 1 < len(items) and items[j + 1].status == "remove" and items[j + 1].name == e.name:
                    j += 1
            grp = items[i:j + 1]
            if len(grp) > 2:
                ident = "%s až %s" % (grp[0].id, grp[-1].id.split("-")[-1])
                rows.append(([ident, e.name, "různá místa (%d)" % len(grp), sum(g.qty for g in grp), status(e),
                              " ".join(sorted({views(g) for g in grp})), "spec 8× TR1: bloky navíc"], STATUS_COL[e.status]))
            else:
                for g in grp:
                    rows.append(([g.id, g.name, g.where, g.qty, status(g), views(g),
                                  ((g.kit + " ") if g.kit and g.kit.startswith("XK") else "") + note(g)], STATUS_COL[g.status]))
            i = j + 1
        return rows

    rcs = "RCS po návrhu %d bloků, spec %s" % (m.rcs_blocks(), m.spec_rcs())
    table(sh, x, ytop, "FUNKČNÍ PRVKY (F) – %s" % rcs, cols, grouped(F))
    SCHEDULED["functional"] = {e.id for e in F}
    x2 = x + sum(c[1] for c in cols) + 5
    table(sh, x2, ytop, "POKLOPY, MŘÍŽKY, SENZORY, KRYTY (G)", cols,
          [([e.id, e.name, e.where, e.qty, status(e), views(e), note(e)], STATUS_COL[e.status]) for e in G])
    SCHEDULED["greebles"] = {e.id for e in G}
    x3 = x2 + sum(c[1] for c in cols) + 5
    colsL = [("ID", 34, "left"), ("typ", 26, "left", 2), ("barva", 21, "left", 2), ("intenzita", 38, "left", 2),
             ("umístění", 34, "left", 3), ("ks", 7, "right"), ("stav", 18, "left")]

    def ltype(e):
        return LIGHT_TYPE_CZ.get(e.data.get("name"), e.name)

    y3 = table(sh, x3, ytop, "SVĚTLA (L)", colsL, [([e.id, ltype(e), COLOR_CZ.get(e.extra.get("color"), ""),
                                                     light_desc(e), e.where, e.qty, status(e)], STATUS_COL[e.status]) for e in L])
    SCHEDULED["lights"] = {e.id for e in L}
    colsK = [("ID", 30, "left"), ("díl kitu", 36, "left", 2), ("z", 6, "left"), ("popis", 106, "left", 3)]
    y3 = table(sh, x3, y3 - 4, "EXTERIÉROVÝ KIT (XK) – návrh", colsK,
               [([e.id, e.name, e.data.get("from", ""), e.what], STATUS_COL[e.status]) for e in K])
    SCHEDULED["kit"] = {e.id for e in K}
    y4 = decal_schedule(sh, m, x3 + sum(c[1] for c in colsL) + 5, ytop)
    grime_schedule(sh, m, x3 + sum(c[1] for c in colsL) + 5, y4 - 4)


def decal_schedule(sh, m, x, ytop):
    D = [e for e in m.elements if e.cat in ("decal", "trim")]
    cols = [("ID", 36, "left"), ("knihovna", 30, "left", 2), ("velikost", 19, "left"), ("umístění", 30, "left", 2),
            ("ks", 7, "right"), ("stav", 18, "left"), ("čte", 9, "left"), ("účel / poznámka", 47, "left", 5)]

    def up(e):
        u = e.extra.get("up")
        if not e.extra.get("text") or u is None:
            return ""
        return "ano" if u[1] > 0.5 else "NE"

    def size(e):
        s = e.extra.get("size")
        return "%s×%s" % (em.fmt(s[0]), em.fmt(s[1])) if s else "pás"

    rows = [([e.id, e.extra.get("item", e.name).replace("D_Big_", "velký "), size(e), e.where, e.qty, stav(e),
              up(e), e.why or e.purpose or e.what], STATUS_COL[e.status]) for e in D]
    SCHEDULED["decals"] = {e.id for e in D}
    return table(sh, x, ytop, "DECALY (D) – všechny pohledy; „čte“: text stojí", cols, rows)


def grime_schedule(sh, m, x, ytop):
    G = [e for e in m.elements if e.cat == "grime"]
    cols = [("ID", 30, "left"), ("druh", 18, "left"), ("kde", 38, "left", 2), ("velikost", 20, "left"), ("stav", 18, "left"),
            ("účel", 72, "left", 2)]
    surface = {"pod": "gondola", "top": "shora", "bottom": "zespodu", "side": "bok", "ray": "ploutev"}

    def size(e):
        s_ = e.data.get("size")
        return "%s×%s" % (em.fmt(s_[0]), em.fmt(s_[1])) if s_ else ""

    def where(e):
        dd = e.data
        if dd.get("on") == "pod":
            return "gondola x %s, %s°" % (em.fmt(dd.get("x", 0)), em.fmt(dd.get("deg", 0)))
        x = dd["x"] if "x" in dd else (dd.get("at") or [None])[0]
        return "%s x %s" % (surface.get(dd.get("on"), dd.get("on", "")), em.fmt(x)) if x is not None else dd.get("on", "")

    rows = [([e.id, e.data.get("kind", ""), where(e), size(e), stav(e), e.why or e.purpose or e.what], STATUS_COL[e.status])
            for e in G]
    SCHEDULED["grime"] = {e.id for e in G}
    return table(sh, x, ytop, "ŠPÍNA (karty špíny, D-G)", cols, rows)


def changes_box(sh, m, x, ytop):
    ch = [e for e in m.elements if e.status in ("change", "remove") and e.cat not in ("decal", "trim")]
    cols = [("ID", 32, "left"), ("akce", 18, "left"), ("změna (postaveno → návrh)", 130, "left", 3), ("důvod", 186, "left", 3)]
    rows, i = [], 0
    while i < len(ch):
        e = ch[i]
        j = i
        while e.status == "remove" and j + 1 < len(ch) and ch[j + 1].status == "remove" and ch[j + 1].name == e.name \
                and ch[j + 1].cat == e.cat and e.cat == "functional":
            j += 1
        grp = ch[i:j + 1]
        if len(grp) > 2:
            rows.append((["%s až %s" % (grp[0].id, grp[-1].id.split("-")[-1]), stav(e),
                          "%d× %s, %d bloků na lodi" % (len(grp), e.name, sum(g.qty for g in grp)), "spec 8× TR1 "
                          "(4 kolem přídě, 2 na gondolu): bloky navíc"], STATUS_COL[e.status]))
        else:
            for g in grp:
                what = m.change_text(g) if g.status == "change" else "%s, %s" % (g.name, g.where)
                if g.extra.get("replaced_by"):
                    what += " → " + ", ".join(g.extra["replaced_by"])
                rows.append(([g.id, stav(g), what, g.why], STATUS_COL[g.status]))
        i = j + 1
    y = table(sh, x, ytop, "ZMĚNY A ODSTRANĚNÍ POSTAVENÉHO (decaly v tabulce D)", cols, rows)
    SCHEDULED["changes"] = {e.id for e in ch}
    y -= 4
    sh.t(x, y - 3.4, "KONTROLA DAT (model výkresu: kam co dopadá, co je skryté, výřezy v deskách, podklad nápisů)", 3.2,
         weight="bold")
    y -= 8.8
    for ident, items in m.conflicts().items():
        txt = "%s: %s" % (ident, "; ".join(t for _, t in items))
        for k, ln in enumerate(wrap(sh, txt, 2.5, 360, 2)):
            sh.t(x + (0 if k == 0 else 3), y, ("• " if k == 0 else "") + ln, 2.5)
            y -= 3.9
    port = m.port_text_decals()
    txt = ("Levobok (zrcadlo pravoboku, vlastní list později): %s – text stojí nahoru. Decaly receptu staví hs_decals na "
           "obou bocích čitelně (x doprava od diváka, nahoru po povrchu)." % ", ".join(
               "%s %s" % (i, "ano" if ok else "NE") for i, ok in port))
    for k, ln in enumerate(wrap(sh, txt, 2.5, 360, 3)):
        sh.t(x + (0 if k == 0 else 3), y, ("• " if k == 0 else "") + ln, 2.5)
        y -= 3.9
    return y


def rules_table(sh, m, x, ytop):
    R = [e for e in m.elements if e.cat == "rule"]
    colsR = [("ID", 48, "left"), ("stav", 18, "left"), ("pravidlo", 300, "left", 2)]
    y = table(sh, x, ytop, "PRAVIDLA DECALŮ", colsR,
              [([e.id, stav(e), e.why or e.purpose or e.what], STATUS_COL[e.status]) for e in R])
    SCHEDULED["rules"] = {e.id for e in R}
    return y


SHEET_SCALE = {"E-01": "1:30, detail 1:20, řezy 1:5", "E-02": "tabulky", "E-03": "1:30", "E-04": "1:30",
               "E-05": "1:20", "E-06": "1:30", "E-07": "1:20 a 1:10", "E-08": "1:10, řez 1:5"}


def title_block(sh, m, x, W, sheet="E-01"):
    """Title block: ship and sheet, scale, sheet number, revision table, data digests and the approval fields."""
    x1 = W - 10
    y0, y1 = 10, 114
    sh.rect(x, y0, x1, y1, ec=INK, lw=0.5, z=50)
    sh.t(x + 3, y1 - 6, "GAMESPACE  ·  HALCYON FREIGHTWORKS", 2.5, GREY)
    sh.t(x + 3, y1 - 13, "WAYFARER – návrh exteriéru (dossier bod 3)", 4.8, weight="bold")
    sh.t(x + 3, y1 - 20, SHEETS[sheet][1], 3.2)
    sh.t(x + 3, y1 - 25.5, "Koncept %s: %s" % (m.design["concept"]["id"], m.design["concept"]["name"]), 2.4)
    ya = y1 - 29
    sh.line([(x, ya), (x1, ya)], 0.25, z=50)
    codes = list(SHEETS)
    cells = [("List", "%s, %d / %d" % (sheet, codes.index(sheet) + 1, len(codes))), ("Revize", m.design["revision"]),
             ("Měřítko", SHEET_SCALE.get(sheet, "1:30")), ("Formát", "A0 na šířku"), ("Datum", "1. 10. 2026"),
             ("Stav", "SCHVÁLENO, REV. %s" % m.design["revision"])]
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
    for i, (k, v) in enumerate((("Kreslil", "Claude (skript draw_exterior_sheet.py), 1. 10. 2026"),
                                ("Kontroloval", "kritik technických výkresů, 1. 10. 2026"),
                                ("Schválil", "autor %s (E-01 až E-08, rám rampy); hřbet R podle jeho pokynu" %
                                 m.design["approved"]["drawings"]["date"]))):
        cx = x + i * cw
        sh.t(cx + 2, yb - 3.8, k, 2.0, GREY)
        for j, ln in enumerate(wrap(sh, v, 2.3, cw - 4, 2)):
            sh.t(cx + 2, yb - 8.4 - j * 3.0, ln, 2.3)
        if i:
            sh.line([(cx, yb), (cx, yb - 14)], 0.25, z=50)
    yr = yb - 14
    sh.line([(x, yr), (x1, yr)], 0.25, z=50)
    sh.t(x + 2, yr - 3.8, "Revize", 2.0, GREY)
    sh.t(x + 2, yr - 8.2, "A  1. 10. 2026  vzorový list E-01", 2.4)
    sh.t(x + 85, yr - 8.2, "B  tabulky E-02, schválené změny (✓), listy E-03 až E-08", 2.4)
    sh.t(x + 225, yr - 8.2, "C  schváleno; hřbet R v primárním laku, rám rampy", 2.4)
    yd = yr - 11
    sh.line([(x, yd), (x1, yd)], 0.25, z=50)
    dg = m.digests
    sh.t(x + 2, yd - 4.2, "Data (sha1): layout %s · hs %s · setup %s · návrh %s · spec %s · knihovna %s" % (
        dg["layout"], dg["recipe"], dg["setup"], dg["design"], dg["spec"], dg["library"]), 2.0)
    sh.t(x + 2, yd - 8.0, "Jeden zdroj dat: výkres obsahuje jen to, co je v datech, a data jen to, co je ve výkresu "
                          "(test Tools/Tests/test_exterior_drawing.py).", 2.0)
    sh.t(x + 2, yd - 11.8, "Nepostavené prvky jsou v Design/%s_exterior_design.json; po schválení se z nich staví "
                           "exteriérový kit." % m.ship, 2.0)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ship", nargs="?", default="Wayfarer")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--sheets", nargs="*", help="only these sheets, e.g. E-03 E-05")
    a = ap.parse_args(argv)
    draw(a.ship, a.dpi, sheets=a.sheets)


if __name__ == "__main__":
    main()
