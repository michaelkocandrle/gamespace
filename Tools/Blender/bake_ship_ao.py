"""Bakes ambient occlusion for a ship that Tools/Blender/build_ai_ship.py has already built.

    blender -b ArtSource/Ships/<Ship>/<Ship>_Meshy.blend --python Tools/Blender/bake_ship_ao.py -- <Ship>

Writes ArtSource/Ships/<Ship>/Textures/T_Ship_<Ship>_AO.png onto the atlas the other maps already
use, so it drops straight into the material next to the base colour, ORM and normal.

Why it is a separate script: the re-baked ORM has no occlusion in it - its red channel is the emissive
mask for the screens (build_ai_ship.py, surface_nodes) - and the hull material needs occlusion to stop
reading as one flat colour (M_Ship_PBR, CavityStrength and WearAmount). Baking only this map takes a
couple of minutes, where the whole recipe takes far longer and would rewrite the meshes.

Unlike the other maps this one is baked from the built meshes themselves, not from the Meshy original:
the built hull is a million triangles, which carries every recess and greeble the occlusion needs, and
the original is not in the .blend any more.
"""

import os
import sys
import time

import bpy

# From this script, not from the .blend: the .blend lives three folders deeper, inside ArtSource.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIZE = 4096
SAMPLES = 16
MARGIN_PX = 16
# How far a ray looks for something to be occluded by, in metres. Cycles' own AO bake has no limit, so
# on a closed 14 m hull almost every point sees another part of the ship and the map came out at 0.27
# mean - a filthy ship, not panel gaps (20. 9. 2026). Half a metre keeps it to recesses and greebles.
DISTANCE_M = 0.5


def log(msg):
    print("bake_ship_ao: %s" % msg, flush=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ship = argv[0] if argv else os.path.basename(bpy.data.filepath).split("_")[0]
    target_path = os.path.join(REPO, "ArtSource", "Ships", ship, "Textures", "T_Ship_%s_AO.png" % ship)

    # The parts that share the ship's atlas, in the order build_ai_ship.py unwraps them. The interior
    # has its own atlas and its own run.
    names = ["SM_Ship_%s" % ship, "SM_Ship_%s_Gear" % ship, "SM_Ship_%s_Lining" % ship]
    objects = [bpy.data.objects[name] for name in names if name in bpy.data.objects]
    if not objects:
        raise SystemExit("bake_ship_ao: none of %s is in %s" % (names, bpy.data.filepath))

    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES

    # Only the ship occludes itself: collision hulls and the sockets are not part of the model.
    for ob in bpy.data.objects:
        ob.hide_render = ob not in objects

    image = bpy.data.images.new("T_Ship_%s_AO" % ship, SIZE, SIZE, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    image.generated_color = (1.0, 1.0, 1.0, 1.0)

    # An occlusion shader through an emission, not Cycles' AO bake type: only this way is the ray
    # distance ours to set. The image node is active but unconnected - that is where the bake lands.
    target = bpy.data.materials.new("AOBakeTarget")
    target.use_nodes = True
    nodes = target.node_tree.nodes
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = SAMPLES
    ao.only_local = True
    ao.inputs["Distance"].default_value = DISTANCE_M
    emission = nodes.new("ShaderNodeEmission")
    target.node_tree.links.new(ao.outputs["AO"], emission.inputs["Color"])
    output = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    target.node_tree.links.new(emission.outputs[0], output.inputs["Surface"])
    node = nodes.new("ShaderNodeTexImage")
    node.image = image
    nodes.active = node

    kept = {ob.name: list(ob.data.materials) for ob in objects}
    for ob in objects:
        ob.data.materials.clear()
        ob.data.materials.append(target)

    start = time.time()
    for index, ob in enumerate(objects):
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        # use_clear only on the first part: the three share one atlas.
        bpy.ops.object.bake(type="EMIT", use_clear=(index == 0), margin=MARGIN_PX, use_selected_to_active=False)
        log("%s baked (%.0f s so far)" % (ob.name, time.time() - start))

    for ob in objects:
        ob.data.materials.clear()
        for material in kept[ob.name]:
            ob.data.materials.append(material)

    image.filepath_raw = target_path
    image.file_format = "PNG"
    image.save()
    log("%d samples, %.2f m, %dx%d, %.0f s -> %s" % (SAMPLES, DISTANCE_M, SIZE, SIZE, time.time() - start, target_path))


main()
