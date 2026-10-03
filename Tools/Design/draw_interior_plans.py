"""The whole-ship interior sheets after the rooms (dossier bod 4): I-07 the signs and decals, I-08 the lights and their
cost, I-09 the schedules of doors, furniture, components and objects - drawn from the same data and built parts as the
deck sheet I-01 (Tools/Design/draw_interior_deck.py) in the style of I-04.

    python Tools/Design/draw_interior_plans.py [Wayfarer] [--dpi 200] [--sheets I-07 I-08 I-09]

I-07 and I-08: the deck's plan 1:20 (DeckSheet.base_plan) with every decal or light at its place, labelled by the part
that carries it, and their tables; I-09: the schedules on A1. Each writes <Ship>_I0n_*.png and .json (the IDs drawn,
labelled and listed: Tools/Tests/test_interior_drawing.py; interior_model.deck_views DECALS, LIGHTS).
"""
import argparse
import json
import os
import sys

import numpy as np
from matplotlib.patches import Polygon as MplPolygon

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import draw_exterior_sheet as ds  # noqa: E402
import draw_interior_deck as dd  # noqa: E402
import draw_interior_sheet as dis  # noqa: E402
import interior_model as im  # noqa: E402
from draw_exterior_sheet import GREY, INK, STATUS_COL  # noqa: E402

SHEETS = {"I-07": ("I07_decals", "Interiér – plán nápisů a decalů: všechny nápisy lodi v půdorysu, položky knihovny"),
          "I-08": ("I08_lights", "Interiér – plán světel a výkon: všechna světla lodi v půdorysu, souhrn po místnostech"),
          "I-09": ("I09_schedules", "Interiér – rozpisy dveří, nábytku, komponent a objektů lodi")}
dis.SHEETS.update(SHEETS)
dis.SHEET_META["I-09"] = dict(dis.SHEET_META_DEFAULT, scale="–")
LABEL_ROWS = dict(tiers_up=[792.0, 799.0, 806.0, 813.0], tiers_dn=[478.0, 471.0, 464.0], bus_up=772.0, bus_dn=484.0)


SET_CZ = "světlo z nastavení lodi (pilot, obrazovky)"


def short_id(ident):
    return ident.split("/")[0]


class PlanSheet(dd.DeckSheet):
    """The deck sheet's machinery for a plan of decals or lights."""

    def __init__(self, m, geo, view):
        super().__init__(m, geo, dd.SECTION_Y)
        self.view = view
        self.views = {view: m.deck_views(dd.SECTION_Y)[view]}
        self.drawn = {view: set()}
        self.decal_pos = {}
        for p in self.places:
            self.decal_pos.update(geo.kit_decals(p))
        for e in m.elements:                       # the interior decals cast by a ray: where they land
            if e.cat == "decal" and e.extra.get("ray") and e.extra.get("dir") and e.status != "remove":
                q = dis.RoomSheet.ray_decal(self, e)
                if q is not None:
                    self.decal_pos[e.id] = q
        self.script = "draw_interior_plans.py"

    def where(self, e):
        """An element's place in plan (layout x, y) - a kit decal from its built quad, a projected or cast one from its
        data, a light from its position."""
        if e.id in self.decal_pos:
            c = self.decal_pos[e.id][0]
            return float(c[0]), float(c[1]), float(c[2])
        if e.extra.get("pos") is not None:
            return tuple(e.extra["pos"])
        return None

    def labels_by_host(self, vw, items, colour):
        """One leader per part that carries the items (a wall module, a ceiling panel), one per item that stands on
        its own (projected signs, the ship's lights by room and kind); every item counts as labelled."""
        groups = {}
        for e in items:
            key = short_id(e.id) if "/" in e.id else (("%s %s" % (e.room, e.id.split("-")[1])) if e.id.startswith("L-") else e.id)
            groups.setdefault(key, []).append(e)
        reqs = []
        for key, es in sorted(groups.items()):
            pts = [self.where(e) for e in es]
            pts = [p for p in pts if p is not None]
            if not pts:
                continue
            P = np.mean([vw.P(p) for p in pts], axis=0)
            if es[0].id.startswith("L-SET"):
                text = "L-SET: pilot + %d obrazovky" % (len(es) - 1) if len(es) > 1 else es[0].id
            elif es[0].id.startswith("L-"):
                nums = sorted(int(e.id.rsplit("-", 1)[1]) for e in es)
                text = "L-%s-%s" % (es[0].id.split("-")[1], ",".join(str(n) for n in nums)) if len(nums) <= 4 else \
                    "L-%s-%d…%d (%d)" % (es[0].id.split("-")[1], nums[0], nums[-1], len(nums))
            elif len(es) > 1:
                text = "%s (%d)" % (key, len(es))
            else:
                text = es[0].id
            for e in es:
                self.lab(self.view, e.id)
            reqs.append({"id": "#g-" + key, "text": text, "anchor": (float(P[0]), float(P[1])), "col": colour,
                         "z": float(P[1]), "hidden": False})
        return reqs


