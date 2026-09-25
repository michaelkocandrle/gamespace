"""The Wayfarer's front cockpit from the approved concept A (ArtSource/Ships/Wayfarer/Concept/Cockpit/
cockpit_target_space.png / _day.png, author 25. 9. 2026): two large tilted MFD pods with rounded satin
bezels left and right, a central pedestal with a holographic radar and the two small centre screens, button
banks under the pods, a low sculpted graphite cowl instead of a dashboard wall and a glare shield.

Called by hs_interior.dashboard() when recipe interior.cockpit.style == "pods". Screens keep the game's
canvas (USpaceCockpitDisplays: left / right 560x490, centre_top 210x259, centre_bottom 210x231), so every
screen quad has its canvas rectangle's aspect ratio and a Display_<name> socket in front of it
(test_cockpit_displays.py). Placement rule (test_cockpit_frame.py): every screen whole in the level view
under the HUD - top edge >= 8 deg (the HUD ends ~5 deg under the eye), bottom edge <= 28 deg under the eye, the nearest screen >= 0.9 m ahead.

Materials: int_console (warm graphite), int_trim (satin metal rims), int_glow (cool edge light, hologram),
accent (Halcyon orange caps and pinstripes), int_red, int_dark.
"""
import math

import bmesh
from mathutils import Vector

RECTS = {"left": (0, 0, 560, 490), "right": (560, 0, 1120, 490),
         "centre_top": (1120, 0, 1330, 259), "centre_bottom": (1120, 259, 1330, 490)}
CANVAS = (1330.0, 490.0)


# ------------------------------------------------------------------------------------------ helpers

def rr_outline(w, h, r, seg=6):
    """A rounded rectangle, centred, counter-clockwise, 4 * (seg + 1) points."""
    r = min(r, w / 2 - 1e-4, h / 2 - 1e-4)
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _frame(c, right, up):
    return lambda u, v, d=0.0, n=None: c + right * u + up * v + (n * d if n is not None else Vector())


def rr_slab(bm, c, right, up, n, w, h, r, depth, seg=6, shape=None):
    """A filled rounded plate, front face at c facing n, depth behind it. shape: (u, v) -> (u, v) warp."""
    out = rr_outline(w, h, r, seg)
    if shape:
        out = [shape(u, v) for u, v in out]
    f = [bm.verts.new(c + right * u + up * v) for u, v in out]
    b = [bm.verts.new(c + right * u + up * v - n * depth) for u, v in out]
    bm.faces.new(f)
    bm.faces.new(b[::-1])
    m = len(out)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((b[i], b[j], f[j], f[i]))


def rr_ring(bm, c, right, up, n, w, h, r, rim, depth, seg=6, shape=None):
    """A rounded-rectangle frame (bezel), front at c facing n. shape: (u, v) -> (u, v) warp of both outlines."""
    out = rr_outline(w, h, r, seg)
    inn = rr_outline(w - 2 * rim, h - 2 * rim, max(r - rim, 0.004), seg)
    if shape:
        out = [shape(u, v) for u, v in out]
        inn = [shape(u, v) for u, v in inn]
    fo = [bm.verts.new(c + right * u + up * v) for u, v in out]
    fi = [bm.verts.new(c + right * u + up * v) for u, v in inn]
    bo = [bm.verts.new(c + right * u + up * v - n * depth) for u, v in out]
    bi = [bm.verts.new(c + right * u + up * v - n * depth) for u, v in inn]
    m = len(out)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((fi[i], fo[i], fo[j], fi[j]))       # front
        bm.faces.new((bo[i], bo[j], fo[j], fo[i]))       # outer wall
        bm.faces.new((fi[i], fi[j], bi[j], bi[i]))       # inner wall
        bm.faces.new((bi[i], bi[j], bo[j], bo[i]))       # back


def tube(bm, a, b, r, seg=8):
    a, b = Vector(a), Vector(b)
    d = b - a
    if d.length < 1e-5:
        return
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def oriented(eye, c):
    """Right / up / normal of a panel at c that faces the eye (pilot looks along +x, right = -y)."""
    n = (Vector(eye) - Vector(c)).normalized()
    right = Vector((0, 0, 1)).cross(n).normalized()
    up = n.cross(right).normalized()
    return right, up, n


