"""Build the Steadfast interior: engine room, cargo bay, corridor, cockpit.

    MSYS_NO_PATHCONV=1 "/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b \\
        --python Tools/Blender/build_steadfast_interior.py

Vstupy (vše relativně ke kořeni repozitáře):
- `ArtSource/Ships/Steadfast/Interior/CargoBay_Shell.glb` - nákladový prostor tak, jak byl poskládaný
  z kitu 23. 9. 2026 (podlaha, stěny, bedny, sloup s potrubím);
- `ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip` - kit (CC0, mimo git, návod k získání
  v README vedle něj). Skript si z něj vybalí jen ty díly, které potřebuje.

Výstup do `ArtSource/Ships/Steadfast/Interior/`:
- `CargoBay.glb`, `Corridor.glb`, `EngineRoom.glb`, `Cockpit.glb` - každá místnost jeden mesh;
- `CockpitGlass.glb` - sklo kokpitu zvlášť (průsvitný materiál nesmí na Nanite mesh);
- `DoorLeaf.glb` - jedno křídlo posuvných dveří, střed v počátku, tloušťka podél X;
- `Interior_layout.json` - kde visí svítidla, akcenty, displeje, dveře, kde hráč začíná a jak velký
  je box s umělou gravitací. Podle něj staví herce `Tools/Assets/import_interior.py`.

Rozvržení (souřadnice Blenderu v metrech, Z nahoru, +X je směr letu; Unreal má stejné X a Z a Y
zrcadlené). Podlaha shellu přečnívá o metr za jeho stěny, takže mezi místnostmi je přepážka 1 m:

    strojovna -7..-1 | průchod | nákladový prostor 0..8 | průchod | chodba 9..17 | dveře | kokpit 17..22

Strop je všude ve 2,4 m (HANDOFF bod 62): ve 2 m byl na postavu s kamerou za zády stísněný. Shell
má stěny jen 2 m vysoké, nad nimi je pás obložení. Dveřní rámy jsou vlastní (průchod 1,3 x 2,1 m),
rám z kitu měl průchod jen 1,4 m vysoký; nad rámem je nadpraží až ke stropu.

Proč strop nákladového prostoru: shell strop má - desku 8 x 6 m ve 2 m - jenže je to podlahový díl
lícem nahoru. Materiál v Unrealu je jednostranný, takže zevnitř deska neexistovala. Teď ji skript
maže úplně (svítidla visí nad ní a deska by jim stínila). Stěny shellu prostor neuzavíraly a některé
panely míří ven, proto je za nimi obložení lícem dovnitř (HANDOFF bod 60, WORKFLOW 9.3 h).

Materiály dílů se přemapují na materiály shellu stejného jména (MI_Trim_01 -> MI_Trim_01), takže
nepřibývá žádná textura. Vlastní materiály podle jména rozpozná import: `M_Lamp` (svítidla, studená
bílá), `M_Screen` (displeje kokpitu, modrá), `M_Light_Button` (tlačítka, oranžová, obsahuje
„light“), `M_Glass` (sklo).
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
LAYOUT = os.path.join(FOLDER, "Interior_layout.json")
KIT_ZIP = os.path.join(ROOT, "ArtSource", "ThirdParty", "Quaternius", "ModularSciFiMegaKit.zip")
KIT_GLTF = "Modular SciFi MegaKit[Standard]/glTF/"

HEIGHT = 2.4                   # floor to ceiling everywhere
SHELL_HEIGHT = 2.0             # the shell's walls, and its upward-facing plate that was the "ceiling"
# Doorways: our own frame. The kit's square frame has a 1.5 m lintel, so at the scale that fits a
# 2.4 m deck its opening was 1.4 m high - nobody walks through that.
OPEN_WIDTH = 1.3
OPEN_HEIGHT = 2.1
DOOR_HEIGHT = 2.25             # top of the frame; a header wall closes the rest up to the ceiling
FRAME_DEPTH = 0.24
ARCH = 0.5                     # kit architecture is built for a 4 m grid; a ship wants half
LINER_OFFSET = 0.05            # the cargo bay's liner, just behind its walls
DOOR_HALF = 1.0                # every doorway is 2 m wide, centred on y = 0

BAY_X = (0.0, 8.0)
BAY_Y = (-3.0, 3.0)
BAY_LAMPS = [(x, y) for y in (-1.5, 1.5) for x in (1.4, 4.0, 6.6)]
# Orange light low down. They stood outside the walls at y +-3.4 until the liner closed the bay.
BAY_ACCENTS = [(4.0, -2.6, 0.6), (4.0, 2.6, 0.6)]

CORRIDOR_X = (9.0, 17.0)
CORRIDOR_Y = (-1.0, 1.0)
CORRIDOR_LAMPS = [(10.5, 0.0), (13.0, 0.0), (15.5, 0.0)]
CORRIDOR_ACCENTS = [(16.6, 0.0, 2.2)]           # over the door to the cockpit

ENGINE_X = (-7.0, -1.0)
ENGINE_Y = (-3.0, 3.0)
ENGINE_LAMPS = [(x, y) for y in (-1.5, 1.5) for x in (-5.5, -2.5)]
ENGINE_ACCENTS = [(-4.0, -1.4, 0.3), (-4.0, 1.4, 0.3)]    # at the foot of the core

COCKPIT_X = (17.0, 22.0)
COCKPIT_Y = (-2.5, 2.5)
COCKPIT_LAMPS = [(18.4, -1.3), (18.4, 1.3)]
WINDOW_Z = (0.95, 2.05)        # the canopy opening in the front wall
MULLIONS_Y = (-0.9, 0.9)
DASH_Y = (-2.1, 2.1)
SEATS_Y = (-0.95, 0.95)
SEAT_X = 20.15
# Blue light off the displays, and where the player starts: in the cargo bay, facing forward.
COCKPIT_SCREENS = [(21.0, -0.95, 1.05), (21.0, 0.95, 1.05)]
SPAWN = (1.5, 0.0, 0.05)
GRAVITY_BOX = ((-7.3, -3.3, -0.4), (22.4, 3.3, 2.8))
DOORS = [{"at": (COCKPIT_X[0], 0.0, 0.0), "dir": (1.0, 0.0, 0.0)}]

PARTS = {
    "floor": "Platforms/Platform_Metal2",
    "floor_dark": "Platforms/Platform_DarkPlates",
    "ceiling": "Platforms/Platform_DarkPlates",
    "wall": "Walls/ShortWall_Metal2_Straight",
    "wall_dark": "Walls/ShortWall_DarkMetal2_Straight",
    "lamp": "Props/Prop_Light_Wide",
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
    """Every part once, out of the kit zip, as a template object."""
    templates = {}
    with zipfile.ZipFile(KIT_ZIP) as kit:
        for part in PARTS.values():
            for ext in (".gltf", ".bin"):
                name = KIT_GLTF + part + ext
                with kit.open(name) as src, open(os.path.join(folder, os.path.basename(name)), "wb") as dst:
                    shutil.copyfileobj(src, dst)
    for key, part in PARTS.items():
        found = [o for o in bpy.data.objects if o.get("kit_part") == part]
        if found:
            templates[key] = found[0]
            continue
        obj = import_glb(os.path.join(folder, os.path.basename(part) + ".gltf"))[0]
        obj["kit_part"] = part
        templates[key] = obj
    return templates


def material(name, colour=(0.0, 0.0, 0.0), emission=None, alpha=1.0):
    """A plain material the import recognises by name."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Alpha"].default_value = alpha
    return mat