def decal_marker(sh, X, Y, r=0.9):
    sh.ax.add_patch(MplPolygon([(X, Y + r), (X + r, Y), (X, Y - r), (X - r, Y)], closed=True, fc=dis.hexrgb(dis.DECAL_FILL),
                               ec=dis.DECAL_EDGE, lw=0.2 * ds.PT, zorder=30))


# ---------------------------------------------------------------------- I-07
def draw_decals(m, geo, dpi, out_dir):
    rs = PlanSheet(m, geo, "DECALS")
    sh, d = rs.sh, rs.d
    ds.frame_and_zones(sh)
    rs.title(34, 822, "PLÁN NÁPISŮ A DECALŮ – PŮDORYS PALUBY, ŘEZ 1,20 m NAD PODLAHOU")
    vw, W, _ = rs.base_plan(50.0, 490.0, grid=False)
    items = [rs.el[i] for i in sorted(rs.views["DECALS"])]
    for e in items:
        p = rs.where(e)
        if p is None:
            continue
        rs.mark("DECALS", e.id)
        decal_marker(sh, *vw.P(p))
    reqs = rs.labels_by_host(vw, items, dis.DECAL_EDGE)
    d.place_labels("DECALS", reqs, 34, W[2] + 4, split_y=vw.P((0, 0.0, 0))[1], size=2.1, **LABEL_ROWS)
    # tables: every decal (paint and structural), the library items used, the grime cards per room
    D = sorted(items, key=lambda e: (list(m.rooms).index(e.room), not e.id.startswith("D-"), e.id))
    cols = [("ID", 40, "left"), ("položka", 27, "left"), ("osazeno", 15, "left"), ("účel / text", 76, "left", 2)]

    def size(e):
        if e.id in rs.decal_pos:
            q = rs.decal_pos[e.id][1]
            q = q - q.mean(axis=0)
            _, _, vt = np.linalg.svd(q, full_matrices=False)
            return "%d×%d cm" % (round(float(np.ptp(q @ vt[0])) * 100), round(float(np.ptp(q @ vt[1])) * 100))
        if e.extra.get("projected"):
            dd_ = next(v for v in m.setup["decals"] if isinstance(v, dict) and v.get("id") == e.id)
            return "%d×%d cm" % (round(2 * dd_["size"][2]), round(2 * dd_["size"][1]))
        s_ = e.extra.get("size") or (0, 0)
        return "%d×%d cm" % (round(s_[0] * 100), round(s_[1] * 100)) if s_[0] else ""
    rows = [([e.id, e.extra.get("item", ""), size(e), e.purpose or e.extra.get("note", "")], STATUS_COL[e.status]) for e in D]
    per = (len(rows) + 2) // 3
    for k in range(3):
        ds.table(sh, 34.0 + k * 163.0, 452.0, "DECALY A NÁPISY (%d)" % len(rows) if k == 0 else "pokračování",
                 cols, rows[k * per:(k + 1) * per], size=2.1, rowh=3.9)
    used = {}
    for e in D:
        used.setdefault(e.extra.get("item", ""), []).append(e)
    lib = m.library
    colsL = [("položka knihovny", 30, "left"), ("ks", 6, "right"), ("druh", 22, "left"), ("knihovna", 17, "left"),
             ("účel", 80, "left", 2)]
    rowsL = [([k, len(v), {"structural": "strukturní", "paint": "informační", "info": "informační", "wear": "opotřebení"}.get(lib.get(k, {}).get("type"), lib.get(k, {}).get("type", "promítaný")),
               "%d×%d cm" % tuple(round(c * 100) for c in lib[k]["size_m"]) if k in lib else "vlastní textura",
               m.decal_purpose(k) if k in lib else (v[0].purpose or "")], INK) for k, v in sorted(used.items())]
    yL = ds.table(sh, 34.0 + 3 * 163.0 + 4.0, 452.0, "POLOŽKY KNIHOVNY (%d)" % len(rowsL), colsL, rowsL, size=2.1, rowh=3.9)
    grime = {}
    for e in m.elements:
        if e.cat == "decal" and e.extra.get("grime") and e.room:
            grime.setdefault(e.room, []).append(e)
    yg = yL - 6.0
    sh.t(34.0 + 3 * 163.0 + 4.0, yg, "Karty špíny (jen v tabulkách listů místností): " + "; ".join(
        "%s %d" % (m.room_code(r), len(v)) for r, v in grime.items()), 2.2, GREY)
    scat = [e for e in m.elements if e.cat == "decal" and e.extra.get("item") == "scatter"]
    colsS = [("pravidlo rozsevu", 34, "left"), ("místnost", 22, "left"), ("stav", 22, "left"), ("oblast a hustota", 110, "left", 2)]
    rowsS = [([e.id, m.room_code(e.room) if e.room else "–", "postaveno" if e.status == "built" else "v kit místnosti 0 ks",
               e.purpose], STATUS_COL[e.status]) for e in scat]
    ds.table(sh, 34.0 + 3 * 163.0 + 4.0, yg - 8.0, "ROZSEV DECALŮ (polohy jen ve stavbě, ne v datech)", colsS, rowsS,
             size=2.1, rowh=3.9)
    rs.schedules = {"decals": {e.id for e in D} | {e.id for e in scat}}
    legend_notes(rs, 1030.0, 822.0, [
        "Kosočtverec = nápis nebo decal na svém místě v půdorysu (na stěně u jejího líce); štítek odkazu = díl, který "
        "nápisy nese, a jejich počet (rozpis v tabulce), nebo ID samostatného nápisu.",
        "D-INT = promítaný nápis lodi (setup.decals), D-I = nápis interiéru lodi (interior.decals); ostatní jsou decaly "
        "dílů kitu (ID dílu / položka knihovny).",
        "Osazeno = velikost z postavené geometrie (kit položky zmenšuje), knihovna = velikost v atlasu.",
        "Strukturní decal nese jen tvar (nýty, mřížky), informační i barvu (nápisy, štítky, pruhy).",
        "Podrobně po stěnách: listy místností I-02 až I-05 (rozvinuté pohledy).",
        "Promítaný nápis je obraz promítnutý ve hře na povrch; decal dílu je součást modelu dílu kitu.",
        "Nezakresleno: štítky ovladačů kokpitu, které klade stavba kokpitu (hs_cockpit, hs_interior_decals) mimo data "
        "interiéru – doplní se do dat interiéru (otevřený bod)."])
    return finish(rs, "I-07", dpi, out_dir, ["DECALS"])