def screen(screen_bm, sockets, name, c, right, up, n, w, h):
    uvl = screen_bm.loops.layers.uv.get("UVMap") or screen_bm.loops.layers.uv.new("UVMap")
    cs = [c + right * (-w / 2) + up * (-h / 2), c + right * (w / 2) + up * (-h / 2),
          c + right * (w / 2) + up * (h / 2), c + right * (-w / 2) + up * (h / 2)]
    vs = [screen_bm.verts.new(p) for p in cs]
    f = screen_bm.faces.new(vs)
    rx0, ry0, rx1, ry1 = RECTS[name]
    W, H = CANVAS
    for loop, uv in zip(f.loops, [(rx0 / W, 1 - ry1 / H), (rx1 / W, 1 - ry1 / H), (rx1 / W, 1 - ry0 / H), (rx0 / W, 1 - ry0 / H)]):
        loop[uvl].uv = uv
    f.normal_update()
    if f.normal.dot(n) < 0:
        f.normal_flip()
    sockets[name] = c + n * 0.03


def loft(bm, rings):
    """Skin a list of closed rings (lists of Vectors, same length) and cap both ends."""
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    m = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(vs[0][::-1])
    bm.faces.new(vs[-1])


# ------------------------------------------------------------------------------------------ parts

def pod(g, screen_bm, sockets, eye, name, c, spec):
    """An MFD pod: graphite shell, satin bezel ring with a cool edge light, the screen, a stalk and a button
    bank under it."""
    right, up, n = oriented(eye, c)
    sw, sh = spec["screen_w"], spec["screen_w"] * 490.0 / 560.0
    side = 1 if c.y > 0 else -1               # +1 left pod (+y), -1 right pod
    out = right * (-side)                      # towards the cockpit wall
    pw, ph = sw + 2 * spec["side_margin"], sh + 2 * spec["top_margin"]
    pc = c + out * spec["outer_bias"]          # the pod is wider on its outer side (concept A)
    so = -side                                  # the outer side in the pod's own u axis (right = pilot's right)
    bulge = spec.get("pod_bulge", 0.06)

    def shape(u, v):
        # concept A: the pod's lower outer corner droops down and out, the inner side stays compact
        k = max(0.0, u * so / (pw / 2 + 0.02))
        return (u + so * 0.02 * k * k * (v < 0), v - bulge * k * k if v < 0 else v)
    rr_slab(g["int_console"], pc - n * 0.006, right, up, n, pw, ph, spec["radius"], 0.09, shape=shape)
    rr_ring(g["int_trim"], pc + n * 0.012, right, up, n, pw + 0.012, ph + 0.012, spec["radius"] + 0.006, 0.026, 0.024, shape=shape)
    rr_ring(g["int_glow"], pc + n * 0.0135, right, up, n, pw - 0.018, ph - 0.018, spec["radius"] - 0.009, 0.004, 0.003, shape=shape)
    # a dark inner mask around the glass (the screen sits in a recess, as a real display does)
    rr_ring(g["int_dark"], c + n * 0.004, right, up, n, sw + 0.03, sh + 0.03, 0.02, 0.016, 0.006)
    screen(screen_bm, sockets, name, c + n * 0.002, right, up, n, sw, sh)
    # the outer strip of the pod: two small status lights and a knob (concept: side info strip)
    s0 = c + out * (sw / 2 + spec["side_margin"] * 0.55 + spec["outer_bias"])
    for k, key in enumerate(("int_glow", "accent")):
        p = s0 + up * (0.07 - k * 0.05) + n * 0.004
        rr_slab(g[key], p, right, up, n, 0.018, 0.018, 0.009, 0.004, 3)
    tube(g["int_trim"], s0 - up * 0.07, s0 - up * 0.07 + n * 0.022, 0.016, 16)
    # stalk from the pod's back down into the cowl
    # (its top stays behind the pod's back shell, which ends 0.096 m behind the screen plane)
    top = pc - n * 0.13 - up * 0.04
    base = Vector((top.x + 0.05, top.y, spec["cowl_z"] - 0.02))
    d = top - base
    res = bmesh.ops.create_cube(g["int_console"], size=1.0)
    bmesh.ops.scale(g["int_console"], vec=(0.1, 0.16, d.length), verts=res["verts"])
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (base + top) / 2
    bmesh.ops.transform(g["int_console"], matrix=m, verts=res["verts"])
    # button bank under the pod: dark plate in a satin rim, rocker switches with orange caps, a knob, a red
    # guarded button, status LEDs
    bc = c - up * (sh / 2 + spec["top_margin"] + 0.062) + n * 0.03 - out * 0.03
    br, bu, bn = oriented(eye, bc)
    bw, bh = 0.30, 0.085
    rr_slab(g["int_console"], bc - bn * 0.004, br, bu, bn, bw + 0.02, bh + 0.02, 0.03, 0.05)
    rr_ring(g["int_trim"], bc + bn * 0.004, br, bu, bn, bw + 0.02, bh + 0.02, 0.03, 0.01, 0.008)
    rr_slab(g["int_dark"], bc + bn * 0.002, br, bu, bn, bw, bh, 0.022, 0.004)
    for k in range(4):
        p = bc + br * (-0.11 + k * 0.034) * side + bn * 0.004
        rr_slab(g["int_console"], p + bn * 0.006, br, bu, bn, 0.022, 0.045, 0.004, 0.008, 2)
        rr_slab(g["accent"], p + bn * 0.016 + bu * 0.008, br, bu, bn, 0.018, 0.02, 0.003, 0.008, 2)
    for k in range(2):
        p = bc + br * (0.035 + k * 0.035) * side + bu * 0.012 + bn * 0.004
        tube(g["int_trim"], p, p + bn * 0.016, 0.009, 12)
    p = bc + br * 0.11 * side + bu * 0.01 + bn * 0.004
    tube(g["int_red"], p, p + bn * 0.012, 0.011, 14)
    for k in range(3):
        p = bc + br * (0.02 + k * 0.03) * side - bu * 0.028 + bn * 0.004
        rr_slab(g["int_glow"], p, br, bu, bn, 0.012, 0.005, 0.002, 0.002, 2)


