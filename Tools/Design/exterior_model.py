"""The exterior drawing model of a ship: every element its drawings show, with its ID, status and geometry per view,
made from the same data the ship is built from (author 1. 10. 2026: one source of data - the drawing contains nothing
that is not in the data and the data nothing that is not in the drawing).

Sources (all with "id" keys, Tools/Design/assign_exterior_ids.py):
  Design/<Ship>_layout.json             outlines (the approved 2D design)
  HardSurface/<Ship>_hs.json            built: panels and plates, zones, recesses, greebles, functional parts, lights,
                                        decals (items, trim, grime, rules), gear, wings
  <Ship>_setup.json                     built: the big projected markings (name, registration, logo, hazards)
  Design/<Ship>_exterior_design.json    not built yet: proposed elements, changes and removals of built ones,
                                        material zones and the exterior kit
Statuses: built, proposed (new), change (built, to be changed: "set"), remove (built, to go).

Views: "SB" starboard (x to the right = nose right, z up; layout metres). Geometry is shapely in view coordinates.
Used by Tools/Design/draw_exterior_sheet.py and Tools/Tests/test_exterior_drawing.py (no matplotlib here).
"""
import hashlib
import json
import math
import os
import re

from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import polylabel, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POD_CY = 1.2
MIRROR_DEFAULT = True

# Kit greeble footprints (Tools/Blender/hs_build_part.py build_kit; the same table in hs_decals.py), along x, across
GREEBLE_SIZE = {"hatch_large": (1.1, 0.7, 0.04), "hatch": (0.62, 0.42, 0.05), "vent": (0.42, 0.24, 0.036),
                "sensor": (0.16, 0.1, 0.075), "strip": (0.55, 0.07, 0.025)}
# Functional parts (Tools/Blender/hs_functional.py): footprint along x, across, height above the surface (size 1)
FUNC_SIZE = {"rcs": (0.26, 0.17, 0.05), "blade": (0.2, 0.07, 0.16), "whip": (0.06, 0.06, 0.32),
             "dome": (0.2, 0.2, 0.105), "connector": (0.12, 0.12, 0.04), "hinge": (0.12, 0.05, 0.06)}
KIND_CZ = {"rcs": "blok RCS", "blade": "anténa (čepel)", "whip": "anténa (prut)", "dome": "senzorová kupole",
           "connector": "konektor", "hinge": "závěs klapky", "grille": "šachta s mřížkou", "piston": "hydraulický válec",
           "frame": "rám rampy", "tread": "nášlapné lišty rampy", "hinge_ramp": "pant rampy",
           "conduit": "rozvody", "ventbox": "větrací skříň",
           "hatch": "poklop", "hatch_large": "velký poklop", "vent": "větrací mřížka", "sensor": "senzor",
           "strip": "kryt kabelů", "strobe": "záblesk", "landing": "přistávací světlomet", "work": "pracovní světlo"}
LIGHT_RGB = {"red": "#D32F2F", "green": "#2E9E44", "white": "#FFFFFF", "amber": "#F2A100", "strip": "#8FD3FF",
             "warm": "#FFB54D"}
VIEW_NAMES = {"SB": "pravobok", "PORT": "levobok", "TOP": "shora", "BOT": "zespodu", "FWD": "zepředu", "AFT": "zezadu",
              "GAP": "mezera gondola–trup"}
SOLID_ACC = {"hull": "trup", "pod": "gondolu", "fin": "ploutev", "wing": "křídlo", "gun": "zbraň",
             "missile_rack": "raketnici", "gear_main": "podvozek", "gear_nose": "podvozek"}
SOLID_INS = {"hull": "trupem", "pod": "gondolou", "fin": "ploutví", "wing": "křídlem", "gun": "zbraní",
             "missile_rack": "raketnicí", "gear_main": "podvozkem", "gear_nose": "podvozkem"}
CHANGE_KEY_CZ = {"where.x": "rozsah x", "where.z": "rozsah z", "x": "x", "z": "z", "materials.box": "materiál ploutve",
                 "materials.flap": "materiál kormidla"}
# decal library tags of items that carry lettering (they must read upright)
TEXT_TAGS = {"ext_stencil", "stencil", "small_stencil", "label", "panelno", "reg", "warning", "switch_label"}
# What each view of sheet E-01 (starboard) draws: A plates and material zones, B functional parts, lights, decals
SHEET_E01 = {"A": {"panel", "frame", "zone", "plate", "recess", "section", "part"},
             "B": {"functional", "greeble", "light", "decal", "trim"}}


def _json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def file_digest(path):
    with open(path, "rb") as f:
        return hashlib.sha1(f.read().replace(b"\r\n", b"\n")).hexdigest()[:12]


def span_at(poly, x):
    """Vertical extent (min, max) of a closed polygon [[x, y], ...] at x, or None."""
    vals = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if x0 == x1:
            if abs(x - x0) < 1e-9:
                vals += [y0, y1]
            continue
        if min(x0, x1) - 1e-9 <= x <= max(x0, x1) + 1e-9:
            t = (x - x0) / (x1 - x0)
            vals.append(y0 + t * (y1 - y0))
    return (min(vals), max(vals)) if vals else None


def bolt_columns(x0, x1, edge, pitch):
    """Bolt columns of a plate from x0 to x1: inset by edge at both ends, evenly spaced at most pitch apart (kit pilot
    critic round 1: a doubler's bolts sat to one side when they stepped by pitch from one end)."""
    span = (x1 - edge) - (x0 + edge)
    if span < -1e-9:
        return []
    n = int(math.ceil(span / pitch - 1e-6))
    if n <= 0:
        return [(x0 + x1) / 2]
    return [x0 + edge + span * i / n for i in range(n + 1)]


