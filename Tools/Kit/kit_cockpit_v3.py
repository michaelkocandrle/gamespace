"""Wayfarer cockpit v3 (author 8. 10. 2026, ArtSource/Ships/Wayfarer/Concept/Cockpit/cockpit_layout_v3_proposal.png):
the sticks on the seat's arms, the consoles thin along the walls and run into the dash wings (one shape, the glossy
column paint), aisles round the seat on both sides.

  SM_Kit_Cockpit_SeatArm07W_L / _R          the seat's forearm rest: a leather pad, 2 x 2 backlit keys, the stick; a
                                            bracket down to the seat's side
  SM_Kit_Cockpit_ConsoleWall18W_L / _R      v4 (concept consoles_v4_concept_b.png): one lofted shape out of the
                                            lining up into the dash wing, a sloped top with the SYS rockers and the
                                            EMERG field sunk in it, a recessed lit kick, light lines on its inner edge

Both are built in the ship layout's coordinates (x from the stern, y to port, z from the cockpit floor) and placed at
the layout's origin (interior.kit_modules.run_parts [[0, 0, 1.15], [1, 0], [part]]): the console follows the hull's
wall polygon exactly. _R is the mirror of _L (kit_cockpit_b._mirror_y: the text still reads right).
"""
import math

from mathutils import Vector

import kit_geo
from kit_geo import frame
import kit_cockpit_b as kb
from kit_cockpit_b import side_prism, screw, legend, led, keycap, rocker_b, emergency_key, MIRROR, _mirror_y
from kit_cockpit import stick, _label

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
WALL = [(15.2, 1.75), (16.5, 1.6), (18.6, 1.0)]     # the cockpit's port wall (Wayfarer_layout.json, rooms.cockpit.poly)
LINER = 0.1                                         # the lining's face inside the hull line
CX1 = 17.85                                         # the console's front, tucked into the dash wing
# cockpit v4 (author 8. 10. 2026: the side consoles read as boxes - concept consoles_v4_concept_b.png approved): one
# lofted shape growing out of the lining and sweeping up into the dash wing. Stations (x, depth from the lining's
# face, height of its inner top edge); the top falls 11 deg towards the aisle (SLOPE); the depth never exceeds v3's
# (the aisles stay as walked).
STATIONS = [(15.9, 0.06, 0.64), (16.0, 0.30, 0.66), (16.5, 0.257, 0.689), (16.7, 0.24, 0.70), (17.25, 0.14, 0.72),
            (17.62, 0.08, 0.835), (CX1, 0.06, 0.835)]
SLOPE = 0.2


def wall_y(x):
    for (a, b), (c, e) in zip(WALL, WALL[1:]):
        if a <= x <= c:
            return b + (e - b) * (x - a) / (c - a)
    return WALL[-1][1]


def _built(fn, name, seed, mirror):
    MIRROR[0] = mirror
    try:
        p = fn(name, seed)
    finally:
        MIRROR[0] = False
    if mirror:
        _mirror_y(p)
    return p


def guarded_toggle(p, c, r, a, n):
    """A toggle under a hinged red guard (22 x 30 mm) in a satin bezel, its black-yellow field."""
    fm = frame(c, r, a, n)
    p.box("Kit_Lip", (-0.013, -0.017, 0.0), (0.013, 0.017, 0.003), bevel=0.0012, segments=2, m=fm)
    p.box("Kit_Seal", (-0.010, -0.014, 0.0028), (0.010, 0.014, 0.0034), m=fm, panel=False)
    p.lathe("Kit_Lip", [(0.0035, 0.0), (0.0035, 0.004), (0.0015, 0.012), (0.0, 0.0125)], tuple(fm @ Vector((0.0, -0.002, 0.003))), axis=tuple(n), seg=12)
    p.box("Kit_Red", (-0.011, -0.015, 0.016), (0.011, 0.015, 0.0175), bevel=0.0008, segments=1, m=fm)
    for sv in (-1, 1):
        p.box("Kit_Red", (sv * 0.011 - 0.001, -0.015, 0.0034), (sv * 0.011 + 0.001, 0.015, 0.0175), m=fm, panel=False)
    p.box("Kit_Red", (-0.011, 0.014, 0.0034), (0.011, 0.015, 0.0175), m=fm, panel=False)
    for k in range(5):                                   # the black-yellow field under it
        p.box("Kit_Signal", (-0.016 + k * 0.0065, -0.024, 0.0), (-0.013 + k * 0.0065, -0.019, 0.0012), m=fm, panel=False)