# ---------------------------------------------------------------------- I-08
def light_marks(sh, X, Y, group, r):
    """The plan's marks by a light symbol: a large black corner top right = casts shadows, an "i" in a ring bottom
    left = only while walking the ship (all of a group's lights, or "i" with a count)."""
    if any(g.extra.get("shadow") for g in group):
        sh.ax.add_patch(MplPolygon([(X + r * 0.7, Y + r * 0.7), (X + r * 0.7 + 1.6, Y + r * 0.7), (X + r * 0.7, Y + r * 0.7 + 1.6)],
                                   closed=True, fc=INK, ec="white", lw=0.1 * ds.PT, zorder=31.6))
    walk = [g for g in group if g.extra.get("interior_only")]
    if walk:
        cx, cy = X - r * 0.75 - 0.8, Y - r * 0.75 - 0.8
        sh.ax.add_patch(dis.Circle((cx, cy), 0.85, fc="white", ec=INK, lw=0.15 * ds.PT, zorder=31.6))
        sh.t(cx, cy - 0.6, "i" if len(walk) == len(group) else "i%d" % len(walk), 1.5, INK, ha="center", z=31.7,
             weight="bold")


def colour_cz(e):
    """A light's colour in words: the kit's role, or the ship's light colour by its hue."""
    if e.extra.get("role"):
        return dis.LIGHT_ROLE_CZ.get(e.extra["role"], e.extra["role"])
    r, g, b = e.extra["colour"][:3]
    if r > 0.8 and g < 0.65 and b < 0.4:
        return "oranžová (akcent)"
    if b > r + 0.08:
        return "studená modrá" if b - r > 0.3 else "studená bílá"
    if r > b + 0.08:
        return "teplá bílá"
    return "neutrální bílá"


