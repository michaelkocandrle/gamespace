"""The Wayfarer's front cockpit from the approved concept A (ArtSource/Ships/Wayfarer/Concept/Cockpit/
cockpit_target_space.png / _day.png, author 25. 9. 2026): two large tilted MFD pods with rounded satin
bezels left and right, a central pedestal with a holographic radar and the two small centre screens, button
banks under the pods, a low sculpted graphite cowl instead of a dashboard wall and a glare shield.

Called by hs_interior.dashboard() when recipe interior.cockpit.style == "pods". Screens keep the game's
canvas (USpaceCockpitDisplays: left / right 880x490 since holo MFD v3, centre_top 210x259, centre_bottom 210x231), so every
screen quad has its canvas rectangle's aspect ratio and a Display_<name> socket in front of it
(test_cockpit_displays.py). Placement rule (test_cockpit_frame.py): every screen whole in the level view
under the HUD - top edge >= 8 deg (the HUD ends ~5 deg under the eye), bottom edge <= 28 deg under the eye, the nearest screen >= 0.9 m ahead.

Materials: int_console (warm graphite), int_trim (satin metal rims), int_glow (cool edge light, hologram),
accent (Halcyon orange caps and pinstripes), int_red, int_dark.
"""
import math

import bmesh
from mathutils import Vector

# (holo MFD v3, 5. 10. 2026: the MFDs SC's 1.8 : 1, 880 px wide - was 560)
SIDE_SOCKETS = {}   # sockets placed by wing_panels (no sockets dict there): build() copies them

RECTS = {"left": (0, 0, 880, 490), "right": (880, 0, 1760, 490),
         "centre_top": (1760, 0, 1970, 259), "centre_bottom": (1760, 259, 1970, 490)}
CANVAS = (1970.0, 490.0)
MFD_ASPECT = 490.0 / 880.0


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


# ------------------------------------------------------------------------------------------ control modules
# Author 25. 9. 2026 (step 4): no round dots - real controls in modules with a housing, screws and a label on every
# control. Each module is a housing (graphite, satin rim, four screws) with a dark face; the controls sit on a grid.
# Labels are mesh decals from the library (ck_*), placed by hs_interior_decals from LABELS.
LABELS = []          # {"item", "at": point on the face, "n": face normal, "scale"} - reset by hs_interior.build
# grime cards where hands and boots work (critic 7. 10. 2026: "everything factory-clean"): {"at", "n", "up", "size",
# "kind", "alpha"} - laid by hs_interior_decals through hs_decals.Placer.card_at; reset by hs_interior.build
GRIME = []


def grime(at, n, up, size, kind="smear", alpha=0.5, wear=False):
    """wear: the light polish / scuff card (DecalWear) instead of the dark dirt. The soft "smear" blotch is not laid
    (critic 7. 10. r4: blotches in the middle of plates read as smoke): dirt sits in seams and on edges only."""
    if kind == "smear":
        return
    GRIME.append({"at": list(at), "n": list(n), "up": list(up), "size": list(size), "kind": kind, "alpha": alpha, "wear": wear})


def stencil(item, at, n, right, up, scale=0.6, max_w=1.0):
    """A small stencil / panel number / warning decal on a face (laid like a control's label)."""
    LABELS.append({"item": item, "at": list(at), "n": list(n), "x": list(right), "y": list(up), "scale": scale, "max_w": max_w})


def _frame_tilt(right, up, n, deg):
    """The frame turned about its right axis (the face tips towards up)."""
    a = math.radians(deg)
    n2 = (n * math.cos(a) + up * math.sin(a)).normalized()
    up2 = (up * math.cos(a) - n * math.sin(a)).normalized()
    return right, up2, n2


def _led(g, p, right, up, n, key):
    rr_slab(g["int_dark"], p + n * 0.002, right, up, n, 0.011, 0.007, 0.0015, 0.003, 2)          # bezel
    rr_slab(g[key], p + n * 0.0028, right, up, n, 0.007, 0.0035, 0.001, 0.001, 2)                  # lens


def _toggle_guarded(g, p, right, up, n, guard_key):
    tube(g["int_trim"], p, p + n * 0.004, 0.0075, 16)                                               # boss
    tip = p + n * 0.024 + up * 0.009
    tube(g["int_trim"], p + n * 0.004, tip, 0.0022, 8)                                              # lever
    d = (tip - p).normalized()
    tube(g["int_trim"], tip - d * 0.004, tip + d * 0.002, 0.0038, 10)
    for su in (-1, 1):                                                                              # guard cheeks
        rr_slab(g[guard_key], p + right * (su * 0.0125) + n * 0.013, n, up, right * su, 0.026, 0.028, 0.002, 0.0025, 2)
    r2, u2, n2 = _frame_tilt(right, up, n, -55.0)                                                  # the cover, flipped up
    hinge = p + up * 0.014 + n * 0.004
    rr_slab(g[guard_key], hinge + u2 * 0.014 + n2 * 0.002, r2, u2, n2, 0.027, 0.028, 0.003, 0.002, 2)
    tube(g["int_trim"], hinge - right * 0.015, hinge + right * 0.015, 0.0025, 8)                  # hinge pin


def _rotary(g, p, right, up, n):
    tube(g["int_dark"], p, p + n * 0.003, 0.016, 24)                                                # skirt
    for k in range(5):                                                                             # detent ticks
        a = math.radians(-60 + 30 * k)
        q = p + n * 0.0032 + (up * math.cos(a) + right * math.sin(a)) * 0.0185
        rr_slab(g["int_glow"], q, right, up, n, 0.0012, 0.0012, 0.0005, 0.0006, 1)
    tube(g["int_trim"], p + n * 0.003, p + n * 0.019, 0.0105, 24)                                   # knob
    for k in range(16):                                                                            # knurling
        a = 2 * math.pi * k / 16
        d = up * math.cos(a) + right * math.sin(a)
        tube(g["int_dark"], p + n * 0.006 + d * 0.0104, p + n * 0.018 + d * 0.0104, 0.0012, 4)
    rr_slab(g["int_glow"], p + n * 0.0195 + up * 0.005, right, up, n, 0.0016, 0.009, 0.0006, 0.0008, 1)   # pointer


def _rocker(g, p, right, up, n):
    rr_slab(g["int_dark"], p + n * 0.004, right, up, n, 0.017, 0.026, 0.002, 0.004, 2)              # housing
    for sv, deg in ((1, 12.0), (-1, -12.0)):
        r2, u2, n2 = _frame_tilt(right, up, n, deg)
        rr_slab(g["int_trim"], p + n * (0.007 if sv > 0 else 0.005) + up * (sv * 0.0058), r2, u2, n2, 0.013, 0.0105, 0.0015, 0.003, 2)
    rr_slab(g["int_glow"], p + n * 0.0086 + up * 0.0085, right, up, n, 0.008, 0.0016, 0.0006, 0.0006, 1)   # "on" bar


def _button(g, p, right, up, n, key):
    rr_ring(g["int_trim"], p + n * 0.004, right, up, n, 0.019, 0.019, 0.003, 0.002, 0.004, 3)       # bezel
    rr_slab(g["int_dark"], p + n * 0.0055, right, up, n, 0.0145, 0.0145, 0.0025, 0.0045, 3)          # cap, 14.5 mm
    rr_slab(g[key], p + n * 0.0058, right, up, n, 0.009, 0.0022, 0.0008, 0.0008, 1)                 # backlit legend bar


def _encoder(g, p, right, up, n):
    tube(g["int_dark"], p, p + n * 0.002, 0.012, 20)
    for k in range(9):                                                                             # LED arc
        a = math.radians(-120 + 30 * k)
        q = p + n * 0.0022 + (up * math.cos(a) + right * math.sin(a)) * 0.0105
        rr_slab(g["int_glow" if k < 6 else "int_dark"], q, right, up, n, 0.0014, 0.0014, 0.0005, 0.0005, 1)
    tube(g["int_trim"], p + n * 0.002, p + n * 0.014, 0.0075, 20)
    tube(g["int_dark"], p + n * 0.014, p + n * 0.0155, 0.0065, 20)
    rr_slab(g["int_glow"], p + n * 0.0157 + up * 0.004, right, up, n, 0.0014, 0.0014, 0.0005, 0.0005, 1)


def seat(tree, c, right, up, n, w, h, clearance=0.002):
    """c moved along n so a w x h plate there stands clear of the surface in `tree` everywhere under it (a
    module set on a bulged or bent fascia sank into it at one side and its labels found the fascia's back)."""
    if tree is None:
        return c
    top = None
    for su in (-0.5, 0.0, 0.5):
        for sv in (-0.5, 0.0, 0.5):
            q = c + right * (su * w) + up * (sv * h)
            hit = tree.ray_cast(q + n * 0.1, -n, 0.3)[0]
            if hit is not None:
                d = (hit - c).dot(n)
                top = d if top is None else max(top, d)
    return c + n * (max(top, 0.0) + clearance) if top is not None else c


def control_module(g, c, right, up, n, w, h, rows, label_scale=0.42, tree=None):
    """A module at c (face centre, facing n): housing w x h, rows of (kind, label item or None) top to bottom,
    spread evenly. Every control with a label gets a ck_* decal under it (LABELS). tree: the surface it is set
    on (seat())."""
    c = seat(tree, c, right, up, n, w, h)
    # a dark gap round the housing: the module reads as set into the dash (it looked laid on it - critic, 25. 9.)
    rr_ring(g["int_dark"], c - n * 0.0005, right, up, n, w + 0.012, h + 0.012, 0.01, 0.0065, 0.03, 4)
    rr_slab(g["int_housing"], c, right, up, n, w, h, 0.006, 0.03)                                  # (SC: grey housings)
    rr_ring(g["int_trim"], c + n * 0.0015, right, up, n, w, h, 0.006, 0.004, 0.003, 4)
    rr_slab(g["int_dark"], c + n * 0.0012, right, up, n, w - 0.012, h - 0.012, 0.003, 0.002, 3)
    for su in (-1, 1):
        for sv in (-1, 1):
            q = c + right * (su * (w / 2 - 0.0045)) + up * (sv * (h / 2 - 0.0045))
            tube(g["int_trim"], q, q + n * 0.0035, 0.0022, 10)
            rr_slab(g["int_dark"], q + n * 0.0036, right, up, n, 0.0032, 0.0007, 0.0002, 0.0004, 1)   # slot
    face = c + n * 0.0014
    grime(c, n, up, (w * 0.9, h * 0.9), "smear", 0.85)
    grime(c - up * (h * 0.3), n, up, (w * 0.8, h * 0.35), "smear", 0.8, wear=True)
    for dv in (up, -up):                                                    # dirt settled round the housing's gap
        grime(c + dv * (h / 2 + 0.02), n, -dv, (w + 0.05, 0.045), "soot", 1.0)
    for du in (right, -right):
        grime(c + du * (w / 2 + 0.02), n, -du, (h + 0.05, 0.045), "soot", 1.0)
    usable_h = h - 0.018
    cell = usable_h / len(rows)
    placed = {}
    for i, row in enumerate(rows):
        v = usable_h / 2 - cell * (i + 0.5)
        for j, (kind, label) in enumerate(row):
            u = -(w - 0.016) / 2 + (w - 0.016) * (j + 0.5) / len(row)
            lift = 0.0055 if label else 0.0
            p = face + right * u + up * (v + lift)
            if kind in ("guarded", "guarded_red"):
                _toggle_guarded(g, p, right, up, n, "int_red" if kind == "guarded_red" else "accent")
            elif kind == "rotary":
                _rotary(g, p, right, up, n)
            elif kind == "rocker":
                _rocker(g, p, right, up, n)
            elif kind == "button":
                _button(g, p, right, up, n, "int_glow")
            elif kind == "encoder":
                _encoder(g, p, right, up, n)
            elif kind in ("led_w", "led_o", "led_blink"):
                _led(g, p, right, up, n, {"led_w": "int_led_w", "led_o": "int_led_o", "led_blink": "int_led_blink"}[kind])
            if label:
                placed[label] = p
                LABELS.append({"item": label, "at": list(face + right * u + up * (v + lift - cell / 2 + 0.0058)),
                               "n": list(n), "x": list(right), "y": list(up), "scale": label_scale,
                               "max_w": (w - 0.016) / len(row) - 0.004})
    return placed


