"""Build the Steadfast interior: cargo bay, corridor towards the cockpit, engine room.

    MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \\
        --python Tools/Blender/build_steadfast_interior.py

Vstupy (vše relativně ke kořeni repozitáře):
- `ArtSource/Ships/Steadfast/Interior/CargoBay_Shell.glb` - nákladový prostor tak, jak byl poskládaný
  z kitu 23. 9. 2026 (podlaha, stěny, bedny, sloup s potrubím);
- `ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip` - kit (CC0, mimo git, návod k získání
  v README vedle něj). Skript si z něj vybalí jen ty díly, které potřebuje.

Výstup do `ArtSource/Ships/Steadfast/Interior/`: `CargoBay.glb`, `Corridor.glb`, `EngineRoom.glb`
(každá místnost jeden mesh) a `Interior_lights.json` (kde visí svítidla a kde svítí akcenty; podle
něj staví světla `Tools/Assets/import_interior.py`).

Rozvržení (souřadnice Blenderu v metrech, Z nahoru, +X je směr letu; Unreal má stejné X a Z a Y
zrcadlené). Podlaha shellu přečnívá o metr za jeho stěny, takže mezi místnostmi je přepážka 1 m
a průchod přes ni:

    strojovna x -7..-1 | průchod -1..0 | nákladový prostor 0..8 | průchod 8..9 | chodba 9..17 | dveře ke kokpitu

Proč strop nákladového prostoru: shell strop má - desku 8 x 6 m ve 2 m - jenže je to podlahový díl
lícem nahoru. Materiál v Unrealu je jednostranný, takže zevnitř deska neexistovala a nahoře byl vidět
vesmír. Stěny shellu prostor neuzavíraly a některé panely míří ven, proto je za nimi obložení lícem
dovnitř (HANDOFF bod 60, WORKFLOW 9.3 h).

Materiály dílů se přemapují na materiály shellu stejného jména (MI_Trim_01 -> MI_Trim_01), takže
nepřibývá žádná textura. Svítidla dostanou `M_Lamp` - import ho pozná podle jména a dá mu studenou
bílou emisi (`MI_KitLamp`).
"""

import json
import math
import os
import shutil
import tempfile
import zipfile

import bmesh
import bpy
import mathutils

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FOLDER = os.path.join(ROOT, "ArtSource", "Ships", "Steadfast", "Interior")
SHELL = os.path.join(FOLDER, "CargoBay_Shell.glb")
LIGHTS = os.path.join(FOLDER, "Interior_lights.json")
KIT_ZIP = os.path.join(ROOT, "ArtSource", "ThirdParty", "Quaternius", "ModularSciFiMegaKit.zip")
KIT_GLTF = "Modular SciFi MegaKit[Standard]/glTF/"

HEIGHT = 2.0                   # floor to ceiling everywhere; the shell's plate sits at 2 m
ARCH = 0.5                     # kit architecture is built for a 4 m grid; a ship wants half
LAMP_MATERIAL = "M_Lamp"
LINER_OFFSET = 0.05            # the cargo bay's liner, just behind its walls

# The cargo bay as the shell has it.
BAY_X = (0.0, 8.0)
BAY_Y = (-3.0, 3.0)
BAY_LAMPS = [(x, y) for y in (-1.5, 1.5) for x in (1.4, 4.0, 6.6)]
# Orange strips low down. They stood outside the walls at y +-3.4 until the liner closed the bay.
BAY_ACCENTS = [(4.0, -2.6, 0.6), (4.0, 2.6, 0.6)]
# Doorways in the bay's end walls, 2 m wide around y = 0: to the engine room aft, the corridor fore.
DOOR_HALF = 1.0

CORRIDOR_X = (9.0, 17.0)
CORRIDOR_Y = (-1.0, 1.0)
CORRIDOR_LAMPS = [(10.5, 0.0), (13.0, 0.0), (15.5, 0.0)]
CORRIDOR_ACCENTS = [(16.6, 0.0, 1.8)]           # over the closed door to the cockpit

