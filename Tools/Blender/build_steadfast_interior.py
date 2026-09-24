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
„light“), `M_Glass` (sklo), `M_White` (bílé plasty), `M_Black_Seat` (sedadla, obsahuje „black“).
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
HULL_GAP = 0.25                # the dark hull box stands this far outside the outermost walls
HULL_TOP = 2.7
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

COCKPIT_X = (17.0, 22.4)
COCKPIT_Y = (-2.5, 2.5)
# The canopy, after the author's reference (Docs/UI, Constellation cockpit 20. 9. 2026): glass over
# the pilots' heads and down the sides, carried by heavy dark beams. Three ribs, each a polyline
# (y, z) from the left sill over the roof to the right sill; beams run along every rib and from rib
# to rib, glass fills between. The back of the room (x 17..CANOPY_START) is an ordinary deck.
CANOPY_START = 18.6
CANOPY_RIBS = [
    (18.6, [(-2.5, 0.95), (-2.5, 2.4), (-1.0, 2.8), (1.0, 2.8), (2.5, 2.4), (2.5, 0.95)]),
    (20.6, [(-2.3, 0.9), (-2.2, 2.3), (-0.9, 2.65), (0.9, 2.65), (2.2, 2.3), (2.3, 0.9)]),
    (22.4, [(-1.35, 0.95), (-1.25, 1.65), (-0.6, 1.95), (0.6, 1.95), (1.25, 1.65), (1.35, 0.95)]),
]
BEAM = (0.16, 0.12)            # width, depth of a canopy beam
COCKPIT_LAMPS = [(17.8, 0.0)]
SEATS_Y = (-0.95, 0.95)
SEAT_X = 19.9
DASH_X = (21.0, 22.2)
# Blue light off the MFDs in front of each pilot, and where the player starts: in the cargo bay.
COCKPIT_SCREENS = [(20.9, -0.95, 1.2), (20.9, 0.95, 1.2)]
# Hero props from Meshy (ArtSource/Ships/Steadfast/Kitbash/Meshy, HANDOFF point 68): placed by the
# import as their own actors with their own textures, instead of the blocky procedural pieces.
# at = floor point under the prop's centre, yaw = where its front faces (degrees, Blender, +X = 0),
# width = the size of its bounding box along its own X after scaling (uniform scale).
MESHY_PROPS = [
    {"mesh": "PilotSeat", "at": (SEAT_X - 0.05, y, 0.0), "yaw": 0.0, "width": 0.84} for y in SEATS_Y
] + [
    {"mesh": "SideConsole", "at": (SEAT_X + 0.15, side * 1.82, 0.0), "yaw": 0.0, "width": 1.15} for side in (-1.0, 1.0)
] + [
    {"mesh": "EquipmentRack", "at": (ENGINE_X[0] + 0.45, 1.9, 0.0), "yaw": 0.0, "width": 1.3},
]
# Stencil decals from the Scenario atlas (ArtSource/Ships/Steadfast/Interior/Decals, HANDOFF point 69).
# cell = index in the 4 x 4 atlas, left to right, top to bottom: 0 yellow hazard stripes, 1 CARGO BAY,
# 2 ENGINE ROOM, 3 COCKPIT, 4-6 DECK A-01..03, 7 arrow (points right), 8 warning triangle,
# 9 CAUTION HIGH VOLTAGE, 10 NO STEP, 11 HALCYON FREIGHTWORKS, 12 FIRE SUPPRESSION, 13 AIRLOCK, 14 "07",
# 15 orange hazard stripes. at = point on the surface, normal = which way the surface faces, size = m.
DECALS = [
    # cargo bay
    {"cell": 1, "at": (7.95, 2.0, 1.55), "normal": (-1, 0, 0), "size": 0.9},
    {"cell": 14, "at": (2.5, 2.95, 1.35), "normal": (0, -1, 0), "size": 0.9},
    {"cell": 12, "at": (5.5, -2.95, 1.5), "normal": (0, 1, 0), "size": 0.7},
    {"cell": 5, "at": (0.05, -2.0, 1.55), "normal": (1, 0, 0), "size": 0.8},
    {"cell": 0, "at": (7.45, 0.0, 0.01), "normal": (0, 0, 1), "size": 1.2},
    {"cell": 0, "at": (0.55, 0.0, 0.01), "normal": (0, 0, 1), "size": 1.2},
    # corridor
    {"cell": 3, "at": (11.0, -0.97, 1.55), "normal": (0, 1, 0), "size": 0.8},
    {"cell": 7, "at": (12.0, -0.97, 1.55), "normal": (0, 1, 0), "size": 0.5},
    {"cell": 11, "at": (13.5, 0.97, 1.5), "normal": (0, -1, 0), "size": 0.8},
    {"cell": 6, "at": (10.2, 0.97, 1.55), "normal": (0, -1, 0), "size": 0.6},
    {"cell": 15, "at": (16.45, 0.0, 0.01), "normal": (0, 0, 1), "size": 1.1},
    # engine room
    {"cell": 2, "at": (-1.07, -2.0, 1.6), "normal": (-1, 0, 0), "size": 0.9},
    {"cell": 9, "at": (-3.5, -2.95, 1.4), "normal": (0, 1, 0), "size": 0.8},
    {"cell": 8, "at": (-2.2, 2.95, 1.45), "normal": (0, -1, 0), "size": 0.5},
    {"cell": 10, "at": (-4.0, 1.9, 0.01), "normal": (0, 0, 1), "size": 0.8},
    {"cell": 4, "at": (-6.93, -1.8, 1.6), "normal": (1, 0, 0), "size": 0.7},
    {"cell": 0, "at": (-1.55, 0.0, 0.01), "normal": (0, 0, 1), "size": 1.2},
]
SPAWN = (1.5, 0.0, 0.05)
GRAVITY_BOX = ((-7.3, -3.3, -0.4), (22.8, 3.3, 3.0))
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

    def add(self, name, bm, mat, face_towards=None, uvs=None):
        """A procedural piece (bmesh in world metres) with one material and box-projected UVs.
        `face_towards`: turn every face to look at this point - for single-sided panels that must
        face into the room (a panel facing out is not there from inside, WORKFLOW 9.3 h)."""
        if face_towards is not None:
            bm.normal_update()           # a face made with faces.new() has a zero normal until now
            target = mathutils.Vector(face_towards)
            flip = [f for f in bm.faces if f.normal.dot(target - f.calc_center_median()) < 0.0]
            bmesh.ops.reverse_faces(bm, faces=flip)
        uv = bm.loops.layers.uv.verify()
        if uvs is not None:
            bm.verts.index_update()      # new vertices have index -1 until this
            # A screen: one face whose vertices were made in the order the picture's corners are
            # given (bottom left, bottom right, top right, top left, or a disc's rim).
            for face in bm.faces:
                for loop in face.loops:
                    loop[uv].uv = uvs[loop.vert.index]
            uvs_done = True
        else:
            uvs_done = False
        for face in ([] if uvs_done else bm.faces):
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
    for side in (-1.0, 1.0):
        face = y + side * (OPEN_WIDTH / 2.0 - 0.012)
        strip(room, (x, face, 0.15), (x, face, OPEN_HEIGHT - 0.1), mats["strip"], size=(0.03, 0.02))
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


