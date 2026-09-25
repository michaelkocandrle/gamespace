"""Wayfarer interior inside the flying hull, built from the approved deck plan (Design/<Ship>_layout.json:
rooms, objects, doors - every object has a purpose there). Called by hs_build_ship.py; the result is the
ship part "Interior" (hs_assemble_ship groups SM_Ship_<Ship>_Int_* objects into it).

Recipe block "interior":
  height_m        clear height of the rooms (layout decks.clear_height)
  wall_inset_m    walls stand this far inside the room rectangle (the hull is outside them)
  sill_z          top of the cockpit tub; above it a liner copies the hull's inside (not the glass)
  lights          work lights per room ("per_room", "intensity_cd", "radius_m", "color")
  seat            Meshy pilot seat GLB (reused from the Steadfast kitbash), its width in metres

Look (SC architecture, warm dark base, cool UI): panelled walls over a dark backing with real gaps,
ribs at the frames, a darker kick band, ceiling panels between two light strips, floor tiles with
gaps. Objects by the layout's names (Czech, as the plan): ramp hydraulics, tractor beam holder, cargo
grid with magnetic locks, under-floor access hatches, reactor alcove, coolers, shield generator,
locker, hygiene cell, food dispenser, bunk, pilot seat, side consoles, dashboard with the game's four
screens (slot M_Ship_<Ship>_Screens, sockets Display_left / right / centre_top / centre_bottom mapped
to USpaceCockpitDisplays::ScreenRect). Materials by key: int_wall, int_panel, int_floor, int_trim,
int_dark, int_light, int_glow, int_fabric, int_leather, accent; screens their own slot.
Doorways are open (sliding leaves come with walking inside the ship).
"""
import json
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

import hs_build_part as hp

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CANVAS = (1330.0, 490.0)          # USpaceCockpitDisplays: 2 x 560 + 210 wide, 490 high
RECTS = {"left": (0, 0, 560, 490), "right": (560, 0, 1120, 490),
         "centre_top": (1120, 0, 1330, 259), "centre_bottom": (1120, 259, 1330, 490)}


class B:
    """bmeshes per material key."""
    def __init__(self):
        self.bm = {}

    def __getitem__(self, k):
        if k not in self.bm:
            self.bm[k] = bmesh.new()
        return self.bm[k]


def box(bm, lo, hi):
    lo, hi = Vector(lo), Vector(hi)
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=hi - lo, verts=res["verts"])
    bmesh.ops.translate(bm, vec=(lo + hi) / 2, verts=res["verts"])


def obox(bm, c, x, z, size):
    x = Vector(x).normalized()
    z = (Vector(z) - x * x.dot(Vector(z))).normalized()
    y = z.cross(x)
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(c)
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def cyl(bm, a, b, r, seg=20):
    a, b = Vector(a), Vector(b)
    d = b - a
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


# ------------------------------------------------------------------------------------------ shell

def panel_wall(g, x0, x1, y, z0, z1, facing, gaps=(), pitch=1.2):
    """A wall along x at y, seen from the room (facing +1: normal +y). Dark backing, panels with 8 mm gaps,
    ribs at the frames, a dark kick band; gaps = [(xa, xb, z_top)] openings."""
    t = 0.02
    back = y - facing * 0.03

    def cut(xa, xb, za, zb):
        # skip what falls into an opening
        for ga, gb, gz in gaps:
            if xa < gb and xb > ga and za < gz:
                return True
        return False
    n = max(1, int(round((x1 - x0) / pitch)))
    edges = [x0 + (x1 - x0) * k / n for k in range(n + 1)]
    for xa, xb in zip(edges, edges[1:]):
        for za, zb, key in ((z0, z0 + 0.18, "int_dark"), (z0 + 0.19, z0 + 1.1, "int_wall"), (z0 + 1.11, z1 - 0.02, "int_panel")):
            if cut(xa, xb, za, zb):
                continue
            ya, yb = sorted((y, y - facing * t))
            box(g[key], (xa + 0.004, ya, za), (xb - 0.004, yb, zb))
        # rib on the frame line
        if xa > x0 + 0.01 and not cut(xa - 0.05, xa + 0.05, z0, z1):
            ya, yb = sorted((y + facing * 0.05, y - facing * 0.02))
            box(g["int_trim"], (xa - 0.05, ya, z0), (xa + 0.05, yb, z1))
    for ga, gb, gz in gaps:
        pass
    ya, yb = sorted((back, back - facing * 0.01))
    for xa, xb in _minus((x0, x1), [(a, b) for a, b, _ in gaps]):
        box(g["int_dark"], (xa, ya, z0), (xb, yb, z1))
    for ga, gb, gz in gaps:
        box(g["int_dark"], (ga, ya, gz), (gb, yb, z1))


def _minus(span, holes):
    parts = [span]
    for h0, h1 in holes:
        out = []
        for a, b in parts:
            if h1 <= a or h0 >= b:
                out.append((a, b))
                continue
            if h0 > a:
                out.append((a, h0))
            if h1 < b:
                out.append((h1, b))
        parts = out
    return parts


def bulkhead(g, x, y0, y1, z0, z1, door, facing):
    """A cross wall at x from y0 to y1 with an open doorway (door: [yc, width] or None), framed."""
    dh = z0 + 2.05
    t = 0.04
    xa, xb = sorted((x, x + facing * t))
    spans = [(y0, y1)] if not door else _minus((y0, y1), [(door[0] - door[1] / 2, door[0] + door[1] / 2)])
    for ya, yb in spans:
        box(g["int_wall"], (xa, ya, z0), (xb, yb, z0 + 1.1))
        box(g["int_panel"], (xa, ya, z0 + 1.11), (xb, yb, z1))
    if door:
        ya, yb = door[0] - door[1] / 2, door[0] + door[1] / 2
        box(g["int_panel"], (xa, ya, dh), (xb, yb, z1))
        # frame: posts and header, proud of the wall, orange marker strip
        for yy in (ya - 0.08, yb):
            box(g["int_trim"], (xa - 0.05, yy, z0), (xb + 0.05, yy + 0.08, dh + 0.08))
        box(g["int_trim"], (xa - 0.05, ya - 0.08, dh), (xb + 0.05, yb + 0.08, dh + 0.1))
        box(g["accent"], (xa - 0.052, ya + 0.1, dh + 0.03), (xb + 0.052, yb - 0.1, dh + 0.06))
        box(g["int_dark"], (xa - 0.01, ya, z0), (xb + 0.01, yb, z0 + 0.02))   # threshold


def floor_tiles(g, x0, x1, y0, y1, z, tile=0.6, holes=()):
    box(g["int_dark"], (x0 - 0.05, y0 - 0.06, z - 0.06), (x1 + 0.05, y1 + 0.06, z - 0.02))   # under the walls: no gap
    nx, ny = max(1, int(round((x1 - x0) / tile))), max(1, int(round((y1 - y0) / tile)))
    for i in range(nx):
        for j in range(ny):
            xa, xb = x0 + (x1 - x0) * i / nx, x0 + (x1 - x0) * (i + 1) / nx
            ya, yb = y0 + (y1 - y0) * j / ny, y0 + (y1 - y0) * (j + 1) / ny
            box(g["int_floor"], (xa + 0.005, ya + 0.005, z - 0.03), (xb - 0.005, yb - 0.005, z))


def ceiling(g, x0, x1, y0, y1, z, lights):
    box(g["int_dark"], (x0, y0, z + 0.04), (x1, y1, z + 0.06))
    for (ya, yb) in ((y0, y0 + 0.35), (y1 - 0.35, y1)):
        box(g["int_panel"], (x0, ya, z), (x1, yb, z + 0.03))           # coves over the walls
    cy0, cy1 = y0 + 0.47, y1 - 0.47
    n = max(1, int(round((x1 - x0) / 1.2)))
    for k in range(n):
        xa, xb = x0 + (x1 - x0) * k / n, x0 + (x1 - x0) * (k + 1) / n
        box(g["int_panel"], (xa + 0.005, cy0, z + 0.01), (xb - 0.005, cy1, z + 0.04))
    for yy in (y0 + 0.36, y1 - 0.46):
        box(g["int_dark"], (x0, yy, z - 0.005), (x1, yy + 0.1, z + 0.035))
        box(g["int_light"], (x0 + 0.05, yy + 0.02, z - 0.01), (x1 - 0.05, yy + 0.08, z))
        for k in range(lights):
            lights_out.append({"at": [x0 + (x1 - x0) * (k + 0.5) / lights, yy + 0.05, z - 0.1]})