ENGINE_X = (-7.0, -1.0)
ENGINE_Y = (-3.0, 3.0)
ENGINE_LAMPS = [(x, y) for y in (-1.5, 1.5) for x in (-5.5, -2.5)]
ENGINE_ACCENTS = [(-4.0, -1.4, 0.3), (-4.0, 1.4, 0.3)]    # at the foot of the core

PARTS = {
    "floor": "Platforms/Platform_Metal2",
    "floor_dark": "Platforms/Platform_DarkPlates",
    "ceiling": "Platforms/Platform_DarkPlates",
    "wall": "Walls/ShortWall_Metal2_Straight",
    "wall_dark": "Walls/ShortWall_DarkMetal2_Straight",
    "lamp": "Props/Prop_Light_Wide",
    "door_frame": "Platforms/Door_Frame_Square",
    "door": "Platforms/Door_DarkMetal",
    "vent": "Props/Prop_Vent_Big",
    "terminal": "Props/Prop_AccessPoint",
    "computer": "Props/Prop_Computer",
    "core": "Columns/Column_Hollow",
    "pipes": "Columns/Column_Pipes",
    "pipe_holder": "Props/Prop_PipeHolder",
}


def log(message):
    print("build_steadfast_interior: %s" % message)


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def load_parts(folder):
    """Every part once, out of the kit zip, as a hidden template object."""
    templates = {}
    with zipfile.ZipFile(KIT_ZIP) as kit:
        for key, part in PARTS.items():
            for ext in (".gltf", ".bin"):
                name = KIT_GLTF + part + ext
                with kit.open(name) as src, open(os.path.join(folder, os.path.basename(name)), "wb") as dst:
                    shutil.copyfileobj(src, dst)
    for key, part in PARTS.items():
        found = [o for o in bpy.data.objects if o.get("kit_part") == part]
        if found:
            templates[key] = found[0]
            continue
        objects = import_glb(os.path.join(folder, os.path.basename(part) + ".gltf"))
        obj = objects[0]
        obj["kit_part"] = part
        templates[key] = obj
    return templates


class Room:
    """Objects that end up as one mesh, and the lights that go with them."""

    def __init__(self, name):
        self.name = name
        self.objects = []
        self.lamps = []
        self.accents = []

    def place(self, template, centre, yaw=0.0, scale=(1.0, 1.0, 1.0), roll=0.0):
        """A copy of the part with its bounding box centred on `centre`, turned `yaw` about Z
        (after an optional `roll` about X), scaled in its own axes. No operators (WORKFLOW 9.2)."""
        obj = bpy.data.objects.new("%s_%s" % (self.name, template.name), template.data.copy())
        bpy.context.scene.collection.objects.link(obj)
        rotation = mathutils.Euler((roll, 0.0, yaw), "XYZ")
        corners = [mathutils.Vector(c) for c in template.bound_box]
        local_centre = sum(corners, mathutils.Vector()) / 8.0
        scaled = mathutils.Vector((local_centre.x * scale[0], local_centre.y * scale[1], local_centre.z * scale[2]))
        obj.rotation_euler = rotation
        obj.scale = scale
        obj.location = mathutils.Vector(centre) - rotation.to_matrix() @ scaled
        self.objects.append(obj)
        return obj


def floor(room, part, xs, ys, z=0.0):
    plates(room, part, xs, ys, z, roll=0.0)


def ceiling(room, part, xs, ys, z=HEIGHT - 0.005):
    """Dark plates face down."""
    plates(room, part, xs, ys, z, roll=math.pi)


def plates(room, part, xs, ys, z, roll):
    """Kit plates over a rectangle; a span that is not a whole number of tiles gets stretched tiles."""
    tile = 4.0 * ARCH
    nx = max(1, int(round((xs[1] - xs[0]) / tile)))
    ny = max(1, int(round((ys[1] - ys[0]) / tile)))
    sx = (xs[1] - xs[0]) / nx / 4.0
    sy = (ys[1] - ys[0]) / ny / 4.0
    for i in range(nx):
        for j in range(ny):
            room.place(part, (xs[0] + (i + 0.5) * (xs[1] - xs[0]) / nx, ys[0] + (j + 0.5) * (ys[1] - ys[0]) / ny, z),
                       scale=(sx, sy, ARCH), roll=roll)