def console_head(g, c, right, up, n, w, h, label):
    """The module at a console's nose (7. 10. 2026, after SC's console heads): a housing-grey plate in a satin rim set
    into a dark gap; the aft half (-right) a perforated speaker grille (a field of round holes in a dark well), the fore
    half a big red push button in a polished bezel under a hinged orange guard, its label under it; four screws."""
    rr_ring(g["int_dark"], c - n * 0.0005, right, up, n, w + 0.012, h + 0.012, 0.012, 0.0065, 0.02, 4)
    rr_slab(g["int_housing"], c + n * 0.004, right, up, n, w, h, 0.01, 0.016, 4)
    rr_ring(g["int_trim"], c + n * 0.0055, right, up, n, w, h, 0.01, 0.004, 0.003, 4)
    # the grille: a dark well, a perforated plate over it (holes as dark discs on the grey, 9 x 7, staggered)
    gc = c + up * (h * 0.22) + n * 0.004
    gw, gh = w - 0.03, h * 0.42
    rr_ring(g["int_trim"], gc + n * 0.0012, right, up, n, gw, gh, 0.008, 0.003, 0.0016, 3)
    rr_slab(g["int_housing"], gc + n * 0.0006, right, up, n, gw - 0.006, gh - 0.006, 0.006, 0.001, 3)
    nu, nv = 24, 14
    for i in range(nu):
        for j in range(nv):
            du = -gw / 2 + 0.009 + (gw - 0.018) * i / (nu - 1) + (0.0036 if j % 2 else 0.0)
            dv = -gh / 2 + 0.009 + (gh - 0.018) * j / (nv - 1)
            if abs(du) > gw / 2 - 0.008:
                continue
            rr_slab(g["int_dark"], gc + right * du + up * dv + n * 0.0008, right, up, n, 0.0026, 0.0026, 0.0013, 0.0004, 2)
    # the button: a polished bezel ring, a deep red cap with a lighter dome, a clear guard on a hinge, the label below
    # the button on its own raised plinth (critic 7. 10. r1: small and hidden under its cover)
    bc = c - up * (h * 0.2) + n * 0.004
    rr_slab(g["int_housing"], bc + n * 0.008, right, up, n, 0.1, 0.1, 0.012, 0.008, 4)               # plinth
    rr_ring(g["int_trim"], bc + n * 0.0085, right, up, n, 0.1, 0.1, 0.012, 0.004, 0.002, 4)
    bc = bc + n * 0.008
    rr_ring(g["int_dark"], bc + n * 0.001, right, up, n, 0.08, 0.08, 0.014, 0.008, 0.002, 4)
    tube(g["int_trim"], bc, bc + n * 0.008, 0.031, 40)                                             # polished bezel
    tube(g["int_dark"], bc + n * 0.008, bc + n * 0.0085, 0.026, 40)
    tube(g["int_red"], bc + n * 0.007, bc + n * 0.02, 0.024, 40)                                   # the mushroom cap
    tube(g["int_red"], bc + n * 0.02, bc + n * 0.023, 0.02, 40)
    tube(g["int_led_o"], bc + n * 0.023, bc + n * 0.0234, 0.008, 24)                               # its lamp
    for su in (-1, 1):                                                                             # the guard's cheeks
        rr_slab(g["int_housing"], bc + right * (su * 0.038) + n * 0.014, n, up, right * su, 0.028, 0.07, 0.003, 0.004, 2)
    hinge = bc + up * 0.036 + n * 0.017
    tube(g["int_trim"], hinge - right * 0.04, hinge + right * 0.04, 0.0035, 12)
    r2, u2, n2 = _frame_tilt(right, up, n, -100.0)                                                 # the red guard, flipped open
    # (critic 7. 10. r2: a bare frame read as a handle) a solid red cover plate with a raised rim and a finger lip
    gcen = hinge + u2 * 0.034 + n2 * 0.002
    rr_slab(g["int_red"], gcen, r2, u2, n2, 0.074, 0.066, 0.006, 0.003, 2)
    rr_ring(g["int_red"], gcen + n2 * 0.004, r2, u2, n2, 0.074, 0.066, 0.006, 0.004, 0.004, 2)
    rr_slab(g["int_red"], gcen + u2 * 0.035 + n2 * 0.003, r2, u2, n2, 0.03, 0.008, 0.003, 0.004, 2)
    for su in (-1, 1):                                                                             # hinge knuckles
        tube(g["int_red"], hinge + right * (su * 0.03) - right * 0.008, hinge + right * (su * 0.03) + right * 0.008, 0.0045, 12)
    # (the label clear of the plinth's rim - its top was cut off, "EMERG UZ")
    # (critic 7. 10.: C22 read upside down) the information layer reads from the seat: along -up, its top forward
    lr, lu = -up, right
    LABELS.append({"item": label, "at": list(bc + right * 0.078 - n * 0.0075), "n": list(n), "x": list(lr), "y": list(lu),
                   "scale": 1.0, "max_w": w * 0.8})
    for su in (-1, 1):
        for sv in (-1, 1):
            q = c + right * (su * (w / 2 - 0.009)) + up * (sv * (h / 2 - 0.009)) + n * 0.004
            tube(g["int_trim"], q, q + n * 0.003, 0.0026, 10)
            rr_slab(g["int_dark"], q + n * 0.0031, right, up, n, 0.0036, 0.0008, 0.0003, 0.0004, 1)
    # (critic 7. 10. r3: half the head a bare grey plate) the information layer on the free plate beside the button:
    # a warning triangle, the panel number, a small service stencil; grime where the hand lands on it
    top_ = c + n * 0.0042
    stencil("tri_warning", top_ - up * (h * 0.2) - right * 0.078, n, lr, lu, 0.4, 0.035)
    stencil("panel_C21" if label == "ck_emerg_o2" else "panel_C22", top_ - up * (h * 0.42), n, lr, lu, 0.45, 0.05)
    grime(top_ - up * (h * 0.2), n, up, (0.14, 0.14), "smear", 1.0)
    grime(top_ - up * (h * 0.2), n, up, (0.12, 0.12), "smear", 0.9, wear=True)
    grime(top_ + up * (h * 0.45), n, -up, (w, 0.06), "rim", 1.0)



def hazard_band(g, c, right, up, n, w, h, pitch=0.02):
    """A hazard hatch band centred at c along `right`: a dark strip with orange 45 deg bars (SC's yellow-black
    hatching on console noses and module edges, here in Halcyon orange), a satin hairline each side."""
    rr_slab(g["int_dark"], c + n * 0.0006, right, up, n, w, h, 0.002, 0.0008, 1)
    k = int(w / pitch)
    bar = pitch * 0.5
    for i in range(k):
        u = -w / 2 + pitch * (i + 0.5)
        if abs(u) > w / 2 - pitch * 0.5:
            continue
        r2 = (right + up).normalized()
        u2 = (up - right).normalized()
        rr_slab(g["accent"], c + right * u + n * 0.0009, r2, u2, n, bar * 0.707, h * 1.414 * 0.62, 0.0004, 0.0003, 1)
    for sv in (-1, 1):
        rr_slab(g["int_trim"], c + up * (sv * (h / 2 + 0.0015)) + n * 0.0007, right, up, n, w, 0.0015, 0.0005, 0.0008, 1)


# ------------------------------------------------------------------------------------------ hologram
# Author 25. 9. 2026 (step 6): the ship's hologram from the Wayfarer's own mesh - additive blue, fresnel, scan
# lines, a slight jitter, slowly turning (M_Ship_Holo: the turn and the jitter are World Position Offset about
# the mesh's centre, which import_ship.py sets as HoloPivot from the imported mesh's bounds). Off the line of
# sight: over the left MFD. Damage colours are prepared in the material (DamageColor x DamageAmount x vertex
# colour R), static for now.


def _envelope(bm, voxels, smooth=30):
    """The outer envelope of the triangles in bm as a new closed bmesh (26. 9. 2026): a decimated copy of the
    whole exterior kept every inner face (hull backs, greeble undersides), and the additive hologram showed them
    all through each other - "a blurred blue mass" (critic). Voxels `voxels` along x: a voxel is surface when a
    triangle passes within 0.87 voxel of its centre (a 6-tight wall), the walls grow one voxel to seal seams,
    empty space floods in from the grid's border, everything the flood did not reach is solid (the hull's
    inside fills up), the solid shrinks back one voxel, and its boundary faces are the envelope."""
    import numpy as np
    from mathutils.bvhtree import BVHTree
    tree = BVHTree.FromBMesh(bm)
    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    vox = (hi.x - lo.x) / voxels
    pad = 3
    o = lo - Vector((pad, pad, pad)) * vox
    n = [int(math.ceil((hi[a] - lo[a]) / vox)) + 2 * pad + 1 for a in range(3)]
    surf = np.zeros(n, dtype=bool)
    thr = 0.87 * vox
    near = tree.find_nearest
    for i in range(n[0]):
        x = o.x + i * vox
        for j in range(n[1]):
            y = o.y + j * vox
            row = surf[i, j]
            for k in range(n[2]):
                if near(Vector((x, y, o.z + k * vox)), thr)[0] is not None:
                    row[k] = True

    def grow(a):
        b = a.copy()
        b[1:] |= a[:-1]; b[:-1] |= a[1:]
        b[:, 1:] |= a[:, :-1]; b[:, :-1] |= a[:, 1:]
        b[:, :, 1:] |= a[:, :, :-1]; b[:, :, :-1] |= a[:, :, 1:]
        return b

    wall = grow(surf)
    out = np.zeros(n, dtype=bool)
    out[0], out[-1], out[:, 0], out[:, -1], out[:, :, 0], out[:, :, -1] = True, True, True, True, True, True
    out &= ~wall
    while True:
        nxt = grow(out) & ~wall
        if nxt.sum() == out.sum():
            break
        out = nxt
    solid = ~out
    # shrink back the voxel the walls grew by (a voxel stays when all six neighbours are solid)
    sh = solid.copy()
    sh[1:] &= solid[:-1]; sh[:-1] &= solid[1:]
    sh[:, 1:] &= solid[:, :-1]; sh[:, :-1] &= solid[:, 1:]
    sh[:, :, 1:] &= solid[:, :, :-1]; sh[:, :, :-1] &= solid[:, :, 1:]
    solid = sh
    env = bmesh.new()
    verts = {}

    def vert(i, j, k):
        key = (i, j, k)
        v = verts.get(key)
        if v is None:
            v = verts[key] = env.verts.new(o + Vector((i - 0.5, j - 0.5, k - 0.5)) * vox)
        return v

    pads = np.pad(solid, 1)
    for axis in range(3):
        a = np.moveaxis(pads, axis, 0)
        diff = a[1:].astype(np.int8) - a[:-1].astype(np.int8)     # +1: empty -> solid, -1: solid -> empty
        for sign in (1, -1):
            for idx in zip(*np.nonzero(diff == sign)):
                # the face lies between cells idx[0]-1 and idx[0] along the axis (padded index = cell + 1)
                c = [int(idx[0]), int(idx[1]) - 1, int(idx[2]) - 1]
                if axis == 0:
                    pts = [(c[0], c[1], c[2]), (c[0], c[1] + 1, c[2]), (c[0], c[1] + 1, c[2] + 1), (c[0], c[1], c[2] + 1)]
                elif axis == 1:
                    pts = [(c[1], c[0], c[2]), (c[1], c[0], c[2] + 1), (c[1] + 1, c[0], c[2] + 1), (c[1] + 1, c[0], c[2])]
                else:
                    pts = [(c[1], c[2], c[0]), (c[1] + 1, c[2], c[0]), (c[1] + 1, c[2] + 1, c[0]), (c[1], c[2] + 1, c[0])]
                vs = [vert(*q) for q in pts]
                # sign +1: solid on the far side, the face looks back along -axis
                env.faces.new(vs if sign < 0 else vs[::-1])
    env.normal_update()
    # the staircase smoothed into a surface by Taubin steps (shrink 0.5, grow 0.53): plain averaging shrank the
    # tail fin away, the Laplacian operator with preserve_volume left the steps as they were
    for _ in range(smooth):
        for f in (0.5, -0.53):
            bmesh.ops.smooth_vert(env, verts=env.verts, factor=f, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bmesh.ops.triangulate(env, faces=env.faces)
    env.normal_update()
    return env


def build_hologram(g, coll, mat, ship, exterior, centre, length=0.16, max_tris=24000, voxels=160):
    """The outer envelope of the exterior objects (_envelope), `length` long, centred on `centre`, decimated, on an
    emitter; returns the object SM_Ship_<Ship>_Hologram (its own part, hs_assemble_ship.py)."""
    import bpy
    bm = bmesh.new()
    # evaluated meshes (the greebles are instanced on point clouds by modifiers: their raw meshes are loose
    # points with instancing attributes - they came through the assemble as garbage vertices, 25. 9. 2026)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in exterior:
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if me is not None and len(me.polygons):
            tmp = bmesh.new()
            tmp.from_mesh(me)
            tmp.transform(ob.matrix_world)
            tm = bpy.data.meshes.new("_holo_part")
            tmp.to_mesh(tm)
            tmp.free()
            # positions and faces only
            bm.from_mesh(tm)
            bpy.data.meshes.remove(tm)
        ev.to_mesh_clear()
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for dom in (bm.verts.layers, bm.edges.layers, bm.faces.layers):
        for kind in ("int", "float", "float_vector", "float_color", "color", "string", "bool"):
            coll_ = getattr(dom, kind, None)
            if coll_ is None:
                continue
            for layer in list(coll_.values()):
                coll_.remove(layer)
    if not bm.faces:
        bm.free()
        return None
    env = _envelope(bm, voxels)
    bm.free()
    bm = env
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    mid = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2))
    k = length / max(max(xs) - min(xs), 1e-6)
    for v in bm.verts:
        v.co = centre + (v.co - mid) * k
    me = bpy.data.meshes.new("SM_Ship_%s_Hologram" % ship)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    # decimated by a modifier the assemble applies (hs_assemble_ship applies every modifier); a modifier also
    # keeps hs_build_ship.finish() off it - its Bevel on this dense mesh made garbage vertices (25. 9. 2026)
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    mod = ob.modifiers.new("Decimate", "DECIMATE")
    mod.ratio = min(1.0, max_tris / max(tris, 1))
    # smooth: the fresnel rim follows the hull's curves, not triangle facets (a "tangle of triangles" by day -
    # critic, 25. 9. 2026)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    if not ob.data.uv_layers:
        # (no texture, but the exporter wants a UV map: a planar one from above)
        uv = ob.data.uv_layers.new(name="UVMap")
        for loop in ob.data.loops:
            co = ob.data.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((co.x - centre.x) / length + 0.5, (co.y - centre.y) / length + 0.5)
    # the emitter under it: a graphite ring, a dark lens with a thin cool rim (a glowing white disc read as a
    # foreign lamp on the dash - critic, 25. 9. 2026)
    base = centre - Vector((0, 0, 0.065))
    tube(g["int_console"], base, base + Vector((0, 0, 0.012)), 0.034, 32)
    tube(g["int_glow"], base + Vector((0, 0, 0.012)), base + Vector((0, 0, 0.013)), 0.026, 32)
    tube(g["int_dark"], base + Vector((0, 0, 0.012)), base + Vector((0, 0, 0.0145)), 0.0235, 32)
    for a in range(3):
        d = Vector((math.cos(a * 2 * math.pi / 3), math.sin(a * 2 * math.pi / 3), 0))
        tube(g["int_trim"], base + d * 0.03, base + d * 0.03 + Vector((0, 0, 0.02)), 0.0025, 6)
    return ob


# ------------------------------------------------------------------------------------------ pilot seat
# Author 25. 9. 2026: the Meshy seat goes, procedural like the exterior. A graphite shell on the pedestal, padded
# pan and back with side bolsters and quilting seams, a headrest, a five-point harness in the Halcyon orange.

