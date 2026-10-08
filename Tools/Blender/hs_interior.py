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


DOOR_LEAVES = []


def build_door(leaf, n, ship, coll, mats, H):
    """A doorway's sliding leaves (author 5. 10. 2026: SC's doors slide into the wall; the author's capture: a panel
    with a light slot and an orange PUSH TO OPEN plate, F to open). One leaf when the wall on one side has room for it,
    else two that part to both sides. Built OPEN (beside the doorway, 10-13.5 cm in front of the wall's forward face,
    clear of the frame posts) so the walk check passes the doorway; the game closes them. Each leaf is its own part
    SM_Ship_<Ship>_Door<n><A|B>_<material>; sockets Control_door<n> (the doorway's centre, for the prompt) and
    Control_door<n>_<a|b> (where the leaf's centre goes when it is closed). Returns [(socket, location)]."""
    x, yc, w, half = leaf["x"], leaf["yc"], leaf["w"], leaf["half"]
    h = 2.08
    t = 0.035
    xf = x + 0.10                       # the leaf's back face
    room_neg = (yc - w / 2) - (-half)   # wall beside the doorway towards -y
    room_pos = half - (yc + w / 2)
    if max(room_neg, room_pos) >= w + 0.06:
        sides = [(-1 if room_neg >= room_pos else 1, w + 0.06)]          # one leaf, the whole width
    else:
        sides = [(-1, w / 2 + 0.03), (1, w / 2 + 0.03)]                  # two halves part
    out = [("Control_door%d" % n, Vector((x + 0.12, yc, 1.2)))]
    # the holographic touch panel beside the doorway (author 5. 10. 2026: SC's door panel, opened in interact mode),
    # on the side the leaf does not slide to, 20 cm past the opening, 6 cm in front of the wall (UShipBoardingComponent
    # puts the hologram there)
    away = -sides[0][0] if len(sides) == 1 else 1
    out.append(("Control_door%d_panel" % n, Vector((x + 0.06, yc + away * (w / 2 + 0.2), 1.3))))
    for k, (sgn, lw) in enumerate(sides):
        letter = "AB"[k]
        closed_c = yc + (0.0 if len(sides) == 1 else sgn * lw / 2)
        open_c = closed_c + sgn * (lw + 0.01)
        g = B()
        y0, y1 = open_c - lw / 2, open_c + lw / 2
        box(g["int_panel"], (xf, y0, 0.01), (xf + t, y1, h))                                   # the leaf
        lead = y1 if sgn < 0 else y0                                                           # the edge that closes
        e = 1 if sgn < 0 else -1          # into the leaf from its closing edge
        px = lead - e * 0.15
        pa, pb = min(px, px - e * 0.11), max(px, px - e * 0.11)
        # both faces alike (the door is opened from both rooms); d = +1 the forward face, -1 the aft one
        # (critic 5. 10. 2026: "a flat matte slab" - a light border, a lighter field broken in three, a lit slot)
        for d, face in ((1, xf + t), (-1, xf)):
            def slab(key, ya, yb, za, zb, proud, depth=0.0):
                lo, hi = sorted((face - d * depth, face + d * proud))
                box(g[key], (lo, ya, za), (hi, yb, zb))
            for (ya, yb, za, zb) in ((y0, y0 + 0.045, 0.01, h), (y1 - 0.045, y1, 0.01, h),
                                     (y0, y1, 0.01, 0.065), (y0, y1, h - 0.055, h)):
                slab("int_trim", ya, yb, za, zb, 0.008)                                         # the light border
            for (za, zb) in ((0.09, 0.74), (0.78, 1.5), (1.54, h - 0.08)):
                slab("int_wall", y0 + 0.07, y1 - 0.07, za, zb, 0.004)                           # the field in three
            slab("int_dark", y0 + 0.07, y1 - 0.07, 0.74, 0.78, 0.002)                           # the breaks between them
            slab("int_dark", y0 + 0.07, y1 - 0.07, 1.5, 1.54, 0.002)
            # the light slot along the closing edge (the kit's warm glow; dims with the ship's power)
            slab("int_glow", min(lead, lead - e * 0.028), max(lead, lead - e * 0.028), 0.3, h - 0.3, 0.012)
            # a recessed pull handle (critic 5. 10.: the orange plate with slots read as a primitive): a satin bezel,
            # a dark pocket, a satin grip bar across it and a thin amber line under it
            slab("int_trim", pa, pb, 0.96, 1.22, 0.006)
            slab("int_dark", pa + 0.012, pb - 0.012, 0.975, 1.205, 0.0065)
            slab("int_trim", pa + 0.022, pb - 0.022, 1.06, 1.12, 0.022)
            slab("accent", pa + 0.02, pb - 0.02, 0.985, 0.993, 0.0075)
        for key, bm in g.bm.items():
            if bm.verts:
                ob = hp.finish(bm, "SM_Ship_%s_Door%d%s_%s" % (ship, n, letter, key), coll, {"angle_deg": 30, "width": 0.002, "segments": 1})
                ob.data.materials.append(mats[key])
        out.append(("Control_door%d_%s" % (n, letter.lower()), Vector((xf + t / 2, closed_c, h / 2))))
    return out


def bulkhead(g, x, y0, y1, z0, z1, door, facing, full=False):
    """A cross wall at x from y0 to y1 with an open doorway (door: [yc, width] or None), framed. full: the doorway
    runs up to the ceiling (z1) with no header - the cockpit's door at the foot of the steep stairs, where a
    header at 2.05 m sat in the way of the head of anyone on the upper steps (walking the ship, 29. 9. 2026)."""
    dh = z1 if full else z0 + 2.05
    t = 0.04
    xa, xb = sorted((x, x + facing * t))
    spans = [(y0, y1)] if not door else _minus((y0, y1), [(door[0] - door[1] / 2, door[0] + door[1] / 2)])
    for ya, yb in spans:
        box(g["int_wall"], (xa, ya, z0), (xb, yb, z0 + 1.1))
        box(g["int_panel"], (xa, ya, z0 + 1.11), (xb, yb, z1))
    if door and full:
        # posts to the ceiling, the orange marker down each post instead of over a header
        ya, yb = door[0] - door[1] / 2, door[0] + door[1] / 2
        for yy in (ya - 0.08, yb):
            box(g["int_trim"], (xa - 0.05, yy, z0), (xb + 0.05, yy + 0.08, z1))
        for yy in (ya - 0.08, yb + 0.08):
            box(g["accent"], (xa - 0.052, yy - 0.004, 1.2), (xb + 0.052, yy + 0.004, z1 - 0.1))
    elif door:
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


def _kit_scale(spec, H, z0=0.0):
    """The modular kit's module scale for a room of height H (hs_interior_kit.shell's formula), when no kit room
    measured it."""
    kc = spec["kit"]
    a = kc.get("chamfer_deg", 35.0)
    return (H - z0 - kc.get("cove_m", 0.12)) / (3.0 + 2.0 * math.cos(math.radians(a)))


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


