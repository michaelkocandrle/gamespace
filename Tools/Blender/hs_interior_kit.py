"""Quaternius Modular Sci-Fi MegaKit pieces (CC0) as the structural layer of a ship interior, the way the SC
reference builds its spaces (starcitizenreference/Screenshot 2026-09-25 02*.png; table in the ship-pipeline
skill): a broken, chamfered profile instead of a box room, portals on every module, a cable tray and pipes
under the ceiling, panels with depth and overlaps. Precise technical detail and the layout's objects stay
procedural (hs_interior.py), markings are decals (Docs/AssetPipeline_Modular.md).

Used by hs_interior.py for the rooms listed in recipe interior.kit.rooms. The kit zip is read directly
(ArtSource/ThirdParty/Quaternius/ModularSciFiMegaKit.zip, not in git - README there).

Kit geometry: a 4 m grid, a wall piece stands on the cell's x = -2 line facing +x, its length along y,
wall 0..3 m, the upper (Top*) pieces 3..5 m. Here one module is 4 kit metres long, scaled to fit the room
length exactly; the height is scaled so that the wall plus the top piece, tilted inwards by chamfer_deg,
ends a cove below the ceiling. The top piece's tilt is the SC-like chamfer; the cove over it holds a
light strip (indirect light, no flat white ceiling).

Pieces keep their UVs and are sorted by material into objects SM_Ship_<Ship>_IntKit_<key>: hs_assemble_ship
joins them into the part "InteriorKit" (no unwrap - the trim sheet UVs are the look). Material keys:
kit_trim01, kit_trim02, kit_trim02b, kit_trim03, kit_cables, kit_padded, kit_padded_grey (textures from
Tools/Assets/tone_kit_textures.py on M_Ship_PBR), int_dark, int_light. The kit's own decals are dropped
(markings are ours).
"""
import math
import os
import tempfile
import zipfile

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ZIP = os.path.join(ROOT, "ArtSource", "ThirdParty", "Quaternius", "ModularSciFiMegaKit.zip")
GLTF = "Modular SciFi MegaKit[Standard]/glTF/"
KIT_DIRS = ("Walls", "Platforms", "Props", "Columns")

# kit material (name without Blender's .001) -> our key; the longest prefix wins, None drops the faces
MATERIALS = [
    ("MI_Trim_01", "kit_trim01"), ("MI_Trim_02_Floor", "kit_trim02b"), ("MI_Trim_02_Variation", "kit_trim02b"),
    ("MI_Trim_02", "kit_trim02"), ("MI_Trim_03_Cables", "kit_cables"), ("MI_Trim_03_Dark", "kit_cables"),
    ("MI_Trim_03", "kit_trim03"), ("MI_PaddedWall", "kit_padded"), ("M_Black", "int_dark"), ("M_Light", "int_light"),
    ("M_Glass", "int_dark"), ("MI_Decal", None), ("M_Decal", None), ("M_LightFade", None),
]
PREVIEW = {"kit_trim01": "Trim01", "kit_trim02": "Trim02", "kit_trim02b": "Trim02B", "kit_trim03": "Trim03",
           "kit_cables": "Cables", "kit_padded": "Padded", "kit_padded_grey": "PaddedGrey"}


def _key(material_name):
    base = material_name.split(".")[0]
    best = None
    for prefix, key in MATERIALS:
        if base.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
            best = (prefix, key)
    return best[1] if best else "kit_trim02"


