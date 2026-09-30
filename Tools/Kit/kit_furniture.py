"""Cabin furniture of the interior kit (kit_parts.json batch "furniture", 30. 9. 2026).

The author approved the Wayfarer's cabin from the kit and asked for its furniture as kit parts, not one-offs for the
ship: a berth with shelves and a reading light, a suit locker, a hygiene cell and a food dispenser - the four boxes
hs_interior built for the approved layout (Wayfarer_layout.json, each with its purpose). The SC references
(starcitizenreference/Screenshot 2026-09-25 021316 / 021331: a berth alcove with padded walls, a lamp in its corner,
orange edges; storage lockers with orange handles; a galley unit with a dispenser bay) set the level: every part a
carcass with frames, doors and fittings in the kit's language - the warm graphite paint, the lighter structure metal,
orange signal parts, housed lights, screens in the cold UI.

For a hull liner room (section L, kit_liner.py): the back edge stands WALL_GAP off the liner's face - clear of its
frames (8 cm) - and nothing rises above the liner's chamfer (vertical to 1.7 m, then 0.75 m in per metre up).
  Bunk     21  berth 2.1 x 0.85: alcove cheeks to 1.72 m edged in orange, the mattress in three quilted cushions (soft
               surfaces, creased seams, buttons), pillow, blanket, two shelves on brackets with dividers and retaining
               bars, padded back rolls, a reading lamp with its switch, two dim housed lights under the lower shelf; the
               base with the life support's air intake and the kit's recessed plinth. The liner stays visible between
               the back rolls and the shelves (its section number and life support label).
  Locker   10  suit and weapon locker 0.95 x 0.55 x 1.8: a tall suit door with a window (the EVA suit on its stand and a
               light over it inside), a narrow weapon door with a lock cylinder and an orange lever latch, a vented boot
               drawer, a status light; the doors in framed and recessed fields.
  Hygiene  15  hygiene cell 1.45 x 1.0 x 2.05: panelled side walls following the chamfer, a sliding door in three fields
               with a hazard edge in a proud frame (built closed) on its head track and sill, the occupancy light over it,
               an occupancy screen, an extraction grille and its duct to the ceiling, corner posts, kick plates.
  Food     16  galley unit 1.6 x 0.45 at 0.8-1.8 m: a chilled cabinet and a ration drawer, the counter with a rubber
               bullnose, a water dispenser bay (nozzle, drip grille, bay light) in a cream fascia of screwed fields beside
               its screen and labelled buttons, stowage doors above; under it a fold-down seat on its hinge and brackets
               with a back cushion.
Frame: kit_rules "faced" pivot - on the floor under the middle of the back edge, front +X, width along +Y (the viewer's
right facing the front), z up.

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- furniture
"""
import math

from mathutils import Vector

import kit_geo
from kit_batch2 import BEV_MID, BEV_SMALL, label
from kit_geo import frame

WALL_GAP = 0.1               # back edge to the liner's face (its frames stand 8 cm off it)
LINER_VT, LINER_RUN = 1.7, 0.75
FRAME_OUT = 0.08             # the liner's exposed frames: 8 cm off the panels, up the chamfer too (kit_liner FL_OUT)
FRONT = frame((0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0))      # u along +Y, v up, w out of the front (+X)
UP = frame((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1))         # a pad lying on a surface: u +X, v +Y, w up
DEEP = (0.035, 0.012, 0.006)  # a door's recessed field: a flat 3.5 cm border, a 6 mm step 12 mm deep (critic round 3: "flat slabs")


def top_at(x, margin=0.02):
    """The highest a part may reach x in front of its back edge: under the liner's chamfer and the frames standing
    FRAME_OUT off it at every module joint - the chamfer's plane moved FRAME_OUT along its normal (0.8, -0.6) drops by
    FRAME_OUT / 0.6 (kit_clash.py found the berth's back and the galley's top in the frames, 30. 9. 2026)."""
    return LINER_VT + (x + WALL_GAP) / LINER_RUN - FRAME_OUT / 0.6 - margin


def front_plate(p, role, x, y0, y1, z0, z1, t=0.02, bevel=BEV_SMALL, pressed=False, secondary=False, panel=True, press=None):
    """A plate facing +X with its face on the plane x; pressed: the face inset 4 cm and set back 6 mm; press: (border,
    depth) of a deeper field (DEEP for doors)."""
    inset = press or ((0.04, 0.006) if pressed and min(y1 - y0, z1 - z0) > 0.14 else None)
    return p.slab(role, FRONT, y0, y1, z0, z1, t, bevel, 1, proud=x, secondary=secondary, panel=panel, inset=inset)


def ring(p, role, x, y0, y1, z0, z1, w, depth, bevel=0.003, bottom=True):
    """Four members round an opening y0..y1 x z0..z1 on the plane x, w wide, standing depth proud of it (a doorway's
    without the bottom one)."""
    members = [(y0 - w, y1 + w, z1, z1 + w), (y0 - w, y0, z0, z1), (y1, y1 + w, z0, z1)]
    if bottom:
        members.append((y0 - w, y1 + w, z0 - w, z0))
    for (a0, a1, b0, b1) in members:
        p.box(role, (x, a0, b0), (x + depth, a1, b1), bevel=bevel, segments=1, panel=False)


def bar_handle(p, x, y, z0, z1):
    """An upright U handle off a face at x: two standoffs and the grip, 4 cm out."""
    for zz in (z0, z1):
        p.tube("Kit_Structure", (x - 0.002, y, zz), (x + 0.04, y, zz), 0.007, 8)
    p.tube("Kit_Structure", (x + 0.04, y, z0 - 0.01), (x + 0.04, y, z1 + 0.01), 0.009, 10)


def hinge(p, x, y, z0, z1):
    # 11 mm (round 2: "no hinges to be seen" at 8 mm)
    p.tube("Kit_Structure", (x + 0.009, y, z0), (x + 0.009, y, z1), 0.011, 10)


def recessed_pull(p, x, y, hw, z):
    """A pull recessed into a face at x, lined in the signal orange, a lip over it (drawers, cabinet doors)."""
    p.box("Kit_Signal", (x - 0.008, y - hw, z - 0.012), (x + 0.0008, y + hw, z + 0.012), panel=False)
    p.box("Kit_Structure", (x - 0.001, y - hw - 0.006, z + 0.012), (x + 0.006, y + hw + 0.006, z + 0.02), bevel=0.002, segments=1, panel=False)


def slots(p, x, y0, y1, z0, z1, n, vertical=False, w=0.008):
    """A row of n dark vent slots cut into a face at x (a cabinet's air, a drawer's drying)."""
    for k in range(n):
        if vertical:
            c = y0 + (k + 0.5) * (y1 - y0) / n
            p.box("Kit_Seal", (x - 0.004, c - w / 2, z0), (x + 0.0012, c + w / 2, z1), panel=False)
        else:
            c = z0 + (k + 0.5) * (z1 - z0) / n
            p.box("Kit_Seal", (x - 0.004, y0, c - w / 2), (x + 0.0012, y1, c + w / 2), panel=False)


def plinth(p, x_front, y0, y1, h=0.08, back=0.05):
    """The kit's recessed plinth under a carcass: a dark recess set back, a housed cool strip in it."""
    p.box("Kit_Seal", (0.0, y0, 0.0), (x_front - back, y1, h), panel=False)
    p.box("Kit_Structure", (x_front - back, y0 + 0.01, 0.028), (x_front - back + 0.012, y1 - 0.01, 0.056), bevel=0.002, segments=1, panel=False)
    p.box("Kit_GlowCool", (x_front - back + 0.012, y0 + 0.02, 0.036), (x_front - back + 0.015, y1 - 0.02, 0.048), panel=False)


