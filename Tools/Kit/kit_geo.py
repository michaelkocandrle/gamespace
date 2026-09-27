"""Geometry toolkit for the interior kit's parametric parts (step 4 of the kit brief, 26. 9. 2026).

A Part collects geometry per material role (the slot names of kit_rules.json naming.slot_roles), then becomes
one Blender object with those slots, UV0 (trim-sheet strips for Kit_Trim, metres box-projected elsewhere),
UV1 = a per-panel random pair (the layered master's panel variation), the face-corner colour 'Col' the layered
master reads (R occlusion, falling towards the floor; G 1 - edge: 0 on the faces a bevel made, so the edge wear sits
on the chamfers only - these parts have almost no vertex off an edge, a per-vertex edge mask would wear whole faces;
B 1 primary / 0 secondary; A layering amount 1), UCX collision objects and
SOCKET_ empties. All coordinates in metres in the part's own frame (kit_rules pivots).
"""
import json
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULES = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "kit_rules.json"), encoding="utf-8"))
TRIM = json.load(open(os.path.join(ROOT, "ArtSource", "Kit", "Textures", "trim_index.json"), encoding="utf-8"))

ROLES = ["Kit_Primary", "Kit_Structure", "Kit_Accent", "Kit_Signal", "Kit_Rubber", "Kit_Fabric", "Kit_Plastic", "Kit_Trim",
         "Kit_Seal", "Kit_GlowWarm", "Kit_GlowCool", "Kit_GlowSignal", "Kit_Screen", "Kit_Glass"]


def frame(origin, ax, ay, az):
    """4x4 matrix of a local frame: local x -> ax, y -> ay, z -> az (world vectors), at origin."""
    ax, ay, az = Vector(ax).normalized(), Vector(ay).normalized(), Vector(az).normalized()
    m = Matrix((ax, ay, az)).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


