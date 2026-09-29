"""Batch 4 of the interior kit, second part: bulkheads with a door (kit_parts.json Bulkhead_Door, 29. 9. 2026).

The author walked the Wayfarer (29. 9. 2026: "fix the material, walls, floor, ceiling"): from eye height the
technical corridor's ends were the procedural bulkhead's flat faces. A bulkhead with a door is an end wall of the
section (kit_batch2.end_wall: plinth, kick panels, the rail at the break, pressed panels, frames to the ceiling)
with a doorway through it:
  size 03  a 0.3 m thick bulkhead: the doorway is a reveal through it - jambs with the sliding door's pocket slot,
           a guide track in the head, a threshold plate with the door's groove - and a back plate at its far face
           (what the next room's doorway frames). In the run it takes the place of a portal (0.3 m).
  size 00  the face only, 3 cm deep: where a kit room meets a room the ship still builds itself (its bulkhead is
           4 cm thick), so nothing may reach further back.
  A        the door on the section's centre line
  B        the door 0.5 m to the left (+Y) of it: the Wayfarer's door from the hold sits beside the cargo grid;
           its top right corner follows the wall's slope, framed like the rest
  C        the door 0.5 m to the right (-Y): the same door seen from the other room
Sections W and L41 (the hull liner's hold, 29. 9. 2026: the rail at 1.3 m as its liner walls, the main and upper
panels either side of it).
The door's clear opening is 1.0 x 2.05 m (hs_interior bulkhead: the doorways the ship builds behind it). Round it:
two collars in layers, a warm strip in a housing over the head washing the frame and the threshold, a status light
beside it (a light, no keypad - author), a frame to the ceiling on each side, a cable drop from the ceiling into
a junction box beside the door.
Frame: kit_rules wall pivot - origin at the bottom corner on the face plane, face +X, width along +Y (0..W); the
reveal and the back plate reach to x = -depth. In a ship's run_parts the pivot is at that corner (kit_layout).

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- batch4b
"""
import math

from mathutils import Vector

import kit_geo
from kit_batch2 import (BEV_MID, BEV_SMALL, FACE, G, GAP, PT, Section, _end_base, label, pressed, seg_frame_wall,
                        strip_light_along)
from kit_geo import frame

DOOR_W, DOOR_H = 1.0, 2.05
OFFSET = {"A": 0.0, "B": 0.5, "C": -0.5}
FW = 0.07                    # the inner door frame's width
CW = 0.03                    # the outer collar's width
CHAMFER = 0.12               # the opening's top corners (the octagonal language of the portals)


def _clip(poly, axis, value, keep_greater):
    """Sutherland-Hodgman against one axis-aligned half-plane; poly [(y, z)]."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina = (a[axis] >= value) if keep_greater else (a[axis] <= value)
        inb = (b[axis] >= value) if keep_greater else (b[axis] <= value)
        if ina:
            out.append(a)
        if ina != inb:
            t = (value - a[axis]) / (b[axis] - a[axis])
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    return out


def _clip_plane(poly, a, b, c):
    """Keeps the part of poly with a*y + b*z <= c."""
    out = []
    n = len(poly)
    for i in range(n):
        p0, p1 = poly[i], poly[(i + 1) % n]
        f0, f1 = a * p0[0] + b * p0[1] - c, a * p1[0] + b * p1[1] - c
        if f0 <= 0:
            out.append(p0)
        if (f0 <= 0) != (f1 <= 0):
            t = f0 / (f0 - f1)
            out.append((p0[0] + t * (p1[0] - p0[0]), p0[1] + t * (p1[1] - p0[1])))
    return out if len(out) >= 3 else []


def _in_section(poly, sec):
    """poly cut to the section's slopes (the convex part of the outline under the cove)."""
    W, vt = sec.width, sec.vt
    poly = _clip_plane(poly, 1.0, 0.75, W + 0.75 * vt)        # right slope: y <= W - (z - vt) * 0.75
    return _clip_plane(poly, -1.0, 0.75, 0.75 * vt) if poly else []   # left slope: y >= (z - vt) * 0.75