def grille(p, x, y0, y1, z0, z1, pitch=0.026):
    """A framed louvre grille over a dark plenum on the plane x (air in or out)."""
    ring(p, "Kit_Structure", x, y0, y1, z0, z1, 0.02, 0.018)
    p.box("Kit_Seal", (x - 0.03, y0, z0), (x + 0.004, y1, z1), panel=False)
    n = max(2, int((z1 - z0) / pitch))
    for k in range(n):
        z = z0 + (k + 0.5) * (z1 - z0) / n
        p.box("Kit_Structure", (x - 0.004, y0, z - 0.005), (x + 0.012, y1, z + 0.005), panel=False)


def screen(p, x, y0, y1, z0, z1, region):
    """A small display on the plane x: a bezel ring and the page (kit_screens.py region) 1 mm proud."""
    ring(p, "Kit_Plastic", x, y0, y1, z0, z1, 0.012, 0.01, bevel=0.002)
    p.box("Kit_Seal", (x - 0.006, y0, z0), (x + 0.004, y1, z1), panel=False)
    p.slab("Kit_Screen", FRONT, y0, y1, z0, z1, 0.001, proud=x + 0.005, atlas=tuple(region), panel=False)


def _grid_axis(a0, a1, r, step, seams, sw):
    """Grid lines across a pad: rows down its rounded edges, even ones inside, three over every seam."""
    pts = [a0 + k * r for k in (0.0, 0.25, 0.55, 0.8)] + [a1 - k * r for k in (0.0, 0.25, 0.55, 0.8)]
    n = max(1, int(round((a1 - a0 - 2 * r) / step)))
    pts += [a0 + r + i * (a1 - a0 - 2 * r) / n for i in range(n + 1)]
    for s in seams:
        pts += [s - sw, s, s + sw]
    pts = sorted(pts)
    out = [pts[0]]
    for q in pts[1:]:
        if q - out[-1] > 0.003:
            out.append(q)
    out[-1] = a1
    return out


def pad_edge(t, r, d):
    """A pad's height d in from its edge (on the rounded rim, no crown): where the piping lies."""
    e = min(1.0, max(0.0, d / r))
    return t - r + r * math.sqrt(max(0.0, 1.0 - (1.0 - e) ** 2))


def pad(p, m, u0, u1, v0, v1, t, r, crown=0.01, seams_u=(), seams_v=(), dent=None, step=0.05, buttons=True, sd=0.005):
    """A cushion as one soft surface in the frame m (u, v across it, w up out of its base at w = 0; critic round 3:
    "smooth vinyl, drawn seams, sharp edges"): the edges rounded over r, every quilted panel between the seams crowned,
    the seams creased, a dimple and a button where two cross, an optional dent (u, v, depth, radius - the pillow's
    head). The base stays open (it lies on something)."""
    sw, td = 0.014, 0.007
    r = min(r, 0.45 * (u1 - u0), 0.45 * (v1 - v0), 0.9 * t)
    us = _grid_axis(u0, u1, r, step, seams_u, sw)
    vs = _grid_axis(v0, v1, r, step, seams_v, sw)
    bu, bv = [u0] + sorted(seams_u) + [u1], [v0] + sorted(seams_v) + [v1]
    tufts = [(a, b) for a in seams_u for b in seams_v]

    def swell(x, bounds):
        for a, b in zip(bounds, bounds[1:]):
            if a <= x <= b:
                return math.sin(math.pi * (x - a) / (b - a))
        return 0.0

    def h(u, v):
        d = min(u - u0, u1 - u, v - v0, v1 - v)
        e = min(1.0, max(0.0, d / r))
        rim = math.sqrt(max(0.0, 1.0 - (1.0 - e) ** 2))
        z = t - r + r * rim + crown * rim * swell(u, bu) * swell(v, bv)
        for s in seams_u:
            z -= sd * rim * math.exp(-((u - s) / (0.45 * sw)) ** 2)
        for s in seams_v:
            z -= sd * rim * math.exp(-((v - s) / (0.45 * sw)) ** 2)
        for (a, b) in tufts:
            z -= td * math.exp(-((u - a) ** 2 + (v - b) ** 2) / 0.018 ** 2)
        if dent:
            a, b, dd, rr = dent
            z -= dd * rim * math.exp(-((u - a) ** 2 + (v - b) ** 2) / rr ** 2)
        return z

    verts, idx = [], {}
    for i, u in enumerate(us):
        for j, v in enumerate(vs):
            idx[i, j] = len(verts)
            verts.append(m @ Vector((u, v, h(u, v))))
    nu, nv = len(us), len(vs)
    faces = [(idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]) for i in range(nu - 1) for j in range(nv - 1)]
    rim_ring = ([(i, 0) for i in range(nu)] + [(nu - 1, j) for j in range(1, nv)] + [(i, nv - 1) for i in range(nu - 2, -1, -1)]
                + [(0, j) for j in range(nv - 2, 0, -1)])
    base = []
    for (i, j) in rim_ring:
        base.append(len(verts))
        verts.append(m @ Vector((us[i], vs[j], 0.0)))
    n = len(rim_ring)
    for k in range(n):
        faces.append((base[k], base[(k + 1) % n], idx[rim_ring[(k + 1) % n]], idx[rim_ring[k]]))
    if m.to_3x3().determinant() < 0:
        faces = [tuple(reversed(f)) for f in faces]
    p.mesh("Kit_Cushion", [tuple(v) for v in verts], faces)
    if buttons:
        w = (m.to_3x3() @ Vector((0, 0, 1))).normalized()
        for (a, b) in tufts:
            c = m @ Vector((a, b, h(a, b)))
            p.tube("Kit_Fabric", tuple(c - w * 0.003), tuple(c + w * 0.003), 0.008, 10)
    return h


def piping(p, x0, x1, y0, y1, z, inset=0.012, r=0.006):
    """A welt cord round a cushion's top, its axis at height z (a thin dark tube along each edge on the rounded rim)."""
    for yy in (y0 + inset, y1 - inset):
        p.tube("Kit_Fabric", (x0 + 0.03, yy, z), (x1 - 0.03, yy, z), r, 8)
    for xx in (x0 + inset, x1 - inset):
        p.tube("Kit_Fabric", (xx, y0 + 0.03, z), (xx, y1 - 0.03, z), r, 8)


def ellipsoid(p, role, c, rx, ry, rz, seg=16, rings=10):
    """A smooth ellipsoid (a helmet's shell, a shoulder)."""
    c = Vector(c)
    verts = [c + Vector((0, 0, -rz))]
    for k in range(1, rings):
        th = math.pi * k / rings - math.pi / 2
        for i in range(seg):
            ph = 2 * math.pi * i / seg
            verts.append(c + Vector((rx * math.cos(th) * math.cos(ph), ry * math.cos(th) * math.sin(ph), rz * math.sin(th))))
    verts.append(c + Vector((0, 0, rz)))
    top = len(verts) - 1

    def ix(k, i):
        return 1 + (k - 1) * seg + i % seg
    faces = [(0, ix(1, i + 1), ix(1, i)) for i in range(seg)]
    faces += [(ix(k, i), ix(k, i + 1), ix(k + 1, i + 1), ix(k + 1, i)) for k in range(1, rings - 1) for i in range(seg)]
    faces += [(top, ix(rings - 1, i), ix(rings - 1, i + 1)) for i in range(seg)]
    p.mesh(role, [tuple(v) for v in verts], faces)


def offset_path(path, off):
    """A polyline (x, z) moved off by `off` to the right of its direction, corners mitred."""
    pts = [Vector(q) for q in path]
    segs = []
    for a, b in zip(pts, pts[1:]):
        d = (b - a).normalized()
        segs.append((a + Vector((d.y, -d.x)) * off, d))
    out = [segs[0][0]]
    for (a, da), (b, db) in zip(segs, segs[1:]):
        s = ((b.x - a.x) * db.y - (b.y - a.y) * db.x) / (da.x * db.y - da.y * db.x)
        out.append(a + da * s)
    d = segs[-1][1]
    out.append(pts[-1] + Vector((d.y, -d.x)) * off)
    return [(v.x, v.y) for v in out]