def duplicate_islands(bm):
    """Loose parts that lie over another part face for face: the kit-bash put six crates twice into
    the same space. Their sides fight for the same pixels (z-fighting), which is the flicker the
    author saw on the crates (23. 9. 2026). Returns the faces of every second copy."""
    island = {}
    for start in bm.faces:
        if start.index in island:
            continue
        mark = len(set(island.values()))
        island[start.index] = mark
        stack = [start]
        while stack:
            face = stack.pop()
            for edge in face.edges:
                for other in edge.link_faces:
                    if other.index not in island:
                        island[other.index] = mark
                        stack.append(other)
    planes = {}
    for face in bm.faces:
        if face.calc_area() < 0.01:
            continue
        n = face.normal
        key = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(n.dot(face.calc_center_median()), 3))
        planes.setdefault(key, []).append(face)
    overlap = {}
    for faces in planes.values():
        for i, a in enumerate(faces):
            box_a = [(min(v.co[k] for v in a.verts), max(v.co[k] for v in a.verts)) for k in range(3)]
            for b in faces[i + 1:]:
                pair = tuple(sorted((island[a.index], island[b.index])))
                if pair[0] == pair[1]:
                    continue
                box_b = [(min(v.co[k] for v in b.verts), max(v.co[k] for v in b.verts)) for k in range(3)]
                area = 1.0
                for k in range(3):
                    lo, hi = max(box_a[k][0], box_b[k][0]), min(box_a[k][1], box_b[k][1])
                    if hi < lo:
                        area = 0.0
                        break
                    area *= max(hi - lo, 1.0) if hi - lo < 1e-3 else hi - lo
                overlap[pair] = overlap.get(pair, 0.0) + area
    # Only true copies: the same footprint to 3 cm. Floor tiles overlap their neighbours a little
    # by design, and "every part that overlaps another" took the whole floor with it.
    bounds = {}
    for face in bm.faces:
        lo, hi = bounds.setdefault(island[face.index], ([1e9] * 3, [-1e9] * 3))
        for v in face.verts:
            for k in range(3):
                lo[k] = min(lo[k], v.co[k])
                hi[k] = max(hi[k], v.co[k])

    def same(a, b):
        return all(abs(bounds[a][e][k] - bounds[b][e][k]) < 0.03 for e in (0, 1) for k in range(3))

    doomed_islands = {pair[1] for pair, area in overlap.items() if area > 0.3 and same(*pair)}
    # And the crates the kit-bash sank half into the floor (-0.52..0.52 m) where another one of the
    # same size already stands on it (0.04..1.08 m): in the 0.04..0.52 m band their sides were the
    # same plane, which is the flicker on the crates' sides and at their feet.
    for pair, area in overlap.items():
        for mine, other in (pair, pair[::-1]):
            if area > 0.3 and bounds[mine][0][2] < -0.3 and bounds[other][0][2] > -0.05:
                doomed_islands.add(mine)
    return [f for f in bm.faces if island[f.index] in doomed_islands], len(doomed_islands)


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
        # The walls closing the shell's floor overhang lie in the very plane of the engine room's and
        # the corridor's end walls, facing the other way: two faces in one plane make shadows
        # flicker. The rooms' own walls are the ones to keep.
        overhang_end = abs(n.z) < 0.5 and (abs(c.x - ENGINE_X[1]) < 0.06 or abs(c.x - CORRIDOR_X[0]) < 0.06)
        if in_doorway or stray_frame or old_ceiling or sunk_terminal or overhang_end:
            doomed.append(face)
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    twins, count = duplicate_islands(bm)
    bmesh.ops.delete(bm, geom=twins, context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    log("shell: vyříznuto %d ploch (průchody, starý dveřní rám, deska ve 2 m, zapuštěný terminál), "
        "%d zdvojených dílů (%d ploch)" % (len(doomed), count, len(twins)))


# --- rooms ----------------------------------------------------------------------------------------

def strip(room, a, b, mat, size=(0.03, 0.05)):
    """A light strip from a to b: a thin glowing bar. The Star Citizen look lives on these - the
    light sits in lines along door frames, ceiling edges and floors, and the rest stays dark
    (HANDOFF point 65)."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    lo = [min(a[k], b[k]) for k in range(3)]
    hi = [max(a[k], b[k]) for k in range(3)]
    for k in range(3):
        if hi[k] - lo[k] < 1e-3:                      # the thin directions get the strip's size
            half = size[0] / 2.0 if k == 2 or (k != 2 and hi[2] - lo[2] > 1e-3) else size[1] / 2.0
            lo[k] -= half
            hi[k] += half
    room.add("Strip", box(lo, hi), mat)


def ceiling_strips(room, xs, ys, mat, skip_x_walls=False):
    """Strips along the wall-ceiling edge all round a room (the end walls' middle left for doors)."""
    z = HEIGHT - 0.035
    inset = 0.03
    for y in (ys[0] + inset, ys[1] - inset):
        strip(room, (xs[0] + 0.1, y, z), (xs[1] - 0.1, y, z), mat)
    if not skip_x_walls:
        for x in (xs[0] + inset, xs[1] - inset):
            for y0, y1 in ((ys[0] + 0.1, -DOOR_HALF - 0.1), (DOOR_HALF + 0.1, ys[1] - 0.1)):
                if y1 - y0 > 0.2:
                    strip(room, (x, y0, z), (x, y1, z), mat)


# --- services: pipes, cables, grating (HANDOFF point 70) -------------------------------------------
# The SC corridors and engine rooms carry their services in the open: pipe runs on brackets under
# the ceiling, sagging cable bundles, grating over the floor ducts. It is most of the fine detail
# the rooms lacked against the references.

def cylinder(a, b, radius, segments=12):
    """A capped cylinder from a to b (bmesh, world metres)."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    axis = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=axis.length)
    rotation = mathutils.Vector((0.0, 0.0, 1.0)).rotation_difference(axis.normalized()).to_matrix()
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0.0, 0.0, 0.0), matrix=rotation)
    bmesh.ops.translate(bm, vec=(a + b) / 2.0, verts=bm.verts)
    return bm


def pipe_run(room, a, b, radius, mats, bracket_every=1.0, hang_to=None):
    """A straight pipe with collars and brackets every metre; `hang_to` = the height of the ceiling
    the brackets hang from (none on a wall run)."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    room.add("Pipe", cylinder(a, b, radius), mats["pipe"])
    length = (b - a).length
    count = max(1, int(length / bracket_every))
    for i in range(count + 1):
        p = a + (b - a) * (i / count)
        d = (b - a).normalized() * 0.03
        room.add("PipeCollar", cylinder(p - d, p + d, radius * 1.25), mats["dark"])
        if hang_to is not None:
            room.add("PipeHanger", box((p.x - 0.015, p.y - 0.015, p.z), (p.x + 0.015, p.y + 0.015, hang_to)), mats["dark"])


def cable(room, a, b, radius, sag, mat, pieces=10):
    """A cable hanging between two points: a chain of short cylinders on a parabola."""
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    points = []
    for i in range(pieces + 1):
        t = i / pieces
        p = a.lerp(b, t)
        p.z -= sag * 4.0 * t * (1.0 - t)
        points.append(p)
    for p, q in zip(points, points[1:]):
        room.add("Cable", cylinder(p, q, radius, segments=8), mat)


def cable_bundle(room, xs, y, z, spacing, mats, sag=0.07, span=1.2):
    """Three cables side by side, clipped to the wall every `span` metres."""
    count = max(1, int((xs[1] - xs[0]) / span))
    step = (xs[1] - xs[0]) / count
    # Plain black and grey: a cable material named with "light" in it was taken for a light strip and
    # glowed orange (the import maps materials by name).
    colours = (mats["dark"], mats["pipe"], mats["dark"])
    for i in range(count):
        x0, x1 = xs[0] + i * step, xs[0] + (i + 1) * step
        for k, mat in enumerate(colours):
            dz = -k * 0.035
            cable(room, (x0, y, z + dz), (x1, y, z + dz), 0.014, sag + k * 0.01, mat)
        room.add("CableClip", box((x0 - 0.02, y - spacing, z - 0.1), (x0 + 0.02, y + spacing, z + 0.02)), mats["pipe"])


def grating(room, xs, ys, mats, bar=0.012, pitch=0.045):
    """A floor grating over a duct: a dark pit plate, a frame and cross bars on top."""
    room.add("GrateBed", box((xs[0], ys[0], 0.0), (xs[1], ys[1], 0.004)), mats["dark"])
    room.add("GrateFrame", box((xs[0], ys[0], 0.0), (xs[1], ys[0] + 0.03, 0.014)), mats["pipe"])
    room.add("GrateFrame", box((xs[0], ys[1] - 0.03, 0.0), (xs[1], ys[1], 0.014)), mats["pipe"])
    x = xs[0] + 0.03
    while x < xs[1] - 0.03:
        room.add("GrateBar", box((x - bar / 2.0, ys[0] + 0.03, 0.004), (x + bar / 2.0, ys[1] - 0.03, 0.014)), mats["pipe"])
        x += pitch


def hull(room, mat):
    """A dark closed box round the engine room, the bay and the corridor, facing in. Where two wall
    panels only meet edge to edge, the raster leaves pixel cracks; through them the planet
    sparkled (author, 23. 9. 2026, find_interior_holes.py). Behind the walls it shows dark instead,
    and it holds the player in too. The cockpit has its own canopy and stays outside it."""
    x0, x1 = ENGINE_X[0] - HULL_GAP, CORRIDOR_X[1] - 0.02
    y0, y1 = min(ENGINE_Y[0], BAY_Y[0]) - HULL_GAP, max(ENGINE_Y[1], BAY_Y[1]) + HULL_GAP
    z0, z1 = -HULL_GAP, HULL_TOP
    bm = box((x0, y0, z0), (x1, y1, z1))
    bmesh.ops.reverse_faces(bm, faces=bm.faces)       # facing in
    # Its fore end stands right behind the cockpit door: leave the doorway open there, or the hull
    # shuts the door from behind (the walk stopped 44 cm short of it, 23. 9. 2026).
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.x < -0.9], context="FACES")
    room.add("Hull", bm, mat)
    for lo, hi in (((x1, y0, z0), (x1, -DOOR_HALF, z1)), ((x1, DOOR_HALF, z0), (x1, y1, z1)),
                   ((x1, -DOOR_HALF, DOOR_HEIGHT), (x1, DOOR_HALF, z1))):
        room.add("HullEnd", polygon([(lo[0], lo[1], lo[2]), (lo[0], hi[1], lo[2]), (lo[0], hi[1], hi[2]),
                                     (lo[0], lo[1], hi[2])]), mat, face_towards=(x0, 0.0, 1.0))


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
    hull(room, room_mats["dark"])
    ceiling_strips(room, BAY_X, BAY_Y, room_mats["strip"])
    for y in (BAY_Y[0] + 0.25, BAY_Y[1] - 0.25):
        pipe_run(room, (BAY_X[0] + 0.3, y, HEIGHT - 0.2), (BAY_X[1] - 0.3, y, HEIGHT - 0.2), 0.06, room_mats, hang_to=HEIGHT)
        pipe_run(room, (BAY_X[0] + 0.3, y * 0.95, HEIGHT - 0.33), (BAY_X[1] - 0.3, y * 0.95, HEIGHT - 0.33), 0.035,
                 room_mats, bracket_every=2.0)
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
    ceiling_strips(room, CORRIDOR_X, CORRIDOR_Y, room_mats["strip"], skip_x_walls=True)
    for y in (CORRIDOR_Y[0] + 0.03, CORRIDOR_Y[1] - 0.03):             # low guide lines by the floor
        strip(room, (CORRIDOR_X[0] + 0.1, y, 0.06), (CORRIDOR_X[1] - 0.3, y, 0.06), room_mats["strip"], size=(0.02, 0.03))
    room.place(templates["terminal"], (16.0, CORRIDOR_Y[1] - 0.25, 1.35), yaw=-math.pi / 2.0)
    room.place(templates["vent"], (12.0, 0.0, HEIGHT - 0.04), roll=math.pi)
    xs = (CORRIDOR_X[0] + 0.25, CORRIDOR_X[1] - 0.35)
    for y, r in ((-0.72, 0.05), (0.72, 0.035)):
        pipe_run(room, (xs[0], y, HEIGHT - 0.18), (xs[1], y, HEIGHT - 0.18), r, room_mats, hang_to=HEIGHT)
    cable_bundle(room, xs, CORRIDOR_Y[1] - 0.06, HEIGHT - 0.32, 0.04, room_mats)
    grating(room, (CORRIDOR_X[0] + 0.4, CORRIDOR_X[1] - 0.6), (-0.3, 0.3), room_mats)
    room.accents = list(CORRIDOR_ACCENTS)
    return room


