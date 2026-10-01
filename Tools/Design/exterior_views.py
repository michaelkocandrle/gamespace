"""The other views of the exterior drawing model (author 1. 10. 2026, dossier point 3: six views from one source of
data). exterior_model.Model builds every element's starboard view (Element.sb); add_views() adds, from the same data,
the plan from above (TOP) and from below (BOT), the end views from behind (AFT) and ahead (FWD) and the port side
(PORT) as Element.geo[view], and per view the solids with their visible parts. Model.use_view(view) makes a view
current, so the drawing code reads it through e.sb, m.solids and m.canopy exactly as it reads the starboard view.

Paper axes (u right, w up), each view as its viewer sees it (third-angle projection):
  SB    u = x,  w = z     nose right                          (exterior_model)
  PORT  u = -x, w = z     nose left: stored as x, z like SB; the drawing's frame mirrors it (Frame flip), so the
                          starboard sheet's helpers (stations, levels, dimensions) draw it unchanged
  TOP   u = x,  w = y     nose right, port up
  BOT   u = x,  w = -y    nose right, starboard up (the belly seen from below)
  AFT   u = -y, w = z     starboard right
  FWD   u = y,  w = z     port right
Ship axes as the layout: x from the stern, y to port, z from the deck.

What a view shows:
  - the solids (hull, pods, wings, fins, guns, missile racks, gear) from the layout's top and front outlines; where
    they overlap, the one nearer the viewer (ORDER) hides the other;
  - everything on the hull's side skin (zones, plates, recesses, proposed plates and frame, greebles, functional
    parts, lights, decals) also where its starboard outline lies on the upper or lower chamfer: that part is mapped
    from (x, z) to (x, half-width of the hull at that height) - the chamfers face up and down as much as sideways;
  - items the recipe places from above or below (x, y), on a pod (x, angle: from above when the angle points up),
    on the aft wall (rays along x) and the proposed design parts;
  - PORT: the starboard view mirrored (the ship is symmetric; mirrored items read right on both sides, hs_decals
    _frame) plus the port-only markings of the setup (their own frame: the lettering check of the port side).
Grime cards are not drawn in any view (schedule on E-02).
"""
import math

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import transform, unary_union

import exterior_model as em

VIEWS = ("PORT", "TOP", "BOT", "AFT", "FWD")
# solids nearest the viewer first: where two overlap in a view the earlier one hides the later one
ORDER = {"TOP": ("fin", "pod", "hull", "wing", "gun", "missile_rack", "gear_main", "gear_nose"),
         "BOT": ("gear_main", "gear_nose", "missile_rack", "pod", "hull", "gun", "wing", "fin"),
         "AFT": ("pod", "hull", "fin", "wing", "missile_rack", "gear_main", "gun", "gear_nose"),
         "FWD": ("hull", "gear_nose", "gun", "wing", "pod", "missile_rack", "gear_main", "fin")}
V_UP = 0.7692307692307693           # section height where the upper chamfer starts (hull front outline)
V_LO = 0.1794871794871795           # ... and where the lower chamfer ends
# drawn in plan from their own data, not from the starboard outline: the canopy frame lies on the glass
NOT_MAPPED = {"F-CANOPY-FRAME", "Z-SEAL-CANOPY"}
CATS_MAPPED = ("zone", "plate", "recess", "panel", "frame", "greeble", "functional", "light", "decal", "trim")


def _apply(fn, g):
    def f(x, y, z=None):
        if hasattr(x, "__len__"):
            out = [fn(a, b) for a, b in zip(x, y)]
            return [o[0] for o in out], [o[1] for o in out]
        return fn(x, y)
    return transform(f, g)


def _mirror_y(g):
    return affinity.scale(g, 1.0, -1.0, origin=(0, 0))


def _both(g):
    """Plan geometry (x, y) with its mirror across the centre line."""
    return unary_union([g, _mirror_y(g)])


def _both_end(g):
    """End-view geometry (y, z) with its mirror across the centre line."""
    return unary_union([g, affinity.scale(g, -1.0, 1.0, origin=(0, 0))])


