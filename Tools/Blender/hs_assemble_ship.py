"""Hard-surface ship (hs_build_ship.py) -> a game-ready .blend for gamespace_ship_export.py.

    MSYS_NO_PATHCONV=1 blender -b ArtSource/Ships/<Ship>/HardSurface/<Ship>_HS.blend --python Tools/Blender/hs_assemble_ship.py -- ArtSource/Ships/<Ship>/HardSurface/<Ship>_hs.json

Driven by the recipe's "assemble" block:
  1. every part's modifiers are applied (bevel, weighted normals, the greeble instancer made real);
  2. parts are joined into the export meshes: "groups" maps a part suffix ("" = the main mesh
     SM_Ship_<Ship>, "Canopy", "Gear", ...) to the objects that go in (the rest goes to the main mesh);
  3. everything moves by "offset" (layout coordinates -> ship coordinates centred on the origin);
  3a. vertex-colour masks for the layered material (Tools/Blender/hs_layers.py, recipe "layers");
  3b. mesh decals and trim strips (Tools/Blender/hs_decals.py, recipe "decals") as the "Decals" part;
  4. a UV map per mesh (smart project) for the engine (not for the decals: they carry atlas UVs);
  5. convex collision hulls (k-DOP, Tools/Blender/build_ai_ship.py) from "collision" boxes and sockets from
     "sockets" - both given in LAYOUT coordinates, like the drawing;
  6. saves "out_blend". Prints HSASSEMBLE {...}.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ai_ship as ai  # noqa: E402  (kdop_hull, build_collision, build_sockets, in_box)

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def shift_box(box, off):
    return {k: [v[0] + off["xyz".index(k)], v[1] + off["xyz".index(k)]] for k, v in box.items()}


def main(argv):
    recipe = json.load(open(path(argv[0]), encoding="utf-8"))
    layout = json.load(open(path(recipe["layout"]), encoding="utf-8"))
    ship = layout["ship"]
    cfg = recipe["assemble"]
    off = cfg["offset"]
    for o in list(bpy.data.objects):
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    kit = bpy.data.collections.get("HS_Kit")
    kit_objs = set(kit.all_objects) if kit else set()
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o not in kit_objs]
    # 1) apply modifiers (the greeble point cloud becomes real kit geometry). new_from_object drops
    #    instances, so the instancer realises them first (otherwise no greeble reached the game).
    ng = bpy.data.node_groups.get("HS_KitInstancer")
    if ng and not any(n.type == "REALIZE_INSTANCES" for n in ng.nodes):
        inst = next(n for n in ng.nodes if n.type == "INSTANCE_ON_POINTS")
        gout = next(n for n in ng.nodes if n.type == "GROUP_OUTPUT")
        real = ng.nodes.new("GeometryNodeRealizeInstances")
        ng.links.new(inst.outputs["Instances"], real.inputs[0])
        ng.links.new(real.outputs[0], gout.inputs[0])
    dg = bpy.context.evaluated_depsgraph_get()
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        o.modifiers.clear()
        old = o.data
        o.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
    for o in kit_objs:
        bpy.data.objects.remove(o)
    # panel identity for the layered material (hs_layers.panel_ids): a hash of the source object per face
    import zlib
    for o in meshes:
        a = o.data.attributes.get("part_obj") or o.data.attributes.new("part_obj", "INT", "FACE")
        h = zlib.crc32(o.name.split(".")[0].encode()) & 0x7FFFFFFF
        a.data.foreach_set("value", [h] * len(o.data.polygons))
        if o.name == "SM_Ship_%s_Hull" % ship:
            recipe["_hull_obj_hash"] = h
    # every mesh needs a real material in every slot: kit greebles take "greeble_material", anything else
    # without one takes "default_material" (both slot names from the recipe's materials)
    def mat(key):
        spec = recipe["materials"][key]
        return bpy.data.materials.get("M_Ship_%s_%s" % (ship, spec["slot"]))
    for o in meshes:
        want = mat(cfg.get("greeble_material", "dark")) if "Greebles" in o.name else mat(cfg.get("default_material", "paint"))
        if not o.data.materials:
            o.data.materials.append(want)
        for i, m in enumerate(o.data.materials):
            if m is None:
                o.data.materials[i] = want
    # 2) groups
    assign = {}
    for suffix, names in cfg.get("groups", {}).items():
        for n in names:
            assign[n] = suffix
    # the interior (hs_interior.py): its own part; the screens a part of their own too, so the unwrap
    # does not touch their canvas UVs
    for o in meshes:
        if "_Int_" in o.name:
            assign[o.name] = "Screens" if o.name.endswith("_Int_Screens") else "Interior"
        elif o.name.endswith("_IntDecals"):
            # interior mesh decals (hs_interior_decals.py): atlas UVs, their own part like the exterior's Decals
            assign[o.name] = "InteriorDecals"
        elif "_IntKit_" in o.name:
            # modular kit pieces (hs_interior_kit.py): their trim-sheet UVs are the look, no unwrap
            assign[o.name] = "InteriorKit"
    groups = {}
    for o in meshes:
        if not o.data.polygons:
            bpy.data.objects.remove(o)
            continue
        groups.setdefault(assign.get(o.name, ""), []).append(o)
    out = {}
    for suffix, obs in groups.items():
        name = "SM_Ship_%s" % ship + ("_%s" % suffix if suffix else "")
        bpy.ops.object.select_all(action="DESELECT")
        for o in obs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        if len(obs) > 1:
            bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active
        ob.name = ob.data.name = name
        # merge duplicate slots of the same material and drop unused ones
        bpy.ops.object.material_slot_remove_unused()
        # 3) layout -> ship coordinates
        ob.data.transform(Matrix.Translation(Vector(off)) @ ob.matrix_world)
        ob.matrix_world = Matrix()
        out[suffix] = ob
    # 3c) real lights from hs_lights.py (scene property, layout coordinates) -> Export/<Ship>_lights.json in
    #     Unreal mesh space (cm, y mirrored) for import_ship.py
    lights = json.loads(bpy.context.scene.get("hs_lights", "[]"))
    if lights:
        for l in lights:
            p = [l["location"][i] + off[i] for i in range(3)]
            l["location_ue_cm"] = [round(p[0] * 100, 1), round(-p[1] * 100, 1), round(p[2] * 100, 1)]
            l["direction_ue"] = [l["direction"][0], -l["direction"][1], l["direction"][2]]
        lights_path = os.path.join(os.path.dirname(path(cfg["out_blend"])), "Export", "%s_lights.json" % ship)
        os.makedirs(os.path.dirname(lights_path), exist_ok=True)
        with open(lights_path, "w", encoding="utf-8") as fh:
            json.dump({"_comment": "Written by Tools/Blender/hs_assemble_ship.py from the recipe's lights (hs_lights.py); read by Tools/Assets/import_ship.py.",
                       "lights": lights}, fh, indent=1)
    # 3a) vertex-colour masks for the layered material (Tools/Blender/hs_layers.py): AO, edges,
    #     secondary paint, layer amount
    layer_report = {}
    if recipe.get("layers"):
        import hs_layers
        layer_report = hs_layers.bake(out[""], recipe["layers"], off)
    # 3b) mesh decals and trim strips laid onto the finished hull (Tools/Blender/hs_decals.py): their own
    #     part with atlas UVs, no unwrap, no collision, not Nanite (setup no_nanite_parts)
    import hs_decals
    decals, decal_report = hs_decals.build(recipe, out[""], ship, off, ROOT)
    if decals is not None:
        out["Decals"] = decals
    # 4) UVs
    for key, ob in out.items():
        if key in ("Decals", "Screens", "InteriorKit", "InteriorDecals"):
            continue
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.select_all(action="SELECT")
        bpy.ops.uv.pack_islands(rotate=True, margin_method="ADD", margin=0.001)
        bpy.ops.object.mode_set(mode="OBJECT")
    # 4b) panel ids in UV channel 1 (after the unwrap, which works on the first UV map)
    if recipe.get("layers"):
        import hs_layers
        hs_layers.panel_ids(out[""], recipe, off)
    # 5) collision and sockets, from layout coordinates
    hull = out[""]
    parts = {k: v for k, v in out.items() if k}
    regions = [{"name": c["name"], "box": shift_box(c["box"], off)} for c in cfg["collision"]]
    ai.build_collision(ship, [o for k, o in out.items() if k not in ("Canopy", "Decals", "Interior", "Screens", "InteriorKit", "InteriorDecals")], regions)
    sockets = {}
    for name, loc in json.loads(bpy.context.scene.get("hs_display_sockets", "{}")).items():
        cfg["sockets"]["Display_" + name] = {"location": loc}
    for name, s in cfg["sockets"].items():
        s = dict(s)
        if "location" in s:
            s["location"] = [s["location"][i] + off[i] for i in range(3)]
        if "box" in s:
            s["box"] = shift_box(s["box"], off)
        sockets[name] = s
    ai.build_sockets(ship, hull, parts, sockets)
    pts = [o.matrix_world @ v.co for o in out.values() for v in o.data.vertices]
    lo = [round(min(p[i] for p in pts), 3) for i in range(3)]
    hi = [round(max(p[i] for p in pts), 3) for i in range(3)]
    bpy.ops.wm.save_as_mainfile(filepath=path(cfg["out_blend"]))
    print("HSASSEMBLE " + json.dumps({"out": cfg["out_blend"], "meshes": {o.name: len(o.data.polygons) for o in out.values()},
                                       "decals": decal_report, "layers": layer_report,
                                       "bounds": [lo, hi]}))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:])