def prism_yz(bm, xa, xb, pts):
    """A prism between xa and xb over the convex polygon pts [(y, z)], its faces turned outward."""
    vs = [bm.verts.new((x, y, z)) for x in (xa, xb) for (y, z) in pts]
    n = len(pts)
    faces = [bm.faces.new(vs[:n]), bm.faces.new(vs[n:])]
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((vs[i], vs[j], vs[n + j], vs[n + i])))
    c = sum((v.co for v in vs), Vector()) / len(vs)
    for f in faces:
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - c) < 0:
            f.normal_flip()


LINER_VT, LINER_RUN = 1.7, 0.75       # the hull liner's section L: vertical to 1.7 m, the chamfer 0.75 in per metre up


def obj_hygiene(g, r, zr, liner=None):
    x0, x1, y0, y1 = r
    t = 0.05
    if liner:
        # a hull liner room (30. 9. 2026): the sides run back to the liner's panels and follow its chamfer, a roof
        # at the cell's height closes it under the chamfer (a box to the ceiling stood through the liner)
        s = -1 if y1 < 0 else 1
        yb = s * (liner - 0.012)
        zt = zr[1]
        yk = s * (liner - LINER_RUN * (zt - LINER_VT) - 0.02)
        zk = LINER_VT + 0.012 / LINER_RUN
        pts = [(y1, 0.0), (yb, 0.0), (yb, zk), (yk, zt), (y1, zt)]
        if s < 0:
            pts = list(reversed(pts))
        for xa in (x0, x1 - t):
            prism_yz(g["int_wall"], xa, xa + t, pts)
        ya, yb2 = sorted((y1, yk))
        box(g["int_panel"], (x0, ya, zt - 0.03), (x1, yb2, zt))
    else:
        box(g["int_wall"], (x0, y0, 0), (x0 + t, y1, zr[1]))
        box(g["int_wall"], (x1 - t, y0, 0), (x1, y1, zr[1]))
    face = y1
    door = (x0 + x1) / 2
    for xa, xb in _minus((x0, x1), [(door - 0.4, door + 0.4)]):
        box(g["int_panel"], (xa, face - t, 0), (xb, face, zr[1]))
    dh = min(2.05, zr[1] - 0.1)            # the doorway's head: under a 2.05 m roof (hull liner room) 1.95
    box(g["int_panel"], (door - 0.4, face - t, dh), (door + 0.4, face, zr[1]))
    box(g["int_trim"], (door - 0.45, face, dh), (door + 0.45, face + 0.04, dh + 0.08))
    box(g["int_dark"], (door - 0.4, face - 0.03, 0.02), (door + 0.4, face - 0.025, dh - 0.01))   # closed sliding leaf
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


KIT_CONSOLES = set()     # "left" / "right": the console is a factory part (kit_modules run_parts, kit_cockpit.py), not built here


