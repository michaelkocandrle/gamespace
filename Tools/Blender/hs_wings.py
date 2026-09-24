"""Shaped wings and fins (whole-ship rebuild part 2, skill ship-pipeline 3b3), called by hs_build_ship.py.

The base builds a wing or fin as the intersection of the drawing's outlines: an exact but flat slab. This
module rebuilds each slab (every connected piece of the part) as a shaped surface inside that slab:

  - thin axis from the slab itself (its smallest extent, PCA), chord along the ship's x, span across
  - span stations every "step" m; at each the exact chord interval of the slab (ray bisection to 1 mm), so
    the planform stays the drawing's outline (the top / side silhouette does not change)
  - an airfoil thickness across the chord (NACA 4-digit shape, "t_ratio" of the slab's thickness at 30 %
    chord = 1): the front silhouette keeps its maximum thickness
  - split into hard-surface pieces with real gaps: a leading-edge strip (chord 0 .. "le"), the box
    (le .. 1), a flap / rudder ("flap": span fractions and chord start) cut out of the box, each piece
    closed (boundary walls), bevelled with weighted normals; flap track fairings under a wing flap
  - piece materials by key (recipe "materials"), flaps secondary paint (face attribute paint2)

Recipe "wings": {"<part>": {"step", "t_ratio", "le", "flap": {"span": [a, b], "chord": c}, "gap",
"fairings", "materials": {"box", "le", "flap", "tip"}}}. Prints nothing; returns a report.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import hs_build_part as hp


def naca(f, t=1.0):
    """Half thickness of a NACA 00xx section at chord fraction f, normalised to 1 at its maximum (f 0.3)."""
    f = min(max(f, 0.0), 1.0)
    y = 0.2969 * math.sqrt(f) - 0.126 * f - 0.3516 * f * f + 0.2843 * f ** 3 - 0.1036 * f ** 4
    return max(y / 0.10003, 0.0) * t     # 0.10003 = the bracket at f 0.3 (a NACA section is thickest there)


def _components(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    seen, comps = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, comp = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            comp.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        verts = {v for g in comp for v in g.verts}
        sub = bmesh.new()
        vmap = {v: sub.verts.new(v.co) for v in verts}
        for g in comp:
            sub.faces.new([vmap[v] for v in g.verts])
        sub.normal_update()
        comps.append(sub)
    bm.free()
    return comps


def _axes(bm):
    """Thin axis (smallest extent), chord axis (ship x projected off it), span axis."""
    pts = [v.co for v in bm.verts]
    c = sum(pts, Vector()) / len(pts)
    best = None
    # candidates: face normals of the big faces (a slab's largest faces are its sides)
    for f in sorted(bm.faces, key=lambda f: -f.calc_area())[:6]:
        n = f.normal.normalized()
        ext = max(p.dot(n) for p in pts) - min(p.dot(n) for p in pts)
        if best is None or ext < best[0]:
            best = (ext, n)
    thin = best[1]
    if thin.z < -0.1 or (abs(thin.z) < 0.1 and thin.y < 0):
        thin = -thin
    chord = Vector((1, 0, 0)) - thin * thin.x
    chord.normalize()
    span = thin.cross(chord).normalized()
    # span away from the hull: up for a fin, outboard for a wing
    if abs(span.z) > 0.5:
        if span.z < 0:
            span = -span
    elif span.y * c.y < 0:
        span = -span
    return c, thin, chord, span


def _slab_at(tree, p, thin, reach=3.0):
    """Top and bottom of the slab along the thin axis through p (None if outside)."""
    a = tree.ray_cast(p + thin * reach, -thin, reach * 2)
    b = tree.ray_cast(p - thin * reach, thin, reach * 2)
    if a[0] is None or b[0] is None:
        return None
    return a[0].dot(thin), b[0].dot(thin)


def _chord_interval(tree, base, chord, thin, span_off, span, lo, hi):
    """Exact [start, end] of the slab along the chord at a span offset (bisection to 1 mm)."""
    xs = [lo + (hi - lo) * k / 200 for k in range(201)]
    inside = [(_slab_at(tree, base + span * span_off + chord * x, thin) is not None) for x in xs]
    if not any(inside):
        return None
    i0 = inside.index(True)
    i1 = len(inside) - 1 - inside[::-1].index(True)

    def bis(a, b, want_inside_at_b):
        for _ in range(14):
            m = (a + b) / 2
            ins = _slab_at(tree, base + span * span_off + chord * m, thin) is not None
            if ins == want_inside_at_b:
                b = m
            else:
                a = m
        return b

    x0 = bis(xs[i0 - 1], xs[i0], True) if i0 > 0 else xs[0]
    x1 = bis(xs[i1 + 1], xs[i1], True) if i1 < len(xs) - 1 else xs[-1]
    return x0, x1


def _piece(stations, f0, f1, n_chord, t_ratio, gap_f=0.0):
    """Closed piece over span stations (list of (span_pt, x0, x1, mid, t)) and chord fractions [f0, f1]."""
    bm = bmesh.new()
    rows = []
    for (sp, x0, x1, mid_fn, tmax, chord, thin) in stations:
        top, bot = [], []
        for k in range(n_chord + 1):
            u = k / n_chord
            f = f0 + (f1 - f0) * (0.5 - 0.5 * math.cos(math.pi * u)) if f0 == 0.0 else f0 + (f1 - f0) * u
            x = x0 + (x1 - x0) * f
            m = mid_fn(x)
            h = 0.5 * tmax * t_ratio * max(naca(f), 0.004)
            p = sp + chord * x
            top.append(bm.verts.new(p + thin * (m + h)))
            bot.append(bm.verts.new(p + thin * (m - h)))
        rows.append((top, bot))
    for (ta, ba), (tb, bb) in zip(rows, rows[1:]):
        for k in range(n_chord):
            bm.faces.new((ta[k], ta[k + 1], tb[k + 1], tb[k]))
            bm.faces.new((ba[k], bb[k], bb[k + 1], ba[k + 1]))
    # chord-end walls (leading / trailing / cut edges) and span-end walls (root / tip)
    for (ta, ba), (tb, bb) in zip(rows, rows[1:]):
        for k in (0, n_chord):
            bm.faces.new((ta[k], tb[k], bb[k], ba[k]))
    for (t, b) in (rows[0], rows[-1]):
        for k in range(n_chord):
            bm.faces.new((t[k], t[k + 1], b[k + 1], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def build(ob, spec, coll, mats, bevel, name):
    """Rebuilds the slab object ob; returns the new objects (the caller removes ob)."""
    step = spec.get("step", 0.08)
    t_ratio = spec.get("t_ratio", 1.0)
    le = spec.get("le", 0.08)
    gap = spec.get("gap", 0.008)
    made = []
    for ci, comp in enumerate(_components(ob)):
        c, thin, chord, span = _axes(comp)
        tree = BVHTree.FromBMesh(comp)
        pts = [v.co for v in comp.verts]
        s_vals = [(p - c).dot(span) for p in pts]
        x_vals = [(p - c).dot(chord) for p in pts]
        s0, s1 = min(s_vals), max(s_vals)
        lo, hi = min(x_vals) - 0.05, max(x_vals) + 0.05
        n_st = max(4, int(math.ceil((s1 - s0) / step)))
        stations = []
        for k in range(n_st + 1):
            so = s0 + 0.0005 + (s1 - s0 - 0.001) * k / n_st
            iv = _chord_interval(tree, c, chord, thin, so, span, lo, hi)
            if iv is None or iv[1] - iv[0] < 0.005:
                continue
            x0, x1 = iv
            base = c + span * so

            def mid_fn(x, base=base):
                r = _slab_at(tree, base + chord * x, thin)
                if r is None:
                    r = _slab_at(tree, base + chord * min(max(x, x0 + 0.01), x1 - 0.01), thin)
                return 0.5 * (r[0] + r[1]) - base.dot(thin) if r else 0.0

            r30 = _slab_at(tree, base + chord * (x0 + 0.3 * (x1 - x0)), thin)
            tmax = (r30[0] - r30[1]) if r30 else 0.05
            stations.append((base, x0, x1, mid_fn, tmax, chord, thin, so))
        if len(stations) < 2:
            continue
        span_len = stations[-1][7] - stations[0][7]
        fl = spec.get("flap")

        def st_range(a, b):
            lo_s, hi_s = stations[0][7] + span_len * a, stations[0][7] + span_len * b
            return [s[:7] for s in stations if lo_s <= s[7] <= hi_s]

        pieces = []
        # a dark core under the pieces, no gaps: the gaps show structure, not daylight (and the silhouette
        # stays closed)
        core_ratio = spec.get("core", 0.9)
        pieces.append(("core", _piece([s[:7] for s in stations], 0.0, 1.0, 24, t_ratio * core_ratio)))
        le_f1 = le
        box_f0 = le + gap / max(1e-3, (stations[0][2] - stations[0][1]))
        pieces.append(("le", _piece([s[:7] for s in stations], 0.0, le_f1, 10, t_ratio)))
        if fl:
            a, b = fl["span"]
            cut = fl["chord"]
            inner = st_range(0.0, a)
            mid = st_range(a, b)
            outer = st_range(b, 1.0)
            gs = gap / max(span_len, 1e-3)
            mid_flap = st_range(a + gs, b - gs)
            for part, sts in (("box", inner), ("box", outer)):
                if len(sts) >= 2:
                    pieces.append((part, _piece(sts, box_f0, 1.0, 24, t_ratio)))
            if len(mid) >= 2:
                pieces.append(("box", _piece(mid, box_f0, cut - 0.006, 20, t_ratio)))
            if len(mid_flap) >= 2:
                pieces.append(("flap", _piece(mid_flap, cut + 0.006, 1.0, 10, t_ratio)))
        else:
            pieces.append(("box", _piece([s[:7] for s in stations], box_f0, 1.0, 24, t_ratio)))
        # flap track fairings: small pods on the pressure side at the flap hinge
        if fl and spec.get("fairings"):
            fb = bmesh.new()
            for fr in spec["fairings"]:
                s = min(stations, key=lambda st: abs(st[7] - (stations[0][7] + span_len * fr)))
                base, x0, x1, mid_fn, tmax, ch, th, so = s
                xh = x0 + (x1 - x0) * fl["chord"]
                m = mid_fn(xh)
                p = base + ch * xh + th * (m - 0.5 * tmax * t_ratio * naca(fl["chord"]) - 0.035)
                hp_box = bmesh.ops.create_cube(fb, size=1.0)
                bmesh.ops.scale(fb, vec=(0.55, 0.06, 0.07), verts=hp_box["verts"])
                mm = Matrix((ch, th.cross(ch), th)).transposed().to_4x4()
                mm.translation = p + ch * 0.1
                bmesh.ops.transform(fb, matrix=mm, verts=hp_box["verts"])
            pieces.append(("fairing", fb))
        for key, bm in pieces:
            obn = hp.finish(bm, "%s_%d_%s" % (name, ci, key), coll, bevel)
            obn.modifiers["Bevel"].width = spec.get("bevel_m", 0.006)
            obn.data.materials.append(mats[spec.get("materials", {}).get(key, "paint")])
            a = obn.data.attributes.new("paint2", "INT", "FACE")
            a.data.foreach_set("value", [1 if key == "flap" else 0] * len(obn.data.polygons))
            made.append(obn)
        comp.free()
    return made
