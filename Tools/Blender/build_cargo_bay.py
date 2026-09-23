"""Build the Steadfast cargo bay: the kit-bashed shell plus its ceiling and ceiling lights.

    MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \\
        --python Tools/Blender/build_cargo_bay.py

Vstupy (vše relativně ke kořeni repozitáře):
- `ArtSource/Ships/Steadfast/Interior/CargoBay_Shell.glb` - prostor tak, jak byl poskládaný z kitu
  23. 9. 2026 (podlaha, stěny, bedny, sloup s potrubím, dveře);
- `ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip` - kit (CC0, mimo git, návod k získání
  v README vedle něj). Skript si z něj vybalí jen ty díly, které potřebuje.

Výstup: `ArtSource/Ships/Steadfast/Interior/CargoBay.glb`, jeden mesh, a ten importuje
`Tools/Assets/import_interior.py`.

Proč strop: shell strop má - desku 8 x 6 m ve 2 m - jenže je to podlahový díl lícem nahoru.
Materiál v Unrealu je jednostranný, takže zevnitř deska neexistovala a nahoře byl vidět vesmír
(23. 9. 2026). Pod ni jde tmavá deska lícem dolů a do ní dvě řady svítidel.

Materiály dílů se přemapují na materiály shellu stejného jména (MI_Trim_01 -> MI_Trim_01), takže
se nepřidává žádná textura. Svítidla dostanou materiál `M_Lamp` - import ho pozná podle jména
a dá mu studenou bílou emisi místo oranžové (`MI_KitLamp`).
"""

import math
import os
import shutil
import sys
import tempfile
import zipfile

import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHELL = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior", "CargoBay_Shell.glb")
OUT = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior", "CargoBay.glb")
KIT_ZIP = os.path.join(ROOT, "ArtSource", "ThirdParty", "Quaternius", "ModularSciFiMegaKit.zip")
KIT_GLTF = "Modular SciFi MegaKit[Standard]/glTF/"

# Blender coordinates (Z up). Unreal sees the same X and Z, and Y mirrored.
BAY_X = (0.0, 8.0)             # the walls' footprint
BAY_Y = (-3.0, 3.0)
CEILING_Z = 2.0                # height of the shell's upward-facing plate
CEILING_PART = "Platforms/Platform_DarkPlates"   # 4 x 4 m, dark plates; x0.5 like all kit architecture
CEILING_SCALE = 0.5
LAMP_PART = "Props/Prop_Light_Wide"              # 1.32 m ceiling fixture, props stay 1:1
# Two rows of three, under the ceiling. import_interior.py puts the work lights under the same spots.
LAMP_ROWS_Y = (-1.5, 1.5)
LAMP_X = (1.4, 4.0, 6.6)
LAMP_MATERIAL = "M_Lamp"
# The shell's walls do not close the bay: the corners at the far end are open, and some panels face
# outwards, so from inside they do not exist either (raycast with face orientation, 23. 9. 2026).
# A liner of the same dark plates stands a hair outside the walls, facing in: hidden where a wall
# is, and it closes the holes where there is none. A doorway for the corridor gets cut into it later.
LINER_OFFSET = 0.05


def log(message):
    print("build_cargo_bay: %s" % message)


def extract(parts):
    """The .gltf and .bin of each part out of the kit zip, into a temporary folder."""
    folder = tempfile.mkdtemp(prefix="gamespace_kit_")
    with zipfile.ZipFile(KIT_ZIP) as kit:
        for part in parts:
            for ext in (".gltf", ".bin"):
                name = KIT_GLTF + part + ext
                target = os.path.join(folder, os.path.basename(name))
                with kit.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    return folder


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def place(template, location, rotation=(0.0, 0.0, 0.0), scale=1.0):
    """A copy of a part's mesh, as a new object (no operators, see Docs/WORKFLOW.md 9.2)."""
    obj = bpy.data.objects.new(template.name + "_copy", template.data.copy())
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = (scale, scale, scale)
    return obj


def base_name(name):
    return name.split(".")[0]