def _box_clip(poly, y0=None, y1=None, z0=None, z1=None):
    for axis, v, g in ((0, y0, True), (0, y1, False), (1, z0, True), (1, z1, False)):
        if v is not None and poly:
            poly = _clip(poly, axis, v, g)
    # drop repeated points (a clip along an existing edge)
    out = []
    for q in poly:
        if not out or (abs(q[0] - out[-1][0]) > 1e-5 or abs(q[1] - out[-1][1]) > 1e-5):
            out.append(q)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-5 and abs(out[0][1] - out[-1][1]) < 1e-5:
        out.pop()
    return out if len(out) >= 3 else []


def _area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def _ccw(poly):
    return poly if _area(poly) > 0 else list(reversed(poly))


def outline(sec):
    """The section's outline on the face plane (y 0..W, z up), counter-clockwise: the cove steps in by 0.14 at the top."""
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    return [(0, 0), (W, 0), (W, vt), (W - xt, top), (W - xt + 0.14, top), (W - xt + 0.14, C), (xt - 0.14, C), (xt - 0.14, top),
            (xt, top), (0, vt)]


def right_limit(sec, z, inset):
    """How far right (y) the outline reaches at height z, inset into the room."""
    W, vt = sec.width, sec.vt
    if z <= vt:
        return W - inset
    return W - (z - vt) * 0.75 - inset / 0.8


def left_limit(sec, z, inset):
    return sec.width - right_limit(sec, z, inset)


def opening(sec, var):
    """The door's clear opening (counter-clockwise, (y, z)): 1.0 x 2.05 m round its centre, top corners chamfered;
    where the section's slope comes closer than the frames, the corner follows the slope instead."""
    yc = sec.width / 2 + OFFSET[var]
    y0, y1 = yc - DOOR_W / 2, yc + DOOR_W / 2
    keep = FW + CW              # the collar meets the slope: a larger margin cost the walker's head its clearance
    pts = [(y0, 0.0), (y1, 0.0)]
    # the right edge: straight up until the slope's parallel keeps it `keep` inside the outline
    if right_limit(sec, DOOR_H, keep) >= y1 - 1e-6:
        pts += [(y1, DOOR_H - CHAMFER), (y1 - CHAMFER, DOOR_H)]
    else:
        zk = sec.vt + (sec.width - keep / 0.8 - y1) / 0.75
        pts += [(y1, zk), (right_limit(sec, DOOR_H, keep), DOOR_H)]
    if left_limit(sec, DOOR_H, keep) <= y0 + 1e-6:
        pts += [(y0 + CHAMFER, DOOR_H), (y0, DOOR_H - CHAMFER)]
    else:
        zl = sec.vt + (y0 - keep / 0.8) / 0.75
        pts += [(left_limit(sec, DOOR_H, keep), DOOR_H), (y0, zl)]
    return pts, (y0, y1)


def _offset(poly, d):
    """The polygon grown by d (counter-clockwise, convex enough: the door opening), by moving each edge out."""
    n = len(poly)
    lines = []
    for i in range(n):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % n])
        t = (b - a).normalized()
        nrm = Vector((t.y, -t.x))                 # outward for a counter-clockwise polygon
        lines.append((a + nrm * d, t))
    out = []
    for i in range(n):
        (p1, t1), (p2, t2) = lines[i - 1], lines[i]
        den = t1.x * t2.y - t1.y * t2.x
        if abs(den) < 1e-9:
            out.append(tuple(p2))
            continue
        s = ((p2.x - p1.x) * t2.y - (p2.y - p1.y) * t2.x) / den
        q = p1 + t1 * s
        out.append((q.x, q.y))
    return out


def _grow(poly, d):
    """The opening grown by d, standing on the floor (the bottom edge stays at z = 0)."""
    return [(y, max(0.0, z)) for (y, z) in _offset(poly, d)]


def _corners(poly, ya, yb, ztop):
    """The triangles between each slanted top edge of an opening-like polygon (a chamfer, a slope cut) and the corner
    of its bounding box (ya / yb, ztop) on that side: what the box has and the polygon has not."""
    out = []
    n = len(poly)
    mid = (ya + yb) / 2
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if abs(a[0] - b[0]) < 1e-5 or abs(a[1] - b[1]) < 1e-5 or max(a[1], b[1]) < 0.5:
            continue
        corner = (yb, ztop) if (a[0] + b[0]) / 2 > mid else (ya, ztop)
        tri = [a, b, corner]
        if abs(_area(tri)) > 1e-4:
            out.append(_ccw(tri))
    return out