class Kit:
    """Loads kit pieces once and stamps them into per-material bmeshes."""

    def __init__(self):
        self.zip = zipfile.ZipFile(ZIP)
        self.names = {os.path.splitext(os.path.basename(n))[0]: n for n in self.zip.namelist()
                      if n.endswith(".gltf") and n.split("/")[-2] in KIT_DIRS}
        self.dir = tempfile.mkdtemp(prefix="hs_kit_")
        self.templates = {}
        self.bm = {}
        self.used = {}

    def _load(self, name):
        src = self.names[name]
        for ext in (".gltf", ".bin"):
            member = src[:-5] + ext
            with open(os.path.join(self.dir, os.path.basename(member)), "wb") as fh:
                fh.write(self.zip.read(member))
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(self.dir, name + ".gltf"))
        new = [o for o in bpy.data.objects if o not in before]
        bpy.context.view_layer.update()
        parts = {}
        for o in new:
            if o.type != "MESH":
                continue
            for index, slot in enumerate(o.material_slots):
                key = _key(slot.material.name) if slot.material else "kit_trim02"
                if key is None:
                    continue
                bm = bmesh.new()
                bm.from_mesh(o.data)
                bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != index], context="FACES")
                if not bm.faces:
                    bm.free()
                    continue
                bmesh.ops.transform(bm, matrix=o.matrix_world, verts=bm.verts)
                for f in bm.faces:
                    f.material_index = 0
                me = parts.get(key)
                if me is not None:
                    bm.from_mesh(me)
                    me.clear_geometry()
                else:
                    me = parts[key] = bpy.data.meshes.new("kit_%s_%s" % (name, key))
                bm.to_mesh(me)
                bm.free()
        for o in new:
            bpy.data.objects.remove(o)
        self.templates[name] = parts
        return parts

    def place(self, name, m):
        """Stamp a kit piece with the 4x4 matrix m (kit metres -> layout metres)."""
        parts = self.templates.get(name) or self._load(name)
        flip = m.determinant() < 0
        for key, me in parts.items():
            bm = self.bm.get(key)
            if bm is None:
                bm = self.bm[key] = bmesh.new()
            nv, nf = len(bm.verts), len(bm.faces)
            bm.from_mesh(me)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            bmesh.ops.transform(bm, matrix=m, verts=bm.verts[nv:])
            if flip:
                bmesh.ops.reverse_faces(bm, faces=bm.faces[nf:])
        self.used[name] = self.used.get(name, 0) + 1

    def objects(self, ship, coll, mats):
        out = []
        for key, bm in self.bm.items():
            if not bm.faces:
                continue
            me = bpy.data.meshes.new("SM_Ship_%s_IntKit_%s" % (ship, key))
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(me.name, me)
            coll.objects.link(ob)
            me.materials.append(mats[key])
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(30))
            out.append(ob)
        for parts in self.templates.values():
            for me in parts.values():
                bpy.data.meshes.remove(me)
        return out


def preview_materials(mats):
    """Blender-side preview only (Eevee renders while iterating): the toned trim textures on the kit keys.
    Unreal takes the material by its slot name."""
    folder = os.path.join(ROOT, "ArtSource", "Ships", "Shared", "Kit")
    for key, tex in PREVIEW.items():
        m = mats.get(key)
        path = os.path.join(folder, "T_Kit_%s_BC.png" % tex)
        if m is None or not os.path.isfile(path):
            continue
        nt = m.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
        orm = nt.nodes.new("ShaderNodeTexImage")
        orm.image = bpy.data.images.load(os.path.join(folder, "T_Kit_%s_ORM.png" % tex), check_existing=True)
        orm.image.colorspace_settings.name = "Non-Color"
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
        nrm = nt.nodes.new("ShaderNodeTexImage")
        nrm.image = bpy.data.images.load(os.path.join(folder, "T_Kit_%s_N.png" % tex), check_existing=True)
        nrm.image.colorspace_settings.name = "Non-Color"
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])


# ------------------------------------------------------------------------------------------ the shell

def _piece_matrix(xc, side, W, s, length, z0):
    """A wall-type piece of one module: kit x=-2 line on the wall line y = side * W, length along ship x."""
    yaw = -90.0 if side > 0 else 90.0
    return (Matrix.Translation((xc, side * (W - 2 * s), z0)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
            @ Matrix.Diagonal((s, length / 4.0, s, 1.0)))


def _tilt(side, W, z, deg):
    p = Vector((0.0, side * W, z))
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg) * (1 if side > 0 else -1), 4, "X") @ Matrix.Translation(-p)


