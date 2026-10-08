"""Wayfarer cockpit v3 (author 8. 10. 2026, ArtSource/Ships/Wayfarer/Concept/Cockpit/cockpit_layout_v3_proposal.png):
the sticks on the seat's arms, the consoles thin along the walls and run into the dash wings (one shape, the glossy
column paint), aisles round the seat on both sides.

  SM_Kit_Cockpit_SeatArm07W_L / _R          the seat's forearm rest: a leather pad, 2 x 2 backlit keys, the stick; a
                                            bracket down to the seat's side
  SM_Kit_Cockpit_ConsoleWall18W_L / _R      the wall console from 16.0 m to the dash wing: an intake, a service
                                            hatch, a tower with the emergency key, six rockers and the status bars on
                                            its seat-facing slope, light lines along its inner face

Both are built in the ship layout's coordinates (x from the stern, y to port, z from the cockpit floor) and placed at
the layout's origin (interior.kit_modules.run_parts [[0, 0, 1.15], [1, 0], [part]]): the console follows the hull's
wall polygon exactly. _R is the mirror of _L (kit_cockpit_b._mirror_y: the text still reads right).
"""
import math

from mathutils import Vector

import kit_geo
from kit_geo import frame
import kit_cockpit_b as kb
from kit_cockpit_b import side_prism, end_prism, screw, legend, led, keycap, rocker_b, emergency_key, MIRROR, _mirror_y
from kit_cockpit import stick, _label

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
WALL = [(15.2, 1.75), (16.5, 1.6), (18.6, 1.0)]     # the cockpit's port wall (Wayfarer_layout.json, rooms.cockpit.poly)
LINER = 0.1                                         # the lining's face inside the hull line
CX0, CX1 = 16.0, 17.85                              # the console's aft end .. its front, tucked into the dash wing
TOP = 0.70                                          # the console's top over the cockpit floor


def wall_y(x):
    for (a, b), (c, e) in zip(WALL, WALL[1:]):
        if a <= x <= c:
            return b + (e - b) * (x - a) / (c - a)
    return WALL[-1][1]


def depth(x):
    """The console's depth from the lining: 0.36 m aft, 0.06 m at the dash (the aisle stays >= 0.53 m)."""
    return 0.36 + (0.06 - 0.36) * (min(max(x, CX0), 17.75) - CX0) / (17.75 - CX0)


def inner_y(x):
    return wall_y(x) - LINER - depth(x)


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
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    x0, x1, y0, y1, at = 16.72, 17.42, 0.42, 0.58, 0.62
    beam = [(x0, 0.53), (x1 - 0.03, 0.53), (x1, 0.56), (x1, 0.598), (x1 - 0.015, 0.605), (x0 + 0.02, 0.605), (x0, 0.585)]
    side_prism(p, "Kit_Frame", beam, y0, y1, 0.006, 1)
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
    p.box("Kit_Frame", (16.87, y0 + 0.004, 0.3), (16.95, y0 + 0.045, 0.532), bevel=0.008, segments=3)
    p.box("Kit_Lip", (16.81, 0.372, 0.28), (17.01, 0.428, 0.39), bevel=0.005, segments=3)
    for xx in (16.83, 16.99):
        for zz in (0.295, 0.375):
            screw(p, Vector((xx, 0.4285, zz)), Y, 0.004)
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
def _inner_frame(xa, xb, z, out=0.0):
    """A frame on the console's inner face between xa and xb: x along it (forward), y up, z out (to the aisle)."""
    a = Vector((xa, inner_y(xa), z))
    b = Vector((xb, inner_y(xb), z))
    t = (b - a).normalized()
    n = Vector((t.y, -t.x, 0.0))                       # out of the face, to the seat
    return a + n * out, t, n, (b - a).length


