"""Vector line drawings of built meshes for the interior drawings (dossier bod 4): an orthographic view of a set of
triangle meshes drawn into a matplotlib sheet - the faces that look at the viewer filled in their material's tint and
shaded a little by their slope, painted far to near (painter's algorithm), with the feature edges (creases over
CREASE_DEG, open borders, silhouettes, material borders) drawn with each face so nearer faces cover them. A cut
plane keeps only what lies beyond it and draws the cut through every mesh as a heavy line (sections, the plan's cut
at 1.2 m).

Used by Tools/Design/draw_interior_sheet.py with the parts placed by Tools/Design/interior_model.py.
"""
import math

import numpy as np
from matplotlib.collections import LineCollection, PolyCollection

CREASE_DEG = 32.0
CUT_LW = 0.5           # mm, cut lines (ISO 128: thick)
EDGE_LW = 0.1          # mm, feature edges of faces beyond the cut
OUTLINE_LW = 0.18      # mm, silhouettes and open borders
PT = 72.0 / 25.4


def srgb(c):
    c = np.clip(np.asarray(c, dtype=float), 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def tint(linear, k=0.5):
    """A material's colour for a drawing: sRGB lightened toward white so dark materials still read as fills and
    lines stay visible on them (k = how much of the colour is kept)."""
    s = srgb(linear)
    return tuple(1.0 - k * (1.0 - s))


class Part:
    """One placed mesh: world vertices (n, 3) in layout metres, triangles, a material name per triangle, an ID tag."""

    def __init__(self, tag, verts, tris, mats, edges=None):
        self.tag, self.verts, self.tris, self.mats = tag, verts, tris, mats
        self._edges = edges

    def edges(self):
        """Edge list (k, 2) vertex indices, the two faces on each edge (-1 = open border), cached."""
        if self._edges is None:
            t = self.tris
            e = np.concatenate([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
            f = np.concatenate([np.arange(len(t))] * 3)
            e = np.sort(e, axis=1)
            order = np.lexsort((e[:, 1], e[:, 0]))
            e, f = e[order], f[order]
            same = np.all(e[1:] == e[:-1], axis=1)
            first = np.concatenate([[True], ~same])
            idx = np.cumsum(first) - 1
            n = idx[-1] + 1 if len(idx) else 0
            uniq = e[first]
            fa = np.full(n, -1)
            fb = np.full(n, -1)
            fa[idx[first]] = f[first]
            sec = ~first
            fb[idx[sec]] = f[sec]
            self._edges = (uniq, fa, fb)
        return self._edges


class View:
    """Orthographic view: paper axes u (right), v (up) and the viewing direction d (away from the viewer), all
    unit vectors in layout space; paper = (ox + s * (p.u - u0), oy + s * (p.v - v0)) in mm."""

    def __init__(self, u, v, d, ox, oy, s, u0=0.0, v0=0.0):
        self.u, self.v, self.d = (np.asarray(a, dtype=float) for a in (u, v, d))
        self.ox, self.oy, self.s, self.u0, self.v0 = ox, oy, s, u0, v0

    def paper(self, pts):
        pts = np.asarray(pts, dtype=float)
        return np.stack([self.ox + self.s * (pts @ self.u - self.u0), self.oy + self.s * (pts @ self.v - self.v0)], -1)

    def P(self, p):
        q = self.paper(np.asarray(p, dtype=float)[None])[0]
        return float(q[0]), float(q[1])


def _normals(V, T):
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] /= ln[ok, None]
    return n, ok


def draw(ax, view, parts, colours, clip=None, cut=None, z=5.0, light=(0.35, -0.45, 0.82), chunks=60,
         cut_col="#1B1B1B", edge_col="#2B2B2B", skip_mats=(), window=None, cut_parts=None, fill=True):
    """Draws the parts into ax. colours: material name -> RGB (0..1) or None to skip. clip: (lo, hi) xyz box in
    layout metres - only faces whose centre lies inside. cut: (point, normal) - faces beyond the plane (normal points
    away from the viewer) and the cut line through every part (or only the parts whose tag is in cut_parts).
    window: (x0, y0, x1, y1) paper mm - everything drawn is clipped to it. fill=False draws only the cut lines.
    Returns the paper segments of the cut and the tags drawn."""
    from matplotlib.patches import Rectangle
    clip_patch = None
    if window is not None:
        clip_patch = Rectangle((window[0], window[1]), window[2] - window[0], window[3] - window[1],
                               transform=ax.transData, fc="none", ec="none")
    added = []
    if not fill:
        parts_cut = [p for p in parts if cut_parts is None or p.tag in cut_parts]
        segs = []
        for p in parts_cut:
            cp, cn = (np.asarray(a, dtype=float) for a in cut)
            segs += _slice(p.verts, p.tris, cp, cn, clip)
        paper = [view.paper(np.asarray(s)) for s in segs]
        if paper:
            lc = LineCollection(paper, colors=cut_col, linewidths=CUT_LW * PT, zorder=z + 0.5, capstyle="round")
            ax.add_collection(lc)
            if clip_patch is not None:
                lc.set_clip_path(clip_patch)
        return paper, set()
    result = _draw(ax, view, parts, colours, clip, cut, z, light, chunks, cut_col, edge_col, skip_mats, added, cut_parts)
    if clip_patch is not None:
        for c in added:
            c.set_clip_path(clip_patch)
    return result


def _draw(ax, view, parts, colours, clip, cut, z, light, chunks, cut_col, edge_col, skip_mats, added, cut_parts):
    def add(c):
        ax.add_collection(c)
        added.append(c)
    lt = np.asarray(light, dtype=float)
    lt /= np.linalg.norm(lt)
    polys, fills, depth, elines, eparts = [], [], [], [], []
    cut_segs = []
    drawn = set()
    for p in parts:
        V, T = p.verts, p.tris
        if len(T) == 0:
            continue
        n, ok = _normals(V, T)
        cen = V[T].mean(axis=1)
        keep = ok & (n @ view.d < -1e-6)
        mats = np.asarray(p.mats)
        if len(mats):
            names, inv = np.unique(mats, return_inverse=True)
            ok_name = np.array([colours.get(m) is not None and m not in skip_mats for m in names])
            col = ok_name[inv]
        else:
            col = np.ones(len(T), bool)
        keep &= col
        if clip is not None:
            lo, hi = (np.asarray(a, dtype=float) for a in clip)
            keep &= np.all((cen >= lo) & (cen <= hi), axis=1)
        if cut is not None:
            cp, cn = (np.asarray(a, dtype=float) for a in cut)
            keep &= (cen - cp) @ cn > 0.0
            if cut_parts is None or p.tag in cut_parts:
                cut_segs += _slice(V, T, cp, cn, clip)
        if not keep.any():
            continue
        idx = np.nonzero(keep)[0]
        if len(idx):
            drawn.add(p.tag)
        P2 = view.paper(V)
        dd = cen[idx] @ view.d
        shade = 0.78 + 0.22 * np.abs(n[idx] @ lt)
        for k, ti in enumerate(idx):
            c = colours[mats[ti]] if len(mats) else (0.85, 0.85, 0.85)
            polys.append(P2[T[ti]])
            fills.append(tuple(min(1.0, ch * shade[k]) for ch in c))
            depth.append(dd[k])
        # feature edges among the kept faces
        E, fa, fb = p.edges()
        visible = np.zeros(len(T), bool)
        visible[idx] = True
        va = np.where(fa >= 0, visible[np.maximum(fa, 0)], False)
        vb = np.where(fb >= 0, visible[np.maximum(fb, 0)], False)
        any_vis = va | vb
        border = (fb < 0) | (va ^ vb)                       # open border or silhouette
        both = va & vb
        crease = np.zeros(len(E), bool)
        if both.any():
            cosang = np.einsum("ij,ij->i", n[fa[both]], n[fb[both]])
            cr = cosang < math.cos(math.radians(CREASE_DEG))
            if len(mats):
                cr |= mats[fa[both]] != mats[fb[both]]
            crease[both] = cr
        feat = any_vis & (border | crease)
        for ei in np.nonzero(feat)[0]:
            f = fa[ei] if va[ei] else fb[ei]
            elines.append((P2[E[ei]], (cen[f] @ view.d) - 1e-4, border[ei]))
    # painter's algorithm: far to near, faces and their edges in chunks
    order = np.argsort(-np.asarray(depth)) if depth else []
    eorder = sorted(range(len(elines)), key=lambda i: -elines[i][1])
    if len(order):
        bounds = np.linspace(0, len(order), chunks + 1).astype(int)
        dsorted = np.asarray(depth)[order]
        ei = 0
        for c in range(chunks):
            a, b = bounds[c], bounds[c + 1]
            if b <= a:
                continue
            sel = order[a:b]
            pc = PolyCollection([polys[i] for i in sel], facecolors=[fills[i] for i in sel],
                                edgecolors=[fills[i] for i in sel], linewidths=0.05 * PT, zorder=z, antialiased=True)
            add(pc)
            near = dsorted[b - 1]
            segs_t, segs_b = [], []
            while ei < len(eorder) and elines[eorder[ei]][1] >= near - 1e-9:
                seg, _, is_border = elines[eorder[ei]]
                (segs_b if is_border else segs_t).append(seg)
                ei += 1
            if segs_t:
                add(LineCollection(segs_t, colors=edge_col, linewidths=EDGE_LW * PT, zorder=z,
                                                 capstyle="round"))
            if segs_b:
                add(LineCollection(segs_b, colors=edge_col, linewidths=OUTLINE_LW * PT, zorder=z,
                                                 capstyle="round"))
        rest = [elines[i][0] for i in eorder[ei:]]
        if rest:
            add(LineCollection(rest, colors=edge_col, linewidths=EDGE_LW * PT, zorder=z))
    paper_cut = []
    if cut_segs:
        segs = [view.paper(np.asarray(s)) for s in cut_segs]
        paper_cut = segs
        add(LineCollection(segs, colors=cut_col, linewidths=CUT_LW * PT, zorder=z + 0.5,
                                         capstyle="round", joinstyle="round"))
    return paper_cut, drawn


def _slice(V, T, cp, cn, clip=None):
    """Segments where the plane (cp, cn) cuts the triangles (3D points)."""
    # a vertex on the plane counts as beyond it (d >= 0): a hull built on frame stations has its panel seams exactly in
    # a section through a station, and the strict test skipped every triangle that only touched the plane
    d = (V - cp) @ cn
    dt = d[T]
    pos = dt >= 0
    cross = ~(np.all(pos, axis=1) | np.all(~pos, axis=1))
    out = []
    for ti in np.nonzero(cross)[0]:
        pts = []
        tri = T[ti]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            da, db = dt[ti, a], dt[ti, b]
            if (da < 0 <= db) or (db < 0 <= da):
                t = da / (da - db)
                pts.append(V[tri[a]] + t * (V[tri[b]] - V[tri[a]]))
        if len(pts) == 2:
            if clip is not None:
                lo, hi = clip
                mid = (pts[0] + pts[1]) / 2
                if np.any(mid < np.asarray(lo)) or np.any(mid > np.asarray(hi)):
                    continue
            out.append(pts)
    return out
