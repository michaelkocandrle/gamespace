"""Cockpit v2 CK-CF: the canopy's inner frame (Design/Wayfarer_cockpit_v2.json, comparison with SC 5. 10. 2026:
"the pilot does not sit in a cage - only a thin line of the glass edge hangs in the sky").

A profile swept inside along every edge of the canopy glass (the glass object's boundary): a graphite frame body
over the glass edge and the hull behind it, a cream lining lip on its cockpit face (Halcyon), a rubber seal strip
where it meets the glass and screws every `bolt_pitch` on the cockpit face. It only frames the glass that is there:
no strut is added across the view (eye-view rule, ship-pipeline: no pillar within 15 degrees of the line of sight).
Built into the interior's per-material bmeshes (hs_interior.B), so it lands in the Interior part.

Recipe (interior.cockpit.canopy_frame): cover_m (over the glass), back_m (over the hull), depth_m, chamfer_m,
lip_m, seal_m, bolt_pitch_m, bolt_r_m, max_dist_m (from the eye: only the cockpit's glass).
"""

import bpy
import bmesh
from mathutils import Vector


def _prism(bm, a, b, section_a, section_b):
    """A closed prism between two cross-sections (lists of points, same length, ordered round)."""
    va = [bm.verts.new(p) for p in section_a]
    vb = [bm.verts.new(p) for p in section_b]
    n = len(va)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((va[i], va[j], vb[j], vb[i])))
    faces.append(bm.faces.new(va[::-1]))
    faces.append(bm.faces.new(vb))
    # outward whatever the edge's direction (a reversed edge mirrored the section and turned the prism inside out:
    # one-sided in the game, those struts were missing from the cockpit)
    bmesh.ops.recalc_face_normals(bm, faces=faces)


def _cyl(bm, a, b, r, seg=10):
    import math
    d = (b - a)
    if d.length < 1e-6:
        return
    z = d.normalized()
    x = z.orthogonal().normalized()
    y = z.cross(x)
    ring_a = [a + (x * math.cos(2 * math.pi * k / seg) + y * math.sin(2 * math.pi * k / seg)) * r for k in range(seg)]
    ring_b = [p + d for p in ring_a]
    _prism(bm, a, b, ring_a, ring_b)