def shell(kit, g, box, obox, room, spec, H, W, lights_out, doors_x=(), hull_top=None):
    """One room's structure along x from room x0 to x1 between the walls at y = +-W: floor plates, walls,
    chamfered top pieces with a light cove, a ceiling with a services run, portals on the module lines.
    g/box/obox are hs_interior's procedural helpers (portals and coves are exact geometry, not kit)."""
    x0, x1 = room["rect"][0], room["rect"][1]
    z0 = room.get("floor_z", 0.0)
    kc = spec["kit"]
    a = kc.get("chamfer_deg", 35.0)
    cove = kc.get("cove_m", 0.12)
    s = (H - z0 - cove) / (3.0 + 2.0 * math.cos(math.radians(a)))
    n = max(1, int(round((x1 - x0) / (4.0 * s))))
    length = (x1 - x0) / n
    inset = 2.0 * s * math.sin(math.radians(a))       # how far the chamfer's top edge comes in
    zc = z0 + 3.0 * s + 2.0 * s * math.cos(math.radians(a))
    Wc = W - inset                                     # ceiling half width
    walls = kc["walls"].get(room["id"], kc["walls"]["default"])
    info = {"modules": n, "scale": round(s, 3), "module_m": round(length, 3), "ceiling_half_width": round(Wc, 3)}
    # a closed dark backing behind the kit: a hull seen from inside is culled, so every gap between pieces
    # showed the sky (first build, 25. 9. 2026)
    for side in (1, -1):
        ya, yb = sorted((side * (W + 0.01), side * (W + 0.04)))
        box(g["int_dark"], (x0, ya, z0 - 0.05), (x1, yb, H + 0.06))
    box(g["int_dark"], (x0, -W - 0.04, H + 0.02), (x1, W + 0.04, H + 0.06))
    for i in range(n):
        xc = x0 + (i + 0.5) * length
        for side, pattern in ((1, walls["port"]), (-1, walls["starboard"])):
            wall, top = pattern[i % len(pattern)]
            m = _piece_matrix(xc, side, W, s, length, z0)
            kit.place(wall, m)
            kit.place(top, _tilt(side, W, z0 + 3.0 * s, a) @ m)
            # the cove over the chamfer: a dark lip and an emissive strip facing the ceiling (indirect light)
            # (a shelf on the chamfer's top edge, a lip on its inner edge hides the strip from below)
            edge = side * (Wc - 0.22 * s)
            ya, yb = sorted((edge, side * W))
            box(g["int_dark"], (xc - length / 2, ya, zc - 0.03), (xc + length / 2, yb, zc))
            la, lb = sorted((edge, edge + side * 0.025))
            box(g["int_trim"], (xc - length / 2, la, zc - 0.05), (xc + length / 2, lb, zc + 0.05))
            sa, sb = sorted((edge + side * 0.05, edge + side * 0.09))
            box(g["int_light"], (xc - length / 2 + 0.08, sa, zc), (xc + length / 2 - 0.08, sb, zc + 0.012))
            # the cove's light: washes the ceiling and the opposite wall (the strip alone is too small for Lumen)
            lights_out.append({"at": [xc, side * (Wc - 0.05), zc - 0.08], "cd": kc.get("cove_cd", 12.0), "type": "point"})
        # floor: plates across the width, the middle row a darker walkway plate
        ny = max(1, int(round(2 * W / (4.0 * s))))
        for j in range(ny):
            yc = -W + (j + 0.5) * 2 * W / ny
            kit.place(kc["floor"][j % len(kc["floor"])], Matrix.Translation((xc, yc, z0)) @ Matrix.Diagonal((length / 4.0, 2 * W / ny / 4.0, 1.0, 1.0)))
        # ceiling panel between the coves, facing down
        # (the hull comes down towards the ramp: the ceiling plate of a module stays under it)
        hz = H
        if hull_top is not None:
            # (across its width too: the hull's roof curves down to the sides)
            hz = min([H] + [hull_top(x0 + (i + t / 6.0) * length, yy) - 0.07 for t in range(7) for yy in (-Wc, 0.0, Wc)])
        # (1 cm short of the module lines - the portals cover the joint; at the ramp the plate's edge sat on
        # the closed ramp's top face)
        kit.place(kc["ceiling"], Matrix.Translation((xc, 0.0, hz)) @ Matrix.Diagonal(((length - 0.02) / 4.0, 2 * Wc / 4.0, -1.0, 1.0)))
        # a down light in a housing in the middle of every module: pools of light on the floor, dark between
        # (a recessed square fitting: dark housing, a lens flush with its face; the kit's lamps are wall lamps)
        box(g["int_dark"], (xc - 0.2, -0.2, H - 0.05), (xc + 0.2, 0.2, H - 0.005))
        box(g["int_trim"], (xc - 0.17, -0.17, H - 0.058), (xc + 0.17, 0.17, H - 0.05))
        box(g["int_light"], (xc - 0.13, -0.13, H - 0.062), (xc + 0.13, 0.13, H - 0.058))
        lights_out.append({"at": [xc, 0.0, H - 0.12], "type": "spot", "cone_deg": kc.get("spot_cone_deg", 80.0),
                           "cd": kc.get("spot_cd", 60.0), "direction": [0.0, 0.0, -1.0]})
    # portals on the module lines (and the room ends): a frame around the whole profile, proud of the panels
    pw, pd = kc.get("portal_w", 0.14), kc.get("portal_d", 0.07)
    for i in range(n + 1):
        x = x0 + i * length
        if any(abs(x - dx) < 0.05 for dx in doors_x) and 0 < i < n:
            continue
        xa, xb = x - pw / 2, x + pw / 2
        for side in (1, -1):
            # on the wall: from the wall line to in front of the deepest panel (WallAstra stands 0.44 kit m proud)
            face = side * (W - kc.get("wall_proud_m", 0.02))
            ya, yb = sorted((side * W, face - side * pd))
            box(g["int_trim"], (xa, ya, z0), (xb, yb, z0 + 3.0 * s))
            # along the chamfer (top pieces stand 0.22 kit m proud of their line)
            pivot = Vector((x, side * W, z0 + 3.0 * s))
            d = Vector((0, -side * math.sin(math.radians(a)), math.cos(math.radians(a))))
            nrm = Vector((0, -side * math.cos(math.radians(a)), -math.sin(math.radians(a))))
            obox(g["int_trim"], pivot + d * s + nrm * (0.22 * s + pd / 2), d, nrm, (2.0 * s + 0.04, pw, pd))
            # a small orange tag at eye height on the portal's face (the section number goes next to it)
            fa, fb = sorted((face - side * pd, face - side * (pd + 0.005)))
            box(g["accent"], (xa + 0.02, fa, z0 + 1.2), (xb - 0.02, fb, z0 + 1.28))   # on the wall portal, under the chamfer
        box(g["int_trim"], (xa, -Wc, H - pd - 0.03), (xb, Wc, H - 0.005))
    # floor guide lights along both walls (cool, like the reference's orientation strips)
    for side in (1, -1):
        ya, yb = sorted((side * (W - 0.03), side * (W - 0.05)))
        box(g["int_dark"], (x0 + 0.1, ya - 0.01 * side, z0), (x1 - 0.1, yb, z0 + 0.1))
        ya, yb = sorted((side * (W - 0.05), side * (W - 0.052)))
        box(g["int_glow"], (x0 + 0.15, ya, z0 + 0.04), (x1 - 0.15, yb, z0 + 0.06))
    # services along the port side of the ceiling: three pipes and their clamps (colour-coded bands)
    ys = [Wc - 0.1, Wc - 0.19, Wc - 0.27]
    rs = [0.035, 0.028, 0.022]
    for y, r in zip(ys, rs):
        g_pipe = g["int_trim"]
        _pipe(g_pipe, (x0, y, H - 0.09 - r), (x1, y, H - 0.09 - r), r)
    k = 0
    x = x0 + 0.3
    while x < x1 - 0.1:
        box(g["int_dark"], (x - 0.02, ys[-1] - 0.05, H - 0.2), (x + 0.02, ys[0] + 0.05, H + 0.005))   # hung from the ceiling
        if k % 3 == 1:
            for y, r, key in zip(ys, rs, ("accent", "int_glow", "int_dark")):
                _pipe(g[key], (x + 0.08, y, H - 0.09 - r), (x + 0.16, y, H - 0.09 - r), r + 0.004)
        k += 1
        x += 0.6
    return info