def pedestal(g, screen_bm, sockets, eye, spec):
    """The central column: rises out of the cowl, narrows, flares into the head that carries the two centre
    screens on its sloped face and the holographic radar emitter on top."""
    x0, zc, ztop = spec["ped_x"], spec["cowl_z"], spec["ped_top"]
    rings = []
    prof = [(0.0, 0.30, 0.26), (0.18, 0.18, 0.2), (0.38, 0.13, 0.16), (0.6, 0.16, 0.16), (0.8, 0.27, 0.19), (1.0, 0.29, 0.2)]
    for t, w, dpt in prof:
        z = zc - 0.06 + (ztop - zc + 0.06) * t
        cx = x0 + 0.1 * (1 - t) - 0.02 * t
        rings.append([Vector((cx + dpt / 2 * u, w / 2 * v, z)) for v, u in rr_outline(2.0, 2.0, 0.7, 4)])
    loft(g["int_console"], rings)
    # orange pinstripes up both front edges (the concept's accent lines)
    for s in (1, -1):
        pts = []
        for t, w, dpt in prof:
            z = zc - 0.06 + (ztop - zc + 0.06) * t
            cx = x0 + 0.1 * (1 - t) - 0.02 * t
            pts.append(Vector((cx - dpt / 2 * 0.72 - 0.003, s * w / 2 * 0.72, z)))
        for a, b in zip(pts, pts[1:]):
            tube(g["accent"], a, b, 0.0035, 6)
    # the head's sloped face with the centre screens side by side
    hc = Vector((x0 - 0.1, 0.0, ztop - 0.075))
    hr, hu, hn = oriented(eye, hc)
    rr_slab(g["int_console"], hc - hn * 0.01, hr, hu, hn, 0.27, 0.16, 0.04, 0.06)
    rr_ring(g["int_trim"], hc + hn * 0.004, hr, hu, hn, 0.27, 0.16, 0.04, 0.012, 0.01)
    for name, du, h in (("centre_top", -0.055, spec["centre_w"] * 259.0 / 210.0), ("centre_bottom", 0.055, spec["centre_w"] * 231.0 / 210.0)):
        c = hc + hr * du + hn * 0.006
        rr_ring(g["int_dark"], c, hr, hu, hn, spec["centre_w"] + 0.016, h + 0.016, 0.01, 0.009, 0.004)
        screen(screen_bm, sockets, name, c - hn * 0.001, hr, hu, hn, spec["centre_w"], h)
    # holographic radar: emitter ring and glowing lens on top, three light rings and four ticks over it
    e = Vector((x0 - 0.02, 0.0, ztop))
    tube(g["int_trim"], e, e + Vector((0, 0, 0.022)), 0.075, 32)
    tube(g["int_glow"], e + Vector((0, 0, 0.022)), e + Vector((0, 0, 0.026)), 0.055, 32)
    up = Vector((0, 0, 1))
    for dz, R in ((0.05, 0.085), (0.08, 0.07), (0.10, 0.042)):
        rr_ring(g["int_glow"], e + up * dz, Vector((0, -1, 0)), Vector((1, 0, 0)), up, 2 * R, 2 * R, R - 1e-4, 0.0045, 0.003, 8)
    for a in range(4):
        d = Vector((math.cos(a * math.pi / 2 + 0.4), math.sin(a * math.pi / 2 + 0.4), 0))
        tube(g["int_glow"], e + up * 0.045 + d * 0.08, e + up * 0.09 + d * 0.06, 0.0022, 5)