def build(g, ship, eye, spec):
    """Adds the frame to g (hs_interior.B: bmeshes per material key). Returns a small report."""
    glass = bpy.data.objects.get("SM_Ship_%s_Canopy" % ship)
    if glass is None or not spec:
        return {"skipped": "no canopy glass" if glass is None else "no spec"}
    eye = Vector(eye)
    cover = spec.get("cover_m", 0.035)
    back = spec.get("back_m", 0.05)
    depth = spec.get("depth_m", 0.08)
    chamfer = spec.get("chamfer_m", 0.008)
    lip = spec.get("lip_m", 0.02)
    seal = spec.get("seal_m", 0.012)
    pitch = spec.get("bolt_pitch_m", 0.15)
    bolt_r = spec.get("bolt_r_m", 0.006)
    max_dist = spec.get("max_dist_m", 3.5)
    extend = spec.get("extend_m", 0.02)       # each segment runs a little past its ends: closed corners
    bm = bmesh.new()
    bm.from_mesh(glass.data)
    bm.transform(glass.matrix_world)
    bm.faces.ensure_lookup_table()
    edges = 0
    bolts = 0
    carry = 0.0
    for e in bm.edges:
        if not e.is_boundary or not e.link_faces:
            continue
        a, b = e.verts[0].co.copy(), e.verts[1].co.copy()
        mid = (a + b) / 2
        if (mid - eye).length > max_dist or mid.z < spec.get("min_z", -1e9) or mid.x < spec.get("min_x", -1e9):
            # (min_x: the rear side windows behind the pilot - out of view, the hull twists at the struts there)
            # (min_z: the glass's lower edges run into the dash and the cowl - the dash frames them)
            continue
        f = e.link_faces[0]
        n = f.normal.copy()
        if n.dot(mid - eye) < 0:          # the glass normal out of the ship (away from the eye)
            n = -n
        t = (b - a).normalized()
        w = n.cross(t)                    # in the glass plane, perpendicular to the edge
        if w.dot(f.calc_center_median() - mid) < 0:
            w = -w                        # w points into the glass
        a2, b2 = a - t * extend, b + t * extend
        inn = -n                          # into the cockpit

        def section(p):
            # round the profile: glass side (over the glass), cockpit face, hull side; chamfer on the cockpit edge
            return [p + w * cover + inn * 0.004,
                    p + w * cover + inn * (depth - chamfer),
                    p + w * (cover - chamfer) + inn * depth,
                    p - w * back + inn * depth,
                    # (behind the glass edge the hull curves in: this corner deeper, or it came out through the skin)
                    p - w * back + inn * spec.get("back_inset_m", 0.04)]
        _prism(g["int_console"], a2, b2, section(a2), section(b2))
        # the cream lining lip on the cockpit face, set in a little from the glass side
        def lip_section(p):
            c = p + w * (cover - chamfer - 0.004) + inn * (depth + 0.001)
            return [c, c - w * lip, c - w * lip + inn * 0.006, c + inn * 0.006]
        _prism(g["int_cream"], a2, b2, lip_section(a2), lip_section(b2))
        # the seal where the frame meets the glass
        def seal_section(p):
            c = p + w * cover + inn * 0.004
            return [c, c + w * seal, c + w * seal + inn * 0.01, c + inn * 0.01]
        _prism(g["int_rubber"], a, b, seal_section(a), seal_section(b))
        # (author 8. 10.: light from lines, not flat brightness) a cool light line on the cockpit face, between the
        # screws and the hull side, 1 mm proud
        if spec.get("glow_line", True):
            def glow_section(p):
                c = p + w * (cover - chamfer - lip - 0.022) + inn * (depth + 0.001)
                return [c, c - w * 0.006, c - w * 0.006 + inn * 0.0015, c + inn * 0.0015]
            _prism(g["int_glow_soft"], a2, b2, glow_section(a2), glow_section(b2))
        # screws along the cockpit face, carried on along the edges so the pitch stays even round the corners
        length = (b - a).length
        s = pitch - carry
        while s < length:
            p = a + t * s + w * (cover - chamfer - lip - 0.012) + inn * depth
            _cyl(g["int_trim"], p, p + inn * 0.004, bolt_r, 8)
            bolts += 1
            s += pitch
        carry = (length - (s - pitch)) if length > 0 else carry
        edges += 1
    # the glass's creases (where the top pane meets the side pane - the thin line in the sky from the seat): a strut
    # centred on the crease, both sides covered, kept out of the cone round the forward line of sight
    import math
    crease_deg = spec.get("crease_deg", 12.0)
    clear_deg = spec.get("clear_view_deg", 15.0)
    half = spec.get("crease_half_w_m", 0.045)
    cdepth = spec.get("crease_depth_m", 0.07)
    creases = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f0, f1 = e.link_faces
        if f0.normal.angle(f1.normal) < math.radians(crease_deg):
            continue
        a, b = e.verts[0].co.copy(), e.verts[1].co.copy()
        mid = (a + b) / 2
        v = mid - eye
        if v.length > max_dist or mid.x < spec.get("min_x", -1e9) or mid.z < spec.get("min_z", -1e9):
            continue
        elev = math.degrees(math.atan2(v.z, max(1e-6, (v.x * v.x + v.y * v.y) ** 0.5)))
        if v.normalized().angle(Vector((1.0, 0.0, 0.0))) < math.radians(clear_deg) and elev < spec.get("clear_up_deg", 90.0):
            # nothing in front of the pilot's line of sight; a bow overhead may come down to clear_up_deg above
            # it (the horizon and the HUD stay free; a bow cut at 15 degrees left a gap mid-air)
            continue
        if abs(mid.y) > spec.get("crease_max_abs_y", 1e9):
            continue                    # the crease's ends run into the side wall (the edge frame covers them)
        n = (f0.normal + f1.normal).normalized()
        if n.dot(v) < 0:
            n = -n
        t = (b - a).normalized()
        w = n.cross(t).normalized()
        inn = -n
        a2, b2 = a - t * extend, b + t * extend

        def csec(p):
            return [p + w * half + inn * 0.004,
                    p + w * half + inn * (cdepth - chamfer),
                    p + w * (half - chamfer) + inn * cdepth,
                    p - w * (half - chamfer) + inn * cdepth,
                    p - w * half + inn * (cdepth - chamfer),
                    p - w * half + inn * 0.004]
        _prism(g["int_console"], a2, b2, csec(a2), csec(b2))

        def clip(p):
            c = p + w * (lip / 2) + inn * (cdepth + 0.001)
            return [c, c - w * lip, c - w * lip + inn * 0.006, c + inn * 0.006]
        _prism(g["int_cream"], a2, b2, clip(a2), clip(b2))
        if spec.get("glow_line", True):
            for side in (-1, 1):                # a light line either side of the bow's lip
                def gclip(p, side=side):
                    c = p + w * (side * (lip / 2 + 0.004)) + inn * (cdepth + 0.001)
                    return [c, c + w * (side * 0.004), c + w * (side * 0.004) + inn * 0.0015, c + inn * 0.0015]
                _prism(g["int_glow_soft"], a2, b2, gclip(a2), gclip(b2))
        length = (b - a).length
        k = int(length / pitch)
        for j in range(k):
            for side in (-1, 1):
                p = a + t * ((j + 0.5) * pitch) + w * (side * (half - chamfer - 0.012)) + inn * cdepth
                _cyl(g["int_trim"], p, p + inn * 0.004, bolt_r, 8)
                bolts += 1
        creases += 1
    bm.free()
    return {"edges": edges, "creases": creases, "bolts": bolts}