def _pipe(bm, a, b, r, seg=12):
    a, b = Vector(a), Vector(b)
    d = b - a
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length)
    m = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m.translation = (a + b) / 2
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])


def fittings(kit, g, box, spec, lights_out):
    """Equipment with a purpose at the functional spots (recipe interior.kit.fittings), clustered like the
    reference: a fire extinguisher by the door, a handrail along the aisle, floor-level air vents.
      {"type": "extinguisher", "at": [x, y_wall]}             bracket, red bottle, the label is a decal
      {"type": "handrail", "x": [x0, x1], "y": y_wall, "z": 1.0}  tube on stand-offs every 0.9 m
      {"type": "vent", "x": [..], "y": y_wall, "z": 0.22}        kit grille facing the room"""
    for f in spec["kit"].get("fittings", []):
        t = f["type"]
        if t == "extinguisher":
            x, yw = f["at"]
            side = 1 if yw > 0 else -1
            yc = yw - side * 0.1
            _pipe(g["int_red"], (x, yc, 0.55), (x, yc, 0.98), 0.065, 16)
            _pipe(g["int_dark"], (x, yc, 0.98), (x, yc, 1.05), 0.03, 12)
            box(g["int_dark"], (x - 0.03, yc - 0.01, 1.03), (x + 0.1, yc + 0.01, 1.05))          # lever
            _pipe(g["int_dark"], (x + 0.05, yc, 1.0), (x + 0.1, yc, 0.7), 0.01, 8)            # hose
            ya, yb = sorted((yw, yc + side * 0.02))
            for z in (0.62, 0.9):
                box(g["int_trim"], (x - 0.08, ya, z), (x + 0.08, yb, z + 0.03))               # bracket bands
            ya, yb = sorted((yw, yw - side * 0.02))
            box(g["int_trim"], (x - 0.1, ya, 0.5), (x + 0.1, yb, 1.1))
        elif t == "handrail":
            x0, x1 = f["x"]
            yw, z = f["y"], f.get("z", 1.0)
            side = 1 if yw > 0 else -1
            yr = yw - side * 0.07
            _pipe(g["int_trim"], (x0, yr, z), (x1, yr, z), 0.018, 12)
            n = max(1, int(round((x1 - x0) / 0.9)))
            for k in range(n + 1):
                x = x0 + (x1 - x0) * k / n
                _pipe(g["int_dark"], (x, yw, z), (x, yr, z), 0.012, 8)
                ya, yb = sorted((yw, yw - side * 0.01))
                box(g["int_dark"], (x - 0.03, ya, z - 0.04), (x + 0.03, yb, z + 0.04))
        elif t == "junction":
            # a service box with latches and status lights (power / data distribution at the functional spots)
            x, yw = f["at"]
            side = 1 if yw > 0 else -1
            z = f.get("z", 1.2)
            w, h, dep = (0.24, 0.3, 0.1) if f.get("small") else (0.36, 0.46, 0.13)
            ya, yb = sorted((yw, yw - side * dep))
            box(g["int_trim"], (x - w / 2, ya, z - h / 2), (x + w / 2, yb, z + h / 2))
            fa, fb = sorted((yw - side * dep, yw - side * (dep + 0.008)))
            box(g["int_dark"], (x - w / 2 + 0.02, fa, z - h / 2 + 0.02), (x + w / 2 - 0.02, fb, z + h / 2 - 0.06))  # door
            for lx in (x - w / 2 + 0.035, x + w / 2 - 0.055):                                                        # latches
                la, lb = sorted((yw - side * (dep + 0.008), yw - side * (dep + 0.022)))
                box(g["int_trim"], (lx, la, z - 0.03), (lx + 0.02, lb, z + 0.03))
            for k, key in enumerate(("int_glow", "int_glow", "accent")):                                              # status lights
                la, lb = sorted((yw - side * dep, yw - side * (dep + 0.006)))
                box(g[key], (x - w / 2 + 0.03 + k * 0.035, la, z + h / 2 - 0.045), (x - w / 2 + 0.05 + k * 0.035, lb, z + h / 2 - 0.03))
            _pipe(g["int_dark"], (x + w / 4, yw - side * dep / 2, z + h / 2), (x + w / 4, yw - side * dep / 2, 1.42), 0.018, 8)
        elif t == "conduit":
            # vertical cable conduits beside the portals, floor to the chamfer line
            yw = f["y"]
            side = 1 if yw > 0 else -1
            for x in f["x"]:
                for k, r in enumerate((0.022, 0.016)):
                    xx = x + 0.12 + k * 0.055
                    yy = yw - side * (0.03 + r)
                    _pipe(g["int_dark" if k else "int_trim"], (xx, yy, 0.1), (xx, yy, 1.4), r, 10)
                for z in (0.35, 0.8, 1.25):
                    ya, yb = sorted((yw, yw - side * 0.075))
                    box(g["int_trim"], (x + 0.09, ya, z), (x + 0.21, yb, z + 0.025))
        elif t == "vent":
            yw, z = f["y"], f.get("z", 0.22)
            side = 1 if yw > 0 else -1
            for x in f["x"]:
                # Prop_Vent_Small lies in the kit's XY plane facing +Z: stand it up facing the room
                m = (Matrix.Translation((x, yw, z)) @ Matrix.Rotation(math.radians(90 * side), 4, "X")
                     @ Matrix.Diagonal((0.45, 0.45, 0.45, 1.0)))
                kit.place("Prop_Vent_Small", m)



