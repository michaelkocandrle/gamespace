"""Parts factory, pilot 1 step 3 (FACTORY_WORKFLOW v0.1, 6. 10. 2026): the material sample board of the kit's shared
base (ArtSource/Kit/kit_materials.json) - one sample per role and a piece of the KF-PORTAL-01 profile with its lip and
cuff, for the showroom (Tools/Assets/import_kit.py SHOWROOM["board"]) next to the SC etalon's anchor shots.

    blender -b --factory-startup --python Tools/Kit/kit_build.py -- factory --no-render

The simplest working version. Frames: origin on the floor at the sample's back, +X out of the board (towards the
viewer once placed with yaw 180), +Y across, +Z up; the floor sample's origin is its centre on the floor, +X along
the walk. Heights are real (the pillars stand 1.8 m), so the maker's hand band (0.9-1.6 m) shows where the edges wear.
"""
import json
import os

from mathutils import Matrix, Vector

import kit_geo

ROOT = kit_geo.ROOT
PROFILE = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Design", "KF-PORTAL-01.json"), encoding="utf-8"))
MATS = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_materials.json"), encoding="utf-8"))

H = 1.8                        # pillar height: the hand band 0.9-1.6 m lies inside
BEV = {r: v["bevel_mm"] / 1000.0 for r, v in MATS["roles"].items() if not r.startswith("_")}

# (category, part, size, section, variant): section "F" = factory sample
FACTORY = [("Sample", "Lacquer", 1.8, "F", "A"), ("Sample", "Lip", 1.8, "F", "A"), ("Sample", "Dark", 1.8, "F", "A"),
           ("Sample", "Profile", 1.8, "F", "A"), ("Sample", "Floor", 0.9, "F", "A")]
VIEWS = {("Sample", p): ((1, 0.0, 0.0), (1, -0.6, 0.2)) for _, p, _, _, _ in FACTORY}


def part_name(cat, part, size, sec, var):
    return "SM_Kit_%s_%s%02d%s_%s" % (cat, part, int(round(size * 10)), sec, var)


def budget(cat, part, size):
    return 30000


def _back(p, w=0.3):
    # the dark board the sample hangs on, so its edges read against something
    p.box("Kit_Dark", (0.0, -w / 2 - 0.02, 0.0), (0.02, w / 2 + 0.02, H), bevel=BEV["Kit_Dark"], segments=1, panel=False)


def _bolts(p, role, x, ys, zs, r=0.005):
    for y in ys:
        for z in zs:
            p.tube(role, (x, y, z), (x + 0.004, y, z), r, 10)


def sample_lacquer(name, seed):
    """Three pressed lacquer panels stacked with 8 mm dark seams (the seam dirt), 4 mm worn bevels, bolts."""
    p = kit_geo.Part(name, seed)
    _back(p)
    for z0, z1 in ((0.0, 0.596), (0.604, 1.196), (1.204, H)):
        p.box("Kit_Lacquer", (0.02, -0.15, z0), (0.08, 0.15, z1), bevel=BEV["Kit_Lacquer"], segments=1,
              inset=(0.03, 0.006), m=None)
        _bolts(p, "Kit_Lip", 0.08, (-0.125, 0.125), (z0 + 0.025, z1 - 0.025))
    p.box("Kit_Dark", (0.02, -0.15, 0.0), (0.075, 0.15, H), panel=False)       # the seams' dark backing
    p.collision_box((0.0, -0.17, 0.0), (0.08, 0.17, H))
    return p


def sample_lip(name, seed):
    """Polished metal: two 18 mm lips on the edges of a dark plate and a polished plate 0.2 x 0.5 at eye height."""
    p = kit_geo.Part(name, seed)
    _back(p)
    p.box("Kit_Dark", (0.02, -0.15, 0.0), (0.07, 0.15, H), bevel=BEV["Kit_Dark"], segments=1)
    lip = PROFILE["profile"]["lip"]["width"] / 1000.0
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.15, s * (0.15 - lip)))
        p.box("Kit_Lip", (0.07, y0, 0.0), (0.082, y1, H), bevel=0.004, segments=2)
    p.box("Kit_Lip", (0.07, -0.1, 1.25), (0.08, 0.1, 1.75), bevel=BEV["Kit_Lip"], segments=2)
    p.collision_box((0.0, -0.17, 0.0), (0.082, 0.17, H))
    return p


def sample_dark(name, seed):
    """The dark third: graphite plate, a ribbed rubber cuff (ribs 7 mm on a 15 mm pitch), a rubber kick strip."""
    p = kit_geo.Part(name, seed)
    _back(p)
    p.box("Kit_Dark", (0.02, -0.15, 0.1), (0.07, 0.15, H), bevel=BEV["Kit_Dark"], segments=1, inset=(0.025, 0.004))
    cf = PROFILE["profile"]["cuff"]
    w = (cf["u1"] - cf["u0"]) / 1000.0
    p.box("Kit_Dark", (0.07, -w / 2, 0.1), (0.074, w / 2, H), panel=False)
    y = -w / 2 + 0.004
    while y + cf["rib_width"] / 1000.0 <= w / 2:
        p.box("Kit_Dark", (0.074, y, 0.1), (0.078, y + cf["rib_width"] / 1000.0, H), bevel=0.001, segments=1, panel=False)
        y += cf["rib_pitch"] / 1000.0
    p.box("Kit_Dark", (0.02, -0.15, 0.0), (0.08, 0.15, 0.1), bevel=0.003, segments=1)      # the kick strip (rev. B)
    for z in (0.025, 0.05, 0.075):
        p.box("Kit_Dark", (0.08, -0.148, z - 0.003), (0.083, 0.148, z + 0.003), panel=False)
    p.collision_box((0.0, -0.17, 0.0), (0.083, 0.17, H))
    return p