def wall(room, part, a, b, inward, gaps=()):
    """A wall from a to b (2D points at floor level), panels facing `inward`, 2 m segments stacked
    twice to the ceiling. `gaps` are (from, to) distances along the wall left open for a doorway."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    length = (b - a).length
    along = (b - a).normalized()
    yaw = math.atan2(inward[1], inward[0])       # the panel faces its own +X
    segment = 4.0 * ARCH
    count = max(1, int(round(length / segment)))
    width = length / count
    row = 2.0 * ARCH                              # panel height at this scale: 1 m
    rows = int(round(HEIGHT / row))
    for i in range(count):
        s0, s1 = i * width, (i + 1) * width
        if any(g0 < s1 - 0.01 and g1 > s0 + 0.01 for g0, g1 in gaps):
            continue
        mid = a + along * ((s0 + s1) / 2.0)
        for r in range(rows):
            room.place(part, (mid.x, mid.y, (r + 0.5) * row), yaw=yaw,
                       scale=(1.0, width / 4.0, HEIGHT / rows / 2.0))


def doorway(room, templates, centre, passage_dir, closed=False):
    """The kit's square frame in a doorway; `passage_dir` is the way through."""
    yaw = math.atan2(passage_dir[1], passage_dir[0]) - math.pi / 2.0    # the frame's depth is its Y
    scale = HEIGHT / 5.0
    room.place(templates["door_frame"], (centre[0], centre[1], HEIGHT / 2.0), yaw=yaw, scale=(scale,) * 3)
    if closed:
        leaf = templates["door"]
        width = 2.11 * scale
        side = mathutils.Vector((-passage_dir[1], passage_dir[0], 0.0))
        for sign in (-1.0, 1.0):
            spot = mathutils.Vector((centre[0], centre[1], 0.0)) + side * (sign * width / 2.0)
            room.place(leaf, (spot.x, spot.y, 4.05 * scale / 2.0), yaw=yaw + (math.pi if sign > 0 else 0.0),
                       scale=(scale,) * 3)


def lamps(room, template, spots):
    length = template.dimensions.x
    for x, y in spots:
        room.place(template, (x, y, HEIGHT - 0.085))
        room.lamps.append((x, y, HEIGHT))


def open_shell_doorways(shell):
    """Cut the doorways into the shell's end walls, and take out its door frame, which stood
    across the far wall edge-on (turned 90 degrees in the kit-bash) and led nowhere."""
    mesh = shell.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    names = [m.name if m else "" for m in mesh.materials]
    doomed = []
    for face in bm.faces:
        c = shell.matrix_world @ face.calc_center_median()
        n = shell.matrix_world.to_3x3() @ face.normal
        # Vertical faces only - the floor runs through the doorway - and all the way through the
        # bulkhead: the shell also closes its floor overhang with a wall 1 m further out.
        in_bulkhead = BAY_X[1] - 0.15 < c.x < CORRIDOR_X[0] + 0.15 or ENGINE_X[1] - 0.15 < c.x < BAY_X[0] + 0.15
        in_doorway = (in_bulkhead and abs(c.y) < DOOR_HALF - 0.01 and 0.0 < c.z < HEIGHT + 0.01
                      and abs(n.z) < 0.5)
        stray_frame = names[face.material_index] == "MI_Trim_01.001" and 6.5 < c.x < 9.5 and abs(c.y) < 0.4
        if in_doorway or stray_frame:
            doomed.append(face)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    log("shell: vyříznuto %d ploch (průchody a starý dveřní rám)" % len(doomed))


