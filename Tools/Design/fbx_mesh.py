"""Reads the meshes of a binary FBX in plain Python (no Blender), for the interior drawings (dossier bod 4: the
drawings show the parts as they are built - Tools/Design/interior_model.py).

    python Tools/Design/fbx_mesh.py ArtSource/Kit/Export/SM_Kit_Wall_HullLiner12L_A.fbx

Our FBX files come from Blender's exporter (Tools/Kit/kit_build.py, Tools/Blender/gamespace_ship_export.py): version
7400, every mesh object's vertices in its own Blender space (metres, Z up), the root model carrying the axis and unit
conversion (-90 deg about X, x100). read() returns each mesh object in Blender space with its own local transform
applied (the root's conversion left out), triangulated, with a material name per triangle, and the null objects
(SOCKET_*) with their Blender-space positions. Collision hulls (UCX_*) are left out unless asked for.
"""
import math
import os
import struct
import sys
import zlib

import numpy as np

_CACHE = {}


def _nodes(data):
    ver = struct.unpack_from("<I", data, 23)[0]
    hdr = "<QQQB" if ver >= 7500 else "<IIIB"
    hsz = struct.calcsize(hdr)

    def prop(off):
        t = chr(data[off])
        off += 1
        if t == "Y":
            return struct.unpack_from("<h", data, off)[0], off + 2
        if t == "C":
            return bool(data[off]), off + 1
        if t == "I":
            return struct.unpack_from("<i", data, off)[0], off + 4
        if t == "F":
            return struct.unpack_from("<f", data, off)[0], off + 4
        if t == "D":
            return struct.unpack_from("<d", data, off)[0], off + 8
        if t == "L":
            return struct.unpack_from("<q", data, off)[0], off + 8
        if t in "fdlib":
            n, enc, clen = struct.unpack_from("<III", data, off)
            off += 12
            raw = data[off:off + clen]
            off += clen
            if enc == 1:
                raw = zlib.decompress(raw)
            dt = {"f": "<f4", "d": "<f8", "l": "<i8", "i": "<i4", "b": "u1"}[t]
            return np.frombuffer(raw, dtype=dt, count=n), off
        if t in "SR":
            n = struct.unpack_from("<I", data, off)[0]
            off += 4
            raw = data[off:off + n]
            return (raw.decode("utf-8", "replace") if t == "S" else raw), off + n
        raise ValueError("FBX property type %r" % t)

    def node(off):
        end, nprops, _, nlen = struct.unpack_from(hdr, data, off)
        if end == 0:
            return None, off + hsz
        off += hsz
        name = data[off:off + nlen].decode()
        off += nlen
        props = []
        for _ in range(nprops):
            v, off = prop(off)
            props.append(v)
        kids = []
        while off < end:
            k, off = node(off)
            if k is None:
                break
            kids.append(k)
        return (name, props, kids), end

    off, top = 27, []
    while off < len(data) - hsz:
        n, off = node(off)
        if n is None:
            break
        top.append(n)
    return top


def _child(n, name):
    return next((k for k in n[2] if k[0] == name), None)


def _p70(n):
    out = {}
    p = _child(n, "Properties70")
    for k in (p[2] if p else []):
        if k[0] == "P":
            out[k[1][0]] = k[1][4:]
    return out


def _matrix(p):
    """Local transform of a model (translation, XYZ euler rotation in degrees, scale; pivots are identity in our
    files)."""
    t = p.get("Lcl Translation", (0.0, 0.0, 0.0))
    r = [math.radians(a) for a in p.get("Lcl Rotation", (0.0, 0.0, 0.0))]
    s = p.get("Lcl Scaling", (1.0, 1.0, 1.0))
    cx, sx, cy, sy, cz, sz = math.cos(r[0]), math.sin(r[0]), math.cos(r[1]), math.sin(r[1]), math.cos(r[2]), math.sin(r[2])
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3] = (rz @ ry @ rx) * np.array(s, dtype=float)
    m[:3, 3] = t
    return m


class Mesh:
    """A triangulated mesh: verts (n, 3) float64, tris (m, 3) int, mat (m,) index into materials, uv (m, 3, 2) the
    first UV layer per triangle corner (None without one)."""

    def __init__(self, name, verts, tris, mat, materials, uv=None):
        self.name, self.verts, self.tris, self.mat, self.materials, self.uv = name, verts, tris, mat, materials, uv