def draw_lights(m, geo, dpi, out_dir):
    rs = PlanSheet(m, geo, "LIGHTS")
    sh, d = rs.sh, rs.d
    ds.frame_and_zones(sh)
    rs.title(34, 822, "PLÁN SVĚTEL – PŮDORYS PALUBY, ŘEZ 1,20 m NAD PODLAHOU (SVĚTLA VŠECH VÝŠEK)")
    vw, W, _ = rs.base_plan(50.0, 490.0, grid=False)
    items = [rs.el[i] for i in sorted(rs.views["LIGHTS"])]
    pts = []
    R0 = 1.0
    for e in items:
        X, Y = vw.P(e.extra["pos"])
        rs.mark("LIGHTS", e.id)
        if e.extra["type"] == "rect" and e.extra.get("width_cm"):
            a = np.asarray(e.extra.get("along") or (0, 1, 0), dtype=float)
            n = float(np.hypot(a @ vw.u, a @ vw.v))
            if n > 0.3:
                rs.lamp(X, Y, e, ((float(a @ vw.u) / n, float(a @ vw.v) / n), e.extra["width_cm"] / 200.0 * vw.s * n),
                        tag=False, size=R0)
                light_marks(sh, X, Y, [e], R0)
                continue
        pts.append((X, Y, e))
    used = [False] * len(pts)
    for i, (X, Y, e) in enumerate(pts):          # lights on one spot (a down-light and its halo): one symbol with rings
        if used[i]:
            continue
        group = [e]
        for j in range(i + 1, len(pts)):
            if not used[j] and np.hypot(pts[j][0] - X, pts[j][1] - Y) < 1.6:
                used[j] = True
                group.append(pts[j][2])
        group.sort(key=lambda g: {"spot": 0, "point": 1}.get(g.extra["type"], 2))
        for k, g in enumerate(group[1:], 1):
            fill = dis.LIGHT_FILL.get(g.extra.get("role")) or dis.hexrgb(dis.md.tint(g.extra["colour"], 0.75))
            sh.ax.add_patch(dis.Circle((X, Y), R0 + 0.75 * k, fc="none", ec=fill, lw=0.6 * ds.PT, zorder=30.8 - k * 0.01))
            sh.ax.add_patch(dis.Circle((X, Y), R0 + 0.75 * k + 0.35, fc="none", ec=INK, lw=0.1 * ds.PT, zorder=30.9))
        rs.lamp(X, Y, group[0], tag=False, size=R0)
        r = R0 + 0.75 * (len(group) - 1)
        light_marks(sh, X, Y, group, r)
        if len(group) > 1:
            sh.t(X - r - 0.4, Y + r - 0.2, "%d×" % len(group), 1.7, INK, ha="right", z=31.5, bg="white")
    reqs = rs.labels_by_host(vw, items, INK)
    d.place_labels("LIGHTS", reqs, 34, W[2] + 4, split_y=vw.P((0, 0.0, 0))[1], size=2.1, **LABEL_ROWS)
    # per room: counts, shadows, flight vs walking, density on the built floor, total candelas
    cols = [("místnost", 30, "left"), ("světel", 13, "right"), ("za letu", 13, "right"), ("jen pěšky „i“", 19, "right"),
            ("se stínem", 15, "right"), ("podlaha m²", 17, "right"), ("na m²", 12, "right"), ("pravidlo kitu", 22, "left"),
            ("Σ cd", 14, "right")]
    rows = []
    for rid, r in m.rooms.items():
        L = m.in_room(rid, ("light",))
        area = dd.room_box(rs, rid)[2]
        key = {"crew": "living", "command": "cockpit", "cargo": "hold"}.get(r.get("zone"))
        rule = m.rules["lights"]["density_per_m2"].get(key) if key else None
        dens = len(L) / area if area else 0
        over = rule and dens > rule[1]
        rows.append(([r["name"], len(L), len([e for e in L if not e.extra.get("interior_only")]),
                      len([e for e in L if e.extra.get("interior_only")]), len([e for e in L if e.extra.get("shadow")]),
                      im.fmt(area, 1), im.fmt(dens, 2), ("%s–%s" % (im.fmt(rule[0], 1), im.fmt(rule[1], 1))) if rule else "není",
                      im.fmt(sum(e.extra["cd"] for e in L), 0)], STATUS_COL["remove"] if over else INK))
    yR = ds.table(sh, 34.0, 452.0, "SVĚTLA PO MÍSTNOSTECH (%d)" % len(items), cols, rows, size=2.3, rowh=4.3)
    # by kind: the kit's sockets and the ship's light kinds
    kinds = {}
    for e in items:
        k = e.id.split("-")[1] if e.id.startswith("L-") else e.id.split("/")[-1].split("_")[0]
        kinds.setdefault((k, e.extra["type"], colour_cz(e)), []).append(e)
    colsK = [("druh (socket / světlo lodi)", 40, "left"), ("ks", 8, "right"), ("typ", 30, "left"), ("barva", 26, "left"),
             ("cd od … do", 22, "right"), ("stín", 9, "left"), ("„i“", 14, "left"), ("místnosti", 26, "left"), ("účel", 72, "left", 2)]
    rowsK = []
    for (k, t, colour), es in sorted(kinds.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        e0 = es[0]
        cds = [e.extra["cd"] for e in es]
        walk = len([e for e in es if e.extra.get("interior_only")])
        purpose = (SET_CZ if k == "SET" else dis.SHIP_LIGHT_CZ.get("L-" + k)) if e0.id.startswith("L-") else \
            dis.SOCKET_CZ.get(k, k)
        if k == "Bay":
            purpose += " (pás nad výklenkem, bodové v emitoru)" if t == "rect" else " (bodové u komponenty)"
        rowsK.append(([("L-" + k) if e0.id.startswith("L-") else k, len(es), dis.LIGHT_TYPE_CZ.get(t, t), colour,
                       "%s … %s" % (im.fmt(min(cds), 2), im.fmt(max(cds), 2)),
                       "ano" if any(e.extra.get("shadow") for e in es) else "–",
                       ("všechna" if walk == len(es) else "%d z %d" % (walk, len(es))) if walk else "–",
                       ", ".join(sorted({m.room_code(e.room) for e in es})), purpose], INK))
    ds.table(sh, 34.0, yR - 6.0, "DRUHY SVĚTEL", colsK, rowsK, size=2.2, rowh=4.0)
    rs.schedules = {"lights": {e.id for e in items}}
    flight = [e for e in items if not e.extra.get("interior_only")]
    legend_notes(rs, 1030.0, 822.0, [
        "Symbol = světlo na svém místě v půdorysu (bodovka křížkem, bodové kroužkem, lineární pás čarou délky zdroje), "
        "barva výplně = barva světla. Černý roh vpravo nahoře = vrhá stín; „i“ v kroužku vlevo dole = svítí jen při "
        "chůzi lodí („i2“ = 2 světla skupiny). Víc světel v jednom bodě (bodovka a svatozář stropu nad sebou) = jeden "
        "symbol s kroužky v barvách dalších světel a počtem „2×“.",
        "Štítek odkazu = díl kitu, který světla nese, a jejich počet; L-FIX = světla svítících pásů a lamp lodi, L-INT = "
        "světla místností lodi (rozpis po socketech na listech místností I-02 až I-05).",
        "„i“ = světlo, které hra zapíná jen při chůzi lodí; za letu svítí %d z %d (z nich se stínem %d)." % (
            len(flight), len(items), len([e for e in flight if e.extra.get("shadow")])),
        "Výkon (cíl autora: zabalená hra 1080p na RTX 2060 6 GB, osvětlení za letu do 20 ms GPU, 29. 9.): poslední měření "
        "chodby z kitu 28. 9. dalo 16,7 ms pěšky a 20,4 ms za letu; proto od 29. 9. svítí osvětlení stěn, kanál, světla "
        "dolů, svatozáře a bodovky na stěnu jen pěšky („i“). Měření celé lodi s kitem po 3. 10. chybí – ověří hlavní "
        "session při předání (snímky výkonu v kokpitu, chodbě a nákladu, za letu i pěšky). Autor ve hře: let se dívat "
        "do chodby z kokpitu (F vstát), projít loď a hlídat trhání obrazu. Červeně v tabulce = hustota nad pravidlem kitu "
        "(místnost bez pravidla: „není“).",
        "L-SET = světla, která hra vytváří z nastavení lodi, ne z modelu: světlo pilota (oko + 0,45 m dopředu, 2,5 cd) "
        "a záře 4 obrazovek (12 cd × podíl plochy obrazovky, k oku pilota). Žádné z nich nevrhá stín.",
        "Hustota = světla / podlaha mezi líci postavených dílů (kokpit: obrys layoutu)."], lights=True)
    return finish(rs, "I-08", dpi, out_dir, ["LIGHTS"])


# ---------------------------------------------------------------------- I-09
def draw_schedules(m, geo, dpi, out_dir):
    """The schedules of the whole interior on A1: doors, furniture, components, objects and the ship's equipment."""
    rs = PlanSheet(m, geo, "LIGHTS")
    rs.sh = ds.Sheet(841.0, 594.0)
    rs.d.sh = rs.sh
    rs.views, rs.drawn = {}, {}
    sh = rs.sh
    ds.frame_and_zones(sh)
    sheet_of = dd.ROOM_SHEET
    els = [e for e in m.elements if e.room and e.status != "remove"]
    order = list(m.rooms)
    key = lambda e: (order.index(e.room), e.id)                  # noqa: E731
    doors = sorted((e for e in m.elements if e.cat == "door"), key=lambda e: e.extra["at"][0])
    colsD = [("ID", 22, "left"), ("dveře", 34, "left"), ("mezi", 18, "left"), ("poloha x, y", 22, "left"), ("šířka", 10, "right"),
             ("výška", 10, "right"), ("provedení", 30, "left", 2), ("stav křídla", 26, "left", 2), ("pohyb", 110, "left", 3),
             ("ovládání", 60, "left", 2), ("účel", 80, "left", 3), ("list", 14, "left")]
    rowsD = []
    for e in doors:
        lf = e.extra.get("leaf") or {}
        st = {"built": "postaveno", "proposed": "otvor postaven, křídlo návrh", "none": "otvor bez křídla"}.get(lf.get("leaf"), "")
        rowsD.append(([e.id + (" +" if lf.get("leaf") == "proposed" else ""), e.name,
                       " / ".join(m.room_code(r) for r in e.extra.get("rooms") or ()),
                       "%s, %s" % (im.fmt(e.extra["at"][0]), im.fmt(e.extra["at"][1])), im.fmt(e.extra["width"]),
                       im.fmt(lf["h"]) if lf.get("h") else "–",
                       lf.get("type", ""), st, lf.get("motion", ""), lf.get("operation", "") or "–", lf.get("purpose", ""),
                       ", ".join(sorted({sheet_of.get(r, "") for r in e.extra.get("rooms") or ()}))],
                      STATUS_COL["proposed"] if lf.get("leaf") == "proposed" else INK))
    y = ds.table(sh, 30.0, 575.0, "DVEŘE (%d)" % len(doors), colsD, rowsD, size=2.2, rowh=4.1)
    furn = sorted((e for e in els if e.cat == "furniture"), key=key)
    colsF = [("ID", 22, "left"), ("nábytek", 34, "left"), ("díl kitu / stavba", 40, "left"), ("umístění, rozměr", 110, "left", 3),
             ("účel", 210, "left", 3), ("list", 14, "left")]
    def dims(e):
        p_ = e.extra.get("placement")
        if p_ is None:
            return ""
        d_ = m.parts["SM_Kit_" + p_.part]["dims_m"]
        return "%s × %s × %s m, čelem k %s" % (im.fmt(d_[1]), im.fmt(d_[0]), im.fmt(d_[2]),
                                            "levoboku" if p_.dir_layout(1.0, 0.0)[1] > 0 else "pravoboku")
    rowsF = [([e.id, e.name, e.kit or "stavba lodi (kokpit)", e.where + ("; " + dims(e) if dims(e) else ""), e.purpose,
               sheet_of.get(e.room, "")], STATUS_COL[e.status]) for e in furn]
    y = ds.table(sh, 30.0, y - 5.0, "NÁBYTEK (%d)" % len(furn), colsF, rowsF, size=2.2, rowh=4.1)
    comps = sorted((e for e in els if e.cat == "component"), key=key)
    colsC = [("ID", 26, "left"), ("komponenta", 40, "left"), ("stav", 28, "left", 2), ("kde (postaveno / navrženo)", 58, "left", 2),
             ("výklenek / místo", 50, "left", 4), ("přístup", 62, "left", 4), ("výměna", 62, "left", 3),
             ("poznámka", 70, "left", 4), ("návrh ke schválení", 76, "left", 5), ("list", 10, "left")]
    rowsC = []
    for e in comps:
        pr = e.extra.get("proposal")
        prop = ("%s: %s" % (pr.get("label", ""), pr.get("why", ""))) if pr else "–"
        rowsC.append(([e.id + (" +" if e.status == "proposed" else ""), e.name, e.extra.get("state_cz") or im.STATUS_CZ[e.status],
                       e.where, e.extra.get("bay") or "–", e.extra.get("access") or "–", e.extra.get("replace") or "–",
                       (e.extra.get("note") or "–").rstrip(".") + ".", prop, sheet_of.get(e.room, "")],
                      STATUS_COL["proposed"] if pr or e.status == "proposed" else STATUS_COL[e.status]))
    y = ds.table(sh, 30.0, y - 5.0, "KOMPONENTY LODI (%d)" % len(comps), colsC, rowsC, size=2.2, rowh=4.1)
    objs = sorted((e for e in m.elements if e.cat == "object" and e.room), key=lambda e: (order.index(e.room), e.id))
    colsO = [("ID", 30, "left"), ("objekt / vybavení", 40, "left"), ("zdroj dat", 44, "left"), ("umístění", 70, "left", 2),
             ("účel", 230, "left", 2), ("list", 14, "left")]
    rowsO = [([e.id + (" ×" if e.status == "remove" else ""), e.name[:1].upper() + e.name[1:],
               {"layout.objects": "layout", "interior.kit.fittings": "vybavení lodi", "interior.decals.grab_bars": "madlo lodi",
                "hs_interior.stairs": "stavba lodi"}.get(e.src.split("[")[0], e.src.split("[")[0]), e.where,
               e.purpose + (" – nestaví se: místnost staví kit" if e.status == "remove" else ""), sheet_of.get(e.room, "")],
              STATUS_COL[e.status]) for e in objs]
    ds.table(sh, 30.0, y - 5.0, "OBJEKTY A VYBAVENÍ LODI (%d)" % len(objs), colsO, rowsO, size=2.2, rowh=4.1)
    rs.schedules = {"doors": {e.id for e in doors}, "furniture": {e.id for e in furn}, "components": {e.id for e in comps},
                    "objects": {e.id for e in objs if e.status != "remove"}}
    x0 = 590.0
    sh.t(x0, 575.0 - 3.4, "LEGENDA A POZNÁMKY", 3.4, weight="bold")
    yy = 575.0 - 10.0
    for col, txt in ((INK, "černě = postaveno (je v datech stavby)"), (STATUS_COL["proposed"], "modře, ID s + = návrh ke schválení autorem"),
                     (STATUS_COL["remove"], "červeně, ID s × = v datech, ale nestaví se (místnost staví kit)")):
        sh.line([(x0, yy + 0.8), (x0 + 10, yy + 0.8)], 0.6, col)
        sh.t(x0 + 13, yy, txt, 2.4, col)
        yy -= 4.6
    for ln in ("Rozměry a souřadnice v metrech: x od zádi trupu k přídi, y + k levoboku / − k pravoboku, z od podlahy hlavní "
               "paluby (podlaha kokpitu +1,15, pod podlahou záporné z).",
               "Řazení: dveře od zádi; ostatní po místnostech od zádi (náklad, chodba, kajuta, kokpit).",
               "Otevřené body a kolize jsou v kontrole dat na listech místností: I-02 (průchod u mřížky, nádrž), I-03 (výklenky "
               "proti layoutu, křídla DR-TEC-CAB), I-05 (avionika, plošina), I-01 (souhrn).",
               "Zdroj dat: layout = Design/Wayfarer_layout.json, vybavení lodi = recept interiéru, stavba lodi = stavitel "
               "interiéru (schody)."):
        for j, part in enumerate(ds.wrap(sh, ln, 2.4, 230, 3)):
            sh.t(x0 + (0 if j == 0 else 3), yy, part, 2.4)
            yy -= 3.8
        yy -= 1.0
    rs.checks = []
    dis.title_block(rs, sh.w - 389.0, sh.w, "I-09")
    return finish(rs, "I-09", dpi, out_dir, [], registry=True)


# ---------------------------------------------------------------------- shared
def legend_notes(rs, x, ytop, notes, lights=False):
    sh = rs.sh
    y = dis.legend(rs, x, ytop, ncol=1, lights=lights, other=(), cut_text="řez (půdorys 1,20 m nad podlahou)") \
        if lights else dd.legend(rs, x, ytop)
    if not lights:
        decal_marker(sh, x + 5, y - 1.0, 1.4)
        sh.t(x + 15, y - 1.8, "nápis nebo decal (kosočtverec v jeho poloze)", 2.2)
        y -= 7.0
    sh.t(x, y - 3, "POZNÁMKY", 3.4, weight="bold")
    y -= 9
    for k, ln in enumerate(notes):
        for j, part in enumerate(ds.wrap(sh, "%d. %s" % (k + 1, ln), 2.2, 140, 5)):
            sh.t(x + (0 if j == 0 else 3), y, part, 2.2)
            y -= 3.5
    rs.checks = []
    dis.title_block(rs, 800.0, sh.w, rs.sheet_code)


def finish(rs, sheet, dpi, out_dir, views, registry=False):
    m = rs.m
    out_dir = out_dir or os.path.join(im.ROOT, "ArtSource", "Ships", m.ship, "Design", "Drawings")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, "%s_%s" % (m.ship, SHEETS[sheet][0]))
    pdf_dir = os.path.join(im.ROOT, "Saved", "Drawings")
    os.makedirs(pdf_dir, exist_ok=True)
    side = {
        "_comment": "Written by Tools/Design/draw_interior_plans.py: the IDs this sheet draws and labels per view and lists "
                    "per schedule, with the digests of the data it was drawn from (Tools/Tests/test_interior_drawing.py).",
        "sheet": sheet, "ship": m.ship, "room": None, "digests": m.digests, "geometry": m.geometry_digests(),
        "drawn": {k: sorted(v) for k, v in rs.drawn.items()},
        "labelled": {k: sorted(i for i in v if not i.startswith("#")) for k, v in rs.d.labelled.items()},
        "schedules": {k: sorted(v) for k, v in rs.schedules.items()}, "checks": [],
    }
    if views:
        side.update({"deck": "main", "deck_views": views, "section_y": dd.SECTION_Y})
    if registry:
        side["registry"] = True
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(side, f, ensure_ascii=False, indent=1)
    rs.sh.save(base + ".png", dpi, os.path.join(pdf_dir, os.path.basename(base) + ".pdf"))
    print("INTSHEET %s wrote %s.png (%d dpi) and .json, PDF in Saved/Drawings" % (sheet, os.path.relpath(base, im.ROOT), dpi))
    return base


def draw(ship="Wayfarer", dpi=200, out_dir=None, sheets=None):
    ds.setup_fonts()
    m = im.Model(ship)
    if not m.geometry_ready():
        raise SystemExit("the FBX files are Git LFS pointers here (git lfs pull): the interior sheets draw the built meshes")
    geo = dis.Geo(m)
    out = []
    for sheet, fn in (("I-07", draw_decals), ("I-08", draw_lights), ("I-09", draw_schedules)):
        if sheets and sheet not in sheets:
            continue
        dd.DeckSheet.sheet_code = sheet
        out.append(fn(m, geo, dpi, out_dir))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ship", nargs="?", default="Wayfarer")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--sheets", nargs="*")
    a = ap.parse_args(argv)
    draw(a.ship, a.dpi, sheets=a.sheets)


if __name__ == "__main__":
    main()
