"""Cockpit parts as factory parts (author 7. 10. 2026: the cockpit built from extruded outlines with one uniform 4 mm
bevel and the ship's ad-hoc materials kept reading as plastic after ten critic rounds - the factory's parts, modelled
with per-element edges on the kit's calibrated material base, read as SC in a few). Pilot: the left armrest console.

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- factory --only SM_Kit_Cockpit_Console12W_A

SM_Kit_Cockpit_Console12W_A  the left console of a one-seat cockpit after SC's Aurora (Docs/Kit/etalon/sc/konzole_*.jpg,
                             kreslo_*.jpg; sheet Docs/Kit/parts/KF-COCKPIT-CONSOLE/part.md)
Frame: x along the console (0 aft .. 1.2 forward), y = u outward from the inner face (0) to the hull (0.67), the pilot on
-y; z up from the cockpit floor. The deck top is 0.60 m (elbow height of a seated pilot); the arm shelf reaches 7 cm in
over the gap to the seat; the stick stands 3 cm inside the inner face (0.40 m from the seat's axis), 0.8 m from the aft
end (a forearm from the elbow on the wrist rest); its head 0.18 m over the deck, leaning 8 deg forward and 6 deg in;
the control block sits forward and outboard with 0.15 m clear round the hand.
Edge hierarchy (the critic's "everything one 4 mm bevel"): primary masses 18-22 mm, plates 8-12 mm, small fittings
1-3 mm; every bevel face carries the edge-wear mask.
"""
import math

from mathutils import Vector

import kit_geo
import kit_batch2
from kit_geo import frame

L, W, TOP = 1.2, 0.67, 0.60


def _label(p, item, at, n, right, up, scale=0.5, is_label=True):
    kit_batch2.label(p, item, at, n, right, up, scale=scale, is_label=is_label)


def _loft(p, role, rings):
    """Skin closed rings (same point count) with quads, shaded smooth, caps on both ends (kit_geo.Part.mesh)."""
    verts, faces = [], []
    m = len(rings[0])
    for r in rings:
        verts += [tuple(v) for v in r]
    for k in range(len(rings) - 1):
        for i in range(m):
            j = (i + 1) % m
            faces.append([k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i])
    faces.append(list(range(m))[::-1])
    faces.append([(len(rings) - 1) * m + i for i in range(m)])
    return p.mesh(role, verts, faces)