def build_bay(shell, templates):
    room = Room("CargoBay")
    open_shell_doorways(shell)
    room.objects.append(shell)
    ceiling(room, templates["ceiling"], BAY_X, BAY_Y)
    lamps(room, templates["lamp"], BAY_LAMPS)
    liner = templates["ceiling"]
    tile = 4.0 * ARCH
    for x, turn in ((BAY_X[0] - LINER_OFFSET, 1.0), (BAY_X[1] + LINER_OFFSET, -1.0)):
        for j in range(int(round((BAY_Y[1] - BAY_Y[0]) / tile))):
            y = BAY_Y[0] + (j + 0.5) * tile
            if abs(y) < DOOR_HALF:
                continue                      # the doorway
            obj = room.place(liner, (x, y, HEIGHT / 2.0), scale=(ARCH,) * 3)
            obj.rotation_euler = (0.0, turn * math.pi / 2.0, 0.0)
    for y, turn in ((BAY_Y[0] - LINER_OFFSET, -1.0), (BAY_Y[1] + LINER_OFFSET, 1.0)):
        for i in range(int(round((BAY_X[1] - BAY_X[0]) / tile))):
            obj = room.place(liner, (BAY_X[0] + (i + 0.5) * tile, y, HEIGHT / 2.0), scale=(ARCH,) * 3)
            obj.rotation_euler = (turn * math.pi / 2.0, 0.0, 0.0)
    # Passages through the 1 m bulkheads to either side. The shell's floor overhang there faces
    # down, so they get a floor of their own too.
    for xs in ((BAY_X[1], CORRIDOR_X[0]), (ENGINE_X[1], BAY_X[0])):
        floor(room, templates["floor"], xs, (-DOOR_HALF, DOOR_HALF), z=0.003)
        wall(room, templates["wall"], (xs[0], -DOOR_HALF), (xs[1], -DOOR_HALF), (0.0, 1.0))
        wall(room, templates["wall"], (xs[0], DOOR_HALF), (xs[1], DOOR_HALF), (0.0, -1.0))
        ceiling(room, templates["ceiling"], xs, (-DOOR_HALF, DOOR_HALF))
    doorway(room, templates, (BAY_X[1], 0.0), (1.0, 0.0))
    doorway(room, templates, (BAY_X[0], 0.0), (-1.0, 0.0))
    room.accents = list(BAY_ACCENTS)
    return room


def build_corridor(templates):
    room = Room("Corridor")
    floor(room, templates["floor"], CORRIDOR_X, CORRIDOR_Y)
    ceiling(room, templates["ceiling"], CORRIDOR_X, CORRIDOR_Y)
    wall(room, templates["wall"], (CORRIDOR_X[0], CORRIDOR_Y[0]), (CORRIDOR_X[1], CORRIDOR_Y[0]), (0.0, 1.0))
    wall(room, templates["wall"], (CORRIDOR_X[0], CORRIDOR_Y[1]), (CORRIDOR_X[1], CORRIDOR_Y[1]), (0.0, -1.0))
    wall(room, templates["wall_dark"], (CORRIDOR_X[1], CORRIDOR_Y[0]), (CORRIDOR_X[1], CORRIDOR_Y[1]), (-1.0, 0.0))
    doorway(room, templates, (CORRIDOR_X[1] - 0.12, 0.0), (1.0, 0.0), closed=True)
    lamps(room, templates["lamp"], CORRIDOR_LAMPS)
    # A terminal by the cockpit door, a vent in the ceiling halfway.
    room.place(templates["terminal"], (16.0, CORRIDOR_Y[1] - 0.25, 1.35), yaw=-math.pi / 2.0)
    room.place(templates["vent"], (12.0, 0.0, HEIGHT - 0.04), roll=math.pi)
    room.accents = list(CORRIDOR_ACCENTS)
    return room