class Room:
    """Objects that end up as one mesh, and the lights that go with them."""

    def __init__(self, name):
        self.name = name
        self.objects = []
        self.lamps = []
        self.accents = []
        self.screens = []

    def place(self, template, centre, yaw=0.0, scale=(1.0, 1.0, 1.0), roll=0.0, pitch=0.0):
        """A copy of the part with its bounding box centred on `centre`: rotated by roll (X),
        pitch (Y), yaw (Z) and scaled in its own axes. No operators (WORKFLOW 9.2)."""
        obj = bpy.data.objects.new("%s_%s" % (self.name, template.name), template.data.copy())
        bpy.context.scene.collection.objects.link(obj)
        rotation = mathutils.Euler((roll, pitch, yaw), "XYZ")
        corners = [mathutils.Vector(c) for c in template.bound_box]
        local_centre = sum(corners, mathutils.Vector()) / 8.0
        scaled = mathutils.Vector((local_centre.x * scale[0], local_centre.y * scale[1], local_centre.z * scale[2]))
        obj.rotation_euler = rotation
        obj.scale = scale
        obj.location = mathutils.Vector(centre) - rotation.to_matrix() @ scaled
        self.objects.append(obj)
        return obj

    def add(self, name, bm, mat):
        """A procedural piece (bmesh in world metres) with one material and box-projected UVs."""
        uv = bm.loops.layers.uv.verify()
        for face in bm.faces:
            n = face.normal
            axis = max(range(3), key=lambda i: abs(n[i]))
            u, v = [i for i in range(3) if i != axis]
            for loop in face.loops:
                loop[uv].uv = (loop.vert.co[u] * 0.5, loop.vert.co[v] * 0.5)
        mesh = bpy.data.meshes.new("%s_%s" % (self.name, name))
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        self.objects.append(obj)
        return obj