class Part:
    def __init__(self, name, seed=1):
        self.name = name
        self.bm = {r: bmesh.new() for r in ROLES}
        for b in self.bm.values():
            # before any vertex: a new custom-data layer invalidates the Python references to existing verts
            b.verts.layers.float_vector.new("local")
        self.meta = {r: [] for r in ROLES}      # per face batch: (faces, uv mode, panel id)
        self.rng = random.Random(seed)
        self.ucx = []                            # convex point sets
        self.sockets = []                        # (name, location, x axis, z axis, params)
        self.decal_items = []                    # shots for hs_decals.Placer
        self.edge_faces = set()                  # faces a bevel made: the edge-wear mask (Col.G = 0)

    # ------------------------------------------------------------------ primitives
    def box(self, role, lo, hi, bevel=0.0, segments=2, m=None, trim=None, panel=True, secondary=False, atlas=None, inset=None):
        """An axis-aligned box lo..hi in local coords (then m), bevelled edges. trim: strip name on Kit_Trim; the
        strip runs along the box's longest axis. Returns the new faces."""
        bm = self.bm[role]
        lo, hi = Vector(lo), Vector(hi)
        size = hi - lo
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0)
        for v in tmp.verts:
            v.co = Vector((lo.x + (v.co.x + 0.5) * size.x, lo.y + (v.co.y + 0.5) * size.y, lo.z + (v.co.z + 0.5) * size.z))
        if inset:
            # a pressed panel: the front face (+z) inset by a border and pushed back - one mesh, no butt joints
            border, depth = inset
            tmp.faces.ensure_lookup_table()
            front = max(tmp.faces, key=lambda f: f.calc_center_median().z)
            bmesh.ops.inset_region(tmp, faces=[front], thickness=border, depth=-depth, use_even_offset=True)
        edge = set()
        if bevel > 0:
            w = min(bevel, 0.45 * min(size), (inset[0] * 0.4) if inset else 1.0)
            res = bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=w, offset_type="OFFSET", segments=segments, profile=0.5,
                                  affect="EDGES", clamp_overlap=True)
            edge = set(res["faces"])
        local = [(v.co.copy()) for v in tmp.verts]
        if m is not None:
            tmp.transform(m)
        faces = self._merge(bm, tmp, local, edge)
        mode = ("trim", trim, lo, hi) if trim else ("atlas", atlas, lo, hi) if atlas else ("box",)
        self.meta[role].append((faces, mode, self._panel_id(panel), secondary))
        return faces

    def slab(self, role, m, u0, u1, v0, v1, thick, bevel=0.0, segments=2, trim=None, panel=True, secondary=False, proud=0.0,
             atlas=None, inset=None):
        """A plate in the frame m: u (local x) and v (local y) extents, front face at local z = proud, thickness
        behind it. atlas: (u0, v0, u1, v1) region of a texture the front face maps to (screens)."""
        return self.box(role, (u0, v0, proud - thick), (u1, v1, proud), bevel, segments, m, trim, panel, secondary, atlas, inset)

    def tube(self, role, a, b, r, seg=16, caps=True, panel=False):
        bm = self.bm[role]
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        if L < 1e-6:
            return []
        tmp = bmesh.new()
        bmesh.ops.create_cone(tmp, cap_ends=caps, cap_tris=False, segments=seg, radius1=r, radius2=r, depth=L)
        local = [v.co.copy() for v in tmp.verts]
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        tmp.transform(Matrix.Translation((a + b) / 2) @ q.to_matrix().to_4x4())
        faces = self._merge(bm, tmp, local)
        for f in faces:
            f.smooth = True
        self.meta[role].append((faces, ("box",), self._panel_id(panel), False))
        return faces

    def poly_prism(self, role, pts2d, m, depth, bevel=0.0, panel=True, segments=2):
        """A prism from a 2D polygon (local x, y) extruded along local -z by depth, front at z = 0, then m."""
        bm = self.bm[role]
        tmp = bmesh.new()
        front = [tmp.verts.new((x, y, 0.0)) for x, y in pts2d]
        back = [tmp.verts.new((x, y, -depth)) for x, y in pts2d]
        tmp.faces.new(front)
        tmp.faces.new(list(reversed(back)))
        n = len(pts2d)
        for i in range(n):
            j = (i + 1) % n
            tmp.faces.new((front[j], front[i], back[i], back[j]))
        bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces)
        edge = set()
        if bevel > 0:
            res = bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=bevel, offset_type="OFFSET", segments=segments, profile=0.5,
                                  affect="EDGES", clamp_overlap=True)
            edge = set(res["faces"])
        local = [v.co.copy() for v in tmp.verts]
        tmp.transform(m)
        faces = self._merge(bm, tmp, local, edge)
        self.meta[role].append((faces, ("box",), self._panel_id(panel), False))
        return faces

    def _merge(self, bm, tmp, local, edge=()):
        tmp.verts.ensure_lookup_table()
        vmap = {}
        for v, lc in zip(tmp.verts, local):
            nv = bm.verts.new(v.co)
            nv[bm.verts.layers.float_vector["local"]] = lc
            vmap[v] = nv
        out = []
        for f in tmp.faces:
            try:
                nf = bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                continue
            out.append(nf)
            if f in edge:
                self.edge_faces.add(nf)
        tmp.free()
        return out

    def _panel_id(self, panel):
        return (self.rng.random(), self.rng.random()) if panel else (0.5, 0.99)

    # ------------------------------------------------------------------ collision, sockets, decals
    def collision_box(self, lo, hi, m=None):
        lo, hi = Vector(lo), Vector(hi)
        pts = [Vector((x, y, z)) for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
        if m is not None:
            pts = [m @ p for p in pts]
        self.ucx.append(pts)

    def collision_hull(self, pts):
        self.ucx.append([Vector(p) for p in pts])

    def socket(self, name, loc, x=(1, 0, 0), z=(0, 0, 1), **params):
        self.sockets.append((name, Vector(loc), Vector(x), Vector(z), params))

    def decal(self, item, frm, to, rot=0.0, scale=1.0, frame_xy=None, label=False):
        self.decal_items.append({"item": item, "from": list(frm), "to": list(to), "rot": rot, "scale": scale,
                                 "frame": frame_xy, "label": label})

    # ------------------------------------------------------------------ finish
    def build(self, coll, mats):
        """One mesh object with the role slots actually used, UVs, vertex colours; UCX objects; sockets."""
        me = bpy.data.meshes.new(self.name)
        out = bmesh.new()
        uv0 = out.loops.layers.uv.new("UVMap")
        uv1 = out.loops.layers.uv.new("PanelId")
        col = out.loops.layers.float_color.new("Col")
        used = [r for r in ROLES if self.bm[r].faces]
        for si, role in enumerate(used):
            src = self.bm[role]
            src.normal_update()
            loc = src.verts.layers.float_vector.get("local")
            vmap = {}
            for v in src.verts:
                vmap[v] = out.verts.new(v.co)
            face_meta = {}
            for faces, mode, pid, secondary in self.meta[role]:
                for f in faces:
                    face_meta[f] = (mode, pid, secondary)
            for f in src.faces:
                if not f.is_valid:
                    continue
                try:
                    nf = out.faces.new([vmap[v] for v in f.verts])
                except ValueError:
                    continue
                nf.material_index = si
                nf.smooth = f.smooth
                mode, pid, secondary = face_meta.get(f, (("box",), (0.5, 0.99), False))
                n = f.normal
                # the face normal in the part's local coords of the box (trim strips pick their axes there)
                lcs = [l.vert[loc] for l in f.loops]
                ln = Vector((0.0, 0.0, 0.0))
                for i in range(len(lcs)):
                    a_, b_ = lcs[i], lcs[(i + 1) % len(lcs)]
                    ln += Vector(((a_.y - b_.y) * (a_.z + b_.z), (a_.z - b_.z) * (a_.x + b_.x), (a_.x - b_.x) * (a_.y + b_.y)))
                for l_src, l_dst in zip(f.loops, nf.loops):
                    p = l_src.vert.co
                    lc = l_src.vert[loc]
                    l_dst[uv0].uv = self._uv(mode, p, lc, ln if mode[0] != "box" else n)
                    l_dst[uv1].uv = pid
                    # occlusion falls off towards the floor (the master's dirt rises there: one clean tone on
                    # everything - critic, 27. 9. 2026)
                    occ = 1.0 - 0.4 * min(1.0, max(0.0, 1.0 - p.z / 0.5))
                    l_dst[col] = (occ, 0.0 if f in self.edge_faces else 1.0, 0.0 if secondary else 1.0, 1.0)
        out.normal_update()
        out.to_mesh(me)
        out.free()
        for role in used:
            me.materials.append(mats[role])
        if "Col" in me.color_attributes:
            # the FBX exporter writes the active colour attribute: the layered master's masks
            me.color_attributes.active_color_name = "Col"
            me.color_attributes.render_color_index = me.color_attributes.find("Col")
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        # sharp edges from the bevels read as smooth faces with crisp silhouettes
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(40))
        for i, pts in enumerate(self.ucx):
            cm = bpy.data.meshes.new("UCX_%s_%02d" % (self.name, i))
            cbm = bmesh.new()
            for p in pts:
                cbm.verts.new(p)
            bmesh.ops.convex_hull(cbm, input=list(cbm.verts))
            cbm.to_mesh(cm)
            cbm.free()
            co = bpy.data.objects.new(cm.name, cm)
            coll.objects.link(co)
            co.parent = ob
            co.display_type = "WIRE"
        for name, loc, x, z, params in self.sockets:
            e = bpy.data.objects.new("SOCKET_" + name, None)
            e.empty_display_type = "ARROWS"
            e.empty_display_size = 0.08
            y = z.cross(x).normalized()
            e.matrix_world = frame(loc, x, y, z)
            coll.objects.link(e)
            e.parent = ob
            e["params"] = json.dumps(params)
        return ob

    def _uv(self, mode, p, lc, n):
        if mode[0] == "trim":
            _, strip, lo, hi = mode
            s = TRIM["strips"][strip]
            size = hi - lo
            axes = sorted(range(3), key=lambda a: -size[a])
            along = axes[0]
            # the strip's height runs across the face's other in-plane axis (the larger of the remaining two
            # that is not the face normal's axis in local coords)
            nl = max(range(3), key=lambda a: abs(n[a])) if n.length > 0 else 2
            rest = [a for a in axes[1:] if a != nl] or axes[1:2]
            across = rest[0]
            t = (lc[across] - lo[across]) / max(1e-6, size[across])
            v0, v1 = s["v_blender"]
            return (lc[along] / s["u_repeat_m"], v0 + (v1 - v0) * (1.0 - t))
        if mode[0] == "atlas":
            _, (au0, av0, au1, av1), lo, hi = mode
            size = hi - lo
            s_ = (lc.x - lo.x) / max(1e-6, size.x)
            t_ = (lc.y - lo.y) / max(1e-6, size.y)
            return (au0 + (au1 - au0) * s_, av0 + (av1 - av0) * t_)
        # metres, box projection by the dominant normal axis
        a = max(range(3), key=lambda k: abs(n[k]))
        if a == 0:
            return (p.y, p.z)
        if a == 1:
            return (p.x, p.z)
        return (p.x, p.y)