def pilot_seat(g, rect, zr):
    x0, x1, y0, y1 = rect
    z0 = zr[0]
    cx, cy = (x0 + x1) / 2 + 0.05, (y0 + y1) / 2
    right = Vector((0, -1, 0))
    fwd, upz = Vector((1, 0, 0)), Vector((0, 0, 1))
    # column from the pedestal to the pan, a swivel ring
    tube(g["int_trim"], Vector((cx, cy, z0 + 0.16)), Vector((cx, cy, z0 + 0.3)), 0.06, 20)
    tube(g["int_dark"], Vector((cx, cy, z0 + 0.3)), Vector((cx, cy, z0 + 0.33)), 0.11, 24)
    # pan: shell, two padded segments (a flat board read as a plank - segments with round edges read as padding)
    pan = Vector((cx + 0.02, cy, z0 + 0.45))
    rr_slab(g["int_console"], pan - upz * 0.07, right, fwd, upz, 0.56, 0.52, 0.05, 0.06, 4)
    for v, h in ((-0.12, 0.22), (0.12, 0.23)):
        rr_slab(g["int_leather"], pan + fwd * v, right, fwd, upz, 0.42, h, 0.028, 0.075, 5)
        rr_slab(g["int_dark"], pan + fwd * v + upz * 0.001, right, fwd, upz, 0.38, 0.004, 0.001, 0.002, 1)   # stitch
    # side bolsters on the pan, turned in towards the pilot
    for sd in (-1, 1):
        side_n = (upz * math.cos(math.radians(25)) - right * sd * math.sin(math.radians(25))).normalized()
        r2 = (right - side_n * right.dot(side_n)).normalized()
        rr_slab(g["int_leather"], pan + right * (sd * 0.245) + upz * 0.05, r2, fwd, side_n, 0.075, 0.46, 0.035, 0.1, 5)
    # back: tilted 12 degrees, a shell behind, four padded segments, bolsters turned in
    t = math.radians(12.0)
    n = Vector((math.cos(t), 0, math.sin(t)))
    up = Vector((-math.sin(t), 0, math.cos(t)))
    back = Vector((cx - 0.21, cy, z0 + 0.9))
    rr_slab(g["int_console"], back - n * 0.09, right, up, n, 0.58, 0.92, 0.07, 0.05, 5)
    for v, h in ((-0.3, 0.17), (-0.11, 0.18), (0.08, 0.18), (0.27, 0.17)):
        # upholstered panels, not pillows (round pads read as a toy - critic, 25. 9. 2026)
        rr_slab(g["int_leather"], back + up * v, right, up, n, 0.4, h, 0.028, 0.085, 5)
        rr_slab(g["int_dark"], back + up * v + n * 0.001, right, up, n, 0.36, 0.004, 0.001, 0.002, 1)   # stitch
    for sd in (-1, 1):
        side_n = (n * math.cos(math.radians(28)) - right * sd * math.sin(math.radians(28))).normalized()
        r2 = (right - side_n * right.dot(side_n)).normalized()
        rr_slab(g["int_leather"], back + right * (sd * 0.25) + n * 0.03, r2, up, side_n, 0.085, 0.74, 0.04, 0.14, 5)
    # headrest on two posts, two pads
    head = back + up * 0.54
    for sd in (-1, 1):
        tube(g["int_trim"], back + up * 0.4 + right * (sd * 0.08) - n * 0.03, head - up * 0.08 + right * (sd * 0.08) - n * 0.03, 0.009, 8)
    rr_slab(g["int_console"], head - n * 0.03, right, up, n, 0.32, 0.21, 0.07, 0.06, 5)
    for v in (-0.045, 0.045):
        rr_slab(g["int_leather"], head + up * v, right, up, n, 0.27, 0.08, 0.035, 0.05, 5)
    # harness: two shoulder straps with adjusters down the back, a lap belt on the pan, a round buckle
    for sd in (-1, 1):
        # the shoulder strap runs from the shell's top edge (over it, into the harness slot) down to the pan
        rr_slab(g["accent"], back + up * 0.02 + right * (sd * 0.1) + n * 0.003, right, up, n, 0.04, 0.86, 0.004, 0.004, 2)
        rr_slab(g["accent"], back + up * 0.46 + right * (sd * 0.1) - n * 0.04, right, n, -up, 0.04, 0.1, 0.004, 0.004, 2)
        rr_slab(g["int_dark"], back + up * 0.455 + right * (sd * 0.1) - n * 0.06, right, n, -up, 0.055, 0.02, 0.003, 0.01, 2)  # slot
        rr_slab(g["accent"], pan + right * (sd * 0.07) - fwd * 0.05 + upz * 0.003, right, fwd, upz,
                0.04, 0.3, 0.004, 0.004, 2)
        rr_slab(g["int_trim"], back + up * 0.34 + right * (sd * 0.1) + n * 0.006, right, up, n, 0.05, 0.035, 0.005, 0.006, 2)
        rr_slab(g["int_trim"], back - up * 0.12 + right * (sd * 0.1) + n * 0.006, right, up, n, 0.046, 0.022, 0.004, 0.005, 2)
        rr_slab(g["accent"], pan + right * (sd * 0.12) + fwd * 0.1 + upz * 0.003, right, fwd, upz, 0.18, 0.04, 0.004, 0.004, 2)
    tube(g["int_trim"], pan + fwd * 0.1 + upz * 0.003, pan + fwd * 0.1 + upz * 0.018, 0.035, 20)
    tube(g["accent"], pan + fwd * 0.1 + upz * 0.018, pan + fwd * 0.1 + upz * 0.021, 0.018, 16)
    # side frame: two satin bars from the pan shell to the back shell, a lever under the pan
    for sd in (-1, 1):
        a_ = pan - upz * 0.05 + right * (sd * 0.28) - fwd * 0.2
        b_ = back - n * 0.08 + right * (sd * 0.28) - up * 0.2
        tube(g["int_trim"], a_, b_, 0.014, 10)
    tube(g["int_trim"], pan - upz * 0.09 + fwd * 0.2 + right * 0.2, pan - upz * 0.09 + fwd * 0.3 + right * 0.24, 0.007, 8)
    # armrests (author 26. 9. 2026): a padded arm on a graphite shell each side, hinged at the back on an arm
    # from the side frame (they fold up for getting in); 23 cm clear of the consoles
    for sd in (-1, 1):
        top = pan + right * (sd * 0.335) + fwd * 0.03 + upz * 0.22
        rr_slab(g["int_console"], top - upz * 0.028, right, fwd, upz, 0.08, 0.34, 0.02, 0.022, 4)
        rr_slab(g["int_leather"], top, right, fwd, upz, 0.07, 0.32, 0.022, 0.028, 4)
        rr_slab(g["int_dark"], top + upz * 0.0005, right, fwd, upz, 0.004, 0.27, 0.001, 0.001, 1)   # stitch
        hinge = top - upz * 0.05 - fwd * 0.15
        tube(g["int_trim"], hinge - right * 0.03, hinge + right * 0.03, 0.013, 12)
        tube(g["int_trim"], pan - upz * 0.05 + right * (sd * 0.3) - fwd * 0.2, hinge, 0.012, 10)
        tube(g["int_trim"], hinge, top - upz * 0.03 - fwd * 0.1, 0.01, 8)