def read(path, collision=False):
    """{"meshes": [Mesh], "nulls": {name: (x, y, z)}} in Blender space (metres), cached per file."""
    key = (os.path.abspath(path), collision, os.path.getmtime(path))
    if key in _CACHE:
        return _CACHE[key]
    data = open(path, "rb").read()
    top = _nodes(data)
    objs = _child(next(n for n in top if n[0] == "Objects"), "Objects") or next(n for n in top if n[0] == "Objects")
    conns = next(n for n in top if n[0] == "Connections")
    by_id = {}
    for n in objs[2]:
        if n[1] and isinstance(n[1][0], int):
            by_id[n[1][0]] = n
    parent, children = {}, {}
    for c in conns[2]:
        if c[0] == "C" and c[1][0] == "OO":
            parent[c[1][1]] = c[1][2]
            children.setdefault(c[1][2], []).append(c[1][1])

    def name_of(n):
        return n[1][1].split("\x00")[0]

    def world(mid):
        """Model-to-Blender transform: the model's own chain without the root (the root carries the exporter's axis
        and unit conversion, which Blender space does not have)."""
        m = np.eye(4)
        cur = mid
        while cur in by_id and by_id[cur][0] == "Model":
            par = parent.get(cur, 0)
            if par == 0:                         # the root model: the conversion, left out
                break
            m = _matrix(_p70(by_id[cur])) @ m
            cur = par
        return m

    meshes, nulls = [], {}
    for mid, n in by_id.items():
        if n[0] != "Model":
            continue
        kind = n[1][2]
        name = name_of(n)
        if kind == "Null":
            m = world(mid)
            nulls[name] = tuple(m[:3, 3])
            continue
        if kind != "Mesh" or (name.startswith("UCX_") and not collision):
            continue
        geo = next((by_id[c] for c in children.get(mid, []) if c in by_id and by_id[c][0] == "Geometry"), None)
        mats = [name_of(by_id[c]) for c in children.get(mid, []) if c in by_id and by_id[c][0] == "Material"]
        if geo is None:
            continue
        v = np.asarray(_child(geo, "Vertices")[1][0], dtype=float).reshape(-1, 3)
        idx = np.asarray(_child(geo, "PolygonVertexIndex")[1][0], dtype=np.int64)
        lem = _child(geo, "LayerElementMaterial")
        pmat = None
        if lem is not None:
            pm = np.asarray(_child(lem, "Materials")[1][0], dtype=np.int64)
            mapping = _child(lem, "MappingInformationType")[1][0]
            pmat = pm if mapping == "ByPolygon" else None
            if mapping == "AllSame":
                pmat = np.full(int((idx < 0).sum()), int(pm[0]) if len(pm) else 0)
        ends = np.nonzero(idx < 0)[0]
        starts = np.concatenate([[0], ends[:-1] + 1])
        real = np.where(idx < 0, ~idx, idx)
        sizes = ends - starts + 1
        tris, tmat, corner = [], [], []
        if np.all(sizes == 3):
            tris = real.reshape(-1, 3)
            tmat = pmat if pmat is not None else np.zeros(len(tris), dtype=np.int64)
            corner = np.arange(len(real)).reshape(-1, 3)
        else:                                   # fan-triangulate n-gons
            for k, (s0, e0) in enumerate(zip(starts, ends)):
                for j in range(1, e0 - s0):
                    tris.append((real[s0], real[s0 + j], real[s0 + j + 1]))
                    corner.append((s0, s0 + j, s0 + j + 1))
                    tmat.append(pmat[k] if pmat is not None else 0)
            tris = np.asarray(tris, dtype=np.int64)
            tmat = np.asarray(tmat, dtype=np.int64)
            corner = np.asarray(corner, dtype=np.int64)
        uv = None
        leu = _child(geo, "LayerElementUV")
        if leu is not None and len(corner):
            uvs = np.asarray(_child(leu, "UV")[1][0], dtype=float).reshape(-1, 2)
            uvi = _child(leu, "UVIndex")
            pv = np.asarray(uvi[1][0], dtype=np.int64) if uvi is not None else np.arange(len(real))
            uv = uvs[pv[corner]]
        m = world(mid)
        vw = v @ m[:3, :3].T + m[:3, 3]
        meshes.append(Mesh(name, vw, np.asarray(tris, dtype=np.int64), np.asarray(tmat, dtype=np.int64), mats, uv))
    out = {"meshes": meshes, "nulls": nulls}
    _CACHE[key] = out
    return out


def main(argv):
    r = read(argv[0])
    for m in r["meshes"]:
        lo, hi = m.verts.min(0), m.verts.max(0)
        print("FBXMESH %s: %d verts, %d tris, bounds %s .. %s, materials %s" % (
            m.name, len(m.verts), len(m.tris), np.round(lo, 3).tolist(), np.round(hi, 3).tolist(), m.materials))
    for k, v in sorted(r["nulls"].items()):
        print("FBXMESH null %s %s" % (k, np.round(v, 4).tolist()))


if __name__ == "__main__":
    main(sys.argv[1:])