def _rr(w, d, r, n=4):
    """A rounded rectangle w x d (centred), its corners in n steps, counter-clockwise."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ------------------------------------------------------------------ the stick (SC's: a chrome ball on a hatched base)
def stick(p, base, label, head_role="Kit_Shell", guard="c", plate_role="Kit_Housing", ball_role="Kit_Lip", bars=28, grip_role="Kit_Gasket"):
    Z, X, Y = Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))
    # the base: a housing-grey plate with an 8 mm rounded edge, four screws, a dark well, the hatch ring, a satin collar
    # (sunk into the arm unit, flush: it overhung the arm's edge - critic r1)
    p.box(plate_role, base + Vector((-0.058, -0.052, -0.012)), base + Vector((0.058, 0.052, 0.0015)), bevel=0.006, segments=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = base + Vector((sx * 0.048, sy * 0.042, 0.0015))
            p.lathe("Kit_Lip", [(0.0035, 0.0), (0.0035, 0.0006), (0.0, 0.0009)], q, seg=12)
    if bars != 28:
        # a solid hazard ring 14 mm wide: 2 x bars slanted segments, Halcyon orange and black alternating, no gaps, a
        # polished 3 mm ring outside (the thin bars on graphite read as a beige dial - critic r32)
        # author 8. 10. (in the cockpit): the hatched ring looked bad - a dark well with a glowing ring, a high-tech light
        p.lathe("Kit_Graphite", [(0.05, 0.0015), (0.05, 0.004), (0.034, 0.004), (0.034, 0.0015)], base, seg=64)
        p.lathe("Kit_GlowStrip", [(0.0455, 0.0038), (0.0455, 0.0052), (0.0425, 0.0052), (0.0425, 0.0038)], base, seg=64)
        p.lathe("Kit_Lip", [(0.053, 0.0015), (0.053, 0.0045), (0.0505, 0.005), (0.0505, 0.0015)], base, seg=64)
    else:
        p.lathe("Kit_Graphite", [(0.05, 0.0015), (0.05, 0.0035), (0.034, 0.0035), (0.034, 0.0015)], base, seg=48)
    for k in range(bars if bars == 28 else 0):                                     # oblique hatch bars, Halcyon orange on graphite
        a0 = 2 * math.pi * k / bars
        pa = base + Vector((0.037 * math.cos(a0), 0.037 * math.sin(a0), 0.0037))
        pb = base + Vector((0.048 * math.cos(a0 + 0.16), 0.048 * math.sin(a0 + 0.16), 0.0037))
        rb = 0.0026 if bars == 28 else 0.0045                  # 15 bars: 9 mm orange, 9 mm black
        p.sweep("Kit_Signal", [pa, pb], rb, seg=6, scale_y=0.00065 / rb)       # (Halcyon orange bars on black)
    p.lathe("Kit_Lip", [(0.034, 0.0), (0.034, 0.006), (0.03, 0.009), (0.024, 0.01)], base, seg=40)
    # the polished ball and the neck
    prof = [(0.0, -0.002)] + [(0.021 * math.sin(math.pi * k / 16), 0.021 - 0.021 * math.cos(math.pi * k / 16)) for k in range(1, 16)] + [(0.0, 0.042)]
    p.lathe(ball_role, prof, base + Z * 0.006, seg=40)
    lean = Vector((math.sin(math.radians(8)), -math.sin(math.radians(6)), 1.0)).normalized()   # forward and in (-y)
    n0 = base + Z * 0.04
    p.lathe("Kit_Lip", [(0.0085, 0.0), (0.0085, 0.022), (0.011, 0.026)], n0, axis=lean, seg=24)
    # the grip: a shaped section (narrow at the neck, a palm swell aft, a flat front) lofted along the lean, rubber
    fwd = (X - lean * X.dot(lean)).normalized()             # forward, square to the grip
    sd = lean.cross(fwd).normalized()                        # outboard (+y); the thumb is on -sd, the pilot's side
    g0 = n0 + lean * 0.024
    rings = []
    gl = 0.105
    for k in range(29):                                       # 28 sections (author 8. 10.: the grip read faceted)
        t = k / 28
        d = 0.034 + 0.014 * math.sin(math.pi * min(t / 0.8, 1.0)) + 0.004 * (t > 0.85)
        w = 0.03 + 0.007 * math.sin(math.pi * min(t / 0.8, 1.0))
        bulge = -0.006 * math.sin(math.pi * min(t / 0.8, 1.0))          # the palm swell sits aft
        c = g0 + lean * (gl * t) + fwd * bulge
        groove = 0.0032 * abs(math.sin(3 * math.pi * t)) if 0.1 < t < 0.6 else 0.0
        ring = []
        for u, v in _rr(d, w, 0.013, 7):
            uu = u - (groove if u > 0 else 0.0)
            ring.append(c + fwd * uu + sd * v)
        rings.append(ring)
    _loft(p, grip_role, rings)
    # the grey head: a rounded block, the front plate down the grip
    head = g0 + lean * (gl + 0.012)
    m = frame(head, fwd, sd, lean)
    p.box(head_role, (-0.026, -0.021, -0.012), (0.024, 0.021, 0.014), bevel=0.009, segments=4, m=m)
    mf = frame(g0 + lean * 0.05 + fwd * 0.022, sd, lean, fwd)
    p.box(head_role, (-0.011, -0.04, -0.003), (0.011, 0.04, 0.003), bevel=0.0025, segments=3, m=mf)
    # on the head: two hats (a cross on a collar), a red button with a collar, on the thumb side a castle button
    for off, kind in ((-0.012, "hat"), (0.01, "hat"), (0.0, "red")):
        c = head + lean * 0.0145 + fwd * off + sd * (0.0 if kind == "hat" else -0.011)
        if kind == "red":
            c = head + lean * 0.0145 + fwd * 0.0 + sd * 0.011
            p.lathe("Kit_Lip", [(0.0062, 0.0), (0.0062, 0.0015), (0.005, 0.002)], c, axis=lean, seg=20)
            p.lathe("Kit_Red", [(0.0048, 0.0), (0.0048, 0.004), (0.004, 0.0052), (0.0, 0.0055)], c, axis=lean, seg=20)
            continue
        p.lathe("Kit_Graphite", [(0.006, 0.0), (0.006, 0.002), (0.0045, 0.0028)], c, axis=lean, seg=20)
        for dv in (fwd, sd):
            p.sweep("Kit_Lip", [c + lean * 0.004 - dv * 0.0045, c + lean * 0.004 + dv * 0.0045], 0.0016, seg=8)
    th = g0 + lean * 0.075 - sd * 0.0215                      # thumb side (inboard: -sd is -y... the pilot side)
    p.lathe("Kit_Lip", [(0.0068, 0.0), (0.0068, 0.0015), (0.0055, 0.002)], th, axis=-sd, seg=20)
    p.lathe("Kit_Graphite", [(0.0054, 0.0), (0.0054, 0.0045), (0.0045, 0.006), (0.0, 0.0062)], th, axis=-sd, seg=20)
    # the trigger: a curved dark blade under the head, in a guard loop
    tr = [g0 + lean * (gl * t) + fwd * (0.032 + 0.008 * math.sin(math.pi * (t - 0.55) / 0.3)) for t in (0.55, 0.62, 0.7, 0.78, 0.85)]
    p.sweep("Kit_Graphite", tr, 0.0062, seg=10, scale_y=0.55)
    # the silver C-guard over the head: two flat bars and a bridge, smooth (36 steps)
    path = []
    if guard == "d":
        # variant B (the concept): a flat brushed bar close along the grip's front, from the head down to the collar,
        # not over the head
        for k in range(13):
            t = k / 12
            bow = 0.012 * math.sin(math.pi * t)
            path.append(head + fwd * (0.03 + bow) + lean * (0.004 - (gl + 0.006) * t))
        p.sweep("Kit_Lip", path, 0.0045, seg=14)
    else:
        for k in range(37):
            a = math.pi * k / 36
            path.append(head + lean * (0.004 + 0.034 * math.sin(a)) + fwd * (-0.036 * math.cos(a) + 0.004))
        path.append(path[-1] - lean * 0.04)
        p.sweep("Kit_Lip", path, 0.0075, seg=12, scale_y=0.6)            # one flat bar, 15 x 9 mm (wires read as a tangle)
    for e in (path[1], path[-1]):                                         # its two pins into the head
        p.lathe("Kit_Graphite", [(0.0045, -0.004), (0.0045, 0.004), (0.0, 0.0045)], tuple(e), axis=tuple(sd), seg=12)
    _label(p, label, base + Vector((-0.062, 0.0, 0.0005)), Z, Vector((0, -1, 0)), X, scale=0.45)


# ------------------------------------------------------------------ the sloped control face, sunk into the deck's nose
def _rocker(p, c, r, a, n, label, label_scale=0.48, index=True, cap="Kit_Shell"):
    """A real rocker: a dark bezel, a cap in two halves tilted about its pivot (one pressed), a lit index, its label."""
    fm = frame(c, r, a, n)
    p.box("Kit_Graphite", (-0.0095, -0.016, -0.002), (0.0095, 0.016, 0.004), bevel=0.0018, segments=2, m=fm)
    for sv, tilt in ((1, 9.0), (-1, -9.0)):
        t = math.radians(tilt)
        a2 = a * math.cos(t) + n * math.sin(t)
        n2 = -a * math.sin(t) + n * math.cos(t)
        p.box(cap, (-0.0075, 0.0 if sv > 0 else -0.012, -0.002), (0.0075, 0.012 if sv > 0 else 0.0, 0.003), bevel=0.0012, segments=2,
              m=frame(c + n * 0.005, r, a2, n2))
    if index:
        p.box("Kit_GlowCool", (-0.004, 0.0085, 0.0066), (0.004, 0.0098, 0.0072), m=fm, panel=False)
    if label_scale > 0:
        _label(p, label, c - a * 0.026 + n * 0.0005, n, r, a, scale=label_scale)


def control_face(p, x0, x1, u0, u1, z0):
    """The deck's nose rises into a sloped face towards the pilot (one mass with the console, SC's): a dark framed
    field with the red key under its hinged cover and its label, three rockers, LED bars, screws."""
    zt = z0 + 0.1
    prof = [(x0, z0), (x1, z0), (x1, zt), (x1 - 0.05, zt), (x0, z0 + 0.012)]
    p.poly_prism("Kit_Console", prof, frame(Vector((0, u0, 0)), (1, 0, 0), (0, 0, 1), (0, -1, 0)), u1 - u0, bevel=0.01, segments=3)
    ang = math.atan2(zt - z0 - 0.012, x1 - 0.05 - x0)
    a = Vector((math.cos(ang), 0, math.sin(ang)))
    n = Vector((-math.sin(ang), 0, math.cos(ang)))
    r = Vector((0, -1, 0))
    c = Vector(((x0 + x1 - 0.05) / 2, (u0 + u1) / 2, (z0 + 0.012 + zt) / 2))
    w, h = (u1 - u0) - 0.04, (x1 - 0.05 - x0) / math.cos(ang) - 0.03
    fm = lambda o: frame(o, r, a, n)                        # noqa: E731
    # the dark field sunk 4 mm in a satin lip
    p.box("Kit_Lip", (-w / 2 - 0.004, -h / 2 - 0.004, -0.004), (w / 2 + 0.004, h / 2 + 0.004, 0.0006), bevel=0.002, segments=2, m=fm(c))
    p.box("Kit_Housing", (-w / 2, -h / 2, -0.004), (w / 2, h / 2, 0.0009), bevel=0.0, m=fm(c), panel=False)
    # the red key and its cover (open 60 deg), the label on an orange plate beside it
    kc = c + a * (h * 0.2) + r * (-w * 0.12)
    p.box("Kit_Graphite", (-0.03, -0.021, 0.0), (0.03, 0.021, 0.007), bevel=0.003, segments=2, m=fm(kc))
    p.box("Kit_Red", (-0.022, -0.014, 0.005), (0.022, 0.014, 0.011), bevel=0.0025, segments=3, m=fm(kc))
    p.box("Kit_GlowRed", (-0.013, -0.002, 0.0108), (0.013, 0.002, 0.0114), m=fm(kc), panel=False)
    hinge = kc + a * 0.023 + n * 0.01
    p.sweep("Kit_Lip", [hinge - r * 0.033, hinge + r * 0.033], 0.0045, seg=12)
    for sv in (-1, 1):                                                    # the hinge's two knuckles on the frame
        p.box("Kit_Graphite", (-0.004, -0.006, -0.01), (0.004, 0.004, 0.0), m=fm(hinge + r * (sv * 0.027)), bevel=0.0012, segments=2)
    t = math.radians(60)
    a2, n2 = a * math.cos(t) + n * math.sin(t), -a * math.sin(t) + n * math.cos(t)
    mc = frame(hinge, r, a2, n2)
    p.box("Kit_Red", (-0.03, 0.0, -0.0015), (0.03, 0.043, 0.0015), bevel=0.0012, segments=2, m=mc)
    for sv in (-1, 1):                                                    # the cover's side walls (a lid, not a sheet)
        p.box("Kit_Red", (sv * 0.03 - 0.0015, 0.0, -0.0095), (sv * 0.03 + 0.0015, 0.043, 0.0), bevel=0.0007, segments=1, m=mc)
    p.box("Kit_Red", (-0.03, 0.0405, -0.0095), (0.03, 0.043, 0.0), bevel=0.0007, segments=1, m=mc)
    lp = kc + r * 0.062
    p.box("Kit_Signal", (-0.026, -0.01, 0.0009), (0.026, 0.01, 0.0018), m=fm(lp), panel=False)
    _label(p, "ck_emerg_o2", lp + n * 0.0019, n, r, a, scale=0.48)
    p.box("Kit_Signal", (-0.034, -0.025, 0.0), (0.034, 0.025, 0.0016), m=fm(kc), panel=False)          # the orange frame
    for i, lab in enumerate(("ck_pwr", "ck_extlt", "ck_eng")):
        _rocker(p, c - a * (h * 0.2) + r * (-w * 0.3 + w * 0.3 * i) + n * 0.0009, r, a, n, lab)
    for su in (-1, 1):
        for sv in (-1, 1):
            q = c + r * (su * (w / 2 + 0.012)) + a * (sv * (h / 2 + 0.006))
            p.lathe("Kit_Lip", [(0.003, 0.0), (0.003, 0.0006), (0.0, 0.0009)], q, axis=n, seg=12)
    lc = c + r * (w / 2 - 0.014) + a * (h * 0.22)
    for k in range(5):
        p.box("Kit_GlowCool" if k < 3 else "Kit_GlowSignal" if k == 3 else "Kit_Graphite",
              (-0.004, -0.014 + 0.006 * k, 0.0009), (0.004, -0.011 + 0.006 * k, 0.0021), m=fm(lc), panel=False)


# ------------------------------------------------------------------ a framed deck module
def module(p, x0, x1, u0, u1, z):
    """A raised mid-grey plate (6 mm edge) in a dark gap, four screws: the unit the deck is built of (SC's consoles are
    rows of such modules, not one board). Returns its top height."""
    p.box("Kit_Graphite", (x0 - 0.006, u0 - 0.006, z - 0.006), (x1 + 0.006, u1 + 0.006, z + 0.0005), panel=False)
    p.box("Kit_Console", (x0, u0, z - 0.012), (x1, u1, z + 0.008), bevel=0.006, segments=3)
    i0, i1, j0, j1 = x0 + 0.022, x1 - 0.022, u0 + 0.022, u1 - 0.022
    for a_, b_ in (((i0, j0), (i1, j0 + 0.0015)), ((i0, j1 - 0.0015), (i1, j1)), ((i0, j0), (i0 + 0.0015, j1)), ((i1 - 0.0015, j0), (i1, j1))):
        p.box("Kit_Graphite", (a_[0], a_[1], z + 0.0078), (b_[0], b_[1], z + 0.0086), panel=False)
    p.grime("rim", ((x0 + x1) / 2, u0 + 0.004, z + 0.0081), (0, 0, 1), (0, -1, 0), (x1 - x0 - 0.02, 0.012), 0.6, wear=True)
    for xx in (x0 + 0.012, x1 - 0.012):
        for uu in (u0 + 0.012, u1 - 0.012):
            p.lathe("Kit_Lip", [(0.0032, 0.0), (0.0032, 0.0006), (0.0, 0.0009)], (xx, uu, z + 0.008), seg=12)
    return z + 0.008


# ------------------------------------------------------------------ the console
def console(name, seed):
    """KF-COCKPIT-CONSOLE v4 (critic in the cockpit, 4.8: "a flat counter with a stick on top"): the deck lowered to
    0.54 m and built of framed modules; the light arm unit held 3 cm over it on two brackets (a visible gap and shadow
    under it, SC's arm on its consoles), its top at elbow height 0.61 m; a perforated wrist rest; legends 2-3x larger;
    Halcyon orange on the stick's hatch ring and round the red key."""
    p = kit_geo.Part(name, seed)
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    DT = TOP - 0.08                                          # the deck's top
    D = DT - 0.032                                           # its underside
    # 1 the pedestal: a trapezoid section (inner face sloping back to u 0.08 at the floor), gunmetal, 18 mm edges
    sec = [(0.08, 0.0), (W, 0.0), (W, D), (0.0, D), (0.0, D - 0.12), (0.08, 0.1)]
    p.poly_prism("Kit_Console", sec, frame(Vector((L, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0)), L, bevel=0.018, segments=3)
    for xr in (0.06, 0.37, 0.68, 0.99, L - 0.06):
        rib = [(0.07, 0.03), (0.095, 0.03), (0.02, D - 0.13), (-0.005, D - 0.13)]
        p.poly_prism("Kit_Housing", rib, frame(Vector((xr + 0.02, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0)), 0.04, bevel=0.006, segments=2)
    for xa, xb in ((0.1, 0.35), (0.41, 0.66), (0.72, 0.97)):
        fld = [(0.072, 0.06), (0.09, 0.06), (0.025, D - 0.15), (0.007, D - 0.15)]
        p.poly_prism("Kit_Graphite", fld, frame(Vector((xb, 0, 0)), (0, 1, 0), (0, 0, 1), (1, 0, 0)), xb - xa, bevel=0.0, segments=1)
    p.box("Kit_Gasket", (0.0, 0.07, 0.0), (L, 0.1, 0.035), bevel=0.004, segments=2)
    for k in range(9):
        zk = 0.14 + k * 0.022
        uk = 0.08 - 0.08 * (zk - 0.1) / (D - 0.22) * 0.85
        p.box("Kit_Panel", (0.43, uk - 0.004, zk), (0.64, uk + 0.002, zk + 0.01), bevel=0.0015, segments=1, panel=False)
    _label(p, "st_vent", Vector((0.535, 0.03, D - 0.17)), Vector((0, -1, 0.4)).normalized(), X,
           Vector((0, 0.4, 1)).normalized(), scale=0.6)
    # 2 the deck: a dark base board, the modules on it
    p.box("Kit_Housing", (-0.004, 0.0, D), (L - 0.16, W + 0.004, DT - 0.006), bevel=0.01, segments=4)
    zm = module(p, 0.22, 0.47, 0.24, W - 0.04, DT - 0.006)              # A: the louvre
    p.box("Kit_Lip", (0.235, 0.255, zm), (0.455, W - 0.055, zm + 0.004), bevel=0.0015, segments=2)
    p.box("Kit_Graphite", (0.242, 0.262, zm + 0.004), (0.448, W - 0.062, zm + 0.0045), panel=False)
    for k in range(12):
        xk = 0.247 + k * 0.0168
        p.box("Kit_Housing", (xk, 0.266, zm + 0.0045), (xk + 0.009, W - 0.066, zm + 0.011), bevel=0.0025, segments=2, panel=False)
    zm = module(p, 0.49, 0.75, 0.24, W - 0.04, DT - 0.006)              # B: the status strip and its legends
    p.box("Kit_Lip", (0.505, 0.3, zm - 0.002), (0.735, 0.4, zm + 0.003), bevel=0.002, segments=2)
    p.box("Kit_Graphite", (0.51, 0.305, zm), (0.73, 0.395, zm + 0.0034), panel=False)
    for k, lab in enumerate(("ck_main", "ck_batt", "ck_temp")):
        xk = 0.545 + 0.075 * k
        p.box("Kit_GlowCool" if k < 2 else "Kit_GlowSignal", (xk - 0.022, 0.358, zm + 0.0034), (xk + 0.022, 0.372, zm + 0.0037), panel=False)
        _label(p, lab, Vector((xk, 0.33, zm + 0.0035)), Z, Vector((0, -1, 0)), X, scale=0.75)
    _label(p, "panel_C21", Vector((0.62, 0.52, zm + 0.0004)), Z, Vector((0, -1, 0)), X, scale=0.6)
    zm = module(p, 0.77, 0.98, 0.24, W - 0.04, DT - 0.006)              # C: a 2 x 2 key pad
    for i, lab in enumerate(("ck_lights", "ck_gear", "ck_vtol", "ck_esp")):
        kx = Vector((0.83 + 0.09 * (i % 2), 0.33 + 0.12 * (i // 2), zm))
        p.box("Kit_Graphite", kx + Vector((-0.016, -0.016, -0.001)), kx + Vector((0.016, 0.016, 0.004)), bevel=0.002, segments=2)
        p.box("Kit_Shell", kx + Vector((-0.012, -0.012, 0.003)), kx + Vector((0.012, 0.012, 0.009)), bevel=0.002, segments=2)
        p.box("Kit_GlowCool", kx + Vector((-0.007, 0.007, 0.0088)), kx + Vector((0.007, 0.0085, 0.0092)), panel=False)
        _label(p, lab, kx + Vector((0.0, -0.042, 0.0005)), Z, Vector((0, -1, 0)), X, scale=0.62)
    _label(p, "st_torque", Vector((0.6, 0.6, zm - 0.008 + 0.0004)), Z, Vector((0, -1, 0)), X, scale=0.5)
    # 3 the nose: the control face rising from the deck, one mass with it
    control_face(p, L - 0.2, L, 0.0, W, D)
    # 4 the arm unit: slim, cantilevered over the gap, held 3 cm over the deck on two brackets (the gap and its shadow
    # make it read as SC's arm), light grey under a clear coat, two steps, its top at elbow height
    AT = TOP + 0.01
    for xb in (0.3, 0.84):
        p.box("Kit_Housing", (xb - 0.04, 0.0, DT - 0.01), (xb + 0.04, 0.17, AT - 0.04), bevel=0.006, segments=2)
        for uu in (0.03, 0.14):
            p.lathe("Kit_Lip", [(0.004, 0.0), (0.004, 0.001), (0.0, 0.0013)], (xb + 0.041, uu, (DT + AT - 0.05) / 2), axis=(1, 0, 0), seg=12)
    def plan(x0, x1, u0, u1, c):                                      # the arm's plan, ends chamfered c at the pilot's side
        return [(x0 + c, u0), (x1 - c, u0), (x1, u0 + c), (x1, u1), (x0, u1), (x0, u0 + c)]
    p.poly_prism("Kit_Shell", plan(0.16, 0.98, -0.075, 0.19, 0.06), frame(Vector((0, 0, AT - 0.016)), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                 0.029, bevel=0.012, segments=4)
    p.poly_prism("Kit_Shell", plan(0.18, 0.96, -0.065, 0.178, 0.05), frame(Vector((0, 0, AT)), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                 0.02, bevel=0.01, segments=4)
    p.poly_prism("Kit_Graphite", plan(0.17, 0.97, -0.07, 0.185, 0.055), frame(Vector((0, 0, AT - 0.0165)), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
                 0.003, bevel=0.0, segments=1, panel=False)
    for x_ in (0.22, 0.92):
        for u_ in (-0.045, 0.155):
            p.lathe("Kit_Lip", [(0.0034, 0.0), (0.0034, 0.0006), (0.0, 0.0009)], (x_, u_, AT), seg=12)
    # panel seams on the arm's top: it is two covers and a rear strip, not one slab
    for x_ in (0.45, 0.73):
        p.box("Kit_Graphite", (x_ - 0.0015, -0.064, AT - 0.0005), (x_ + 0.0015, 0.177, AT + 0.0004), panel=False)
    p.box("Kit_Graphite", (0.181, 0.118, AT - 0.0005), (0.959, 0.121, AT + 0.0004), panel=False)
    for x_ in (0.3, 0.6, 0.88):
        p.lathe("Kit_Lip", [(0.003, 0.0), (0.003, 0.0006), (0.0, 0.0008)], (x_, 0.15, AT), seg=12)
    sx, su = 0.8, -0.02
    # the wrist rest: a padded cushion with a satin welt, rows of perforation holes
    p.box("Kit_Cushion", (0.47, su - 0.042, AT), (0.71, su + 0.042, AT + 0.03), bevel=0.013, segments=4)
    for i in range(18):
        for j in range(5):
            hx, hu = 0.49 + 0.0118 * i, su - 0.024 + 0.012 * j + (0.006 if i % 2 else 0.0)
            if abs(hu - su) > 0.029:
                continue
            p.box("Kit_Graphite", (hx - 0.0018, hu - 0.0018, AT + 0.0295), (hx + 0.0018, hu + 0.0018, AT + 0.0306), panel=False)
    stick(p, Vector((sx, su, AT)), "ck_rcs")
    _label(p, "hazard_subtle", Vector((0.9, 0.08, AT + 0.0004)), Z, Vector((0, -1, 0)), X, scale=0.35)
    _label(p, "maker", Vector((0.62, -0.0005, D - 0.06)), Vector((0, -1, 0)), X, Z, scale=0.5)
    # 5 the grab handle at the front outboard corner
    hp = [Vector((L - 0.06, W - 0.03, DT + 0.03)), Vector((L + 0.05, W - 0.03, DT + 0.03)), Vector((L + 0.07, W - 0.08, DT + 0.03)),
          Vector((L + 0.07, W - 0.2, DT + 0.03)), Vector((L + 0.05, W - 0.22, DT + 0.03)), Vector((L - 0.03, W - 0.22, DT + 0.03))]
    p.sweep("Kit_Panel", hp, 0.018, seg=12, scale_y=0.5)
    p.sweep("Kit_Signal", hp[1:5], 0.0185, seg=12, scale_y=0.12)          # the orange grip band
    # 6 dirt: the kick, the module gaps, under the arm, polish on the arm's inner edge
    p.grime("rim", (L / 2, 0.075, 0.04), (0, -1, 0), (0, 0, 1), (L - 0.1, 0.05), 0.8)
    p.grime("rim", (0.6, W - 0.03, DT), (0, 0, 1), (0, -1, 0), (0.75, 0.03), 0.6)
    p.grime("rim", (0.35, -0.05, AT + 0.001), (0, 0, 1), (0, -1, 0), (0.2, 0.025), 0.7, wear=True)
    p.collision_box((0.0, -0.075, 0.0), (L, W, TOP + 0.04))
    return p