lights_out = []
KIT = None          # the modular kit while build() runs (hs_interior_kit.Kit), for textured procedural parts
COCKPIT = {}        # recipe interior.cockpit while build() runs


def tbox(g, key, kit_key, lo, hi, tile=0.9):
    """A box in a kit trim material when the kit is on, else in the flat interior material."""
    if KIT is not None:
        import hs_interior_kit
        hs_interior_kit.kit_box(KIT, kit_key, lo, hi, tile)
    else:
        box(g[key], lo, hi)


# ------------------------------------------------------------------------------------------ objects

def hatch(g, r, z):
    x0, x1, y0, y1 = r
    box(g["int_trim"], (x0, y0, z), (x1, y1, z + 0.006))
    box(g["int_floor"], (x0 + 0.04, y0 + 0.04, z + 0.004), (x1 - 0.04, y1 - 0.04, z + 0.01))
    box(g["accent"], (x1 - 0.14, (y0 + y1) / 2 - 0.05, z + 0.01), (x1 - 0.06, (y0 + y1) / 2 + 0.05, z + 0.02))


def obj_hydraulics(g, r, zr):
    x0, x1, y0, y1 = r
    zr = (zr[0], min(zr[1], 1.42))        # the upper mount on the wall under the chamfer (it hung in the air)
    for k in (0.3, 0.7):
        x = x0 + (x1 - x0) * k
        yc = (y0 + y1) / 2
        cyl(g["int_dark"], (x, yc, zr[0] + 0.1), (x, yc, zr[0] + 1.3), 0.06)
        cyl(g["int_trim"], (x, yc, zr[0] + 1.25), (x, yc, zr[1] - 0.1), 0.03)
        box(g["int_trim"], (x - 0.08, y0, zr[0]), (x + 0.08, y1, zr[0] + 0.1))
        box(g["int_trim"], (x - 0.08, y0, zr[1] - 0.12), (x + 0.08, y1, zr[1]))
    box(g["accent"], (x0, y0 + 0.02, 1.35), (x1, y0 + 0.03, 1.45))