def cowl(g, spec, zfloor):
    """The low graphite cowl in place of a dashboard wall: a slab across the nose, arched, with a rounded rear
    lip carrying an orange pinstripe, open knee wells under the pods."""
    xa, xb = spec["cowl_x"]
    zc = spec["cowl_z"]
    yw = spec["cowl_half_width"]
    bm = g["int_console"]
    nu, nv = 14, 6
    top, bot = [], []
    for i in range(nv + 1):
        x = xa + (xb - xa) * i / nv
        rowt, rowb = [], []
        for j in range(nu + 1):
            y = -yw + 2 * yw * j / nu
            z = zc + 0.05 * (i / nv) + 0.035 * (1 - (y / yw) ** 2)
            rowt.append(bm.verts.new((x, y, z)))
            rowb.append(bm.verts.new((x, y, z - 0.07)))
        top.append(rowt)
        bot.append(rowb)
    for i in range(nv):
        for j in range(nu):
            bm.faces.new((top[i][j], top[i][j + 1], top[i + 1][j + 1], top[i + 1][j]))
            bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1]))
    for i in range(nv):
        for j in (0, nu):
            a, b = (top[i][j], top[i + 1][j]) if j == nu else (top[i + 1][j], top[i][j])
            c, d = (bot[i + 1][j], bot[i][j]) if j == nu else (bot[i][j], bot[i + 1][j])
            bm.faces.new((a, b, c, d))
    for j in range(nu):
        bm.faces.new((top[0][j + 1], top[0][j], bot[0][j], bot[0][j + 1]))              # rear lip face
        bm.faces.new((top[nv][j], top[nv][j + 1], bot[nv][j + 1], bot[nv][j]))          # front
    # rear lip: a rounded satin edge and the pinstripe just under it
    for j in range(nu):
        a, b = top[0][j].co.copy(), top[0][j + 1].co.copy()
        tube(g["int_trim"], a + Vector((-0.004, 0, -0.004)), b + Vector((-0.004, 0, -0.004)), 0.012, 10)
        tube(g["accent"], a + Vector((-0.012, 0, -0.03)), b + Vector((-0.012, 0, -0.03)), 0.0035, 6)


def build(g, screen_bm, sockets, eye, spec, zfloor):
    eye = Vector(eye)
    cowl(g, spec, zfloor)
    for name, y in (("left", spec["pod_y"]), ("right", -spec["pod_y"])):
        pod(g, screen_bm, sockets, eye, name, Vector((spec["pod_x"], y, spec["pod_z"])), spec)
    pedestal(g, screen_bm, sockets, eye, spec)


# ------------------------------------------------------------------------------------------ wrap-around dash

def _pod_frame(eye, spec, side):
    c = Vector((spec["pod_x"], side * spec["pod_y"], spec["pod_z"]))
    right, up, n = oriented(eye, c)
    return c, right, up, n