def obj_console(g, r, zr, z0):
    x0, x1, y0, y1 = r
    if ("left" if y0 > 0 else "right") in KIT_CONSOLES:
        return
    top = zr[1] - 0.1
    if COCKPIT.get("style") in ("pods", "wrap"):
        # the outer edge stood 2-3 cm into the hull where the tub narrows (geometry check, 25. 9. 2026)
        if y1 > 0:
            y1 -= 0.04
        else:
            y0 += 0.04
    if COCKPIT.get("style") in ("pods", "wrap"):
        # (7. 10. 2026: the kit trim strip on the body's inner face read as crumpled foil under the top - the body
        # in the cockpit's warm graphite)
        # (critic 7. 10.: boxy CAD blocks) the body with its vertical edges rounded 3 cm in plan
        import hs_cockpit as _hc
        _hc.rr_slab(g["int_console"], Vector(((x0 + x1) / 2, (y0 + y1) / 2, top)), Vector((1, 0, 0)), Vector((0, 1, 0)),
                    Vector((0, 0, 1)), x1 - x0, y1 - y0, 0.03, top - z0, 3)
    else:
        tbox(g, "int_dark", "kit_trim02", (x0, y0, z0), (x1, y1, top), 1.0)
    if COCKPIT.get("style") in ("pods", "wrap"):
        # a top plate inside the body with a satin rim (the old tilted plate overhung the console; its glow
        # rectangle was a placeholder and its knobs bare cylinders - control modules come from hs_cockpit)
        # (7. 10. 2026, SC's consoles: mid-grey satin metal housings round dark insets - the near-black top read as one
        # slab) the top plate in the housing grey
        box(g["int_housing"], (x0 + 0.03, y0 + 0.03, top), (x1 - 0.03, y1 - 0.03, top + 0.012))
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
        # (author 5. 10. 2026: the consoles flat slabs, "plastic and cheap" - the corridor ceiling's level: layered
        # trims, ribs, a padded forearm rest, a vent)
        import hs_cockpit
        sgn = 1.0 if y0 > 0 else -1.0               # +1: the left console (outboard = +y)
        inner = y0 if y0 > 0 else y1                # the face towards the pilot

        def proud(d):
            return sorted((inner, inner - sgn * d))
        # the forearm rest along the inner edge of the top, behind the HOTAS: a padded leather bar on a graphite base
        # (critic 7. 10. r4: the stick out of the forearm's line, the arm "in wings") an arm shelf off the console's
        # inner edge, in to 0.36 m from the seat axis, at the console's top height - the forearm lies on it from the
        # elbow to the stick at 0.40 m
        sh_in = sgn * 0.36
        ya_, yb_ = sorted((sh_in, inner + sgn * 0.02))
        hs_cockpit.rr_slab(g["int_housing"], Vector(((x0 + 0.2 + x0 + 0.95) / 2, (ya_ + yb_) / 2, top + 0.012)), Vector((1, 0, 0)),
                           Vector((0, 1, 0)), Vector((0, 0, 1)), 0.75, yb_ - ya_, 0.02, 0.05, 3)
        hs_cockpit.rr_ring(g["int_trim"], Vector(((x0 + 0.2 + x0 + 0.95) / 2, (ya_ + yb_) / 2, top + 0.0125)), Vector((1, 0, 0)),
                           Vector((0, 1, 0)), Vector((0, 0, 1)), 0.75, yb_ - ya_, 0.02, 0.004, 0.002, 3)
        pc = Vector((x0 + 0.47, sgn * 0.40, top + 0.016))     # the wrist rest in line with the stick, 10 cm behind it
        hs_cockpit.rr_slab(g["int_console"], pc, Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.46, 0.1, 0.03, 0.014, 4)
        hs_cockpit.rr_slab(g["int_leather_perf"], pc + Vector((0, 0, 0.034)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.44, 0.085, 0.032, 0.04, 6)   # (front face at c, depth behind)
        hs_cockpit.rr_slab(g["int_dark"], pc + Vector((0, 0, 0.0345)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.4, 0.004, 0.001, 0.002, 1)   # the welt, sunk into the pad
        # the inner face: a dark recessed kick at the foot under a satin plinth strip, a trim band under the top,
        # structural ribs between them and a louvred vent near the front
        ya, yb = proud(0.004)
        box(g["int_dark"], (x0 + 0.02, ya, z0), (x1 - 0.02, yb, z0 + 0.07))
        ya, yb = proud(0.016)
        box(g["int_trim"], (x0 + 0.01, ya, z0 + 0.07), (x1 - 0.01, yb, z0 + 0.086))
        ya, yb = proud(0.01)
        box(g["int_trim"], (x0 + 0.01, ya, top - 0.095), (x1 - 0.01, yb, top - 0.078))
        ya, yb = proud(0.013)
        for f in (0.2, 0.45, 0.7):
            xr = x0 + (x1 - x0) * f
            box(g["int_console"], (xr - 0.016, ya, z0 + 0.086), (xr + 0.016, yb, top - 0.095))
            for zz in (z0 + 0.11, top - 0.12):
                ya2, yb2 = proud(0.016)
                cyl(g["int_trim"], (xr, (ya2 + yb2) / 2, zz), (xr, yb2 if sgn < 0 else ya2, zz), 0.005, 8)
        # (critic 7. 10. r2/r3: the inner faces empty blocks) a bolted service panel aft of the vent with its stencil,
        # a panel number by the rib; boot scuffs along the kick
        sp0, sp1 = x0 + 0.3, x0 + 0.62
        sz0, sz1 = z0 + 0.14, top - 0.13
        ya, yb = proud(0.005)
        box(g["int_trim"], (sp0 - 0.008, ya, sz0 - 0.008), (sp1 + 0.008, yb, sz1 + 0.008))
        ya, yb = proud(0.009)
        box(g["int_housing"], (sp0, ya, sz0), (sp1, yb, sz1))
        for xx in (sp0 + 0.018, sp1 - 0.018):
            for zz in (sz0 + 0.018, sz1 - 0.018):
                q = Vector((xx, inner - sgn * 0.009, zz))
                cyl(g["int_trim"], q, q - Vector((0, sgn * 0.0015, 0)), 0.003, 8)          # flush screws, not knobs
        nin = Vector((0, -sgn, 0))
        rgt = Vector((sgn, 0, 0))
        hs_cockpit.stencil("st_service", Vector(((sp0 + sp1) / 2, inner - sgn * 0.0095, sz1 - 0.04)), nin, rgt, Vector((0, 0, 1)), 0.9, 0.3)
        hs_cockpit.stencil("hatch_small", Vector(((sp0 + sp1) / 2, inner - sgn * 0.0095, (sz0 + sz1) / 2 - 0.01)), nin, rgt,
                           Vector((0, 0, 1)), 0.9, 0.2)
        hs_cockpit.stencil("panel_B03" if sgn > 0 else "panel_B07", Vector((x0 + 0.2 * (x1 - x0) + 0.04, inner - sgn * 0.0135, top - 0.13)),
                           nin, rgt, Vector((0, 0, 1)), 0.5, 0.05)
        # (critic 7. 10.: a smeared blot, not dirt settled at the edge) a narrow rim on the kick's top edge only
        hs_cockpit.grime(Vector(((x0 + x1) / 2, inner - sgn * 0.004, z0 + 0.094)), nin, Vector((0, 0, -1)), (x1 - x0 - 0.1, 0.035), "rim", 0.85)
        # (author 7. 10. 2026: "layer decals and textures over each other") the console's decal stack after the etalon's
        # analysis (Docs/Kit/etalon/decal_stack.md): mid detail (seams, rivet rows, slot rows, a socket), the information
        # layer (small tone-on-tone stencils, subtle hatching, corner marks) and wear (scuffs where forearms and boots
        # rub, scratches by the controls, a short streak) on the top, the inner face and the nose
        st = hs_cockpit.stencil
        Z3, X3, Yo = Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))   # (a right-handed frame on the top: X x Y = Z)
        tz = top + 0.012
        mid = inner + sgn * (abs(y1 - y0) / 2)
        outer = inner + sgn * abs(y1 - y0)
        # top: wear along the inner edge, scratches, rivets along the outer edge, slot row, stencils, hatching, corners
        for xx in (x0 + 0.26, x0 + 0.58):
            st("edge_scuff", Vector((xx, inner + sgn * 0.04, tz)), Z3, X3, Yo, 0.6, 9.0)
        st("scratches", Vector((x0 + 0.55, mid - sgn * 0.02, tz)), Z3, X3, Yo, 0.45, 9.0)
        # hands at the HOTAS and along the forearm edge: smears and a worn rim (critic 7. 10.: the grime invisible)
        hs_cockpit.grime(Vector((x0 + 0.75, inner + sgn * 0.15, tz)), Z3, Yo, (0.26, 0.24), "smear", 1.0)
        hs_cockpit.grime(Vector(((x0 + x1) / 2, inner + sgn * 0.03, tz)), Z3, Yo * sgn, (x1 - x0 - 0.12, 0.06), "rim", 1.0)
        hs_cockpit.grime(Vector(((x0 + x1) / 2, inner + sgn * 0.022, tz)), Z3, Yo * sgn, (x1 - x0 - 0.14, 0.04), "rim", 1.0, wear=True)
        hs_cockpit.grime(Vector((x0 + 0.75, inner + sgn * 0.15, tz)), Z3, Yo, (0.2, 0.2), "smear", 0.9, wear=True)
        hs_cockpit.grime(Vector(((x0 + x1) / 2, inner - sgn * 0.004, z0 + 0.105)), nin, Vector((0, 0, -1)), (x1 - x0 - 0.12, 0.03), "rim", 0.9, wear=True)
        st("rivet_row_8", Vector((x0 + 0.36, outer - sgn * 0.038, tz)), Z3, X3, Yo, 0.8, 9.0)
        st("slot_s", Vector((x0 + 0.78, inner + sgn * 0.44, tz)), Z3, X3, Yo, 0.5, 9.0)
        st("st_torque", Vector((x0 + 0.62, mid, tz)), Z3, Yo, -X3, 0.5, 9.0)
        st("hazard_subtle", Vector((x0 + 0.055, mid, tz)), Z3, Yo, -X3, 0.85, 9.0)

        # the inner face: a rivet row under the top, boot scuffs at the kick, a socket with its label aft, a streak
        st("rivet_row_16", Vector(((x0 + x1) / 2, inner - sgn * 0.0005, top - 0.024)), nin, rgt, Z3, 0.9, 9.0)
        # (critic 7. 10.: the inner face one flat field) panel seams down it with their numbers, an inspection stencil,
        # a high-voltage tag by the socket, dirt settled in the seams
        for k_, xs_ in enumerate((x0 + 0.27, x0 + 0.66)):          # (clear of the ribs and the vent)
            if xs_ > x1 - 0.06:
                continue
            st("seam_straight", Vector((xs_, inner - sgn * 0.0005, z0 + 0.36)), nin, Z3, -rgt, 0.8, 9.0)
            st(("panel_A12", "panel_A14", "panel_E11")[k_], Vector((xs_ + 0.035, inner - sgn * 0.0005, top - 0.12)), nin, rgt, Z3, 0.42, 9.0)
            hs_cockpit.grime(Vector((xs_, inner - sgn * 0.004, z0 + 0.36)), nin, -rgt, (0.4, 0.03), "rim", 0.8)
        st("st_inspect", Vector((x1 - 0.2, inner - sgn * 0.0005, top - 0.065)), nin, rgt, Z3, 0.5, 9.0)
        st("warn_hv", Vector((x0 + 0.12, inner - sgn * 0.0005, z0 + 0.42)), nin, rgt, Z3, 0.45, 9.0)
        for xx in (x0 + 0.39, x0 + 0.69):
            st("edge_scuff", Vector((xx, inner - sgn * 0.0005, z0 + 0.11)), nin, rgt, Z3, 0.6, 9.0)
        st("socket", Vector((x0 + 0.12, inner - sgn * 0.0005, z0 + 0.36)), nin, rgt, Z3, 0.8, 9.0)
        st("label_power", Vector((x0 + 0.12, inner - sgn * 0.0005, z0 + 0.29)), nin, rgt, Z3, 0.45, 9.0)
        st("streak_short", Vector((sp0 + 0.05, inner - sgn * 0.0005, z0 + 0.112)), nin, rgt, Z3, 0.3, 9.0)
        # the nose (facing forward): an access panel, a vent stencil, a bolt row under the top
        nose_r = Vector((0, 1, 0))
        st("access_panel", Vector((x1 + 0.0005, mid, z0 + 0.36)), X3, nose_r, Z3, 0.8, 9.0)
        st("st_vent", Vector((x1 + 0.0005, mid, top - 0.12)), X3, nose_r, Z3, 0.6, 9.0)
        st("bolt_row_4", Vector((x1 + 0.0005, mid, top - 0.03)), X3, nose_r, Z3, 0.7, 9.0)
        vx0, vx1 = x1 - 0.33, x1 - 0.1
        vz0, vz1 = z0 + 0.16, top - 0.14
        ya, yb = proud(0.006)
        box(g["int_trim"], (vx0 - 0.012, ya, vz0 - 0.012), (vx1 + 0.012, yb, vz1 + 0.012))
        ya, yb = proud(0.008)
        box(g["int_dark"], (vx0, ya, vz0), (vx1, yb, vz1))
        k = 0
        zz = vz0 + 0.012
        while zz < vz1 - 0.01:
            ya, yb = proud(0.014)
            box(g["int_console"], (vx0 + 0.006, ya, zz), (vx1 - 0.006, yb, zz + 0.008))
            zz += 0.022
            k += 1
        # (critic 5. 10.: the console tops large empty slabs; 7. 10.: SC's console heads - a speaker grille, a big red
        # guarded push button, hazard hatching) the module ahead of the HOTAS: a housing-grey plate in a satin rim, the
        # aft half a perforated grille, the fore half a red emergency button under a hinged orange guard, a hazard band
        # along the console's nose
        tc = Vector((x1 - 0.15, (y0 + y1) / 2, top + 0.012))
        X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
        # (author 7. 10.: the emergency button turned the wrong way, out of place) SC's block sloped towards the pilot:
        # the red guarded key over a row of labelled rockers, read from the seat
        hs_cockpit.sc_control_block(g, Vector((x1 - 0.12, (y0 + y1) / 2 + sgn * 0.06, top + 0.012 + 0.065)), 0.26, 0.18, 38.0,
                                    "ck_emerg_o2" if y0 > 0 else "ck_qt",
                                    ["ck_pwr", "ck_extlt", "ck_eng"] if y0 > 0 else ["ck_shld", "ck_cool", "ck_wpn"])
        # (critic 7. 10. r1: the top round the HOTAS 60 % empty) a rocker bank in the middle band beside the HOTAS,
        # 2 x 2 labelled rockers in a grey housing
        rc = Vector((x0 + 0.78, (y0 + y1) / 2 + (0.005 if y0 > 0 else -0.005), top + 0.016))
        hs_cockpit.control_module(g, rc, Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), 0.15, 0.22,
                                  [[("rocker", "ck_pwr"), ("rocker", "ck_eng")], [("rocker", "ck_extlt"), ("rocker", "ck_batt")]]
                                  if y0 > 0 else
                                  [[("rocker", "ck_shld"), ("rocker", "ck_cool")], [("rocker", "ck_wpn"), ("rocker", "ck_sys")]],
                                  label_scale=0.5)
        hs_cockpit.hazard_band(g, Vector((x1 - 0.036, (y0 + y1) / 2, top + 0.012)), Y, X, Z, (y1 - y0) - 0.09, 0.022)
        # (critic round 3: the top still a bare slab from the seat) a rubber mat strip in a satin-rimmed recess along
        # the outer half, ahead of the switch module, with ribs across it
        mc = Vector(((x0 + 0.66 + x1 - 0.28) / 2, (y1 - 0.11) if y0 > 0 else (y0 + 0.11), top + 0.012))
        ml = (x1 - 0.28) - (x0 + 0.66)
        if ml > 0.08:
            X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
            hs_cockpit.rr_ring(g["int_trim"], mc + Z * 0.005, X, Y, Z, ml, 0.13, 0.01, 0.01, 0.005, 3)
            hs_cockpit.rr_slab(g["int_dark"], mc + Z * 0.0015, X, Y, Z, ml - 0.016, 0.114, 0.008, 0.002, 3)
            k = 0
            while (k + 1) * 0.028 < ml - 0.03:
                hs_cockpit.rr_slab(g["int_console"], mc + X * (-ml / 2 + 0.02 + k * 0.028) + Z * 0.004, X, Y, Z, 0.012, 0.1, 0.004, 0.0025, 2)
                k += 1
        # (critic round 2: the outer half of the top still empty) a switch module on the outer half, beside the forearm rest
        oc = Vector((x0 + 0.53, (y1 - 0.11) if y0 > 0 else (y0 + 0.11), top + 0.016))   # (clear of the canopy module aft)
        hs_cockpit.control_module(g, oc, Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), 0.16, 0.2,
                                  [[("rocker", "ck_hyd"), ("rocker", "ck_o2")], [("guarded", "ck_esp"), ("button", "ck_aux")],
                                   [("led_w", "ck_ready"), ("led_o", "ck_heat")]] if y0 > 0 else
                                  [[("rocker", "ck_rcs"), ("rocker", "ck_ifcs")], [("guarded", "ck_qt"), ("button", "ck_scan")],
                                   [("led_w", "ck_link"), ("led_blink", "ck_armed")]])
        if y0 < 0:
            # the right console's module aft of the stick, mirroring the left one: lights, comms, two status LEDs
            hs_cockpit.control_module(g, Vector((x0 + 0.32, (y0 + y1) / 2 - 0.05, top + 0.016)), Vector((0, -1, 0)), Vector((1, 0, 0)),
                                      Vector((0, 0, 1)), 0.18, 0.11, [[("led_w", "ck_link"), ("led_o", "ck_trk"), ("led_blink", "ck_warn")], [("rocker", "ck_lights"), ("button", "ck_comms")]])
        if y0 > 0:
            # the left console's module aft of the throttle: the canopy LOCK rocker and three labelled status LEDs
            # (18 cm: at 15 the outer LED's label crossed the housing's rim)
            import hs_cockpit
            hs_cockpit.control_module(g, Vector((x0 + 0.32, (y0 + y1) / 2 + 0.05, top + 0.016)), Vector((0, -1, 0)), Vector((1, 0, 0)),
                                      Vector((0, 0, 1)), 0.18, 0.11, [[("led_o", "ck_seal"), ("led_w", "ck_press"), ("led_blink", "ck_warn")], [("rocker", "ck_lock"), ("guarded", "ck_canopy")]])
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
        if COCKPIT.get("inner_frame"):
            # cockpit v2 CK-CF: the canopy's inner frame round the glass (hs_canopy_frame.py)
            import hs_canopy_frame
            print("HSINTERIOR canopy inner frame", hs_canopy_frame.build(g, ship, eye, COCKPIT["inner_frame"]))
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