def _catmull(points, sub):
    """Catmull-Rom resample of a polyline of tuples (each value interpolated alike), `sub` steps per span."""
    out = []
    n = len(points)
    for i in range(n - 1):
        p0, p1, p2, p3 = points[max(i - 1, 0)], points[i], points[i + 1], points[min(i + 2, n - 1)]
        for k in range(sub):
            t = k / sub
            out.append(tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(points[-1])
    return out


def pilot_seat_v3(g, rect, zr):
    """The pilot seat after SC's (author 5. 10. 2026: "the seat still not good enough, plastic and cheap"): one
    sculpted bucket shell swept from the pan's front lip up the back to the headrest (a U section whose sides rise
    into wings), quilted channels of padding on it with bolsters along the sides, a five-point harness in dark webbing
    with a machined rotary buckle, and a structural frame - spine spars, a gas strut, the swivel post on floor rails.
    Seat-local: x forward, z up from the floor, the pilot's right is -y."""
    x0, x1, y0, y1 = rect
    z0 = zr[0]
    cx, cy = (x0 + x1) / 2 + 0.05, (y0 + y1) / 2
    side = Vector((0, -1, 0))

    def W(x, z):
        return Vector((cx + x, cy, z0 + z))

    # the spine: (x, z, half width, wing height) from the pan's front lip up to the head
    spine = _catmull([(0.29, 0.405, 0.245, 0.03), (0.14, 0.395, 0.265, 0.05), (-0.04, 0.40, 0.275, 0.065),
                      (-0.165, 0.455, 0.28, 0.08), (-0.205, 0.60, 0.285, 0.11), (-0.23, 0.80, 0.285, 0.125),
                      (-0.255, 1.00, 0.275, 0.115), (-0.272, 1.15, 0.235, 0.075), (-0.285, 1.27, 0.17, 0.055),
                      (-0.292, 1.39, 0.16, 0.05), (-0.295, 1.44, 0.15, 0.04)], 4)
    m = len(spine)
    frames = []
    for i, (x, z, hw, wing) in enumerate(spine):
        a, b = spine[max(i - 1, 0)], spine[min(i + 1, m - 1)]
        t = Vector((b[0] - a[0], 0, b[1] - a[1])).normalized()
        nrm = t.cross(side).normalized()           # towards the pilot (up on the pan, forward on the back)
        frames.append((W(x, z), nrm, hw, wing))
    # arc length along the spine (for the channels)
    arc = [0.0]
    for i in range(1, m):
        arc.append(arc[-1] + (frames[i][0] - frames[i - 1][0]).length)

    def surf(i, u, lift=0.0):
        """The shell's front surface at station i, across-coordinate u in -1..1, lifted along the normal."""
        c, nrm, hw, wing = frames[i]
        rise = wing * abs(u) ** 3.2
        return c + side * (u * hw) + nrm * (rise + lift)

    U = [-1.0 + 2.0 * k / 20 for k in range(21)]
    # 1) the shell: the U section with a 4.5 cm wall, its rim rounded over (a carbon-grey composite)
    rings = []
    for i in range(m):
        c, nrm, hw, wing = frames[i]
        front = [surf(i, u) for u in U]
        back = [surf(i, u * 1.02, -0.045) - nrm * 0.01 * (1 - abs(u)) for u in reversed(U)]
        lip = [surf(i, 1.0, 0.012) + side * 0.008, surf(i, 1.0, -0.02) + side * 0.016]
        lip_l = [surf(i, -1.0, -0.02) - side * 0.016, surf(i, -1.0, 0.012) - side * 0.008]
        rings.append(front + lip + back + lip_l)
    loft(g["int_seat"], rings)            # (critic / SC Aurora: a mid-grey shell, not a black one - 7. 10. 2026)

    # 2) the padding: quilted channels across the pan and up the back, each a pillowed strip with rounded ends,
    # 1.4 cm grooves between them; bolsters along both sides of the back and the pan
    def pad(i0, i1, u0, u1, bulge, base=0.004, ends=0.35, key="int_leather", stitch=False):
        rr = []
        n_u = 12
        for i in range(i0, i1 + 1):
            s_ = (arc[i] - arc[i0]) / max(arc[i1] - arc[i0], 1e-4)
            end = max(math.sin(math.pi * min(max(s_, 0.0), 1.0)), 0.02) ** ends
            top, bot = [], []
            for k in range(n_u + 1):
                u = u0 + (u1 - u0) * k / n_u
                w = (u - u0) / (u1 - u0)
                b = bulge * end * max(math.sin(math.pi * w), 0.0) ** 0.55
                top.append(surf(i, u, base + b))
                bot.append(surf(i, u, -0.004))
            rr.append(top + list(reversed(bot)))
        loft(g[key], rr)
        if stitch:
            # (critic 7. 10. r1) a light double stitch along both long edges of the channel, 9 and 13 mm in
            for uu in (u0 + (u1 - u0) * 0.06, u0 + (u1 - u0) * 0.085, u1 - (u1 - u0) * 0.085, u1 - (u1 - u0) * 0.06):
                line = []
                for i in range(i0 + 1, i1):
                    s_ = (arc[i] - arc[i0]) / max(arc[i1] - arc[i0], 1e-4)
                    end = max(math.sin(math.pi * min(max(s_, 0.0), 1.0)), 0.02) ** ends
                    w = (uu - u0) / (u1 - u0)
                    b = bulge * end * max(math.sin(math.pi * w), 0.0) ** 0.55
                    line.append(surf(i, uu, base + b + 0.0006))
                for pa, pb in zip(line, line[1:]):
                    tube(g["int_webbing"], pa, pb, 0.0006, 4)

    def at(arc_len):
        return min(range(m), key=lambda i: abs(arc[i] - arc_len))
    # channel stations by arc length from the front lip (m): pan 2, back 4, head 1
    channels = [(0.02, 0.17), (0.185, 0.33), (0.40, 0.56), (0.575, 0.72), (0.735, 0.88), (0.895, 1.02), (1.10, 1.25)]
    for a0, a1 in channels:
        i0, i1 = at(a0), at(a1)
        if i1 - i0 >= 2:
            pad(i0, i1, -0.66, 0.66, 0.042 if a0 < 1.0 else 0.05, key="int_leather_perf")   # perforated centre field
    for sgn in (-1, 1):
        # (critic 7. 10.: the sides one smooth black bolster) the back's bolster in three stitched segments
        for a0, a1 in ((0.03, 0.30), (0.40, 0.60), (0.62, 0.82), (0.84, 1.03)):
            i0, i1 = at(a0), at(a1)
            u0, u1 = (0.72, 0.97) if sgn > 0 else (-0.97, -0.72)
            pad(i0, i1, u0, u1, 0.05, ends=0.5, stitch=True)
    # the grooves' welts: a thin dark line down the middle of each gap
    for a0, a1 in channels[:-1]:
        i = at(a1 + 0.008)
        ring_pts = [surf(i, u, 0.004) for u in U[3:-3]]
        for pa, pb in zip(ring_pts, ring_pts[1:]):
            tube(g["int_dark"], pa, pb, 0.0035, 6)

    # 3) the harness: five points in dark webbing over the padding, steel adjusters, a machined rotary buckle
    def strap(points, width=0.046, thick=0.006, key="int_webbing"):   # (dark webbing: the fabric grey read cartoon blue)
        """Webbing (7. 10. 2026, critic: flat paper strips): a 6 mm band with chamfered edges, smoothed along its path
        (Catmull-Rom), a light box stitch 5 mm in from each edge."""
        pts = [Vector(q) for q in _catmull([tuple(q) for q in points], 3)] if len(points) > 2 else list(points)
        rr, st = [], ([], [])
        ch = 0.0018
        for k, p_ in enumerate(pts):
            a_, b_ = pts[max(k - 1, 0)], pts[min(k + 1, len(pts) - 1)]
            t_ = (b_ - a_).normalized()
            n_ = Vector((0, 0, 1)) if abs(t_.z) < 0.7 else Vector((1, 0, 0))
            w_ = t_.cross(n_).normalized()
            n_ = w_.cross(t_).normalized()
            hw = width / 2
            rr.append([p_ + w_ * hw, p_ + w_ * hw + n_ * (thick - ch), p_ + w_ * (hw - ch) + n_ * thick,
                       p_ - w_ * (hw - ch) + n_ * thick, p_ - w_ * hw + n_ * (thick - ch), p_ - w_ * hw])
            for side_k, sg in enumerate((1, -1)):
                st[side_k].append(p_ + w_ * (sg * (hw - 0.005)) + n_ * (thick + 0.0002))
        loft(g[key], rr)
        for line in st:
            for pa, pb in zip(line, line[1:]):
                tube(g["int_trim"], pa, pb, 0.0005, 4)

    buckle = surf(at(0.24), 0.0, 0.05)
    shoulder_i, hip_i = at(1.06), at(0.40)
    for sgn in (-1, 1):
        u = sgn * 0.27
        path = [surf(i, u, 0.056) for i in range(shoulder_i, hip_i - 1, -2)]
        # (critic 7. 10.: the webbing broke in a sharp right angle like steel strip) a soft curve down into the lock
        path += [surf(at(0.35), u * 0.8, 0.062), surf(at(0.30), u * 0.5, 0.064)]
        path.append(buckle + side * (sgn * 0.03) + Vector((0.0, 0, 0.004)))
        strap(path)
        # over the top of the back into the harness slot
        top = surf(at(1.09), u, 0.03)
        strap([top, top - frames[at(1.09)][1] * 0.07 + Vector((0, 0, 0.012))], width=0.046)
        # the adjuster on the chest and the lap belt from the hip to the buckle
        adj = surf(at(0.83), u, 0.064)
        # (a machined frame the webbing runs through, a dark bar across it, not a plain plate)
        fn_ = frames[at(0.83)][1]
        rr_ring(g["int_trim"], adj + fn_ * 0.006, side, Vector((0, 0, 1)), fn_, 0.062, 0.036, 0.007, 0.007, 0.011, 4)
        rr_slab(g["int_dark"], adj + fn_ * 0.004, side, Vector((0, 0, 1)), fn_, 0.05, 0.008, 0.003, 0.006, 2)
        rr_slab(g["int_trim"], adj + fn_ * 0.0075 - Vector((0, 0, 0.011)), side, Vector((0, 0, 1)), fn_, 0.05, 0.005, 0.0025, 0.004, 2)
        # over the bolster, not beside it, curving into the lock
        lap = [surf(at(0.42), sgn * 0.96, 0.072), surf(at(0.38), sgn * 0.86, 0.078), surf(at(0.34), sgn * 0.68, 0.074),
               surf(at(0.30), sgn * 0.45, 0.066), buckle + side * (sgn * 0.035)]
        strap(lap, width=0.05)
        rr_slab(g["accent"], surf(at(0.70), u, 0.062), side, Vector((0, 0, 1)), frames[at(0.70)][1], 0.03, 0.05, 0.004, 0.003, 2)
    # crotch strap and the buckle: a satin disc, a dark ring, the orange release tab
    strap([surf(at(0.05), 0.0, 0.03), buckle - Vector((0.03, 0, 0)) + Vector((0, 0, 0.002))], width=0.05)
    up_ = frames[at(0.24)][1]
    tube(g["int_trim"], buckle, buckle + up_ * 0.016, 0.042, 28)
    tube(g["int_dark"], buckle + up_ * 0.016, buckle + up_ * 0.02, 0.034, 24)
    tube(g["accent"], buckle + up_ * 0.02, buckle + up_ * 0.026, 0.018, 18)
    # (critic 7. 10.: "the buckle only an orange disc") four steel latch tongues into the rotary lock, a knurl ring
    for k in range(4):
        a_ = math.radians(45 + 90 * k)
        dv = side * math.cos(a_) + Vector((1, 0, 0)) * math.sin(a_)
        dv = (dv - up_ * dv.dot(up_)).normalized()
        rr_slab(g["int_trim"], buckle + dv * 0.052 + up_ * 0.012, dv.cross(up_).normalized(), dv, up_, 0.026, 0.024, 0.004, 0.005, 2)
    for k in range(24):
        a_ = 2 * math.pi * k / 24
        q = buckle + up_ * 0.0165 + (side * math.cos(a_) + up_.cross(side) * math.sin(a_)) * 0.0425
        tube(g["int_dark"], q, q + up_ * 0.003, 0.0016, 4)
    rr_slab(g["int_trim"], buckle + up_ * 0.026, side, Vector((1, 0, 0)), up_, 0.026, 0.006, 0.002, 0.004, 1)

    # (critic 7. 10. r1: the shell one smooth colour) a satin metal rail along each wing of the back, three screws
    for sgn in (-1, 1):
        ia, ib = at(0.52), at(0.95)
        for i in (ia, (ia + ib) // 2, ib):
            q = surf(i, sgn * 1.0, 0.0) + side * (sgn * 0.017)
            tube(g["int_trim"], q, q + side * (sgn * 0.004), 0.006, 12)
        pts = [surf(i, sgn * 1.0, -0.016) + side * (sgn * 0.0165) for i in range(ia, ib + 1)]
        for pa, pb in zip(pts, pts[1:]):
            tube(g["int_housing"], pa, pb, 0.012, 8)
    # (critic 7. 10. r3: no mechanical frame) a machined side frame on each wing of the back: a 6 cm plate in the
    # housing grey standing out of the shell's flank along the back, three hex bolts and a lightening slot
    for sgn in (-1, 1):
        ia, ib = at(0.42), at(1.0)
        rr = []
        for i in range(ia, ib + 1):
            o = surf(i, sgn * 1.0, -0.012) + side * (sgn * 0.02)
            p_in = surf(i, sgn * 1.0, -0.072) + side * (sgn * 0.02)
            rr.append([o, o + side * (sgn * 0.012), p_in + side * (sgn * 0.012), p_in])
        if sgn < 0:
            rr = [list(reversed(r_)) for r_ in rr]
        loft(g["int_housing"], rr)
        for i in (ia + 2, (ia + ib) // 2, ib - 2):
            q = surf(i, sgn * 1.0, -0.042) + side * (sgn * 0.033)
            tube(g["int_trim"], q, q + side * (sgn * 0.004), 0.007, 6)
        for i in range(ia + 4, ib - 3):
            q0 = surf(i, sgn * 1.0, -0.06) + side * (sgn * 0.0325)
            q1 = surf(i + 1, sgn * 1.0, -0.06) + side * (sgn * 0.0325)
            tube(g["int_dark"], q0, q1, 0.004, 6)
        for i in range(ia + 3, ib - 2, 3):                                                           # lightening holes
            q = surf(i, sgn * 1.0, -0.035) + side * (sgn * 0.0325)
            tube(g["int_dark"], q - side * (sgn * 0.001), q + side * (sgn * 0.0005), 0.009, 14)
        lv = surf(ia, sgn * 1.0, -0.04) + side * (sgn * 0.04)
        tube(g["int_trim"], lv, lv + side * (sgn * 0.008), 0.009, 14)                                 # recline lever
        tube(g["int_trim"], lv + side * (sgn * 0.006), lv + side * (sgn * 0.006) + Vector((0.07, 0, -0.03)), 0.005, 8)
        tube(g["accent"], lv + side * (sgn * 0.006) + Vector((0.07, 0, -0.03)), lv + side * (sgn * 0.006) + Vector((0.1, 0, -0.042)), 0.009, 12)
    # (critic 7. 10.: no joint between pan and back) a machined pivot hub each side where the back meets the pan:
    # a housing-grey disc, a satin cap, six bolts round it
    for sgn in (-1, 1):
        hc = surf(at(0.40), sgn * 1.0, -0.035) + side * (sgn * 0.035)
        ax_ = side * sgn
        tube(g["int_housing"], hc, hc + ax_ * 0.016, 0.05, 32)
        tube(g["int_trim"], hc + ax_ * 0.016, hc + ax_ * 0.022, 0.022, 24)
        tube(g["int_dark"], hc + ax_ * 0.022, hc + ax_ * 0.024, 0.009, 12)
        ref = Vector((1, 0, 0))
        oth = ax_.cross(ref).normalized()
        for k in range(6):
            a_ = 2 * math.pi * k / 6
            q = hc + ax_ * 0.016 + (ref * math.cos(a_) + oth * math.sin(a_)) * 0.036
            tube(g["int_trim"], q, q + ax_ * 0.004, 0.0045, 6)
    # (SC's seat: grab handles beside the headrest, the maker's mark on it) satin loops on both sides of the head,
    # the maker's mark across the headrest
    for sgn in (-1, 1):
        h0 = surf(at(1.12), sgn * 1.0, -0.01) + side * (sgn * 0.012)
        h1 = surf(at(1.30), sgn * 1.0, -0.01) + side * (sgn * 0.012)
        loop = [h0, h0 + side * (sgn * 0.045), h1 + side * (sgn * 0.045), h1]
        for pa, pb in zip(loop, loop[1:]):
            tube(g["int_trim"], pa, pb, 0.008, 10)
    hh = surf(at(1.33), 0.0, 0.056)
    stencil("maker", hh, frames[at(1.33)][1], -side, frames[at(1.33)][1].cross(-side).normalized(), 0.3, 0.2)
    # 4) the frame: spine spars behind the shell, a gas strut, the swivel post and its plinth on two floor rails
    for sgn in (-1, 1):
        sp = [surf(i, sgn * 0.82, -0.07) - frames[i][1] * 0.02 for i in range(at(0.30), at(1.12), 3)]
        for pa, pb in zip(sp, sp[1:]):
            tube(g["int_trim"], pa, pb, 0.016, 10)
        rail_a, rail_b = W(-0.30, 0.015) + side * (sgn * 0.17), W(0.30, 0.015) + side * (sgn * 0.17)
        rr_slab(g["int_dark"], (rail_a + rail_b) / 2, side, Vector((1, 0, 0)), Vector((0, 0, 1)), 0.045, 0.66, 0.006, 0.02, 2)
        rr_slab(g["int_trim"], (rail_a + rail_b) / 2 + Vector((0, 0, 0.021)), side, Vector((1, 0, 0)), Vector((0, 0, 1)), 0.016, 0.64, 0.004, 0.006, 2)
    base = W(0.0, 0.035)
    rr_slab(g["int_console"], base, side, Vector((1, 0, 0)), Vector((0, 0, 1)), 0.42, 0.46, 0.05, 0.05, 5)
    tube(g["int_trim"], W(0.0, 0.085), W(0.0, 0.27), 0.055, 24)
    tube(g["int_dark"], W(0.0, 0.27), W(0.0, 0.30), 0.12, 28)
    tube(g["int_trim"], W(0.0, 0.30), W(0.0, 0.33), 0.1, 28)
    # the gas strut from the post to the back's spar cross-bar
    hinge = surf(at(0.48), 0.0, -0.09)
    tube(g["int_trim"], W(-0.02, 0.24), (W(-0.02, 0.24) + hinge) / 2, 0.022, 14)
    tube(g["int_dark"], (W(-0.02, 0.24) + hinge) / 2, hinge, 0.013, 12)
    tube(g["int_trim"], surf(at(0.48), -0.8, -0.09), surf(at(0.48), 0.8, -0.09), 0.014, 10)
    # the height lever under the pan's right edge
    tube(g["int_trim"], surf(at(0.10), -1.0, -0.06), surf(at(0.10), -1.0, -0.06) + Vector((0.08, -0.03, -0.01)), 0.007, 8)
    tube(g["accent"], surf(at(0.10), -1.0, -0.06) + Vector((0.08, -0.03, -0.01)), surf(at(0.10), -1.0, -0.06) + Vector((0.11, -0.04, -0.012)), 0.011, 10)

    # (7. 10. 2026: no armrests on the seat - the consoles moved in to 0.43 m and are the armrests, as in SC)


# ------------------------------------------------------------------------------------------ HOTAS
# Author 25. 9. 2026 (step 5): a HOTAS-style stick and throttle on the side consoles - grip, trigger, hats and
# buttons, a rubber boot over the mechanism, where the pilot's hands rest (forearms on the consoles).

def _ring(c, fwd, side, up_, d, w, r, seg=5, groove=0.0):
    """A rounded-rectangle ring around c in the plane (fwd, side), depth d along fwd, width w along side;
    groove pushes the front face in (finger grooves)."""
    pts = []
    for u, v in rr_outline(d, w, r, seg):
        if groove and u > d / 2 - r - 1e-6:
            u -= groove
        pts.append(c + fwd * u + side * v)
    return pts


def _boot(g, base, top_r=0.018, bottom_r=0.05, h=0.07, folds=6):
    """A rubber bellows (critic 7. 10.: "a stepped cone of discs"): smooth convolutions - a sine profile sampled finely
    over a taper, 36 around, in rubber; a satin clamp ring at its foot with six screws, a narrow collar at its top."""
    rings = []
    steps = folds * 8
    for k in range(steps + 1):
        t = k / steps
        rr = bottom_r + (top_r - bottom_r) * t ** 0.85 + 0.0055 * (0.5 + 0.5 * math.cos(2 * math.pi * folds * t)) * (1.0 - 0.6 * t)
        z = base.z + h * t
        rings.append([Vector((base.x + rr * math.cos(2 * math.pi * i / 36), base.y + rr * math.sin(2 * math.pi * i / 36), z)) for i in range(36)])
    loft(g["int_rubber"], rings)
    tube(g["int_trim"], base - Vector((0, 0, 0.002)), base + Vector((0, 0, 0.007)), bottom_r + 0.008, 36)        # clamp ring
    for k in range(6):
        a_ = 2 * math.pi * (k + 0.5) / 6
        q = base + Vector(((bottom_r + 0.0045) * math.cos(a_), (bottom_r + 0.0045) * math.sin(a_), 0.007))
        tube(g["int_dark"], q, q + Vector((0, 0, 0.0015)), 0.0022, 6)
    tube(g["int_trim"], base + Vector((0, 0, h - 0.004)), base + Vector((0, 0, h + 0.006)), top_r + 0.003, 24)  # top collar


def _base_plate(g, c, w, d, label=None):
    """A satin-rimmed graphite plate with four screws on a console top (horizontal), label at its aft edge."""
    right, up, n = Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))
    rr_slab(g["int_console"], c, right, up, n, w, d, 0.01, 0.02)
    rr_ring(g["int_trim"], c + n * 0.0015, right, up, n, w, d, 0.01, 0.004, 0.003, 4)
    for su in (-1, 1):
        for sv in (-1, 1):
            q = c + right * (su * (w / 2 - 0.007)) + up * (sv * (d / 2 - 0.007))
            tube(g["int_trim"], q, q + n * 0.0035, 0.0025, 10)
    if label:
        LABELS.append({"item": label, "at": list(c + up * (-d / 2 + 0.011) + n * 0.0002), "n": list(n), "x": list(right),
                       "y": list(up), "scale": 0.45, "max_w": w - 0.03})


def hotas_stick(g, base):
    """The flight stick at base (console top): plate, collar, boot, shaft, grip leaning forward 12 deg with
    finger grooves, trigger, two hats, a red pickle button, two side buttons and a pinky lever."""
    _base_plate(g, base, 0.13, 0.13, "ck_flight")
    tube(g["int_trim"], base, base + Vector((0, 0, 0.008)), 0.056, 32)                            # collar
    _boot(g, base + Vector((0, 0, 0.008)))
    shaft0 = base + Vector((0, 0, 0.07))
    tube(g["int_trim"], shaft0, shaft0 + Vector((0, 0, 0.04)), 0.011, 16)
    lean = math.radians(12.0)
    ax = Vector((math.sin(lean), 0.0, math.cos(lean)))
    fwd = Vector((math.cos(lean), 0.0, -math.sin(lean)))
    side = Vector((0.0, 1.0, 0.0))
    g0 = shaft0 + Vector((0, 0, 0.035))
    L = 0.13
    rings = []
    for k in range(9):
        t = k / 8
        d = 0.042 + 0.01 * math.sin(math.pi * min(t / 0.8, 1.0))
        w = 0.035 + 0.006 * math.sin(math.pi * min(t / 0.8, 1.0))
        groove = 0.0035 * abs(math.sin(3 * math.pi * t)) if t < 0.72 else 0.0
        rings.append(_ring(g0 + ax * (L * t), fwd, side, ax, d, w, 0.014, 5, groove))
    loft(g["int_rubber"], rings)
    top = g0 + ax * L
    # the head: a dark slanted cap with the hats and the pickle
    rr_slab(g["int_housing"], top + ax * 0.004, side * -1, fwd, ax, 0.034, 0.046, 0.012, 0.006, 4)   # grey head (SC)
    for off, rr in ((-0.01, 0.0065), (0.012, 0.0055)):
        c = top + ax * 0.004 + fwd * off
        tube(g["int_trim"], c, c + ax * 0.008, rr, 14)                                             # hat base
        for dv in (fwd, side):
            tube(g["int_trim"], c + ax * 0.008 - dv * 0.004, c + ax * 0.008 + dv * 0.004, 0.0016, 6)   # 4-way cross
    c = top + ax * 0.002 + side * 0.012 + fwd * 0.004
    tube(g["int_red"], c, c + ax * 0.007 + side * 0.003, 0.005, 12)                                # pickle
    # trigger: a curved blade in front, under the head
    for k in range(4):
        t0, t1 = 0.62 + k * 0.05, 0.62 + (k + 1) * 0.05
        a = g0 + ax * (L * t0) + fwd * (0.03 + 0.004 * math.sin(math.pi * k / 3))
        b_ = g0 + ax * (L * t1) + fwd * (0.03 + 0.004 * math.sin(math.pi * (k + 1) / 3))
        tube(g["int_trim"], a, b_, 0.0045, 8)
    # side buttons (backlit caps) on the thumb side (inboard, towards the pilot: +y for the right-hand stick)
    for t in (0.78, 0.9):
        c = g0 + ax * (L * t) + side * 0.021 - fwd * 0.004
        # (critic 7. 10.: glowing dots read as placeholders) a satin collar, a dark domed cap, a hairline index bar
        tube(g["int_trim"], c, c + side * 0.003, 0.0068, 16)
        tube(g["int_dark"], c + side * 0.002, c + side * 0.006, 0.0052, 16)
        tube(g["int_dark"], c + side * 0.006, c + side * 0.007, 0.0042, 16)
        tube(g["int_trim"], c + side * 0.0071 - fwd * 0.003, c + side * 0.0071 + fwd * 0.003, 0.0007, 4)
    # a dark trigger blade with a satin guard loop, a rubber palm swell at the back
    for k in range(5):
        t0, t1 = 0.58 + k * 0.045, 0.58 + (k + 1) * 0.045
        a = g0 + ax * (L * t0) + fwd * (0.034 + 0.006 * math.sin(math.pi * k / 4))
        b_ = g0 + ax * (L * t1) + fwd * (0.034 + 0.006 * math.sin(math.pi * (k + 1) / 4))
        tube(g["int_dark"], a, b_, 0.0062, 10)
    ga = g0 + ax * (L * 0.52) + fwd * 0.028
    gb = g0 + ax * (L * 0.52) + fwd * 0.052
    gc_ = g0 + ax * (L * 0.84) + fwd * 0.05
    for pa, pb in ((ga, gb), (gb, gc_)):
        tube(g["int_trim"], pa, pb, 0.0028, 8)
    rr_slab(g["int_rubber"], g0 + ax * (L * 0.5) - fwd * 0.03, side, ax, -fwd, 0.04, 0.07, 0.016, 0.01, 4)
    # pinky lever at the foot of the grip
    a = g0 + ax * 0.018 + fwd * 0.026
    tube(g["int_trim"], a, a + fwd * 0.018 - ax * 0.006, 0.004, 8)


def hotas_throttle(g, base):
    """The throttle at base (console top, the lever at 30 % forward): a housing with the slot, brush strips
    and detent marks, the lever and a handle turned in towards the pilot with a thumb hat and backlit
    buttons."""
    right, up, n = Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))
    _base_plate(g, base, 0.085, 0.32, "ck_eng")
    rr_slab(g["int_dark"], base + n * 0.0016, right, up, n, 0.016, 0.24, 0.004, 0.02, 3)           # slot
    for sd in (-1, 1):                                                                             # brush strips
        rr_slab(g["int_fabric"], base + n * 0.0018 + right * (sd * 0.0065), right, up, n, 0.004, 0.24, 0.001, 0.003, 1)
    for k in range(6):                                                                             # detents
        q = base + n * 0.0017 + up * (-0.11 + k * 0.044) + right * 0.019
        rr_slab(g["accent" if k == 0 else "int_glow"], q, right, up, n, 0.012, 0.0022, 0.0005, 0.0008, 1)
    lever0 = base + up * (-0.11 + 0.3 * 0.22) + n * 0.002
    top = lever0 + Vector((-0.012, 0.0, 0.1))
    tube(g["int_trim"], lever0, top, 0.014, 16)
    tube(g["int_rubber"], lever0, lever0 + Vector((0, 0, 0.025)), 0.022, 16)                       # boot over the slot
    # handle: turned 15 deg in towards the pilot (-y: the left console is at +y), leaning back a little
    turn = math.radians(15.0)
    fwd = Vector((math.cos(turn), -math.sin(turn), 0.0))
    side = Vector((math.sin(turn), math.cos(turn), 0.0))
    ax = Vector((-0.12, 0.0, 1.0)).normalized()
    rings = []
    for k in range(7):
        t = k / 6
        d = 0.065 + 0.008 * math.sin(math.pi * t)
        w = 0.05 + 0.012 * math.sin(math.pi * min(t / 0.85, 1.0))
        rings.append(_ring(top + ax * (0.085 * t - 0.01), fwd, side, ax, d, w, 0.016, 5))
    loft(g["int_rubber"], rings)
    head = top + ax * 0.075
    rr_slab(g["int_housing"], head + ax * 0.004, side * -1, fwd, ax, 0.054, 0.066, 0.014, 0.006, 4)   # cap (SC: grey)
    # (critic 7. 10.: "a black block") a grey machined shell on the outboard flank of the grip, a satin seam line,
    # two screws - the rubber stays only where the fingers and the palm hold it
    sh_c = top + ax * 0.045 + side * 0.03
    rr_slab(g["int_housing"], sh_c, fwd, ax, side, 0.06, 0.06, 0.012, 0.006, 4)
    rr_ring(g["int_trim"], sh_c + side * 0.0005, fwd, ax, side, 0.06, 0.06, 0.012, 0.0015, 0.001, 4)
    for dv in (-0.02, 0.02):
        q = sh_c + ax * dv + side * 0.0004
        tube(g["int_trim"], q, q + side * 0.0012, 0.0022, 8)
    # thumb hat and two backlit buttons on the inboard face (towards the pilot: -side)
    face = head - side * 0.03 - ax * 0.02
    tube(g["int_trim"], face, face - side * 0.008, 0.0065, 14)
    for dv in (fwd, ax):
        tube(g["int_trim"], face - side * 0.008 - dv * 0.004, face - side * 0.008 + dv * 0.004, 0.0016, 6)
    for k, off in enumerate((-0.018, 0.018)):
        c = face + fwd * off
        tube(g["int_trim"], c, c - side * 0.003, 0.0066, 16)
        tube(g["accent" if k else "int_dark"], c - side * 0.002, c - side * 0.0065, 0.005, 16)
    # a thumb slider in a channel under the hat
    sl = face - ax * 0.02
    rr_slab(g["int_dark"], sl - side * 0.0005, fwd, ax, -side, 0.04, 0.008, 0.003, 0.003, 2)
    rr_slab(g["int_trim"], sl - side * 0.003 + fwd * 0.006, fwd, ax, -side, 0.008, 0.01, 0.002, 0.003, 2)
    # index-finger slew nub at the front
    c = head + fwd * 0.036 - ax * 0.015
    tube(g["int_trim"], c, c + fwd * 0.006, 0.0045, 10)
    # (critic 7. 10. r2: "a rounded box with dots") finger ridges down the front, a palm swell at the back, a satin
    # band under the cap, a red guarded button on top and a two-way rocker on the outboard face
    for k, h in enumerate((0.012, 0.03, 0.048)):
        q = top + ax * h + fwd * (0.036 + 0.004 * math.sin(math.pi * h / 0.085))
        tube(g["int_rubber"], q - side * 0.024, q + side * 0.024, 0.0045, 10)
    rr_slab(g["int_rubber"], top + ax * 0.035 - fwd * 0.037, side, ax, -fwd, 0.056, 0.06, 0.02, 0.012, 4)   # palm swell
    rr_slab(g["int_trim"], head - ax * 0.0035, side * -1, fwd, ax, 0.058, 0.07, 0.015, 0.003, 4)            # satin band
    cap = head + ax * 0.0045
    tube(g["int_dark"], cap, cap + ax * 0.003, 0.011, 18)
    tube(g["int_red"], cap + ax * 0.003, cap + ax * 0.008, 0.0075, 18)
    for su in (-1, 1):
        rr_slab(g["int_trim"], cap + side * (su * 0.012) + ax * 0.005, ax, fwd, side * su, 0.012, 0.022, 0.002, 0.003, 2)
    ro = head + side * 0.03 - ax * 0.012
    rr_slab(g["int_dark"], ro, fwd, ax, side, 0.026, 0.014, 0.003, 0.003, 2)
    for sv in (-1, 1):
        rr_slab(g["int_trim"], ro + fwd * (sv * 0.006) + side * 0.003, fwd, ax, side, 0.01, 0.01, 0.002, 0.003, 2)