def knob(p, c, n, r=0.011):
    """A knurled rotary selector: a satin skirt, a graphite knob with ribs, a lit index line."""
    n = Vector(n)
    p.lathe("Kit_Lip", [(r + 0.004, 0.0), (r + 0.004, 0.002), (r + 0.002, 0.003)], tuple(c), axis=tuple(n), seg=24)
    p.lathe("Kit_Inset", [(r, 0.002), (r, 0.012), (r * 0.85, 0.016), (0.0, 0.0165)], tuple(c), axis=tuple(n), seg=24)
    t = Vector((1, 0, 0)) if abs(n.x) < 0.9 else Vector((0, 1, 0))
    b = n.cross(t).normalized()
    t = b.cross(n).normalized()
    for k in range(16):
        ang = 2 * math.pi * k / 16
        q = Vector(c) + (t * math.cos(ang) + b * math.sin(ang)) * r
        p.sweep("Kit_Housing", [q + n * 0.003, q + n * 0.011], 0.0009, seg=4)
    p.box("Kit_GlowCool", (-0.0007, 0.002, 0.0164), (0.0007, r * 0.8, 0.0168), m=frame(Vector(c), t, b, n), panel=False)


def boot(p, c, n, r0=0.035, r1=0.012, h=0.03, folds=4):
    """A folded rubber boot round the stick's neck."""
    prof = [(r0, 0.0)]
    for k in range(folds * 2):
        t = (k + 1) / (folds * 2)
        rr = r0 + (r1 - r0) * t + (0.004 if k % 2 == 0 else -0.002)
        prof.append((rr, h * t))
    prof.append((0.0, h))
    p.lathe("Kit_Gasket", prof, tuple(c), axis=tuple(n), seg=32)


