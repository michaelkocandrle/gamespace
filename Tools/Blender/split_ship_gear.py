"""Moves a ship's modelled landing gear out of the hull mesh into its own part, SM_Ship_<Ship>_Gear.

A ship modelled with its gear down has it joined into SM_Ship_<Ship>: three legs (struts,
pistons, feet and rubber pads) hanging under the belly, their soles exactly on the SOCKET_Gear_*
empties. A separate part is exported as its own FBX and becomes its own mesh component in Unreal,
which ASpaceshipPawn raises into the hull when the gear goes up (SC-2a).

    blender -b ArtSource\\Ships\\<Ship>\\<Ship>.blend --python Tools\\Blender\\split_ship_gear.py -- [--dry-run]

What counts as gear: every loose part of the hull mesh that reaches below the belly (lower than
BELOW_M) inside a box around one of the gear sockets (GEAR_BOX_M half extent in X and Y), except
the bay doors and the landing light (HullPaint and Glass materials), which stay on the hull. Run
once; a second run finds nothing left to move. Saves the .blend (keep it in git: it is the source).
Afterwards export as usual (gamespace_ship_export.py) and import (Tools/Assets/import_ship.py).
"""

import sys

import bmesh
import bpy
from mathutils import Vector

BELOW_M = -1.25
GEAR_BOX_M = (0.75, 0.6)
KEEP_MATERIALS = ("HullPaint", "Glass")


def main(argv):
    dry_run = "--dry-run" in argv
    hull = next((o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("SM_Ship_")
                 and o.name.count("_") == 2), None)
    if hull is None:
        raise SystemExit("split_ship_gear: no SM_Ship_<Ship> hull mesh in this file")
    ship = hull.name.split("_")[2]
    target = "SM_Ship_%s_Gear" % ship
    if bpy.data.objects.get(target):
        print("split_ship_gear: %s already exists, nothing to do" % target)
        return 0
    sockets = [o.matrix_world.translation.copy() for o in bpy.data.objects
               if o.type == "EMPTY" and o.parent == hull and o.name.startswith("SOCKET_Gear")]
    if not sockets:
        raise SystemExit("split_ship_gear: %s has no SOCKET_Gear_* empties" % hull.name)

    bm = bmesh.new()
    bm.from_mesh(hull.data)
    bm.verts.ensure_lookup_table()
    world = hull.matrix_world
    materials = [m.name if m else "" for m in hull.data.materials]

    seen = set()
    picked = []
    for start in bm.verts:
        if start.index in seen:
            continue
        island, stack = [], [start]
        seen.add(start.index)
        while stack:
            v = stack.pop()
            island.append(v)
            for e in v.link_edges:
                o = e.other_vert(v)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        points = [world @ v.co for v in island]
        low = min(p.z for p in points)
        centre = sum(points, Vector()) / len(points)
        near = any(abs(centre.x - s.x) <= GEAR_BOX_M[0] and abs(centre.y - s.y) <= GEAR_BOX_M[1] for s in sockets)
        mats = {materials[f.material_index] for v in island for f in v.link_faces}
        keep = any(k in m for m in mats for k in KEEP_MATERIALS)
        if low < BELOW_M and near and not keep:
            picked.append(island)

    count = sum(len(i) for i in picked)
    print("split_ship_gear: %d loose parts, %d vertices of %s are gear" % (len(picked), count, hull.name))
    if dry_run or not picked:
        return 0

    for v in bm.verts:
        v.select_set(False)
    for island in picked:
        for v in island:
            v.select_set(True)
    bm.select_flush(True)
    bm.to_mesh(hull.data)
    bm.free()

    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = hull
    hull.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    gear = next(o for o in bpy.context.selected_objects if o != hull)
    gear.name = target
    gear.data.name = target
    # Only the slots the legs use (HullDark, BareMetal, Rubber).
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = gear
    gear.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
    print("split_ship_gear: %s (%d vertices, materials %s), %s keeps %d vertices" % (
        gear.name, len(gear.data.vertices), [m.name for m in gear.data.materials], hull.name, len(hull.data.vertices)))
    bpy.ops.wm.save_mainfile()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []))