# ------------------------------------------------------------------------------------------ SC-style armrest controls
# Author 7. 10. 2026: "the lever not good enough, the emergency button turned the wrong way and makes no sense - take
# what SC has and how they have it". SC Aurora (Docs/Kit/etalon/sc/konzole_*.jpg, kreslo_*.jpg): a stick on a chrome
# ball over a base disc ringed with black-and-white hatching, a slim flat-sided grip with a silver C-guard arching over
# its head, a perforated wrist rest behind it, a grey control block sloped towards the pilot carrying the red QNTM-style
# guarded key (a rectangular red lens under a hinged red cover) over a row of labelled rockers, and a C-shaped grab
# handle off the arm's outboard front with the maker's mark.

def _sphere(bm, c, r, nu=20, nv=12):
    rings = []
    for k in range(1, nv):
        t = math.pi * k / nv
        z, rr = -math.cos(t) * r, math.sin(t) * r
        rings.append([c + Vector((rr * math.cos(2 * math.pi * i / nu), rr * math.sin(2 * math.pi * i / nu), z)) for i in range(nu)])
    loft(bm, rings)


def _hatch_disc(g, c, r_in, r_out, k=36):
    """A flat ring of alternating dark / light wedges, each one sheared - SC's hatched stick base."""
    for i in range(k):
        a0, a1 = 2 * math.pi * i / k, 2 * math.pi * (i + 1) / k
        sh = 2 * math.pi / k * 1.2
        q = [c + Vector((r_in * math.cos(a0), r_in * math.sin(a0), 0.0)), c + Vector((r_in * math.cos(a1), r_in * math.sin(a1), 0.0)),
             c + Vector((r_out * math.cos(a1 + sh), r_out * math.sin(a1 + sh), 0.0)), c + Vector((r_out * math.cos(a0 + sh), r_out * math.sin(a0 + sh), 0.0))]
        bm = g["int_dark"] if i % 2 else g["accent"]
        vs = [bm.verts.new(p) for p in q] + [bm.verts.new(p - Vector((0, 0, 0.002))) for p in q]
        bm.faces.new(vs[3::-1])                                     # (the loop runs clockwise from above)
        for j in range(4):
            jj = (j + 1) % 4
            bm.faces.new((vs[jj], vs[j], vs[4 + j], vs[4 + jj]))