def _members(p, pts, width, proud, depth, role, closed_bottom=False):
    """Frame members along the opening's edges (not along the floor), `width` wide outside the edge, `proud` in
    front of the face, `depth` deep."""
    centre = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if not closed_bottom and abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6:
            continue
        m, ln = seg_frame_wall(a, b, centre)
        # local y points into the opening: the member lies outside it (-y); ends overlap a little at the mitres
        p.slab(role, m, -0.012, ln + 0.012, -width, 0.0, depth, BEV_SMALL, segments=1, proud=proud, panel=False)


def bulkhead_door(sec, var, depth, name, seed):
    p = kit_geo.Part(name, seed)
    W, vt, top, xt, C = sec.width, sec.vt, sec.top, sec.xt, sec.ceiling
    hole, (y0, y1) = opening(sec, var)
    hole = _ccw(hole)
    frame_out = _grow(hole, FW)
    collar_out = _grow(hole, FW + CW)
    ol = outline(sec)
    back = max(depth, 0.03)
    rib = 0.03
    # ---------------------------------------------------------------- base: plinth, kick panels, the rail
    fl, fr = y0 - FW - CW, y1 + FW + CW
    spans = [s for s in ((0.0, fl), (fr, W)) if s[1] - s[0] > 0.04]
    # the rail's height: the section's break (W), or 1.3 m in a hull liner's room (the liner walls carry it there)
    rail = 1.3 if sec.key.startswith("L") else vt
    if depth > 0.05:
        _end_base(p, sec, spans, backing=False)
    else:
        _thin_base(p, sec, spans, rail)
    # ---------------------------------------------------------------- the dark backing / the back plate
    # everything of the outline but the opening, at x = -back: the thin one is a dark plate a panel's depth behind
    # the face (the procedural bulkhead is 4 cm), the thick one the far face the next room's doorway frames
    bm = frame((-back, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))
    for poly in [_box_clip(ol, y1=y0), _box_clip(ol, y0=y1), _box_clip(ol, y0=y0, y1=y1, z0=DOOR_H)] + _corners(hole, y0, y1, DOOR_H):
        if poly and abs(_area(poly)) > 1e-4:
            p.poly_prism("Kit_Seal", _ccw(poly), bm, 0.01, panel=False)
    # ---------------------------------------------------------------- panels on the face
    inner = FW + CW + GAP / 2
    # the lower zone beside the door (kick panels are in _end_base): main panels up to the rail
    for (u0, u1) in ((G, fl - GAP / 2), (fr + GAP / 2, W - G)):
        if u1 - u0 > 0.06:
            pressed(p, FACE, u0, u1, 0.5 + GAP / 2, rail - 0.055)
            if rail < vt - 0.2:
                # the liner's upper plate between the rail and the chamfer's foot
                pressed(p, FACE, u0, u1, rail + 0.055, vt - 0.03, proud=-0.008)
    # the upper zone: left and right of the door up to the outline, over the door to the ceiling (panels cut to the
    # outline and round the collar)
    for poly in (_box_clip(ol, y1=fl - GAP / 2, z0=vt + 0.03), _box_clip(ol, y0=fr + GAP / 2, z0=vt + 0.03)):
        if poly and abs(_area(poly)) > 0.01:
            p.poly_prism("Kit_Primary", _ccw(poly), FACE, PT, panel=True)
    head = max(q[1] for q in collar_out) + GAP / 2
    over_p = _box_clip(ol, y0=fl - GAP / 2, y1=fr + GAP / 2, z0=head)
    if over_p and abs(_area(over_p)) > 0.01:
        p.poly_prism("Kit_Primary", _ccw(over_p), FACE, PT, panel=True)
    # the triangles between the collar's chamfers and the zone lines (else the backing shows as black corners)
    ctop = max(q[1] for q in collar_out)
    for tri in _corners(collar_out, fl, fr, ctop):
        tri = _in_section(tri, sec)
        if tri and abs(_area(tri)) > 0.002:
            p.poly_prism("Kit_Primary", _ccw(tri), FACE, PT * 0.8, panel=True)
    if head - ctop > 0.004:
        p.slab("Kit_Primary", FACE, fl, fr, ctop, head - GAP / 2, PT * 0.8, panel=False)
    # ---------------------------------------------------------------- frames to the ceiling beside the door
    for y in (fl - rib, fr + rib):
        if rib + 0.02 < y < W - rib - 0.02:
            ztop = min(C, _top_at(sec, y)) - 0.01
            p.slab("Kit_Structure", FACE, y - rib, y + rib, 0.1, ztop, 0.07, proud=0.045, panel=False)
            for z in (0.35, 0.8, 1.6, 2.0):
                if z < ztop - 0.08:
                    p.tube("Kit_Structure", (0.045, y, z), (0.05, y, z), 0.0065, 6)
    # the head beam under the ceiling across the cove fascias
    p.slab("Kit_Structure", FACE, xt - 0.14, W - xt + 0.14, C - 0.07, C, 0.08, BEV_SMALL, segments=1, proud=0.035, panel=False)
    # ---------------------------------------------------------------- the door frame in two layers
    _members(p, hole, FW, 0.045, 0.06, "Kit_Structure")
    _members(p, frame_out, CW, 0.022, 0.035, "Kit_Primary")
    # hazard band on the frame's two legs (low) and a plate over the head
    label(p, "hazard_stripe", (0.045, y0 - FW / 2, 0.25), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.45)
    label(p, "hazard_stripe", (0.045, y1 + FW / 2, 0.25), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.45)
    # ---------------------------------------------------------------- the light over the door
    # (under a 2.3 m ceiling there is no room over the collar): a housing on the head member's front, its diffuser
    # facing down and out, washing the frame, the threshold and the floor in front of the door
    top = [q for q in hole if abs(q[1] - DOOR_H) < 1e-6]
    if len(top) >= 2:
        ha, hb = min(q[0] for q in top) + 0.04, max(q[0] for q in top) - 0.04
        if hb - ha > 0.2:
            hz = DOOR_H + 0.012
            p.box("Kit_Structure", (0.04, ha - 0.015, hz), (0.1, hb + 0.015, hz + 0.05), bevel=BEV_SMALL, segments=1, panel=False)
            p.box("Kit_GlowWarm", (0.055, ha, hz - 0.004), (0.09, hb, hz + 0.001), panel=False)
            strip_light_along(p, "Light_Door_0", (0.075, (ha + hb) / 2, hz - 0.012), (0.35, 0, -0.937), (0, 1, 0), hb - ha, 0.03,
                              "warm", 2.2, 1.8)
            if depth > 0.05:
                # and one in the reveal's head, in front of the leaf's slot: the doorway is not a black hole
                p.box("Kit_GlowWarm", (-depth / 2 + 0.035, ha + 0.05, DOOR_H - 0.006), (-0.035, hb - 0.05, DOOR_H + 0.001), panel=False)
                strip_light_along(p, "Light_Reveal_0", (-depth / 4 - 0.01, (ha + hb) / 2, DOOR_H - 0.01), (0, 0, -1), (0, 1, 0),
                                  hb - ha - 0.1, 0.05, "warm", 1.6, 1.4)
    # ---------------------------------------------------------------- the status light beside the door (a light, no keypad)
    sy = y0 - FW - CW - 0.09
    status = sy > 0.08
    if status:
        p.box("Kit_Structure", (0.0, sy - 0.03, 1.38), (0.03, sy + 0.03, 1.56), bevel=0.004, segments=1, panel=False)
        p.box("Kit_GlowSignal", (0.028, sy - 0.012, 1.49), (0.034, sy + 0.012, 1.53), panel=False)
        p.box("Kit_Plastic", (0.028, sy - 0.012, 1.41), (0.033, sy + 0.012, 1.47), panel=False)
    # ---------------------------------------------------------------- a cable drop into a junction box
    jy = fr + rib + 0.12 if fr + rib + 0.25 < W - 0.15 else fl - rib - 0.3
    if 0.12 < jy < W - 0.12 and _top_at(sec, jy) > 1.9:
        zt = min(C, _top_at(sec, jy)) - 0.03
        p.box("Kit_Structure", (0.0, jy - 0.09, 1.02), (0.07, jy + 0.09, 1.26), bevel=0.006, segments=2)
        p.box("Kit_Primary", (0.07, jy - 0.075, 1.035), (0.075, jy + 0.075, 1.245), bevel=0.002, segments=1)
        for zz in (1.05, 1.23):
            for yy in (jy - 0.06, jy + 0.06):
                p.tube("Kit_Structure", (0.075, yy, zz), (0.08, yy, zz), 0.005, 6)
        for k, dy in enumerate((-0.03, 0.02)):
            p.tube("Kit_Rubber", (0.035, jy + dy, 1.26), (0.035, jy + dy, zt), 0.011 if k == 0 else 0.009, 10, caps=False)
        for zc in [z for z in (1.5, 1.85, 2.15) if z < zt - 0.05]:
            p.slab("Kit_Structure", FACE, jy - 0.05, jy + 0.045, zc - 0.012, zc + 0.012, 0.05, BEV_SMALL, segments=1, proud=0.05, panel=False)
        label(p, "st_service", (0.075, jy, 1.14), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.5, True)
    # ---------------------------------------------------------------- the reveal through a thick bulkhead
    if depth > 0.05:
        _reveal(p, hole, depth)
    # ---------------------------------------------------------------- collision: the wall round the opening
    lo_x = -back
    p.collision_box((lo_x, 0, 0), (0.0, max(0.02, y0), C))
    p.collision_box((lo_x, y1, 0), (0.0, W, C))
    p.collision_box((lo_x, y0, DOOR_H), (0.0, y1, C))
    # the slope-cut corner of an offset door: a hull over the triangle between the opening and the side
    cut = sorted([q for q in hole if q[1] > 0.05 and y0 + 0.2 < q[0] <= y1 + 1e-6], key=lambda q: q[1])
    if len(cut) >= 2:
        # 3 cm behind the lining's slanted edge: the walker's head passes the corner without catching on it (a
        # capsule at the door's centre had 1 cm - the game's walker stopped short of the reveal)
        (ya, za), (yb, zb) = cut[0], cut[-1]
        t = ((yb - ya), (zb - za))
        ln = (t[0] ** 2 + t[1] ** 2) ** 0.5
        n = (t[1] / ln, -t[0] / ln)                 # away from the opening (right and up)
        if n[0] < 0:
            n = (-n[0], -n[1])
        k = 0.03
        za2 = za + k / max(n[1], 1e-3) if abs(ya - y1) < 1e-6 else za
        yb2 = yb + k / max(n[0], 1e-3) if abs(zb - DOOR_H) < 1e-6 else yb
        tri = [(y1, min(za2, DOOR_H - 0.01)), (min(yb2, y1 - 0.01), DOOR_H), (y1, DOOR_H)]
        pts = [(x, y, z) for x in (lo_x, 0.0) for (y, z) in tri]
        p.collision_hull(pts)
    p.socket("Snap_Start", (0, 0, 0), x=(0, -1, 0), z=(0, 0, 1))
    p.socket("Snap_End", (0, W, 0), x=(0, 1, 0), z=(0, 0, 1))
    return p