def materials():
    """Blender materials per role, named as the slots (the importer maps them to MI_Kit_<Maker>_<Role>); their
    Principled values follow the Halcyon palette so the catalog renders read like the game."""
    pal = RULES["palettes"]["Halcyon"]
    spec = {
        "Kit_Primary": (pal["Kit_Primary"], 0.5, 0.0, None),
        "Kit_Structure": (pal["Kit_Structure"], 0.36, 1.0, None),
        "Kit_Accent": (pal["Kit_Accent"], 0.42, 0.0, None),
        "Kit_Signal": (pal["Kit_Signal"], 0.42, 0.0, None),
        "Kit_Rubber": ([0.018, 0.018, 0.02], 0.86, 0.0, None),
        "Kit_Fabric": ([0.03, 0.03, 0.032], 0.9, 0.0, None),
        "Kit_Plastic": ([0.035, 0.035, 0.038], 0.5, 0.0, None),
        "Kit_Trim": ([0.3, 0.3, 0.3], 0.45, 0.5, None),
        "Kit_Seal": ([0.012, 0.012, 0.013], 0.7, 0.0, None),
        "Kit_GlowWarm": ([0.1, 0.1, 0.1], 0.3, 0.0, (pal["Kit_GlowWarm"], 14.0)),
        "Kit_GlowCool": ([0.05, 0.05, 0.06], 0.3, 0.0, (pal["Kit_GlowCool"], 8.0)),
        "Kit_GlowSignal": ([0.1, 0.05, 0.02], 0.3, 0.0, (pal["Kit_GlowSignal"], 4.0)),
        "Kit_Screen": ([0.01, 0.01, 0.015], 0.2, 0.0, ([0.35, 0.6, 1.0], 3.0)),
        "Kit_Glass": ([0.02, 0.03, 0.035], 0.05, 0.0, None),
        "Kit_Decal": ([0.2, 0.2, 0.2], 0.5, 0.0, None),
        "Kit_DecalAO": ([0.0, 0.0, 0.0], 0.5, 0.0, None),
        "Kit_DecalPaint": ([0.6, 0.6, 0.6], 0.5, 0.0, None),
    }
    tex = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
    out = {}
    for name, (c, r, mt, emit) in spec.items():
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (c[0], c[1], c[2], 1.0)
        bsdf.inputs["Roughness"].default_value = r
        bsdf.inputs["Metallic"].default_value = mt
        if emit:
            ec, strength = emit
            bsdf.inputs["Emission Color"].default_value = (ec[0], ec[1], ec[2], 1.0)
            bsdf.inputs["Emission Strength"].default_value = strength
        if name == "Kit_Trim":
            nt = m.node_tree
            img = nt.nodes.new("ShaderNodeTexImage")
            img.image = bpy.data.images.load(os.path.join(tex, "T_Kit_Trim_BC.png"), check_existing=True)
            nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
            nimg = nt.nodes.new("ShaderNodeTexImage")
            nimg.image = bpy.data.images.load(os.path.join(tex, "T_Kit_Trim_N.png"), check_existing=True)
            nimg.image.colorspace_settings.name = "Non-Color"
            nmap = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(nimg.outputs["Color"], nmap.inputs["Color"])
            nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
            oimg = nt.nodes.new("ShaderNodeTexImage")
            oimg.image = bpy.data.images.load(os.path.join(tex, "T_Kit_Trim_ORM.png"), check_existing=True)
            oimg.image.colorspace_settings.name = "Non-Color"
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(oimg.outputs["Color"], sep.inputs["Color"])
            nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
            nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
        if name in ("Kit_Decal", "Kit_DecalAO", "Kit_DecalPaint"):
            _decal_nodes(m, name)
        m.diffuse_color = (c[0] ** 0.45, c[1] ** 0.45, c[2] ** 0.45, 1.0)
        out[name] = m
    return out


