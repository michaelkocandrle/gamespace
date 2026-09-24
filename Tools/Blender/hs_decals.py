"""Mesh decals and trim strips on a hard-surface ship (skill ship-pipeline 3b3), called by hs_assemble_ship.py.

The library (Tools/Blender/decal_library.py) holds the atlases and an index of every item's UV rect, size,
type and tags. This module puts them on the ship from the recipe's "decals" block, in LAYOUT coordinates.
Placement is by RULES, so everything regenerates (a seed fixes the random parts):

  rules.hull_seams      a rivet strip along every panel seam of the hull (rings at the seam stations, lines)
  rules.pod_gaps        ... along every panel gap of the pods (read from the pod recipe)
  rules.plate_edges     a rivet line inside the edges of every armour plate (from the detail recipe)
  rules.panel_marks     a panel number on every pod panel, numbers / stencils on listed hull panels
  rules.clusters        dense scatter of small items round service points (engines, the bay, the intake)
  rules.companions      next to every hatch a service label, a handle and a red marker; chevrons round
                        ports and caps; below grilles (sometimes) a dirt streak
  rules.coverage        a jittered grid over the calm surfaces: at least one small decal per ~0.5 m panel
  rules.panel_lines     thin engraved panel lines with 45-degree jogs (SC density: a line every 0.3-0.8 m)
  items / trim          hand-placed hero decals and strips

Where ("on"): pod (x, deg) / side (x, z) / top / bottom (x, y) / ray (at, dir); "rot" about the normal,
"scale", "mirror" (default true). Ribbons: pod_ring, pod_line, hull_ring, side_line, top_line, bottom_line,
ray_line.

Every decal is a grid of quads laid onto the ship (each vertex ray-cast back along the normal, 2 mm off);
one that would cross an edge is skipped, and two footprints may not overlap (hero items are placed first).
By type (library index):
  structural  normal-only quad (slot Decal) + colour-only AO quad (DecalAO): the hull's paint shows through
  info, wear  own-colour quad (DecalPaint), a hair higher
Trim strips are structural: Trim + TrimAO. All of it is one mesh (the "Decals" part, not Nanite) with the
atlas UVs; no unwrap, no collision. build() also returns the counts per part (pods, hull), rule and type.
"""
import hashlib
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

SLOTS = ("Decal", "DecalAO", "DecalPaint", "Trim", "TrimAO")
POD_Y = 2.38          # |y| beyond this a hit is on a pod (the hull's half width is 2.30)


def _frame(n, rot_deg=0.0, y_hint=0.0):
    """In-surface axes that read right from outside: x to the viewer's right, y = n x x (not mirrored),
    turned by rot_deg about n. Front and back faces: x across the ship."""
    up = Vector((0, 0, 1)) - n * n.z
    if abs(n.z) < 0.9 and abs(n.x) < 0.7 and up.length > 1e-3:
        # sides and slopes: the item's up is up the surface (text upright seen from beside the ship)
        x = up.normalized().cross(n)
    else:
        if abs(n.x) > 0.7:
            ref = Vector((0, 1 if n.x > 0 else -1, 0))
        elif abs(n.z) >= 0.9:
            # roof and belly: read from the nearer side of the ship
            ref = Vector((-1, 0, 0)) if (y_hint > 0.05) == (n.z > 0) else Vector((1, 0, 0))
        else:
            ref = Vector((-1, 0, 0)) if n.y > 0.3 else Vector((1, 0, 0))
        x = ref - n * n.dot(ref)
        if x.length < 1e-4:
            x = n.orthogonal()
    x.normalize()
    if rot_deg:
        x = Matrix.Rotation(math.radians(rot_deg), 3, n) @ x
    return x, n.cross(x)


def _stable(*keys):
    return int(hashlib.md5("|".join(str(k) for k in keys).encode()).hexdigest()[:8], 16)