def build_engine_room(templates):
    room = Room("EngineRoom")
    floor(room, templates["floor_dark"], ENGINE_X, ENGINE_Y)
    ceiling(room, templates["ceiling"], ENGINE_X, ENGINE_Y)
    x0, x1 = ENGINE_X
    y0, y1 = ENGINE_Y
    gap = ((y1 - y0) / 2.0 - DOOR_HALF, (y1 - y0) / 2.0 + DOOR_HALF)
    wall(room, templates["wall_dark"], (x0, y0), (x1, y0), (0.0, 1.0))
    wall(room, templates["wall_dark"], (x0, y1), (x1, y1), (0.0, -1.0))
    wall(room, templates["wall_dark"], (x0, y0), (x0, y1), (1.0, 0.0))
    wall(room, templates["wall_dark"], (x1, y0), (x1, y1), (-1.0, 0.0), gaps=[gap])
    lamps(room, templates["lamp"], ENGINE_LAMPS)
    # The power plant: a core with four pipe columns round it, all floor to ceiling.
    core_x = (x0 + x1) / 2.0
    room.place(templates["core"], (core_x, 0.0, HEIGHT / 2.0), scale=(0.8, 0.8, HEIGHT / 5.0))
    for dx, dy in ((1.0, 1.0), (1.0, -1.0), (-1.0, 1.0), (-1.0, -1.0)):
        room.place(templates["pipes"], (core_x + 0.9 * dx, 0.9 * dy, HEIGHT / 2.0), scale=(0.6, 0.6, HEIGHT / 5.0))
    # Pipe racks along the side walls, a console facing the core.
    for y, yaw in ((y0 + 0.65, 0.0), (y1 - 0.65, math.pi)):
        room.place(templates["pipe_holder"], (core_x, y, 0.47), yaw=yaw)
    room.place(templates["computer"], (x1 - 0.55, -1.6, 0.8), yaw=-math.pi / 2.0)
    room.accents = list(ENGINE_ACCENTS)
    return room


def finish(room, shell_materials, lamp):
    """Shell materials on every part, the lamp material on the fixtures' glow, one mesh, one GLB."""
    for obj in room.objects:
        for slot in obj.material_slots:
            name = slot.material.name.split(".")[0] if slot.material else ""
            if name == "M_Light":
                slot.material = lamp
            elif name in shell_materials:
                slot.material = shell_materials[name]
            else:
                raise SystemExit("build_steadfast_interior: materiál %s shell nemá" % name)
    target = room.objects[0]
    with bpy.context.temp_override(active_object=target, selected_editable_objects=room.objects,
                                   selected_objects=room.objects):
        bpy.ops.object.join()
    target.name = room.name
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == target)
    path = os.path.join(FOLDER, room.name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True)
    triangles = sum(len(p.vertices) - 2 for p in target.data.polygons)
    log("%s: %d trojúhelníků, %d svítidel, %d akcentů -> %s" % (room.name, triangles, len(room.lamps), len(room.accents), path))
    bpy.data.objects.remove(target, do_unlink=True)


def main():
    for path in (SHELL, KIT_ZIP):
        if not os.path.exists(path):
            raise SystemExit("build_steadfast_interior: chybí %s" % path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell = import_glb(SHELL)[0]
    shell_materials = {}
    for material in shell.data.materials:
        if material:
            shell_materials.setdefault(material.name.split(".")[0], material)
    folder = tempfile.mkdtemp(prefix="gamespace_kit_")
    templates = load_parts(folder)

    lamp = bpy.data.materials.new(LAMP_MATERIAL)
    lamp.use_nodes = True
    bsdf = next(n for n in lamp.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bsdf.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.0

    rooms = [build_bay(shell, templates), build_corridor(templates), build_engine_room(templates)]
    lights = {}
    for room in rooms:
        lights[room.name] = {"work": [list(p) for p in room.lamps], "accent": [list(p) for p in room.accents]}
        finish(room, shell_materials, lamp)
    for template in set(templates.values()):     # one part can serve twice (floor and ceiling)
        bpy.data.objects.remove(template, do_unlink=True)
    shutil.rmtree(folder, ignore_errors=True)
    with open(LIGHTS, "w", encoding="utf-8") as out:
        json.dump({"_comment": "Světla interiéru Steadfastu v metrech, souřadnice Blenderu (Unreal: Y zrcadlené). "
                               "Píše Tools/Blender/build_steadfast_interior.py, čte Tools/Assets/import_interior.py. "
                               "work = svítidla pod stropem (bodovka míří dolů), accent = oranžová světla.",
                   **lights}, out, ensure_ascii=False, indent=1)
    log("světla -> %s" % LIGHTS)


main()