def sc_stick(g, base, label, inboard):
    """SC's stick at base (console top): a grey base plate with a hatched ring, a chrome ball and neck, a slim grip
    (dark rubber sides, a grey front plate and head, buttons under the thumb), the silver C-guard over the head.
    inboard: the unit vector towards the pilot (the thumb side)."""
    X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))
    Ym, Yp = Vector((0, -1, 0)), Vector((0, 1, 0))        # right-handed frames: (-Y) x X = Z, Y x Z = X
    side = inboard.normalized()
    rr_slab(g["int_housing"], base + Z * 0.008, Ym, X, Z, 0.15, 0.15, 0.025, 0.012, 5)                # base plate
    rr_ring(g["int_trim"], base + Z * 0.0085, Ym, X, Z, 0.15, 0.15, 0.025, 0.004, 0.002, 5)
    tube(g["int_dark"], base + Z * 0.0075, base + Z * 0.009, 0.06, 40)
    _hatch_disc(g, base + Z * 0.0105, 0.04, 0.054)
    tube(g["int_trim"], base + Z * 0.008, base + Z * 0.014, 0.033, 32)                                 # collar
    _sphere(g["int_trim"], base + Z * 0.03, 0.022)                                                      # chrome ball
    tube(g["int_trim"], base + Z * 0.045, base + Z * 0.07, 0.009, 16)                                  # neck
    for k in range(4):
        q = base + Z * 0.0085 + (side * math.cos(math.pi / 4 + k * math.pi / 2) + X * math.sin(math.pi / 4 + k * math.pi / 2)) * 0.06
        tube(g["int_trim"], q, q + Z * 0.002, 0.003, 8)
    # the grip: leaning forward 8 deg, 12 cm, a slim box with soft edges
    lean = math.radians(8.0)
    ax = (Z * math.cos(lean) + X * math.sin(lean)).normalized()
    fwd = (X * math.cos(lean) - Z * math.sin(lean)).normalized()
    g0 = base + Z * 0.07
    gc = g0 + ax * 0.06
    # body: rubber, built as a rounded slab standing along ax (front face towards fwd)
    rings = []
    for k in range(13):
        t_ = k / 12
        d_ = 0.036 + 0.012 * math.sin(math.pi * min(t_ / 0.85, 1.0))                 # front-back: the palm swell
        w_ = 0.03 + 0.006 * math.sin(math.pi * min(t_ / 0.85, 1.0))
        rings.append(_ring(g0 + ax * (0.12 * t_) + fwd * 0.002, fwd, Yp, ax, d_, w_, 0.012, 4,
                           0.0025 * abs(math.sin(3 * math.pi * t_)) if t_ < 0.6 else 0.0))
    loft(g["int_rubber"], rings)
    # the grey front plate down the grip's face and the grey head block
    rr_slab(g["int_housing"], gc + fwd * 0.0235 + ax * 0.01, Yp, ax, fwd, 0.026, 0.085, 0.009, 0.004, 4)
    head = g0 + ax * 0.122
    rr_slab(g["int_housing"], head + ax * 0.012, Ym, fwd, ax, 0.04, 0.054, 0.012, 0.022, 4)
    # the C-guard: a flat silver bar from the head's back over its top to the front, down to the trigger height
    pts = []
    for k in range(37):                                     # (12 steps read as chain links - critic eye 7. 10.)
        t = math.pi * k / 36
        pts.append(head + ax * (0.008 + 0.032 * math.sin(t)) + fwd * (-0.034 * math.cos(t)) + fwd * 0.004)
    pts.append(pts[-1] - ax * 0.035)
    for sd in (-1, 1):                                                  # a pair of flat silver bars, 2 cm apart
        for a, b in zip(pts, pts[1:]):
            tube(g["int_trim"], a + Yp * (sd * 0.009), b + Yp * (sd * 0.009), 0.0042, 8)
    tube(g["int_trim"], pts[18] - Yp * 0.011, pts[18] + Yp * 0.011, 0.004, 8)        # the bridge at the top
    # buttons on the head's top and the thumb side, a hat
    for k, off in enumerate((-0.012, 0.012)):
        c = head + ax * 0.024 + fwd * off
        tube(g["int_dark"], c, c + ax * 0.004, 0.0065, 16)
        tube(g["accent" if k else "int_trim"], c + ax * 0.004, c + ax * 0.0055, 0.0048, 16)
    th = gc + side * 0.018 + ax * 0.035
    tube(g["int_trim"], th, th + side * 0.004, 0.0068, 16)
    for dv in (fwd, ax):
        tube(g["int_trim"], th + side * 0.004 - dv * 0.004, th + side * 0.004 + dv * 0.004, 0.0016, 6)
    tr = gc + fwd * 0.046 + ax * 0.02                                                                   # trigger
    rr_slab(g["int_dark"], tr, Yp, ax, fwd, 0.016, 0.03, 0.006, 0.012, 3)
    # label on the base plate, aft of the stick, read from the seat
    stencil(label, base + Z * 0.0145 - X * 0.062, Z, Ym, X, 0.45, 0.08)
    grime(base + Z * 0.0145, Z, X, (0.16, 0.16), "smear", 0.8, wear=True)


def sc_control_block(g, c, w, h, tilt_deg, key_label, rockers):
    """The grey control block sloped towards the pilot (SC's QNTM / CYCLE CONFIGURATION block): a wedge pedestal, on its
    face the red guarded key (a rectangular red lens in a dark bezel under a hinged red cover) with its label, a row of
    labelled rockers under it, hatched corner plates, screws. c: the face's centre; the face looks aft and up."""
    t = math.radians(tilt_deg)
    n = Vector((-math.sin(t), 0.0, math.cos(t)))
    up = Vector((math.cos(t), 0.0, math.sin(t)))
    right = Vector((0.0, -1.0, 0.0))
    rr_slab(g["int_housing"], c, right, up, n, w, h, 0.01, 0.1, 4)                                      # the wedge
    rr_ring(g["int_trim"], c + n * 0.0006, right, up, n, w, h, 0.01, 0.003, 0.0015, 4)
    face = c + n * 0.0008
    # the red key: dark bezel, red lens, its lamp, the red cover hinged at the top and flipped up
    kc = face + up * (h * 0.22)
    rr_slab(g["int_dark"], kc + n * 0.004, right, up, n, 0.058, 0.04, 0.006, 0.006, 3)
    rr_slab(g["int_red"], kc + n * 0.0075, right, up, n, 0.044, 0.026, 0.004, 0.004, 3)
    rr_slab(g["int_led_o"], kc + n * 0.0078, right, up, n, 0.03, 0.004, 0.0015, 0.0005, 2)
    hinge = kc + up * 0.023 + n * 0.009
    tube(g["int_trim"], hinge - right * 0.03, hinge + right * 0.03, 0.0028, 10)
    r2, u2, n2 = _frame_tilt(right, up, n, -62.0)                     # (at -105 it read edge-on as a red stick)
    rr_slab(g["int_red"], hinge + u2 * 0.021 + n2 * 0.002, r2, u2, n2, 0.056, 0.04, 0.006, 0.003, 2)
    rr_ring(g["int_trim"], hinge + u2 * 0.021 + n2 * 0.0025, r2, u2, n2, 0.056, 0.04, 0.006, 0.002, 0.001, 2)
    LABELS.append({"item": key_label, "at": list(kc - up * 0.031 + n * 0.0002), "n": list(n), "x": list(right), "y": list(up),
                   "scale": 0.85, "max_w": w * 0.8})
    # the rockers
    k = len(rockers)
    for i, lab in enumerate(rockers):
        p = face + up * (-h * 0.3) + right * (-w * 0.32 + w * 0.64 * i / max(k - 1, 1))
        _rocker(g, p, right, up, n)
        LABELS.append({"item": lab, "at": list(p - up * 0.022 + n * 0.0002), "n": list(n), "x": list(right), "y": list(up),
                       "scale": 0.42, "max_w": w / k - 0.006})
    # hatched plates in the lower corners, four screws
    for su in (-1, 1):
        hp = face + right * (su * (w / 2 - 0.016)) + up * (h * 0.2)
        rr_slab(g["int_dark"], hp + n * 0.001, right, up, n, 0.02, 0.03, 0.002, 0.001, 2)
        stencil("hazard_subtle", hp + n * 0.0016, n, up, -right, 0.08, 0.03)
        for sv in (-1, 1):
            q = face + right * (su * (w / 2 - 0.007)) + up * (sv * (h / 2 - 0.007))
            tube(g["int_trim"], q, q + n * 0.002, 0.0024, 8)
    grime(face - up * (h * 0.2), n, up, (w * 0.8, h * 0.4), "smear", 0.8, wear=True)
    grime(c - n * 0.06 - up * (h / 2), Vector((0, 0, 1)), Vector((1, 0, 0)), (w + 0.04, 0.05), "soot", 0.9)


def grab_handle(g, a, out, up_):
    """A C-shaped grey grab handle standing off the arm's outboard front (SC's RSI handle), the maker's mark on it."""
    out, up_ = out.normalized(), up_.normalized()
    fwd = up_.cross(out).normalized()
    pts = [a, a + out * 0.07, a + out * 0.07 + fwd * 0.12, a + fwd * 0.12]
    for p, q in zip(pts, pts[1:]):
        rr_slab(g["int_housing"], (p + q) / 2 + up_ * 0.0, (q - p).normalized().cross(up_).normalized(), (q - p).normalized(), up_,
                0.034, (q - p).length + 0.034, 0.01, 0.028, 3)
    stencil("maker", a + out * 0.07 + fwd * 0.06 + up_ * 0.0002, up_, -fwd if out.y > 0 else fwd, out if out.y > 0 else -out, 0.2, 0.12)


def glass_panel(g, screen_bm, sockets, name, c, right, up, n, w, h, proud, visor=True):
    """A display as a glass panel standing proud of its mount (author 25. 9. 2026, step 3): a dark back plate
    closes the recess at c, the glass floats `proud` in front on four stand-offs, a thin satin technical frame
    (7 mm) holds its edge with a cool edge light, small clamps at the corners. The glass is the Screens part
    (M_Ship_Screen: lit content opaque, the empty glass dithered see-through - the back plate shows)."""
    # its own material (M_Ship_ScreenBack: matte, pixel animation like the page seen over it)
    rr_slab(g["int_screen_back"], c - n * 0.03, right, up, n, w + 0.03, h + 0.03, 0.018, 0.008)
    p = c + n * proud
    screen(screen_bm, sockets, name, p, right, up, n, w, h)
    # graphite, not satin: a metal frame with corner clamps read as a monitor standing on a table (critic)
    rr_ring(g["int_console"], p + n * 0.004, right, up, n, w + 0.016, h + 0.016, 0.01, 0.0075, 0.01)
    rr_ring(g["int_glow"], p + n * 0.0045, right, up, n, w + 0.004, h + 0.004, 0.005, 0.0018, 0.002)
    # a visor over the glass joins it to the dash's top edge; a cool light line under it lights the desk at night
    # (not on the centre screens: seen from the eye above them it covered their titles - 25. 9. 2026)
    if visor:
        r2, u2, n2 = _frame_tilt(right, up, n, 70.0)
        rr_slab(g["int_console"], p + up * (h / 2 + 0.018) + n * 0.02, r2, u2, n2, w + 0.05, 0.05, 0.01, 0.012, 3)
    rr_slab(g["int_glow"], p - up * (h / 2 + 0.016) + n * 0.002, right, up, n, w * 0.8, 0.003, 0.001, 0.002, 1)
    for su in (-1, 1):
        for sv in (-1, 1):
            q = p + right * (su * (w / 2 + 0.004)) + up * (sv * (h / 2 + 0.004))
            tube(g["int_trim"], q - n * (proud + 0.03), q - n * 0.006, 0.005, 8)
            rr_slab(g["int_dark"], q + n * 0.006 - right * su * 0.004 - up * sv * 0.004, right, up, n, 0.014, 0.014, 0.003, 0.01, 2)


HOLO_BM = {}        # holo MFD v4 (author 8. 10. 2026: the MFDs in the radar's holo style): "HoloField", "HoloBeam"


def _holo_quad(key, pts, uvs):
    """A quad with canvas UVs into HOLO_BM[key] (hs_interior writes them as SM_Ship_<ship>_Int_<key>, the Screens part)."""
    bm = HOLO_BM.setdefault(key, bmesh.new())
    uvl = bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for loop, uv in zip(f.loops, uvs):
        loop[uvl].uv = uv