def _thin_base(p, sec, spans, rail):
    """_end_base for a face 3 cm deep: no recessed plinth (it reaches 10 cm behind the face - into the room the ship
    builds behind the bulkhead), a rubber skirting on the face instead; the kick panels and the rail as the walls."""
    vt = rail
    for (a, b) in spans:
        p.box("Kit_Rubber", (0.0, a, 0.0), (0.014, b, 0.1), bevel=0.003, panel=False)
        p.slab("Kit_Primary", FACE, a + G, b - G, 0.1 + GAP / 2, 0.5 - GAP / 2, PT, BEV_MID, secondary=True)
        p.slab("Kit_Trim", FACE, a + G, b - G, 0.1 + GAP / 2, 0.2 + GAP / 2, 0.006, BEV_SMALL, proud=0.003, trim="kickplate", panel=False)
        p.slab("Kit_Signal", FACE, a, b, vt - 0.049, vt - 0.043, 0.01, proud=-0.006, panel=False)
        p.slab("Kit_Trim", FACE, a, b, vt - 0.025, vt + 0.025, 0.045, BEV_SMALL, proud=0.014, trim="rail_bolted", panel=False)


def _top_at(sec, y):
    """The outline's height at y on the face (the ceiling, or the slope near the sides)."""
    W, vt = sec.width, sec.vt
    d = min(y, W - y)
    if d >= sec.xt - 0.14:
        return sec.ceiling
    if d >= sec.xt:
        return sec.top
    return vt + d / 0.75