def stairs(g, fb, floor_faces, zc, x0=15.30, half_w=0.5, rise_max=0.195, tread=0.18, wall=15.24):
    """Steep ship's stairs from the cabin's deck up to the raised cockpit floor (zc), through the rear wall's door
    (the cockpit sits 1.15 m up so the pilot's eye is in the canopy's glass band, step 2 of the author's view
    targets 25. 9. 2026). Solid blocks with a satin tread plate and a lit nosing on each step, closed side walls
    under the floor's ledges, a handrail on both sides. The floor slab is cut open over the flight.
    x0 = 15.30, 6 cm clear of the rear wall (15.24): walking the ship (29. 9. 2026) a 1.80 m walker going down
    caught its head on the wall over the full-height doorway (2.30) - the flight at 15.24 left no margin. The
    strip from the rear wall's face (wall) to the first riser is floored, the side walls start at the wall."""
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
    # the slab's rear edge (x 15.2, 3 cm tall) stayed whole across the flight: a sliver hanging in the doorway at
    # 1.12 m that stopped anyone walking down the stairs (walking the ship, 29. 9. 2026); along the rear wall
    # it is hidden against the bulkhead, so it goes entirely
    fb.normal_update()
    rear = [f for f in fb.faces if abs(f.normal.x) > 0.9 and f.calc_center_median().x < x0
            and zc - 0.05 < f.calc_center_median().z < zc + 0.01]
    bmesh.ops.delete(fb, geom=rear, context="FACES")
    if x0 > wall:
        box(g["int_floor"], (wall, -half_w, -0.03), (x0, half_w, 0.0))
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
        box(g["int_panel"], (min(x0, wall), ya, 0.0), (x_top + 0.04, yb, zc))
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