# --- procedural shapes --------------------------------------------------------------------------

def box(lo, hi, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    size = mathutils.Vector(hi) - mathutils.Vector(lo)
    centre = (mathutils.Vector(hi) + mathutils.Vector(lo)) / 2.0
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centre, verts=bm.verts)
    if bevel > 0.0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES")
    return bm


def prism(section_xz, y0, y1):
    """A section in the XZ plane (counter-clockwise seen from -Y) extruded from y0 to y1."""
    bm = bmesh.new()
    front = [bm.verts.new((x, y0, z)) for x, z in section_xz]
    back = [bm.verts.new((x, y1, z)) for x, z in section_xz]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    count = len(section_xz)
    for i in range(count):
        j = (i + 1) % count
        bm.faces.new((front[i], back[i], back[j], front[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def quad(corners):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(c) for c in corners])
    return bm


def turned(bm, angle_z, pivot):
    bmesh.ops.rotate(bm, verts=bm.verts, cent=pivot, matrix=mathutils.Matrix.Rotation(angle_z, 3, "Z"))
    return bm


# --- architecture ---------------------------------------------------------------------------------

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


def floor(room, part, xs, ys, z=0.0):
    plates(room, part, xs, ys, z, roll=0.0)


def ceiling(room, part, xs, ys, z=HEIGHT - 0.005):
    """Dark plates face down."""
    plates(room, part, xs, ys, z, roll=math.pi)


def wall(room, part, a, b, inward, gaps=(), z0=0.0, z1=HEIGHT):
    """A wall from a to b (2D, metres) between heights z0 and z1, panels facing `inward`: 2 m
    segments, stacked in rows of about 1 m. `gaps` are (from, to) distances along the wall left
    open for a doorway."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    length = (b - a).length
    along = (b - a).normalized()
    yaw = math.atan2(inward[1], inward[0])       # the panel faces its own +X
    count = max(1, int(round(length / (4.0 * ARCH))))
    width = length / count
    rows = max(1, int(round((z1 - z0) / (2.0 * ARCH))))
    row = (z1 - z0) / rows
    for i in range(count):
        s0, s1 = i * width, (i + 1) * width
        if any(g0 < s1 - 0.01 and g1 > s0 + 0.01 for g0, g1 in gaps):
            continue
        mid = a + along * ((s0 + s1) / 2.0)
        for r in range(rows):
            room.place(part, (mid.x, mid.y, z0 + (r + 0.5) * row), yaw=yaw,
                       scale=(1.0, width / 4.0, row / 2.0))


def doorway(room, templates, centre, passage_dir, mats):
    """A frame in a 2 m wide doorway along X (`passage_dir` is +-X): two jambs, a lintel with an
    orange strip either side, and a header above it up to the ceiling, facing both ways."""
    x, y = centre[0], centre[1]
    d = FRAME_DEPTH / 2.0
    for side in (-1.0, 1.0):
        lo, hi = sorted((y + side * OPEN_WIDTH / 2.0, y + side * DOOR_HALF))
        room.add("Jamb", box((x - d, lo, 0.0), (x + d, hi, DOOR_HEIGHT), bevel=0.02), mats["body"])
    room.add("Lintel", box((x - d, y - OPEN_WIDTH / 2.0, OPEN_HEIGHT), (x + d, y + OPEN_WIDTH / 2.0, DOOR_HEIGHT),
                           bevel=0.02), mats["body"])
    for sign in (-1.0, 1.0):
        face = x + sign * (d + 0.004)
        room.add("DoorStrip", box((min(face, face + sign * 0.01), y - OPEN_WIDTH / 2.0 + 0.1, OPEN_HEIGHT + 0.05),
                                  (max(face, face + sign * 0.01), y + OPEN_WIDTH / 2.0 - 0.1, OPEN_HEIGHT + 0.09)),
                 mats["button"])
        base = mathutils.Vector((x + sign * (d + 0.01), y))
        side = mathutils.Vector((0.0, 1.0))
        wall(room, templates["wall_dark"], base - side * DOOR_HALF, base + side * DOOR_HALF, (sign, 0.0),
             z0=DOOR_HEIGHT, z1=HEIGHT)


def lamps(room, template, spots):
    for x, y in spots:
        room.place(template, (x, y, HEIGHT - 0.085))
        room.lamps.append((x, y, HEIGHT))


def open_shell(shell):
    """Cut the doorways into the shell's end walls, take out its door frame - it stood across the
    far wall edge-on (turned 90 degrees in the kit-bash) and led nowhere - and its upward-facing
    plate at 2 m, which the fixtures now hang above."""
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
        in_doorway = in_bulkhead and abs(c.y) < DOOR_HALF - 0.01 and 0.0 < c.z < HEIGHT + 0.01 and abs(n.z) < 0.5
        stray_frame = names[face.material_index] == "MI_Trim_01.001" and 6.5 < c.x < 9.5 and abs(c.y) < 0.4
        # ...and the thin panel that went with it, standing edge-on down the middle of the bay in
        # front of the fore doorway: it read as a pole in the shots and stopped the player
        # walking back from the corridor (interior_walk, 23. 9. 2026).
        stray_frame = stray_frame or (names[face.material_index] in ("MI_Trim_02.001", "MI_Trim_01.002")
                                      and 6.8 < c.x < 8.2 and abs(c.y) < 0.2 and abs(n.z) < 0.5)
        old_ceiling = (n.z > 0.9 and abs(c.z - SHELL_HEIGHT) < 0.05 and BAY_X[0] - 1.1 < c.x < BAY_X[1] + 1.1
                       and abs(c.y) < BAY_Y[1] + 1.1)
        # A wall terminal the kit-bash sank half into the aft wall: its screen is behind the liner,
        # and all that stuck out was its top plate, which threw a black wedge of shadow down the
        # wall. build_bay() hangs a proper one in its place.
        sunk_terminal = -0.35 < c.x < 1.0 and 1.1 < c.y < 1.95 and 1.05 < c.z < 1.65
        if in_doorway or stray_frame or old_ceiling or sunk_terminal:
            doomed.append(face)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    log("shell: vyříznuto %d ploch (průchody, starý dveřní rám, deska ve 2 m, zapuštěný terminál)" % len(doomed))


# --- rooms ----------------------------------------------------------------------------------------

def build_bay(shell, templates, room_mats):
    room = Room("CargoBay")
    open_shell(shell)
    room.objects.append(shell)
    ceiling(room, templates["ceiling"], BAY_X, BAY_Y)
    lamps(room, templates["lamp"], BAY_LAMPS)
    # Liner: dark plates behind the walls, facing in, full height (the shell's walls stop at 2 m).
    liner = templates["ceiling"]
    tile = 4.0 * ARCH
    stretch = ARCH * HEIGHT / tile
    for x, turn in ((BAY_X[0] - LINER_OFFSET, 1.0), (BAY_X[1] + LINER_OFFSET, -1.0)):
        for j in range(int(round((BAY_Y[1] - BAY_Y[0]) / tile))):
            y = BAY_Y[0] + (j + 0.5) * tile
            if abs(y) < DOOR_HALF:
                continue                      # the doorway; doorway() puts a header above it
            obj = room.place(liner, (x, y, HEIGHT / 2.0), scale=(stretch, ARCH, ARCH))
            obj.rotation_euler = (0.0, turn * math.pi / 2.0, 0.0)
    for y, turn in ((BAY_Y[0] - LINER_OFFSET, -1.0), (BAY_Y[1] + LINER_OFFSET, 1.0)):
        for i in range(int(round((BAY_X[1] - BAY_X[0]) / tile))):
            obj = room.place(liner, (BAY_X[0] + (i + 0.5) * tile, y, HEIGHT / 2.0), scale=(ARCH, stretch, ARCH))
            obj.rotation_euler = (turn * math.pi / 2.0, 0.0, 0.0)
    # Passages through the 1 m bulkheads to either side. The shell's floor overhang there faces
    # down, so they get a floor of their own too.
    for xs in ((BAY_X[1], CORRIDOR_X[0]), (ENGINE_X[1], BAY_X[0])):
        floor(room, templates["floor"], xs, (-DOOR_HALF, DOOR_HALF), z=0.003)
        wall(room, templates["wall"], (xs[0], -DOOR_HALF), (xs[1], -DOOR_HALF), (0.0, 1.0))
        wall(room, templates["wall"], (xs[0], DOOR_HALF), (xs[1], DOOR_HALF), (0.0, -1.0))
        ceiling(room, templates["ceiling"], xs, (-DOOR_HALF, DOOR_HALF))
    room.place(templates["terminal"], (BAY_X[0] + 0.25, 1.6, 1.35), yaw=0.0)
    doorway(room, templates, (BAY_X[1], 0.0), (1.0, 0.0), room_mats)
    doorway(room, templates, (BAY_X[0], 0.0), (-1.0, 0.0), room_mats)
    room.accents = list(BAY_ACCENTS)
    return room


def build_corridor(templates, room_mats):
    room = Room("Corridor")
    floor(room, templates["floor"], CORRIDOR_X, CORRIDOR_Y)
    ceiling(room, templates["ceiling"], CORRIDOR_X, CORRIDOR_Y)
    wall(room, templates["wall"], (CORRIDOR_X[0], CORRIDOR_Y[0]), (CORRIDOR_X[1], CORRIDOR_Y[0]), (0.0, 1.0))
    wall(room, templates["wall"], (CORRIDOR_X[0], CORRIDOR_Y[1]), (CORRIDOR_X[1], CORRIDOR_Y[1]), (0.0, -1.0))
    doorway(room, templates, (CORRIDOR_X[1], 0.0), (1.0, 0.0), room_mats)   # the sliding door is its own actor
    lamps(room, templates["lamp"], CORRIDOR_LAMPS)
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
    for y, yaw in ((y0 + 0.65, 0.0), (y1 - 0.65, math.pi)):
        room.place(templates["pipe_holder"], (core_x, y, 0.47), yaw=yaw)
    room.place(templates["computer"], (x1 - 0.55, -1.6, 0.8), yaw=-math.pi / 2.0)
    room.accents = list(ENGINE_ACCENTS)
    return room


def seat(room, y, frame, cushion):
    """A pilot's seat facing +X: pedestal, seat pan, reclined back, headrest, armrests."""
    x = SEAT_X
    room.add("SeatBase", box((x - 0.14, y - 0.14, 0.0), (x + 0.14, y + 0.14, 0.38), bevel=0.02), frame)
    room.add("SeatPan", box((x - 0.28, y - 0.27, 0.38), (x + 0.26, y + 0.27, 0.5), bevel=0.03), cushion)
    back = box((x - 0.36, y - 0.27, 0.48), (x - 0.24, y + 0.27, 1.18), bevel=0.03)
    bmesh.ops.rotate(back, verts=back.verts, cent=(x - 0.3, y, 0.5),
                     matrix=mathutils.Matrix.Rotation(math.radians(-12.0), 3, "Y"))
    room.add("SeatBack", back, cushion)
    head = box((x - 0.52, y - 0.14, 1.2), (x - 0.4, y + 0.14, 1.42), bevel=0.03)
    room.add("SeatHead", head, cushion)
    for side in (-1.0, 1.0):
        arm = box((x - 0.22, y + side * 0.33 - 0.04, 0.62), (x + 0.2, y + side * 0.33 + 0.04, 0.68), bevel=0.01)
        room.add("SeatArm", arm, frame)


def dashboard(room, body, screen, button, dark):
    """The console along the canopy: a slanted desk with three displays and rows of buttons."""
    front = COCKPIT_X[1] - 0.05
    section = [(front, 0.0), (front - 0.55, 0.0), (front - 0.55, 0.62), (front - 0.95, 0.74),
               (front - 0.92, 0.82), (front, 1.0)]
    room.add("Dash", prism(section, DASH_Y[0], DASH_Y[1]), body)
    # The slanted face runs from (front-0.92, 0.82) to (front, 1.0); screens sit on it.
    a = mathutils.Vector((front - 0.86, 0.0, 0.835))
    b = mathutils.Vector((front - 0.12, 0.0, 0.985))
    normal = mathutils.Vector((-(b - a).z, 0.0, (b - a).x)).normalized() * -1.0
    if normal.z < 0.0:
        normal = -normal
    lift = normal * 0.006
    for y0, y1 in ((-1.75, -0.2), (-0.55, 0.55), (0.2, 1.75)):
        if (y0, y1) == (-0.55, 0.55):
            p0 = a + (b - a) * 0.08
            p1 = a + (b - a) * 0.62
        else:
            p0 = a + (b - a) * 0.25
            p1 = a + (b - a) * 0.95
        # Wound so that the face points up towards the pilot (the other way round it faced the floor).
        corners = [(p0.x, y0, p0.z), (p1.x, y0, p1.z), (p1.x, y1, p1.z), (p0.x, y1, p0.z)]
        room.add("Screen", quad([mathutils.Vector(c) + lift for c in corners]), screen)
    # Buttons along the edge nearest the pilot, a dark lip under them.
    room.add("DashLip", box((front - 0.97, DASH_Y[0], 0.70), (front - 0.9, DASH_Y[1], 0.76)), dark)
    for i in range(24):
        y = DASH_Y[0] + 0.2 + i * (DASH_Y[1] - DASH_Y[0] - 0.4) / 23.0
        if abs(y) < 0.6:
            continue
        p = a + (b - a) * 0.12
        room.add("Button", box((p.x - 0.02, y - 0.03, p.z - 0.01), (p.x + 0.02, y + 0.03, p.z + 0.012)), button)


def build_cockpit(templates, mats):
    room = Room("Cockpit")
    x0, x1 = COCKPIT_X
    y0, y1 = COCKPIT_Y
    floor(room, templates["floor"], COCKPIT_X, COCKPIT_Y)
    ceiling(room, templates["ceiling"], COCKPIT_X, COCKPIT_Y)
    wall(room, templates["wall_dark"], (x0, y0), (x1, y0), (0.0, 1.0))
    wall(room, templates["wall_dark"], (x0, y1), (x1, y1), (0.0, -1.0))
    # Back wall either side of the door, a little behind the frame so the door leaves slide in
    # behind it rather than through it.
    for a, b in (((x0 + 0.12, y0), (x0 + 0.12, -DOOR_HALF)), ((x0 + 0.12, DOOR_HALF), (x0 + 0.12, y1))):
        wall(room, templates["wall_dark"], a, b, (1.0, 0.0))
    # Front: a low wall, the canopy opening, a band to the ceiling; mullions split the glass.
    wall(room, templates["wall_dark"], (x1, y0), (x1, y1), (-1.0, 0.0), z1=WINDOW_Z[0])
    wall(room, templates["wall_dark"], (x1, y0), (x1, y1), (-1.0, 0.0), z0=WINDOW_Z[1])
    frame = mats["dark"]
    for y in (y0 + 0.05,) + MULLIONS_Y + (y1 - 0.05,):
        room.add("Mullion", box((x1 - 0.08, y - 0.05, WINDOW_Z[0] - 0.02), (x1 + 0.04, y + 0.05, WINDOW_Z[1] + 0.02), bevel=0.01), frame)
    for z in WINDOW_Z:
        room.add("Sill", box((x1 - 0.1, y0, z - 0.04), (x1 + 0.04, y1, z + 0.04), bevel=0.01), frame)
    dashboard(room, mats["body"], mats["screen"], mats["button"], mats["dark"])
    for y in SEATS_Y:
        seat(room, y, mats["dark"], mats["cushion"])
    lamps(room, templates["lamp"], COCKPIT_LAMPS)
    room.screens = list(COCKPIT_SCREENS)
    return room


def build_glass(mat):
    room = Room("CockpitGlass")
    x = COCKPIT_X[1] + 0.02
    room.add("Glass", quad([(x, COCKPIT_Y[0], WINDOW_Z[0]), (x, COCKPIT_Y[1], WINDOW_Z[0]),
                            (x, COCKPIT_Y[1], WINDOW_Z[1]), (x, COCKPIT_Y[0], WINDOW_Z[1])]), mat)
    return room


def build_door_leaf(templates):
    """One leaf that fills half the frame's opening (a little overlap), centred on the origin, thin
    along X."""
    room = Room("DoorLeaf")
    leaf = templates["door"]
    dims = leaf.dimensions                     # width X 2.11, thickness Y 0.2, height Z 4.05
    width, height = OPEN_WIDTH / 2.0 + 0.03, OPEN_HEIGHT + 0.02
    room.place(leaf, (0.0, 0.0, 0.0), yaw=math.pi / 2.0,
               scale=(width / dims.x, 0.06 / dims.y, height / dims.z))
    log("dveře: průchod %.2f x %.2f m, křídlo %.2f x %.2f m" % (OPEN_WIDTH, OPEN_HEIGHT, width, height))
    return room, width, height


def finish(room, shell_materials, own):
    """Shell materials on every kit part, our own by name, one mesh, one GLB."""
    for obj in room.objects:
        for slot in obj.material_slots:
            name = slot.material.name.split(".")[0] if slot.material else ""
            if name == "M_Light":
                slot.material = own["lamp"]
            elif name in own_names(own):
                continue
            elif name in shell_materials:
                slot.material = shell_materials[name]
            else:
                raise SystemExit("build_steadfast_interior: materiál %s shell nemá" % name)
    target = room.objects[0]
    if len(room.objects) > 1:
        with bpy.context.temp_override(active_object=target, selected_editable_objects=room.objects,
                                       selected_objects=room.objects):
            bpy.ops.object.join()
    target.name = room.name
    for obj in bpy.context.scene.objects:
        obj.select_set(obj == target)
    path = os.path.join(FOLDER, room.name + ".glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True)
    triangles = sum(len(p.vertices) - 2 for p in target.data.polygons)
    log("%s: %d trojúhelníků, %d svítidel -> %s" % (room.name, triangles, len(room.lamps), os.path.basename(path)))
    bpy.data.objects.remove(target, do_unlink=True)


def own_names(own):
    return {m.name for m in own.values()}


def main():
    for path in (SHELL, KIT_ZIP):
        if not os.path.exists(path):
            raise SystemExit("build_steadfast_interior: chybí %s" % path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell = import_glb(SHELL)[0]
    shell_materials = {}
    for mat in shell.data.materials:
        if mat:
            shell_materials.setdefault(mat.name.split(".")[0], mat)
    folder = tempfile.mkdtemp(prefix="gamespace_kit_")
    templates = load_parts(folder)

    own = {
        "lamp": material("M_Lamp", emission=(1.0, 1.0, 1.0)),
        "screen": material("M_Screen", emission=(0.2, 0.6, 1.0)),
        "button": material("M_Light_Button", emission=(1.0, 0.4, 0.1)),
        "glass": material("M_Glass", colour=(0.6, 0.7, 0.8), alpha=0.15),
    }
    mats = dict(own, body=shell_materials["MI_Trim_02"], dark=shell_materials["M_Black"],
                cushion=shell_materials["MI_PaddedWall"])

    rooms = [build_engine_room(templates), build_bay(shell, templates, mats), build_corridor(templates, mats),
             build_cockpit(templates, mats), build_glass(own["glass"])]
    leaf, leaf_width, leaf_height = build_door_leaf(templates)
    layout = {
        "_comment": "Interiér Steadfastu v metrech, souřadnice Blenderu (Unreal: Y zrcadlené). Píše "
                    "Tools/Blender/build_steadfast_interior.py, čte Tools/Assets/import_interior.py. "
                    "work = svítidla pod stropem (bodovka míří dolů), accent = oranžová světla, "
                    "screen = modré světlo displejů, doors = posuvné dveře (at = střed prahu, dir = směr "
                    "průchodu), spawn = kde hráč začíná, gravity_box = umělá gravitace.",
        "rooms": {},
        "doors": [dict(d, leaf=[leaf_width, leaf_height]) for d in DOORS],
        "spawn": list(SPAWN),
        "gravity_box": [list(GRAVITY_BOX[0]), list(GRAVITY_BOX[1])],
    }
    for room in rooms + [leaf]:
        layout["rooms"][room.name] = {"work": [list(p) for p in room.lamps],
                                      "accent": [list(p) for p in room.accents],
                                      "screen": [list(p) for p in room.screens]}
        finish(room, shell_materials, own)
    for template in set(templates.values()):     # one part can serve twice (floor and ceiling)
        bpy.data.objects.remove(template, do_unlink=True)
    shutil.rmtree(folder, ignore_errors=True)
    with open(LAYOUT, "w", encoding="utf-8") as out:
        json.dump(layout, out, ensure_ascii=False, indent=1)
    old = os.path.join(FOLDER, "Interior_lights.json")
    if os.path.exists(old):
        os.remove(old)
    log("rozvržení -> %s" % LAYOUT)


main()