def build_engine_room(templates, room_mats):
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
    ceiling_strips(room, ENGINE_X, ENGINE_Y, room_mats["strip"])
    # Heavy feeds from the core out under the ceiling, down the side walls; cable bundles above the racks.
    for y in (-0.45, 0.45):
        pipe_run(room, (core_x + 0.55, y, HEIGHT - 0.22), (x1 - 0.4, y, HEIGHT - 0.22), 0.08, room_mats, hang_to=HEIGHT)
        pipe_run(room, (core_x - 0.55, y, HEIGHT - 0.22), (x0 + 0.3, y, HEIGHT - 0.22), 0.08, room_mats, hang_to=HEIGHT)
    for y in (y0 + 0.2, y1 - 0.2):
        pipe_run(room, (x0 + 0.4, y, HEIGHT - 0.25), (x1 - 0.4, y, HEIGHT - 0.25), 0.06, room_mats, hang_to=HEIGHT)
        pipe_run(room, (x0 + 0.5, y, 0.2), (x0 + 0.5, y, HEIGHT - 0.25), 0.06, room_mats, bracket_every=0.7)
        cable_bundle(room, (x0 + 0.6, x1 - 0.5), y - (0.08 if y > 0 else -0.08), 1.65, 0.05, room_mats, sag=0.1)
    for cx in (x0 + 0.03, x1 - 0.03):                                   # upright strips in the corners
        for cy in (y0 + 0.03, y1 - 0.03):
            strip(room, (cx, cy, 0.2), (cx, cy, HEIGHT - 0.2), room_mats["strip"], size=(0.03, 0.03))
    room.accents = list(ENGINE_ACCENTS)
    return room