# =============================================================================== the berth
def bunk(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D = 0.85
    hw = L / 2                       # outer half width
    iw = hw - 0.03                   # between the cheeks
    zp = 0.42                        # the platform's top
    # the cheeks at the head and the foot: the bed's sides, then stepping back to carry the shelves (the alcove)
    zt = top_at(0.0)                 # 1.66 at the back
    prof = [(0.0, 0.0), (D, 0.0), (D, 0.72), (0.32, 0.98), (0.32, 1.72), ((1.72 - zt) * LINER_RUN + 0.01, 1.72), (0.0, zt)]
    assert all(z <= top_at(x) for x, z in prof)
    # an orange edge down each cheek's front, up its slope and the alcove's upright (the reference's berth frame), 8 mm
    # proud (round 3: "the orange bar at the foot ends in the air" - it stopped where the cheek turned back)
    edge = [(D, 0.12), (D, 0.72), (0.32, 0.98), (0.32, 1.7)]
    strip = edge + list(reversed(offset_path(edge, 0.008)))
    for s in (1, -1):
        m = frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0))
        p.poly_prism("Kit_Primary", prof, m, 0.03, bevel=0.004, segments=1)
        p.poly_prism("Kit_Signal", strip, frame((0, s * (hw - 0.016), 0), (1, 0, 0), (0, 0, 1), (0, s, 0)), 0.012, panel=False)
    # the base: pressed front with the life support's air intake, the recessed plinth under it
    plinth(p, D - 0.03, -iw, iw)
    front_plate(p, "Kit_Primary", D - 0.03, -iw, -0.31, 0.08, zp - 0.02, pressed=True)
    front_plate(p, "Kit_Primary", D - 0.03, 0.31, iw, 0.08, zp - 0.02, pressed=True)
    front_plate(p, "Kit_Primary", D - 0.03, -0.31, 0.31, 0.08, 0.13, panel=False)
    front_plate(p, "Kit_Primary", D - 0.03, -0.31, 0.31, zp - 0.07, zp - 0.02, panel=False)
    grille(p, D - 0.03, -0.29, 0.29, 0.15, zp - 0.09)
    p.box("Kit_Seal", (0.0, -iw, 0.08), (D - 0.05, iw, zp - 0.02), panel=False)       # the cavity's back behind the front
    # the platform and its front rail (a lip that keeps the mattress on in low gravity)
    p.box("Kit_Structure", (0.0, -iw, zp - 0.02), (D, iw, zp), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (D - 0.035, -iw, zp), (D, iw, zp + 0.05), bevel=0.004, segments=1, panel=False)
    # the mattress in three quilted cushions (rounds 1-3: "smooth vinyl, drawn seams"): each a soft surface, two seams
    # along its depth and one across creased into it, a button in a dimple where they cross, piping on the rim
    n, T, R = 3, 0.14, 0.035
    span = 2 * iw - 0.01
    xm = (0.03 + D - 0.04) / 2
    top = zp + T
    for k in range(n):
        y0 = -iw + 0.005 + k * span / n + 0.004
        y1 = y0 + span / n - 0.008
        pad(p, frame((0, 0, zp), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.03, D - 0.04, y0, y1, T, R, crown=0.014,
            seams_u=(xm,), seams_v=(y0 + (y1 - y0) / 3, y0 + 2 * (y1 - y0) / 3))
        piping(p, 0.03, D - 0.04, y0, y1, zp + pad_edge(T, R, 0.012) - 0.002)
    # the pillow: fuller, a dent where the head lies
    # (verification round: "a square block, no dent") the dent 4 cm deep, the rim standing round it
    pad(p, frame((0, 0, top), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.1, 0.52, -iw + 0.04, -iw + 0.38, 0.095, 0.04, crown=0.012,
        dent=(0.3, -iw + 0.21, 0.04, 0.1))
    # the blanket folded at the foot: the fold rolled at its head side, one end hanging over the front, a hem band
    # (round 1: "a tonal block, no fold or edge")
    by0, by1 = iw - 0.42, iw - 0.05
    p.box("Kit_Fabric", (0.05, by0, top), (D + 0.005, by1, top + 0.035), bevel=0.016, segments=3, panel=False)
    p.box("Kit_Fabric", (D + 0.005, by0, 0.36), (D + 0.025, by1, top + 0.035), bevel=0.009, segments=3, panel=False)
    p.tube("Kit_Fabric", (0.05, by0 + 0.018, top + 0.0175), (D + 0.005, by0 + 0.018, top + 0.0175), 0.0185, 10)
    p.box("Kit_Cushion", (D + 0.025, by0 + 0.01, 0.37), (D + 0.028, by1 - 0.01, 0.395), panel=False)
    # the back: a panel behind the rolls, one behind the shelves; between them the liner shows (its section number)
    front_plate(p, "Kit_Primary", 0.02, -iw, iw, zp, 1.02, pressed=True)
    front_plate(p, "Kit_Primary", 0.02, -iw, iw, 1.12, zt, pressed=True)      # (from 1.12: the lower shelf's brackets on it)
    # two padded rolls on it (into the pressed panel's 6 mm inset - geometry check), quilted every ~0.34 m
    nv = int(round((2 * iw - 0.04) / 0.34))
    seams = tuple(-iw + 0.02 + k * (2 * iw - 0.04) / nv for k in range(1, nv))
    for (z0, z1) in ((0.6, 0.8), (0.8, 1.0)):
        # (verification round: "a smooth band with a seam, no swelling or buttons") fuller panels, buttoned
        pad(p, frame((0.013, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), -iw + 0.02, iw - 0.02, z0 + 0.004, z1 - 0.004, 0.087, 0.03,
            crown=0.022, seams_u=seams, seams_v=((z0 + z1) / 2,), step=0.07, sd=0.008)
    # two shelves between the cheeks (round 3: "two long bare boards"): each on three brackets into the back panel,
    # split in three by dividers that keep things from sliding, a lip at the front, a retaining bar on square posts
    for zs in (1.28, 1.56):
        p.box("Kit_Structure", (0.02, -iw, zs - 0.02), (0.31, iw, zs), bevel=0.003, segments=1, panel=False)
        p.box("Kit_Structure", (0.295, -iw, zs), (0.31, iw, zs + 0.03), bevel=0.002, segments=1, panel=False)
        for yy in (-0.55, 0.0, 0.55):
            # (verification round: "brackets not to be seen, posts read as pins") 17 x 13 cm, 14 mm; posts 18 mm
            p.poly_prism("Kit_Structure", [(0.014, zs - 0.02), (0.17, zs - 0.02), (0.014, zs - 0.15)],
                         frame((0, yy + 0.007, 0), (1, 0, 0), (0, 0, 1), (0, 1, 0)), 0.014, bevel=0.002, segments=1)
        for yy in (-0.35, 0.35):
            p.box("Kit_Structure", (0.014, yy - 0.004, zs), (0.295, yy + 0.004, zs + 0.1), bevel=0.002, segments=1, panel=False)
        for yy in (-iw + 0.012, -0.35, 0.35, iw - 0.012):
            p.box("Kit_Structure", (0.293, yy - 0.009, zs + 0.03), (0.311, yy + 0.009, zs + 0.1), bevel=0.002, segments=1, panel=False)
        p.tube("Kit_Structure", (0.302, -iw + 0.005, zs + 0.085), (0.302, iw - 0.005, zs + 0.085), 0.008, 10)
    # the berth light under the lower shelf (round 1: "a highlight on the shelf edges, not a warm strip"; round 3: "one
    # even band the whole width - the lamp should lead"): two short housed diffusers, a dim rect light under each
    for k, (a0, a1) in enumerate(((-0.9, -0.25), (0.25, 0.9))):
        p.box("Kit_Structure", (0.19, a0, 1.25), (0.29, a1, 1.26), bevel=0.002, segments=1, panel=False)
        p.box("Kit_GlowWarm", (0.2, a0 + 0.012, 1.245), (0.28, a1 - 0.012, 1.25), panel=False, bezel_face=-1)
        p.socket("Light_Berth_%d" % k, (0.24, (a0 + a1) / 2, 1.24), x=(0, 0, -1), z=(1, 0, 0), type="rect", role="warm", cd=0.9,
                 radius_m=1.4, width_cm=(a1 - a0 - 0.024) * 100.0, height_cm=6.0, dir_ue=[0.0, 0.0, -1.0], along_ue=[0.0, -1.0, 0.0])
    # the reading lamp on the head cheek's inner face: a base, a short arm, a round head with a glowing lens aimed at
    # the pillow (round 1: "a dark box, reads as nothing"); its switch under it
    yl = -iw
    lb = Vector((0.23, yl, 1.15))
    p.box("Kit_Structure", (lb.x - 0.03, yl, lb.z - 0.03), (lb.x + 0.03, yl + 0.012, lb.z + 0.03), bevel=0.004, segments=1, panel=False)
    # (round 2: "a white plastic cylinder, no light on the pillow"): a graphite head, the lens in an orange ring, a
    # joint at the base, aimed at the pillow; 15 cd in a 75 degree cone (60 burnt the pillow white, 30 left a hard spot -
    # round 3)
    hc = Vector((lb.x + 0.02, yl + 0.1, lb.z - 0.02))
    d = (Vector((0.31, -iw + 0.21, top + 0.05)) - hc).normalized()
    p.box("Kit_Structure", (lb.x - 0.012, yl + 0.01, lb.z - 0.012), (lb.x + 0.012, yl + 0.03, lb.z + 0.012), bevel=0.005, segments=2, panel=False)
    p.tube("Kit_Structure", (lb.x, yl + 0.02, lb.z), tuple(hc), 0.007, 8)
    ha, hb = hc - d * 0.035, hc + d * 0.035
    p.tube("Kit_Plastic", tuple(ha), tuple(hb), 0.03, 16)
    p.tube("Kit_Signal", tuple(hb - d * 0.001), tuple(hb + d * 0.002), 0.031, 16)
    p.tube("Kit_GlowWarm", tuple(hb + d * 0.002), tuple(hb + d * 0.005), 0.023, 16)
    ls = hb + d * 0.02
    p.socket("Light_Reading_0", tuple(ls), x=tuple(d), z=(1, 0, 0), type="spot", role="warm", cd=15.0,
             cone_deg=75.0, radius_m=1.8, source_radius_cm=2.5, dir_ue=[d.x, -d.y, d.z])
    p.box("Kit_Plastic", (0.17, yl, 0.88), (0.27, yl + 0.012, 0.96), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (0.19, yl + 0.012, 0.9), (0.21, yl + 0.02, 0.94), panel=False)
    p.box("Kit_GlowSignal", (0.245, yl + 0.012, 0.93), (0.255, yl + 0.015, 0.94), panel=False)
    label(p, "st_service", (D - 0.03 - 0.003, -0.5, 0.26), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.4, True)
    p.grime("soot", (D - 0.03, 0.0, 0.1), (1, 0, 0), (0, 0, -1), (2 * iw - 0.1, 0.1), 0.8)
    p.collision_box((0.0, -hw, 0.0), (D, hw, zp + 0.2))
    return p


# =============================================================================== the suit and weapon locker
def locker(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D, H = 0.55, 1.8
    hw = L / 2
    fx = D                               # the carcass front
    # the carcass: sides, top, back, the recessed plinth
    zc = top_at(0.0)
    xc = (H - zc) * LINER_RUN + 0.005                 # the back top edge chamfered under the liner's frames
    prof = [(0.0, 0.0), (D, 0.0), (D, H), (xc, H), (0.0, zc)]
    for s in (1, -1):
        p.poly_prism("Kit_Primary", prof, frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0)), 0.025, bevel=0.004, segments=1)
    yi = hw - 0.025
    p.box("Kit_Primary", (xc, -yi, H - 0.03), (D, yi, H), bevel=0.003, segments=1)
    p.quads("Kit_Primary", [[(0.0, -yi, zc), (xc, -yi, H), (xc, yi, H), (0.0, yi, zc)]], toward=(-1.0, 0.0, 4.0))
    p.box("Kit_Seal", (0.0, -yi, 0.08), (0.02, yi, zc), panel=False)
    plinth(p, fx, -hw + 0.025, hw - 0.025)
    # the front frame: outer members, the mullion between the doors, the rail over the boot drawer
    yi0, yi1, zi0, zi1 = -hw + 0.055, hw - 0.055, 0.11, H - 0.06
    # 2.6 cm deep: the doors sit 1.6 cm back in it (round 1: "doors and frame in one plane, no depth")
    ring(p, "Kit_Structure", fx, yi0, yi1, zi0, zi1, 0.03, 0.026)
    ym = hw - 0.055 - 0.32                # the weapon door's inner edge
    p.box("Kit_Structure", (fx, ym - 0.03, 0.35), (fx + 0.026, ym, zi1), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (fx, yi0, 0.35), (fx + 0.026, yi1, 0.38), bevel=0.003, segments=1, panel=False)
    # the suit door: a window high enough for the helmet, a recessed field with vent slots under it, the U handle and
    # a catch at its meeting edge, hinges outside (round 3: "flat slabs, one detail a door")
    dy0, dy1, dz0, dz1 = yi0 + 0.004, ym - 0.034, 0.384, zi1 - 0.004
    wy0, wy1, wz0, wz1 = dy0 + 0.1, dy1 - 0.1, 0.98, dz1 - 0.06
    df = fx + 0.01                       # the doors' faces, 6 mm behind the frame's
    front_plate(p, "Kit_Primary", df, dy0, dy1, dz0, wz0, secondary=True, press=DEEP)
    for (a0, a1, b0, b1) in ((dy0, dy1, wz1, dz1), (dy0, wy0, wz0, wz1), (wy1, dy1, wz0, wz1)):
        front_plate(p, "Kit_Primary", df, a0, a1, b0, b1, secondary=True)
    ring(p, "Kit_Structure", df, wy0, wy1, wz0, wz1, 0.014, 0.008, bevel=0.002)
    p.box("Kit_Glass", (df - 0.014, wy0, wz0), (df - 0.01, wy1, wz1), panel=False)
    slots(p, df - DEEP[1], dy0 + 0.08, dy1 - 0.08, 0.5, 0.62, 5)
    # inside, seen through the window (round 2: "a black hole"; round 3: "an indefinite shape"): the EVA suit on its
    # stand in its light shell - helmet with a dark visor, the orange neck ring, shoulders, torso, arms, chest pack -
    # under a spot at the top front
    yc = (wy0 + wy1) / 2
    p.box("Kit_Structure", (0.02, yc - 0.02, 1.3), (0.24, yc + 0.02, 1.33), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Accent", (0.2, yc - 0.12, 0.98), (0.36, yc + 0.12, 1.34), bevel=0.045, segments=3, panel=False)
    for s in (1, -1):
        ellipsoid(p, "Kit_Accent", (0.28, yc + s * 0.125, 1.3), 0.075, 0.07, 0.06, seg=12, rings=8)
        p.tube("Kit_Accent", (0.28, yc + s * 0.15, 1.28), (0.29, yc + s * 0.16, 1.0), 0.042, 12)
    p.box("Kit_Structure", (0.345, yc - 0.08, 1.1), (0.372, yc + 0.08, 1.26), bevel=0.008, segments=1, panel=False)
    p.box("Kit_Signal", (0.37, yc - 0.03, 1.2), (0.376, yc + 0.03, 1.23), panel=False)
    # (verification round: "a smooth dummy") a belt, the life support's two hoses from the chest pack up to the ring
    p.box("Kit_Rubber", (0.2, yc - 0.125, 1.03), (0.366, yc + 0.125, 1.06), bevel=0.01, segments=2, panel=False)
    for s in (1, -1):
        p.tube("Kit_Rubber", (0.372, yc + s * 0.065, 1.24), (0.37, yc + s * 0.075, 1.3), 0.011, 10)
        p.tube("Kit_Rubber", (0.37, yc + s * 0.075, 1.3), (0.335, yc + s * 0.06, 1.345), 0.011, 10)
    p.tube("Kit_Signal", (0.28, yc, 1.335), (0.28, yc, 1.375), 0.075, 16)
    ellipsoid(p, "Kit_Accent", (0.28, yc, 1.49), 0.115, 0.105, 0.125)
    p.box("Kit_Seal", (0.335, yc - 0.075, 1.45), (0.4, yc + 0.075, 1.54), bevel=0.028, segments=3, panel=False)
    p.box("Kit_GlowDim", (0.44, wy0, H - 0.035), (0.5, wy1, H - 0.03), panel=False, bezel_face=-1)
    sd = (Vector((0.28, yc, 1.3)) - Vector((0.46, yc, 1.74))).normalized()
    p.socket("Light_Suit_0", (0.46, yc, 1.74), x=tuple(sd), z=(1, 0, 0), type="spot", role="warm", cd=3.0, cone_deg=70.0,
             radius_m=1.0, source_radius_cm=3.0, dir_ue=[sd.x, -sd.y, sd.z])
    bar_handle(p, df, dy1 - 0.04, 1.0, 1.3)
    p.box("Kit_Structure", (df, dy1 - 0.06, dz1 - 0.05), (df + 0.006, dy1 - 0.02, dz1 - 0.02), bevel=0.002, segments=1, panel=False)
    hinge(p, df + 0.002, dy0 + 0.004, dz0 + 0.02, dz1 - 0.02)      # a piano hinge (verification round: "hinges only hinted")
    # the weapon door: a pressed door, a lock cylinder and an orange lever latch at its meeting edge
    ey0, ey1 = ym + 0.004, yi1 - 0.004
    front_plate(p, "Kit_Primary", df, ey0, ey1, dz0, dz1, t=0.02, pressed=True, secondary=True)
    # the lock: a keyed module on its plate; the latch: a backing plate, the body, the orange lever on a pivot, LOCK
    # beside it (round 1: "a thin bar without a pivot, the lock a dot")
    c = (df + 0.005, ey0 + 0.06, 1.1)
    p.box("Kit_Structure", (df, c[1] - 0.025, c[2] - 0.04), (df + 0.005, c[1] + 0.025, c[2] + 0.04), bevel=0.002, segments=1, panel=False)
    p.tube("Kit_Structure", c, (c[0] + 0.012, c[1], c[2]), 0.016, 14)
    p.box("Kit_Seal", (c[0] + 0.012, c[1] - 0.002, c[2] - 0.008), (c[0] + 0.0135, c[1] + 0.002, c[2] + 0.008), panel=False)
    p.box("Kit_Structure", (df, ey0 + 0.025, 1.17), (df + 0.004, ey0 + 0.095, 1.37), bevel=0.002, segments=1, panel=False)
    p.box("Kit_Structure", (df + 0.004, ey0 + 0.035, 1.2), (df + 0.016, ey0 + 0.085, 1.34), bevel=0.003, segments=1, panel=False)
    p.tube("Kit_Structure", (df + 0.016, ey0 + 0.06, 1.315), (df + 0.032, ey0 + 0.06, 1.315), 0.011, 12)
    p.box("Kit_Signal", (df + 0.016, ey0 + 0.045, 1.215), (df + 0.03, ey0 + 0.075, 1.33), bevel=0.003, segments=1, panel=False)
    label(p, "ck_lock", (df, ey0 + 0.19, 1.27), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.3, True)
    hinge(p, df + 0.002, ey1 - 0.004, dz0 + 0.02, dz1 - 0.02)
    # the boot drawer: a recessed field with drying slots, the pull recessed along its top border (round 1: "the drawer
    # reads as part of the doors"; round 3: "vent slots on the boot drawer")
    front_plate(p, "Kit_Primary", df, yi0 + 0.004, yi1 - 0.004, zi0 + 0.004, 0.346, secondary=True, press=DEEP)
    recessed_pull(p, df, 0.0, 0.12, 0.325)
    slots(p, df - DEEP[1], -0.3, 0.3, 0.19, 0.26, 14, vertical=True)
    # a status light on the frame's head
    p.box("Kit_GlowCool", (fx + 0.026, yi1 - 0.06, zi1 + 0.01), (fx + 0.029, yi1 - 0.03, zi1 + 0.02), panel=False)
    label(p, "st_inspect", (df, (ey0 + ey1) / 2, 0.62), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.4, True)
    p.grime("soot", (df, 0.0, 0.14), (1, 0, 0), (0, 0, -1), (L - 0.2, 0.08), 0.8)
    p.collision_box((0.0, -hw, 0.0), (D + 0.06, hw, H))
    return p


# =============================================================================== the hygiene cell
def hygiene(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D, H = 1.0, 2.05
    hw = L / 2
    # the roof: sloped under the chamfer, then a notch under the liner's cable tray (on the chamfer 0.27-0.34 m off the
    # face, down to 1.99 m - the first roof at 2.05 ran into it), then flat at the cell's height
    zb, zn = top_at(0.0), 1.95
    xn = (zn - zb) * LINER_RUN
    xs = (H - top_at(0.0, 0.0)) * LINER_RUN + 0.02    # the flat roof clear of the frames' line by 2 cm
    prof = [(0.0, 0.0), (D, 0.0), (D, H), (xs, H), (xs, zn), (xn, zn), (0.0, zb)]
    assert all(z <= top_at(x) + 1e-6 for x, z in prof)
    for s in (1, -1):
        m = frame((0, s * hw, 0), (1, 0, 0), (0, 0, 1), (0, s, 0))
        p.poly_prism("Kit_Primary", prof, m, 0.03, bevel=0.004, segments=1)
        # the side walls in panels (round 3: "a big dark mass with no edge"): a seam across at 1 m and one up the
        # middle, a kick band at the foot
        for (a, b) in (((0.04, 1.017), (D - 0.04, 1.023)), ((0.497, 0.12), (0.503, 1.017)), ((0.497, 1.023), (0.503, H - 0.04))):
            p.box("Kit_Seal", (a[0], min(s * (hw - 0.003), s * (hw + 0.0012)), a[1]), (b[0], max(s * (hw - 0.003), s * (hw + 0.0012)), b[1]),
                  panel=False)
        p.box("Kit_Structure", (0.02, min(s * hw, s * (hw + 0.004)), 0.0), (D - 0.035, max(s * hw, s * (hw + 0.004)), 0.1),
              bevel=0.002, segments=1, panel=False)
    # the extraction filter's access hatch on its +Y side, under the fan and clear of a neighbour 0.6 m deep (the
    # cabin's locker; round 3: "a big dark mass at the cabin's entrance" - the side seen from there at eye level): a
    # proud frame, the pressed lid, four bolts, the orange pull tab, its label
    side = frame((0, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 1, 0))       # u along -X, v up, w out of the +Y side
    hz0, hz1 = 1.14, 1.74
    for (a0, a1, b0, b1) in ((0.62, 0.94, hz1, hz1 + 0.02), (0.62, 0.94, hz0 - 0.02, hz0), (0.62, 0.64, hz0, hz1), (0.92, 0.94, hz0, hz1)):
        p.box("Kit_Structure", (a0, hw, b0), (a1, hw + 0.01, b1), bevel=0.002, segments=1, panel=False)
    p.slab("Kit_Primary", side, -0.92, -0.64, hz0, hz1, 0.012, BEV_SMALL, 1, proud=hw + 0.006, secondary=True, inset=(0.03, 0.004))
    for xx in (0.66, 0.9):
        for zz in (hz0 + 0.02, hz1 - 0.02):
            p.tube("Kit_Structure", (xx, hw + 0.005, zz), (xx, hw + 0.01, zz), 0.006, 8)
    p.box("Kit_Signal", (0.74, hw + 0.004, hz0 + 0.06), (0.82, hw + 0.0072, hz0 + 0.075), panel=False)
    label(p, "st_service", (0.78, hw + 0.006, hz1 - 0.14), (0, 1, 0), (-1, 0, 0), (0, 0, 1), 0.35, True)
    # the roof's plates; the extraction fan on it, its duct up into the ceiling
    yi = hw - 0.03
    p.box("Kit_Primary", (xs, -yi, H - 0.03), (D, yi, H), panel=False)
    p.box("Kit_Primary", (xn, -yi, zn - 0.03), (xs, yi, zn), panel=False)
    p.box("Kit_Primary", (xs - 0.03, -yi, zn), (xs, yi, H - 0.03), panel=False)
    p.quads("Kit_Primary", [[(0.0, -yi, zb), (xn, -yi, zn), (xn, yi, zn), (0.0, yi, zb)]], toward=(1.0, 0.0, 4.0))
    # (0.39-0.67 m out: at 0.75 its box reached the ceiling services' strut channels - kit_clash.py)
    p.box("Kit_Structure", (0.39, -0.16, H), (0.67, 0.16, H + 0.08), bevel=0.006, segments=1)
    # a metal duct with dark collars (round 2: "the duct merges with the frame and the ceiling")
    p.tube("Kit_Structure", (0.53, 0.0, H + 0.08), (0.53, 0.0, 2.31), 0.05, 14, caps=False)
    for zc in (H + 0.08, 2.28):
        p.tube("Kit_Primary", (0.53, 0.0, zc - 0.012), (0.53, 0.0, zc + 0.012), 0.058, 14)
    # the front wall either side of the doorway and over it (pressed panels), kick plates at their foot
    dw, dh = 0.4, 1.97
    fx = D
    for (y0, y1) in ((-hw, -dw - 0.04), (dw + 0.04, hw)):
        # the secondary graphite (round 1: "milky brown, lighter than the walls")
        front_plate(p, "Kit_Primary", fx, y0, y1, 0.0, H, t=0.03, pressed=True, secondary=True)
        p.slab("Kit_Trim", FRONT, y0 + 0.02, y1 - 0.02, 0.01, 0.11, 0.006, BEV_SMALL, 1, proud=fx + 0.003, trim="kickplate", panel=False)
    front_plate(p, "Kit_Primary", fx, -dw - 0.04, dw + 0.04, dh + 0.04, H, t=0.03, secondary=True)
    # corner posts in the structure metal, the door's frame proud of the wall
    for s in (1, -1):
        p.box("Kit_Structure", (fx - 0.035, min(s * (hw - 0.035), s * (hw + 0.005)), 0.0), (fx + 0.012, max(s * (hw - 0.035), s * (hw + 0.005)), H),
              bevel=0.004, segments=1, panel=False)
    ring(p, "Kit_Structure", fx, -dw, dw, 0.0, dh, 0.04, 0.035, bevel=0.008, bottom=False)     # (round 2: "a thin frame")
    # the door (built closed - the layout's walk_exempt; rounds 1-3: "one flat slab, nothing says it slides"): the
    # leaf's body, three fields on it with dark gaps between, a hazard band on its leading edge, the pull in the middle
    # field; its head track over it, a threshold with the guide groove under it, the seal at the jamb
    p.box("Kit_Seal", (fx - 0.06, -dw, 0.0), (fx - 0.04, dw, dh), panel=False)
    front_plate(p, "Kit_Primary", fx - 0.012, -dw + 0.006, dw - 0.006, 0.012, dh - 0.03, t=0.02, panel=False)
    # (verification round: "thin grooves, still one slab") the fields 12 mm off the body, 2 cm apart, the middle one
    # in the primary paint
    lf = fx                              # the fields' faces
    for k, (z0, z1) in enumerate(((0.02, 0.61), (0.63, 1.33), (1.35, dh - 0.036))):
        front_plate(p, "Kit_Primary", lf, -dw + 0.018, dw - 0.066, z0, z1, t=0.02, secondary=k != 1)
    p.slab("Kit_Trim", FRONT, dw - 0.058, dw - 0.018, 0.02, dh - 0.036, 0.012, BEV_SMALL, 1, proud=lf, trim="hazard", panel=False)
    p.box("Kit_Structure", (lf, dw - 0.14, 0.84), (lf + 0.004, dw - 0.08, 1.26), bevel=0.002, segments=1, panel=False)
    p.box("Kit_Signal", (lf + 0.001, dw - 0.125, 0.92), (lf + 0.005, dw - 0.095, 1.18), panel=False)
    p.box("Kit_Structure", (lf + 0.004, dw - 0.123, 0.95), (lf + 0.012, dw - 0.097, 0.97), panel=False)
    p.box("Kit_Structure", (fx - 0.03, -dw, dh - 0.03), (fx, dw, dh), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Seal", (fx - 0.001, -dw + 0.01, dh - 0.02), (fx + 0.0008, dw - 0.01, dh - 0.012), panel=False)
    p.box("Kit_Structure", (fx - 0.035, -dw, 0.0), (fx + 0.03, dw, 0.012), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Seal", (fx - 0.002, -dw + 0.01, 0.012), (fx + 0.006, dw - 0.01, 0.0126), panel=False)
    p.box("Kit_Rubber", (fx - 0.006, -dw, 0.012), (fx + 0.004, -dw + 0.006, dh - 0.03), panel=False)     # the leaf's seal at the jamb
    # the occupancy screen beside the door, the extraction grille over it on the other side; the occupancy light in a
    # housing on the frame's head (round 3: "a housed light over the door tied to the screen's state")
    screen(p, fx, dw + 0.09, hw - 0.1, 1.36, 1.5, REGIONS["hygiene"])
    grille(p, fx, -hw + 0.08, -dw - 0.1, 1.55, 1.85)
    p.box("Kit_Structure", (fx + 0.035, -0.12, dh + 0.004), (fx + 0.06, 0.12, dh + 0.036), bevel=0.003, segments=1, panel=False)
    p.box("Kit_GlowCool", (fx + 0.06, -0.1, dh + 0.01), (fx + 0.0615, 0.1, dh + 0.03), panel=False)
    label(p, "st_vent", (fx, (-hw - dw) / 2, 1.47), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.35, True)
    p.grime("soot", (fx + 0.004, 0.0, 0.01), (1, 0, 0), (0, 0, -1), (0.76, 0.08), 0.7)
    p.collision_box((0.0, -hw, 0.0), (D + 0.03, hw, H))
    return p


# =============================================================================== the galley unit
def food(var, L, name, seed):
    p = kit_geo.Part(name, seed)
    D = 0.45
    hw = L / 2
    z0, z1 = 0.8, 1.8
    # the unit's back and a plate behind the seat, on brackets back to the liner (a plate over the whole height left
    # a big plain field under the unit - the liner shows there instead)
    sy0, sy1 = -0.34, 0.08
    # the unit's back 0.1 m off the wall plate's plane: its top then clears the liner's frames on the chamfer
    xb = 0.1
    assert z1 <= top_at(xb)
    front_plate(p, "Kit_Primary", xb + 0.02, -hw, hw, z0, z1, pressed=True)
    # the seat's back plate in the lighter secondary graphite (round 3: "the seat in a black niche, no back wall")
    front_plate(p, "Kit_Primary", 0.02, sy0 - 0.06, sy1 + 0.06, 0.15, z0, pressed=True, secondary=True)
    for (yy, zz) in ((-hw + 0.2, 1.6), (hw - 0.2, 1.6), (-hw + 0.2, 0.9), (hw - 0.2, 0.9)):
        p.box("Kit_Structure", (-WALL_GAP - 0.012, yy - 0.03, zz - 0.04), (xb, yy + 0.03, zz + 0.04), bevel=0.003, segments=1, panel=False)
    p.box("Kit_Structure", (-WALL_GAP - 0.012, (sy0 + sy1) / 2 - 0.03, 0.26), (0.0, (sy0 + sy1) / 2 + 0.03, 0.34), bevel=0.003, segments=1, panel=False)
    # the carcass: sides in the structure metal, bottom and top
    xc = xb + 0.02
    for s in (1, -1):
        p.box("Kit_Structure", (xc, min(s * hw, s * (hw - 0.03)), z0), (D, max(s * hw, s * (hw - 0.03)), z1), bevel=0.004, segments=1, panel=False)
    iw = hw - 0.03
    p.box("Kit_Primary", (xc, -iw, z0), (D, iw, z0 + 0.03), bevel=0.003, segments=1)
    p.box("Kit_Primary", (xc, -iw, z1 - 0.03), (D, iw, z1), bevel=0.003, segments=1)
    # low: the chilled cabinet (left, hinged, the cooler's air slots low in it) and the ration drawer (right), a mullion
    # between them; recessed fields, the pulls recessed in orange along their top borders, rubber bumpers (round 2:
    # "generic bar pulls, boxes in one plane"; round 3: "flat slabs, no hinges or vents")
    zl0, zl1 = z0 + 0.03, 1.2
    p.box("Kit_Seal", (xc, -iw, zl0), (D - 0.02, iw, zl1), panel=False)
    for (a0, a1) in ((-iw + 0.004, -0.018), (0.018, iw - 0.004)):
        front_plate(p, "Kit_Primary", D, a0, a1, zl0 + 0.004, zl1 - 0.004, secondary=True, press=DEEP)
        recessed_pull(p, D, (a0 + a1) / 2, 0.075, zl1 - 0.024)
        for yy in (a0 + 0.02, a1 - 0.02):
            p.box("Kit_Rubber", (D, yy - 0.008, zl0 + 0.02), (D + 0.004, yy + 0.008, zl0 + 0.036), panel=False)
    slots(p, D - DEEP[1], -iw + 0.1, -0.12, zl0 + 0.06, zl0 + 0.13, 4)
    for zz in ((zl0 + 0.05, zl0 + 0.12), (zl1 - 0.12, zl1 - 0.05)):
        hinge(p, D, -iw + 0.006, *zz)
    p.box("Kit_Structure", (D - 0.02, -0.015, zl0), (D + 0.012, 0.015, zl1), bevel=0.003, segments=1, panel=False)
    p.box("Kit_GlowCool", (D, -iw + 0.05, zl1 - 0.034), (D + 0.003, -iw + 0.09, zl1 - 0.024), panel=False)       # cooling
    # the counter: a 4 cm slab 10 cm proud of the doors with a rubber bullnose (round 3: "a thin strip in the cabinet's
    # plane, no overhang or edge")
    p.box("Kit_Structure", (xc, -iw, zl1), (D + 0.1, iw, zl1 + 0.04), bevel=0.004, segments=1, panel=False)
    p.tube("Kit_Rubber", (D + 0.1, -iw, zl1 + 0.02), (D + 0.1, iw, zl1 + 0.02), 0.021, 16)
    # the middle: the dispenser as its own housing on the counter, 5 cm proud of the doors (round 2: "a hole cut in a
    # flat board - the reference's unit stands out of its panel"): cream cheeks and cap, a thick orange frame, the
    # water bay, the screen and its buttons; the fascia in three screwed fields (round 3: "a flat beige plastic panel")
    zm0, zm1 = zl1 + 0.04, 1.55
    fm = D + 0.05
    for s in (1, -1):
        p.box("Kit_Accent", (D - 0.02, min(s * iw, s * (iw - 0.015)), zm0), (fm, max(s * iw, s * (iw - 0.015)), zm1), bevel=0.004, segments=1)
    p.box("Kit_Accent", (D - 0.02, -iw + 0.015, zm1 - 0.015), (fm, iw - 0.015, zm1), bevel=0.003, segments=1)
    bay = (0.12, 0.56, zm0 + 0.05, zm1 - 0.055)
    by0, by1, bz0, bz1 = bay
    ys = -0.18                           # the seam between the screen's field and the service field
    for (a0, a1, b0, b1) in ((-iw + 0.015, ys - 0.004, zm0, zm1 - 0.015), (ys + 0.004, by0, zm0, zm1 - 0.015),
                             (by1, iw - 0.015, zm0, zm1 - 0.015), (by0, by1, zm0, bz0), (by0, by1, bz1, zm1 - 0.015)):
        front_plate(p, "Kit_Accent", fm, a0, a1, b0, b1, t=0.02, panel=False)
    p.box("Kit_Seal", (fm - 0.03, ys - 0.006, zm0), (fm - 0.016, ys + 0.006, zm1 - 0.015), panel=False)
    ring(p, "Kit_Signal", fm, -iw + 0.035, iw - 0.035, zm0 + 0.03, zm1 - 0.035, 0.02, 0.01, bevel=0.003)
    for yy in (-iw + 0.05, ys - 0.025, ys + 0.025, by0 - 0.028, by1 + 0.028, iw - 0.05):
        for zz in (zm0 + 0.045, zm1 - 0.05):
            p.tube("Kit_Structure", (fm - 0.001, yy, zz), (fm + 0.005, yy, zz), 0.005, 6)
    label(p, "st_service", (fm, (ys + by0) / 2, zm0 + 0.19), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.5, True)
    # the bay: a dark recess behind the fascia
    bx0, bx1 = xc + 0.1, fm - 0.02
    p.box("Kit_Seal", (bx0 - 0.02, by0 - 0.01, bz0), (bx0, by1 + 0.01, bz1), panel=False)
    p.box("Kit_Seal", (bx0, by0 - 0.01, bz1 - 0.01), (bx1, by1 + 0.01, bz1), panel=False)
    p.box("Kit_Seal", (bx0, by0 - 0.01, bz0), (bx1, by1 + 0.01, bz0 + 0.01), panel=False)
    for (a0, a1) in ((by0 - 0.01, by0), (by1, by1 + 0.01)):
        p.box("Kit_Seal", (bx0, a0, bz0), (bx1, a1, bz1), panel=False)
    ring(p, "Kit_Structure", fm, by0, by1, bz0, bz1, 0.015, 0.012, bevel=0.002)
    c = ((by0 + by1) / 2)
    p.box("Kit_Structure", (bx0 + 0.02, c - 0.05, bz1 - 0.06), (bx0 + 0.13, c + 0.05, bz1 - 0.01), bevel=0.004, segments=1, panel=False)  # the head
    p.tube("Kit_Structure", (bx0 + 0.075, c, bz1 - 0.06), (bx0 + 0.075, c, bz1 - 0.12), 0.01, 12)                                        # the nozzle
    for k in range(8):
        yy = by0 + 0.02 + k * (by1 - by0 - 0.04) / 7
        p.box("Kit_Structure", (bx0 + 0.01, yy - 0.004, bz0 + 0.01), (bx1 - 0.01, yy + 0.004, bz0 + 0.02), panel=False)       # the drip grille
    # a dim warm strip at the bay's back under its roof (round 1: "a white burnt-out spot"): it lights the nozzle and
    # the grille, the strip itself out of sight
    p.box("Kit_GlowDim", (bx0 + 0.005, by0 + 0.03, bz1 - 0.016), (bx0 + 0.035, by1 - 0.03, bz1 - 0.01), panel=False)
    p.socket("Light_Bay_0", (bx0 + 0.06, c, bz1 - 0.04), x=(0, 0, -1), z=(1, 0, 0), type="point", role="warm", cd=0.6,
             radius_m=0.6, source_radius_cm=3.0)
    screen(p, fm, -0.42, -0.25, zm0 + 0.1, zm0 + 0.27, REGIONS["galley"])
    # three buttons under the screen's soft-key labels (WATER, CHILL, RATION - kit_screens), each with a cool backlit
    # dot (round 1: "controls without labels or light")
    for k, yy in enumerate((-0.39, -0.335, -0.28)):
        p.box("Kit_Plastic", (fm, yy - 0.025, zm0 + 0.045), (fm + 0.014, yy + 0.025, zm0 + 0.08), bevel=0.003, segments=1, panel=False)
        p.box("Kit_GlowCool", (fm + 0.014, yy - 0.012, zm0 + 0.06), (fm + 0.0152, yy + 0.012, zm0 + 0.065), panel=False)
    # the fingers' wear round the buttons, the drips under the bay (the style: dirt only where it builds up)
    # (at points on the fascia itself: a card lands on the first surface its ray meets - a button's face stands 14 mm out)
    p.grime("smear", (fm, -0.335, zm0 + 0.038), (1, 0, 0), (0, 0, 1), (0.22, 0.06), 1.0)
    p.grime("streaks", (fm, c, bz0 - 0.017), (1, 0, 0), (0, 0, 1), (by1 - by0 - 0.04, 0.045), 1.0)
    # high: two stowage doors in recessed fields, finger slots and push latches on their bottom borders, hinges at their
    # outer edges, a mullion between them
    zh0, zh1 = zm1, z1 - 0.03
    p.box("Kit_Seal", (xc, -iw, zh0), (D - 0.02, iw, zh1), panel=False)
    for s, (a0, a1) in ((-1, (-iw + 0.004, -0.018)), (1, (0.018, iw - 0.004))):
        front_plate(p, "Kit_Primary", D, a0, a1, zh0 + 0.004, zh1 - 0.004, secondary=True, press=DEEP)
        p.box("Kit_Seal", (D - 0.004, (a0 + a1) / 2 - 0.08, zh0 + 0.012), (D + 0.001, (a0 + a1) / 2 + 0.08, zh0 + 0.026), panel=False)
        p.box("Kit_Structure", (D, (a0 + a1) / 2 + 0.1, zh0 + 0.012), (D + 0.006, (a0 + a1) / 2 + 0.13, zh0 + 0.028), bevel=0.002, segments=1, panel=False)
        hy = a0 + 0.002 if s < 0 else a1 - 0.002
        for zz in ((zh0 + 0.03, zh0 + 0.07), (zh1 - 0.07, zh1 - 0.03)):
            hinge(p, D, hy, *zz)
    p.box("Kit_Structure", (D - 0.02, -0.015, zh0), (D + 0.012, 0.015, zh1), bevel=0.003, segments=1, panel=False)
    # a dim warm strip under the unit, over the seat (round 2: "the seat hangs in a dark pocket")
    p.box("Kit_Structure", (D - 0.07, -iw + 0.04, z0 - 0.006), (D - 0.01, iw - 0.04, z0), panel=False)
    p.box("Kit_GlowDim", (D - 0.06, -iw + 0.05, z0 - 0.011), (D - 0.02, iw - 0.05, z0 - 0.006), panel=False, bezel_face=-1)
    # (round 3: "a cream cushion beside the olive berth" - the same upholstery, burnt pale by 1.2 cd 20 cm over it)
    # in front of the seat: the back cushion and plate lit, the seat's top only at a slant
    p.socket("Light_Seat_0", (0.38, (sy0 + sy1) / 2, 0.7), x=(0, 0, -1), z=(1, 0, 0), type="point", role="warm", cd=0.2,
             radius_m=1.1, source_radius_cm=10.0)
    # the fold-down seat under it: a hinge rail on the wall plate, the pan and its cushion, a rubber front edge, the
    # hinge's knuckles, two gusset brackets under it, an orange release tab at its side (round 2: "no visible hinge or
    # bracket - floats"; round 3: "no readable fold mechanism")
    p.box("Kit_Structure", (0.02, sy0 - 0.02, 0.4), (0.06, sy1 + 0.02, 0.45), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Structure", (0.06, sy0, 0.43), (0.42, sy1, 0.455), bevel=0.004, segments=1, panel=False)
    p.box("Kit_Rubber", (0.41, sy0, 0.428), (0.425, sy1, 0.457), bevel=0.003, segments=1, panel=False)
    pad(p, frame((0, 0, 0.455), (1, 0, 0), (0, 1, 0), (0, 0, 1)), 0.07, 0.41, sy0 + 0.01, sy1 - 0.01, 0.055, 0.02, crown=0.016,
        seams_v=((sy0 + sy1) / 2,), step=0.05)
    for yy in (sy0 + 0.03, (sy0 + sy1) / 2, sy1 - 0.03):
        p.tube("Kit_Structure", (0.062, yy - 0.025, 0.428), (0.062, yy + 0.025, 0.428), 0.015, 12)
    for yy in (sy0 + 0.03, sy1 - 0.03):
        p.poly_prism("Kit_Structure", [(0.02, 0.43), (0.38, 0.43), (0.02, 0.2)],
                     frame((0, yy - 0.006, 0), (1, 0, 0), (0, 0, 1), (0, -1, 0)), 0.012, bevel=0.003, segments=1)
    p.box("Kit_Signal", (0.3, sy1, 0.432), (0.35, sy1 + 0.012, 0.448), bevel=0.002, segments=1, panel=False)
    pad(p, frame((0.013, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0)), sy0 + 0.02, sy1 - 0.02, 0.56, 0.76, 0.062, 0.02, crown=0.01,
        seams_u=((sy0 + sy1) / 2,), step=0.05)
    p.collision_box((0.0, -hw, z0), (D + 0.12, hw, z1))
    p.collision_box((0.02, sy0, 0.4), (0.42, sy1, 0.51))
    return p


# =============================================================================== the batch
REGIONS = {"hygiene": (0.125, 0.25, 0.375, 0.5), "galley": (0.75, 0.0, 1.0, 0.25)}     # kit_screens.py pages
FURNITURE = [("Furniture", "Bunk", 2.1, "L", "A"), ("Furniture", "Locker", 0.95, "L", "A"),
             ("Furniture", "Hygiene", 1.45, "L", "A"), ("Furniture", "Food", 1.6, "L", "A")]
VIEWS = {(c, pa): ((1.0, 0.05, 0.15), (1.0, -0.85, 0.45)) for c, pa, _, _, _ in FURNITURE}
BUILDERS = {"Bunk": bunk, "Locker": locker, "Hygiene": hygiene, "Food": food}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(size * 10 + 0.5), sec, var)


def build_part(cat, part, size, sec_key, var, seed):
    return BUILDERS[part](var, size, part_name(cat, part, size, sec_key, var), seed)


def budget(cat, part, size):
    return int(kit_geo.RULES["tri_budget"]["Furniture"])