def _quad_faces(bm, quads, eye):
    """Add quads (4 Vectors each) facing the eye; returns the faces."""
    out = []
    for q in quads:
        f = bm.faces.new([bm.verts.new(p) for p in q])
        f.normal_update()
        if f.normal.dot(Vector(eye) - f.calc_center_median()) < 0:
            f.normal_flip()
        out.append(f)
    return out


def dash(g, screen_bm, sockets, eye, spec, zfloor):
    """One sculpted dashboard wrapping around the pilot: from the side consoles it sweeps forward, carries the
    two MFDs sunk into its face, dips in the middle (the forward-down view stays open, the holographic radar
    stands there) and has a glare-shield top. The screens sit in recesses with a satin bezel; the panel
    around them carries status lights, a knob and a row of keys (author 25. 9. 2026: no tablets on a table)."""
    import bpy
    eye = Vector(eye)
    tmp = bmesh.new()
    tilt = math.tan(math.radians(spec.get("fascia_tilt_deg", 22.0)))
    zb = spec.get("fascia_bottom_z", 0.97)
    below = spec.get("pod_below_m", 0.1)          # panel face below the screen for the key row

    def column(bx, by, z0, z1):
        b = Vector((bx, by, z0))
        f = Vector((bx - eye.x, by - eye.y, 0)).normalized()
        return b, Vector((bx, by, z1)) + f * tilt * (z1 - z0)

    cols = []
    for side in (1, -1):
        c, right, up, n = _pod_frame(eye, spec, side)
        sw = spec["screen_w"]
        sh = sw * 490.0 / 560.0
        pw = sw + 2 * spec["side_margin"]
        # screen in its recess, a satin bezel and a thin cool light line round the glass
        rr_ring(g["int_dark"], c, right, up, n, sw + 0.03, sh + 0.03, 0.018, 0.015, 0.035)
        rr_ring(g["int_trim"], c + n * 0.006, right, up, n, sw + 0.05, sh + 0.05, 0.03, 0.014, 0.012)
        rr_ring(g["int_glow"], c + n * 0.0065, right, up, n, sw + 0.022, sh + 0.022, 0.016, 0.003, 0.003)
        screen(screen_bm, sockets, "left" if side > 0 else "right", c - n * 0.02, right, up, n, sw, sh)
        hw, hh = (sw + 0.05) / 2, (sh + 0.05) / 2
        P = lambda u, v, c=c, right=right, up=up: c + right * u + up * v
        uo, ui = (pw / 2) * (-side), (pw / 2) * side
        vt, vb = sh / 2 + spec["top_margin"], -(sh / 2 + spec["top_margin"] + below)
        u_lo, u_hi = sorted((uo, ui))
        quads = [
            [P(u_lo, vb), P(u_hi, vb), P(u_hi, -hh), P(u_lo, -hh)],      # under the screen (key row)
            [P(u_lo, hh), P(u_hi, hh), P(u_hi, vt), P(u_lo, vt)],        # over it
            [P(u_lo, -hh), P(-hw, -hh), P(-hw, hh), P(u_lo, hh)],        # left strip
            [P(hw, -hh), P(u_hi, -hh), P(u_hi, hh), P(hw, hh)],          # right strip
        ]
        _quad_faces(tmp, quads, eye)
        cols.append((side, "pod_outer", P(uo, vb), P(uo, vt)))
        cols.append((side, "pod_inner", P(ui, vb), P(ui, vt)))
        # the outer strip: status lights and a knob; the key row under the screen
        s0 = c + right * ((hw + (pw / 2 - hw) / 2) * (-side)) + n * 0.004
        for k, key in enumerate(("int_glow", "accent", "int_glow")):
            rr_slab(g[key], s0 + up * (0.09 - k * 0.045), right, up, n, 0.016, 0.016, 0.008, 0.004, 3)
        tube(g["int_trim"], s0 - up * 0.07, s0 - up * 0.07 + n * 0.022, 0.017, 18)
        tube(g["accent"], s0 - up * 0.07 + n * 0.022, s0 - up * 0.07 + n * 0.026, 0.006, 12)
        kc = c - up * (hh + below * 0.5) + n * 0.004
        for k in range(7):
            p = kc + right * (-0.15 + k * 0.05)
            rr_slab(g["int_dark"], p + n * 0.002, right, up, n, 0.036, 0.03, 0.005, 0.004, 2)
            rr_slab(g["accent" if k in (1, 4) else "int_trim"], p + n * 0.008, right, up, n, 0.028, 0.022, 0.004, 0.006, 2)
            if k % 2 == 0:
                rr_slab(g["int_glow"], p + n * 0.009 + up * 0.02, right, up, n, 0.012, 0.004, 0.0015, 0.002, 2)
    L = {k: (b, t) for s, k, b, t in cols if s > 0}
    R = {k: (b, t) for s, k, b, t in cols if s < 0}
    wing = [tuple(w) for w in spec.get("wing", [(17.3, 1.13, 1.06), (17.62, 0.98, 1.22)])]   # (x, |y|, top z)
    seq = [column(x, y, zb, zt) for x, y, zt in wing]
    seq.append(L["pod_outer"])
    pod_l = len(seq) - 1
    seq.append(L["pod_inner"])
    seq.append(column(spec["centre_x"], 0.0, zb, spec.get("centre_top_z", 1.3)))
    seq.append(R["pod_inner"])
    pod_r = len(seq) - 1
    seq.append(R["pod_outer"])
    seq += [column(x, -y, zb, zt) for x, y, zt in reversed(wing)]
    quads = []
    for i in range(len(seq) - 1):
        (b0, t0), (b1, t1) = seq[i], seq[i + 1]
        if i in (pod_l, pod_r):
            # under a pod panel: from its lower edge down to the fascia's bottom line
            quads.append([Vector((b0.x, b0.y, zb)), Vector((b1.x, b1.y, zb)), b1, b0])
        else:
            quads.append([b0, b1, t1, t0])
    front = _quad_faces(tmp, quads, eye)
    tops = []
    for i in range(len(seq) - 1):
        (b0, t0), (b1, t1) = seq[i], seq[i + 1]
        f0 = Vector((t0.x - eye.x, t0.y - eye.y, 0)).normalized()
        f1 = Vector((t1.x - eye.x, t1.y - eye.y, 0)).normalized()
        tops.append([t0, t1, t1 + f1 * 0.3 + Vector((0, 0, -0.04)), t0 + f0 * 0.3 + Vector((0, 0, -0.04))])   # sloping away: the shelf stays out of the view
    for f in _quad_faces(tmp, tops, eye):
        if f.normal.z < 0:
            f.normal_flip()
    bmesh.ops.remove_doubles(tmp, verts=tmp.verts, dist=1e-4)
    bmesh.ops.solidify(tmp, geom=tmp.faces[:], thickness=0.03)
    mesh = bpy.data.meshes.new("_dash_tmp")
    tmp.to_mesh(mesh)
    g["int_console"].from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    tmp.free()
    # the satin edge along the glare shield, the orange pinstripe under it, a satin lip along the bottom
    for i in range(len(seq) - 1):
        (b0, t0), (b1, t1) = seq[i], seq[i + 1]
        if i in (pod_l, pod_r):
            b0, b1 = Vector((b0.x, b0.y, zb)), Vector((b1.x, b1.y, zb))
        tube(g["int_trim"], t0, t1, 0.011, 10)
        if i not in (pod_l, pod_r):
            # (not across the MFD panels: there the strip above the glass is too narrow, the line cut the screens)
            tube(g["accent"], t0 + Vector((0, 0, -0.03)), t1 + Vector((0, 0, -0.03)), 0.0035, 6)
        tube(g["int_trim"], b0 + Vector((0, 0, 0.004)), b1 + Vector((0, 0, 0.004)), 0.01, 10)
    return seq