def _leg_y(hole, side):
    ys = [q[0] for q in hole if 0.05 < q[1] < 1.0]
    return max(ys) if side == "right" else min(ys)


def _reveal(p, hole, depth):
    """The doorway through the bulkhead: lining along every edge of the opening from the face back to -depth, the
    door's pocket slot in the jambs and head (a sliding leaf retracted into the bulkhead), a guide track, the
    threshold plate with its groove."""
    n = len(hole)
    centre = (sum(q[0] for q in hole) / n, sum(q[1] for q in hole) / n)
    mid = -depth / 2
    for i in range(n):
        a, b = hole[i], hole[(i + 1) % n]
        if abs(a[1]) < 1e-6 and abs(b[1]) < 1e-6:
            continue
        ya, za = a
        yb, zb = b
        t = Vector((0.0, yb - ya, zb - za))
        ln = t.length
        t.normalize()
        # the lining's normal points into the opening
        nrm = Vector((0.0, -t.z, t.y))
        c = Vector((0.0, centre[0] - (ya + yb) / 2, centre[1] - (za + zb) / 2))
        if nrm.dot(c) < 0:
            nrm = -nrm
        # a frame on the edge: local x along it, local y back along -X, local z the normal into the opening
        m = frame((0.0, ya, za), t, Vector((-1.0, 0.0, 0.0)), nrm)
        if Vector((-1.0, 0.0, 0.0)).cross(nrm).dot(t) < 0:
            m = frame((0.0, yb, zb), -t, Vector((-1.0, 0.0, 0.0)), nrm)
        # two lining plates either side of the pocket slot
        p.slab("Kit_Primary", m, 0.0, ln, 0.0, depth / 2 - 0.02, 0.02, BEV_SMALL, segments=1, proud=0.0)
        p.slab("Kit_Primary", m, 0.0, ln, depth / 2 + 0.02, depth, 0.02, BEV_SMALL, segments=1, proud=0.0)
        # the slot: a dark recess between them
        p.slab("Kit_Seal", m, 0.0, ln, depth / 2 - 0.02, depth / 2 + 0.02, 0.01, proud=-0.02, panel=False)
        # guide track along the head's slot
        if za > 1.5 and zb > 1.5:
            p.slab("Kit_Structure", m, 0.01, ln - 0.01, depth / 2 - 0.028, depth / 2 - 0.02, 0.02, proud=0.006, panel=False)
            p.slab("Kit_Structure", m, 0.01, ln - 0.01, depth / 2 + 0.02, depth / 2 + 0.028, 0.02, proud=0.006, panel=False)
    # threshold: a brushed plate over the reveal's floor with the leaf's groove across it
    y0 = min(q[0] for q in hole)
    y1 = max(q[0] for q in hole if q[1] < 0.5)
    tm = frame((0, 0, 0), (0, 1, 0), (-1, 0, 0), (0, 0, 1))
    p.slab("Kit_Trim", tm, y0, y1, 0.0, depth / 2 - 0.015, 0.006, BEV_SMALL, segments=1, proud=0.004, trim="antislip_tread", panel=False)
    p.slab("Kit_Trim", tm, y0, y1, depth / 2 + 0.015, depth, 0.006, BEV_SMALL, segments=1, proud=0.004, trim="antislip_tread", panel=False)
    p.slab("Kit_Structure", tm, y0, y1, depth / 2 - 0.015, depth / 2 + 0.015, 0.012, proud=0.001, panel=False)
    # the floor under it (a run's stand-in floor may be missing there): a structure slab
    p.box("Kit_Structure", (-depth, y0 - 0.02, -0.04), (0.0, y1 + 0.02, -0.002), panel=False)


BATCH4B = [("Bulkhead", "Door", 0.3, "W", "B"), ("Bulkhead", "Door", 0.0, "W", "A"), ("Bulkhead", "Door", 0.3, "W", "A"),
           ("Bulkhead", "Door", 0.0, "L41", "C")]
VIEWS = {("Bulkhead", "Door"): ((1, 0.0, 0.12), (1, -0.8, 0.3))}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    name = part_name(cat, part, size, sec_key, var)
    return bulkhead_door(Section(sec_key), var, size, name, seed)


def budget(cat, part, size):
    b = kit_geo.RULES["tri_budget"]
    return int(b["Wall_base"] + b["Wall_per_m"] * 2.4)