def beam(p, q, width, depth):
    """A square-section beam from p to q (world metres), its depth pointing away from the canopy's
    centre line so it reads from inside."""
    p, q = mathutils.Vector(p), mathutils.Vector(q)
    axis = (q - p)
    length = axis.length
    axis.normalize()
    outward = mathutils.Vector((0.0, (p.y + q.y) / 2.0, (p.z + q.z) / 2.0 - 1.2))
    outward = (outward - axis * outward.dot(axis))
    if outward.length < 1e-4:
        outward = mathutils.Vector((0.0, 0.0, 1.0)) - axis * axis.z
    outward.normalize()
    side = axis.cross(outward).normalized()
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    frame = mathutils.Matrix((axis, side, outward)).transposed()
    for v in bm.verts:
        v.co = frame @ mathutils.Vector((v.co.x * length, v.co.y * width, v.co.z * depth)) + (p + q) / 2.0
    return bm


def polygon(points):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in points])
    return bm


def screen_quad(screens, name, centre, facing, size, mat):
    """A picture on a rectangle facing `facing` (towards the viewer), right way round and upright."""
    c = mathutils.Vector(centre)
    f = mathutils.Vector(facing).normalized()
    right = mathutils.Vector((0.0, 0.0, 1.0)).cross(f).normalized()     # the viewer's right
    up = f.cross(right).normalized()
    w, h = size
    corners = [c + right * sx * w / 2 + up * sz * h / 2 for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    screens.add(name, polygon(corners), mat, uvs=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])


