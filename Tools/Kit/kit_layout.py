"""Where the kit parts of a ship's kit rooms go - plain Python, shared by Unreal (Tools/Assets/kit_rooms.py) and
Blender (Tools/Blender/check_ship_geometry.py puts the same parts into the ship for its hole, float and hull checks).

The recipe block interior.kit_modules (ArtSource/Ships/<Ship>/HardSurface/<Ship>_hs.json) is in layout (design)
metres: x forward, y to port, z from the deck. Wall runs (start, end, face normal, modules) and run parts (start,
direction, parts one after another) as import_kit.SHOWROOM, whose placement this repeats in Unreal's axes (y
mirrored): a wall module's pivot is its start on the face plane, it faces +X and runs along its local -Y; a run part
runs along +X from its pivot.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(ROOT, "ArtSource", "Kit", "Export", "kit_manifest.json")


def manifest_parts():
    return json.load(open(MANIFEST, encoding="utf-8"))["parts"]


def layout_parts(mods, parts):
    """[(part short name, (x, y_unreal, z) in layout metres, yaw in Unreal degrees)] for a kit_modules block.
    parts: kit_manifest.json "parts" (lengths)."""
    out = []
    for i, (a, b, n, mods_) in enumerate(mods.get("wall_runs", [])):
        a, b, n = (a[0], -a[1]), (b[0], -b[1]), (n[0], -n[1])
        yaw = math.degrees(math.atan2(n[1], n[0]))
        nat = (math.sin(math.radians(yaw)), -math.cos(math.radians(yaw)))
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        d = ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        same = nat[0] * d[0] + nat[1] * d[1] > 0
        total = sum(parts["SM_Kit_" + m]["length_m"] for m in mods_)
        if abs(total - ln) > 0.01:
            raise ValueError("wall run %d: modules %.2f m for a run of %.2f m" % (i, total, ln))
        cum = 0.0
        for m in mods_:
            lm = parts["SM_Kit_" + m]["length_m"]
            t = cum if same else cum + lm
            out.append((m, (a[0] + d[0] * t, a[1] + d[1] * t, 0.0), yaw))
            cum += lm
    for a, d, parts_ in mods.get("run_parts", []):
        z = a[2] if len(a) > 2 else 0.0
        a, d = (a[0], -a[1]), (d[0], -d[1])
        yaw = math.degrees(math.atan2(d[1], d[0]))
        cum = 0.0
        for m in parts_:
            out.append((m, (a[0] + d[0] * cum, a[1] + d[1] * cum, z), yaw))
            cum += parts["SM_Kit_" + m]["length_m"]
    return out


def rotate(yaw, x, y):
    """(x, y) turned by yaw degrees (Unreal: about +Z, X towards Y)."""
    ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    return x * ca - y * sa, x * sa + y * ca


def kit_blends():
    """The Kit_*.blend files (kit_build.py saves each job's parts at the origin, one collection per part; the N stub
    walls of batch 1 sit in Kit_Batch2.blend, so look a part up by name, not by its batch)."""
    folder = os.path.join(ROOT, "ArtSource", "Kit")
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.startswith("Kit_") and f.endswith(".blend")]