def _decal_nodes(m, name):
    """Decal atlas in Blender for the catalog (in the game these are DBuffer decal masters): structural = graphite
    with the decal normal, cut out by M.R; AO = black by (1 - AO) x M.R; paint = the atlas colour by BC.a x M.R."""
    d = os.path.join(ROOT, "ArtSource", "Ships", "Shared", "Decals")
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(transp.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])

    def img(fn, noncolor=True):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(d, fn), check_existing=True)
        if noncolor:
            t.image.colorspace_settings.name = "Non-Color"
        return t
    mm = img("T_Decals_M.png")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(mm.outputs["Color"], sep.inputs["Color"])
    fac = nt.nodes.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Red"], fac.inputs[0])
    fac.inputs[1].default_value = 1.0
    nt.links.new(fac.outputs[0], mix.inputs["Fac"])
    if name == "Kit_Decal":
        bsdf.inputs["Base Color"].default_value = (0.06, 0.06, 0.065, 1.0)
        nm = img("T_Decals_N.png")
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    elif name == "Kit_DecalAO":
        bsdf.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        ao = img("T_Decals_AO.png")
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(ao.outputs["Color"], inv.inputs[1])
        nt.links.new(inv.outputs[0], fac.inputs[1])
    else:
        bc = img("T_Decals_BC.png", noncolor=False)
        nt.links.new(bc.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(bc.outputs["Alpha"], fac.inputs[1])
        nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