def _rot(v, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _rbox(cx, cy, w, h, deg=0.0):
    """Rectangle w x h centred at (cx, cy), turned by deg (counter-clockwise)."""
    g = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return affinity.rotate(g, deg, origin=(cx, cy)) if deg else g


class Views:
    def __init__(self, m):
        self.m = m
        self.solids = {}
        self.canopy = {}
        self._solids()

    # ------------------------------------------------------------------ coordinates
    @staticmethod
    def paper(view, g):
        """Ship-plane geometry of a view to paper axes: TOP/BOT take (x, y), AFT/FWD (y, z), PORT (x, z)."""
        if g is None or g.is_empty:
            return g
        if view == "BOT":
            return _mirror_y(g)
        if view == "AFT":
            return affinity.scale(g, -1.0, 1.0, origin=(0, 0))
        return g

    @staticmethod
    def paper_pt(view, p):
        if view == "BOT":
            return (p[0], -p[1])
        if view == "AFT":
            return (-p[0], p[1])
        return (p[0], p[1])

    # ------------------------------------------------------------------ solids per view
    def _solids(self):
        m = self.m
        top, front, side = m.top, m.front, m.side

        def poly(pts):
            return Polygon(pts).buffer(0)

        def xb(name):
            b = Polygon(side[name]).bounds
            return b[0], b[2]

        def yb(name):
            ys = [p[0] for p in front[name]]
            return min(ys), max(ys)

        pa = m.pod_axis
        pod_r = max(r for _, r in m.pod_profile)
        plan = {"hull": poly(top["hull"]), "pod": _both(poly(top["pod"])), "wing": _both(poly(top["wing"])),
                "fin": _both(poly(top["fin"])),
                # the gun as built (recipe parts.gun.cylinders: body, barrel, muzzle), not the layout's outline
                "gun": _both(unary_union([box(c["x"][0], c["y"] - c["r"], c["x"][1], c["y"] + c["r"])
                                          for c in m.recipe["parts"]["gun"]["cylinders"]])),
                "missile_rack": _both(box(xb("missile_rack")[0], yb("missile_rack")[0], xb("missile_rack")[1],
                                          yb("missile_rack")[1])),
                "gear_main": _both(box(xb("gear_main")[0], yb("gear_main")[0], xb("gear_main")[1], yb("gear_main")[1])),
                "gear_nose": box(xb("gear_nose")[0], yb("gear_nose")[0], xb("gear_nose")[1], yb("gear_nose")[1])}
        end = {"hull": poly(front["hull"]), "pod": _both_end(Point(pa[0], pa[1]).buffer(pod_r, 64)),
               "wing": _both_end(poly(front["wing"])), "fin": _both_end(poly(front["fin"])),
               "gun": _both_end(poly(front["gun"])), "missile_rack": _both_end(poly(front["missile_rack"])),
               "gear_main": _both_end(poly(front["gear_main"])), "gear_nose": poly(front["gear_nose"])}
        for view in ("TOP", "BOT", "AFT", "FWD"):
            src = plan if view in ("TOP", "BOT") else end
            out, cover = {}, Polygon()
            for k, name in enumerate(ORDER[view]):
                g = self.paper(view, src[name])
                vis = em.polys_only(g.difference(cover).buffer(0)) if not cover.is_empty else g
                if view == "TOP" and name.startswith("gear"):
                    vis = Polygon()
                out[name] = {"poly": g, "visible": vis, "rank": len(ORDER[view]) - k,
                             "material": m.solids[name]["material"]}
                cover = unary_union([cover, g])
            self.solids[view] = out
        self.canopy["TOP"] = poly(top["canopy"])
        self.canopy["BOT"] = Polygon()
        self.canopy["AFT"] = Polygon()
        self.canopy["FWD"] = poly(front["canopy"])
        # PORT: the starboard solids (the frame mirrors them)
        self.solids["PORT"] = {name: dict(s, rank=0) for name, s in m.solids.items()}
        self.canopy["PORT"] = m.canopy
        self.solids["SB"] = m.solids
        self.canopy["SB"] = m.canopy
        # the hull's aft wall (section at the stern) and the nose tip seen from ahead
        zb, zt = m.zspan(0.0)
        hw = m.hw(0.0)
        self.aft_wall = Polygon([(u * hw, zb + v * (zt - zb)) for u, v in m.section]).buffer(0)
        self.ramp = box(-1.15, -0.12, 1.15, 1.35)

    def section_at(self, x):
        zb, zt = self.m.zspan(x)
        hw = self.m.hw(x)
        return Polygon([(u * hw, zb + v * (zt - zb)) for u, v in self.m.section]).buffer(0)

    # ------------------------------------------------------------------ placing
    def put(self, e, view, shape, kind, solid, anchor=None, up=None, ghost=None, seams=None, marks=None):
        """An element's geometry in a view (ship-plane coordinates of that view, turned to paper axes here); several
        calls for one view (both sides, both pods) add up. marks: [(point, up)] the reading direction of each copy
        of a lettered marking."""
        if shape is None or shape.is_empty:
            return
        shape = self.paper(view, shape)
        if marks:
            marks = [(self.paper_pt(view, pt), self.paper_pt(view, u)) for pt, u in marks]
        if anchor is not None:
            anchor = self.paper_pt(view, anchor)
        if ghost is not None:
            ghost = self.paper(view, ghost)
        if up is not None:
            up = self.paper_pt(view, up)
        old = e.geo.get(view)
        if old is not None:
            shape = unary_union([old["shape"], shape])
            if ghost is not None and old.get("ghost") is not None:
                ghost = unary_union([old["ghost"], ghost])
            ghost = ghost if ghost is not None else old.get("ghost")
            anchor = old["anchor"] if old.get("anchor_set") else anchor
            up = old.get("up") or up
            seams = (old.get("seams") or []) + (seams or [])
            marks = (old.get("marks") or []) + (marks or [])
        sol = self.solids[view][solid]
        vis_part, vis_frac = None, 1.0
        if kind == "area":
            vis_part = shape.intersection(sol["visible"])
            vis_frac = vis_part.area / shape.area if shape.area > 0 else 1.0
            if vis_part.area < max(0.15 * shape.area, 0.0004) or vis_part.area < 1e-5:
                vis_part = None
        anchor_set = anchor is not None
        if anchor is None:
            if vis_part is not None:
                a = em.largest(em.polys_only(vis_part))
                a = a.representative_point() if not a.is_empty else shape.representative_point()
            elif kind == "area":
                a = shape.representative_point()
            elif kind == "line":
                a = em.largest_line(shape).interpolate(0.5, normalized=True)
            else:
                parts_ = [g for g in getattr(shape, "geoms", [shape])]
                a = max(parts_, key=lambda g: (g.area, g.centroid.x)).centroid
            anchor = (a.x, a.y)
            if view in ("AFT", "FWD") and abs(anchor[0]) < 0.3:
                # a body or line on the centre line seen end-on: point at its starboard (AFT) / port (FWD) half,
                # so the labels of the centre line do not run down one line
                half = shape.intersection(box(0.35, -10, 20, 10))
                if not half.is_empty:
                    h_ = em.largest(em.polys_only(half)) if half.area > 0 else em.largest_line(half)
                    q = h_.representative_point() if half.area > 0 else h_.interpolate(0.3, normalized=True)
                    anchor = (q.x, q.y)
        if kind == "area":
            hidden = vis_part is None
        else:
            hidden = False
            p = Point(anchor)
            for oname, o in self.solids[view].items():
                if oname != solid and o["rank"] > sol["rank"] and o["poly"].buffer(-0.005).contains(p):
                    hidden = True
                    break
        e.geo[view] = {"shape": shape, "kind": kind, "anchor": anchor, "anchor_set": anchor_set, "solid": solid,
                       "depth": sol["rank"], "hidden": hidden, "vis_frac": vis_frac, "up": up, "ghost": ghost,
                       "seams": seams, "marks": marks or None}
        e.views.add(view)

    # ------------------------------------------------------------------ side skin seen from above and below
    def chamfer(self, top):
        return self.m.hull_band(0.0, 21.0, V_UP if top else 0.0, 1.0 if top else V_LO)

    def side_to_plan(self, g, top):
        """Starboard (x, z) geometry on the hull side: the part on the upper (top) or lower chamfer, mapped to plan
        (x, y) of the starboard side (y < 0)."""
        part = g.intersection(self.chamfer(top))
        if part.is_empty:
            return part
        m = self.m
        return _apply(lambda x, z: (x, -m.hull_y(x, z)), part)

    def plan_strip(self, x0, x1, top, z_from=None):
        """The flat roof (top) or keel (bottom) between x0 and x1 in plan; with z_from only where the roof rises
        above (keel lies below) that height - an aft cap "z above 2.2" starts where the sloping stern top gets there."""
        xs = [x0 + (x1 - x0) * k / 80 for k in range(81)]
        if z_from is not None:
            xs = [x for x in xs if (self.m.zspan(x)[1] >= z_from if top else self.m.zspan(x)[0] <= z_from)]
        if len(xs) < 2:
            return Polygon()
        u = self.m.u_out(1.0 if top else 0.0)
        pts = [(x, self.m.hw(x) * u) for x in xs] + [(x, -self.m.hw(x) * u) for x in reversed(xs)]
        return Polygon(pts).buffer(0).intersection(self.solids["TOP"]["hull"]["poly"])

    def map_side(self, e):
        """An element on the hull's side skin, where it lies on a chamfer: in TOP / BOT (both sides when mirrored)."""
        sb = e.geo.get("SB")
        if not sb or sb["solid"] != "hull" or sb["kind"] not in ("area", "line") or e.id in NOT_MAPPED:
            return
        mirrored = not (e.qty == 1 and e.data.get("mirror") is False) and not (
            e.extra.get("setup") and not e.data.get("symmetric"))
        for view, top in (("TOP", True), ("BOT", False)):
            g = self.side_to_plan(sb["shape"], top)
            if sb["kind"] == "area":
                g = em.polys_only(g.buffer(0))
                if g.is_empty or g.area < 0.004:
                    continue
            else:
                if g.is_empty or g.length < 0.05:
                    continue
            ghost = e.extra.get("ghost")
            gp = None
            if ghost is not None and not isinstance(ghost, LineString):
                gp = em.polys_only(self.side_to_plan(ghost, top).buffer(0))
                gp = None if gp.is_empty else gp
            shape = _both(g) if mirrored else g
            self.put(e, view, shape, sb["kind"], "hull", ghost=_both(gp) if (gp is not None and mirrored) else gp)

    # ------------------------------------------------------------------ pods
    def pod_patch(self, xr, dr, step=0.1):
        """Plan area of a patch of the port pod: x range x angle range (0 outboard, 90 up, 180 inboard)."""
        m = self.m
        xs = [xr[0]]
        while xs[-1] + step < xr[1]:
            xs.append(xs[-1] + step)
        xs.append(xr[1])
        ds = [dr[0] + (dr[1] - dr[0]) * k / 12 for k in range(13)]
        out = []
        for x0, x1 in zip(xs, xs[1:]):
            for d0, d1 in zip(ds, ds[1:]):
                pts = [(x0, m.pod_axis[0] + m.pod_r(x0) * math.cos(math.radians(d0))),
                       (x1, m.pod_axis[0] + m.pod_r(x1) * math.cos(math.radians(d0))),
                       (x1, m.pod_axis[0] + m.pod_r(x1) * math.cos(math.radians(d1))),
                       (x0, m.pod_axis[0] + m.pod_r(x0) * math.cos(math.radians(d1)))]
                out.append(Polygon(pts).buffer(1e-6))
        return unary_union(out).buffer(-1e-6)

    def pod_item(self, e, x, deg, w, h, rot=0.0, kind="area", ghost_of=None):
        """A small item on the pods' surface at (x, angle), footprint w along x and h round: from above when it faces
        up, from below when it faces down (both pods)."""
        if rot % 180 == 90:
            w, h = h, w
        s = math.sin(math.radians(deg))
        if abs(s) <= 0.17:
            return
        view = "TOP" if s > 0 else "BOT"
        m = self.m
        yc = m.pod_axis[0] + m.pod_r(x) * math.cos(math.radians(deg))
        hh = max(h * abs(s), 0.012)
        g = _both(box(x - w / 2, yc - hh / 2, x + w / 2, yc + hh / 2))
        self.put(e, view, g, kind, "pod", ghost=ghost_of)

    # ------------------------------------------------------------------ build all views
    def build(self):
        m = self.m
        for e in m.elements:
            e.geo = {"SB": e.sb}
            e.vextra = {"SB": {"ghost": e.extra.get("ghost"), "seams": e.extra.get("seams"), "up": e.extra.get("up")}}
        for e in m.elements:
            if e.cat in CATS_MAPPED and e.sb and e.status != "remove" or (e.cat in ("plate", "zone") and e.sb):
                self.map_side(e)
        self._parts()
        self._zones_plates()
        self._pod_things()
        self._top_bottom_items()
        self._aft_items()
        self._end_profiles()
        self._design()
        self._port()
        for e in m.elements:
            for view, g in e.geo.items():
                if view != "SB" and g is not None:
                    e.vextra[view] = {"ghost": g.get("ghost"), "seams": g.get("seams"), "up": g.get("up"),
                                      "marks": g.get("marks")}
        m.view_solids = self.solids
        m.view_canopy = self.canopy
        m.views_model = self
        # a view tag means a drawing: tags the starboard model set without geometry are what this module misses
        m.views_missing = sorted((e.id, v) for e in m.elements for v in e.views
                                 if v in VIEWS and e.geo.get(v) is None)

    def _parts(self):
        m = self.m
        for ident, solid, views in (("P-HULL", "hull", ("TOP", "BOT", "AFT", "FWD")),
                                    ("P-POD", "pod", ("TOP", "BOT", "AFT", "FWD")),
                                    ("F-WING", "wing", ("TOP", "BOT", "AFT", "FWD")),
                                    ("F-FIN", "fin", ("TOP", "AFT", "FWD")),
                                    ("F-GUN-S3", "gun", ("TOP", "BOT", "AFT", "FWD")),
                                    ("F-MISSILE-S2", "missile_rack", ("BOT", "AFT", "FWD")),
                                    ("F-GEAR-MAIN", "gear_main", ("BOT", "AFT", "FWD")),
                                    ("F-GEAR-NOSE", "gear_nose", ("BOT", "AFT", "FWD"))):
            e = m.by_id[ident]
            for view in views:
                s = self.solids[view][solid]
                g = s["poly"]
                # put() takes ship-plane coordinates; the solids are stored on paper already
                self.put(e, view, self.paper(view, g), "area", solid)
        # gun collars: rings round the gun at its mount stations
        gm = m.by_id["F-GUNMOUNT-01"]
        d = gm.data
        r = d["r"] + 0.03
        plan = _both(unary_union([box(a - 0.06, d["y"] - r, a + 0.06, d["y"] + r) for a in d["at"]]))
        for view in ("TOP", "BOT"):
            self.put(gm, view, plan, "area", "gun")
        ring = _both_end(Point(d["y"], d["z"]).buffer(r, 32).difference(Point(d["y"], d["z"]).buffer(d["r"], 32)))
        for view in ("AFT", "FWD"):
            self.put(gm, view, ring, "area", "gun")
        # pod exhaust (aft) and intake (ahead), the glowing nozzle floor
        rev = m.recipe["parts"]["pod"]["revolve"]
        pa = m.pod_axis
        ex, it = rev["exhaust"], rev["intake"]
        c = Point(pa[0], pa[1])
        self.put(m.by_id[ex["id"]], "AFT", _both_end(c.buffer(ex["r_lip"], 64).difference(c.buffer(ex["r_duct"], 64))),
                 "area", "pod")
        self.put(m.by_id["F-NOZZLE"], "AFT", _both_end(c.buffer(ex["r_duct"], 64)), "area", "pod")
        self.put(m.by_id[it["id"]], "FWD", _both_end(c.buffer(it["r_lip"], 64)), "area", "pod")
        # canopy frame struts across the glass, from above
        cf = m.by_id["F-CANOPY-FRAME"]
        w = cf.data["strut_width"] / 2
        struts = unary_union([self.canopy["TOP"].intersection(box(x - w, -5, x + w, 5)) for x in cf.data["struts_x"]])
        self.put(cf, "TOP", struts, "area", "hull", anchor=(cf.data["struts_x"][0], 0.0))
        # the plan of the pod pipe run on the pod's inboard side
        pr = m.by_id["F-POD-PIPES"]
        xs = [pr.data["x"][0] + (pr.data["x"][1] - pr.data["x"][0]) * k / 20 for k in range(21)]
        line = LineString([(x, pa[0] - m.pod_r(x) - pr.data.get("standoff", 0.035)) for x in xs])
        self.put(pr, "TOP", _both(line.buffer(0.03, cap_style=2)), "area", "pod")

    def _zones_plates(self):
        m = self.m
        for z in m.recipe["parts"]["hull"].get("zones", []):
            e = m.by_id[z["id"]]
            w = dict(z["where"])
            if e.change and "where.x" in e.change:
                w["x"] = e.change["where.x"]
            if e.change and "where.z" in e.change:
                w["z"] = e.change["where.z"]
            xs = w.get("x", [-1, 22])
            zs = w.get("z", [-5, 6])
            x0, x1 = max(xs[0], 0.0), min(xs[1], 21.0)
            for view, top in (("TOP", True), ("BOT", False)):
                if "normal_abs_y_min" in w:
                    continue
                if top and zs[1] >= max(m.zspan(x)[1] for x in (x0 + 0.01, (x0 + x1) / 2, x1 - 0.01)):
                    self.put(e, view, self.plan_strip(x0, x1, True, z_from=zs[0]), "area", "hull")
                elif not top and zs[0] <= min(m.zspan(x)[0] for x in (x0 + 0.01, (x0 + x1) / 2, x1 - 0.01)):
                    self.put(e, view, self.plan_strip(x0, x1, False, z_from=zs[1]), "area", "hull")
            # seen from ahead: the nose tip in front of x0; from behind: the cap on the aft wall
            if x1 >= 21.0:
                self.put(e, "FWD", self.section_at(x0), "area", "hull")
            if x0 <= 0.0:
                self.put(e, "AFT", self.aft_wall.intersection(box(-5, zs[0], 5, zs[1])), "area", "hull")
        # the canopy seal (design) seen from above and from ahead
        seal = m.by_id["Z-SEAL-CANOPY"]
        wd = seal.data["w"]
        for view in ("TOP", "FWD"):
            c = self.canopy[view]
            self.put(seal, view, c.buffer(wd, join_style=2).difference(c), "area", "hull")
        # recipe plates and recesses facing up / down / aft
        for p in m.recipe["detail"].get("hull_plates", []) + m.recipe["detail"].get("hull_recesses", []):
            e = m.by_id[p["id"]]
            nz = p.get("normal_z")
            if p.get("centre") and "z" in p and "normal_x" not in p and not nz:
                # a centre plate over the roof (the dark aft cap plate P-B-01): its roof part, the chamfers map
                self.put(e, "TOP", self.plan_strip(p["x"][0], p["x"][1], True, z_from=p["z"][0]), "area", "hull")
                continue
            if "abs_y" in p and nz and abs(nz[0]) >= 0.85 and "normal_x" not in p:
                ay = p["abs_y"]
                g = box(p["x"][0], -ay[1], p["x"][1], ay[1]) if p.get("centre") or ay[0] == 0 else \
                    _both(box(p["x"][0], ay[0], p["x"][1], ay[1]))
                self.put(e, "TOP" if nz[0] > 0 else "BOT", g, "area", "hull")
            elif "normal_x" in p:
                ay = p["abs_y"]
                g = box(-ay[1], p["z"][0], ay[1], p["z"][1]) if p.get("centre") else \
                    _both_end(box(ay[0], p["z"][0], ay[1], p["z"][1]))
                self.put(e, "AFT", g.intersection(self.aft_wall.buffer(0.3)), "area", "hull")

    def _pod_things(self):
        m = self.m
        rev = m.recipe["parts"]["pod"]["revolve"]
        # pod sections with their panel seams; pod armour plates; the open bay
        for s in rev["sections"]:
            e = m.by_id[s["id"]]
            for view, sg in (("TOP", 1), ("BOT", -1)):
                d0, d1 = (0.0, 180.0) if sg > 0 else (180.0, 360.0)
                area = self.pod_patch(s["x"], (d0, d1))
                seams = []
                if s["kind"] == "panels":
                    xs = [s["x"][0] + 0.01 + k * (s["x"][1] - s["x"][0] - 0.02) / 12 for k in range(13)]
                    for k in range(s["around"]):
                        deg = (s.get("phase_deg", 0) + k * 360.0 / s["around"]) % 360
                        if math.sin(math.radians(deg)) * sg > 0.05:
                            ln = LineString([(x, m.pod_axis[0] + m.pod_r(x) * math.cos(math.radians(deg))) for x in xs])
                            seams += [self.paper(view, ln), self.paper(view, _mirror_y(ln))]
                    for k in range(1, s.get("rows", 1)):
                        x = s["x"][0] + k * (s["x"][1] - s["x"][0]) / s["rows"]
                        ln = LineString([(x, m.pod_axis[0] - m.pod_r(x)), (x, m.pod_axis[0] + m.pod_r(x))])
                        seams += [self.paper(view, ln), self.paper(view, _mirror_y(ln))]
                self.put(e, view, _both(area), "area", "pod", seams=seams,
                         anchor=((s["x"][0] + s["x"][1]) / 2, m.pod_axis[0] + (0.55 if s["kind"] == "panels" else -0.6)))
        for p in m.recipe["detail"]["pod"].get("plates", []):
            e = m.by_id[p["id"]]
            d0, d1 = p["deg"]
            mid = math.sin(math.radians((d0 + d1) / 2))
            view = "TOP" if mid > 0 else "BOT"
            self.put(e, view, _both(self.pod_patch(p["x"], (d0, d1))), "area", "pod")
        bay = m.recipe["detail"]["pod"]["bay"]
        self.put(m.by_id[bay["id"]], "TOP", _both(self.pod_patch(bay["x"], (max(bay["deg"][0], 8.0), bay["deg"][1]))),
                 "area", "pod")
        # greebles, functional parts, lenses, strips, decals and trims on the pods
        from exterior_model import FUNC_SIZE, GREEBLE_SIZE
        for g in rev.get("greebles", []):
            sx, sy, _ = GREEBLE_SIZE[g["part"]]
            self.pod_item(m.by_id[g["id"]], g["x"], g["angle_deg"], sx, sy)
        for it in m.recipe["functional"].get("items", []):
            if it["on"] != "pod":
                continue
            e = m.by_id[it["id"]]
            fx, fy, _ = FUNC_SIZE[it["kind"]]
            s = it.get("size", 1.0)
            if e.change and e.change.get("kit"):
                fx, fy, _ = m.kit[e.change["kit"]]["size"]
                s = 1.0
            self.pod_item(e, it["x"], it["deg"], fx * s, fy * s, it.get("rot", 0.0))
        for it in m.recipe["lights"].get("lenses", []):
            if it["on"] == "pod":
                self.pod_item(m.by_id[it["id"]], it["x"], it["deg"], max(it["size"][0], 0.08), max(it["size"][1], 0.04))
        for it in m.recipe["lights"].get("strips", []):
            if it.get("on", "pod") != "pod":
                continue
            e = m.by_id[it["id"]]
            s = math.sin(math.radians(it["deg"]))
            if abs(s) <= 0.17:
                continue
            r = it.get("r")
            xs = [it["x"][0] + k * (it["x"][1] - it["x"][0]) / 10 for k in range(11)]
            ln = LineString([(x, m.pod_axis[0] + (r if r else m.pod_r(x)) * math.cos(math.radians(it["deg"]))) for x in xs])
            self.put(e, "TOP" if s > 0 else "BOT", _both(ln), "line", "pod")
        for it in m.recipe["decals"].get("items", []):
            if it["on"] != "pod":
                continue
            e = m.by_id[it["id"]]
            w, h = e.extra["size"]
            along = it.get("along")
            x = it["x"] + (along["step"] * (along["count"] - 1) / 2 if along else 0.0)
            ww = w + (along["step"] * (along["count"] - 1) if along else 0.0)
            self.pod_item(e, x, it["deg"], ww, h, it.get("rot", 0.0))
        for it in m.recipe["decals"].get("trim", []):
            if it["on"] != "pod_ring":
                continue
            e = m.by_id[it["id"]]
            for view, sg in (("TOP", 1), ("BOT", -1)):
                d0, d1 = it["deg"]
                ys = []
                k = d0
                while k <= d1 + 1e-6:
                    if math.sin(math.radians(k)) * sg > 0.05:
                        ys.append(m.pod_axis[0] + m.pod_r(it["x"]) * math.cos(math.radians(k)))
                    k += 5
                if ys:
                    ln = LineString([(it["x"], min(ys)), (it["x"], max(ys))])
                    self.put(e, view, _both(ln), "line", "pod")
        for it in m.design.get("functional", []):
            if it["on"] == "pod":
                e = m.by_id[it["id"]]
                k = m.kit[it["kit"]]
                self.pod_item(e, it["x"], it["deg"], k["size"][0], k["size"][1])

    def _top_bottom_items(self):
        """Items the recipe places from above or below at (x, y): greebles (once), functional parts, lenses, decals
        (both sides unless "mirror": false), the belly light strip and the belly trim line."""
        m = self.m
        from exterior_model import FUNC_SIZE, GREEBLE_SIZE

        def sides(it, default=True):
            return (1, -1) if it.get("mirror", default) else (1,)

        for g in m.recipe["parts"]["hull"].get("greebles", []):
            if g["from"] == "side":
                continue
            sx, sy, _ = GREEBLE_SIZE[g["part"]]
            self.put(m.by_id[g["id"]], "TOP" if g["from"] == "top" else "BOT", box(g["x"] - sx / 2, g.get("y", 0) - sy / 2,
                                                                                   g["x"] + sx / 2, g.get("y", 0) + sy / 2),
                     "area", "hull")
        for it in m.recipe["functional"].get("items", []):
            if it["on"] not in ("top", "bottom"):
                continue
            e = m.by_id[it["id"]]
            fx, fy, _ = FUNC_SIZE[it["kind"]]
            s = it.get("size", 1.0)
            if e.change and e.change.get("kit"):
                fx, fy, _ = m.kit[e.change["kit"]]["size"]
                s = 1.0
            w, h = (fy * s, fx * s) if it.get("rot", 0) % 180 == 90 else (fx * s, fy * s)
            g = unary_union([box(it["x"] - w / 2, sd * it.get("y", 0) - h / 2, it["x"] + w / 2, sd * it.get("y", 0) + h / 2)
                             for sd in sides(it)])
            solid = self._landing_plan(it["x"], it.get("y", 0), it["on"] == "top")
            self.put(e, "TOP" if it["on"] == "top" else "BOT", g, "area", solid)
        for it in m.recipe["lights"].get("lenses", []):
            e = m.by_id[it["id"]]
            w, h = it["size"][0], it["size"][1]
            if it["on"] in ("top", "bottom"):
                g = unary_union([box(it["x"] - w / 2, sd * it.get("y", 0) - h / 2, it["x"] + w / 2, sd * it.get("y", 0) + h / 2)
                                 for sd in sides(it)])
                self.put(e, "TOP" if it["on"] == "top" else "BOT", g, "area", "hull")
            elif it["on"] == "ray" and it["dir"][0] == 0:
                hit = m.section_hit(it["at"][0], it["at"][1], it["at"][2], it["dir"][1], it["dir"][2])
                if hit and abs(hit[2][1]) > 0.3:
                    y = hit[1][0]
                    view = "TOP" if hit[2][1] > 0 else "BOT"
                    g = unary_union([box(it["at"][0] - w / 2, sd * y - h / 2, it["at"][0] + w / 2, sd * y + h / 2)
                                     for sd in sides(it)])
                    self.put(e, view, g, "area", "hull")
        for it in m.recipe["lights"].get("strips", []):
            if it.get("on") == "bottom":
                e = m.by_id[it["id"]]
                g = unary_union([LineString([(it["x"][0], sd * it["y"]), (it["x"][1], sd * it["y"])]) for sd in sides(it)])
                self.put(e, "BOT", g, "line", "hull")
        for it in m.recipe["decals"].get("items", []):
            e = m.by_id[it["id"]]
            ch = m.changes.get(it["id"], {}).get("set") or {}
            w, h = e.extra["size"]
            rot = it.get("rot", 0.0)
            along = it.get("along")
            n = along["count"] if along else 1
            if it["on"] in ("top", "bottom"):
                top = it["on"] == "top"
                y0 = it.get("y", 0.0)
                # reading direction (hs_decals._frame): roof and belly read from the nearer side of the ship (a
                # copy at y > 5 cm from port, otherwise from starboard); rot turns about the outward normal, which
                # is counter-clockwise from above and clockwise in plan axes from below
                r_ = rot if top else -rot
                parts, marks = [], []
                for sd in sides(it):
                    yy = sd * y0
                    up = _rot((0.0, -1.0) if yy > 0.05 else (0.0, 1.0), r_)
                    for k in range(n):
                        x = it["x"] + (along["step"] * k if along else 0.0)
                        parts.append(_rbox(x, yy, w, h, r_))
                        marks.append(((x, yy), up))
                solid = self._landing_plan(it["x"], y0, top)
                self.put(e, "TOP" if top else "BOT", unary_union(parts), "area", solid,
                         anchor=(it["x"], y0), marks=marks if e.extra.get("text") else None)
            elif it["on"] == "ray" and it["dir"][0] == 0:
                hit = m.section_hit(it["at"][0], it["at"][1], it["at"][2], it["dir"][1], it["dir"][2])
                if not hit or abs(hit[2][1]) <= 0.3:
                    continue
                y = hit[1][0]
                view = "TOP" if hit[2][1] > 0 else "BOT"
                hh = h * abs(hit[2][1])
                parts = []
                for sd in sides(it):
                    for k in range(n):
                        x = it["at"][0] + (along["step"] * k if along else 0.0)
                        parts.append(box(x - w / 2, sd * y - hh / 2, x + w / 2, sd * y + hh / 2))
                self.put(e, view, unary_union(parts), "area", "hull")
        for it in m.recipe["decals"].get("trim", []):
            if it["on"] == "bottom_line":
                e = m.by_id[it["id"]]
                self.put(e, "BOT", LineString([(it["a"][0], it["a"][1]), (it["b"][0], it["b"][1])]), "line", "hull")

    def _end_profiles(self):
        """Functional parts on the hull near the bow (x >= 15, seen from ahead) or the stern (x <= 3, from behind):
        their profile standing out of the surface - the bow RCS blocks are the part of the spec's 8 thrusters only
        an end view shows (critic of the views, round 2)."""
        m = self.m
        from exterior_model import FUNC_SIZE
        for it in m.recipe["functional"].get("items", []):
            if it["on"] not in ("side", "top", "bottom"):
                continue
            x = it["x"]
            view = "FWD" if x >= 15.0 else ("AFT" if x <= 3.0 else None)
            if view is None:
                continue
            e = m.by_id[it["id"]]
            fx, fy, fh = FUNC_SIZE[it["kind"]]
            s_ = it.get("size", 1.0)
            if e.change and e.change.get("kit"):
                fx, fy, fh = m.kit[e.change["kit"]]["size"]
                s_ = 1.0
            fx, fy, fh = fx * s_, fy * s_, fh * s_
            sides = (1, -1) if it.get("mirror", True) else (1,)
            if it["on"] == "side":
                h = fx if it.get("rot", 0) % 180 == 90 else fy
                y0 = m.hull_y(x, it["z"])
                g = unary_union([box(sd * y0, it["z"] - h / 2, sd * (y0 + fh), it["z"] + h / 2) if sd > 0 else
                                 box(sd * (y0 + fh), it["z"] - h / 2, sd * y0, it["z"] + h / 2) for sd in sides])
            else:
                zb, zt = m.zspan(x)
                y = it.get("y", 0.0)
                z0, z1 = (zt, zt + fh) if it["on"] == "top" else (zb - fh, zb)
                g = unary_union([box(sd * y - fy / 2, z0, sd * y + fy / 2, z1) for sd in sides])
            self.put(e, view, g, "area", "hull")

    def _landing_plan(self, x, y, top):
        """The solid a ray from above (top) or below at plan (x, y) hits first."""
        p = Point(x, y if top else -y)
        view = "TOP" if top else "BOT"
        best = None
        for name, s in self.solids[view].items():
            if s["poly"].buffer(0.005).contains(p) and (best is None or s["rank"] > best[1]):
                best = (name, s["rank"])
        return best[0] if best else "hull"

    def _aft_items(self):
        """The aft wall (rays along +x from behind the stern): plates are in _zones_plates; RCS blocks, lenses, decals
        and the ramp outline here (AFT coordinates (y, z), both sides unless "mirror": false)."""
        m = self.m
        from exterior_model import FUNC_SIZE

        def sides(it):
            return (1, -1) if it.get("mirror", True) else (1,)

        for it in m.recipe["functional"].get("items", []):
            if it["on"] == "ray" and it["dir"][0] != 0:
                e = m.by_id[it["id"]]
                fx, fy, _ = FUNC_SIZE[it["kind"]]
                s = it.get("size", 1.0)
                if e.change and e.change.get("kit"):
                    fx, fy, _ = m.kit[e.change["kit"]]["size"]
                    s = 1.0
                g = unary_union([box(sd * it["at"][1] - fx * s / 2, it["at"][2] - fy * s / 2,
                                     sd * it["at"][1] + fx * s / 2, it["at"][2] + fy * s / 2) for sd in sides(it)])
                self.put(e, "AFT" if it["dir"][0] > 0 else "FWD", g, "area", "hull")
        for it in m.recipe["lights"].get("lenses", []):
            if it["on"] == "ray" and it["dir"][0] != 0:
                e = m.by_id[it["id"]]
                w, h = it["size"][0], it["size"][1]
                g = unary_union([box(sd * it["at"][1] - w / 2, it["at"][2] - h / 2, sd * it["at"][1] + w / 2,
                                     it["at"][2] + h / 2) for sd in sides(it)])
                self.put(e, "AFT" if it["dir"][0] > 0 else "FWD", g, "area", "hull")
        for it in m.recipe["decals"].get("items", []):
            if it["on"] != "ray" or it["dir"][0] == 0:
                continue
            e = m.by_id[it["id"]]
            w, h = e.extra["size"]
            rot = it.get("rot", 0.0)
            # aft face: the item's x runs across the ship, to the viewer's right (hs_decals._frame); rot about n
            parts = [_rbox(-sd * it["at"][1], it["at"][2], w, h, rot) for sd in sides(it)]
            g = self.paper("AFT", unary_union(parts))       # built in paper axes: undo put()'s turn
            up = self.paper_pt("AFT", _rot((0.0, 1.0), rot))
            marks = [((sd * it["at"][1], it["at"][2]), up) for sd in sides(it)]
            self.put(e, "AFT", g, "area", "hull", anchor=(it["at"][1], it["at"][2]),
                     marks=marks if e.extra.get("text") else None)
        for it in m.recipe["decals"].get("trim", []):
            if it["on"] == "ray_line":
                e = m.by_id[it["id"]]
                ln = LineString([(p[1], p[2]) for p in it["points"]])
                self.put(e, "AFT", ln, "line", "hull")
        # the big projected markings of the setup on the aft wall (Unreal decal components)
        off = m.recipe["assemble"]["offset"]
        for e in m.elements:
            if e.cat != "decal" or not e.extra.get("setup"):
                continue
            d = dict(e.data)
            if e.change and "location" in e.change:
                d["location"] = e.change["location"]
            loc = (d["location"][0] / 100.0 - off[0], -d["location"][1] / 100.0 - off[1], d["location"][2] / 100.0 - off[2])
            X = em.x_axis(d["rotation"])
            if abs(X[0]) > 0.7 and loc[0] < 1.0:
                Y = em.y_axis(d["rotation"])
                Z = (X[1] * Y[2] - X[2] * Y[1], X[2] * Y[0] - X[0] * Y[2], X[0] * Y[1] - X[1] * Y[0])
                sy, sz = d["size"][1] / 100.0, d["size"][2] / 100.0
                ey = abs(Y[1]) * sy + abs(Z[1]) * sz
                ez = abs(Y[2]) * sy + abs(Z[2]) * sz
                self.put(e, "AFT", box(loc[1] - ey / 2, loc[2] - ez / 2, loc[1] + ey / 2, loc[2] + ez / 2), "area", "hull")

    def _design(self):
        """The proposed design parts outside the starboard view: ramp pistons and the ramp light on the aft wall,
        the strobes seen from above, below, behind and ahead, the landing light from below and ahead."""
        m = self.m
        for it in m.design.get("functional", []):
            if it["on"] != "aft":
                continue
            e = m.by_id[it["id"]]
            k = m.kit[it["kit"]]
            if it["kind"] == "frame":
                # a U round the ramp opening: both sides and the top (the deck lip closes it at the bottom)
                (y0, y1), (z0, z1), w = it["y"], it["z"], it["w"]
                g = box(y0, z0, y1, z1).difference(box(y0 + w, z0 - 1.0, y1 - w, z1 - w))
                self.put(e, "AFT", g, "area", "hull", anchor=(y1 - w / 2, (z0 + z1) / 2))
                continue
            w = k["size"][0] if "size" in k else k["d"]
            g = unary_union([box(sd * it["y"] - w / 2, it["z"][0], sd * it["y"] + w / 2, it["z"][1])
                             for sd in ((1, -1) if it.get("mirror", True) else (1,))])
            self.put(e, "AFT", g, "area", "hull")
        fin_tip_y = max(p[0] for p in m.front["fin"])
        for it in m.design.get("lights", []):
            e = m.by_id[it["id"]]
            k = m.kit[it["kit"]]
            w, h = k["size"][0], k["size"][1]
            sides = (1, -1) if it.get("mirror", True) else (1,)
            on = it["on"]
            if on == "fin_tip":
                ytip = max(p[1] for p in m.top["fin"])
                self.put(e, "TOP", unary_union([box(it["x"] - w / 2, sd * (ytip - 0.12) - 0.04, it["x"] + w / 2,
                                                    sd * (ytip - 0.12) + 0.04) for sd in sides]), "area", "fin")
                for view in ("AFT", "FWD"):
                    self.put(e, view, unary_union([box(sd * fin_tip_y - 0.05, it["z"] - 0.01, sd * fin_tip_y + 0.05,
                                                       it["z"] + 0.04) for sd in sides]), "profile", "fin")
            elif on == "wing_tip":
                for view in ("TOP", "BOT"):
                    self.put(e, view, unary_union([box(it["x"] - w / 2, sd * it["y"] - 0.05, it["x"] + w / 2,
                                                       sd * it["y"] + 0.02) for sd in sides]), "area", "wing")
                for view in ("AFT", "FWD"):
                    self.put(e, view, unary_union([box(sd * it["y"] - 0.04, it["z"] - h / 2, sd * it["y"] + 0.04,
                                                       it["z"] + h / 2) for sd in sides]), "area", "wing")
            elif on == "bottom":
                zb = m.zspan(it["x"])[0]
                self.put(e, "BOT", unary_union([box(it["x"] - w / 2, sd * it["y"] - h / 2, it["x"] + w / 2,
                                                    sd * it["y"] + h / 2) for sd in sides]), "area", "hull")
                self.put(e, "FWD", box(it["y"] - h / 2, zb - k["size"][2], it["y"] + h / 2, zb), "profile", "hull")
            elif on == "aft":
                self.put(e, "AFT", unary_union([box(sd * it["y"] - w / 2, it["z"] - h / 2, sd * it["y"] + w / 2,
                                                    it["z"] + h / 2) for sd in sides]), "area", "hull")

    def _port(self):
        """The port side: everything on both sides as on the starboard view (x, z; the frame mirrors it - mirrored
        items read right on both sides, hs_decals._frame, so upright stays upright); the setup's port-only markings
        in their own frame (the lettering check of the port side)."""
        m = self.m
        for e in m.elements:
            sb = e.geo.get("SB")
            if e.extra.get("setup") or not sb:
                continue
            g = dict(sb, ghost=e.extra.get("ghost"), seams=e.extra.get("seams"), up=e.extra.get("up"), marks=None)
            e.geo["PORT"] = g
            e.views.add("PORT")
        off = m.recipe["assemble"]["offset"]
        for e in m.elements:
            if e.cat != "decal" or not e.extra.get("setup"):
                continue
            d = dict(e.data)
            old = None
            if e.change and "location" in e.change:
                old = (d["location"][0] / 100.0 - off[0], d["location"][2] / 100.0 - off[2])
                d["location"] = e.change["location"]
            loc = (d["location"][0] / 100.0 - off[0], -d["location"][1] / 100.0 - off[1], d["location"][2] / 100.0 - off[2])
            X = em.x_axis(d["rotation"])
            if loc[1] > 0.5 and abs(X[1]) > 0.7:
                Y = em.y_axis(d["rotation"])
                Z = (X[1] * Y[2] - X[2] * Y[1], X[2] * Y[0] - X[0] * Y[2], X[0] * Y[1] - X[1] * Y[0])
                sy, sz = d["size"][1] / 100.0, d["size"][2] / 100.0
                ex = abs(Y[0]) * sy + abs(Z[0]) * sz
                ez = abs(Y[2]) * sy + abs(Z[2]) * sz
                on_pod = abs(abs(loc[1]) - m.pod_axis[0]) < 1.2 and loc[0] < 6.0 and abs(loc[1]) > 2.6
                solid = "pod" if on_pod else "hull"
                up_sign = 1 if float(d.get("flip_v", 0.0)) >= 0.5 else -1
                up = (Y[0] * up_sign, Y[2] * up_sign)
                g = box(loc[0] - ex / 2, loc[2] - ez / 2, loc[0] + ex / 2, loc[2] + ez / 2)
                ghost = box(old[0] - ex / 2, old[1] - ez / 2, old[0] + ex / 2, old[1] + ez / 2) if old else None
                self.put(e, "PORT", g, "area", solid, anchor=(loc[0], loc[2]), up=up, ghost=ghost)
                e.geo["PORT"]["depth"] = 9.0


def add_views(m):
    """Element.geo[view] for every view, Model.view_solids / view_canopy; Model.use_view() switches."""
    Views(m).build()