def _wall_console(name, seed):
    p = kit_geo.Part(name, seed)
    p.edge_roles = {"Kit_Frame": "Kit_FrameEdge"}
    p.sharp_deg = 20.0
    xs = [CX0, 16.5, CX1]
    inner = [(x, inner_y(x)) for x in xs]
    outer = [(x, wall_y(x) - LINER + 0.02) for x in xs]     # 2 cm into the lining: no gap at the wall
    p.poly_prism("Kit_Frame", inner + outer[::-1], frame(Vector((0, 0, TOP)), X, Y, Z), TOP, bevel=0.009, segments=1)
    # a dark kick 4 cm in along the floor
    kick = [(x, inner_y(x) + 0.035) for x in xs]
    p.poly_prism("Kit_Inset", kick + outer[::-1], frame(Vector((0, 0, 0.05)), X, Y, Z), 0.05, bevel=0.003, segments=1)
    # the inner face: graphite panels with seams and screws, a light line low and one under the top edge
    for (xa, xb) in ((CX0, 16.5), (16.5, 17.75)):
        o, t, n, ln = _inner_frame(xa, xb, 0.0)
        fm = frame(o, t, Z, n)
        segs = 1 if ln < 0.6 else 3
        for k in range(segs):
            s0 = 0.03 + k * (ln - 0.06) / segs + (0.002 if k else 0.0)
            s1 = 0.03 + (k + 1) * (ln - 0.06) / segs - (0.002 if k < segs - 1 else 0.0)
            p.box("Kit_Inset", (s0, 0.12, -0.002), (s1, TOP - 0.08, 0.005), bevel=0.003, segments=2, m=fm)
            for ss in (s0 + 0.014, s1 - 0.014):
                for zz in (0.134, TOP - 0.094):
                    screw(p, fm @ Vector((ss, zz, 0.0055)), n, 0.003)
        for zz, h in ((0.09, 0.005), (TOP - 0.045, 0.004)):
            p.box("Kit_Seal", (0.02, zz - 0.006, -0.001), (ln - 0.02, zz + 0.006, 0.0012), m=fm, panel=False)
            p.box("Kit_GlowStrip", (0.023, zz - h / 2, 0.0005), (ln - 0.023, zz + h / 2, 0.0022), bevel=0.0008, segments=1, m=fm, panel=False)
    o, t, n, ln = _inner_frame(16.5, 17.75, 0.0)
    _label(p, "st_service", frame(o, t, Z, n) @ Vector((0.25, 0.3, 0.0056)), n, t, Z, scale=0.6)
    _label(p, "pn_2", frame(o, t, Z, n) @ Vector((0.06, TOP - 0.11, 0.0056)), n, t, Z, scale=0.6)
    # 1 the aft top: a service hatch (a framed lid, a recessed pull, four screws, its plate)
    hx0, hx1 = CX0 + 0.04, 16.62
    hu0, hu1 = inner_y(hx1) + 0.03, wall_y(hx1) - LINER - 0.03
    zt = TOP
    p.box("Kit_Seal", (hx0 - 0.004, hu0 - 0.004, zt - 0.001), (hx1 + 0.004, hu1 + 0.004, zt + 0.0008), panel=False)
    p.box("Kit_Frame", (hx0, hu0, zt), (hx1, hu1, zt + 0.012), bevel=0.004, segments=2)
    p.box("Kit_Inset", (hx0 + 0.02, hu0 + 0.02, zt + 0.011), (hx1 - 0.02, hu1 - 0.02, zt + 0.015), bevel=0.002, segments=2)
    for xx in (hx0 + 0.035, hx1 - 0.035):
        for uu in (hu0 + 0.035, hu1 - 0.035):
            screw(p, Vector((xx, uu, zt + 0.015)), Z, 0.0045)
    p.box("Kit_Seal", (hx1 - 0.16, (hu0 + hu1) / 2 - 0.015, zt + 0.008), (hx1 - 0.08, (hu0 + hu1) / 2 + 0.015, zt + 0.0152), bevel=0.003, segments=2)
    p.sweep("Kit_Lip", [Vector((hx1 - 0.15, (hu0 + hu1) / 2, zt + 0.011)), Vector((hx1 - 0.09, (hu0 + hu1) / 2, zt + 0.011))], 0.003, seg=12)
    p.box("Kit_Lip", (hx0 + 0.06, hu0 + 0.05, zt + 0.0148), (hx0 + 0.15, hu0 + 0.1, zt + 0.0162), bevel=0.0006, segments=1, panel=False)
    p.box("Kit_Legend", (hx0 + 0.062, hu0 + 0.052, zt + 0.0152), (hx0 + 0.148, hu0 + 0.098, zt + 0.0166), panel=False)
    legend(p, "SERVICE", Vector((hx0 + 0.105, hu0 + 0.081, zt + 0.0166)), X, Y, Z, h=0.009, role="Kit_Seal")
    legend(p, "HF-WC 01", Vector((hx0 + 0.105, hu0 + 0.064, zt + 0.0166)), X, Y, Z, h=0.0065, role="Kit_Seal")
    # 2 the tower beside the pilot (x 16.72 .. 17.18): its slope faces the seat with the emergency key, two rows of
    # rockers and the status bars
    tx0, tx1 = 16.72, 17.18
    yi = inner_y(tx1) + 0.012                          # never over the aisle (the inner edge leans in forward)
    yo = wall_y(tx1) - LINER + 0.01
    th = 0.24
    prof = [(yi, TOP), (yo, TOP), (yo, TOP + th), (yi + 0.11, TOP + th), (yi, TOP + 0.08)]
    end_prism(p, "Kit_Frame", prof, tx0, tx1, 0.008, 1)
    a = Vector((0.0, 0.11, th - 0.08)).normalized()    # up the slope
    r = X
    nf = r.cross(a)                                    # out of the slope, to the seat and up
    if nf.y > 0:
        r, nf = -r, -nf
    fc = Vector(((tx0 + tx1) / 2, yi + 0.055, TOP + 0.08 + (th - 0.08) / 2)) + nf * 0.0005
    ff = lambda o: frame(o, r, a, nf)                  # noqa: E731
    w2, h2 = (tx1 - tx0) / 2 - 0.02, ((0.11 ** 2 + (th - 0.08) ** 2) ** 0.5) / 2 - 0.012
    p.box("Kit_Lip", (-w2 - 0.004, -h2 - 0.004, -0.004), (w2 + 0.004, h2 + 0.004, 0.0015), bevel=0.002, segments=2, m=ff(fc))
    p.box("Kit_Inset", (-w2, -h2, -0.004), (w2, h2, 0.002), m=ff(fc), panel=False)
    for row, labs in enumerate((("PWR", "EXT LT", "ENG"), ("LIGHTS", "GEAR", "VTOL"))):
        for i, lab in enumerate(labs):
            q = fc + r * (-0.155 + 0.068 * i) + a * (0.03 - 0.062 * row) + nf * 0.002
            rocker_b(p, q, r, a, nf, lit="Kit_GlowAmber" if lab == "GEAR" else "Kit_GlowCool")
            legend(p, lab, q - a * 0.027 + nf * 0.0002, r, a, nf, h=0.0068)
    emergency_key(p, fc + r * 0.135 + a * 0.0 + nf * 0.002, r, a, nf)
    # the tower's seat-facing foot (TOP .. TOP + 0.08): a light line, a plate; two seams across its top
    p.box("Kit_Seal", (tx0 + 0.02, yi - 0.0012, TOP + 0.035), (tx1 - 0.02, yi + 0.0004, TOP + 0.047), panel=False)
    p.box("Kit_GlowStrip", (tx0 + 0.023, yi - 0.0026, TOP + 0.0385), (tx1 - 0.023, yi - 0.0006, TOP + 0.0435), bevel=0.0006, segments=1, panel=False)
    p.box("Kit_Lip", (tx0 + 0.03, yi - 0.0012, TOP + 0.054), (tx0 + 0.12, yi + 0.0004, TOP + 0.072), bevel=0.0005, segments=1, panel=False)
    p.box("Kit_Legend", (tx0 + 0.032, yi - 0.0018, TOP + 0.0555), (tx0 + 0.118, yi - 0.0008, TOP + 0.0705), panel=False)
    legend(p, "PWR MGMT", Vector((tx0 + 0.075, yi - 0.0018, TOP + 0.063)), X, Z, -Y, h=0.0068, role="Kit_Seal")
    for xs_ in (tx0 + 0.15, tx1 - 0.15):
        p.box("Kit_Seal", (xs_ - 0.001, yi + 0.115, TOP + th - 0.0006), (xs_ + 0.001, yo - 0.005, TOP + th + 0.0004), panel=False)
    # the status bars on the tower's top, read from the seat
    sc = Vector(((tx0 + tx1) / 2, (yi + 0.11 + yo) / 2, TOP + th + 0.0005))
    p.box("Kit_Lip", (sc.x - 0.075, sc.y - 0.04, sc.z - 0.001), (sc.x + 0.075, sc.y + 0.04, sc.z + 0.003), bevel=0.0015, segments=2)
    p.box("Kit_Seal", (sc.x - 0.07, sc.y - 0.035, sc.z + 0.003), (sc.x + 0.07, sc.y + 0.035, sc.z + 0.0035), panel=False)
    fm = lambda o: frame(o, X, Y, Z)                   # noqa: E731
    for k, lab in enumerate(("MAIN", "BATT", "TEMP")):
        q = Vector((sc.x - 0.02, sc.y + 0.022 - 0.022 * k, sc.z + 0.0035))
        for gi in range(8):
            on = gi < (8, 6, 3)[k]
            x0_ = 0.004 + gi * 0.0068
            p.box(("Kit_GlowCool" if k < 2 else "Kit_GlowAmber") if on else "Kit_Inset",
                  (x0_, -0.0035, 0.0), (x0_ + 0.0055, 0.0035, 0.0007 if on else 0.0003), m=fm(q), panel=False)
        legend(p, lab, q - X * 0.026 + Z * 0.0002, X, Y, Z, h=0.007)
    _label(p, "maker", Vector(((tx0 + tx1) / 2, yo - 0.0005 - 0.0, TOP + 0.15)), Y, -X, Z, scale=0.3)
    # 3 the front top towards the dash (critic r1: 3 modules): a graphite field sunk in a satin lip with four backlit
    # keys, two knurled selectors and a small grille, its legends
    gx0, gx1 = 17.22, 17.68
    gu0, gu1 = inner_y(gx1) + 0.012, wall_y(gx1) - LINER - 0.012
    gm = (gu0 + gu1) / 2
    p.box("Kit_Lip", (gx0, gu0, TOP - 0.001), (gx1, gu1, TOP + 0.004), bevel=0.0015, segments=2)
    p.box("Kit_Inset", (gx0 + 0.006, gu0 + 0.006, TOP + 0.002), (gx1 - 0.006, gu1 - 0.006, TOP + 0.0045), panel=False)
    for i, lab in enumerate(("DOOR", "RAMP", "LOCK", "CAB")):
        q = Vector((gx0 + 0.04 + i * 0.05, gm, TOP + 0.0045 - 0.0055))
        keycap(p, frame(q, -Y, X, Z), lab)
    for i, lab in enumerate(("COOL", "VENT")):
        c = Vector((gx0 + 0.26 + i * 0.065, gm + 0.004, TOP + 0.0045))
        knob(p, c, Z)
        legend(p, lab, c + Vector((0.0, -0.024, 0.0002)), X, Y, Z, h=0.0055)
    p.box("Kit_Lip", (gx1 - 0.075, gm - 0.022, TOP + 0.0045), (gx1 - 0.012, gm + 0.022, TOP + 0.0065), bevel=0.0008, segments=1, panel=False)
    p.box("Kit_Perforated", (gx1 - 0.072, gm - 0.019, TOP + 0.0063), (gx1 - 0.015, gm + 0.019, TOP + 0.0072), panel=False)
    # a satin strip along the top's inner edge
    for (xa, xb) in ((CX0, 16.5), (16.5, 17.75)):
        o, t, n, ln = _inner_frame(xa, xb, TOP - 0.006, out=-0.004)
        p.box("Kit_Lip", (0.0, 0.0, -0.002), (ln, 0.006, 0.0035), bevel=0.0012, segments=2, m=frame(o, t, Z, n), panel=False)
        o2, t2, n2, ln2 = _inner_frame(xa, xb, TOP - 0.016, out=0.0)
        p.box("Kit_GlowStrip", (0.01, -0.0025, -0.0005), (ln2 - 0.01, 0.0025, 0.0018), bevel=0.0006, segments=1, m=frame(o2, t2, Z, n2), panel=False)
    p.collision_hull([Vector((x, y, z)) for (x, y) in inner + outer for z in (0.0, TOP + 0.02)])
    p.collision_box((tx0, yi, TOP), (tx1, yo, TOP + th))
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
    return p
