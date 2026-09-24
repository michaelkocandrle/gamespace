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
    box(g["int_dark"], (x0, y0, z - 0.06), (x1, y1, z - 0.02))
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


# ------------------------------------------------------------------------------------------ objects

def hatch(g, r, z):
    x0, x1, y0, y1 = r
    box(g["int_trim"], (x0, y0, z), (x1, y1, z + 0.006))
    box(g["int_floor"], (x0 + 0.04, y0 + 0.04, z + 0.004), (x1 - 0.04, y1 - 0.04, z + 0.01))
    box(g["accent"], (x1 - 0.14, (y0 + y1) / 2 - 0.05, z + 0.01), (x1 - 0.06, (y0 + y1) / 2 + 0.05, z + 0.02))


def obj_hydraulics(g, r, zr):
    x0, x1, y0, y1 = r
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
    box(g["accent"], (x0 + 0.1, face - 0.045, zr[1] - 0.25), (x0 + 0.5, face - 0.04, zr[1] - 0.2))


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
    box(g["int_dark"], (x0, y0, z0), (x1, y1, zr[1] - 0.1))
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
    """The instrument panel: a sloped fascia facing the pilot's eye with the game's four screens."""
    x0, x1, y0, y1 = r
    box(g["int_dark"], (x0 + 0.2, y0, z0), (x1, y1, zr[0]))                   # lower body
    top = zr[1]
    fascia_c = Vector((x0 + 0.25, 0.0, (zr[0] + top) / 2))
    to_eye = (Vector(eye) - fascia_c).normalized()
    n = Vector((to_eye.x, 0, to_eye.z)).normalized()
    up = Vector((0, 0, 1)) - n * n.z
    up.normalize()
    obox(g["int_trim"], fascia_c - n * 0.03, (0, 1, 0), n, (y1 - y0, top - zr[0] + 0.1, 0.05))
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
        obox(g["int_dark"], c - n * 0.001, right, n, (w + 0.04, h + 0.04, 0.012))
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


# ------------------------------------------------------------------------------------------ main

def build(recipe, layout, coll, mats, ship, hull):
    spec = recipe["interior"]
    H = spec.get("height_m", 2.3)
    inset = spec.get("wall_inset_m", 0.05)
    g = B()
    lights_out.clear()
    rooms = {r["id"]: r for r in layout["rooms"]}
    doors = layout["doors"]
    report = {"rooms": [], "objects": 0}
    for rid, r in rooms.items():
        x0, x1, y0, y1 = r["rect"]
        z0 = r.get("floor_z", 0.0)
        if rid == "cockpit":
            continue
        y0i, y1i = y0 + inset, y1 - inset
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
    # cockpit: floor, step, tub walls to the sill, rear wall, liner above the sill
    ck = rooms["cockpit"]
    zc = ck["floor_z"]
    poly = ck["poly"]
    sill = spec.get("sill_z", 1.05)
    fb = g["int_floor"]
    top = [fb.verts.new((p[0], p[1], zc)) for p in poly]
    bmesh.ops.contextual_create(fb, geom=top)
    box(g["int_dark"], (15.2, -1.0, 0.0), (15.5, 1.0, zc))                    # step up
    box(g["int_trim"], (15.47, -1.0, zc - 0.02), (15.5, 1.0, zc))
    for a, b in zip(poly, poly[1:]):
        pa, pb = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
        d = pb - pa
        length = d.length
        nrm = Vector((-d.y, d.x, 0)).normalized()
        if nrm.dot(Vector((17.3, 0, 0)) - pa) < 0:
            nrm = -nrm
        c = (pa + pb) / 2 + nrm * 0.03
        obox(g["int_wall"], (c.x, c.y, (zc + sill) / 2), d, (0, 0, 1), (length, 0.04, sill - zc))
        obox(g["int_trim"], (c.x, c.y, sill), d, (0, 0, 1), (length, 0.08, 0.03))
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
            seat(coll, mats, spec, (x0, x1, y0, y1), zr)
        else:
            continue
        report["objects"] += 1
    objs = []
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
    for f in src.faces:
        c = f.calc_center_median()
        if 15.2 <= c.x <= 19.6 and c.z > sill - 0.05 and abs(c.y) < 2.2:
            vs = []
            for v in f.verts:
                if v.index not in vmap:
                    vmap[v.index] = lb.verts.new(v.co - v.normal * 0.03)
                vs.append(vmap[v.index])
            try:
                nf = lb.faces.new(vs[::-1])
            except ValueError:
                pass
    src.free()
    if lb.faces:
        me = bpy.data.meshes.new("SM_Ship_%s_Int_Liner" % ship)
        lb.to_mesh(me)
        lb.free()
        ob = bpy.data.objects.new(me.name, me)
        coll.objects.link(ob)
        me.materials.append(mats["int_wall"])
        for p in me.polygons:
            p.use_smooth = True
        objs.append(ob)
    report["lights"] = len(lights_out)
    return objs, sockets, list(lights_out), report


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