def main():
    if not os.path.exists(SHELL):
        raise SystemExit("build_cargo_bay: chybí %s" % SHELL)
    if not os.path.exists(KIT_ZIP):
        raise SystemExit("build_cargo_bay: chybí kit %s (README vedle)" % KIT_ZIP)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    shell = import_glb(SHELL)
    shell_materials = {base_name(m.name): m for o in shell for m in o.data.materials if m}
    log("shell: %d objektů, materiály %s" % (len(shell), ", ".join(sorted(shell_materials))))

    folder = extract((CEILING_PART, LAMP_PART))
    ceiling_src = import_glb(os.path.join(folder, os.path.basename(CEILING_PART) + ".gltf"))[0]
    lamp_src = import_glb(os.path.join(folder, os.path.basename(LAMP_PART) + ".gltf"))[0]

    added = []
    # Ceiling tiles, turned face down (180 degrees about X) a hair under the shell's plate.
    tile = 4.0 * CEILING_SCALE
    nx = int(round((BAY_X[1] - BAY_X[0]) / tile))
    ny = int(round((BAY_Y[1] - BAY_Y[0]) / tile))
    for i in range(nx):
        for j in range(ny):
            added.append(place(ceiling_src,
                               (BAY_X[0] + (i + 0.5) * tile, BAY_Y[0] + (j + 0.5) * tile, CEILING_Z - 0.005),
                               rotation=(math.pi, 0.0, 0.0), scale=CEILING_SCALE))
    # Fixtures: the part runs from -1.32 to 0 along X and hangs 15 cm below its origin.
    lamp_length = -min(v.co.x for v in lamp_src.data.vertices)
    for y in LAMP_ROWS_Y:
        for x in LAMP_X:
            added.append(place(lamp_src, (x + lamp_length / 2.0, y, CEILING_Z - 0.01)))
    log("strop: %d desek %dx%d, %d svítidel" % (nx * ny, nx, ny, len(LAMP_ROWS_Y) * len(LAMP_X)))
    # Liner: the plate's face is +Z; turned about Y it faces along X, about X along Y.
    half = tile / 2.0
    liner = 0
    for x, turn in ((BAY_X[0] - LINER_OFFSET, math.pi / 2.0), (BAY_X[1] + LINER_OFFSET, -math.pi / 2.0)):
        for j in range(ny):
            added.append(place(ceiling_src, (x, BAY_Y[0] + (j + 0.5) * tile, half),
                               rotation=(0.0, turn, 0.0), scale=CEILING_SCALE))
            liner += 1
    for y, turn in ((BAY_Y[0] - LINER_OFFSET, -math.pi / 2.0), (BAY_Y[1] + LINER_OFFSET, math.pi / 2.0)):
        for i in range(nx):
            added.append(place(ceiling_src, (BAY_X[0] + (i + 0.5) * tile, y, half),
                               rotation=(turn, 0.0, 0.0), scale=CEILING_SCALE))
            liner += 1
    log("obložení: %d desek" % liner)

    # Materials: the shell's own for the trim sheets, a named one for the lamps' glowing face.
    lamp = bpy.data.materials.new(LAMP_MATERIAL)
    lamp.use_nodes = True
    bsdf = next(n for n in lamp.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    for obj in added:
        for slot in obj.material_slots:
            name = base_name(slot.material.name) if slot.material else ""
            if name == "M_Light":
                slot.material = lamp
            elif name in shell_materials:
                slot.material = shell_materials[name]
            else:
                raise SystemExit("build_cargo_bay: materiál %s shell nemá" % name)
    for src in (ceiling_src, lamp_src):
        bpy.data.objects.remove(src, do_unlink=True)
    shutil.rmtree(folder, ignore_errors=True)

    # One mesh, like the shell was.
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    target = shell[0]
    with bpy.context.temp_override(active_object=target, selected_editable_objects=meshes, selected_objects=meshes):
        bpy.ops.object.join()
    target.name = "CargoBay"
    triangles = sum(len(p.vertices) - 2 for p in target.data.polygons)
    log("slito: %d trojúhelníků" % triangles)

    bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=False, export_apply=True)
    log("uloženo %s" % OUT)


main()