def holo_projector(g, screen_bm, sockets, name, top, right, n, w, h, eye, holo):
    """CK-HP (cockpit v2, author 4. 10. 2026: the MFDs a hologram, not an onboard computer): an emitter bar on the
    pod's top edge - a chamfered graphite housing with a brushed cap and a lens slot of light along its top - and the
    MFD picture standing over it as light, facing the eye, with nothing behind it but the cockpit (no back plate, no
    monitor bezel). The picture is the Screens part as before; its socket keeps the Display_<name> name."""
    Z = Vector((0.0, 0.0, 1.0))
    fwd = Vector((n.x, n.y, 0.0)).normalized()
    ew, ed, eh = holo.get("emitter", [w + 0.04, 0.05, 0.045])
    base = top + fwd * (ed * 0.15)
    rr_slab(g["int_console"], base + Z * eh, right, fwd, Z, ew, ed, 0.006, eh, 2)                 # housing
    rr_slab(g["int_trim"], base + Z * (eh + 0.003), right, fwd, Z, ew - 0.012, ed - 0.012, 0.004, 0.003, 2)   # cap
    rr_slab(g["int_glow"], base + Z * (eh + 0.0045), right, fwd, Z, ew - 0.05, 0.006, 0.002, 0.002, 1)       # lens
    for su in (-1, 1):                                                                              # end caps
        q = base + right * (su * (ew / 2 - 0.008)) + Z * (eh * 0.5)
        tube(g["int_trim"], q - fwd * (ed * 0.5), q + fwd * (ed * 0.5), 0.006, 8)
    centre = base + Z * (eh + holo.get("image_gap", 0.025) + h / 2)
    r2, u2, n2 = oriented(eye, centre)
    screen(screen_bm, sockets, name, centre, r2, u2, n2, w, h)
    # holo MFD v4 (author 8. 10. 2026: "the MFDs from this" - the radar's light): an additive field of light 4 mm
    # behind the picture, 1 cm larger round it (its glowing edge, corner brackets, the rolling scan band frame
    # the page), UV (0, 0) at its lower left; and the beam - a fan of light from the lens slot up to the picture's
    # lower edge, UV v 0 at the lens
    fc, fw, fh = centre - n2 * 0.004, w + 0.02, h + 0.02
    _holo_quad("HoloField", [fc - r2 * fw / 2 - u2 * fh / 2, fc + r2 * fw / 2 - u2 * fh / 2, fc + r2 * fw / 2 + u2 * fh / 2, fc - r2 * fw / 2 + u2 * fh / 2],
               [(0, 0), (1, 0), (1, 1), (0, 1)])
    lens = base + Z * (eh + 0.0045)
    lw = ew - 0.05
    pb = centre - u2 * (h / 2) - n2 * 0.004
    _holo_quad("HoloBeam", [lens - right * lw / 2, lens + right * lw / 2, pb + r2 * w / 2, pb - r2 * w / 2],
               [(0, 0), (1, 0), (1, 1), (0, 1)])


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
    rr_ring(g["int_glow_soft"], pc + n * 0.0135, right, up, n, pw - 0.018, ph - 0.018, spec["radius"] - 0.009, 0.004, 0.003, shape=shape)
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
    # 13 cm aft of ped_x: at 10 cm the column's top front rim sat 2 cm nearer the eye than the screens' top edge
    # and cut their titles off (ray cast from the eye, 25. 9. 2026)
    hc = Vector((x0 - 0.13, 0.0, ztop - 0.075))
    hr, hu, hn = oriented(eye, hc)
    cw = spec["centre_w"]
    if spec.get("holo_mfd"):
        # holo MFD v3 (author 5. 10. 2026: the centre screens in their rounded chrome frame read as a toy tablet):
        # the column ends in an emitter bar and the RADAR / SELF STATUS pictures stand over it as light, like the MFDs
        Z = Vector((0.0, 0.0, 1.0))
        top = Vector((x0 - 0.13, 0.0, ztop))
        fwd = Vector((hn.x, hn.y, 0.0)).normalized()
        ew = 2 * cw + 0.07
        rr_slab(g["int_console"], top + Z * 0.012, hr, fwd, Z, ew, 0.07, 0.012, 0.03, 3)                    # housing
        rr_slab(g["int_trim"], top + Z * 0.0145, hr, fwd, Z, ew - 0.012, 0.058, 0.008, 0.003, 3)            # cap
        rr_slab(g["int_glow"], top + Z * 0.016, hr, fwd, Z, ew - 0.04, 0.006, 0.002, 0.002, 1)              # lens
        for su in (-1, 1):
            q = top + hr * (su * (ew / 2 - 0.008)) + Z * 0.0
            tube(g["int_trim"], q - fwd * 0.03, q + fwd * 0.03, 0.006, 8)
        if spec.get("centre_screens", True):
            for name, du, h in (("centre_top", -(cw / 2 + 0.008), cw * 259.0 / 210.0), ("centre_bottom", cw / 2 + 0.008, cw * 231.0 / 210.0)):
                c = top + hr * du + Z * (0.016 + 0.02 + h / 2)
                r2, u2, n2 = oriented(eye, c)
                screen(screen_bm, sockets, name, c, r2, u2, n2, cw, h)
        else:
            # author 8. 10. 2026: no small centre screens - a 3D holographic radar stands over the emitter instead
            # (USpaceHoloRadarComponent at this socket, toggled from interact mode)
            sockets["Control_radar"] = top + Z * 0.017
        return
    rr_slab(g["int_console"], hc - hn * 0.01, hr, hu, hn, 2 * cw + 0.09, cw * 1.35 + 0.04, 0.04, 0.06)
    rr_ring(g["int_trim"], hc + hn * 0.004, hr, hu, hn, 2 * cw + 0.09, cw * 1.35 + 0.04, 0.04, 0.012, 0.01)
    for name, du, h in (("centre_top", -(cw / 2 + 0.012), cw * 259.0 / 210.0), ("centre_bottom", cw / 2 + 0.012, cw * 231.0 / 210.0)):
        c = hc + hr * du + hn * 0.006
        glass_panel(g, screen_bm, sockets, name, c, hr, hu, hn, spec["centre_w"], h, 0.015, visor=False)
    # (the wire "holographic radar" that stood here is gone: the ship hologram replaces it, off the line of
    # sight - build_hologram; a satin cap closes the pedestal's top)
    # (no cap on top: it covered the top edge of the centre screens from the eye - critic, 25. 9. 2026)


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
    holo_lift = 0.0
    if spec.get("holo_mfd"):
        # cockpit v2: the pods sit lower, the holo picture stands over them (holo_projector)
        new_z = spec["holo_mfd"].get("pod_z", spec["pod_z"])
        sh0 = spec["screen_w"] * 490.0 / 560.0
        holo_lift = (spec["pod_z"] + sh0 / 2 + spec["top_margin"]) - (new_z + spec["holo_mfd"].get("fascia_h", 0.2) / 2)
        spec = dict(spec, pod_z=new_z)
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
        hw, hh = (sw + 0.05) / 2, (sh + 0.05) / 2
        P = lambda u, v, c=c, right=right, up=up: c + right * u + up * v
        uo, ui = (pw / 2) * (-side), (pw / 2) * side
        u_lo, u_hi = sorted((uo, ui))
        holo = spec.get("holo_mfd")
        if holo:
            # cockpit v2: a lower, closed fascia (no screen hole) with the holo projector on its top edge
            half = holo.get("fascia_h", 0.2) / 2
            vt, vb = half, -(half + holo.get("below", 0.02))
            # (1 cm past the wrap's edges: flush to them the lowered fascia left hairline gaps at its seam, GEOTEST holes)
            quads = [[P(u_lo - 0.01, vb - 0.01), P(u_hi + 0.01, vb - 0.01), P(u_hi + 0.01, vt + 0.01), P(u_lo - 0.01, vt + 0.01)]]
            # the picture is wider than the old screen (holo MFD v3: image_w, SC's 1.8 : 1); the pod stays
            iw = holo.get("image_w", sw)
            holo_projector(g, screen_bm, sockets, "left" if side > 0 else "right", P(0.0, vt), right, n, iw, iw * MFD_ASPECT, eye, holo)
            module_h = 2 * half - 0.02
        else:
            # screen in its recess, a satin bezel and a thin cool light line round the glass
            rr_ring(g["int_dark"], c, right, up, n, sw + 0.03, sh + 0.03, 0.018, 0.015, 0.035)
            rr_ring(g["int_trim"], c + n * 0.006, right, up, n, sw + 0.05, sh + 0.05, 0.03, 0.014, 0.012)
            glass_panel(g, screen_bm, sockets, "left" if side > 0 else "right", c, right, up, n, sw, sh, 0.02)
            vt, vb = sh / 2 + spec["top_margin"], -(sh / 2 + spec["top_margin"] + below)
            quads = [
                [P(u_lo, vb), P(u_hi, vb), P(u_hi, -hh), P(u_lo, -hh)],      # under the screen (key row)
                [P(u_lo, hh), P(u_hi, hh), P(u_hi, vt), P(u_lo, vt)],        # over it
                [P(u_lo, -hh), P(-hw, -hh), P(-hw, hh), P(u_lo, hh)],        # left strip
                [P(hw, -hh), P(u_hi, -hh), P(u_hi, hh), P(hw, hh)],          # right strip
            ]
            module_h = sh + 0.04
        _quad_faces(tmp, quads, eye)
        # (holo: the outer edge keeps the old pod's top height - the wrap from the side console meets the canopy
        # lining there; lowered with the fascia it left a gap along the sill, GEOTEST holes)
        # (cockpit v4 r4, critic: the raised outer edge stood as a bright fin over the MFD) outer_lift_scale lowers it
        outer_top = P(uo, vt) + Vector((0.0, 0.0, holo_lift * spec.get("outer_lift_scale", 1.0))) if holo else P(uo, vt)
        cols.append((side, "pod_outer", P(uo, vb), outer_top))
        if holo:
            # and right inside it the low edge: a vertical step outside the picture, the shelf and its trim stay low
            # over the pod (sloping from the raised edge they crossed the picture)
            cols.append((side, "pod_outer_low", P(uo * 0.995, vb), P(uo * 0.995, vt)))
        cols.append((side, "pod_inner", P(ui, vb), P(ui, vt)))
        # the outer strip: a control module (status LEDs, a rotary selector, two backlit keys); the key row under
        # the screen
        # (1 cm in from the strip's outer edge: the fascia bends back there and its far side crossed the module)
        s0 = c + right * ((hw + (pw / 2 - hw) / 2 - 0.01) * (-side)) + n * 0.004
        # every status LED has its label (unlabelled lamps read as placeholders - critic, 25. 9. 2026)
        rows = ([[("led_w", "ck_main"), ("led_o", "ck_batt"), ("led_blink", "ck_fault")], [("rotary", "ck_pwr")], [("button", "ck_eng"), ("button", "ck_shld")],
                 [("rocker", "ck_hyd"), ("rocker", "ck_o2")]]
                if side > 0 else
                [[("led_o", "ck_link"), ("led_w", "ck_trk"), ("led_blink", "ck_warn")], [("rotary", "ck_scan")], [("button", "ck_qt"), ("button", "ck_comms")],
                 [("rocker", "ck_esp"), ("rocker", "ck_ifcs")]])
        from mathutils.bvhtree import BVHTree
        placed = control_module(g, s0, right, up, n, pw / 2 - hw - 0.03, module_h, rows, tree=BVHTree.FromBMesh(tmp))
        if "ck_pwr" in placed:
            # the PWR selector as a socket (interact mode clicks it; SpaceshipPawn::GetPowerControlLocation)
            sockets["Control_pwr"] = placed["ck_pwr"] + n * 0.012
        kc = (c - up * 0.02 if holo else c - up * (hh + below * 0.5)) + n * 0.004
        # the key row (author 5. 10. 2026: the pastel pads read as plastic toys): SC's backlit keys - a satin bezel
        # strip with a recessed well per key, a dark graphite cap with a dished face, a lit legend bar along its top
        # edge, a status LED on the active ones (amber on two), separator ribs between the wells
        rr_slab(g["int_trim"], kc + n * 0.003, right, up, n, 0.37, 0.046, 0.008, 0.006, 3)
        rr_slab(g["int_dark"], kc + n * 0.0035, right, up, n, 0.36, 0.038, 0.006, 0.002, 3)
        # (cockpit v3 r1, critic: a light line under the MFD panel across its width) a cool line in a dark channel
        rr_slab(g["int_dark"], kc - up * 0.04 + n * 0.0025, right, up, n, 0.37, 0.012, 0.002, 0.002, 2)
        rr_slab(g["int_glow_soft"], kc - up * 0.04 + n * 0.0035, right, up, n, 0.35, 0.004, 0.0015, 0.0015, 2)
        for k in range(7):
            p = kc + right * (-0.15 + k * 0.05)
            rr_slab(g["int_dark"], p + n * 0.0015, right, up, n, 0.04, 0.032, 0.005, 0.005, 3)                 # the well
            rr_slab(g["int_console"], p + n * 0.0085, right, up, n, 0.034, 0.026, 0.005, 0.0075, 4)            # the cap
            rr_slab(g["int_dark"], p + n * 0.0088 - up * 0.002, right, up, n, 0.026, 0.014, 0.004, 0.0008, 3)  # its dish
            rr_slab(g["int_glow"], p + n * 0.0089 + up * 0.0095, right, up, n, 0.022, 0.0032, 0.0012, 0.0012, 2)   # legend bar
            if k in (0, 2, 3, 6):
                rr_slab(g["accent" if k in (2, 6) else "int_glow"], p + n * 0.0089 - up * 0.0095 + right * 0.012, right, up, n,
                        0.004, 0.004, 0.0018, 0.0012, 2)                                                       # status LED
            if k < 6:
                q = p + right * 0.025
                rr_slab(g["int_trim"], q + n * 0.0055, right, up, n, 0.004, 0.034, 0.001, 0.003, 1)            # rib
        if holo:
            # the fascia's broad face (critic 6. 10.: a cloudy empty slab): panel seams above and below the key row,
            # vertical breaks at the ends, bolt heads at the panels' corners
            fc = c + n * 0.0015
            for v in (0.05, -0.068):
                rr_slab(g["int_dark"], fc + up * v, right, up, n, 0.36, 0.003, 0.001, 0.002, 1)
            for u in (-0.185, 0.185):
                rr_slab(g["int_dark"], fc + right * u - up * 0.01, right, up, n, 0.003, 0.2, 0.001, 0.002, 1)
                for v in (0.075, -0.092):
                    q = c + right * (u * 0.93) + up * v
                    tube(g["int_trim"], q, q + n * 0.004, 0.0035, 8)
    L = {k: (b, t) for s, k, b, t in cols if s > 0}
    R = {k: (b, t) for s, k, b, t in cols if s < 0}
    wing = [tuple(w) for w in spec.get("wing", [(17.3, 1.13, 1.06), (17.62, 0.98, 1.22)])]   # (x, |y|, top z)
    seq = [column(x, y, zb, zt) for x, y, zt in wing]
    seq.append(L["pod_outer"])
    if "pod_outer_low" in L:
        seq.append(L["pod_outer_low"])
    pod_l = len(seq) - 1
    seq.append(L["pod_inner"])
    seq.append(column(spec["centre_x"], 0.0, zb, spec.get("centre_top_z", 1.3)))
    seq.append(R["pod_inner"])
    pod_r = len(seq) - 1
    if "pod_outer_low" in R:
        seq.append(R["pod_outer_low"])
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
        # straight forward: fanned out radially the shelf's ends ran into the cockpit walls
        f0 = f1 = Vector((1.0, 0.0, 0.0))
        tops.append([t0, t1, t1 + f1 * 0.3 + Vector((0, 0, -0.04)), t0 + f0 * 0.3 + Vector((0, 0, -0.04))])   # sloping away: the shelf stays out of the view
    for f in _quad_faces(tmp, tops, eye):
        if f.normal.z < 0:
            f.normal_flip()
    bmesh.ops.remove_doubles(tmp, verts=tmp.verts, dist=1e-4)
    bmesh.ops.solidify(tmp, geom=tmp.faces[:], thickness=0.03)
    mesh = bpy.data.meshes.new("_dash_tmp")
    tmp.to_mesh(mesh)
    # (critic 7. 10.: the lower third of the pilot's view a black mass) the dash wrap in the housing grey, like SC's
    g["int_housing"].from_mesh(mesh)
    bpy.data.meshes.remove(mesh)
    tmp.free()
    # panel breaks across the glare shield every ~25 cm and a row of bolts along its back edge (critic: empty
    # dash top - the reference has seams, bolts and layers on every surface)
    for (b0, t0), (b1, t1) in zip(seq, seq[1:]):
        span = (t1 - t0).length
        k = max(1, int(span / 0.25))
        for j in range(1, k + 1):
            q = t0.lerp(t1, j / (k + 1))
            tube(g["int_dark"], q + Vector((0.004, 0, 0.004)), q + Vector((0.26, 0, -0.03)), 0.0025, 4)
        for j in range(k * 2 + 1):
            q = t0.lerp(t1, (j + 0.5) / (k * 2 + 1)) + Vector((0.24, 0, -0.028))
            tube(g["int_trim"], q, q + Vector((0, 0, 0.004)), 0.004, 6)
    # the satin edge along the glare shield, the orange pinstripe under it, a satin lip along the bottom
    for i in range(len(seq) - 1):
        (b0, t0), (b1, t1) = seq[i], seq[i + 1]
        if i in (pod_l, pod_r):
            b0, b1 = Vector((b0.x, b0.y, zb)), Vector((b1.x, b1.y, zb))
        tube(g["int_trim"], t0, t1, 0.011, 10)
        if i not in (pod_l, pod_r):
            # (not across the MFD panels: there the strip above the glass is too narrow, the line cut the screens)
            tube(g["int_accent_glow"], t0 + Vector((0, 0, -0.03)), t1 + Vector((0, 0, -0.03)), 0.0035, 6)
        tube(g["int_trim"], b0 + Vector((0, 0, 0.004)), b1 + Vector((0, 0, 0.004)), 0.01, 10)
    # (cockpit v4 r4, critic: the fin between the console and the MFD a bare bright plate; lowering it opened the sill)
    # its face carries a graphite inset in a satin rim and a light line under its top edge, the console's language
    if holo and len(seq) > 4:
        for i0, i1 in ((1, 2), (len(seq) - 3, len(seq) - 2)):
            (fb0, ft0), (fb1, ft1) = seq[i0], seq[i1]
            nrm = (fb1 - fb0).cross(ft0 - fb0).normalized()
            if nrm.dot(Vector(eye) - fb0) < 0:
                nrm = -nrm
            P = lambda u, v, fb0=fb0, fb1=fb1, ft0=ft0, ft1=ft1: fb0.lerp(fb1, u).lerp(ft0.lerp(ft1, u), v)   # noqa: E731
            quad = [P(0.14, 0.22), P(0.86, 0.22), P(0.86, 0.78), P(0.14, 0.78)]
            cen = sum(quad, Vector()) / 4
            for key, grow, off in (("int_trim", 0.012, 0.004), ("int_dark", 0.0, 0.007)):
                pts = [q + (q - cen).normalized() * grow for q in quad]
                fr = [g[key].verts.new(q + nrm * off) for q in pts]
                bk = [g[key].verts.new(q - nrm * 0.004) for q in pts]
                g[key].faces.new(fr if (fr[1].co - fr[0].co).cross(fr[2].co - fr[0].co).dot(nrm) > 0 else fr[::-1])
                for i in range(4):
                    j = (i + 1) % 4
                    try:
                        g[key].faces.new((bk[i], bk[j], fr[j], fr[i]))
                    except ValueError:
                        pass
            tube(g["int_glow_soft"], P(0.04, 0.9) + nrm * 0.005, P(0.96, 0.9) + nrm * 0.005, 0.003, 6)
    return seq