def largest(geom):
    if geom.is_empty:
        return geom
    if isinstance(geom, Polygon):
        return geom
    polys = [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
    return max(polys, key=lambda g: g.area) if polys else Polygon()


def largest_line(geom):
    """The longest line of a (multi)line geometry."""
    if geom.geom_type == "LineString":
        return geom
    lines = [g for g in getattr(geom, "geoms", []) if g.geom_type == "LineString"]
    return max(lines, key=lambda g: g.length) if lines else geom


def polys_only(geom):
    if geom.is_empty:
        return Polygon()
    if isinstance(geom, (Polygon, MultiPolygon)):
        return geom
    polys = [g for g in getattr(geom, "geoms", []) if isinstance(g, (Polygon, MultiPolygon))]
    return unary_union(polys) if polys else Polygon()


class Element:
    """One drawn thing with an ID. sb: {"shape": shapely geometry, "kind": area | line | point | profile,
    "anchor": (x, z), "solid": name, "depth": outboard y, "hidden": bool} or None when not in the starboard view."""

    def __init__(self, ident, cat, name, status="built", **kw):
        self.id, self.cat, self.name, self.status = ident, cat, name, status
        self.what = kw.pop("what", "")
        self.material = kw.pop("material", None)
        self.kit = kw.pop("kit", None)
        self.qty = kw.pop("qty", 1)
        self.src = kw.pop("src", "")
        self.data = kw.pop("data", {})
        self.views = kw.pop("views", set())
        self.change = kw.pop("change", None)
        self.why = kw.pop("why", "")
        self.where = kw.pop("where", "")
        self.extra = kw
        self.sb = None
        self.geo = {}               # view -> geometry like sb (exterior_views); sb is the current view's
        self.vextra = {}            # view -> the view's ghost, pod seams and reading direction

    def __repr__(self):
        return "<%s %s %s>" % (self.id, self.cat, self.status)


class Model:
    def __init__(self, ship="Wayfarer"):
        self.ship = ship
        d = os.path.join(ROOT, "ArtSource", "Ships", ship)
        self.paths = {"layout": os.path.join(d, "Design", "%s_layout.json" % ship),
                      "recipe": os.path.join(d, "HardSurface", "%s_hs.json" % ship),
                      "setup": os.path.join(d, "%s_setup.json" % ship),
                      "spec": os.path.join(d, "%s_spec.json" % ship),
                      "design": os.path.join(d, "Design", "%s_exterior_design.json" % ship)}
        self.layout = _json(self.paths["layout"])
        self.recipe = _json(self.paths["recipe"])
        self.setup = _json(self.paths["setup"])
        self.spec = _json(self.paths["spec"])
        self.design = _json(self.paths["design"])
        lib_path = os.path.join(ROOT, self.recipe["decals"]["index"])
        self.paths["library"] = lib_path
        self.library = _json(lib_path)
        self.digests = {k: file_digest(p) for k, p in self.paths.items()}
        self.materials = {m["id"]: m for m in self.design["materials"]}
        self.mat_of_recipe = {m["recipe"]: m["id"] for m in self.design["materials"] if m.get("recipe")}
        self.mat_of_recipe.setdefault("nozzle", "MZ-METAL")
        self.kit = {k["id"]: k for k in self.design["kit"]}
        self.changes = {c["id"]: c for c in self.design.get("changes", [])}
        self.elements = []
        self.by_id = {}
        self._outlines()
        self._solids()
        self._build()
        import exterior_views
        exterior_views.add_views(self)
        self.view = "SB"

    def use_view(self, view):
        """Make a view current (exterior_views): e.sb, e.extra ghost / seams / up, self.solids and self.canopy then
        hold that view's geometry, so the drawing code draws any view as it draws the starboard one."""
        for e in self.elements:
            e.sb = e.geo.get(view)
            vx = e.vextra.get(view, {})
            for k in ("ghost", "seams", "up", "marks"):
                if vx.get(k) is not None:
                    e.extra[k] = vx[k]
                else:
                    e.extra.pop(k, None)
        self.solids = self.view_solids[view]
        self.canopy = self.view_canopy[view]
        self.view = view

    # ------------------------------------------------------------------ geometry of the ship (layout data)
    def _outlines(self):
        ext = self.layout["exterior"]
        self.side = {}
        self.top = {}
        self.front = {}
        for view, store in (("side", self.side), ("top", self.top), ("front", self.front)):
            for e in ext[view]:
                if "poly" in e:
                    store.setdefault(e["part"], e["poly"])
        self.hull_side = self.side["hull"]
        self.hull_top = self.top["hull"]
        fp = self.front["hull"]
        ys, zs = [p[0] for p in fp], [p[1] for p in fp]
        self.f_y = max(abs(min(ys)), abs(max(ys)))
        self.f_z0, self.f_z1 = min(zs), max(zs)
        # normalised front section (u -1..1 across, v 0 keel .. 1 roof), as the hull loft (hs_build_ship.loft)
        self.section = [(p[0] / self.f_y, (p[1] - self.f_z0) / (self.f_z1 - self.f_z0)) for p in fp]
        rev = self.recipe["parts"]["pod"]["revolve"]
        self.pod_axis = (rev["axis"]["y"], rev["axis"]["z"])
        self.pod_profile = rev["profile"]
        self.seams = list(self.recipe["parts"]["hull"]["seams"]["x"])

    def zspan(self, x):
        s = span_at(self.hull_side, min(max(x, 1e-4), 21.0 - 1e-4))
        return s

    def hw(self, x):
        s = span_at(self.hull_top, min(max(x, 1e-4), 21.0 - 1e-4))
        return max(abs(s[0]), abs(s[1])) if s else 0.01

    def z_of(self, x, v):
        zb, zt = self.zspan(x)
        return zb + v * (zt - zb)

    def v_of(self, x, z):
        zb, zt = self.zspan(x)
        return (z - zb) / max(zt - zb, 1e-6)

    def u_out(self, v):
        """Outboard half-width of the normalised section at height v."""
        best = 0.0
        n = len(self.section)
        for i in range(n):
            (u0, v0), (u1, v1) = self.section[i], self.section[(i + 1) % n]
            if min(v0, v1) - 1e-9 <= v <= max(v0, v1) + 1e-9 and v0 != v1:
                t = (v - v0) / (v1 - v0)
                best = max(best, abs(u0 + t * (u1 - u0)))
            elif v0 == v1 and abs(v - v0) < 1e-9:
                best = max(best, abs(u0), abs(u1))
        return best

    def hull_y(self, x, z):
        return self.hw(x) * self.u_out(min(max(self.v_of(x, z), 0.0), 1.0))

    def pod_r(self, x):
        prof = self.pod_profile
        if x <= prof[0][0]:
            return prof[0][1]
        for (x0, r0), (x1, r1) in zip(prof, prof[1:]):
            if x0 <= x <= x1 and x1 > x0:
                return r0 + (x - x0) / (x1 - x0) * (r1 - r0)
        return prof[-1][1]

    def pod_z(self, x, deg, extra=0.0):
        return self.pod_axis[1] + (self.pod_r(x) + extra) * math.sin(math.radians(deg))

    def pod_depth(self, x, deg):
        return self.pod_axis[0] + self.pod_r(x) * math.cos(math.radians(deg))

    def rib_v(self, x):
        """Section heights (v0, v1) the frame rib FR-RIB covers at seam station x: the whole height at the main
        bulkheads ("full"), elsewhere only the shoulder ("v_other"; author 3. 10. 2026, whole-ship kit critic: ribs
        on all 15 stations made the sides read dark)."""
        fr = next((f for f in self.design["frame"] if f["kind"] == "ribs"), None)
        if fr is None or x not in self.seams:
            return None
        full = fr.get("full")
        return tuple(fr["v"]) if full is None or x in full else tuple(fr["v_other"])

    def rib_in_band(self, x, v0, v1):
        """True when the rib at station x crosses the band v0..v1 (the plates there keep off the rib)."""
        r = self.rib_v(x)
        return r is not None and r[0] < v1 and r[1] > v0

    def band_stations(self, band):
        """Stations that bound a side band's plates: the band's x range (default the hull ends) and the seams in it,
        without the seams inside its merged bays."""
        p = self.design["panels"]
        x0, x1 = band.get("x", p["ends"])
        inner = {s for s in self.seams for a, b in band.get("merge", []) if a < s < b}
        return [x0] + [s for s in self.seams if x0 < s < x1 and s not in inner] + [x1]

    def bay_no(self, x):
        """Bay number of the bay that starts at x (counted between the hull ends and all seams, as the IDs)."""
        p = self.design["panels"]
        return sum(1 for s in [p["ends"][0]] + self.seams if s <= x + 1e-9)

    def hull_band(self, x0, x1, v0, v1, step=0.1):
        xs = {x0, x1}
        xs |= {p[0] for p in self.hull_side if x0 < p[0] < x1}
        k = math.floor(x0 / step) + 1
        while k * step < x1:
            xs.add(round(k * step, 6))
            k += 1
        xs = sorted(xs)
        lower = [(x, self.z_of(x, v0)) for x in xs]
        upper = [(x, self.z_of(x, v1)) for x in reversed(xs)]
        return Polygon(lower + upper).buffer(0)

    def section_hit(self, x, y0, z0, dy, dz):
        """First hit of a ray (dx = 0) with the hull section at station x (port side coordinates)."""
        zb, zt = self.zspan(x)
        hw = self.hw(x)
        pts = [(u * hw, zb + v * (zt - zb)) for u, v in self.section]
        best = None
        n = len(pts)
        L = math.hypot(dy, dz)
        dy, dz = dy / L, dz / L
        for i in range(n):
            (ay, az), (by, bz) = pts[i], pts[(i + 1) % n]
            ey, ez = by - ay, bz - az
            den = dy * ez - dz * ey
            if abs(den) < 1e-12:
                continue
            t = ((ay - y0) * ez - (az - z0) * ey) / den
            s = ((ay - y0) * dz - (az - z0) * dy) / den
            if t > 1e-6 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best[0]):
                nrm = (ez, -ey)
                ln = math.hypot(*nrm)
                best = (t, (y0 + t * dy, z0 + t * dz), (nrm[0] / ln, nrm[1] / ln))
        return best

    def pod_poly(self):
        prof = self.pod_profile
        cy = self.pod_axis[1]
        top = [(x, cy + r) for x, r in prof]
        bot = [(x, cy - r) for x, r in reversed(prof)]
        return Polygon(top + bot).buffer(0)

    def _solids(self):
        """Side-view solids with their outboard depth (|y|) along x, and what of each is visible from starboard."""
        top = self.top

        def from_top(part, const=None):
            if const is not None:
                return lambda x: const
            poly = top[part]
            return lambda x: max((abs(v) for v in (span_at(poly, x) or (0.0, 0.0))), default=0.0)

        def from_front(part):
            m = max(abs(p[0]) for p in self.front[part])
            return lambda x: m

        self.solids = {
            "hull": {"poly": Polygon(self.hull_side).buffer(0), "depth": self.hw, "material": "MZ-PAINT1"},
            "pod": {"poly": self.pod_poly(), "depth": lambda x: self.pod_axis[0] + self.pod_r(x), "material": "MZ-PAINT1"},
            "fin": {"poly": Polygon(self.side["fin"]).buffer(0), "depth": from_top("fin"), "material": "MZ-PAINT1"},
            "wing": {"poly": Polygon(self.side["wing"]).buffer(0), "depth": from_top("wing"), "material": "MZ-PAINT1"},
            "gun": {"poly": Polygon(self.side["gun"]).buffer(0), "depth": from_top("gun"), "material": "MZ-DARK"},
            "missile_rack": {"poly": Polygon(self.side["missile_rack"]).buffer(0), "depth": from_front("missile_rack"),
                             "material": "MZ-DARK"},
            "gear_main": {"poly": Polygon(self.side["gear_main"]).buffer(0), "depth": from_front("gear_main"), "material": "MZ-METAL"},
            "gear_nose": {"poly": Polygon(self.side["gear_nose"]).buffer(0), "depth": from_front("gear_nose"), "material": "MZ-METAL"},
        }
        for name, s in self.solids.items():
            vis = s["poly"]
            x0, _, x1, _ = s["poly"].bounds
            for oname, o in self.solids.items():
                if oname == name or not o["poly"].intersects(s["poly"]):
                    continue
                ox0, oz0, ox1, oz1 = o["poly"].bounds
                a, b = max(x0, ox0), min(x1, ox1)
                cover = []
                k = a
                while k < b - 1e-9:
                    k1 = min(k + 0.05, b)
                    xm = (k + k1) / 2
                    if o["depth"](xm) > s["depth"](xm) + 1e-6:
                        cover.append(box(k, oz0 - 1, k1 + 1e-6, oz1 + 1))
                    k = k1
                if cover:
                    vis = vis.difference(o["poly"].intersection(unary_union(cover)))
            s["visible"] = polys_only(vis.buffer(0))
        self.canopy = self._canopy_side()

    def _canopy_side(self):
        """The glass seen from starboard. hs_build_ship.split_canopy makes glass of the hull faces inside BOTH canopy
        outlines (side and top): where the hull is wider than the top outline, the glass ends higher up the shoulder
        than the side outline's lower edge - at the height where the hull's half-width equals the top outline's
        (the plan view showed it, 1. 10. 2026: the side outline alone drew glass over painted hull aft of x 17.6)."""
        side = Polygon(self.side["canopy"]).buffer(0)
        top = [tuple(p) for p in self.top["canopy"]]
        x0, _, x1, _ = side.bounds
        n = 240
        lower = []
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            sp = span_at(top, min(max(x, top[0][0] + 1e-6), max(p[0] for p in top) - 1e-6))
            half = max(abs(sp[0]), abs(sp[1])) if sp else 0.0
            zb, zt = self.zspan(x)
            if self.hw(x) <= half + 1e-6:
                z = zb
            else:
                lo, hi = zb, zt                     # hull_y falls with z on the shoulder: bisect hull_y = half
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if self.hull_y(x, mid) > half:
                        lo = mid
                    else:
                        hi = mid
                z = hi
            lower.append((x, z))
        above = Polygon(lower + [(x1, 10.0), (x0, 10.0)]).buffer(0)
        return polys_only(side.intersection(above).buffer(0))

    def canopy_lower(self, x):
        """Lower edge of the glass seen from starboard at station x (None outside the canopy)."""
        sp = span_at(list(largest(self.canopy).exterior.coords), x)
        return sp[0] if sp else None

    # ------------------------------------------------------------------ elements
    def add(self, el):
        if el.id in self.by_id:
            raise ValueError("duplicate id %s" % el.id)
        ch = self.changes.get(el.id)
        if ch and el.status == "built":
            el.status = "remove" if ch["action"] == "remove" else "change"
            el.change = ch.get("set")
            el.why = ch.get("why", "")
        el.purpose = self.design.get("purpose", {}).get(el.id) or (el.what if el.src == "design" else "")
        el.approved = el.id in set(self.design.get("approved", {}).get("ids", []))
        self.elements.append(el)
        self.by_id[el.id] = el
        return el

    def landing(self, x, z, default="hull"):
        """The solid a ray from beside the ship (starboard) at (x, z) hits first: the nearest one containing the point
        (hs_functional, hs_lights and hs_decals cast against the whole ship; the hull greebles against the hull only)."""
        p = Point(x, z)
        best = None
        for name, s in self.solids.items():
            if name.startswith("gear"):
                continue
            if s["poly"].buffer(0.005).contains(p):
                d = s["depth"](x)
                if best is None or d > best[1]:
                    best = (name, d)
        return best[0] if best else default

    def place(self, el, shape, kind, solid, depth=None, anchor=None):
        """The element's starboard geometry. An area is hidden when almost none of it shows on the visible part of
        its solid; anything else when its anchor lies under a solid nearer the viewer."""
        if shape is None or shape.is_empty:
            return
        vis_part = None
        vis_frac = 1.0
        if kind == "area":
            vis_part = shape.intersection(self.solids[solid]["visible"])
            vis_frac = vis_part.area / shape.area if shape.area > 0 else 1.0
            if vis_part.area < max(0.15 * shape.area, 0.0004) or vis_part.area < 1e-5:
                vis_part = None
        if anchor is None:
            if vis_part is not None:
                a = polys_only(vis_part)
                a = largest(a).representative_point() if not a.is_empty else shape.representative_point()
            else:
                a = shape.representative_point() if kind == "area" else shape.interpolate(0.5, normalized=True) \
                    if kind == "line" else shape.centroid
            anchor = (a.x, a.y)
        if depth is None:
            depth = self.solids[solid]["depth"](anchor[0])
        if kind == "area":
            hidden = vis_part is None
        else:
            hidden = False
            p = Point(anchor)
            for oname, o in self.solids.items():
                if oname != solid and o["poly"].buffer(-0.005).contains(p) and o["depth"](anchor[0]) > depth + 0.02:
                    hidden = True
                    break
        el.sb = {"shape": shape, "kind": kind, "anchor": anchor, "solid": solid, "depth": depth, "hidden": hidden,
                 "vis_frac": vis_frac}
        el.views.add("SB")

    def mat(self, recipe_key):
        return self.mat_of_recipe.get(recipe_key, "MZ-PAINT1")

    def _build(self):
        r, des = self.recipe, self.design
        # materials and kit (legend and parts list rows; they carry IDs too)
        for m in des["materials"]:
            self.add(Element(m["id"], "material", m["name"], m["status"], what=m["what"], src="design", data=m))
        for k in des["kit"]:
            self.add(Element(k["id"], "kit", k["name"], k["status"], what=k["what"], src="design", data=k))
        for key, solid, name in (("hull", "hull", "plášť trupu"), ("pod", "pod", "plášť gondoly")):
            part = r["parts"][key]
            el = self.add(Element(part["id"], "part", name, src="recipe", data=part,
                                  material=self.mat(part.get("material", "paint"))))
            if el.change and "material" in el.change:
                el.material = self.mat(el.change["material"])
            el.qty = 1 if key == "hull" else 2
            el.where = "loft z výkresu" if key == "hull" else "rotace profilu"
            self.place(el, self.solids[solid]["poly"], "area", solid)
        self._zones()
        self._plates()
        self._recesses()
        self._greebles()
        self._functional()
        self._grilles_and_design_functional()
        self._lights()
        self._panels()
        self._shoulder_conduits()
        self._zones_on_panels()
        self._frame()
        self._pod_sections()
        self._decals()

    # zones: built hull zones and the proposed canopy seal
    def _zones(self):
        hull = self.solids["hull"]["poly"]
        for z in self.recipe["parts"]["hull"].get("zones", []):
            el = self.add(Element(z["id"], "zone", z["name"], material=self.mat(z["material"]), src="recipe",
                                  data=z, what=z.get("name", "")))
            w = dict(z["where"])

            def zone_shape(w):
                xs = w.get("x", [-1, 22])
                zs = w.get("z", [-5, 6])
                shape = hull.intersection(box(xs[0], zs[0], xs[1], zs[1]))
                if "normal_abs_y_min" in w:
                    shape = shape.difference(self.canopy.buffer(0.05))
                return polys_only(shape), "x %s–%s" % (fmt(xs[0]), fmt(min(xs[1], 21.0)))

            if el.change and ("where.x" in el.change or "where.z" in el.change):
                el.extra["ghost"], el.extra["ghost_where"] = zone_shape(w)
                w["x"] = el.change.get("where.x", w.get("x"))
                if "where.z" in el.change:
                    w["z"] = el.change["where.z"]
                el.extra["on_panels"] = el.change.get("on") == "panels"
            shape, el.where = zone_shape(w)
            el.qty = 2 if "normal_abs_y_min" in w else 1
            el.views |= {"SB", "PORT"}
            self.place(el, polys_only(shape), "area", "hull", anchor=None)
        for z in self.design.get("zones", []):
            el = self.add(Element(z["id"], "zone", "těsnění kabiny", z["status"], material=z["material"], kit=z["kit"],
                                  src="design", data=z, what=z["what"]))
            ring = self.canopy.buffer(z["w"], join_style=2).difference(self.canopy).intersection(self.solids["hull"]["poly"])
            el.where = "obvod kabiny"
            el.qty = 1
            self.place(el, polys_only(ring), "area", "hull")

    def _zones_on_panels(self):
        """A zone the design paints on the plates (the stripe) covers only the plates' faces, not the frame; a
        removed built plate names the new plates that take its place."""
        panels = [e for e in self.elements if e.cat == "panel" and e.sb]
        for e in self.elements:
            if e.cat == "plate" and e.status == "remove" and e.sb:
                e.extra["replaced_by"] = sorted(p.id for p in panels
                                                if p.sb["shape"].intersection(e.sb["shape"]).area > 0.25 * e.sb["shape"].area
                                                or p.sb["shape"].intersection(e.sb["shape"]).area > 0.25 * p.sb["shape"].area)
        plates = unary_union([e.sb["shape"] for e in panels])
        for e in self.elements:
            if e.cat == "zone" and e.extra.get("on_panels") and e.sb:
                e.where += ", na deskách"
                self.place(e, polys_only(e.sb["shape"].intersection(plates)), "area", "hull")

    def _plates(self):
        hull = self.solids["hull"]["poly"]
        for p in self.recipe["detail"].get("hull_plates", []):
            mat = self.mat(p["material"]) if p.get("material") else ("MZ-PAINT2" if p.get("secondary") else "MZ-PAINT1")
            el = self.add(Element(p["id"], "plate", "deska", material=mat, src="recipe", data=p, what=p.get("_what", "")))
            el.where = "x %s–%s" % (fmt(p["x"][0]), fmt(p["x"][1]))
            side_visible = "z" in p and "normal_x" not in p and not (p.get("normal_z") and min(p["normal_z"]) >= 0.85)
            el.qty = 1 if p.get("centre") else 2
            if side_visible:
                shape = hull.intersection(box(p["x"][0], p["z"][0], p["x"][1], p["z"][1]))
                self.place(el, polys_only(shape), "area", "hull")
            else:
                nz = p.get("normal_z", [0, 0])
                el.views.add("AFT" if "normal_x" in p else ("TOP" if nz[0] > 0 else "BOT"))

    def _recesses(self):
        hull = self.solids["hull"]["poly"]
        for p in self.recipe["detail"].get("hull_recesses", []):
            el = self.add(Element(p["id"], "recess", "zapuštění", material="MZ-DARK", src="recipe", data=p,
                                  what=p.get("_what", "")))
            el.where = "x %s–%s" % (fmt(p["x"][0]), fmt(p["x"][1]))
            el.qty = 1 if p.get("centre") else 2
            if "z" in p and "abs_y" not in p:
                self.place(el, polys_only(hull.intersection(box(p["x"][0], p["z"][0], p["x"][1], p["z"][1]))), "area", "hull")
            else:
                el.views.add("TOP")

    def _greebles(self):
        for g in self.recipe["parts"]["hull"].get("greebles", []):
            sx, sy, h = GREEBLE_SIZE[g["part"]]
            el = self.add(Element(g["id"], "greeble", KIND_CZ[g["part"]], src="recipe", data=g,
                                  what=g.get("_what", ""), material="MZ-PAINT1", kit="kit:" + g["part"]))
            if g["from"] == "side":
                el.qty = 2 if g.get("mirror", True) else 1
                el.where = "bok x %s z %s" % (fmt(g["x"]), fmt(g["z"]))
                self.place(el, box(g["x"] - sx / 2, g["z"] - sy / 2, g["x"] + sx / 2, g["z"] + sy / 2), "area", "hull",
                           depth=self.hull_y(g["x"], g["z"]), anchor=(g["x"], g["z"]))
            else:
                el.qty = 1
                el.where = "%s x %s y %s" % ("hřbet" if g["from"] == "top" else "břicho", fmt(g["x"]), fmt(g.get("y", 0)))
                el.views.add("TOP" if g["from"] == "top" else "BOT")
        rev = self.recipe["parts"]["pod"]["revolve"]
        for g in rev.get("greebles", []):
            sx, sy, h = GREEBLE_SIZE[g["part"]]
            el = self.add(Element(g["id"], "greeble", KIND_CZ[g["part"]], src="recipe", data=g, material="MZ-PAINT1",
                                  kit="kit:" + g["part"], what="na gondole"))
            el.qty = 2
            el.where = "gondola x %s, %s°" % (fmt(g["x"]), fmt(g["angle_deg"]))
            self._place_pod_item(el, g["x"], g["angle_deg"], sx, sy, h)

    def _place_pod_item(self, el, x, deg, w, h, height, rot=0.0, light=False):
        """Something on the pod surface at (x, deg) with footprint w (along x) x h (around): its face when it faces
        the starboard viewer, its profile on the outline at the crown / keel when it stands proud enough."""
        if rot % 180 == 90:
            w, h = h, w
        c = math.cos(math.radians(deg))
        z = self.pod_z(x, deg)
        if c > 0.17:
            hh = max(h * abs(c), 0.01)
            self.place(el, box(x - w / 2, z - hh / 2, x + w / 2, z + hh / 2), "area", "pod",
                       depth=self.pod_depth(x, deg), anchor=(x, z))
        elif abs(c) <= 0.17 and (height >= 0.08 or light):
            s = 1 if math.sin(math.radians(deg)) > 0 else -1
            zr = self.pod_z(x, deg)
            shape = box(x - w / 2, min(zr, zr + s * max(height, 0.02)), x + w / 2, max(zr, zr + s * max(height, 0.02)))
            self.place(el, shape, "profile", "pod", depth=self.pod_axis[0] + 0.5, anchor=(x, zr + s * height / 2))
        else:
            el.views.add("GAP")     # faces inboard: seen only between the pod and the hull

    def _functional(self):
        f = self.recipe["functional"]
        for it in f.get("items", []):
            kind = it["kind"]
            el = self.add(Element(it["id"], "functional", KIND_CZ[kind], src="recipe", data=it, what=it.get("_what", ""),
                                  material="MZ-PAINT1" if kind == "rcs" else "MZ-DARK", kit="func:" + kind))
            el.qty = 2 if it.get("mirror", True) else 1
            self._with_ghost(el, it, self._place_func_item)
        self._functional_parts(f)

    def _with_ghost(self, el, it, placer):
        """Place an item; a changed position also keeps the built one as a ghost (drawn red dashed)."""
        new = dict(it)
        moved = False
        for k, v in (el.change or {}).items():
            if "." not in k and "[" not in k and k not in ("kit", "item"):
                new[k] = v
                moved = True
        if moved:
            ghost = Element("_ghost", el.cat, el.name)
            ghost.extra = dict(el.extra)
            placer(ghost, it)
            if ghost.sb:
                el.extra["ghost"] = ghost.sb["shape"]
                el.extra["ghost_where"] = ghost.where
                el.extra["ghost_lands_on"] = ghost.extra.get("lands_on")
        placer(el, new)

    def _place_func_item(self, el, it):
        kind = it["kind"]
        s = it.get("size", 1.0)
        fx, fy, fh = FUNC_SIZE[kind]
        kit_id = (el.change or {}).get("kit") or it.get("kit")
        if kit_id:
            k = self.kit[kit_id]
            fx, fy, fh = k["size"]
            s = 1.0
            el.kit = k["id"]
        fx, fy, fh = fx * s, fy * s, fh * s
        if True:
            on = it["on"]
            if on == "side":
                el.where = "bok x %s z %s" % (fmt(it["x"]), fmt(it["z"]))
                w, h = (fy, fx) if (it.get("rot", 0) % 180) == 90 else (fx, fy)
                solid = self.landing(it["x"], it["z"])
                if solid != "hull":
                    el.extra["lands_on"] = solid
                self.place(el, box(it["x"] - w / 2, it["z"] - h / 2, it["x"] + w / 2, it["z"] + h / 2), "area", solid,
                           depth=self.hull_y(it["x"], it["z"]) if solid == "hull" else self.solids[solid]["depth"](it["x"]),
                           anchor=(it["x"], it["z"]))
            elif on == "pod":
                el.where = "gondola x %s, %s°" % (fmt(it["x"]), fmt(it["deg"]))
                self._place_pod_item(el, it["x"], it["deg"], fx, fy, fh, it.get("rot", 0.0))
            elif on in ("top", "bottom"):
                el.where = "%s x %s y %s" % ("hřbet" if on == "top" else "břicho", fmt(it["x"]), fmt(it.get("y", 0)))
                el.views.add("TOP" if on == "top" else "BOT")
                if fh >= 0.08:
                    zb, zt = self.zspan(it["x"])
                    zz = zt if on == "top" else zb
                    sgn = 1 if on == "top" else -1
                    if kind == "whip":
                        shape = LineString([(it["x"], zz), (it["x"], zz + sgn * fh)]).buffer(0.012, cap_style=2)
                    elif kind == "dome":
                        shape = Point(it["x"], zz).buffer(fx / 2).intersection(
                            box(it["x"] - 1, zz, it["x"] + 1, zz + fh) if sgn > 0 else box(it["x"] - 1, zz - fh, it["x"] + 1, zz))
                    else:
                        shape = Polygon([(it["x"] - fx / 2, zz), (it["x"] + fx / 2, zz),
                                         (it["x"] + fx / 2 - 0.02, zz + sgn * fh), (it["x"] + fx / 2 - 0.02 - 0.06 * s, zz + sgn * fh)])
                    self.place(el, shape.buffer(0), "profile", "hull", depth=self.hw(it["x"]) + 0.5,
                               anchor=(it["x"], zz + sgn * fh / 2))
            elif on == "ray":
                el.where = "zadní stěna" if it["dir"][0] else "paprsek"
                el.views.add("AFT")

    def _functional_parts(self, f):
        for gm in f.get("gun_mounts", []):
            el = self.add(Element(gm["id"], "functional", "objímky zbraně", src="recipe", data=gm,
                                  what=gm.get("_why", ""), material="MZ-DARK"))
            el.qty = 2 * len(gm["at"])
            el.where = "zbraň x %s" % ", ".join(fmt(a) for a in gm["at"])
            r = gm["r"] + 0.03
            shape = unary_union([box(a - 0.06, gm["z"] - r, a + 0.06, gm["z"] + r) for a in gm["at"]])
            self.place(el, shape, "area", "gun", depth=gm["y"] + r, anchor=(gm["at"][0], gm["z"]))
        # whole parts (gear, gun, missile rack, wing, fin, canopy frame, pod intake / exhaust / bay / pipes)
        g = self.recipe["gear"]
        for key, solid in (("gear_main", "gear_main"), ("gear_nose", "gear_nose")):
            gi = g[key]
            el = self.add(Element(gi["id"], "functional", "hlavní podvozek" if key == "gear_main" else "příďový podvozek",
                                  src="recipe", data=gi, material="MZ-METAL", what=g.get("_comment", "")))
            el.qty = 2 if gi.get("mirror") else 1
            el.where = "x %s y %s, z %s až %s" % (fmt(gi["at"][0]), fmt(gi["at"][1]), fmt(gi["at"][2]),
                                               fmt(self.solids[solid]["poly"].bounds[1]))
            self.place(el, self.solids[solid]["poly"], "area", solid)
        for path, solid, name, mat in ((("parts", "gun"), "gun", "zbraň S3", "MZ-DARK"),
                                       (("parts", "missile_rack"), "missile_rack", "raketnice S2", "MZ-DARK"),
                                       (("wings", "wing"), "wing", "křídlo", "MZ-PAINT1"),
                                       (("wings", "fin"), "fin", "ploutev", "MZ-PAINT1")):
            node = self.recipe[path[0]][path[1]]
            el = self.add(Element(node["id"], "part", name, src="recipe", data=node, material=mat))
            el.qty = 2
            bx = self.solids[solid]["poly"].bounds
            el.where = "x %s–%s, z %s–%s" % (fmt(bx[0]), fmt(bx[2]), fmt(bx[1]), fmt(bx[3]))
            if el.change and "materials.box" in el.change:
                el.material = self.mat(el.change["materials.box"])
            self.place(el, self.solids[solid]["poly"], "area", solid)
        nz = self.recipe["parts"]["nozzle"]
        nzb = self.recipe["parts"]["pod"]["revolve"]["exhaust"].get("nozzle")
        el = self.add(Element(nz["id"], "part", "žhnoucí jádro trysky" if nzb else "žhnoucí dno trysky", src="recipe",
                              data=nzb["core"] if nzb else nz, material="MZ-METAL"))
        el.qty, el.where = 2, "za hrdlem trysky" if nzb else "dno výfuku gondoly"
        el.views.add("AFT")
        if nzb:
            # the nozzle's parts (kit pilot step d): one element each, drawn from behind (E-05) and in detail G
            x_lip = self.recipe["parts"]["pod"]["revolve"]["exhaust"]["x_lip"]
            for key, name, mat in (("collar", "límec trysky", "MZ-METAL"), ("rings", "prstence zvonu", "MZ-METAL"),
                                   ("ribs", "žebra zvonu", "MZ-GUNMETAL"), ("throat", "prstenec hrdla", "MZ-METAL"),
                                   ("plug", "středové těleso", "MZ-METAL"), ("struts", "táhla středového tělesa",
                                                                              "MZ-GUNMETAL")):
                part = nzb[key]
                el = self.add(Element(part["id"], "functional", name, src="recipe", data=part, material=mat,
                                      what=part.get("_what", "")))
                el.qty = 2 * part.get("count", len(part.get("at", [])) or 1)
                el.where = "tryska gondoly, x %s–%s" % (fmt(x_lip), fmt(x_lip + nzb["core"]["x"]))
                el.views.add("AFT")
        cf = self.recipe["canopy_frame"]
        el = self.add(Element(cf["id"], "functional", "rám kabiny", src="recipe", data=cf, material="MZ-PAINT1",
                              what=cf.get("_comment", "")))
        el.qty, el.where = 1, "příčky x %s" % ", ".join(fmt(x) for x in cf["struts_x"])
        w = cf["strut_width"] / 2
        shape = unary_union([self.canopy.intersection(box(x - w, -5, x + w, 6)) for x in cf["struts_x"]])
        self.place(el, polys_only(shape), "area", "hull", anchor=(cf["struts_x"][0], self.canopy.intersection(
            box(cf["struts_x"][0] - w, -5, cf["struts_x"][0] + w, 6)).centroid.y))
        rev = self.recipe["parts"]["pod"]["revolve"]
        ex = rev["exhaust"]
        el = self.add(Element(ex["id"], "functional", "výfuk gondoly", src="recipe", data=ex, material="MZ-METAL",
                              what="výfukový límec a kužel"))
        el.qty, el.where = 2, "x %s" % fmt(ex["x_lip"])
        self.place(el, self.pod_poly().intersection(box(ex["x_lip"], -5, ex["x_lip"] + 0.12, 6)), "area", "pod",
                   anchor=(ex["x_lip"] + 0.06, POD_CY - 0.3))
        it = rev["intake"]
        el = self.add(Element(it["id"], "functional", "sání gondoly", src="recipe", data=it, material="MZ-DARK",
                              what="sání s nábojem a %d žebry" % it["spokes"]))
        el.qty, el.where = 2, "x %s" % fmt(it["x_lip"])
        self.place(el, box(it["x_lip"] - 0.05, POD_CY - it["r_lip"], it["x_lip"], POD_CY + it["r_lip"]), "area", "pod")
        bay = self.recipe["detail"]["pod"]["bay"]
        el = self.add(Element(bay["id"], "functional", "otevřená šachta gondoly", src="recipe", data=bay,
                              material="MZ-DARK", what=bay.get("_what", "")))
        el.qty, el.where = 2, "x %s–%s, %s–%s°" % (fmt(bay["x"][0]), fmt(bay["x"][1]), fmt(bay["deg"][0]), fmt(bay["deg"][1]))
        self.place(el, self._pod_patch(bay["x"], bay["deg"]), "area", "pod")
        pr = self.recipe["detail"]["pod"]["pipe_run"]
        el = self.add(Element(pr["id"], "functional", "potrubí gondoly", src="recipe", data=pr, material="MZ-METAL",
                              what=pr.get("_what", "")))
        el.qty, el.where = 2, "x %s–%s, vnitřní strana" % (fmt(pr["x"][0]), fmt(pr["x"][1]))
        el.views.add("TOP")

    def frame_line(self, frame_id, xr, step=0.1):
        """A line along a frame element of the design between x xr[0] and xr[1]: a longeron (its v) or the canopy
        seal (just below the glass)."""
        xs = [xr[0]]
        while xs[-1] + step < xr[1]:
            xs.append(xs[-1] + step)
        xs.append(xr[1])
        fr = next((f for f in self.design["frame"] if f["id"] == frame_id), None)
        if fr is not None and fr["kind"] == "longeron":
            xs = [x for x in xs if fr["x"][0] <= x <= fr["x"][1]]
            return LineString([(x, self.z_of(x, fr["v"])) for x in xs]), "na podélníku %s, x %s–%s" % (
                frame_id, fmt(xs[0]), fmt(xs[-1]))
        z = next(z for z in self.design["zones"] if z["id"] == frame_id)
        pts = []
        for x in xs:
            zl = self.canopy_lower(x)
            if zl is not None:
                pts.append((x, zl - z["w"] / 2))
        return LineString(pts), "na těsnění kabiny %s, x %s–%s" % (frame_id, fmt(pts[0][0]), fmt(pts[-1][0]))

    def _pod_patch(self, xr, dr, step=0.1):
        """Side-view area of a pod patch x range x angle range (angles within -90..90)."""
        xs = [xr[0]]
        while xs[-1] + step < xr[1]:
            xs.append(xs[-1] + step)
        xs.append(xr[1])
        d0, d1 = max(dr[0], -90), min(dr[1], 90)
        lo = [(x, self.pod_z(x, d0)) for x in xs]
        hi = [(x, self.pod_z(x, d1)) for x in reversed(xs)]
        return Polygon(lo + hi).buffer(0)

    def _grilles_and_design_functional(self):
        for it in self.design.get("functional", []):
            kind = it["kind"]
            el = self.add(Element(it["id"], "functional", KIND_CZ[kind], it["status"], src="design", data=it,
                                  what=it["what"], kit=it.get("kit"),
                                  material={"grille": "MZ-DARK", "piston": "MZ-METAL", "frame": "MZ-GUNMETAL", "tread": "MZ-GUNMETAL",
                                            "hinge_ramp": "MZ-METAL", "conduit": "MZ-GUNMETAL",
                                            "ventbox": "MZ-GUNMETAL"}.get(kind, "MZ-PAINT1")))
            el.qty = 2 if it.get("mirror", True) else 1
            if it["on"] == "side":
                el.where = "bok x %s–%s" % (fmt(it["x"][0]), fmt(it["x"][1]))
                shape = box(it["x"][0], it["z"][0], it["x"][1], it["z"][1])
                xc, zc = (it["x"][0] + it["x"][1]) / 2, (it["z"][0] + it["z"][1]) / 2
                self.place(el, shape, "area", "hull", depth=self.hull_y(xc, zc), anchor=(xc, zc))
            elif it["on"] == "pod":
                el.where = "gondola x %s, %s°" % (fmt(it["x"]), fmt(it["deg"]))
                k = self.kit[it["kit"]]
                self._place_pod_item(el, it["x"], it["deg"], k["size"][0], k["size"][1], k["size"][2])
            elif it["on"] == "aft":
                el.where = "zadní stěna u rampy"
                el.views.add("AFT")
            elif it["on"] == "roof":
                el.where = "hřbet x %s–%s" % (fmt(it["x"][0]), fmt(it["x"][1]))
                el.views.add("TOP")

    def _cuts(self, ids, margin):
        geoms = []
        for i in ids:
            el = self.by_id.get(i)
            if el is None:
                raise KeyError("cut %s: no such element" % i)
            if el.id == "Z-SEAL-CANOPY":
                geoms.append(self.canopy.buffer(el.data["w"] + margin, join_style=2))
            elif el.sb:
                geoms.append(el.sb["shape"].buffer(margin, join_style=2))
        return unary_union(geoms) if geoms else Polygon()

    def hardware(self):
        """Parts that sit on the hull's side skin (built or proposed, not removed): what a plate must clear."""
        return [e for e in self.elements if e.sb and e.sb["solid"] == "hull" and e.sb["kind"] == "area"
                and e.status != "remove" and e.data.get("kind") != "conduit"
                and (e.cat == "greeble" or (e.cat == "functional" and e.id != "F-CANOPY-FRAME")
                                              or (e.cat == "light" and not e.extra.get("strip")))]

    def _panels(self):
        p = self.design["panels"]
        hull = self.solids["hull"]["poly"]
        cut = self._cuts(p["cut"], p["cut_margin"])
        hw = self.hardware() if p.get("cut_hardware") else []
        if hw:
            cut = unary_union([cut] + [e.sb["shape"].buffer(p["cut_margin"], join_style=2) for e in hw])
        self.panel_spec = p
        rib_half = self.kit["XK-RIB"]["w"] / 2

        def off(x, band):
            # beside a rib: half the rib + gap; at a seam without a rib in this band (author 3. 10. 2026: full ribs only
            # at the main bulkheads) the plates meet at a plain seam; at the band's own x limit or the hull end: gap
            if self.rib_in_band(x, band["v"][0], band["v"][1]):
                return rib_half + p["gap"]
            return p.get("seam_gap", p["gap"]) if x in self.seams else p["gap"]

        for band in p["bands"]:
            # merged bays (band "merge": [[a, b]]): one long plate from station a to b, the ribs between stop at the
            # band (whole-ship kit critic round 1, 3. 10. 2026: the name WAYFARER ran over three plates and two ribs);
            # a band's "x" limits it along the hull (the nose plate N across bands L and U, 3. 10. 2026)
            st = self.band_stations(band)
            for j in range(1, len(st)):
                a, b = st[j - 1], st[j]
                i = self.bay_no(a)
                xa = a + off(a, band)
                xb = b - off(b, band)
                raw = self.hull_band(xa, xb, band["v"][0], band["v"][1]).intersection(hull.buffer(-0.02))
                shape = largest(polys_only(raw.difference(cut)))
                if shape.is_empty or shape.area < p["min_area_m2"]:
                    continue
                if 2 * shape.boundary.distance(polylabel(shape, 0.005)) < p.get("min_width_m", 0.0):
                    continue                    # a strip left round a grille or a recess: the frame shows
                ident = "P-S-%s%02d" % (band["band"], i)
                for h in hw:
                    if h.sb["shape"].buffer(p["cut_margin"]).intersects(raw) and h.id not in p["cut"]:
                        h.extra.setdefault("cut_in", []).append(ident)
                el = self.add(Element(ident, "panel", band["name"],
                                      "built" if band["band"] in p.get("built_bands", []) else p["status"],
                                      material=band["material"],
                                      kit=band["kit"], src="design", data={"band": band["band"], "bay": i, "x": [a, b]},
                                      what="deska %s, příčky x %s–%s" % (band["name"], fmt(a), fmt(b))))
                el.qty = 2
                el.where = "x %s–%s" % (fmt(a), fmt(b))
                sub = band.get("sub") or {}
                skip = band.get("merge", []) + sub.get("skip", [])
                subs = self.side_subs(shape, band, i) if sub and not any(s0 <= a and b <= s1 for s0, s1 in skip) else []
                for kind, g in subs:
                    if kind == "hatch":
                        # as on the roof: the hatch sits in a hole of the plate (the decal build fills it again)
                        shape = largest(polys_only(shape.difference(g.buffer(self.kit["XK-HATCH"]["gap"],
                                                                              join_style=2)).buffer(0)))
                self.place(el, shape, "area", "hull", depth=self.hull_y(shape.representative_point().x,
                                                                        shape.representative_point().y))
                for kind, g in subs:
                    kit_id = {"doubler": "XK-DOUBLER", "hatch": "XK-HATCH"}[kind]
                    sel = self.add(Element("%s-%s" % (ident, {"doubler": "D", "hatch": "H"}[kind]), "panel",
                                           band["name"], el.status, material=band["material"], kit=kit_id,
                                           src="design", data={"band": band["band"], "bay": i, "x": [a, b],
                                                               "sub": kind, "of": ident},
                                           what={"doubler": "přídavný panel na desce %s",
                                                 "hatch": "malý poklop v desce %s"}[kind] % ident))
                    sel.qty, sel.where = 2, el.where
                    c = g.representative_point()
                    self.place(sel, g, "area", "hull", depth=self.hull_y(c.x, c.y))

    def side_subs(self, shape, band, bay):
        """Doubler panel and small hatch on a side plate (panels.bands[].sub; kit pilot step c, 2. 10. 2026: the shoulder
        plates like the roof's), in the side view (x, z) within the sub band of section heights v: even bays a square
        doubler at the aft end and the hatch forward, odd bays the hatch at the aft end and a long doubler strip
        forward. Each keeps the margin off the plate's edges and cut-outs and off the plate number's lower aft corner
        (D-R-PANEL-NUMBERS), slides along the bay to clear them, or is left out. [(kind, outline)]."""
        sub = band["sub"]
        mg = sub["margin"]
        v0, v1 = sub["v"]
        inner = shape.buffer(-mg, join_style=2)
        x0, z0, x1, z1 = shape.bounds
        marks = []
        # the rule's element is made later (_decals): read its data
        d = next((r for r in self.design.get("decals", []) if r.get("id") == "D-R-PANEL-NUMBERS"), None)
        if d is not None and band["band"] in d.get("bands", []):
            marks.append(box(x0 - 0.01, z0 - 0.01, x0 + d["edge"] + 0.18, z0 + d["edge"] + d["size"] + 0.02))
        step = 0.02

        def strip(xa, xb):
            pts_lo = [(x, self.z_of(x, v0)) for x in (xa, xb)]
            pts_hi = [(x, self.z_of(x, v1)) for x in (xb, xa)]
            return Polygon(pts_lo + pts_hi)

        def runs(avoid):
            out, start, x, last = [], None, x0 + mg, None
            while x <= x1 - mg + 1e-9:
                ln = LineString([(x, self.z_of(x, v0)), (x, self.z_of(x, v1))])
                ok = inner.contains(ln) and not any(o.intersects(ln) for o in avoid)
                if ok and start is None:
                    start = x
                if not ok and start is not None:
                    out.append((start, last))
                    start = None
                last = x
                x += step
            if start is not None:
                out.append((start, last))
            return out

        def window(length, at, avoid):
            fits = [r for r in runs(avoid) if r[1] - r[0] >= length - 1e-9]
            if not fits:
                return None
            r = fits[0] if at == "aft" else fits[-1]
            xa = r[0] if at == "aft" else r[1] - length
            return strip(xa, xa + length)

        out = []
        hx = self.kit["XK-HATCH"]["size"][0]
        if bay % 2:
            g = window(hx, "aft", marks)
            if g is not None:
                out.append(("hatch", g))
            rs = runs(marks + [o.buffer(mg) for _, o in out])
            best = max(rs, key=lambda r: r[1] - r[0]) if rs else None
            if best and best[1] - best[0] >= sub["doubler_odd_min"]:
                out.append(("doubler", strip(best[0], best[1])))
        else:
            g = window(sub["doubler_even_len"], "aft", marks)
            if g is not None:
                out.append(("doubler", g))
            g = window(hx, "fwd", marks + [o.buffer(mg) for _, o in out])
            if g is not None:
                out.append(("hatch", g))
        return out

    def _shoulder_conduits(self):
        """The conduits along the shoulder (F-CONDUIT-S, functional on: shoulder): each pipe a strip along its section
        height v from x0 to x1 in the side view, over the S plates (not cut out of them: lifted over the plates and the
        ribs on clamps)."""
        for it in self.design.get("functional", []):
            if it.get("kind") != "conduit" or it.get("on") != "shoulder":
                continue
            el = self.by_id[it["id"]]
            strips = []
            for p in it["pipes"]:
                xs = [it["x"][0] + (it["x"][1] - it["x"][0]) * i / 40 for i in range(41)]
                ln = LineString([(x, self.z_of(x, p["v"])) for x in xs])
                strips.append(ln.buffer(p["d"] / 2, cap_style=2))
            g = unary_union(strips)
            el.qty, el.where = 2, "rameno x %s–%s" % (fmt(it["x"][0]), fmt(it["x"][1]))
            xc = (it["x"][0] + it["x"][1]) / 2
            self.place(el, g, "area", "hull", depth=self.hull_y(xc, self.z_of(xc, it["pipes"][0]["v"])),
                       anchor=(xc, self.z_of(xc, it["pipes"][0]["v"])))

    def _frame(self):
        hull = self.solids["hull"]["poly"].buffer(-0.01)
        cut = self._cuts(self.design["panels"]["cut"], 0.02)
        if self.design["panels"].get("cut_hardware"):
            cut = unary_union([cut] + [e.sb["shape"].buffer(0.02, join_style=2) for e in self.hardware()
                                       if e.cat != "light"])
        for fr in self.design["frame"]:
            el = self.add(Element(fr["id"], "frame", {"ribs": "žebra rámu", "spine": "páteř hřbetu"}.get(fr["kind"], "podélník"),
                                  fr["status"], material=fr["material"], kit=fr["kit"], src="design", data=fr,
                                  what=fr["what"]))
            w = self.kit[fr["kit"]]["w"] / 2
            if fr["kind"] == "aft":
                # the aft wall's frame: drawn and built in the aft view (exterior_views._aft)
                el.qty, el.where = 1, "zadní stěna"
                el.views.add("AFT")
                continue
            if fr["kind"] == "spine":
                # on the roof's centre line: drawn in plan (exterior_views), seen from the side only edge-on
                el.qty, el.where = 1, "osa hřbetu x %s–%s" % (fmt(fr["x"][0]), fmt(fr["x"][1]))
                continue
            if fr["kind"] == "ribs":
                pieces = []
                for x in self.seams:
                    g = self.hull_band(x - w, x + w, *self.rib_v(x))
                    for band in self.design["panels"]["bands"]:
                        if any(a < x < b for a, b in band.get("merge", [])):
                            g = g.difference(self.hull_band(x - w - 0.01, x + w + 0.01, band["v"][0], band["v"][1]))
                    pieces.append(g)
                el.qty = 2 * len(self.seams)
                full = [x for x in self.seams if self.rib_v(x) == tuple(fr["v"])]
                el.where = "na %d příčkách, po celé výšce na %d přepážkách (x %s)" % (
                    len(self.seams), len(full), ", ".join(fmt(x) for x in full))
            else:
                xs = []
                x = fr["x"][0]
                while x < fr["x"][1]:
                    xs.append(x)
                    x += 0.1
                xs.append(fr["x"][1])
                zc = [(x, self.z_of(x, fr["v"])) for x in xs]
                pieces = [Polygon([(x, z - w) for x, z in zc] + [(x, z + w) for x, z in reversed(zc)])]
                el.qty = 2
                el.where = "x %s–%s" % (fmt(fr["x"][0]), fmt(fr["x"][1]))
            shape = polys_only(unary_union(pieces).intersection(hull).difference(cut))
            anchor = None
            if fr["kind"] == "ribs":
                x = min((s for s in self.seams if self.rib_v(s) == tuple(fr["v"])), key=lambda s: abs(s - 12.8))
                anchor = (x, self.z_of(x, 0.3))
            self.place(el, shape, "area", "hull", depth=self.hw(10.0), anchor=anchor)

    def _pod_sections(self):
        rev = self.recipe["parts"]["pod"]["revolve"]
        mats = self.recipe["parts"]["pod"].get("materials", {})
        pod = self.pod_poly()
        for s in rev["sections"]:
            mat = self.mat(mats.get("_" + s["name"], self.recipe["parts"]["pod"]["material"]))
            el = self.add(Element(s["id"], "section", "úsek gondoly %s" % s["name"], src="recipe", data=s, material=mat,
                                  what=("%d panelů dokola, %d řady" % (s["around"], s.get("rows", 1))) if s["kind"] == "panels"
                                  else "prstenec"))
            el.qty = 2
            el.where = "x %s–%s" % (fmt(s["x"][0]), fmt(s["x"][1]))
            shape = pod.intersection(box(s["x"][0], -5, s["x"][1], 6))
            lines = []
            if s["kind"] == "panels":
                xs = [s["x"][0] + 0.01 + k * (s["x"][1] - s["x"][0] - 0.02) / 12 for k in range(13)]
                for k in range(s["around"]):
                    deg = s.get("phase_deg", 0) + k * 360.0 / s["around"]
                    dd = (deg + 180) % 360 - 180
                    if math.cos(math.radians(dd)) > 0.05:
                        lines.append(LineString([(x, self.pod_z(x, dd)) for x in xs]))
                for k in range(1, s.get("rows", 1)):
                    x = s["x"][0] + k * (s["x"][1] - s["x"][0]) / s["rows"]
                    lines.append(LineString([(x, POD_CY - self.pod_r(x)), (x, POD_CY + self.pod_r(x))]))
            el.extra["seams"] = lines
            self.place(el, polys_only(shape), "area", "pod",
                       anchor=((s["x"][0] + s["x"][1]) / 2, POD_CY - 0.55 if s["kind"] == "panels" else POD_CY + 0.6))
        for p in self.recipe["detail"]["pod"].get("plates", []):
            el = self.add(Element(p["id"], "plate", "pancíř gondoly", src="recipe", data=p, material="MZ-PAINT1",
                                  what=p.get("_what", "")))
            el.qty = 2
            el.where = "x %s–%s, %s–%s°" % (fmt(p["x"][0]), fmt(p["x"][1]), fmt(p["deg"][0]), fmt(p["deg"][1]))
            if math.cos(math.radians((p["deg"][0] + p["deg"][1]) / 2)) > 0:
                self.place(el, self._pod_patch(p["x"], p["deg"]), "area", "pod")
            else:
                el.views.add("TOP")

    def _lights(self):
        L = self.recipe["lights"]
        for it in L.get("lenses", []):
            col = it.get("mirror_color", it["color"])
            light = it.get("light")
            el = self.add(Element(it["id"], "light", "světlo %s" % it["name"], src="recipe", data=it, what=it.get("_what", ""),
                                  material=None))
            el.extra.update(color=col, light=light, lens=True)
            el.qty = 1 if it.get("mirror") is False else 2
            on = it["on"]
            w, h = it["size"][0], it["size"][1]
            if on == "pod":
                el.where = "gondola x %s, %s°" % (fmt(it["x"]), fmt(it["deg"]))
                self._place_pod_item(el, it["x"], it["deg"], max(w, 0.08), max(h, 0.04), it["size"][2], light=True)
            elif on in ("top", "bottom"):
                el.where = "%s x %s" % ("hřbet" if on == "top" else "břicho", fmt(it["x"]))
                zb, zt = self.zspan(it["x"])
                zz = zt if on == "top" else zb
                self.place(el, box(it["x"] - w / 2, zz - 0.02, it["x"] + w / 2, zz + 0.02), "profile", "hull",
                           depth=self.hw(it["x"]) + 0.5, anchor=(it["x"], zz))
                el.views.add("TOP" if on == "top" else "BOT")
            elif on == "ray":
                at, d = it["at"], it["dir"]
                if d[0] == 0:
                    hit = self.section_hit(at[0], at[1], at[2], d[1], d[2])
                    y, z = hit[1] if hit else (at[1], at[2])
                    el.where = "x %s z %s" % (fmt(at[0]), fmt(z))
                    self.place(el, box(at[0] - w / 2, z - h / 2, at[0] + w / 2, z + h / 2), "area", "hull",
                               depth=abs(y), anchor=(at[0], z))
                else:
                    el.where = "zadní stěna"
                    el.views.add("AFT")
        for it in L.get("strips", []):
            el = self.add(Element(it["id"], "light", "světelný pás %s" % it["name"], src="recipe", data=it,
                                  what=it.get("_what", "")))
            el.extra.update(color=it["color"], light=it.get("light"), strip=True)
            el.qty = 2
            on = it.get("on", "pod")
            if on == "pod":
                r = it.get("r")
                xs = [it["x"][0] + k * (it["x"][1] - it["x"][0]) / 10 for k in range(11)]
                pts = [(x, POD_CY + (r if r else self.pod_r(x)) * math.sin(math.radians(it["deg"]))) for x in xs]
                el.where = "gondola x %s–%s, %s°" % (fmt(it["x"][0]), fmt(it["x"][1]), fmt(it["deg"]))
                dep = self.pod_axis[0] + (r if r else 0.95) * math.cos(math.radians(it["deg"]))
                self.place(el, LineString(pts), "line", "pod", depth=dep)
            elif on == "side":
                # z: one height, or a polyline [[x, z], ...] (the strip in the L/U channel follows the bands' taper)
                pts = side_strip_pts(it)
                line = LineString(pts)
                p_ = line.interpolate(0.5, normalized=True)
                mid = (p_.x, p_.y)
                zs = "%s" % fmt(it["z"]) if not isinstance(it["z"], list) else "%s–%s" % (
                    fmt(min(z for _, z in pts)), fmt(max(z for _, z in pts)))
                if el.change and el.change.get("on") == "frame":
                    el.extra["ghost"] = line
                    el.extra["ghost_where"] = "bok x %s–%s z %s" % (fmt(it["x"][0]), fmt(it["x"][1]), zs)
                    line, el.where = self.frame_line(el.change["frame"], it["x"])
                    p = line.interpolate(0.5, normalized=True)
                    mid = (p.x, p.y)
                else:
                    el.where = "bok x %s–%s z %s" % (fmt(it["x"][0]), fmt(it["x"][1]), zs)
                self.place(el, line, "line", "hull", depth=self.hull_y(*mid), anchor=mid)
            else:
                el.where = "břicho x %s–%s" % (fmt(it["x"][0]), fmt(it["x"][1]))
                el.views.add("BOT")
        for it in self.design.get("lights", []):
            el = self.add(Element(it["id"], "light", KIND_CZ[it["kind"]], it["status"], src="design", data=it,
                                  what=it["what"], kit=it.get("kit")))
            el.extra.update(color=it["color"], light=it.get("light"), lens=True)
            el.qty = 1 if it.get("mirror") is False else 2
            k = self.kit[it["kit"]]
            w, h = k["size"][0], k["size"][1]
            on = it["on"]
            if on == "fin_tip":
                el.where = "špička ploutve x %s" % fmt(it["x"])
                self.place(el, box(it["x"] - w / 2, it["z"] - 0.01, it["x"] + w / 2, it["z"] + 0.03), "profile", "fin",
                           depth=self.solids["fin"]["depth"](it["x"]) + 0.01, anchor=(it["x"], it["z"]))
            elif on == "wing_tip":
                el.where = "konec křídla x %s" % fmt(it["x"])
                self.place(el, box(it["x"] - w / 2, it["z"] - h / 2, it["x"] + w / 2, it["z"] + h / 2), "area", "wing",
                           depth=it["y"], anchor=(it["x"], it["z"]))
            elif on == "bottom":
                el.where = "břicho x %s" % fmt(it["x"])
                zb, _ = self.zspan(it["x"])
                self.place(el, box(it["x"] - w / 2, zb - k["size"][2], it["x"] + w / 2, zb), "profile", "hull",
                           depth=self.hw(it["x"]) + 0.5, anchor=(it["x"], zb))
                el.views.add("BOT")
            else:
                el.where = "zadní stěna z %s" % fmt(it["z"])
                el.views.add("AFT")

    def _decals(self):
        lib = self.library["decals"]
        dz = self.recipe["decals"]
        for it in dz.get("items", []):
            ch = self.changes.get(it["id"], {}).get("set") or {}
            orig = it
            if "item" in ch:
                it = dict(it, item=ch["item"])
            item = lib.get(it["item"])
            if item is None:
                raise KeyError("%s: library has no %s" % (it["id"], it["item"]))
            sc = it.get("scale", 1.0)
            w, h = item["size_m"][0] * sc, item["size_m"][1] * sc
            text = bool(TEXT_TAGS & set(item.get("tags", [])))
            el = self.add(Element(it["id"], "decal", it["item"], src="recipe", data=orig, what=it.get("_what", item["purpose"])))
            el.extra.update(item=it["item"], size=(w, h), text=text, rot=it.get("rot", 0.0),
                            ink="light" if "light ink" in item["purpose"] else ("dark" if "dark ink" in item["purpose"] else None))
            el.qty = 1 if it.get("mirror") is False else 2
            self._with_ghost(el, it, self._place_decal_item)
        self._decal_rest(dz)

    def _place_decal_item(self, el, it):
        w, h = el.extra["size"]
        if True:
            on = it["on"]
            rot = it.get("rot", 0.0)
            if on == "side":
                el.where = "bok x %s z %s" % (fmt(it["x"]), fmt(it["z"]))
                ww, hh = (h, w) if rot % 180 == 90 else (w, h)
                solid = self.landing(it["x"], it["z"])
                if solid != "hull":
                    el.extra["lands_on"] = solid
                self.place(el, box(it["x"] - ww / 2, it["z"] - hh / 2, it["x"] + ww / 2, it["z"] + hh / 2), "area", solid,
                           depth=(self.hull_y(it["x"], it["z"]) if solid == "hull" else self.solids[solid]["depth"](it["x"])) + 0.003,
                           anchor=(it["x"], it["z"]))
                el.extra["up"] = (-math.sin(math.radians(rot)), math.cos(math.radians(rot)))
            elif on == "pod":
                el.where = "gondola x %s, %s°" % (fmt(it["x"]), fmt(it["deg"]))
                along = it.get("along")
                if along:
                    el.qty *= along["count"]
                self._place_pod_item(el, it["x"] + (along["step"] * (along["count"] - 1) / 2 if along else 0.0), it["deg"],
                                     w + (along["step"] * (along["count"] - 1) if along else 0.0), h, 0.0, rot)
                if el.sb:
                    el.extra["up"] = (-math.sin(math.radians(rot)), math.cos(math.radians(rot)))
            elif on == "ray" and it["dir"][0] == 0:
                at, d = it["at"], it["dir"]
                hit = self.section_hit(at[0], at[1], at[2], d[1], d[2])
                y, z = hit[1] if hit else (at[1], at[2])
                n = hit[2] if hit else (1, 0)
                el.where = "%s x %s z %s" % ("rameno" if abs(n[1]) > 0.3 else "bok", fmt(at[0]), fmt(z))
                along = it.get("along")
                x0 = at[0] + (along["step"] * (along["count"] - 1) / 2 if along else 0.0)
                ww = w + (along["step"] * (along["count"] - 1) if along else 0.0)
                hh = h * abs(n[0])
                self.place(el, box(x0 - ww / 2, z - hh / 2, x0 + ww / 2, z + hh / 2), "area", "hull", depth=abs(y),
                           anchor=(x0, z))
                el.extra["up"] = (0.0, 1.0)
                if along:
                    el.qty *= along["count"]
            else:
                el.where = {"top": "hřbet", "bottom": "břicho"}.get(on, "zadní stěna") + (
                    " x %s" % fmt(it["x"]) if "x" in it else "")
                el.views.add({"top": "TOP", "bottom": "BOT"}.get(on, "AFT"))

    def _decal_rest(self, dz):
        for it in dz.get("trim", []):
            el = self.add(Element(it["id"], "trim", it["strip"], src="recipe", data=it, what=it.get("_what", "")))
            el.qty = 2 if it.get("mirror", True) else 1
            if it["on"] == "pod_ring":
                d0, d1 = it["deg"]
                pts = []
                k = d0
                while k <= d1 + 1e-6:
                    dd = (k + 180) % 360 - 180
                    if math.cos(math.radians(dd)) > 0.02:
                        pts.append(self.pod_z(it["x"], dd))
                    k += 5
                el.where = "prstenec gondoly x %s" % fmt(it["x"])
                if pts:
                    self.place(el, LineString([(it["x"], min(pts)), (it["x"], max(pts))]), "line", "pod",
                               depth=self.pod_axis[0] + 0.9, anchor=(it["x"], (min(pts) + max(pts)) / 2))
            else:
                el.where = "břicho" if it["on"] == "bottom_line" else "obrys rampy"
                el.views.add("BOT" if it["on"] == "bottom_line" else "AFT")
        for it in dz.get("grime", []):
            el = self.add(Element(it["id"], "grime", it.get("kind", it.get("card", "špína")), src="recipe", data=it,
                                  what=it.get("_what", "")))
            el.where = it.get("on", "")
        for key, rule in dz.get("rules", {}).items():
            if key.startswith("_") or not isinstance(rule, dict):
                continue
            el = self.add(Element(rule["id"], "rule", key, src="recipe", data=rule, what=rule.get("_comment", "")))
            el.where = "pravidlo"
        for it in self.design.get("decals", []):
            el = self.add(Element(it["id"], "rule", "čísla panelů", it["status"], src="design", data=it, what=it["what"]))
            el.where = "každá deska P-S"
        # the big projected markings of the setup (Unreal decal components; [pitch, yaw, roll], size [depth, Y, Z])
        off = self.recipe["assemble"]["offset"]
        for d in self.setup.get("decals", []):
            if d["name"].startswith("Int_"):
                continue
            el = self.add(Element(d["id"], "decal", d["texture"], src="setup", data=d, what=d["name"]))
            el.extra.update(item=d["texture"], text=not d.get("symmetric"), setup=True,
                            ink="dark" if sum(d.get("tint", [1, 1, 1])) / 3 < 0.3 else None)
            el.qty = 1
            if el.change and "location" in el.change:
                old = (d["location"][0] / 100.0 - off[0], d["location"][2] / 100.0 - off[2])
                d = dict(d, location=el.change["location"])
                el.extra["ghost_loc"] = old
            loc = (d["location"][0] / 100.0 - off[0], -d["location"][1] / 100.0 - off[1], d["location"][2] / 100.0 - off[2])
            X = x_axis(d["rotation"])
            Y = y_axis(d["rotation"])
            Z = (X[1] * Y[2] - X[2] * Y[1], X[2] * Y[0] - X[0] * Y[2], X[0] * Y[1] - X[1] * Y[0])
            sy, sz = d["size"][1] / 100.0, d["size"][2] / 100.0
            up_sign = 1 if float(d.get("flip_v", 0.0)) >= 0.5 else -1
            up = (Y[0] * up_sign, Y[2] * up_sign)      # ship space x and z (Unreal x forward, z up)
            el.extra["up"] = up
            el.extra["size"] = (sz, sy)
            el.where = "x %s z %s" % (fmt(loc[0]), fmt(loc[2]))
            starboard = loc[1] < -0.5
            if starboard and abs(X[1]) > 0.7:
                ex = abs(Y[0]) * sy + abs(Z[0]) * sz
                ez = abs(Y[2]) * sy + abs(Z[2]) * sz
                shape = box(loc[0] - ex / 2, loc[2] - ez / 2, loc[0] + ex / 2, loc[2] + ez / 2)
                if "ghost_loc" in el.extra:
                    gx, gz = el.extra["ghost_loc"]
                    el.extra["ghost"] = box(gx - ex / 2, gz - ez / 2, gx + ex / 2, gz + ez / 2)
                    el.extra["ghost_where"] = "x %s z %s" % (fmt(gx), fmt(gz))
                on_pod = abs(abs(loc[1]) - self.pod_axis[0]) < 1.2 and loc[0] < 6.0 and abs(loc[1]) > 2.6
                solid = "pod" if on_pod else "hull"
                if on_pod:
                    el.where = "gondola x %s z %s" % (fmt(loc[0]), fmt(loc[2]))
                depth = abs(loc[1]) if not on_pod else self.pod_axis[0] + 0.9
                self.place(el, shape, "area", solid, depth=depth if solid == "pod" else self.hull_y(loc[0], loc[2]),
                           anchor=(loc[0], loc[2]))
            else:
                el.views.add("PORT" if loc[1] > 0.5 else "AFT")

    def change_text(self, el):
        """What a change does, built value → new value, for the changes schedule."""
        if el.status == "remove":
            return "odstranit"
        out = []
        ch = el.change or {}
        if "at" in ch:
            out.append("z boku → paprsek z bodu %s směrem %s" % (fmtv(ch["at"]), fmtv(ch["dir"])))
            ch = {k: v for k, v in ch.items() if k not in ("on", "at", "dir")}
        for k, v in ch.items():
            node = el.data
            for part in k.split("."):
                node = node.get(part) if isinstance(node, dict) else None
            if k == "kit":
                out.append("blok %s z receptu → díl kitu %s" % (el.data.get("kind", ""), v))
            elif k == "material" and node is None:
                out.append("materiál paint → %s" % v)
            elif k == "location":
                off = self.recipe["assemble"]["offset"]
                gx, gz = el.extra.get("ghost_loc", (None, None))
                out.append("x %s z %s → x %s z %s" % (fmt(gx), fmt(gz), fmt(v[0] / 100.0 - off[0]), fmt(v[2] / 100.0 - off[2])))
            elif k.startswith("areas["):
                out.append("boční oblast rozsevu zrušena")
            elif k == "on" and v == "frame":
                out.append("%s → %s" % (el.extra.get("ghost_where", ""), el.where))
            elif k == "frame" or (k == "on" and v == "panels"):
                continue
            elif k == "item":
                out.append("knihovna %s → %s" % (el.data.get("item"), v))
            else:
                out.append("%s %s → %s" % (CHANGE_KEY_CZ.get(k, k), fmtv(node), fmtv(v)))
        return "; ".join(out)

    def conflicts(self):
        """What the drawing finds in the data, per ID: parts landing elsewhere, hidden from the side, cut out of a
        plate, lettering on a background of its own tone, and anything on the side skin a plate would bury."""
        out = {}
        plates = [e for e in self.elements if e.cat == "panel" and e.sb]
        plate_union = unary_union([e.sb["shape"] for e in plates]) if plates else Polygon()
        hw = [h for h in self.hardware()]

        def note(e, kind, text):
            out.setdefault(e.id, []).append((kind, text))

        def behind(e):
            a = e.sb["anchor"]
            for oname, o in self.solids.items():
                if oname != e.sb["solid"] and o["poly"].intersects(e.sb["shape"]) and o["depth"](a[0]) > e.sb["depth"]:
                    return oname
            return "pod" if a[0] < 6 else "wing"

        for e in self.elements:
            if e.extra.get("ghost_lands_on"):
                note(e, "lands", "postavená poloha dopadala na %s – opraveno změnou" % SOLID_ACC[e.extra["ghost_lands_on"]])
            if e.extra.get("lands_on"):
                note(e, "lands", "dopadá na %s" % SOLID_ACC[e.extra["lands_on"]])
            if not e.sb or e.status == "remove" or e.cat not in ("decal", "greeble", "functional", "light"):
                continue
            if e.sb["hidden"]:
                note(e, "hidden", "z boku skryté za %s" % SOLID_INS[behind(e)])
            elif e.sb["kind"] == "area" and 0.0 < e.sb.get("vis_frac", 1.0) < 0.85:
                note(e, "partial", "z boku z %d %% skryté za %s" % (round(100 * (1 - e.sb["vis_frac"])), SOLID_INS[behind(e)]))
            if e.extra.get("cut_in"):
                note(e, "cut", "výřez v desce %s" % ", ".join(sorted(set(e.extra["cut_in"]))))
            if e.sb["solid"] == "hull" and e.sb["kind"] == "area" and e.cat in ("greeble", "functional", "light") \
                    and not e.extra.get("cut_in") and e.data.get("kind") != "conduit" \
                    and e.sb["shape"].intersection(plate_union).area > 1e-4:
                # (a conduit runs over the plates on clamps: F-CONDUIT-S on the shoulder)
                note(e, "buried", "leží pod deskou bez výřezu")
            if e.sb["solid"] == "hull" and e.sb["kind"] == "line" and e.sb["shape"].intersection(plate_union).length > 0.05:
                note(e, "buried", "vede pod deskami (%.1f m)" % e.sb["shape"].intersection(plate_union).length)
            if e.cat == "decal" and e.extra.get("text") and e.sb["kind"] == "area":
                for h in hw:
                    if h.sb["solid"] == e.sb["solid"] and h.sb["shape"].intersection(e.sb["shape"]).area > 0.2 * e.sb["shape"].area:
                        note(e, "covered", "nápis z %d %% pod dílem %s" % (
                            round(100 * h.sb["shape"].intersection(e.sb["shape"]).area / e.sb["shape"].area), h.id))
            if e.cat == "decal" and e.extra.get("text") and e.extra.get("ink") and e.sb["solid"] == "hull":
                shp = e.sb["shape"]
                lums = []
                for pl in plates:
                    a = shp.intersection(pl.sb["shape"]).area
                    if a > 0:
                        lums.append((a, self.lum(pl.material)))
                rest = shp.area - sum(a for a, _ in lums)
                if rest > 1e-6:
                    lums.append((rest, self.lum(self.by_id["P-HULL"].material)))
                bg = sum(a * l for a, l in lums) / max(sum(a for a, _ in lums), 1e-9)
                if (e.extra["ink"] == "dark" and bg < 0.45) or (e.extra["ink"] == "light" and bg > 0.6):
                    note(e, "ink", "%s nápis na %s podkladu" % ("tmavý" if e.extra["ink"] == "dark" else "světlý",
                                                               "tmavém" if bg < 0.45 else "světlém"))
        return out

    def lum(self, mid):
        h = self.materials[mid]["draw"]["fill"].lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def port_text_decals(self):
        """The port side's lettered setup markings and whether they read upright (the same rule as starboard)."""
        return [(e.id, e.extra["up"][1] > 0.5) for e in self.elements if e.cat == "decal" and e.extra.get("setup")
                and e.extra.get("text") and "PORT" in e.views]

    # ------------------------------------------------------------------ queries
    def in_view(self, view="SB", cats=None):
        out = [e for e in self.elements if (e.sb if view == "SB" else None)]
        if cats:
            out = [e for e in out if e.cat in cats]
        return out

    def rcs_blocks(self):
        """Thruster blocks on the ship after the design (mirrored ones twice), removed ones left out."""
        return sum(e.qty for e in self.elements if e.cat == "functional" and e.data.get("kind") == "rcs"
                   and e.status != "remove")

    def spec_rcs(self):
        """Manoeuvring thruster count of the spec ("8x TR1 (...)", key "maneuvering")."""
        def find(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "maneuvering" and isinstance(v, str):
                        return v
                    found = find(v)
                    if found:
                        return found
            return None
        m = re.match(r"\s*(\d+)\s*[x×]", find(self.spec) or "")
        return int(m.group(1)) if m else None


def side_strip_pts(it):
    """Side-view points (x, z) of a hull side light strip: "z" is one height over "x", or a polyline [[x, z], ...]
    (hs_lights interpolates it the same way)."""
    if isinstance(it["z"], list):
        return [(float(x), float(z)) for x, z in it["z"]]
    return [(it["x"][0], it["z"]), (it["x"][1], it["z"])]


def x_axis(rotation):
    pitch, yaw = (list(rotation) + [0.0, 0.0, 0.0])[:2]
    p, y = math.radians(pitch), math.radians(yaw)
    return (math.cos(p) * math.cos(y), math.cos(p) * math.sin(y), math.sin(p))


def y_axis(rotation):
    pitch, yaw, roll = (list(rotation) + [0.0, 0.0, 0.0])[:3]
    p, y, r = math.radians(pitch), math.radians(yaw), math.radians(roll)
    return (math.sin(r) * math.sin(p) * math.cos(y) - math.cos(r) * math.sin(y),
            math.sin(r) * math.sin(p) * math.sin(y) + math.cos(r) * math.cos(y),
            -math.sin(r) * math.cos(p))


def fmtv(v):
    if v is None:
        return "-"
    if isinstance(v, (list, tuple)):
        return "; ".join(fmtv(x) for x in v) if len(v) > 2 else "–".join(fmtv(x) for x in v)
    if isinstance(v, (int, float)):
        return fmt(v)
    return str(v)


def fmt(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return s.replace(".", ",") if s != "-0" else "0"


if __name__ == "__main__":
    import sys
    m = Model(sys.argv[1] if len(sys.argv) > 1 else "Wayfarer")
    cats = {}
    for e in m.elements:
        cats.setdefault(e.cat, [0, 0])
        cats[e.cat][0] += 1
        cats[e.cat][1] += 1 if e.sb else 0
    for c, (n, sb) in sorted(cats.items()):
        print("EXTMODEL %-10s %3d elements, %3d on the starboard view" % (c, n, sb))
    print("EXTMODEL RCS blocks %d (spec %s)" % (m.rcs_blocks(), m.spec_rcs()))
    print("EXTMODEL hidden on SB:", ", ".join(e.id for e in m.elements if e.sb and e.sb["hidden"]))