# ------------------------------------------------------------------ the seat's arm
def _seat_arm(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge", "Kit_PanelPaint": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    x0, x1, y0, y1, at = 16.72, 17.42, 0.42, 0.58, 0.62
    beam = [(x0, 0.53), (x1 - 0.03, 0.53), (x1, 0.56), (x1, 0.598), (x1 - 0.015, 0.605), (x0 + 0.02, 0.605), (x0, 0.585)]
    side_prism(p, "Kit_PanelPaint", beam, y0, y1, 0.01, 3)          # (shape pass 8. 10.) rounded, not a chamfered box
    # the forearm pad: leather on a graphite base, a domed top, a grey stitch in a dark channel
    p.box("Kit_Inset", (x0 + 0.015, y0 + 0.006, 0.603), (17.02, y1 - 0.006, 0.61), bevel=0.003, segments=2)
    p.box("Kit_Leather", (x0 + 0.02, y0 + 0.01, 0.608), (17.0, y1 - 0.01, at), bevel=0.01, segments=4)
    p.box("Kit_Leather", (x0 + 0.03, y0 + 0.02, 0.612), (16.99, y1 - 0.02, at + 0.006), bevel=0.008, segments=4)
    for uu in (y0 + 0.028, y1 - 0.028):
        p.box("Kit_Seal", (x0 + 0.04, uu - 0.0013, at + 0.0045), (16.98, uu + 0.0013, at + 0.0062), panel=False)
        xx = x0 + 0.045
        while xx + 0.004 < 16.975:
            p.box("Kit_Housing", (xx, uu - 0.0006, at + 0.0048), (xx + 0.004, uu + 0.0006, at + 0.0066), panel=False)
            xx += 0.006
    # 2 x 2 backlit keys and the stick ahead of the pad
    kc = Vector((17.115, (y0 + y1) / 2, 0.605))
    p.box("Kit_Inset", (17.03, y0 + 0.008, 0.6025), (x1 - 0.012, y1 - 0.012, 0.6052), bevel=0.0015, segments=2, panel=False)   # the controls' field
    p.box("Kit_Lip", (17.055, y0 + 0.012, 0.603), (17.175, y1 - 0.012, 0.607), bevel=0.0015, segments=2)
    for i, lab in enumerate(("LT", "GR", "VT", "ESP")):
        q = kc + X * (0.026 * (1 if i % 2 else -1)) + Y * (0.0245 * (1 if i < 2 else -1))
        keycap(p, frame(q - Z * 0.0055, -Y, X, Z), lab)
    stick(p, Vector((17.33, (y0 + y1) / 2, 0.605)), "ck_rcs", head_role="Kit_Frame", guard="d", plate_role="Kit_Inset",
          ball_role="Kit_Gasket", bars=15, grip_role="Kit_Inset")
    # a cool light line along the arm's outer underside (it reads from the aisle), its channel
    p.box("Kit_Seal", (x0 + 0.03, y1 - 0.002, 0.533), (x1 - 0.05, y1 + 0.0008, 0.545), panel=False)
    p.box("Kit_GlowStrip", (x0 + 0.033, y1 - 0.001, 0.5365), (x1 - 0.053, y1 + 0.0016, 0.5415), bevel=0.0008, segments=1, panel=False)
    # the bracket to the seat: a post under the arm and a plate on the seat's side, bolted
    # (critic r3: the post and the plate hung under the arm as blocks) a swept strut from the arm's underside curving
    # down into a round flange on the seat's side, a satin collar where it meets the arm
    for sx in (16.9, 17.2):
        p.box("Kit_PanelSatin", (sx - 0.07, y0 + 0.01, 0.505), (sx + 0.07, y0 + 0.09, 0.531), bevel=0.008, segments=3)   # the cover
        p.box("Kit_Lip", (sx - 0.045, y0 + 0.015, 0.497), (sx + 0.045, y0 + 0.085, 0.505), bevel=0.002, segments=2)     # top flange
        p.box("Kit_PanelSatin", (sx - 0.03, y0 + 0.02, 0.37), (sx + 0.03, y0 + 0.055, 0.5), bevel=0.01, segments=3)    # the post
        p.box("Kit_PanelSatin", (sx - 0.03, 0.386, 0.37), (sx + 0.03, y0 + 0.055, 0.405), bevel=0.01, segments=3)     # the leg
        p.box("Kit_Lip", (sx - 0.045, 0.378, 0.352), (sx + 0.045, 0.386, 0.422), bevel=0.002, segments=2)            # seat flange
        for su in (-1, 1):
            for sv in (-1, 1):
                screw(p, Vector((sx + su * 0.033, 0.3862, 0.387 + sv * 0.025)), Y, 0.0032)
                screw(p, Vector((sx + su * 0.033, y0 + 0.05 + sv * 0.022, 0.4968)), -Z, 0.0032)
        p.box("Kit_GlowStrip", (sx - 0.0015, y0 + 0.0195, 0.39), (sx + 0.0015, y0 + 0.021, 0.48), panel=False)        # a line down it
    _label(p, "st_hfcl", Vector((17.2, y1 + 0.0005, 0.565)), Y, -X, Z, scale=0.35)
    # (cockpit v3 r1, critic: one detail where SC has five) a satin strip along the top's outer edge, perforation in
    # the pad's middle band, two screwed graphite side panels with a grille between, a light line and an LED on the
    # front, a folded rubber boot round the stick, a guarded toggle by the keys, the serial plate
    p.box("Kit_Lip", (x0 + 0.02, y1 - 0.009, 0.603), (x1 - 0.02, y1 - 0.001, 0.607), bevel=0.0012, segments=2, panel=False)
    for i in range(int((16.97 - x0 - 0.06) / 0.006)):
        for j in range(5):
            hx, hu = x0 + 0.05 + i * 0.006, (y0 + y1) / 2 - 0.012 + j * 0.006 + (0.003 if i % 2 else 0.0)
            p.box("Kit_Seal", (hx - 0.001, hu - 0.001, at + 0.0058), (hx + 0.001, hu + 0.001, at + 0.0066), panel=False)
    for (sa, sb) in ((x0 + 0.03, x0 + 0.21), (x0 + 0.29, x0 + 0.47)):
        p.box("Kit_Inset", (sa, y1 - 0.002, 0.545), (sb, y1 + 0.004, 0.597), bevel=0.002, segments=2)
        for xx in (sa + 0.01, sb - 0.01):
            for zz in (0.553, 0.589):
                screw(p, Vector((xx, y1 + 0.0045, zz)), Y, 0.0035)
    p.box("Kit_Lip", (x0 + 0.215, y1 - 0.001, 0.55), (x0 + 0.285, y1 + 0.0035, 0.592), bevel=0.001, segments=1, panel=False)
    p.box("Kit_Perforated", (x0 + 0.219, y1 + 0.0032, 0.554), (x0 + 0.281, y1 + 0.0042, 0.588), panel=False)
    p.box("Kit_Seal", (x1 + 0.0002, y0 + 0.02, 0.566), (x1 + 0.0016, y1 - 0.02, 0.576), panel=False)
    p.box("Kit_GlowStrip", (x1 + 0.0012, y0 + 0.024, 0.5685), (x1 + 0.0028, y1 - 0.045, 0.5735), bevel=0.0006, segments=1, panel=False)
    led(p, Vector((x1 + 0.0016, y1 - 0.03, 0.571)), X, glow="Kit_GlowAmber", r=0.0024)
    boot(p, Vector((17.33, (y0 + y1) / 2, 0.609)), Z)
    guarded_toggle(p, Vector((17.225, y0 + 0.03, 0.6055)), -Y, X, Z)
    p.box("Kit_Lip", (x0 + 0.5, y1 - 0.0005, 0.5465), (x0 + 0.62, y1 + 0.0018, 0.5655), bevel=0.0005, segments=1, panel=False)
    p.box("Kit_Legend", (x0 + 0.502, y1 + 0.0012, 0.548), (x0 + 0.618, y1 + 0.0022, 0.564), panel=False)
    legend(p, "HF-SA 07  SN 2214", Vector((x0 + 0.56, y1 + 0.0022, 0.556)), -X, Z, Y, h=0.0055, role="Kit_Seal")
    p.collision_box((x0, y0, 0.22), (x1, y1, 0.68))
    return p


def seat_arm(name, seed, mirror=False):
    return _built(_seat_arm, name, seed, mirror)


# ------------------------------------------------------------------ the wall console
def _station(x):
    """(depth, inner top z) at x, linear between the stations."""
    for (xa, da, za), (xb, db, zb) in zip(STATIONS, STATIONS[1:]):
        if xa <= x <= xb:
            t = (x - xa) / (xb - xa)
            return da + (db - da) * t, za + (zb - za) * t
    return STATIONS[-1][1], STATIONS[-1][2]


def _V(x, s, z):
    """A point s in from the lining's face (s < 0: into the lining) at height z."""
    return Vector((x, wall_y(x) - LINER - s, z))


def _section(x):
    """The console's cross-section at x, round from the lining's foot: the kick recessed 5 cm (its top chamfered out
    to the face), the inner face, a 25 mm chamfer to the top, the sloped top back into the lining."""
    d, zi = _station(x)
    zo = zi + SLOPE * (d - 0.005)
    return [_V(x, -0.02, 0.0), _V(x, d - 0.05, 0.0), _V(x, d - 0.05, 0.10), _V(x, d, 0.13), _V(x, d, zi - 0.03),
            _V(x, d - 0.025, zi), _V(x, -0.02, zo)]


def top_pt(x, s):
    """A point on the console's sloped top."""
    d, zi = _station(x)
    return _V(x, s, zi + SLOPE * (d - 0.025 - s))


def top_frame(x, s):
    """(point, right, up, normal) on the top: up towards the wall (reads from the seat), right forward."""
    q = top_pt(x, s)
    a = (top_pt(x, s - 0.01) - q).normalized()
    r0 = (top_pt(x + 0.01, s) - q).normalized()
    n = r0.cross(a).normalized()
    if n.z < 0:
        n = -n
    r = a.cross(n).normalized()
    return q, r, a, n


def _skin(p, role, rings, centres):
    """Closed rings (same count) skinned with quads, each face turned away from its ring pair's centre; caps."""
    verts, faces = [], []
    m = len(rings[0])
    for ring in rings:
        verts += [Vector(v) for v in ring]
    def fix(f, c):
        a_, b_, c_ = verts[f[0]], verts[f[1]], verts[f[2]]
        nrm = (b_ - a_).cross(c_ - a_)
        ctr = sum((verts[i] for i in f), Vector()) / len(f)
        return f if nrm.dot(ctr - c) >= 0 else f[::-1]
    for k in range(len(rings) - 1):
        c = (centres[k] + centres[k + 1]) / 2
        for i in range(m):
            j = (i + 1) % m
            faces.append(fix([k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i], c))
    faces.append(fix(list(range(m)), centres[1]))                         # the caps face away from the next ring
    faces.append(fix([(len(rings) - 1) * m + i for i in range(m)], centres[-2]))
    return p.mesh(role, [tuple(v) for v in verts], faces)


def _top_patch(p, role, x0, x1, s0, s1, z0, z1):
    """A slab following the sloped top between x0..x1 and s0..s1 (s1 a number or a function of x: a field that
    narrows with the console), from z0 to z1 over it (insets, bezels)."""
    xs = [x0] + [st[0] for st in STATIONS if x0 < st[0] < x1] + [x1]
    rings, centres = [], []
    for x in xs:
        s1x = s1(x) if callable(s1) else s1
        ring = [top_pt(x, s0) + Vector((0, 0, z0)), top_pt(x, s1x) + Vector((0, 0, z0)),
                top_pt(x, s1x) + Vector((0, 0, z1)), top_pt(x, s0) + Vector((0, 0, z1))]
        rings.append(ring)
        centres.append(sum(ring, Vector()) / 4)
    _skin(p, role, rings, centres)


def _face_patch(p, role, x0, x1, z0, z1, o0, o1):
    """A slab on the console's inner face between x0..x1 and z0..z1, o0..o1 proud of it (windows, frames)."""
    xs = [x0] + [st[0] for st in STATIONS if x0 < st[0] < x1] + [x1]
    rings, centres = [], []
    for x in xs:
        d = _station(x)[0]
        ring = [_V(x, d + o0, z0), _V(x, d + o0, z1), _V(x, d + o1, z1), _V(x, d + o1, z0)]
        rings.append(ring)
        centres.append(sum(ring, Vector()) / 4)
    _skin(p, role, rings, centres)


# (author 9. 10. 2026: "layer more on it - mesh decals, everything stacked, SC level") the library's structural and
# info decals stacked on the console's faces: (item, weight, size w x h in m from the library index)
DRESS_FILL = {"rivet_row_4", "seam_straight", "bolt", "slot_s", "socket", "socket_round", "light_housing", "red_dot", "corner_mark"}
DRESS = [("rivet_row_4", 3, 0.2, 0.03), ("seam_straight", 2, 0.5, 0.04), ("bolt_row_4", 1, 0.42, 0.05), ("bolt", 2, 0.05, 0.05),
         ("slot_s", 2, 0.2, 0.05), ("socket", 1, 0.12, 0.08), ("socket_round", 1, 0.1, 0.1), ("vent_small", 1, 0.2, 0.14),
         ("light_housing", 1, 0.16, 0.08), ("panel_A12", 1, 0.14, 0.05), ("panel_B07", 1, 0.14, 0.05), ("panel_E16", 1, 0.14, 0.05),
         ("st_inspect", 1, 0.18, 0.03), ("st_torque", 1, 0.168, 0.03), ("st_gnd", 1, 0.134, 0.03), ("label_power", 1, 0.2, 0.07),
         ("corner_mark", 1, 0.08, 0.08), ("hazard_subtle", 1, 0.36, 0.05), ("red_dot", 1, 0.018, 0.018), ("st_vent", 0, 0.2255, 0.03)]


def _dress(p, rng, spots):
    """spots: (at, normal, xdir, ydir, max_w, max_h) - one library decal fitted into each (scaled down to fit, 35 % at
    least, else a smaller pick), chosen by weight."""
    import kit_batch2
    total = sum(w for it, w, _, _ in DRESS if it in DRESS_FILL)
    placed = {}                                    # (one item not twice within 30 cm: the drawings tell copies apart by it)
    for spot in spots:
        at, n, xd, yd, mw, mh = spot[:6]
        if len(spot) > 6:                          # a fixed item where it makes sense (a panel number, a stencil)
            item = spot[6]
            sw, sh = next((d[2], d[3]) for d in DRESS if d[0] == item)
            kit_batch2.label(p, item, at, n, xd, yd, scale=min(1.0, mw / sw, mh / sh))
            placed.setdefault(item, []).append(Vector(at))
            continue
        for _ in range(8):
            k = rng.uniform(0, total)
            for item, w, sw, sh in DRESS:
                k -= w if item in DRESS_FILL else 0
                if k <= 0 and item in DRESS_FILL:
                    break
            sc = min(1.0, mw / sw, mh / sh)
            if sc >= 0.35 and all((Vector(at) - q).length > 0.3 for q in placed.get(item, [])):
                kit_batch2.label(p, item, at, n, xd, yd, scale=sc)
                placed.setdefault(item, []).append(Vector(at))
                break


def _wall_console(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge", "Kit_PanelPaint": "Kit_FrameEdge", "Kit_PanelSatin": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    # the body: one loft through the stations, the panel paint (author 8. 10.: the column's glossy white)
    xs = [st[0] for st in STATIONS]
    rings = [_section(x) for x in xs]
    centres = []
    for x in xs:
        d, zi = _station(x)
        centres.append(_V(x, min(d * 0.45, d - 0.07), zi * 0.5))
    _skin(p, "Kit_PanelSatin", rings, centres)       # (concept B: white and lit, the mirror coat read grey)
    # the kick's back: dark, a light line along its top lights the recess and the floor (concept B)
    kick = [[_V(x, _station(x)[0] - 0.0505, 0.004), _V(x, _station(x)[0] - 0.0505, 0.098),
             _V(x, _station(x)[0] - 0.047, 0.098), _V(x, _station(x)[0] - 0.047, 0.004)] for x in xs]
    _skin(p, "Kit_Inset", kick, [sum(r, Vector()) / 4 for r in kick])
    # (v4 r1: a thin line under the overhang did not read) a 4 cm band of light along the kick's back: the recess glows
    # (author 9. 10.: the band did not fit and did not read as light) the kick's back lit softly over its height, the
    # source a bright LED line hidden under the overhang's edge
    band = [[_V(x, _station(x)[0] - 0.0468, 0.008), _V(x, _station(x)[0] - 0.0468, 0.092),
             _V(x, _station(x)[0] - 0.0458, 0.092), _V(x, _station(x)[0] - 0.0458, 0.008)] for x in xs]
    _skin(p, "Kit_GlowWindow", band, [sum(r, Vector()) / 4 for r in band])
    p.sweep("Kit_GlowFoot", [_V(x, _station(x)[0] - 0.04, 0.1025) for x in xs], 0.0035, seg=8)   # (on the overhang's underside)
    # the inner top edge: a satin rail in the chamfer and a cool light line under it, both running on into the dash
    p.sweep("Kit_Lip", [_V(x, _station(x)[0] - 0.011, _station(x)[1] - 0.012) for x in xs], 0.0045, seg=10)
    p.sweep("Kit_GlowStrip", [_V(x, _station(x)[0] + 0.0012, _station(x)[1] - 0.042) for x in xs], 0.0022, seg=8)
    # seams down the inner face at its breaks and between them
    # (v4 r1: black seams every 30 cm read as cracks) hairline seams only where the face breaks
    for x in (16.5, 17.25):
        d, zi = _station(x)
        p.sweep("Kit_Seal", [_V(x, d + 0.0002, 0.135), _V(x, d + 0.0002, zi - 0.05)], 0.0007, seg=4)
    da = _station(16.3)[0]
    t = (_V(16.31, da, 0) - _V(16.3, da, 0)).normalized()
    nf = Vector((t.y, -t.x, 0.0))
    if nf.dot(Vector((0, -1, 0))) < 0:
        nf = -nf
    _label(p, "maker", _V(16.3, da + 0.0008, 0.52), nf, t, Vector((0, 0, 1)), scale=0.55)
    # (concept B) one graphite field along the top, narrowing with the console, in a satin bezel: the SYS rockers in a
    # row by the wall, the emergency key, the power bars and the caution lamp ahead of them
    edge = lambda x: _station(x)[0] - 0.045                # noqa: E731
    _top_patch(p, "Kit_Lip", 16.03, 17.18, 0.018, lambda x: edge(x) + 0.012, -0.002, 0.0025)
    _top_patch(p, "Kit_Inset", 16.04, 17.17, 0.024, lambda x: edge(x) + 0.006, -0.001, 0.0034)
    labs = ("PWR", "EXT LT", "ENG", "LIGHTS", "GEAR", "VTOL")
    for i, lab in enumerate(labs):
        q, r, a, n = top_frame(16.1 + i * 0.08, 0.098)
        rocker_b(p, q + n * 0.0034, r, a, n, lit="Kit_GlowAmber" if lab == "GEAR" else "Kit_GlowCool")
        legend(p, lab, q - a * 0.034 + n * 0.0036, r, a, n, h=0.0085)
    q, r, a, n = top_frame(16.07, 0.142)
    legend(p, "SYS", q + n * 0.0036, r, a, n, h=0.013)
    q, r, a, n = top_frame(16.72, 0.068)
    emergency_key(p, q + n * 0.0034, r, a, n)
    for k, lab in enumerate(("MAIN", "BATT")):
        for gi in range(8):
            on = gi < (8, 5)[k]
            q, r, a, n = top_frame(16.84 + gi * 0.017, 0.064 + 0.03 * k)
            fm = frame(q + n * 0.0034, r, a, n)
            p.box("Kit_GlowCool" if on else "Kit_Seal", (-0.0065, -0.004, 0.0), (0.0065, 0.004, 0.0009 if on else 0.0004), m=fm, panel=False)
        q, r, a, n = top_frame(16.805, 0.064 + 0.03 * k)
        legend(p, lab, q + n * 0.0036, r, a, n, h=0.0055)
    q, r, a, n = top_frame(17.1, 0.08)
    led(p, q + n * 0.0034, n, glow="Kit_GlowAmber", r=0.004)
    legend(p, "CAUT", q - a * 0.02 + n * 0.0036, r, a, n, h=0.0055)
    # (concept B) lit windows in the inner face: a dark recess in a satin frame, a band of light along its foot
    for (wx0, wx1) in ((16.08, 16.46), (16.56, 17.16), (17.3, 17.58)):
        _face_patch(p, "Kit_Lip", wx0 - 0.008, wx1 + 0.008, 0.162, 0.408, 0.0004, 0.003)
        # (author 9. 10.: dark rectangles with no purpose) the cabin air's return grilles: a diffuser lit from behind,
        # horizontal louvres over it in the satin frame, the light between them; VENT stencilled over each
        _face_patch(p, "Kit_GlowWindow", wx0, wx1, 0.17, 0.4, 0.0004, 0.0016)
        zz = 0.182
        while zz < 0.39:
            _face_patch(p, "Kit_Inset", wx0 + 0.006, wx1 - 0.006, zz, zz + 0.011, 0.0016, 0.007)
            zz += 0.021
        for vx in (wx0 + (wx1 - wx0) / 3, wx0 + 2 * (wx1 - wx0) / 3):
            _face_patch(p, "Kit_Lip", vx - 0.004, vx + 0.004, 0.17, 0.4, 0.0016, 0.0075)          # louvre bearers
    # the stacked decals: a band on the inner face over the windows, the gaps between them, the top's front
    import random as _r
    rng = _r.Random(seed * 7 + 3)
    spots = []
    x = 15.98
    while x < 17.62:
        d, zi = _station(x)
        tt = (_V(x + 0.01, d, 0) - _V(x, d, 0)).normalized()
        nn = Vector((tt.y, -tt.x, 0.0))
        if nn.dot(Vector((0, -1, 0))) < 0:
            nn = -nn
        for zz, mh in ((0.47, 0.07), (min(0.58, zi - 0.075), 0.05)):
            if rng.random() < 0.8:
                spots.append((_V(x + rng.uniform(-0.02, 0.02), d, zz), nn, tt, Vector((0, 0, 1)), 0.2, mh))
        x += rng.uniform(0.1, 0.16)
    for wi, (wx0, wx1) in enumerate(((16.08, 16.46), (16.56, 17.16), (17.3, 17.58))):
        for (xx_, item, mw, mh) in ((wx0 + 0.06, ("panel_A12", "panel_B07", "panel_E16")[wi], 0.1, 0.035), (wx1 - 0.12, "st_vent", 0.17, 0.025)):
            d, zi = _station(xx_)
            tt = (_V(xx_ + 0.01, d, 0) - _V(xx_, d, 0)).normalized()
            nn = Vector((tt.y, -tt.x, 0.0))
            if nn.dot(Vector((0, -1, 0))) < 0:
                nn = -nn
            spots.append((_V(xx_, d, 0.428), nn, tt, Vector((0, 0, 1)), mw, mh, item))
    for gx in (16.51, 17.23):
        d, zi = _station(gx)
        tt = (_V(gx + 0.01, d, 0) - _V(gx, d, 0)).normalized()
        nn = Vector((tt.y, -tt.x, 0.0))
        if nn.dot(Vector((0, -1, 0))) < 0:
            nn = -nn
        spots.append((_V(gx, d, 0.28), nn, Vector((0, 0, 1)), -tt, 0.2, 0.045, "bolt_row_4"))   # the frames' join, bolted
    for fx in (17.3, 17.45, 17.6, 17.74):
        q, r, a, n = top_frame(fx, 0.035)
        spots.append((q, n, r, a, 0.14, 0.04))
    _dress(p, rng, spots)
    # the collision: one hull per span
    for (x0, x1) in zip(xs, xs[1:]):
        pts = []
        for x in (x0, x1):
            d, zi = _station(x)
            pts += [_V(x, -0.02, 0.0), _V(x, d, 0.0), _V(x, d, zi), _V(x, -0.02, zi + SLOPE * (d - 0.005))]
        p.collision_hull(pts)
    return p


def wall_console(name, seed, mirror=False):
    return _built(_wall_console, name, seed, mirror)


# ------------------------------------------------------------------ the seat back's shell
def seat_back(name, seed):
    """The pilot seat's back from behind (cockpit v3 r1, critic: a black slab): a glossy shell on the back's 8 deg
    slope (measured off PilotSeat.glb as placed: x 16.636 at 0.45 m, 16.55 at 1.05 m), a graphite inset in four
    fields, the mechanism cover with screws, the serial plate and a black-yellow field, a light line under the top."""
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    u = Vector((-0.086, 0.0, 0.6)).normalized()           # up the back
    n = Vector((-u.z, 0.0, u.x))                           # out of it, aft
    r = u.cross(n)                                         # right x up = out: the viewer behind sees -y as right
    r = -r if r.dot(Vector((0, -1, 0))) < 0 else r
    o = Vector((16.636 - 0.143 * (0.74 - 0.45), 0.0, 0.74)) + n * 0.003
    fm = lambda q: frame(q, r, u, n)                       # noqa: E731
    p.box("Kit_Frame", (-0.2, -0.3, -0.006), (0.2, 0.3, 0.012), bevel=0.01, segments=3, m=fm(o))
    for (a0, a1, b0, b1) in ((-0.15, -0.002, 0.02, 0.24), (0.002, 0.15, 0.02, 0.24), (-0.15, -0.002, -0.2, 0.016), (0.002, 0.15, -0.2, 0.016)):
        p.box("Kit_Inset", (a0, b0, 0.011), (a1, b1, 0.015), bevel=0.002, segments=2, m=fm(o))
    for su in (-1, 1):
        for sv in (-1, 1):
            screw(p, fm(o) @ Vector((su * 0.175, sv * 0.27, 0.0125)), n, 0.004)
    # the mechanism cover at the bottom
    p.box("Kit_Housing", (-0.08, -0.29, 0.012), (0.08, -0.21, 0.03), bevel=0.006, segments=3, m=fm(o))
    for su in (-1, 1):
        for sv in (-1, 1):
            screw(p, fm(o) @ Vector((su * 0.068, -0.25 + sv * 0.028, 0.0302)), n, 0.0035)
    for k in range(6):                                     # the black-yellow field over it
        p.box("Kit_Signal", (-0.04 + k * 0.014, -0.205, 0.012), (-0.033 + k * 0.014, -0.188, 0.0135), m=fm(o), panel=False)
    p.box("Kit_Lip", (0.03, 0.25, 0.0118), (0.13, 0.28, 0.0135), bevel=0.0005, segments=1, m=fm(o), panel=False)
    p.box("Kit_Legend", (0.032, 0.252, 0.0128), (0.128, 0.278, 0.0142), m=fm(o), panel=False)
    legend(p, "PS-07  SN 0417", fm(o) @ Vector((0.08, 0.265, 0.0142)), r, u, n, h=0.0075, role="Kit_Seal")
    p.box("Kit_Seal", (-0.16, 0.255, 0.0118), (-0.02, 0.271, 0.0132), m=fm(o), panel=False)
    p.box("Kit_GlowStrip", (-0.157, 0.259, 0.0128), (-0.023, 0.267, 0.0145), bevel=0.0008, segments=1, m=fm(o), panel=False)
    _label(p, "maker", fm(o) @ Vector((0.0, -0.06, 0.0151)), n, r, u, scale=0.45)
    p.collision_box(tuple(fm(o) @ Vector((-0.2, -0.3, -0.006))), tuple(fm(o) @ Vector((0.2, 0.3, 0.03))))
    # (cockpit v4, author 9. 10.: layers; critic r3/r4: the seat's shell smooth and grey) satin shell wings round the
    # backrest's sides and rear corners (measured off PilotSeat.glb as placed: its back's x and half width by height),
    # a graphite inset on each, a light line down the front edge, screws
    prof = [(0.55, 16.61, 0.36), (0.65, 16.598, 0.337), (0.75, 16.584, 0.326), (0.85, 16.569, 0.305), (0.95, 16.556, 0.272)]
    for sd in (1, -1):
        rings, cens, ins, inc, glow = [], [], [], [], []
        for z, xb, w in prof:
            xr, xf = xb - 0.006, xb + 0.17
            yo, yi = sd * (w + 0.008), sd * (w + 0.02)
            ring = [Vector((xr - 0.012, sd * (w - 0.12), z)), Vector((xr, sd * (w - 0.12), z)), Vector((xr, yo, z)), Vector((xf, yo, z)),
                    Vector((xf, yi, z)), Vector((xr - 0.012, yi, z))]
            rings.append(ring)
            cens.append(Vector(((xr + xf) / 2, sd * (w - 0.02), z)))
            glow.append(Vector((xf + 0.0015, sd * (w + 0.014), z)))
            if 0.6 <= z <= 0.9:
                ring2 = [Vector((xr + 0.03, yi - sd * 0.0005, z)), Vector((xf - 0.03, yi - sd * 0.0005, z)),
                         Vector((xf - 0.03, yi + sd * 0.003, z)), Vector((xr + 0.03, yi + sd * 0.003, z))]
                ins.append(ring2)
                inc.append(sum(ring2, Vector()) / 4 - Vector((0, sd * 0.01, 0)))
        _skin(p, "Kit_PanelSatin", rings, cens)
        if len(ins) >= 2:
            _skin(p, "Kit_Inset", ins, inc)
        p.sweep("Kit_GlowStrip", glow, 0.0025, seg=8)
        for z, xb, w in (prof[0], prof[-1]):
            for xx in (xb + 0.03, xb + 0.14):
                screw(p, Vector((xx, sd * (w + 0.0205), z + (0.02 if z < 0.7 else -0.02))), Vector((0, sd, 0)), 0.0035)
    # (critic r3: the floor's centre empty) behind the seat a graphite anti-slip field in a 20 mm satin frame, a studded
    # tread, the maker's mark at its aft end
    fx0, fx1, fy = 16.0, 16.46, 0.27
    p.box("Kit_Lip", (fx0, -fy, -0.002), (fx1, fy, 0.004), bevel=0.002, segments=2)
    p.box("Kit_Inset", (fx0 + 0.02, -fy + 0.02, 0.0), (fx1 - 0.02, fy - 0.02, 0.0055), bevel=0.0015, segments=1)
    xx = fx0 + 0.05
    while xx < fx1 - 0.04:
        yy = -fy + 0.05
        while yy < fy - 0.04:
            p.lathe("Kit_Housing", [(0.006, 0.0), (0.006, 0.0012), (0.0, 0.0018)], (xx, yy, 0.0055), axis=(0, 0, 1), seg=10)
            yy += 0.03
        xx += 0.03
    _label(p, "maker", Vector((fx0 + 0.035, 0.0, 0.0062)), Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((1, 0, 0)), scale=0.5)
    return p