def wing_panels(g, eye, spec):
    """Control modules on the wings of the dash, between the side consoles and the MFDs: left GEAR (guarded),
    LIGHTS, COOL; right MASTER ARM (red guard), WPN, NAV; status LEDs over them."""
    zb = spec.get("fascia_bottom_z", 0.97)
    tilt = math.tan(math.radians(spec.get("fascia_tilt_deg", 22.0)))
    wing = [tuple(w) for w in spec.get("wing", [(17.3, 1.13, 1.06), (17.62, 0.98, 1.22)])]
    for side in (1, -1):
        # (cockpit v4 r4, critic: the wing a separate bright plate) its face carries the console's language: a graphite
        # inset in a satin rim in its tall half, the console's light line along its foot to the MFD pod
        def col(x, y, zt):
            b = Vector((x, side * y, zb))
            f = Vector((x - eye[0], side * y - eye[1], 0)).normalized()
            return b, Vector((x, side * y, zt)) + f * tilt * (zt - zb)
        (b0, t0), (b1, t1) = col(*wing[0]), col(*wing[1])
        nrm = (b1 - b0).cross(t0 - b0).normalized()
        if nrm.dot(Vector(eye) - b0) < 0:
            nrm = -nrm
        P = lambda u, v: b0.lerp(b1, u).lerp(t0.lerp(t1, u), v)                     # noqa: E731
        quad = [P(0.42, 0.2), P(0.94, 0.2), P(0.94, 0.75), P(0.42, 0.75)]
        for key, grow, off in (("int_trim", 0.01, 0.003), ("int_dark", 0.0, 0.005)):
            cen = sum(quad, Vector()) / 4
            pts = [q + (q - cen).normalized() * grow for q in quad]
            fr = [g[key].verts.new(q + nrm * off) for q in pts]
            bk = [g[key].verts.new(q - nrm * 0.004) for q in pts]
            g[key].faces.new(fr if (fr[1].co - fr[0].co).cross(fr[2].co - fr[0].co).dot(nrm) > 0 else fr[::-1])
            for i in range(4):
                j = (i + 1) % 4
                try:
                    g[key].faces.new((bk[i], bk[j], fr[j], fr[i]))
                except ValueError:
                    pass
        tube(g["int_glow_soft"], P(0.02, 0.1) + nrm * 0.004, P(1.0, 0.1) + nrm * 0.004, 0.0028, 6)
        for x, y, zt in wing[1:]:
            zc = (zb + zt) / 2
            f = Vector((x - eye[0], side * y - eye[1], 0)).normalized()
            c = Vector((x + 0.1, side * (y - 0.1), zc)) + f * tilt * (zc - zb)
            # on the wing's own face (a panel squared to the eye stood half inside the sloped fascia): the face
            # the eye's ray meets, its normal, "right" level along it
            from mathutils.bvhtree import BVHTree
            tree = BVHTree.FromBMesh(g["int_console"])
            e = Vector(eye)
            hit, nrm, _, _ = tree.ray_cast(e, (c - e).normalized(), 3.0)
            if hit is not None:
                n = nrm if nrm.dot(e - hit) > 0 else -nrm
                r = Vector((0, 0, 1)).cross(n).normalized()
                u = n.cross(r).normalized()
                c = hit - n * 0.035
            else:
                r, u, n = oriented(eye, c)
            # (the ENGINE switch under a red guard beside the seat, author 5. 10. 2026: SC's power / engines triad)
            rows = ([[("guarded", "ck_gear"), ("guarded", "ck_vtol"), ("guarded_red", "ck_eng"), ("rocker", "ck_lights")],
                     [("led_o", "ck_temp"), ("button", "ck_cool"), ("button", "ck_boost"), ("button", "ck_decpl"), ("led_blink", "ck_warn")]]
                    if side > 0 else
                    [[("guarded_red", "ck_masterarm"), ("encoder", "ck_wpn"), ("rotary", "ck_nav"), ("rocker", "ck_rcs")],
                     [("led_blink", "ck_armed"), ("button", "ck_aux"), ("led_o", "ck_heat"), ("led_w", "ck_ready")]])
            placed = control_module(g, c + n * 0.035, r, u, n, 0.2, 0.15, rows, tree=tree)
            if "ck_eng" in placed and side > 0:
                # the ENGINE switch as a socket (interact mode clicks it; SpaceshipPawn::GetEngineControlLocation)
                SIDE_SOCKETS["Control_eng"] = placed["ck_eng"] + n * 0.015


def underdash(g, eye, spec, zfloor, lights_out):
    """What is under the dash instead of a black hole: support ribs, cable runs with clamps, rudder pedals,
    blue footwell lights. Returns the footwell back wall box (hs_interior gives it a kit trim texture)."""
    zb = spec.get("fascia_bottom_z", 0.97)
    xw = spec.get("footwell_back_x", 18.62)
    anchors = (-0.45, 0.0, 0.45)          # where the cable runs are held (their sag is zero there)
    for y in (-0.75, -0.45, 0.45, 0.75):
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
    for y in anchors:
        # a clamp bar across all three runs, bolted to the footwell wall
        tube(g["int_trim"], Vector((xw - 0.2, y, zb - 0.07)), Vector((xw + 0.01, y, zb - 0.07)), 0.012, 8)
        tube(g["int_trim"], Vector((xw - 0.2, y, zb - 0.07)), Vector((xw - 0.2, y, zb - 0.13)), 0.008, 6)
        # the bracket plate every run passes through
        res = bmesh.ops.create_cube(g["int_trim"], size=1.0)
        bmesh.ops.scale(g["int_trim"], vec=(0.2, 0.03, 0.1), verts=res["verts"])
        bmesh.ops.translate(g["int_trim"], vec=(xw - 0.1, y, zb - 0.1), verts=res["verts"])
    for y in (-0.2, 0.2):
        c = Vector((18.05, y, zfloor + 0.12))
        r, u, n = Vector((0, -1, 0)), Vector((0.45, 0, 0.89)).normalized(), Vector((-0.89, 0, 0.45)).normalized()
        rr_slab(g["int_console"], c, r, u, n, 0.11, 0.2, 0.02, 0.03)
        for j in range(4):
            rr_slab(g["int_trim"], c + n * 0.002 + u * (-0.06 + j * 0.04), r, u, n, 0.08, 0.008, 0.003, 0.004, 2)
        # the mechanism, visible (the pedals looked loose - critic, 25. 9. 2026): a base plate on the floor, a heel
        # hinge on two brackets, a push rod from the pedal's back to a damper on the footwell wall
        heel = c - u * 0.1 - n * 0.012
        box_c = Vector((heel.x + 0.06, y, zfloor + 0.006))
        rr_slab(g["int_console"], box_c + Vector((0, 0, 0.006)), Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), 0.15, 0.3, 0.015, 0.012, 3)
        tube(g["int_trim"], heel + Vector((0, -0.07, 0)), heel + Vector((0, 0.07, 0)), 0.012, 12)          # hinge pin
        for sd in (-1, 1):
            rr_slab(g["int_trim"], heel + Vector((0, sd * 0.06, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, sd, 0)),
                    0.05, 0.045, 0.008, 0.01, 2)                                                            # hinge bracket
        rod0 = c - n * 0.02 + u * 0.03
        rod1 = Vector((xw - 0.01, y, rod0.z + 0.04))
        tube(g["int_trim"], rod0, rod0.lerp(rod1, 0.55), 0.009, 10)
        tube(g["int_dark"], rod0.lerp(rod1, 0.5), rod1, 0.016, 12)                                        # damper
        tube(g["int_trim"], rod1 - Vector((0.01, 0, 0)), rod1 + Vector((0.01, 0, 0)), 0.03, 12)            # wall mount
    for y0, y1 in ((-0.9, -0.2), (0.2, 0.9)):
        tube(g["int_glow_soft"], Vector((spec["pod_x"] - 0.02, y0, zb - 0.02)), Vector((spec["pod_x"] - 0.02, y1, zb - 0.02)), 0.004, 6)
    lights_out.append({"at": [18.3, 0.0, zfloor + 0.35], "cd": spec.get("footwell_cd", 2.5)})
    return (xw, -0.95, zfloor), (xw + 0.04, 0.95, zb)


def build_wrap(g, screen_bm, sockets, eye, spec, zfloor, lights_out):
    dash(g, screen_bm, sockets, eye, spec, zfloor)
    for side in (1, -1):
        # the displays light the desk and the pod faces round them (cool, small, no shadow)
        # (20 cm in front of the screen at its height: 12 cm under it the light sat on the knee panel and burnt
        # two blue spots at the bottom of the pilot's view)
        lights_out.append({"at": [spec["pod_x"] - 0.2, side * spec["pod_y"], spec["pod_z"] - 0.02], "cd": spec.get("desk_light_cd", 3.0),
                           "type": "point", "color": [0.45, 0.7, 1.0], "source_radius_cm": 8.0})
    SIDE_SOCKETS.clear()
    wing_panels(g, eye, spec)
    sockets.update(SIDE_SOCKETS)
    pedestal(g, screen_bm, sockets, eye, spec)
    return underdash(g, eye, spec, zfloor, lights_out)