def sample_profile(name, seed):
    """A 1.8 m piece of the KF-PORTAL-01 pillar: the three lacquer steps (base, step 2, crown) with 4 mm worn
    bevels, the polished lips over the crown's edges, the ribbed rubber cuff in the crown's middle (profile in mm:
    u across -> y, v out of the wall -> x)."""
    p = kit_geo.Part(name, seed)
    pr = PROFILE["profile"]
    mm = 0.001
    _back(p, 0.3)
    bv = BEV["Kit_Lacquer"]
    for st in pr["steps"][:2]:
        p.box("Kit_Lacquer", (0.02 + st["v0"] * mm, (st["u0"] - 150) * mm, 0.0), (0.02 + st["v1"] * mm, (st["u1"] - 150) * mm, H),
              bevel=bv, segments=1)
    crown = pr["steps"][2]
    lip = pr["lip"]["width"]
    p.box("Kit_Lacquer", (0.02 + crown["v0"] * mm, (crown["u0"] + lip - 150) * mm, 0.0),
          (0.02 + crown["v1"] * mm, (crown["u1"] - lip - 150) * mm, H), bevel=bv, segments=1)
    for a, b in ((crown["u0"], crown["u0"] + lip), (crown["u1"] - lip, crown["u1"])):
        p.box("Kit_Lip", (0.02 + crown["v0"] * mm, (a - 150) * mm, 0.0), (0.02 + crown["v1"] * mm, (b - 150) * mm, H),
              bevel=crown.get("chamfer", 12) * mm * 0.6, segments=3)
    cf = pr["cuff"]
    top = 0.02 + crown["v1"] * mm
    p.box("Kit_Dark", (top - cf["depth"] * mm, (cf["u0"] - 150) * mm, 0.0), (top + 0.0005, (cf["u1"] - 150) * mm, H), panel=False)
    u = cf["u0"] + 4
    while u + cf["rib_width"] <= cf["u1"]:
        p.box("Kit_Dark", (top - cf["depth"] * mm, (u - 150) * mm, 0.0), (top + 0.002, (u + cf["rib_width"] - 150) * mm, H),
              bevel=0.001, segments=1, panel=False)
        u += cf["rib_pitch"]
    _bolts(p, "Kit_Lip", 0.02 + pr["steps"][0]["v1"] * mm, (-0.13, 0.13), [0.1 + k * 0.08 for k in range(int((H - 0.2) / 0.08) + 1)],
           r=0.005)
    p.collision_box((0.0, -0.17, 0.0), (0.13, 0.17, H))
    return p


def _octagon(cx, cy, w, h, c):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def sample_floor(name, seed):
    """The KF-PORTAL-01 walkway plate (rev. B): octagonal, 0.9 x 1.2, corners chamfered 120 mm, a polished lip 18 mm
    round it, the field sunk 6 mm with the anti-slip lanes (80 mm on a 110 mm pitch), bolts; under it a dark sheet."""
    p = kit_geo.Part(name, seed)
    fl = PROFILE["floor"]
    L, W, c, lip, rec = fl["plate_lengths"][0], fl["walk_width"], fl["corner_chamfer"], fl["lip"], fl["insert_recess"]
    p.box("Kit_Dark", (-L / 2 - 0.05, -W / 2 - 0.05, -0.03), (L / 2 + 0.05, W / 2 + 0.05, -0.02), panel=False)
    outer = _octagon(0, 0, L, W, c)
    inner = _octagon(0, 0, L - 2 * lip, W - 2 * lip, c - lip * 0.41)
    ident = Matrix.Identity(4)
    for i in range(8):
        j = (i + 1) % 8
        p.poly_prism("Kit_Lip", [outer[i], outer[j], inner[j], inner[i]], ident, 0.02, bevel=0.0015, segments=1)
    p.poly_prism("Kit_Dark", inner, Matrix.Translation((0, 0, -rec)), 0.014, bevel=0.0, panel=True)
    ln = fl["lanes"]
    y = -W / 2 + lip + 0.04
    while y + ln["width"] <= W / 2 - lip - 0.04:
        p.box("Kit_AntiSlip", (-L / 2 + c, y, -rec), (L / 2 - c, y + ln["width"], -rec + 0.0015), panel=False)
        y += ln["pitch"]
    for x, yy in ((-L / 2 + 0.05, -W / 2 + c + 0.03), (L / 2 - 0.05, -W / 2 + c + 0.03), (-L / 2 + 0.05, W / 2 - c - 0.03),
                  (L / 2 - 0.05, W / 2 - c - 0.03)):
        p.tube("Kit_Lip", (x, yy, -rec), (x, yy, -rec + 0.0015), 0.006, 10)
    p.collision_box((-L / 2, -W / 2, -0.03), (L / 2, W / 2, 0.0))
    return p


BUILDERS = {"Lacquer": sample_lacquer, "Lip": sample_lip, "Dark": sample_dark, "Profile": sample_profile, "Floor": sample_floor}


def build_part(cat, part, size, sec_key, var, seed):
    return BUILDERS[part](part_name(cat, part, size, sec_key, var), seed)