def clad_bulkhead(kit, x, facing, y0, y1, door, s, z0, H):
    """Kit panels on a cross wall's face at x (facing -1: the face looks aft, +1: forward): a wall band up to
    the chamfer line, flat plates above it, a plate over the doorway. door: (y centre, width) or None."""
    yaw = 180.0 if facing < 0 else 0.0
    # the kit's wall line (x = -2 kit m) lands on the face: after the turn it sits at +2s (aft) or -2s (forward)
    tx = x - 2.0 * s if facing < 0 else x + 2.0 * s
    frame = 0.08
    spans = [(y0, y1)]
    if door:
        a, b = door[0] - door[1] / 2 - frame, door[0] + door[1] / 2 + frame
        spans = [(p, q) for p, q in ((y0, a), (b, y1)) if q - p > 0.05]
    zc = z0 + 3.0 * s

    def piece(name, ya, yb, zb, zt, height_kit):
        kit.place(name, Matrix.Translation((tx, (ya + yb) / 2, zb)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
                  @ Matrix.Diagonal((s, (yb - ya) / 4.0, (zt - zb) / height_kit, 1.0)))

    for ya, yb in spans:
        piece("WallBand_Straight", ya, yb, z0, zc, 3.0)
        piece("ShortWall_MetalPlates_Straight", ya, yb, zc, H, 1.0)
    if door:
        piece("ShortWall_MetalPlates_Straight", door[0] - door[1] / 2 - frame, door[0] + door[1] / 2 + frame, z0 + 2.15, H, 1.0)


def _uv_layer(bm):
    return bm.loops.layers.uv.get("UVMap") or bm.loops.layers.uv.new("UVMap")


def project_uv(bm, faces, tile_m):
    """Cube-projected UVs, one texture tile per tile_m metres (procedural parts in a kit material)."""
    uv = _uv_layer(bm)
    for f in faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for loop in f.loops:
            co = loop.vert.co
            loop[uv].uv = (co[a] / tile_m, co[b] / tile_m)


def kit_box(kit, key, lo, hi, tile_m=0.6):
    """A box in a kit material (the InteriorKit part keeps these UVs)."""
    bm = kit.bm.get(key)
    if bm is None:
        bm = kit.bm[key] = bmesh.new()
    _uv_layer(bm)
    lo, hi = Vector(lo), Vector(hi)
    nf = len(bm.faces)
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=hi - lo, verts=res["verts"])
    bmesh.ops.translate(bm, vec=(lo + hi) / 2, verts=res["verts"])
    bm.faces.ensure_lookup_table()
    faces = bm.faces[nf:]
    for f in faces:
        f.normal_update()
    project_uv(bm, faces, tile_m)


def kit_obox(kit, key, c, x, z, size, tile_m=0.6):
    """An oriented box (hs_interior.obox) in a kit material."""
    bm = kit.bm.get(key)
    if bm is None:
        bm = kit.bm[key] = bmesh.new()
    _uv_layer(bm)
    x = Vector(x).normalized()
    z = (Vector(z) - x * x.dot(Vector(z))).normalized()
    y = z.cross(x)
    nf = len(bm.faces)
    res = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=size, verts=res["verts"])
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(c)
    bmesh.ops.transform(bm, matrix=m, verts=res["verts"])
    bm.faces.ensure_lookup_table()
    faces = bm.faces[nf:]
    for f in faces:
        f.normal_update()
    project_uv(bm, faces, tile_m)