def radar_disc(screens, centre, radius, mat, segments=40):
    """The radar hologram: a flat disc above the console, the picture mapped across it."""
    c = mathutils.Vector(centre)
    pts, uvs = [], []
    for i in range(segments):
        a = 2.0 * math.pi * i / segments
        pts.append(c + mathutils.Vector((math.cos(a) * radius, math.sin(a) * radius, 0.0)))
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    screens.add("HoloRadar", polygon(pts), mat, uvs=uvs)


def mfd(room, centre, facing, size, screen, dark, screens=None):
    """A display on a thin arm: a dark bezel, the glowing screen just in front, a stalk down to the
    console. `facing` is the unit vector the screen looks along."""
    c = mathutils.Vector(centre)
    f = mathutils.Vector(facing).normalized()
    side = mathutils.Vector((0.0, 0.0, 1.0)).cross(f).normalized()
    up = f.cross(side).normalized()
    w, h = size
    corners = [c + side * sx * w / 2 + up * sz * h / 2 for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bezel = bmesh.new()
    back = [bezel.verts.new(p - f * 0.03) for p in corners]
    front = [bezel.verts.new(p + side * 0 ) for p in corners]
    bezel.faces.new(front[::-1])
    bezel.faces.new(back)
    for i in range(4):
        j = (i + 1) % 4
        bezel.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bezel, faces=bezel.faces)
    room.add("MfdBezel", bezel, dark)
    inset = [c + side * sx * (w / 2 - 0.02) + up * sz * (h / 2 - 0.02) + f * 0.004
             for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    if screens is not None:
        # The picture is a hologram: its own mesh (translucent, not Nanite), a hair in front.
        screen_quad(screens, "Mfd", c + f * 0.006, f, (w - 0.04, h - 0.04), screen)
    else:
        room.add("Mfd", polygon(inset), screen)
    base = c - up * h / 2 - f * 0.015
    room.add("MfdStalk", box((base.x - 0.02, base.y - 0.02, 0.85), (base.x + 0.02, base.y + 0.02, base.z)), dark)


def console(room, lo, hi, top_tilt, body, button, white, dark, rows=3, keep_clear=()):
    """A console box whose top slopes towards -X by top_tilt metres, with rows of buttons on it.
    `keep_clear`: (x0, x1, y0, y1) areas with no buttons - where a screen lies on the top."""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    section = [(x1, z0), (x0, z0), (x0, z1 - top_tilt), (x1, z1)]
    room.add("Console", prism(section, y0, y1), body)
    for r in range(rows):
        t = (r + 0.7) / (rows + 0.4)
        x = x0 + (x1 - x0) * t
        z = z1 - top_tilt + top_tilt * t + 0.012
        count = max(2, int((y1 - y0) / 0.09))
        for i in range(count):
            y = y0 + 0.06 + i * (y1 - y0 - 0.12) / max(1, count - 1)
            if any(a <= x <= b and c <= y <= d for a, b, c, d in keep_clear):
                continue
            mat = button if (i + r) % 3 else white
            room.add("Button", box((x - 0.025, y - 0.025, z - 0.01), (x + 0.025, y + 0.025, z + 0.012)), mat)


def toggle(room, x, y, z, mats, up=True):
    """A toggle switch on a sloped top: a base plate, a guard either side, a lever."""
    room.add("ToggleBase", box((x - 0.022, y - 0.016, z), (x + 0.022, y + 0.016, z + 0.008)), mats["dark"])
    for side in (-1.0, 1.0):
        room.add("ToggleGuard", box((x - 0.018, y + side * 0.016, z), (x + 0.018, y + side * 0.02, z + 0.025)), mats["pipe"])
    tip = (x + (0.012 if up else -0.012), y, z + 0.035)
    room.add("ToggleLever", cylinder((x, y, z + 0.008), tip, 0.004, segments=6), mats["white"])


def knob(room, x, y, z, mats, r=0.018):
    room.add("Knob", cylinder((x, y, z), (x, y, z + 0.022), r, segments=10), mats["dark"])
    room.add("KnobCap", cylinder((x, y, z + 0.022), (x, y, z + 0.026), r * 0.8, segments=10), mats["pipe"])


def front_console(room, mats, keep_clear):
    """The console at the nose, in three panels with seams between them: a knee recess at the front,
    a chamfered lip with a light line, vent slots, screen brows, and the top filled with toggles,
    knobs, lit keys and indicators between the screens. Top line as before: 0.75 m at the pilot's
    edge rising to 0.95 m at the nose (the screens and the radar sit on it)."""
    dx0, dx1 = DASH_X
    top = lambda x: 0.75 + 0.2 * (x - dx0) / (dx1 - dx0)
    section = [(dx1, 0.0), (dx0 + 0.22, 0.0), (dx0 + 0.22, 0.34), (dx0 + 0.04, 0.46), (dx0, 0.5),
               (dx0, 0.71), (dx0 + 0.035, top(dx0 + 0.035)), (dx1, top(dx1))]
    panels = ((-1.1, -0.44), (-0.4, 0.4), (0.44, 1.1))
    for y0, y1 in panels:
        room.add("Console", prism(section, y0, y1), mats["dark"])
        # the lip: a trim band along the pilot's edge, and a thin light line under it
        room.add("ConsoleLip", box((dx0 - 0.012, y0 + 0.01, 0.66), (dx0 + 0.002, y1 - 0.01, 0.71)), mats["pipe"])
        room.add("ConsoleLight", box((dx0 - 0.014, y0 + 0.03, 0.645), (dx0 - 0.004, y1 - 0.03, 0.655)), mats["strip"])
        # vent slots on the front face below the lip
        y = y0 + 0.08
        while y < y1 - 0.08:
            room.add("ConsoleVent", box((dx0 - 0.006, y - 0.012, 0.53), (dx0 + 0.002, y + 0.012, 0.62)), mats["pipe"])
            y += 0.05
    # seams: dark gaps between the panels, a raised spine in the middle for the radar
    # (the console's own profile, a centimetre lower and set back, so the seam stays under the top)
    seam = [(x + 0.02, z - 0.012) for x, z in section]
    for y in (-0.42, 0.42):
        room.add("ConsoleSeam", prism(seam, y - 0.02, y + 0.02), mats["pipe"])
    room.add("RadarPlinth", cylinder((dx0 + 0.6, 0.0, top(dx0 + 0.6)), (dx0 + 0.6, 0.0, top(dx0 + 0.6) + 0.07), 0.2, segments=24),
             mats["pipe"])
    # a glowing rim only: the ring sits below the plinth's top, a hair wider, so its cap stays hidden
    room.add("RadarRing", cylinder((dx0 + 0.6, 0.0, top(dx0 + 0.6) + 0.035), (dx0 + 0.6, 0.0, top(dx0 + 0.6) + 0.05), 0.205,
                                   segments=24), mats["strip"])
    # screen brows: a thin hood over the far edge of each screen bay
    for y in SEATS_Y:
        room.add("ScreenBrow", box((dx0 + 0.47, y - 0.3, top(dx0 + 0.47)), (dx0 + 0.53, y + 0.3, top(dx0 + 0.53) + 0.06)),
                 mats["pipe"])
    # the top: rows of controls wherever the screens and the radar leave room
    def free(x, y):
        if any(a <= x <= b and c <= y <= d for a, b, c, d in keep_clear):
            return False
        return (x - (dx0 + 0.6)) ** 2 + y ** 2 > 0.26 ** 2
    for r, x in enumerate((dx0 + 0.1, dx0 + 0.22, dx0 + 0.62, dx0 + 0.78, dx0 + 0.95, dx0 + 1.1)):
        z = top(x)
        y = -1.05
        k = 0
        while y < 1.05:
            if free(x, y):
                kind = (r + k) % 5
                if kind in (0, 1):
                    toggle(room, x, y, z, mats, up=(k % 2 == 0))
                elif kind == 2:
                    knob(room, x, y, z, mats)
                elif kind == 3:
                    room.add("Key", box((x - 0.02, y - 0.02, z), (x + 0.02, y + 0.02, z + 0.012)), mats["button"])
                else:
                    room.add("Indicator", box((x - 0.008, y - 0.008, z), (x + 0.008, y + 0.008, z + 0.006)), mats["strip"])
            y += 0.075
            k += 1


def build_cockpit(templates, mats):
    """The cockpit: a deck at the back with the door, the canopy over the front, a low console at
    the nose, MFDs on arms, two seats, side consoles and an overhead panel. Returns the room and
    the canopy's glass as a room of its own (translucent: not Nanite)."""
    room = Room("Cockpit")
    glass = Room("CockpitGlass")
    screens = Room("CockpitScreens")
    x0 = COCKPIT_X[0]
    y0, y1 = COCKPIT_Y
    # The deck at the back, the door wall a little behind the frame so the leaves slide in behind it.
    floor(room, templates["floor"], (x0, CANOPY_START), COCKPIT_Y)
    ceiling(room, templates["ceiling"], (x0, CANOPY_START + 0.1), COCKPIT_Y)   # a little under the canopy's edge
    wall(room, templates["wall_dark"], (x0, y0), (CANOPY_START, y0), (0.0, 1.0))
    wall(room, templates["wall_dark"], (x0, y1), (CANOPY_START, y1), (0.0, -1.0))
    for a, b in (((x0 + 0.12, y0), (x0 + 0.12, -DOOR_HALF)), ((x0 + 0.12, DOOR_HALF), (x0 + 0.12, y1))):
        wall(room, templates["wall_dark"], a, b, (1.0, 0.0))
    ribs = [(x, [mathutils.Vector((x, y, z)) for y, z in pts]) for x, pts in CANOPY_RIBS]
    # Under the canopy: the floor follows the ribs' footprint, a tub of dark panels up to the sills.
    outline = [(x, pts[0].y) for x, pts in ribs] + [(x, pts[-1].y) for x, pts in reversed(ribs)]
    inside = (20.0, 0.0, 1.2)
    room.add("CanopyFloor", polygon([(x, y, 0.0) for x, y in outline]), mats["body"], face_towards=inside)
    for (xa, pa), (xb, pb) in zip(ribs, ribs[1:]):
        for index in (0, -1):
            a, b = pa[index], pb[index]
            room.add("Tub", polygon([(a.x, a.y, 0.0), (b.x, b.y, 0.0), (b.x, b.y, b.z), (a.x, a.y, a.z)]), mats["trim"],
                     face_towards=inside)
    nose = ribs[-1][1]
    room.add("Tub", polygon([(nose[0].x, nose[0].y, 0.0), (nose[0].x, nose[0].y, nose[0].z),
                             (nose[-1].x, nose[-1].y, nose[-1].z), (nose[-1].x, nose[-1].y, 0.0)]), mats["trim"],
             face_towards=inside)
    # Where the canopy meets the deck's ceiling: close the gap above 2.4 m at the first rib.
    first = ribs[0][1]
    room.add("CanopyHeader", polygon([(CANOPY_START, first[1].y, HEIGHT)] + [(p.x, p.y, p.z) for p in first[1:-1]]
                                     + [(CANOPY_START, first[-2].y, HEIGHT)]), mats["trim"], face_towards=inside)
    # The canopy: beams along and between the ribs, glass in between. The nose rib's glass closes
    # the front.
    width, depth = BEAM
    for x, pts in ribs:
        for a, b in zip(pts, pts[1:]):
            room.add("Beam", beam(a, b, width, depth), mats["frame"])
    for (xa, pa), (xb, pb) in zip(ribs, ribs[1:]):
        for i in range(len(pa)):
            room.add("Beam", beam(pa[i], pb[i], width * 0.8, depth), mats["frame"])
        for i in range(len(pa) - 1):
            glass.add("Glass", polygon([pa[i], pa[i + 1], pb[i + 1], pb[i]]), mats["glass"])
    glass.add("Glass", polygon(nose), mats["glass"])
    # The low console at the nose, following the taper, with a screen for each pilot.
    dx0, dx1 = DASH_X
    clear = [(dx0 + 0.1, dx0 + 0.5, y - 0.3, y + 0.3) for y in SEATS_Y]
    front_console(room, mats, clear)
    # The console's two screens, tipped back towards the pilots (the console top rises 0.2 m over 1.2 m).
    tilt = math.atan2(0.2, dx1 - dx0)
    face_up = mathutils.Vector((-math.sin(tilt), 0.0, math.cos(tilt)))
    for y, page in zip(SEATS_Y, ("DashLeft", "DashRight")):
        centre = mathutils.Vector((dx0 + 0.3, y, 0.75 + 0.2 * 0.3 / (dx1 - dx0) + 0.012))
        # Facing up the slope, "up" on the picture pointing forward: seen from the seat it reads upright.
        f = face_up
        fwd = mathutils.Vector((math.cos(tilt), 0.0, math.sin(tilt)))
        side = fwd.cross(f).normalized()            # the pilot's right, looking forward and down
        w, h = 0.5, 0.3
        corners = [centre + side * sx * w / 2 + fwd * sz * h / 2 for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        screens.add("DashScreen", polygon(corners), mats["holo"][page], uvs=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    radar_disc(screens, ((dx0 + dx1) / 2.0, 0.0, 1.08), 0.26, mats["holo"]["Radar"])
    # Two MFDs per pilot on arms, out to the sides and a little low so the view ahead stays open
    # (in the reference they sit at the edges of the view), turned towards the pilot's eyes.
    # Which page each MFD shows: left seat Status | Power, right seat Comms | Scan (as seen sitting).
    pages = {(SEATS_Y[0], 1.0): "Status", (SEATS_Y[0], -1.0): "Power", (SEATS_Y[1], 1.0): "Comms", (SEATS_Y[1], -1.0): "Scan"}
    for y in SEATS_Y:
        for side in (-1.0, 1.0):
            centre = mathutils.Vector((SEAT_X + 0.7, y + side * 0.62, 1.02))
            eye = mathutils.Vector((SEAT_X - 0.1, y, 1.25))
            mfd(room, centre, tuple(eye - centre), (0.3, 0.21), mats["holo"][pages[(y, side)]], mats["dark"], screens)
    # Side consoles and seats are Meshy props now (MESHY_PROPS); an overhead panel between the seats.
    over = box((SEAT_X - 0.1, -0.55, 2.42), (SEAT_X + 0.9, 0.55, 2.6), bevel=0.02)
    room.add("Overhead", over, mats["dark"])
    for i in range(5):
        for j in range(4):
            x = SEAT_X + 0.08 + i * 0.18
            y = -0.4 + j * 0.27
            room.add("OverheadButton", box((x - 0.03, y - 0.04, 2.40), (x + 0.03, y + 0.04, 2.42)),
                     mats["button"] if (i + j) % 2 else mats["white"])
    lamps(room, templates["lamp"], COCKPIT_LAMPS)
    room.screens = list(COCKPIT_SCREENS)
    return room, glass, screens


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
        "white": material("M_White", colour=(0.8, 0.8, 0.8)),
        "black": material("M_Black_Seat", colour=(0.02, 0.02, 0.02)),
        "strip": material("M_Strip", emission=(1.0, 0.82, 0.6)),
    }
    mats = dict(own, body=shell_materials["MI_Trim_02"], dark=shell_materials["M_Black"],
                cushion=shell_materials["MI_PaddedWall"], trim=shell_materials["MI_Trim_01"],
                frame=shell_materials["M_Black"], pipe=shell_materials["MI_Trim_02"])      # the reference's canopy beams are near black

    mats["holo"] = {page: material("M_Holo_" + page, emission=(0.3, 0.6, 1.0))
                    for page in ("Power", "Status", "Comms", "Scan", "DashLeft", "DashRight", "Radar")}
    own.update({"holo_" + k: v for k, v in mats["holo"].items()})
    cockpit, canopy_glass, cockpit_screens = build_cockpit(templates, mats)
    rooms = [build_engine_room(templates, mats), build_bay(shell, templates, mats), build_corridor(templates, mats),
             cockpit, canopy_glass, cockpit_screens]
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
        "props": [dict(p, at=list(p["at"])) for p in MESHY_PROPS],
        "decals": [dict(d, at=list(d["at"]), normal=list(d["normal"])) for d in DECALS],
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