def wing_panels(g, eye, spec):
    """Switch panels on the wings of the dash, between the side consoles and the MFDs: a recessed plate in a
    satin rim, toggles, a rotary knob, indicator lights."""
    zb = spec.get("fascia_bottom_z", 0.97)
    tilt = math.tan(math.radians(spec.get("fascia_tilt_deg", 22.0)))
    for side in (1, -1):
        for x, y, zt in [tuple(w) for w in spec.get("wing", [(17.3, 1.13, 1.06), (17.62, 0.98, 1.22)])][1:]:
            zc = (zb + zt) / 2
            f = Vector((x - eye[0], side * y - eye[1], 0)).normalized()
            c = Vector((x + 0.1, side * (y - 0.1), zc)) + f * tilt * (zc - zb)
            r, u, n = oriented(eye, c)
            rr_slab(g["int_dark"], c + n * 0.035, r, u, n, 0.2, 0.13, 0.02, 0.01)
            rr_ring(g["int_trim"], c + n * 0.04, r, u, n, 0.21, 0.14, 0.022, 0.008, 0.008)
            for j in range(4):
                p = c + n * 0.041 + r * (-0.07 + j * 0.035) + u * 0.02
                rr_slab(g["int_console"], p, r, u, n, 0.02, 0.03, 0.004, 0.004, 2)
                tube(g["int_trim"], p, p + n * 0.02 + u * 0.006, 0.004, 6)
                rr_slab(g["int_glow" if j % 2 else "accent"], p - u * 0.03, r, u, n, 0.01, 0.004, 0.0015, 0.002, 2)
            tube(g["int_trim"], c + n * 0.041 + r * 0.075 - u * 0.03, c + n * 0.062 + r * 0.075 - u * 0.03, 0.013, 14)