class Placer:
    def __init__(self, target, spec, index, off, pod_axis):
        bm = bmesh.new()
        bm.from_mesh(target.data)
        bm.transform(target.matrix_world)
        self.tree = BVHTree.FromBMesh(bm)
        bm.free()
        self.offset = spec.get("offset_m", 0.002)
        self.grid_m = spec.get("grid_m", 0.06)
        self.index = index
        self.off = Vector(off)
        self.pod = pod_axis
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.placed = []                  # (centre, radius, x, y, w, h) for the overlap test
        self.frames = []                  # (item, frame) of every placed decal, for the companion rules
        self.log = []                     # (rule, item, part)
        self.ribbons = []                 # (rule, strip, part, metres)
        self.skipped = {"edge": 0, "overlap": 0, "miss": 0}

    # ------------------------------------------------------------------ rays
    def ray(self, spec, side):
        on = spec["on"]
        if on == "pod":
            a = math.radians(spec["deg"] if side > 0 else 180.0 - spec["deg"])
            radial = Vector((0.0, math.cos(a), math.sin(a)))
            return Vector((spec["x"], self.pod[0] * side, self.pod[1])) + radial * 3.0, -radial
        if on == "side":
            return Vector((spec["x"], 10.0 * side, spec["z"])), Vector((0, -side, 0))
        if on in ("top", "bottom"):
            s = 1 if on == "top" else -1
            return Vector((spec["x"], spec.get("y", 0.0) * side, 10.0 * s)), Vector((0, 0, -s))
        if on == "ray":
            at, d = Vector(spec["at"]), Vector(spec["dir"]).normalized()
            at.y *= side
            d.y *= side
            return at - d * 3.0, d
        if on == "hull_ring":
            # from outside the hull towards its centre line at x (pods are rejected by y later)
            a = math.radians(spec["deg"])
            radial = Vector((0.0, math.cos(a), math.sin(a)))
            return Vector((spec["x"], 0.0, spec.get("zc", 1.2))) + radial * 6.0, -radial
        raise ValueError(on)

    def cast(self, origin, d):
        hit, n, _, _ = self.tree.ray_cast(origin + self.off, d, 20.0)
        return (hit, n.normalized()) if hit is not None else (None, None)

    def part_of(self, p_ship):
        q = p_ship - self.off
        side = "_L" if q.y > 0 else "_R"
        if math.hypot(abs(q.y) - self.pod[0], q.z - self.pod[1]) < 1.05 and -0.7 < q.x < 6.0:
            return "pod" + side
        if abs(q.y) > POD_Y - 0.1:
            return ("fin" if q.z > 2.05 else "wing") + side
        return "hull"

    def lay(self, p, n, reach=0.12):
        hit, hn = self.cast(p - self.off + n * reach, -n)
        if hit is None or (hit - p).length > reach * 1.5:
            return None, None
        return hit + hn * self.offset, hn

    # ------------------------------------------------------------------ decals
    def laid_grid(self, centre, n, x, y, w, h):
        nx, ny = max(1, int(math.ceil(w / self.grid_m))), max(1, int(math.ceil(h / self.grid_m)))
        pts = []
        for j in range(ny + 1):
            row = []
            for i in range(nx + 1):
                s, t = i / nx, j / ny
                q, qn = self.lay(centre + x * ((s - 0.5) * w) + y * ((t - 0.5) * h), n)
                if q is None or qn.dot(n) < math.cos(math.radians(30)):
                    return None
                row.append((q, qn, s, t))
            pts.append(row)
        # a step between neighbouring points (a plate edge) means the decal would fold over it
        for j in range(len(pts)):
            for i in range(len(pts[0])):
                for dj, di in ((0, 1), (1, 0)):
                    if j + dj < len(pts) and i + di < len(pts[0]):
                        a, b = pts[j][i][0], pts[j + dj][i + di][0]
                        if abs((b - a).dot(n)) > 0.012:
                            return None
        return pts

    def grid(self, pts, n, uv_rect, slot, lift):
        verts = [[(self.bm.verts.new(q + qn * lift), s, t) for q, qn, s, t in row] for row in pts]
        u0, v0, u1, v1 = uv_rect
        for j in range(len(verts) - 1):
            for i in range(len(verts[0]) - 1):
                quad = [verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]]
                f = self.bm.faces.new([q[0] for q in quad])
                f.material_index = slot
                f.smooth = True
                for loop, (_, s, t) in zip(f.loops, quad):
                    loop[self.uv].uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)
                if f.normal.dot(n) < 0:
                    f.normal_flip()

    def place_at(self, name, hit, n, rot=0.0, scale=1.0, rule="items", check_overlap=True, frame=None):
        """One decal at a surface point; returns its frame (centre, x, y, w, h, n) or None."""
        item = self.index["decals"][name]
        x, y = frame if frame else _frame(n, rot, (hit - self.off).y)
        w, h = (v * scale for v in item["size_m"])
        rad = 0.5 * math.hypot(w, h)
        if check_overlap:
            # oriented rectangles (separating axes), not circles: a long rivet row is not a disc
            for c, r, xb, yb, wb, hb in self.placed:
                d = c - hit
                if d.length > r + rad:
                    continue
                if all(abs(d.dot(u)) < (w / 2 * abs(x.dot(u)) + h / 2 * abs(y.dot(u)) +
                                        wb / 2 * abs(xb.dot(u)) + hb / 2 * abs(yb.dot(u))) * 0.95
                       for u in (x, y, xb, yb)):
                    self.skipped["overlap"] += 1
                    return None
        pts = self.laid_grid(hit, n, x, y, w, h)
        if pts is None:
            self.skipped["edge"] += 1
            return None
        if item["type"] == "structural":
            self.grid(pts, n, item["uv"], 0, 0.0)
            self.grid(pts, n, item["uv"], 1, 0.0006)
        else:
            self.grid(pts, n, item["uv"], 2, 0.0012)
        self.placed.append((hit, rad, x, y, w, h))
        fr = (hit, x, y, w, h, n)
        self.frames.append((name, fr))
        self.log.append((rule, name, self.part_of(hit)))
        return fr

    def decal(self, spec, side, rule="items"):
        origin, d = self.ray(spec, side)
        hit, n = self.cast(origin, d)
        if hit is None:
            self.skipped["miss"] += 1
            return None
        return self.place_at(spec["item"], hit, n, spec.get("rot", 0.0), spec.get("scale", 1.0), rule,
                             spec.get("check_overlap", True))

    # ------------------------------------------------------------------ ribbons
    def ribbon(self, spec, side, rule="trim"):
        strip = self.index["trim"][spec["strip"]]
        h = strip["height_m"] * spec.get("scale", 1.0)
        pts = []
        g = self.grid_m
        on = spec["on"]
        if on == "pod_ring":
            a0, a1 = spec["deg"]
            n_seg = max(8, int(abs(a1 - a0) / 3))
            for k in range(n_seg + 1):
                pts.append(self.ray({"on": "pod", "x": spec["x"], "deg": a0 + (a1 - a0) * k / n_seg}, side))
        elif on == "pod_line":
            x0, x1 = spec["x"]
            n_seg = max(4, int((x1 - x0) / g))
            for k in range(n_seg + 1):
                pts.append(self.ray({"on": "pod", "x": x0 + (x1 - x0) * k / n_seg, "deg": spec["deg"]}, side))
        elif on == "hull_ring":
            a0, a1 = spec["deg"]
            n_seg = max(8, int(abs(a1 - a0) / 1.5))
            for k in range(n_seg + 1):
                pts.append(self.ray({"on": "hull_ring", "x": spec["x"], "deg": a0 + (a1 - a0) * k / n_seg,
                                     "zc": spec.get("zc", 1.2)}, 1))
        elif on in ("side_line", "top_line", "bottom_line"):
            poly = [Vector(q) for q in spec["points"]] if "points" in spec else [Vector(spec["a"]), Vector(spec["b"])]
            kind = {"side_line": "side", "top_line": "top", "bottom_line": "bottom"}[on]
            for idx, (a, b) in enumerate(zip(poly, poly[1:])):
                n_seg = max(2, int((b - a).length / g))
                for k in range(n_seg + (1 if idx == len(poly) - 2 else 0)):
                    p = a + (b - a) * (k / n_seg)
                    pts.append(self.ray({"on": kind, "x": p.x, "y": p.y, "z": p.z}, side))
        elif on == "ray_line":
            poly = [Vector(p) for p in spec["points"]]
            d = Vector(spec["dir"]).normalized()
            for a, b in zip(poly, poly[1:]):
                n_seg = max(1, int((b - a).length / g))
                for k in range(n_seg):
                    pts.append((a + (b - a) * (k / n_seg) - d * 2.0, d))
            pts.append((poly[-1] - d * 2.0, d))
        else:
            raise ValueError(on)
        # break where the hull under the path is not continuous (a jump, a bend over 35 deg), or where a
        # hull ring reached a pod
        runs, run, spacing = [], [], None
        for o, d in pts:
            p, n = self.cast(o, d)
            if p is not None and on == "hull_ring" and abs((p - self.off).y) > POD_Y - 0.05:
                p = None
            if p is not None and run:
                step = (p - run[-1][0]).length
                spacing = spacing or step
                if step > max(spacing, 0.02) * 3 or n.dot(run[-1][1]) < math.cos(math.radians(35)) or \
                        abs((p - run[-1][0]).dot(run[-1][1])) > 0.01:
                    runs.append(run)
                    run = []
            if p is None:
                if run:
                    runs.append(run)
                run = []
                continue
            run.append((p, n))
        runs.append(run)
        for hits in (r for r in runs if len(r) >= 3):
            self._ribbon_run(hits, strip, h, rule, spec["strip"])

    def _ribbon_run(self, hits, strip, h, rule, name):
        dist = [0.0]
        for (a, _), (b, _) in zip(hits, hits[1:]):
            dist.append(dist[-1] + (b - a).length)
        v0, v1 = strip["v"]
        for slot, lift in ((3, 0.0), (4, 0.0006)):
            rows = []
            for k, (p, n) in enumerate(hits):
                t = (hits[min(k + 1, len(hits) - 1)][0] - hits[max(k - 1, 0)][0]).normalized()
                across = n.cross(t).normalized()
                row = []
                for s in (-0.5, 0.5):
                    q2, qn = self.lay(p + across * (s * h), n)
                    if q2 is None or qn.dot(n) < 0.8:
                        row = None     # an edge of the strip hangs off the surface (a bay rim): break here
                        break
                    row.append(self.bm.verts.new(q2 + qn * lift))
                rows.append((row, dist[k] / strip["tile_m"], n))
            for (ra, ua, na), (rb, ub, _) in zip(rows, rows[1:]):
                if ra is None or rb is None:
                    continue
                f = self.bm.faces.new([ra[0], rb[0], rb[1], ra[1]])
                f.material_index = slot
                f.smooth = True
                for loop, uv in zip(f.loops, ((ua, v0), (ub, v0), (ub, v1), (ua, v1))):
                    loop[self.uv].uv = uv
                if f.normal.dot(na) < 0:
                    f.normal_flip()
        self.ribbons.append((rule, name, self.part_of(hits[len(hits) // 2][0]), dist[-1]))


# ---------------------------------------------------------------------------------------------- rules

def _pod_sections(recipe):
    rev = recipe["parts"]["pod"]["revolve"]
    return {s["name"]: s for s in rev["sections"]}


def _deg_free(deg, blocked):
    d = deg % 360
    return not any(a <= d <= b or a <= d - 360 <= b for a, b in blocked)


def rule_hull_seams(pl, r, recipe):
    seams = recipe["parts"]["hull"]["seams"]
    x0, x1 = r["region_x"]
    for x in seams["x"]:
        if x0 < x < x1 - 0.1:
            pl.ribbon({"strip": r.get("strip", "seam_rivets"), "on": "hull_ring", "x": x, "deg": [-180, 180],
                       "zc": r.get("zc", 1.2)}, 1, "hull_seams")
    for line in r.get("lines", []):
        for side in (1, -1):
            pl.ribbon({"strip": r.get("strip", "seam_rivets"), "on": "side_line",
                       "a": [line["x"][0], 0, line["z"]], "b": [line["x"][1], 0, line["z"]]}, side, "hull_seams")


def _split(a, b, holes):
    """[a, b] minus the holes, as a list of intervals longer than 5 cm."""
    parts = [(a, b)]
    for h0, h1 in holes:
        nxt = []
        for p0, p1 in parts:
            if h1 <= p0 or h0 >= p1:
                nxt.append((p0, p1))
                continue
            if h0 > p0:
                nxt.append((p0, h0))
            if h1 < p1:
                nxt.append((h1, p1))
        parts = nxt
    return [(p0, p1) for p0, p1 in parts if p1 - p0 > 0.05]


def rule_pod_gaps(pl, r, recipe):
    blocked = [tuple(b) for b in r.get("blocked_deg", [])]
    avoid = r.get("avoid", [])      # boxes {x, deg} the strips keep out of (the open bay)
    strip = r.get("strip", "seam_rivets")
    for name, sec in _pod_sections(recipe).items():
        if sec["kind"] != "panels":
            continue
        xa, xb = sec["x"]
        span = 360.0 / sec["around"]
        for side in (1, -1):
            for k in range(1, sec["rows"]):
                xr = xa + (xb - xa) * k / sec["rows"]
                for a0, a1 in r.get("ring_ranges", [[-60, 50], [100, 300]]):
                    for b0, b1 in _split(a0, a1, [av["deg"] for av in avoid if av["x"][0] <= xr <= av["x"][1]]):
                        pl.ribbon({"strip": strip, "on": "pod_ring", "x": xr, "deg": [b0, b1]}, side, "pod_gaps")
            for k in range(sec["around"]):
                deg = sec.get("phase_deg", 0.0) + k * span
                if _deg_free(deg, blocked):
                    cuts = [av["x"] for av in avoid if av["deg"][0] <= deg % 360 <= av["deg"][1] or av["deg"][0] <= deg % 360 - 360 <= av["deg"][1]]
                    for x0, x1 in _split(xa + 0.05, xb - 0.05, cuts):
                        pl.ribbon({"strip": strip, "on": "pod_line", "x": [x0, x1], "deg": deg}, side, "pod_gaps")


def rule_plate_edges(pl, r, recipe):
    det = recipe.get("detail", {})
    strip = r.get("strip", "rivet_line")
    ins = r.get("inset_m", 0.03)
    for p in det.get("pod", {}).get("plates", []):
        x0, x1 = p["x"]
        d0, d1 = p["deg"]
        dd = math.degrees(ins / 0.95)
        for side in (1, -1):
            for deg in (d0 + dd, d1 - dd):
                pl.ribbon({"strip": strip, "on": "pod_line", "x": [x0 + ins, x1 - ins], "deg": deg}, side, "plate_edges")
            for xx in (x0 + ins, x1 - ins):
                pl.ribbon({"strip": strip, "on": "pod_ring", "x": xx, "deg": [d0 + dd, d1 - dd]}, side, "plate_edges")
    for reg in det.get("hull_plates", []):
        x0, x1 = reg["x"][0] + ins, reg["x"][1] - ins
        sides = (1,) if reg.get("centre") else (1, -1)
        if "z" in reg:
            z0, z1 = reg["z"][0] + ins, min(reg["z"][1], 3.2) - ins
            for side in sides:
                for zz in (z0, z1):
                    pl.ribbon({"strip": strip, "on": "side_line", "a": [x0, 0, zz], "b": [x1, 0, zz]}, side, "plate_edges")
                for xx in (x0, x1):
                    pl.ribbon({"strip": strip, "on": "side_line", "a": [xx, 0, z0], "b": [xx, 0, z1]}, side, "plate_edges")
        elif "abs_y" in reg:
            kind = "top_line" if reg.get("normal_z", [0.5, 1])[0] > 0 else "bottom_line"
            y1 = reg["abs_y"][1] - ins
            for yy in (-y1, y1):
                pl.ribbon({"strip": strip, "on": kind, "a": [x0, yy, 0], "b": [x1, yy, 0]}, 1, "plate_edges")
            for xx in (x0, x1):
                pl.ribbon({"strip": strip, "on": kind, "a": [xx, -y1, 0], "b": [xx, y1, 0]}, 1, "plate_edges")


def rule_panel_marks(pl, r, recipe):
    """A panel number on every pod panel (picked by a stable hash of the panel, so it regenerates the same)
    and the listed hull marks (numbers or named stencils)."""
    numbers = sorted(n for n, it in pl.index["decals"].items() if "panelno" in it.get("tags", []))
    blocked = [tuple(b) for b in r.get("blocked_deg", [])]
    for name, sec in _pod_sections(recipe).items():
        if sec["kind"] != "panels":
            continue
        xa, xb = sec["x"]
        span = 360.0 / sec["around"]
        for row in range(sec["rows"]):
            for k in range(sec["around"]):
                deg = sec.get("phase_deg", 0.0) + (k + 0.3) * span
                if not _deg_free(deg, blocked):
                    continue
                xx = xa + (xb - xa) * (row + 0.25) / sec["rows"]
                for side in (1, -1):
                    item = numbers[_stable(name, row, k, side) % len(numbers)]
                    pl.decal({"item": item, "on": "pod", "x": xx, "deg": deg}, side, "panel_marks")
    for m in r.get("hull", []):
        for side in ((1,) if m.get("mirror") is False else (1, -1)):
            item = m.get("item") or numbers[_stable("hull", m.get("x"), m.get("z"), m.get("y"), side) % len(numbers)]
            pl.decal(dict(m, item=item), side, "panel_marks")


def rule_clusters(pl, clusters, rng, avoid=()):
    """Dense scatter of small items round service points (engines, the bay, the intake, the ramp); none
    inside the "avoid" boxes (x, deg) on the pods (the open bay)."""
    for c in clusters:
        pool = c["items"]
        for side in ((1, -1) if c.get("mirror", True) else (1,)):
            placed, tries = 0, 0
            while placed < c["count"] and tries < c["count"] * 15:
                tries += 1
                item = pool[rng.randrange(len(pool))]
                rot = rng.choice(c.get("rots", [0, 0, 0, 90]))
                if c["on"] == "pod":
                    spec = {"item": item, "on": "pod", "x": c["x"] + rng.uniform(-c["dx"], c["dx"]),
                            "deg": c["deg"] + rng.uniform(-c["ddeg"], c["ddeg"]), "rot": rot}
                    if any(av["x"][0] <= spec["x"] <= av["x"][1] and av["deg"][0] <= spec["deg"] <= av["deg"][1] for av in avoid):
                        continue
                else:
                    jit = [rng.uniform(-c.get("dx", 0), c.get("dx", 0)), rng.uniform(-c.get("dy", 0), c.get("dy", 0)),
                           rng.uniform(-c.get("dz", 0), c.get("dz", 0))]
                    spec = {"item": item, "on": c["on"], "x": c.get("x", 0) + jit[0], "y": c.get("y", 0.0) + jit[1],
                            "z": c.get("z", 0.0) + jit[2], "rot": rot,
                            "at": [c.get("x", 0) + jit[0], c.get("y", 0.0) + jit[1], c.get("z", 0.0) + jit[2]],
                            "dir": c.get("dir", [1, 0, 0])}
                if pl.decal(spec, side, "clusters"):
                    placed += 1


def rule_panel_lines(pl, r, recipe, rng):
    """Thin engraved panel lines (SC: the main source of density, a line every 0.3-0.8 m, with 45-degree
    jogs). Hull sides and roof: per bay between the hull seam stations, "per_bay" polylines; pods: short
    lines inside the panels. All from the seed."""
    strips = r.get("strips", ["panel_line", "panel_line", "panel_line_step"])
    seams = sorted(recipe["parts"]["hull"]["seams"]["x"])
    x0, x1 = r["region_x"]
    stations = [x0] + [x for x in seams if x0 < x < x1] + [x1]
    for xa, xb in zip(stations, stations[1:]):
        if xb - xa < 0.5:
            continue
        for band in r.get("side_bands", []):
            for k in range(band.get("per_bay", 2)):
                z0 = rng.uniform(*band["z"])
                z1 = min(max(z0 + rng.choice([-1, 1]) * rng.uniform(0.08, 0.25), band["z"][0]), band["z"][1])
                xm = rng.uniform(xa + 0.2, max(xa + 0.25, xb - 0.2 - abs(z1 - z0)))
                jog = abs(z1 - z0)
                pts = [[xa + 0.04, 0, z0], [xm, 0, z0], [xm + jog, 0, z1], [xb - 0.04, 0, z1]]
                if rng.random() < 0.4:
                    pts = pts[:2] + [[xm, 0, z0 + rng.choice([-1, 1]) * rng.uniform(0.15, 0.35)]]
                for side in (1, -1):
                    pl.ribbon({"strip": rng.choice(strips), "on": "side_line", "points": pts}, side, "panel_lines")
        for band in r.get("top_bands", []):
            for k in range(band.get("per_bay", 1)):
                y0 = rng.uniform(*band["y"])
                xm = rng.uniform(xa + 0.2, max(xa + 0.25, xb - 0.35))
                dy = 0.12 * rng.choice([-1, 1])
                pts = [[xa + 0.04, y0, 0], [xm, y0, 0], [xm + 0.12, y0 + dy, 0], [xb - 0.04, y0 + dy, 0]]
                kind = band.get("on", "top_line")
                for yy in ((1, -1) if band.get("mirror", True) else (1,)):
                    pl.ribbon({"strip": rng.choice(strips), "on": kind, "points": [[q[0], q[1] * yy, 0] for q in pts]}, 1, "panel_lines")
    pod = r.get("pod")
    if pod:
        avoid = pod.get("avoid", [])
        blocked = [tuple(b) for b in pod.get("blocked_deg", [])]
        for name, sec in _pod_sections(recipe).items():
            if sec["kind"] != "panels":
                continue
            xa, xb = sec["x"]
            span = 360.0 / sec["around"]
            for row in range(sec["rows"]):
                ra, rb = xa + (xb - xa) * row / sec["rows"], xa + (xb - xa) * (row + 1) / sec["rows"]
                for k in range(sec["around"]):
                    if rng.random() > pod.get("chance", 0.6):
                        continue
                    deg = sec.get("phase_deg", 0.0) + (k + rng.uniform(0.3, 0.7)) * span
                    if not _deg_free(deg, blocked):
                        continue
                    xs = sorted([rng.uniform(ra + 0.05, rb - 0.05) for _ in range(2)])
                    mid = (xs[0] + xs[1]) / 2
                    if xs[1] - xs[0] < 0.2 or any(av["x"][0] - 0.05 <= mid <= av["x"][1] + 0.05 and av["deg"][0] <= deg <= av["deg"][1] for av in avoid):
                        continue
                    for side in (1, -1):
                        pl.ribbon({"strip": "panel_line", "on": "pod_line", "x": xs, "deg": deg}, side, "panel_lines")


def rule_coverage(pl, r, rng):
    """At least one small decal per ~0.5 m panel on the calm surfaces: a jittered grid over each listed
    area, an item from the pool at each point (skipped where something already sits)."""
    for a in r["areas"]:
        pool = a["items"]
        step = a.get("step", 0.55)
        dv = a.get("dv", step)
        for side in ((1, -1) if a.get("mirror", True) else (1,)):
            u = a["u"][0]
            while u <= a["u"][1]:
                v = a["v"][0]
                while v <= a["v"][1]:
                    if rng.random() < a.get("chance", 0.7):
                        uu, vv = u + rng.uniform(-0.15, 0.15) * step, v + rng.uniform(-0.15, 0.15) * dv
                        item = pool[rng.randrange(len(pool))]
                        if a["on"] == "pod":
                            spec = {"item": item, "on": "pod", "x": uu, "deg": vv}
                            if any(av["x"][0] <= uu <= av["x"][1] and av["deg"][0] <= vv <= av["deg"][1] for av in a.get("avoid", [])):
                                spec = None
                        elif a["on"] == "side":
                            spec = {"item": item, "on": "side", "x": uu, "z": vv}
                        else:
                            spec = {"item": item, "on": a["on"], "x": uu, "y": vv}
                        if spec:
                            pl.decal(spec, side, "coverage")
                    v += dv
                u += step


def rule_greeble_companions(pl, r, recipe, rng):
    """The kit greebles of the hull (hatches, vents, sensors, hs_build_ship place_greebles) get the same
    companions as decal hatches: a service label beside a hatch, a red marker, chevrons by a sensor,
    a small stencil by a vent."""
    labels = sorted(n for n, it in pl.index["decals"].items() if "label" in it.get("tags", []))
    small = sorted(n for n, it in pl.index["decals"].items() if "small_stencil" in it.get("tags", []))
    for g in recipe["parts"]["hull"].get("greebles", []):
        kind = g["part"]
        size = {"hatch_large": (1.1, 0.7), "hatch": (0.62, 0.42), "vent": (0.42, 0.24), "sensor": (0.16, 0.1),
                "strip": (0.55, 0.07)}.get(kind, (0.3, 0.2))
        sides = (1, -1) if g["from"] == "side" and g.get("mirror", True) else (1,)
        for side in sides:
            if g["from"] == "side":
                spec = {"on": "side", "x": g["x"], "z": g["z"] + size[1] / 2 + 0.07}
                spec2 = {"on": "side", "x": g["x"] - size[0] / 2 - 0.08, "z": g["z"]}
            else:
                off = size[1] / 2 + 0.07
                spec = {"on": g["from"], "x": g["x"], "y": g.get("y", 0.0) + off}
                spec2 = {"on": g["from"], "x": g["x"] - size[0] / 2 - 0.08, "y": g.get("y", 0.0)}
            key = (kind, g["x"], side)
            if kind in ("hatch", "hatch_large"):
                pl.decal(dict(spec, item=labels[_stable(*key) % len(labels)]), side, "greeble_companions")
                pl.decal(dict(spec2, item="red_marker"), side, "greeble_companions")
            elif kind == "sensor":
                pl.decal(dict(spec, item="chevrons_port"), side, "greeble_companions")
            elif kind == "vent":
                pl.decal(dict(spec, item=small[_stable(*key) % len(small)]), side, "greeble_companions")


def rule_companions(pl, r, rng):
    """Next to every hatch: a service label above and a handle beside. Below grilles on side surfaces: a
    dirt streak, only now and then ("streak_chance": the clean look)."""
    labels = sorted(n for n, it in pl.index["decals"].items() if "label" in it.get("tags", []))
    for name, fr in list(pl.frames):
        tags = pl.index["decals"][name].get("tags", [])
        hit, x, y, w, h, n = fr
        if "hatch" in tags:
            lab = labels[_stable(name, round(hit.x, 2), round(hit.y, 2), round(hit.z, 2)) % len(labels)]
            lh = pl.index["decals"][lab]["size_m"][1]
            q, qn = pl.lay(hit + y * (h / 2 + lh / 2 + 0.03), n)
            if q is not None:
                pl.place_at(lab, q, qn, rule="companions", frame=(x, y), check_overlap=False)
            q, qn = pl.lay(hit - x * (w / 2 + 0.06), n)
            if q is not None:
                pl.place_at("handle", q, qn, rule="companions", frame=(-y, x), check_overlap=False)
        if set(tags) & {"socket", "cap"} and rng.random() < r.get("bracket_chance", 0.8):
            pl.place_at("chevrons_port", hit + n * 0.0004, n, rule="companions", frame=(x, y), check_overlap=False)
        if "hatch" in tags and rng.random() < r.get("marker_chance", 0.7):
            q, qn = pl.lay(hit + x * (w / 2 - 0.02) + y * (h / 2 + 0.02), n)
            if q is not None:
                pl.place_at("red_marker", q, qn, rule="companions", frame=(x, y), check_overlap=False)
        if "grille" in tags and abs(n.z) < 0.7 and rng.random() < r.get("streak_chance", 0.35):
            st = "streak_drip" if w > 0.25 else "streak_short"
            sh = pl.index["decals"][st]["size_m"][1]
            down = Vector((0, 0, -1))
            down = (down - n * n.dot(down)).normalized()
            q, qn = pl.lay(hit + down * (h / 2 + sh / 2 - 0.01), n)
            if q is not None:
                pl.place_at(st, q, qn, rule="companions", frame=(qn.cross(-down).normalized(), -down), check_overlap=False)


# ---------------------------------------------------------------------------------------------- build

def build(recipe, target, ship, off, root):
    """Returns the Decals object (ship coordinates) or None, and a report with the counts."""
    spec = recipe.get("decals")
    if not spec:
        return None, {}
    index = json.load(open(os.path.join(root, spec["index"]), encoding="utf-8"))
    rev = recipe["parts"]["pod"]["revolve"]["axis"]
    pl = Placer(target, spec, index, off, (rev["y"], rev["z"]))
    rng = random.Random(spec.get("seed", 7))
    rules = spec.get("rules", {})
    # hero items first (they win the overlap test), then the rules
    for it in spec.get("items", []):
        along = it.get("along")
        for k in range(along["count"] if along else 1):
            one = dict(it)
            if along and "at" in it:
                one["at"] = [it["at"][0] + along["step"] * k] + list(it["at"][1:])
            elif along:
                one["x"] = it["x"] + along["step"] * k
            for side in ((1, -1) if it.get("mirror", True) else (1,)):
                pl.decal(one, side, "items")
    if "panel_marks" in rules:
        rule_panel_marks(pl, rules["panel_marks"], recipe)
    if "clusters" in rules:
        rule_clusters(pl, rules["clusters"], rng, rules.get("pod_gaps", {}).get("avoid", []))
    if "greeble_companions" in rules:
        rule_greeble_companions(pl, rules["greeble_companions"], recipe, rng)
    if "companions" in rules:
        rule_companions(pl, rules["companions"], rng)
    if "coverage" in rules:
        rule_coverage(pl, rules["coverage"], rng)
    if "panel_lines" in rules:
        rule_panel_lines(pl, rules["panel_lines"], recipe, rng)
    if "hull_seams" in rules:
        rule_hull_seams(pl, rules["hull_seams"], recipe)
    if "pod_gaps" in rules:
        rule_pod_gaps(pl, rules["pod_gaps"], recipe)
    if "plate_edges" in rules:
        rule_plate_edges(pl, rules["plate_edges"], recipe)
    for tr in spec.get("trim", []):
        for side in ((1, -1) if tr.get("mirror", True) and tr["on"].startswith("pod") else (1,)):
            pl.ribbon(tr, side, "trim")
    name = "SM_Ship_%s_Decals" % ship
    me = bpy.data.meshes.new(name)
    pl.bm.to_mesh(me)
    pl.bm.free()
    for slot in SLOTS:
        m = bpy.data.materials.get("M_Ship_%s_%s" % (ship, slot)) or bpy.data.materials.new("M_Ship_%s_%s" % (ship, slot))
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    by_part, by_rule, by_type = {}, {}, {}
    for rule, item, part in pl.log:
        by_part[part] = by_part.get(part, 0) + 1
        by_rule[rule] = by_rule.get(rule, 0) + 1
        t = index["decals"][item]["type"]
        by_type[t] = by_type.get(t, 0) + 1
    strips = {}
    for rule, strip, part, length in pl.ribbons:
        s = strips.setdefault(part, [0, 0.0])
        s[0] += 1
        s[1] += length
    report = {"decals": len(pl.log), "by_part": by_part, "by_rule": by_rule, "by_type": by_type,
              "strip_runs": {k: {"runs": v[0], "metres": round(v[1], 1)} for k, v in strips.items()},
              "skipped": pl.skipped, "faces": len(me.polygons)}
    return ob, report