def obj_tractor(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_dark"], (x0, y1 - 0.08, zr[0]), (x1, y1, zr[1]))
    box(g["int_glow"], (x0 + 0.05, y1 - 0.085, zr[1] - 0.12), (x0 + 0.2, y1 - 0.08, zr[1] - 0.06))
    cyl(g["int_trim"], ((x0 + x1) / 2, y1 - 0.2, zr[0] + 0.3), ((x0 + x1) / 2, y1 - 0.2, zr[0] + 0.75), 0.05)
    box(g["accent"], ((x0 + x1) / 2 - 0.04, y1 - 0.24, zr[0] + 0.15), ((x0 + x1) / 2 + 0.04, y1 - 0.16, zr[0] + 0.32))


def obj_cargo_grid(g, r, zr):
    x0, x1, y0, y1 = r
    for k in range(5):
        x = x0 + (x1 - x0) * k / 4
        box(g["int_trim"], (x - 0.03, y0, 0.0), (x + 0.03, y1, 0.025))
    for k in range(3):
        y = y0 + (y1 - y0) * k / 2
        box(g["int_trim"], (x0, y - 0.03, 0.0), (x1, y + 0.03, 0.025))
        for i in range(5):
            x = x0 + (x1 - x0) * i / 4
            box(g["int_dark"], (x - 0.07, y - 0.07, 0.0), (x + 0.07, y + 0.07, 0.035))
            box(g["accent"], (x - 0.03, y - 0.03, 0.035), (x + 0.03, y + 0.03, 0.04))


def obj_reactor(g, r, zr):
    x0, x1, y0, y1 = r
    s = 1 if y0 > 0 else -1
    wall = y1 if s > 0 else y0
    box(g["int_dark"], (x0, min(y0, y1), zr[0]), (x1, max(y0, y1), zr[1]))
    cyl(g["int_glow"], ((x0 + x1) / 2, (y0 + y1) / 2, zr[0] + 0.3), ((x0 + x1) / 2, (y0 + y1) / 2, zr[1] - 0.3), 0.22)
    face = y0 if s > 0 else y1
    for k in range(9):
        x = x0 + 0.05 + (x1 - x0 - 0.1) * k / 8
        box(g["int_trim"], (x - 0.015, face - 0.03, zr[0] + 0.1), (x + 0.015, face, zr[1] - 0.1))
    for zz in (zr[0] + 0.1, zr[1] - 0.12):
        box(g["int_trim"], (x0, face - 0.04, zz), (x1, face, zz + 0.04))
    box(g["accent"], (x0 + 0.1, face - 0.045, zr[1] - 0.115), (x0 + 0.5, face - 0.04, zr[1] - 0.085))   # on the top rail


def obj_cooler(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_trim"], (x0, y0, zr[0]), (x1, y1, zr[1]))
    face = y0 if y0 > 0 else y1
    s = -1 if y0 > 0 else 1
    for k in range(12):
        z = zr[0] + 0.15 + (zr[1] - zr[0] - 0.3) * k / 11
        box(g["int_dark"], (x0 + 0.05, face + s * 0.0, z), (x1 - 0.05, face + s * 0.03, z + 0.03))
    for dy in (0.15, 0.35):
        yy = (y0 + y1) / 2 + (dy - 0.25)
        cyl(g["int_trim"], ((x0 + x1) / 2, yy, zr[1]), ((x0 + x1) / 2, yy, 2.3), 0.03)


def obj_shield(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_dark"], (x0, y0, zr[0]), (x1, y1, zr[0] + 0.25))
    box(g["int_dark"], (x0, y0, zr[1] - 0.2), (x1, y1, zr[1]))
    c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, 0))
    for k in range(5):
        z = zr[0] + 0.35 + k * 0.2
        cyl(g["int_glow" if k % 2 else "int_trim"], (c.x, c.y, z), (c.x, c.y, z + 0.12), min(x1 - x0, y1 - y0) * 0.42, 28)
    cyl(g["int_trim"], (c.x, c.y, zr[0] + 0.25), (c.x, c.y, zr[1] - 0.2), 0.08)


def obj_locker(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_panel"], (x0, y0, zr[0]), (x1, y1, zr[1]))
    face = y1 if y1 < 0 else y0
    s = 1 if y1 < 0 else -1
    xm = (x0 + x1) / 2
    box(g["int_dark"], (xm - 0.004, face, zr[0] + 0.05), (xm + 0.004, face + s * 0.005, zr[1] - 0.05))
    for xh in (xm - 0.06, xm + 0.04):
        box(g["int_trim"], (xh, face, 1.0), (xh + 0.02, face + s * 0.04, 1.3))
    box(g["int_glow"], (xm + 0.12, face, 1.5), (xm + 0.3, face + s * 0.006, 1.62))


def obj_hygiene(g, r, zr):
    x0, x1, y0, y1 = r
    t = 0.05
    box(g["int_wall"], (x0, y0, 0), (x0 + t, y1, zr[1]))
    box(g["int_wall"], (x1 - t, y0, 0), (x1, y1, zr[1]))
    face = y1
    door = (x0 + x1) / 2
    for xa, xb in _minus((x0, x1), [(door - 0.4, door + 0.4)]):
        box(g["int_panel"], (xa, face - t, 0), (xb, face, zr[1]))
    box(g["int_panel"], (door - 0.4, face - t, 2.05), (door + 0.4, face, zr[1]))
    box(g["int_trim"], (door - 0.45, face, 2.05), (door + 0.45, face + 0.04, 2.13))
    box(g["int_dark"], (door - 0.4, face - 0.03, 0.02), (door + 0.4, face - 0.025, 2.04))   # closed sliding leaf
    box(g["int_glow"], (door + 0.45, face, 1.2), (door + 0.5, face + 0.01, 1.35))


def obj_food(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_panel"], (x0, y0, zr[0]), (x1, y1, zr[1]))
    face = y1
    box(g["int_dark"], (x0 + 0.2, face - 0.15, zr[0] + 0.3), (x0 + 0.7, face + 0.001, zr[0] + 0.65))
    box(g["int_light"], (x0 + 0.2, face - 0.15, zr[0] + 0.64), (x0 + 0.7, face - 0.1, zr[0] + 0.65))
    box(g["int_glow"], (x1 - 0.5, face, zr[0] + 0.5), (x1 - 0.2, face + 0.005, zr[0] + 0.75))
    box(g["int_trim"], (x0 + 0.3, face, 0.42), (x1 - 0.3, face + 0.35, 0.47))     # fold seat
    box(g["int_dark"], (x0 + 0.3, face, 0.0), (x0 + 0.35, face + 0.05, 0.42))


def obj_bunk(g, r, zr):
    x0, x1, y0, y1 = r
    box(g["int_trim"], (x0, y0, 0), (x1, y1, 0.42))
    box(g["int_fabric"], (x0 + 0.04, y0 + 0.04, 0.42), (x1 - 0.04, y1 - 0.02, 0.58))
    box(g["int_fabric"], (x1 - 0.45, y0 + 0.12, 0.58), (x1 - 0.1, y1 - 0.1, 0.66))
    for z in (1.35, 1.8):
        box(g["int_panel"], (x0, y1 - 0.35, z), (x1, y1, z + 0.03))
    box(g["int_light"], (x0 + 0.1, y1 - 0.34, 1.34), (x1 - 0.1, y1 - 0.3, 1.35))
    lights_out.append({"at": [(x0 + x1) / 2, y1 - 0.3, 1.25], "warm": True, "cd": 6})


def obj_console(g, r, zr, z0):
    x0, x1, y0, y1 = r
    top = zr[1] - 0.1
    if COCKPIT.get("style") in ("pods", "wrap"):
        # the outer edge stood 2-3 cm into the hull where the tub narrows (geometry check, 25. 9. 2026)
        if y1 > 0:
            y1 -= 0.04
        else:
            y0 += 0.04
    tbox(g, "int_dark", "kit_trim02", (x0, y0, z0), (x1, y1, top), 1.0)
    if COCKPIT.get("style") in ("pods", "wrap"):
        # a top plate inside the body with a satin rim (the old tilted plate overhung the console; its glow
        # rectangle was a placeholder and its knobs bare cylinders - control modules come from hs_cockpit)
        box(g["int_console"], (x0 + 0.03, y0 + 0.03, top), (x1 - 0.03, y1 - 0.03, top + 0.012))
        for xa, xb, ya, yb in ((x0 + 0.02, x1 - 0.02, y0 + 0.02, y0 + 0.03), (x0 + 0.02, x1 - 0.02, y1 - 0.03, y1 - 0.02),
                               (x0 + 0.02, x0 + 0.03, y0 + 0.02, y1 - 0.02), (x1 - 0.03, x1 - 0.02, y0 + 0.02, y1 - 0.02)):
            box(g["int_trim"], (xa, ya, top), (xb, yb, top + 0.016))
        # seams across the top plate and bolts round it (the plate was an empty board - critic, 25. 9. 2026)
        for f in (0.33, 0.66):
            xs = x0 + (x1 - x0) * f
            box(g["int_dark"], (xs - 0.002, y0 + 0.035, top + 0.012), (xs + 0.002, y1 - 0.035, top + 0.0135))
        for f in (0.08, 0.3, 0.5, 0.7, 0.92):
            for yy in (y0 + 0.045, y1 - 0.045):
                cyl(g["int_trim"], (x0 + (x1 - x0) * f, yy, top + 0.012), (x0 + (x1 - x0) * f, yy, top + 0.016), 0.004, 6)
        if y0 > 0:
            # the left console's module aft of the throttle: the canopy LOCK rocker and two status LEDs
            import hs_cockpit
            hs_cockpit.control_module(g, Vector((x0 + 0.32, (y0 + y1) / 2 + 0.05, top + 0.016)), Vector((0, -1, 0)), Vector((1, 0, 0)),
                                      Vector((0, 0, 1)), 0.15, 0.11, [[("led_o", None), ("led_w", None), ("led_blink", None)], [("rocker", "ck_lock"), ("guarded", "ck_canopy")]])
        return
    inner = y1 if y1 < 0 else y0
    outer = y0 if y1 < 0 else y1
    c = Vector(((x0 + x1) / 2, (inner * 0.4 + outer * 0.6), zr[1] - 0.05))
    tilt = Vector((0, 0.5 * (1 if inner > outer else -1), 1))
    obox(g["int_trim"], c, (1, 0, 0), tilt, (x1 - x0, abs(y1 - y0) * 0.95, 0.04))
    n = tilt.normalized()
    for k in range(8):
        p = c + Vector((-(x1 - x0) * 0.35 + k * (x1 - x0) * 0.1, 0, 0)) + n * 0.03
        cyl(g["int_dark"], p, p + n * 0.03, 0.012, 8)
    obox(g["int_glow"], c + Vector((0.15, 0, 0)) + n * 0.021 + Vector((0, (inner - outer) * 0.12, 0)), (1, 0, 0), tilt, (0.18, 0.12, 0.004))


def dashboard(g, r, zr, z0, ship, screen_bm, sockets, eye):
    """The instrument panel: a sloped fascia facing the pilot's eye with the game's four screens, or the
    concept-A pods (hs_cockpit.py) when recipe interior.cockpit.style is "pods"."""
    if COCKPIT.get("style") == "wrap":
        import hs_cockpit
        back = hs_cockpit.build_wrap(g, screen_bm, sockets, eye, COCKPIT, z0, lights_out)
        tbox(g, "int_dark", "kit_trim01", back[0], back[1], 0.8)      # footwell back wall, panel trim
        return
    if COCKPIT.get("style") == "pods":
        import hs_cockpit
        hs_cockpit.build(g, screen_bm, sockets, eye, COCKPIT, z0)
        return
    x0, x1, y0, y1 = r
    tbox(g, "int_dark", "kit_trim01", (x0 + 0.2, y0, z0), (x1, y1, zr[0]))   # lower body (kit panel trim)
    top = zr[1]
    fascia_c = Vector((x0 + 0.25, 0.0, (zr[0] + top) / 2))
    to_eye = (Vector(eye) - fascia_c).normalized()
    n = Vector((to_eye.x, 0, to_eye.z)).normalized()
    up = Vector((0, 0, 1)) - n * n.z
    up.normalize()
    # dark fascia: the screens are the brightest thing on the panel (readability first)
    obox(g["int_dark"], fascia_c - n * 0.03, (0, 1, 0), n, (y1 - y0, top - zr[0] + 0.1, 0.05))
    box(g["int_dark"], (x0 + 0.25, y0, top), (x1, y1, top + 0.04))            # glare shield
    right = Vector((0, -1, 0))                                                # pilot faces +x: right = -y
    # 7 cm over the fascia's middle: from the eye the screens span ~15..29 deg down, whole inside the
    # cockpit camera's view (88 deg wide) with the view level, as the author wants it (22. 9. 2026)
    screens = {"left": (-0.33, 0.07, 0.29, 0.25), "right": (0.33, 0.07, 0.29, 0.25),
               "centre_top": (0.0, 0.14, 0.11, 0.135), "centre_bottom": (0.0, -0.01, 0.11, 0.12)}
    uvl = screen_bm.loops.layers.uv.get("UVMap") or screen_bm.loops.layers.uv.new("UVMap")
    for name, (u, v, w, h) in screens.items():
        c = fascia_c + right * u + up * v + n * 0.002
        # bezel
        obox(g["int_trim"], c - n * 0.001, right, n, (w + 0.04, h + 0.04, 0.012))
        cs = [c + right * (-w / 2) + up * (-h / 2), c + right * (w / 2) + up * (-h / 2),
              c + right * (w / 2) + up * (h / 2), c + right * (-w / 2) + up * (h / 2)]
        cs = [p + n * 0.007 for p in cs]
        vs = [screen_bm.verts.new(p) for p in cs]
        f = screen_bm.faces.new(vs)
        rx0, ry0, rx1, ry1 = RECTS[name]
        W, H = CANVAS
        uvs = [(rx0 / W, 1 - ry1 / H), (rx1 / W, 1 - ry1 / H), (rx1 / W, 1 - ry0 / H), (rx0 / W, 1 - ry0 / H)]
        for loop, uv in zip(f.loops, uvs):
            loop[uvl].uv = uv
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()
        sockets[name] = c + n * 0.03
    # soft keys under the side screens and a toggle row over them (real buttons around the displays, as in
    # the reference cockpits; small and dim, so the screens stay the brightest thing on the panel)
    for u0 in (-0.33, 0.33):
        for k in range(6):
            c = fascia_c + right * (u0 - 0.125 + k * 0.05) + up * (-0.105) + n * 0.004
            obox(g["int_dark"], c, right, n, (0.034, 0.026, 0.012))
            obox(g["int_glow" if k in (0, 3) else "int_trim"], c + n * 0.007, right, n, (0.026, 0.018, 0.004))
    for k in range(12):
        c = fascia_c + right * (-0.44 + k * 0.08) + up * 0.245 + n * 0.004
        obox(g["int_dark"], c, right, n, (0.03, 0.03, 0.01))
        cyl(g["int_trim"], c, c + n * 0.03 + up * 0.008, 0.005, 6)
        if k % 4 == 1:
            obox(g["accent"], c + up * -0.022 + n * 0.006, right, n, (0.012, 0.006, 0.003))


# ------------------------------------------------------------------------------------------ main

def _hull_top(hull):
    """The hull's inside height at x on the centre line (a ray up from the cabin)."""
    from mathutils.bvhtree import BVHTree
    hb = bmesh.new()
    hb.from_mesh(hull.data)
    hb.transform(hull.matrix_world)
    tree = BVHTree.FromBMesh(hb)
    hb.free()

    def top(x, y=0.0):
        hit = tree.ray_cast(Vector((x, y, 1.2)), Vector((0, 0, 1)), 5.0)[0]
        return hit.z if hit is not None else 9.0
    return top


def stairs(g, fb, floor_faces, zc, x0=15.24, half_w=0.5, rise_max=0.195, tread=0.18):
    """Steep ship's stairs from the cabin's deck up to the raised cockpit floor (zc), through the rear wall's door
    (the cockpit sits 1.15 m up so the pilot's eye is in the canopy's glass band, step 2 of the author's view
    targets 25. 9. 2026). Solid blocks with a satin tread plate and a lit nosing on each step, closed side walls
    under the floor's ledges, a handrail on both sides. The floor slab is cut open over the flight."""
    n = int(math.ceil(zc / rise_max))
    rise = zc / n
    x_top = x0 + (n - 1) * tread
    # open the floor over the flight: cut at the top riser and the flight's sides, drop what lies over it
    geom = list({v for f in floor_faces for v in f.verts}) + list({e for f in floor_faces for e in f.edges}) + list(floor_faces)
    for co, no in (((x_top, 0, 0), (1, 0, 0)), ((0, half_w, 0), (0, 1, 0)), ((0, -half_w, 0), (0, 1, 0))):
        geom = list(dict.fromkeys(el for el in geom if el.is_valid))
        r = bmesh.ops.bisect_plane(fb, geom=geom, dist=1e-5, plane_co=co, plane_no=no)
        geom = geom + r["geom"]
    drop = [f for f in {el for el in geom if isinstance(el, bmesh.types.BMFace) and el.is_valid}
            if f.calc_center_median().x < x_top and abs(f.calc_center_median().y) < half_w]
    bmesh.ops.delete(fb, geom=drop, context="FACES")
    for i in range(n):
        xa, xb = x0 + i * tread, x0 + (i + 1) * tread
        zt = (i + 1) * rise
        if i == n - 1:
            # the top riser: the floor slab's edge, closed down to the deck
            box(g["int_dark"], (x_top, -half_w, 0.0), (x_top + 0.04, half_w, zc - 0.03))
            break
        box(g["int_dark"], (xa, -half_w, 0.0), (xb, half_w, zt - 0.02))
        box(g["int_trim"], (xa, -half_w + 0.01, zt - 0.02), (xb, half_w - 0.01, zt))            # tread plate
        box(g["int_glow"], (xa - 0.004, -half_w + 0.06, zt - 0.016), (xa, half_w - 0.06, zt - 0.006))   # lit nosing
        box(g["accent"], (xa, -half_w + 0.01, zt), (xa + 0.035, half_w - 0.01, zt + 0.002))       # hazard edge
    for sd in (1, -1):
        # side walls under the floor's ledges, and the handrail on posts along the pitch
        ya, yb = sorted((sd * half_w, sd * (half_w + 0.03)))
        box(g["int_panel"], (x0, ya, 0.0), (x_top + 0.04, yb, zc))
        yr = sd * (half_w - 0.05)
        p0 = Vector((x0 + 0.05, yr, rise + 0.9))
        p1 = Vector((x_top + 0.1, yr, zc + 0.9))
        cyl(g["int_trim"], p0, p1, 0.02, 12)
        for q in (p0, p1, p0.lerp(p1, 0.5)):
            # vertical posts down to the tread (or the cockpit floor) under them, with a foot flange: the upper
            # posts used to end on the side wall above its top - hanging in the air (critic, 25. 9. 2026)
            i = int((q.x - x0) / tread)
            zt = zc if i >= n - 1 else (i + 1) * rise
            cyl(g["int_trim"], Vector((q.x, yr, zt)), q, 0.012, 8)
            cyl(g["int_trim"], Vector((q.x, yr, zt)), Vector((q.x, yr, zt + 0.006)), 0.03, 12)


def _gable(bm, hull, x, z0, g=None):
    """Closes a cross wall from its top (z0) up to the hull's section at x, facing +x: over the cockpit's rear
    wall the view met the cabin roof's culled inside (geometry check, 25. 9. 2026). A fan of rays in the
    y-z plane finds the section; the panel stops 1.5 cm inside it."""
    from mathutils.bvhtree import BVHTree
    hb = bmesh.new()
    hb.from_mesh(hull.data)
    hb.transform(hull.matrix_world)
    tree = BVHTree.FromBMesh(hb)
    hb.free()
    c = Vector((x, 0.0, z0))
    ring = []
    for i in range(31):
        a = math.radians(6.0 * i)
        d = Vector((0.0, round(math.cos(a), 6), round(math.sin(a), 6)))
        hit = tree.ray_cast(c, d, 5.0)[0]
        if hit is None:
            return
        ring.append(c + d * max((hit - c).length - 0.015, 0.0))
    vs = [bm.verts.new(c)] + [bm.verts.new(p) for p in ring]
    new = []
    for i in range(1, len(vs) - 1):
        # counter-clockwise seen from +x: the face looks into the cockpit
        new.append(bm.faces.new((vs[0], vs[i], vs[i + 1])))
    ext = bmesh.ops.extrude_face_region(bm, geom=new)
    bmesh.ops.translate(bm, vec=(-0.02, 0.0, 0.0), verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=list(set(new) | {e for e in ext["geom"] if isinstance(e, bmesh.types.BMFace)}))
    if g is None:
        return
    # structure on it, not a bare plane (a plain dark rear wall, author 25. 9. 2026): satin ribs up to the hull,
    # a beam across, a dark recess between the middle ribs
    for yy in (-1.25, -0.65, 0.0, 0.65, 1.25):
        hit = tree.ray_cast(Vector((x, yy, z0)), Vector((0.0, 0.0, 1.0)), 5.0)[0]
        if hit is None or hit.z - z0 < 0.12:
            continue
        box(g["int_trim"], (x, yy - 0.03, z0), (x + 0.035, yy + 0.03, hit.z - 0.07))
    hb_ = tree.ray_cast(Vector((x, 0.0, z0)), Vector((0.0, 0.0, 1.0)), 5.0)[0]
    if hb_ is not None and hb_.z - z0 > 0.5:
        zb = z0 + 0.35
        wy = [tree.ray_cast(Vector((x, 0.0, zb)), Vector((0.0, sd, 0.0)), 5.0)[0] for sd in (1, -1)]
        if all(wy):
            box(g["int_trim"], (x, -abs(wy[1].y) + 0.03, zb - 0.04), (x + 0.045, abs(wy[0].y) - 0.03, zb + 0.04))
            box(g["accent"], (x + 0.045, -abs(wy[1].y) + 0.05, zb - 0.006), (x + 0.048, abs(wy[0].y) - 0.05, zb + 0.006))
        box(g["int_dark"], (x + 0.001, -0.6, z0 + 0.06), (x + 0.012, 0.6, zb - 0.07))


MATS = {}


def build(recipe, layout, coll, mats, ship, hull):
    MATS.clear()
    MATS.update(mats)
    spec = recipe["interior"]
    H = spec.get("height_m", 2.3)
    inset = spec.get("wall_inset_m", 0.05)
    g = B()
    lights_out.clear()
    import hs_cockpit
    hs_cockpit.LABELS.clear()
    rooms = {r["id"]: r for r in layout["rooms"]}
    doors = layout["doors"]
    report = {"rooms": [], "objects": 0}
    kit_rooms = (spec.get("kit") or {}).get("rooms", [])
    kit = None
    global KIT, COCKPIT
    KIT = None
    COCKPIT = spec.get("cockpit", {})
    if kit_rooms:
        import hs_interior_kit
        kit = KIT = hs_interior_kit.Kit()
        hs_interior_kit.preview_materials(mats)
        report["kit"] = {}
    door_xs = [d["at"][0] for d in doors if d["axis"] == "x"]
    for rid, r in rooms.items():
        x0, x1, y0, y1 = r["rect"]
        z0 = r.get("floor_z", 0.0)
        if rid == "cockpit":
            continue
        y0i, y1i = y0 + inset, y1 - inset
        if rid in kit_rooms:
            # the SC-like structure from the modular kit (hs_interior_kit.py)
            report["kit"][rid] = hs_interior_kit.shell(kit, g, box, obox, r, spec, H, y1i, lights_out, door_xs, _hull_top(hull))
            report["rooms"].append(rid)
            continue
        floor_tiles(g, x0, x1, y0i, y1i, z0)
        ceiling(g, x0, x1, y0i, y1i, H, spec["lights"].get("per_room", 2))
        panel_wall(g, x0, x1, y1i, z0, H, -1)
        panel_wall(g, x0, x1, y0i, z0, H, +1)
        report["rooms"].append(rid)
    # cross walls with the layout's doors
    xs = sorted({r["rect"][0] for r in rooms.values()} | {r["rect"][1] for r in rooms.values() if r["id"] != "cockpit"})
    y0i, y1i = -1.9 + inset, 1.9 - inset
    for x in xs:
        if x > 15.3:
            continue
        d = next((dd for dd in doors if dd["axis"] == "x" and abs(dd["at"][0] - x) < 0.01), None)
        if abs(x - 1.0) < 0.01:
            # the ramp's inside: a closed leaf with ribs (the ramp opens with walking inside the ship)
            box(g["int_dark"], (x - 0.05, y0i, 0), (x, y1i, H))
            box(g["int_panel"], (x, -1.3, 0.02), (x + 0.03, 1.3, 2.1))
            for yy in (-0.9, -0.3, 0.3, 0.9):
                box(g["int_trim"], (x + 0.03, yy - 0.04, 0.05), (x + 0.07, yy + 0.04, 2.05))
            box(g["accent"], (x + 0.03, -1.3, 2.1), (x + 0.05, 1.3, 2.16))
            continue
        bulkhead(g, x, y0i, y1i, 0.0, H, (d["at"][1], d["width"]) if d else None, 1)
        if kit is not None:
            # kit panels on the faces that look into kit rooms
            ks = next(iter(report["kit"].values()))["scale"]
            for rid in kit_rooms:
                rx0, rx1 = rooms[rid]["rect"][0], rooms[rid]["rect"][1]
                if abs(rx1 - x) < 0.01:
                    hs_interior_kit.clad_bulkhead(kit, x - 0.005, -1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H)
                if abs(rx0 - x) < 0.01:
                    hs_interior_kit.clad_bulkhead(kit, x + 0.045, 1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H)
            if abs(x - rooms["cockpit"]["rect"][0]) < 0.01:
                # the cockpit's rear wall: kit panels over the plain bulkhead and a satin beam where it meets the
                # frame lining (a large dark plane under the rear window, author 25. 9. 2026)
                # (from the deck: the cockpit floor is raised and the stairs show the wall down to it)
                hs_interior_kit.clad_bulkhead(kit, x + 0.045, 1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H)
                box(g["int_trim"], (x + 0.04, y0i, H - 0.06), (x + 0.12, y1i, H))
                _gable(g["int_panel"], hull, x + 0.04, H, g)
    # cockpit: floor, step, tub walls to the sill, rear wall, liner above the sill
    ck = rooms["cockpit"]
    zc = ck["floor_z"]
    poly = ck["poly"]
    sill = spec.get("sill_z", 1.05)
    fb = g["int_floor"]
    top = [fb.verts.new((p[0], p[1], zc)) for p in poly]
    res = bmesh.ops.contextual_create(fb, geom=top)
    # a closed slab, not a single face: finish() recalculates normals, and a lone face came out facing down -
    # culled, the pilot's feet stood over the terrain seen through the hull (25. 9. 2026)
    ext = bmesh.ops.extrude_face_region(fb, geom=res["faces"])
    bmesh.ops.translate(fb, vec=(0, 0, -0.03), verts=[v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)])
    stairs(g, fb, res["faces"] + [e for e in ext["geom"] if isinstance(e, bmesh.types.BMFace)], zc)
    # the tub follows the plan's outline, but the hull is narrower than the plan in places at sill height: clamp
    # every corner inside the hull (a sill trim ran through the wall there, author 25. 9. 2026)
    from mathutils.bvhtree import BVHTree
    hb = bmesh.new()
    hb.from_mesh(hull.data)
    hb.transform(hull.matrix_world)
    htree = BVHTree.FromBMesh(hb)
    hb.free()

    def inside_hull(pt, z):
        x, y = pt
        if abs(y) < 0.3:
            return pt
        sgn = 1 if y > 0 else -1
        hit = htree.ray_cast(Vector((x, 0.0, z)), Vector((0.0, sgn, 0.0)), 5.0)[0]
        if hit is not None and abs(y) > abs(hit.y) - 0.07:
            return (x, sgn * (abs(hit.y) - 0.07))
        return pt
    tub = [inside_hull(p, sill - 0.01) for p in poly]
    for a, b in zip(tub, tub[1:]):
        pa, pb = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
        d = pb - pa
        length = d.length
        nrm = Vector((-d.y, d.x, 0)).normalized()
        if nrm.dot(Vector((17.3, 0, 0)) - pa) < 0:
            nrm = -nrm
        c = (pa + pb) / 2 + nrm * 0.03
        if kit is not None and not COCKPIT.get("style") == "wrap":
            # quilted charcoal padding on the tub (the reference's cockpit side walls)
            hs_interior_kit.kit_obox(kit, "kit_padded_grey", (c.x, c.y, (zc + sill) / 2), d, (0, 0, 1), (length, 0.04, sill - zc), 0.5)
        else:
            # graphite panels with a horizontal seam and a satin kick strip (the kit's quilted padding read as
            # scaffolding through the canopy glass - critic, 25. 9. 2026)
            obox(g["int_console"], (c.x, c.y, (zc + sill) / 2), d, (0, 0, 1), (length, 0.04, sill - zc))
            obox(g["int_dark"], (c.x + nrm.x * 0.021, c.y + nrm.y * 0.021, zc + (sill - zc) * 0.55), d, (0, 0, 1), (length, 0.003, 0.008))
            obox(g["int_trim"], (c.x + nrm.x * 0.022, c.y + nrm.y * 0.022, zc + 0.06), d, (0, 0, 1), (length, 0.006, 0.1))
        obox(g["int_trim"], (c.x, c.y, sill), d, (0, 0, 1), (length, 0.08, 0.03))
        # the sill shelf from the tub out to the hull (the tub is clamped inside the hull: the view slipped
        # through the gap between its top and the frame lining)
        caps = []
        for p_ in (pa, pb):
            sgn = 1 if p_.y > 0 else -1
            # the hull narrows upwards: the nearest of the shelf's bottom and top heights, 1.5 cm inside it
            hits = [htree.ray_cast(Vector((p_.x, 0.0, z_)), Vector((0.0, sgn, 0.0)), 5.0)[0] for z_ in (sill - 0.02, sill + 0.005)]
            hy = min(abs(h.y) for h in hits) if all(h is not None for h in hits) else None
            # (to the frame lining 3 cm inside the hull, not behind it)
            caps.append(Vector((p_.x, sgn * (hy - 0.035), sill)) if hy is not None and abs(p_.y) > 0.3 else None)
        if all(caps) and (pa.y > 0) == (pb.y > 0):
            q = [Vector((pa.x, pa.y, sill)), Vector((pb.x, pb.y, sill)), caps[1], caps[0]]
            fb2 = g["int_console"]
            vs = [fb2.verts.new(v) for v in q] + [fb2.verts.new(v - Vector((0, 0, 0.02))) for v in q]
            for idx in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                try:
                    fb2.faces.new([vs[i] for i in idx])
                except ValueError:
                    pass
        if COCKPIT.get("style") in ("pods", "wrap"):
            # the orange line along the sill (concept A: the accent runs round the cockpit at console height)
            obox(g["int_accent_glow" if "int_accent_glow" in MATS else "accent"], (c.x, c.y, sill - 0.035), d, (0, 0, 1), (length, 0.086, 0.012))
    report["cockpit"] = True
    # every layout object by its name
    eye = recipe["assemble"]["sockets"]["Cockpit"]["location"]
    screen_bm = bmesh.new()
    sockets = {}
    for o in layout["objects"]:
        x0, x1, y0, y1 = o["rect"]
        zr = o.get("z", [0.0, 1.0])
        name = o["name"]
        if o.get("below"):
            z = rooms[o["room"]].get("floor_z", 0.0)
            hatch(g, (x0, x1, y0, y1), z + 0.001)
        elif "Hydraulika" in name:
            obj_hydraulics(g, (x0, x1, y0, y1), zr)
        elif "paprsek" in name:
            obj_tractor(g, (x0, x1, y0, y1), zr)
        elif "mřížka" in name:
            obj_cargo_grid(g, (x0, x1, y0, y1), zr)
        elif "Reaktor" in name:
            obj_reactor(g, (x0, x1, y0, y1), zr)
        elif "Chladič" in name:
            obj_cooler(g, (x0, x1, y0, y1), zr)
        elif "štítů" in name:
            obj_shield(g, (x0, x1, y0, y1), zr)
        elif "Skříň" in name:
            obj_locker(g, (x0, x1, y0, y1), zr)
        elif "Hygienick" in name:
            obj_hygiene(g, (x0, x1, y0, y1), zr)
        elif "Výdejník" in name:
            obj_food(g, (x0, x1, y0, y1), zr)
        elif "Lůžko" in name:
            obj_bunk(g, (x0, x1, y0, y1), zr)
        elif "konzole" in name:
            obj_console(g, (x0, x1, y0, y1), zr, zc)
        elif "Přístrojová" in name:
            dashboard(g, (x0, x1, y0, y1), zr, zc, ship, screen_bm, sockets, eye)
        elif "křeslo" in name:
            if COCKPIT.get("style") == "wrap":
                # procedural, like the exterior: no AI geometry in the ship (author, 25. 9. 2026)
                import hs_cockpit
                hs_cockpit.pilot_seat(g, (x0, x1, y0, y1), zr)
            else:
                seat(coll, mats, spec, (x0, x1, y0, y1), zr)
        else:
            continue
        report["objects"] += 1
    if kit is not None:
        hs_interior_kit.fittings(kit, g, box, spec, lights_out)
        cockpit_detail(g, layout, zc, sill)
    holo_centre = None
    if COCKPIT.get("hologram") and "int_console" in g.bm:
        # (here, while the dash's bmesh still exists - finish() frees it)
        from mathutils.bvhtree import BVHTree
        at = Vector(COCKPIT["hologram"]["at"])
        hit = BVHTree.FromBMesh(g["int_console"]).ray_cast(at + Vector((0, 0, 0.4)), Vector((0, 0, -1)), 1.0)[0]
        holo_centre = Vector((at.x, at.y, (hit.z if hit is not None else at.z) + 0.065))
    objs = []
    if kit is not None:
        objs += kit.objects(ship, coll, mats)
        report["kit"]["pieces"] = kit.used
    bevel = {"angle_deg": 30, "width": 0.004, "segments": 2}
    for key, bm in g.bm.items():
        if not bm.verts:
            continue
        ob = hp.finish(bm, "SM_Ship_%s_Int_%s" % (ship, key), coll, bevel)
        ob.data.materials.append(mats[key])
        objs.append(ob)
    if screen_bm.faces:
        me = bpy.data.meshes.new("SM_Ship_%s_Int_Screens" % ship)
        screen_bm.to_mesh(me)
        screen_bm.free()
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
        m = bpy.data.materials.get("M_Ship_%s_Screens" % ship) or bpy.data.materials.new("M_Ship_%s_Screens" % ship)
        me.materials.append(m)
        objs.append(ob)
    # liner: the hull's inside above the cockpit sill, where there is no glass (a hull seen from inside is
    # culled - the sky would show through it)
    lb = bmesh.new()
    src = bmesh.new()
    src.from_mesh(hull.data)
    vmap = {}
    hull_src = {}
    # the rest of the interior gets a dark inner skin 5 cm inside the hull: every gap between the rooms'
    # pieces (ceiling edges, wall joints, over the cockpit's rear wall) showed the sky through the hull's
    # culled inside (geometry check, 25. 9. 2026)
    db = bmesh.new()
    dmap = {}
    for f in src.faces:
        c = f.calc_center_median()
        # (faces reaching into the cockpit belong to its lining - by vertices, not centres: large hull faces
        # left slits at the sill and the rear corner)
        # (overlapping the cockpit lining's region by a face: at the boundary one hull face fell in neither)
        in_ck = min(v.co.x for v in f.verts) >= 15.2 and max(v.co.z for v in f.verts) > sill - 0.05
        if 1.0 <= c.x and not in_ck and c.z > -0.1 and abs(c.y) < 2.4:
            vs = []
            for v in f.verts:
                if v.index not in dmap:
                    dmap[v.index] = db.verts.new(v.co - v.normal * 0.05)
                vs.append(dmap[v.index])
            try:
                db.faces.new(vs[::-1])
            except ValueError:
                pass
    for f in src.faces:
        c = f.calc_center_median()
        # the whole nose too: beyond x 19.6 the pilot looked through the dash dip at the hull's culled inside -
        # the terrain showed through what looked like a lower window (geometry check, 25. 9. 2026)
        # and the roof just aft of the cockpit's rear wall: over the 2.3 m wall the view met the cabin roof's
        # culled inside
        if max(v.co.x for v in f.verts) >= 15.2 and max(v.co.z for v in f.verts) > sill - 0.05 and abs(c.y) < 2.4:
            vs = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = lb.verts.new(v.co - v.normal * 0.03)
                    hull_src[vmap[v.index]] = v.co.copy()
                vs.append(vmap[v.index])
            try:
                nf = lb.faces.new(vs[::-1])
            except ValueError:
                pass
    src.free()
    # a metal rim along every edge where the liner meets the glass: the frame reads as built structure
    lb.edges.ensure_lookup_table()
    # rims and pinstripes only where the liner meets the glass - not where it merely ends at the cut region's
    # limits (a grey line hung across the window seen from the nose, author 25. 9. 2026)
    cano = bpy.data.objects.get("SM_Ship_%s_Canopy" % ship)
    ctree = None
    if cano is not None:
        from mathutils.bvhtree import BVHTree
        cb = bmesh.new()
        cb.from_mesh(cano.data)
        cb.transform(cano.matrix_world)
        ctree = BVHTree.FromBMesh(cb)
        cb.free()

    def at_glass(a, b):
        if ctree is None:
            return True
        for t in (0.25, 0.5, 0.75):
            loc, _, _, dist = ctree.find_nearest(a.lerp(b, t))
            if loc is None or dist > 0.07:
                return False
        return True
    from mathutils.bvhtree import BVHTree as _BVH
    lb.faces.ensure_lookup_table()
    for f in lb.faces:
        f.normal_update()
    ltree = _BVH.FromBMesh(lb)

    def on_liner(p, lift):
        # the lining is curved: a point offset in a straight line leaves it - put it back on the surface
        loc, nrm, idx, dist = ltree.find_nearest(p)
        if loc is None:
            return p
        n_ = lb.faces[idx].normal
        return loc + n_ * lift
    lb.verts.ensure_lookup_table()
    hull_pt = {v: hull_src.get(v, v.co) for v in lb.verts}     # keyed by vertex: new bmesh verts have index -1
    reveal = []
    rim = bmesh.new()
    stripe = bmesh.new()
    inset = COCKPIT.get("pinstripe_inset_m", 0.07)
    for e in lb.edges:
        if len(e.link_faces) == 1 and (e.verts[0].co - e.verts[1].co).length > 0.01:
            # the window reveal: a band from the lining's edge out to the hull, closing the 3 cm gap the view
            # slipped through beside the glass - along every open edge (hairlines of sky along the frame where
            # an edge sat just over at_glass's 7 cm, geometry check 25. 9. 2026)
            ha, hb_ = hull_pt[e.verts[0]], hull_pt[e.verts[1]]
            reveal.append((e.verts[0].co.copy(), e.verts[1].co.copy(), hb_ + (hb_ - e.verts[1].co) * 0.1, ha + (ha - e.verts[0].co) * 0.1))
        if len(e.link_faces) == 1 and (e.verts[0].co - e.verts[1].co).length > 0.01 and at_glass(e.verts[0].co, e.verts[1].co):
            f = e.link_faces[0]
            f.normal_update()
            _rim(rim, on_liner(e.verts[0].co, 0.014), on_liner(e.verts[1].co, 0.014), 0.01)
            if COCKPIT.get("style") in ("pods", "wrap"):
                # an orange pinstripe running parallel to the glass edge on the frame (concept A)
                a, b = e.verts[0].co, e.verts[1].co
                along = (b - a).normalized()
                inward = f.calc_center_median() - (a + b) / 2
                inward = (inward - along * inward.dot(along) - f.normal * inward.dot(f.normal)).normalized()
                _rim(stripe, on_liner(a + inward * inset, 0.004), on_liner(b + inward * inset, 0.004), 0.0035)
    if COCKPIT.get("style") in ("pods", "wrap"):
        # panel seams across the frame lining: cuts at fixed stations, a dark groove along each cut
        cut = lb.copy()
        for x in COCKPIT.get("seam_x", []):
            res = bmesh.ops.bisect_plane(cut, geom=cut.verts[:] + cut.edges[:] + cut.faces[:], plane_co=(x, 0, 0), plane_no=(1, 0, 0))
            for el in res["geom_cut"]:
                if isinstance(el, bmesh.types.BMEdge) and el.link_faces:
                    _rim(rim, on_liner(el.verts[0].co, 0.004), on_liner(el.verts[1].co, 0.004), 0.004)
        cut.free()
    if reveal:
        # both sides as separate faces, no merge or normal recalculation: solidified bands merged by
        # hp.finish() into a non-manifold strip, normals recalculated outwards, the view passed through
        rb = bmesh.new()
        for q in reveal:
            for vs in (q, q[::-1]):
                try:
                    rb.faces.new([rb.verts.new(p) for p in vs])
                except ValueError:
                    pass
        me_r = bpy.data.meshes.new("SM_Ship_%s_Int_Reveal" % ship)
        rb.to_mesh(me_r)
        rb.free()
        ob = bpy.data.objects.new(me_r.name, me_r)
        coll.objects.link(ob)
        # the cream accent round the windows on the dark graphite frame (author 25. 9. 2026, step 7)
        ob.data.materials.append(mats["int_cream" if "int_cream" in mats else "int_trim"])
        objs.append(ob)
    if stripe.verts:
        ob = hp.finish(stripe, "SM_Ship_%s_Int_LinerStripe" % ship, coll, {"angle_deg": 40, "width": 0, "segments": 1})
        # faintly lit: the frame's lines still read at night and in space (critic, 25. 9. 2026)
        ob.data.materials.append(mats.get("int_accent_glow", mats["accent"]))
        objs.append(ob)
    if rim.verts:
        ob = hp.finish(rim, "SM_Ship_%s_Int_LinerRim" % ship, coll, {"angle_deg": 40, "width": 0, "segments": 1})
        # graphite, not satin metal: through the glass the metal rims read as chrome tubes (critic, 25. 9. 2026)
        ob.data.materials.append(mats["int_console"] if COCKPIT.get("style") == "wrap" else mats["int_trim"])
        objs.append(ob)
    if COCKPIT.get("style") == "wrap" and COCKPIT.get("liner_ribs", True):
        # structural ribs across the frame lining at the panel stations: the lining's layer like the corridor's
        # portals (step 7 of the author's cockpit brief) - a graphite band standing proud of the lining
        ribs = bmesh.new()
        cut = lb.copy()
        for x in COCKPIT.get("seam_x", []):
            res = bmesh.ops.bisect_plane(cut, geom=cut.verts[:] + cut.edges[:] + cut.faces[:], plane_co=(x, 0, 0), plane_no=(1, 0, 0))
            for el in res["geom_cut"]:
                if isinstance(el, bmesh.types.BMEdge) and el.link_faces:
                    a_, b_ = el.verts[0].co.copy(), el.verts[1].co.copy()
                    if (b_ - a_).length < 1e-4:
                        continue
                    na, nb = on_liner(a_, 0.0) - a_, on_liner(b_, 0.0) - b_
                    fa = el.link_faces[0]
                    fa.normal_update()
                    nrm_ = fa.normal.copy()
                    if nrm_.dot(Vector((17.0, 0.0, 2.2)) - a_) < 0:
                        nrm_ = -nrm_
                    q = [a_ + Vector((-0.03, 0, 0)), b_ + Vector((-0.03, 0, 0)), b_ + Vector((0.03, 0, 0)), a_ + Vector((0.03, 0, 0))]
                    vs0 = [ribs.verts.new(v + nrm_ * 0.004) for v in q]
                    vs1 = [ribs.verts.new(v + nrm_ * 0.026) for v in q]
                    for idx in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
                        try:
                            ribs.faces.new([(vs0 + vs1)[i] for i in idx])
                        except ValueError:
                            pass
        cut.free()
        if ribs.verts:
            ob = hp.finish(ribs, "SM_Ship_%s_Int_LinerRibs" % ship, coll, {"angle_deg": 40, "width": 0.002, "segments": 1})
            ob.data.materials.append(mats["int_console"])
            objs.append(ob)
    if lb.faces:
        me = bpy.data.meshes.new("SM_Ship_%s_Int_Liner" % ship)
        lb.to_mesh(me)
        lb.free()
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
        me.materials.append(mats["int_frame" if COCKPIT.get("style") in ("pods", "wrap") else "int_wall"])
        # each face looks away from the hull 3 cm behind it (facing the cockpit's centre point failed on the
        # frame's steep faces beside the glass: hairlines of sky there, geometry check 25. 9. 2026)
        from mathutils.bvhtree import BVHTree
        hb = bmesh.new()
        hb.from_mesh(hull.data)
        hb.transform(hull.matrix_world)
        htree = BVHTree.FromBMesh(hb)
        hb.free()
        def _faces_hull(c, n, reach):
            # the hull is behind a lining face: nearer along the normal than against it (a hull flange or
            # trim strip a few cm in front must not flip it)
            fw = htree.ray_cast(c + n * 0.002, n, reach)
            bw = htree.ray_cast(c - n * 0.002, -n, reach)
            return fw[0] is not None and (bw[0] is None or fw[3] < bw[3])
        for p in me.polygons:
            if _faces_hull(Vector(p.center), p.normal.copy(), 0.08):
                p.flip()
        if db.faces:
            me_d = bpy.data.meshes.new("SM_Ship_%s_Int_HullSkin" % ship)
            db.to_mesh(me_d)
            for p in me_d.polygons:
                if _faces_hull(Vector(p.center), p.normal.copy(), 0.12):
                    p.flip()
            me_d.update()
            ob_d = bpy.data.objects.new(me_d.name, me_d)
            coll.objects.link(ob_d)
            me_d.materials.append(mats["int_dark"])
            objs.append(ob_d)
        db.free()
        me.update()
        me.shade_smooth()
        # the hull's facets meet at sharp creases: smooth normals across them streaked the walls (25. 9. 2026)
        me.set_sharp_from_angle(angle=math.radians(COCKPIT.get("liner_sharp_deg", 25.0)))
        objs.append(ob)
    if spec.get("decals"):
        # mesh decals and grab bars laid onto everything built so far (hs_interior_decals.py)
        import hs_interior_decals
        dspec = dict(spec["decals"])
        dspec["_cockpit"] = COCKPIT
        dobjs, report["decals"] = hs_interior_decals.build(objs, ship, coll, dspec, ROOT, mats, eye)
        objs += dobjs
    if holo_centre is not None and "holo" in mats:
        # the ship hologram over the left MFD (hs_cockpit.build_hologram): on the pod's top, found by a ray down
        import hs_cockpit
        from mathutils.bvhtree import BVHTree
        hg = COCKPIT["hologram"]
        centre = holo_centre
        exterior = [o for o in coll.objects if o.type == "MESH" and "_Int" not in o.name and not o.name.endswith(("_Canopy", "_Hologram"))
                    and "Gear" not in o.name and not o.name.startswith(("UCX_", "SOCKET_"))]
        emit = B()
        ho = hs_cockpit.build_hologram(emit, coll, mats["holo"], ship, exterior, centre, hg.get("length_m", 0.16))
        for key, bm in emit.bm.items():
            if bm.verts:
                eo = hp.finish(bm, "SM_Ship_%s_Int_HoloEmitter_%s" % (ship, key), coll, {"angle_deg": 30, "width": 0.002, "segments": 1})
                eo.data.materials.append(mats[key])
                objs.append(eo)
        if ho is not None:
            objs.append(ho)
            # the hologram lights its surroundings a little (step 7): a cool point light, no shadow
            lights_out.append({"at": list(centre), "cd": hg.get("light_cd", 1.5), "color": [0.35, 0.65, 1.0], "type": "point"})
            report["hologram"] = {"centre": [round(v, 3) for v in centre], "tris": sum(len(p.vertices) - 2 for p in ho.data.polygons)}
    report["lights"] = len(lights_out)
    return objs, sockets, list(lights_out), report


def _rim(bm, a, b, r):
    d = b - a
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=d.length + r)
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def cockpit_detail(g, layout, zc, sill):
    """Controls and structure around the pilot (SC cockpits: HOTAS on the side consoles, switch panels on the
    sills, seat rails, console edge lights, footwell light). Readability of the HUD and the displays first:
    nothing bright above the dashboard line."""
    objs = {o["name"]: o for o in layout["objects"] if o["room"] == "cockpit"}
    right = next(o for n, o in objs.items() if "Pravá konzole" in n)
    left = next(o for n, o in objs.items() if "Levá konzole" in n)
    seat_o = next(o for n, o in objs.items() if "křeslo" in n)
    ztop = right["z"][1] - 0.1 + 0.012          # on the console's top plate
    # HOTAS: the stick on the right console, the throttle on the left, where the forearms rest (hs_cockpit)
    import hs_cockpit
    hs_cockpit.hotas_stick(g, Vector((right["rect"][0] + 0.8, right["rect"][3] - 0.16, ztop + 0.004)))
    hs_cockpit.hotas_throttle(g, Vector((left["rect"][0] + 0.7, left["rect"][2] + 0.14, ztop + 0.004)))
    # console edge lights facing the pilot (dim, below the dashboard line)
    for o in (left, right):
        x0, x1, y0, y1 = o["rect"]
        inner = y0 if y0 > 0 else y1
        s_ = 1 if y0 > 0 else -1
        box(g["int_glow"], (x0 + 0.05, inner - s_ * 0.002, ztop - 0.06), (x1 - 0.05, inner + s_ * 0.0, ztop - 0.05))
    # tread strips on the cockpit floor between the stairs and the footwell (a plain slab - critic 25. 9.)
    k = 0
    xx = 16.2
    while xx < 18.55:
        box(g["int_trim"], (xx, -0.85, zc + 0.0005), (xx + 0.018, 0.85, zc + 0.003))
        xx += 0.09
        k += 1
    # seat rails and pedestal
    x0, x1, y0, y1 = seat_o["rect"]
    for yy in (-0.2, 0.2):
        box(g["int_trim"], (x0 - 0.25, yy - 0.025, zc), (x1 + 0.1, yy + 0.025, zc + 0.03))
    box(g["int_dark"], (x0 + 0.15, -0.22, zc + 0.03), (x1 - 0.15, 0.22, zc + 0.16))
    # (the sill switch panels are gone: the tub is clamped inside the hull now and they hung beside it; the
    # control modules on the side consoles replace them)
    # frame wash: two dim spots at the foot of the front pillars grazing up the canopy frame's lining, so the
    # frame and its metal rims read as structure instead of black bars (the lamps themselves stay out of view)
    wash = COCKPIT.get("frame_wash_cd", 4.0)
    for s_ in (1, -1):
        lights_out.append({"at": [17.7, s_ * 1.05, sill + 0.05], "cd": wash, "type": "spot", "cone_deg": 90.0,
                           "direction": [0.25, s_ * 0.35, 0.9]})
        if COCKPIT.get("style") in ("pods", "wrap"):
            # from the shoulders behind the pilot, up and forward onto the frame and the canopy arches: the
            # painted frame reads as a form by day and by night (concept A)
            lights_out.append({"at": [16.1, s_ * 0.55, zc + 1.65], "cd": wash * 0.45, "type": "spot", "cone_deg": 120.0,
                               "direction": [0.85, s_ * 0.25, 0.45], "warm": True})
    # a dim fill over the pilot's shoulders (seat, consoles, the rear of the tub)
    # islands of light: a narrow pool on each side console (the hands, the modules), dark between (step 7)
    for o in (left, right):
        x0, x1, y0, y1 = o["rect"]
        lights_out.append({"at": [(x0 + x1) / 2, (y0 + y1) / 2, ztop + 0.75], "cd": COCKPIT.get("console_pool_cd", 3.0), "type": "spot",
                           "cone_deg": 45.0, "direction": [0.0, 0.0, -1.0], "warm": True, "source_radius_cm": 4.0})
    lights_out.append({"at": [16.3, 0.0, zc + 1.5], "cd": 1.6, "warm": True, "source_radius_cm": 30.0})
    # footwell light (warm, small): the pilot's legs and the tub read in the dark
    for s_ in (1, -1):
        lights_out.append({"at": [17.6, s_ * 0.55, zc + 0.12], "cd": 2.0, "warm": True})


def seat(coll, mats, spec, r, zr):
    """The Meshy pilot seat, scaled to the layout's width, standing on the cockpit floor facing +x."""
    path = os.path.join(ROOT, spec["seat"]["glb"])
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    for o in set(bpy.data.objects) - before:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    if not new:
        return
    bpy.ops.object.select_all(action="DESELECT")
    for o in new:
        o.select_set(True)
    bpy.context.view_layer.objects.active = new[0]
    if len(new) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    vs = [v.co for v in ob.data.vertices]
    lo = Vector([min(v[i] for v in vs) for i in range(3)])
    hi = Vector([max(v[i] for v in vs) for i in range(3)])
    # Meshy faces -Y: turn so the seat faces +x (the nose)
    ob.data.transform(Matrix.Translation(-(lo + hi) / 2 * Vector((1, 1, 0)) - Vector((0, 0, lo.z))))
    ob.data.transform(Matrix.Rotation(math.radians(spec["seat"].get("yaw_deg", 90)), 4, "Z"))
    vs = [v.co for v in ob.data.vertices]
    width = max(v.y for v in vs) - min(v.y for v in vs)
    s = spec["seat"]["width_m"] / max(width, 1e-3)
    ob.data.transform(Matrix.Scale(s, 4))
    x0, x1, y0, y1 = r
    ob.data.transform(Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, zr[0])))
    ob.name = ob.data.name = "SM_Ship_Wayfarer_Int_Seat"
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)
    for i, m in enumerate(ob.data.materials):
        ob.data.materials[i] = mats["int_leather"] if i == 0 else mats["int_dark"]