def underdash(g, eye, spec, zfloor, lights_out):
    """What is under the dash instead of a black hole: support ribs, cable runs with clamps, rudder pedals,
    blue footwell lights. Returns the footwell back wall box (hs_interior gives it a kit trim texture)."""
    zb = spec.get("fascia_bottom_z", 0.97)
    xw = spec.get("footwell_back_x", 18.62)
    for y in (-0.62, -0.3, 0.3, 0.62):
        a, b = Vector((xw - 0.02, y, zfloor)), Vector((spec["pod_x"] + 0.05, y, zb - 0.01))
        d = b - a
        res = bmesh.ops.create_cube(g["int_trim"], size=1.0)
        bmesh.ops.scale(g["int_trim"], vec=(0.05, 0.035, d.length), verts=res["verts"])
        m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        m.translation = (a + b) / 2
        bmesh.ops.transform(g["int_trim"], matrix=m, verts=res["verts"])
    for k, (key, r, dz) in enumerate((("int_dark", 0.016, 0.0), ("accent", 0.008, 0.03), ("int_dark", 0.011, 0.055))):
        pts = []
        for i in range(13):
            t = i / 12
            sag = 0.06 * math.sin(math.pi * ((t * 4) % 1.0))
            pts.append(Vector((xw - 0.08 - k * 0.03, -0.9 + 1.8 * t, zb - 0.07 - dz - sag)))
        for a, b in zip(pts, pts[1:]):
            tube(g[key], a, b, r, 8)
    for y in (-0.62, -0.3, 0.3, 0.62):
        tube(g["int_trim"], Vector((xw - 0.18, y, zb - 0.08)), Vector((xw - 0.02, y, zb - 0.08)), 0.012, 8)
    for y in (-0.2, 0.2):
        c = Vector((18.05, y, zfloor + 0.12))
        r, u, n = Vector((0, -1, 0)), Vector((0.45, 0, 0.89)).normalized(), Vector((-0.89, 0, 0.45)).normalized()
        rr_slab(g["int_console"], c, r, u, n, 0.11, 0.2, 0.02, 0.03)
        for j in range(4):
            rr_slab(g["int_trim"], c + n * 0.002 + u * (-0.06 + j * 0.04), r, u, n, 0.08, 0.008, 0.003, 0.004, 2)
        tube(g["int_trim"], c - n * 0.03 - u * 0.1, Vector((18.3, y, zfloor)), 0.015, 10)
    for y0, y1 in ((-0.9, -0.2), (0.2, 0.9)):
        tube(g["int_glow"], Vector((spec["pod_x"] - 0.02, y0, zb - 0.02)), Vector((spec["pod_x"] - 0.02, y1, zb - 0.02)), 0.004, 6)
    lights_out.append({"at": [18.3, 0.0, zfloor + 0.35], "cd": spec.get("footwell_cd", 2.5)})
    return (xw, -0.95, zfloor), (xw + 0.04, 0.95, zb)


def build_wrap(g, screen_bm, sockets, eye, spec, zfloor, lights_out):
    dash(g, screen_bm, sockets, eye, spec, zfloor)
    wing_panels(g, eye, spec)
    pedestal(g, screen_bm, sockets, eye, spec)
    return underdash(g, eye, spec, zfloor, lights_out)