def _gable(bm, hull, x, z0, g=None, door=None):
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
        # over a full-height doorway (door: y centre, width) a rib starts above the beam: at the wall's foot it
        # was in the way of the head of anyone coming down the stairs
        zr = z0 + 0.39 if door and abs(yy - door[0]) < door[1] / 2 + 0.05 else z0
        box(g["int_trim"], (x, yy - 0.03, zr), (x + 0.035, yy + 0.03, hit.z - 0.07))
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
    KIT_CONSOLES.clear()
    for a, d_, parts_ in (recipe.get("interior", {}).get("kit_modules", {}).get("run_parts") or []):
        for m_ in parts_:
            if m_.startswith("Cockpit_Console"):
                KIT_CONSOLES.add("left" if a[1] > 0 else "right")
    DOOR_LEAVES.clear()
    spec = recipe["interior"]
    H = spec.get("height_m", 2.3)
    inset = spec.get("wall_inset_m", 0.05)
    g = B()
    lights_out.clear()
    import hs_cockpit
    hs_cockpit.LABELS.clear()
    hs_cockpit.GRIME.clear()
    rooms = {r["id"]: r for r in layout["rooms"]}
    doors = layout["doors"]
    report = {"rooms": [], "objects": 0}
    # rooms from the interior kit (ArtSource/Kit): their parts come in Unreal as components of the ship
    # (Tools/Assets/kit_rooms.py); here only the bulkheads and the stand-ins for the parts the kit lacks. Switched off
    # (kit_modules.enabled false) the rooms keep their own interior (Tools/Kit/kit_layout.active_rooms)
    mods = spec.get("kit_modules") or {}
    mod_rooms = mods.get("rooms", []) if mods.get("enabled", True) else []
    # a kit room may keep some of the ship's own interior until the kit has it (kit_modules.keep: "floor", "objects"),
    # and may be wider than its layout rectangle (kit_modules.width: the hull liner's face to face, 29. 9. 2026) - the
    # floor, the ramp's leaf and the bulkheads next to it reach that far
    keep = mods.get("keep", {}) if mod_rooms else {}
    kit_half = {rid: w / 2 for rid, w in (mods.get("width", {}) if mod_rooms else {}).items() if rid in mod_rooms}
    kit_rooms = [r for r in (spec.get("kit") or {}).get("rooms", []) if r not in mod_rooms]
    kit = None
    global KIT, COCKPIT
    KIT = None
    COCKPIT = spec.get("cockpit", {})
    # the modular kit (interior.kit) whenever the recipe has it: its rooms, and the cockpit's rear wall, its gable and
    # details, which need it even when every one of its rooms went to the interior kit (29. 9. 2026: with the hold a
    # kit room the cockpit lost its rear wall's gable - a black void over the cabin's ceiling)
    if spec.get("kit"):
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
        if rid in mod_rooms:
            # the ceiling's dark backing as every room has it (ceiling()): the neighbours' backings rest on it (the
            # cabin's hung free without it - geometry check); above the kit's ceiling, never seen
            box(g["int_dark"], (x0, y0i, H + 0.04), (x1, y1i, H + 0.06))
            for xa, xb in mods.get("stand_in_floor", []):
                if x0 <= xa < xb <= x1:
                    floor_tiles(g, xa, xb, -1.3, 1.3, z0, tile=xb - xa)
            if "floor" in keep.get(rid, []):
                hw = kit_half.get(rid, y1i)
                floor_tiles(g, x0, x1, -hw, hw, z0)
            report.setdefault("kit_modules", []).append(rid)
            report["rooms"].append(rid)
            continue
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
    def wall_half(x):
        """How far a cross wall at x reaches: to the widest kit room next to it (a hull liner's face), else the rooms'."""
        wide = [kit_half[r["id"]] for r in rooms.values() if r["id"] in kit_half and (abs(r["rect"][0] - x) < 0.01 or abs(r["rect"][1] - x) < 0.01)]
        return max(wide) + 0.06 if wide else y1i
    for x in xs:
        if x > 15.3:
            continue
        d = next((dd for dd in doors if dd["axis"] == "x" and abs(dd["at"][0] - x) < 0.01), None)
        wh = wall_half(x)
        if wh > y1i + 0.01:
            # wings out to a hull liner's face, in the liner's outline (vertical, then its chamfer): a box to the
            # ceiling would stand out of the hull where it narrows over the ramp
            vt, rise = 1.7, 0.5
            for sgn in (1, -1):
                zk = vt + (wh - y1i) / 0.75
                pts = [(y1i, 0.0), (wh, 0.0), (wh, vt), (y1i, min(zk, H))]
                if zk > H:
                    pts = [(y1i, 0.0), (wh, 0.0), (wh, vt), (wh - (H - vt) * 0.75, H), (y1i, H)]
                bm = g["int_dark"]
                vs = [bm.verts.new((x + dx, sgn * yy, zz)) for dx in (-0.05, 0.0) for (yy, zz) in pts]
                n = len(pts)
                f0 = bm.faces.new(vs[:n])
                f1 = bm.faces.new(list(reversed(vs[n:])))
                for i in range(n):
                    j = (i + 1) % n
                    bm.faces.new((vs[i], vs[j], vs[n + j], vs[n + i]))
        if abs(x - 1.0) < 0.01:
            if wh > y1i + 0.01:
                # a kit hold: the ramp's header beam over its first 0.6 m, where the hull closes in over the ramp and
                # a kit ceiling does not fit (the ramp frame's housing), a hazard line along its lower edge
                box(g["int_trim"], (x, -1.74, 2.12), (x + 0.6, 1.74, H + 0.02))
                box(g["int_dark"], (x + 0.02, -1.7, 2.1), (x + 0.58, 1.7, 2.12))
                box(g["accent"], (x + 0.58, -1.7, 2.1), (x + 0.6, 1.7, 2.14))
            # the ramp's inside: a closed leaf with ribs (the ramp opens with walking inside the ship)
            box(g["int_dark"], (x - 0.05, y0i, 0), (x, y1i, H))
            box(g["int_panel"], (x, -1.3, 0.02), (x + 0.03, 1.3, 2.1))
            for yy in (-0.9, -0.3, 0.3, 0.9):
                box(g["int_trim"], (x + 0.03, yy - 0.04, 0.05), (x + 0.07, yy + 0.04, 2.05))
            box(g["accent"], (x + 0.03, -1.3, 2.1), (x + 0.05, 1.3, 2.16))
            continue
        full = d is not None and abs(x - rooms["cockpit"]["rect"][0]) < 0.01
        bulkhead(g, x, y0i, y1i, 0.0, H, (d["at"][1], d["width"]) if d else None, 1, full=full)
        if d is not None and not full and spec.get("door_leaves", True):
            # a sliding leaf in this doorway (author 5. 10. 2026: SC's doors open); how far the wall beside it runs
            near = [kit_half[r["id"]] for r in rooms.values() if r["id"] in kit_half and (abs(r["rect"][0] - x) < 0.01 or abs(r["rect"][1] - x) < 0.01)]
            DOOR_LEAVES.append({"x": x, "yc": d["at"][1], "w": d["width"], "half": min(near) if near else y1i, "name": d.get("name", "")})
        if kit is not None:
            # kit panels on the faces that look into kit rooms
            ks = next((v["scale"] for v in report["kit"].values() if isinstance(v, dict) and "scale" in v), None) or _kit_scale(spec, H)
            for rid in kit_rooms:
                rx0, rx1 = rooms[rid]["rect"][0], rooms[rid]["rect"][1]
                if abs(rx1 - x) < 0.01:
                    hs_interior_kit.clad_bulkhead(kit, x - 0.005, -1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H, full=full)
                if abs(rx0 - x) < 0.01:
                    hs_interior_kit.clad_bulkhead(kit, x + 0.045, 1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H, full=full)
            if abs(x - rooms["cockpit"]["rect"][0]) < 0.01:
                # the cockpit's rear wall: kit panels over the plain bulkhead and a satin beam where it meets the
                # frame lining (a large dark plane under the rear window, author 25. 9. 2026)
                # (from the deck: the cockpit floor is raised and the stairs show the wall down to it)
                hs_interior_kit.clad_bulkhead(kit, x + 0.045, 1, y0i, y1i, (d["at"][1], d["width"]) if d else None, ks, 0.0, H, full=full)
                beam = [(y0i, y1i)]
                if full:
                    # stops at the doorway's posts: over the stairs it was the head's first obstacle
                    beam = [(y0i, d["at"][1] - d["width"] / 2 - 0.08), (d["at"][1] + d["width"] / 2 + 0.08, y1i)]
                for ya, yb in beam:
                    box(g["int_trim"], (x + 0.04, ya, H - 0.06), (x + 0.12, yb, H))
                _gable(g["int_panel"], hull, x + 0.04, H, g, (d["at"][1], d["width"]) if full else None)
    # cockpit: floor, step, tub walls to the sill, rear wall, liner above the sill
    ck = rooms["cockpit"]
    zc = ck["floor_z"]
    poly = ck["poly"]
    sill = spec.get("sill_z", 1.05)
    fb = g["int_floor_ck"]                                    # (the cockpit's own floor tone, 7. 10. 2026)
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
            # (7. 10. 2026: the 8.6 cm glowing band shone through the holo MFDs - critic, rounds 1-3 - now a 1.4 cm
            # pinstripe in a dark channel)
            obox(g["int_dark"], (c.x, c.y, sill - 0.036), d, (0, 0, 1), (length, 0.034, 0.012))
            obox(g["int_accent_glow" if "int_accent_glow" in MATS else "accent"], (c.x, c.y, sill - 0.034), d, (0, 0, 1), (length, 0.014, 0.012))
    report["cockpit"] = True
    # every layout object by its name
    eye = recipe["assemble"]["sockets"]["Cockpit"]["location"]
    screen_bm = bmesh.new()
    sockets = {}
    for o in layout["objects"]:
        x0, x1, y0, y1 = o["rect"]
        zr = o.get("z", [0.0, 1.0])
        name = o["name"]
        if o.get("room") in mod_rooms and "objects" not in keep.get(o.get("room"), []):
            # the kit's walls stand for them (the reactor behind a grille, the shield generator behind a hatch)
            report["objects_in_kit_rooms"] = report.get("objects_in_kit_rooms", 0) + 1
            continue
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
            obj_hygiene(g, (x0, x1, y0, y1), zr, kit_half.get(o.get("room")))
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
                hs_cockpit.pilot_seat_v3(g, (x0, x1, y0, y1), zr)   # (v3 5. 10. 2026; pilot_seat = the old box-pad seat)
            else:
                seat(coll, mats, spec, (x0, x1, y0, y1), zr)
        else:
            continue
        report["objects"] += 1
    if kit is not None:
        # fittings in a room the interior kit took over stay out, unless marked "keep" (the fire extinguisher)
        def in_mod_room(f):
            xs = f.get("x") or [f["at"][0]] if f.get("x") or f.get("at") else []
            xs = xs if isinstance(xs, list) else [xs]
            return any(rooms[r]["rect"][0] <= x <= rooms[r]["rect"][1] for r in mod_rooms for x in xs)
        fits = [f for f in spec["kit"].get("fittings", []) if f.get("keep") or not in_mod_room(f)]
        hs_interior_kit.fittings(kit, g, box, dict(spec, kit=dict(spec["kit"], fittings=fits)), lights_out)
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
        # nothing is built in the kit rooms here: a ray there would lay its decal on the dark skin behind the kit
        dspec["_exclude_x"] = [rooms[r]["rect"][:2] for r in mod_rooms]
        dobjs, report["decals"] = hs_interior_decals.build(objs, ship, coll, dspec, ROOT, mats, eye)
        objs += dobjs
    # the sliding door leaves (built open, the game closes them): their own parts Door<n>A/B and sockets
    for n, leaf in enumerate(DOOR_LEAVES):
        for name, at in build_door(leaf, n, ship, coll, mats, H):
            sockets[name] = at
    if holo_centre is not None and "holo" in mats:
        # the ship hologram over the left MFD (hs_cockpit.build_hologram): on the pod's top, found by a ray down
        import hs_cockpit
        from mathutils.bvhtree import BVHTree
        hg = COCKPIT["hologram"]
        centre = holo_centre
        # (the canopy belongs to the envelope: without it the voxel flood ran into the cockpit through its frame)
        exterior = [o for o in coll.objects if o.type == "MESH" and "_Int" not in o.name and not o.name.endswith("_Hologram")
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
    if spec.get("fixture_lights"):
        # a light for every strip and lamp (SC breakdown, 26. 9. 2026: ~1 light per m2, short reach, no shadow)
        import hs_fixture_lights
        report["fixture_lights"] = hs_fixture_lights.fixture_lights(objs, mats, spec["fixture_lights"], lights_out)
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
    # (author 7. 10. 2026: as SC has it) SC-style sticks on both arms: a chrome ball on a hatched base, a slim grip
    # under a silver C-guard (Aurora flies on two sticks; the left one strafes)
    # the hand at 0.47 m from the seat axis, 15 cm ahead of the eye (a seated pilot's forearm along the console)
    if "right" not in KIT_CONSOLES:
        hs_cockpit.sc_stick(g, Vector((right["rect"][0] + 0.8, -0.40, ztop + 0.004)), "ck_flight", Vector((0, 1, 0)))
    if "left" not in KIT_CONSOLES:
        hs_cockpit.sc_stick(g, Vector((left["rect"][0] + 0.8, 0.40, ztop + 0.004)), "ck_rcs", Vector((0, -1, 0)))
    # console edge lights facing the pilot (dim, below the dashboard line)
    for o in (left, right):
        x0, x1, y0, y1 = o["rect"]
        inner = y0 if y0 > 0 else y1
        s_ = 1 if y0 > 0 else -1
        # (critic 7. 10. r1: a burnt-out white line) a soft diffuser set back in a dark channel with satin lips
        box(g["int_dark"], (x0 + 0.04, inner - s_ * 0.006, ztop - 0.066), (x1 - 0.04, inner + s_ * 0.0, ztop - 0.044))
        for za, zb in ((ztop - 0.068, ztop - 0.064), (ztop - 0.046, ztop - 0.042)):
            ya_, yb_ = sorted((inner - s_ * 0.008, inner))
            box(g["int_trim"], (x0 + 0.04, ya_, za), (x1 - 0.04, yb_, zb))
        ya_, yb_ = sorted((inner - s_ * 0.0075, inner - s_ * 0.0065))
        box(g["int_glow_soft"], (x0 + 0.05, ya_, ztop - 0.06), (x1 - 0.05, yb_, ztop - 0.05))
    # the cockpit floor (author 7. 10. 2026: "the floor more - the layout of the objects, how far they are from the
    # seat and the panel"), layered after the SC Aurora's (Docs/Kit/etalon/sc/kreslo_*.jpg, podlaha_*.jpg): plates with
    # seams and corner screws, an anti-slip aisle behind the seat, a perforated footrest plate before it, louvred floor
    # vents along the console feet, marker lights at the aisle's edges; stencils, a hazard edge at the stairs, the
    # walked line and dirt in the corners
    import hs_cockpit as _hc
    Zf, Xf, Yf = Vector((0, 0, 1)), Vector((1, 0, 0)), Vector((0, 1, 0))
    Ymf = Vector((0, -1, 0))
    ci = abs(left["rect"][2])                                 # the consoles' inner face from the axis (0.43)
    sx0, sx1 = seat_o["rect"][0], seat_o["rect"][1]
    fx0, fx1 = 16.22, 18.6                                    # the stairs' top edge .. the cowl's foot
    # 1 plates: dark seams across and along, screws at the crossings
    for xs in (16.55, 17.45, 18.05):
        box(g["int_dark"], (xs - 0.004, -0.95, zc), (xs + 0.004, 0.95, zc + 0.0008))
        for d_ in (-0.007, 0.007):
            box(g["int_trim"], (xs + d_ - 0.002, -0.95, zc), (xs + d_ + 0.002, 0.95, zc + 0.0012))
    for ys in (-ci, ci):
        box(g["int_dark"], (fx0, ys - 0.004, zc), (fx1, ys + 0.004, zc + 0.0008))
    for xs in (16.55, 17.45, 18.05):
        for ys in (-ci - 0.03, -ci + 0.03, ci - 0.03, ci + 0.03):
            cyl(g["int_trim"], (xs + 0.03, ys, zc), (xs + 0.03, ys, zc + 0.002), 0.005, 8)
    # 2 the aisle behind the seat: an anti-slip plate in a satin frame (ribs across), the walked line on it
    ax0, ax1, aw = fx0 + 0.03, sx0 - 0.04, ci - 0.07
    box(g["int_trim"], (ax0 - 0.012, -aw - 0.012, zc), (ax1 + 0.012, aw + 0.012, zc + 0.004))
    box(g["int_floor_ck"], (ax0, -aw, zc), (ax1, aw, zc + 0.006))
    xx = ax0 + 0.02
    while xx < ax1 - 0.02:
        box(g["int_rubber"], (xx, -aw + 0.02, zc + 0.006), (xx + 0.012, aw - 0.02, zc + 0.0085))
        xx += 0.032
    _hc.grime(Vector(((ax0 + ax1) / 2, 0.0, zc + 0.0085)), Zf, Xf, (0.22, ax1 - ax0), "smear", 0.8, wear=True)
    _hc.hazard_band(g, Vector((fx0 + 0.02, 0.0, zc + 0.004)), Ymf, Xf, Zf, 2 * aw, 0.024)
    # 3 the footrest before the seat: a plate sloped up 18 deg towards the cowl, perforated, satin edges, grip bars
    tx0, tx1 = 17.62, 17.92
    t = math.radians(24.0)
    fc = Vector(((tx0 + tx1) / 2, 0.0, zc + 0.02 + math.tan(t) * (tx1 - tx0) / 2))
    nrm = Vector((-math.sin(t), 0.0, math.cos(t)))
    upv = Vector((math.cos(t), 0.0, math.sin(t)))
    _hc.rr_slab(g["int_dark"], fc - nrm * 0.01, Ymf, upv, nrm, 0.62, (tx1 - tx0) / math.cos(t), 0.02, 0.06, 3)       # wedge
    _hc.rr_slab(g["int_housing"], fc, Ymf, upv, nrm, 0.58, (tx1 - tx0) / math.cos(t) - 0.03, 0.015, 0.008, 3)
    _hc.rr_ring(g["int_trim"], fc + nrm * 0.0005, Ymf, upv, nrm, 0.58, (tx1 - tx0) / math.cos(t) - 0.03, 0.015, 0.006, 0.002, 3)
    pl = (tx1 - tx0) / math.cos(t)
    for i in range(36):                                       # dense perforation: small holes, staggered
        for j in range(11):
            p = fc + Ymf * (-0.255 + 0.0146 * i + (0.0073 if j % 2 else 0.0)) + upv * (-pl / 2 + 0.03 + (pl - 0.1) * j / 10) + nrm * 0.0008
            _hc.rr_slab(g["int_dark"], p, Ymf, upv, nrm, 0.0055, 0.0055, 0.0027, 0.0004, 2)
    hb = fc - upv * (pl / 2 - 0.012) + nrm * 0.012                # the heel bar across the foot of the plate
    _hc.tube(g["int_trim"], hb - Ymf * 0.28, hb + Ymf * 0.28, 0.009, 14)
    for sd in (-1, 1):                                        # side cheeks down to the floor, toe strips
        ch = fc + Ymf * (sd * 0.3) - nrm * 0.02
        _hc.rr_slab(g["int_housing"], ch, upv, -nrm, Ymf * sd, pl, 0.07, 0.01, 0.012, 3)
        ts = fc + Ymf * (sd * 0.13) + upv * (pl / 2 - 0.05) + nrm * 0.007
        _hc.rr_slab(g["int_rubber"], ts, Ymf, upv, nrm, 0.16, 0.035, 0.008, 0.003, 2)
        for sv in (-1, 1):
            q = fc + Ymf * (sd * 0.275) + upv * (sv * (pl / 2 - 0.02)) - nrm * 0.0005
            _hc.tube(g["int_trim"], q, q + nrm * 0.002, 0.0045, 8)
    _hc.grime(fc + nrm * 0.009, nrm, upv, (0.5, 0.26), "smear", 0.9, wear=True)
    _hc.stencil("panel_G08", fc + nrm * 0.0092 - upv * (pl / 2 - 0.035) + Ymf * 0.2, nrm, Ymf, upv, 0.4, 9.0)
    # 4 louvred floor vents along the console feet, both sides of the seat and the footwell
    for sd in (-1, 1):
        vy = sd * (ci + 0.0)
        for vx0, vx1 in ((16.3, 16.5), (17.5, 17.6)):
            ya, yb = sorted((vy - sd * 0.0, vy - sd * 0.09))
            box(g["int_trim"], (vx0 - 0.008, ya - 0.008, zc), (vx1 + 0.008, yb + 0.008, zc + 0.003))
            box(g["int_dark"], (vx0, ya, zc - 0.01), (vx1, yb, zc + 0.002))
            xv = vx0 + 0.01
            while xv < vx1 - 0.006:
                box(g["int_housing"], (xv, ya + 0.004, zc - 0.006), (xv + 0.006, yb - 0.004, zc + 0.0015))
                xv += 0.016
        # dirt settled in the corner between the floor and the console's foot
        _hc.grime(Vector(((fx0 + 17.5) / 2, sd * (ci - 0.01), zc + 0.003)), Zf, Yf * sd, (17.5 - fx0, 0.07), "soot", 0.9)
        # marker lights along the aisle's edge, every 30 cm
        xl = fx0 + 0.1
        while xl < sx0 - 0.05:
            yl = sd * (ci - 0.02)
            ya, yb = sorted((yl, yl - sd * 0.012))
            box(g["int_trim"], (xl - 0.018, ya - 0.004, zc), (xl + 0.018, yb + 0.004, zc + 0.004))
            box(g["int_glow_soft"], (xl - 0.012, ya, zc + 0.004), (xl + 0.012, yb, zc + 0.0048))
            xl += 0.3
    # plate numbers and a torque stencil, read from the seat
    _hc.stencil("panel_D05", Vector((16.4, -0.2, zc + 0.0069)), Zf, Ymf, Xf, 0.5, 9.0)       # on the aisle plate
    _hc.stencil("panel_G08", Vector((18.12, 0.6, zc + 0.0009)), Zf, Ymf, Xf, 0.5, 9.0)
    _hc.stencil("st_torque", Vector((18.12, -0.6, zc + 0.0009)), Zf, Ymf, Xf, 0.5, 9.0)
    _hc.grime(Vector((18.2, 0.0, zc + 0.001)), Zf, Xf, (0.9, 0.35), "rim", 0.6)          # dust at the cowl's foot
    # seat rails and pedestal
    x0, x1, y0, y1 = seat_o["rect"]
    for yy in (-0.2, 0.2):
        box(g["int_trim"], (x0 - 0.25, yy - 0.025, zc), (x1 + 0.1, yy + 0.025, zc + 0.03))
        box(g["int_dark"], (x0 - 0.24, yy - 0.006, zc + 0.03), (x1 + 0.09, yy + 0.006, zc + 0.0305))   # the slot
        for xe in (x0 - 0.25, x1 + 0.08):                                                             # end stops
            box(g["int_housing"], (xe, yy - 0.028, zc + 0.03), (xe + 0.024, yy + 0.028, zc + 0.044))
            box(g["int_red"], (xe + 0.006, yy - 0.01, zc + 0.044), (xe + 0.018, yy + 0.01, zc + 0.047))
            for sd_ in (-1, 1):
                cyl(g["int_trim"], (xe + 0.012, yy + sd_ * 0.019, zc + 0.044), (xe + 0.012, yy + sd_ * 0.019, zc + 0.0455), 0.003, 6)
        xb_ = x0 - 0.2
        while xb_ < x1 + 0.08:
            for sd_ in (-1, 1):
                cyl(g["int_dark"], (xb_, yy + sd_ * 0.017, zc + 0.03), (xb_, yy + sd_ * 0.017, zc + 0.033), 0.004, 6)
            xb_ += 0.15
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
