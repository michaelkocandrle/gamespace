"""Exterior sheets E-03 to E-08 of a ship (dossier point 3, author 1. 10. 2026: the rest of the six views and the
details in the style of the approved sample sheet E-01), drawn by Tools/Design/draw_exterior_sheet.py from the views
of the exterior model (Tools/Design/exterior_views.py):

  E-03  from above 1:30      E-04  from below 1:30      E-05  from behind and ahead 1:20
  E-06  port side 1:30 (views A and B as on E-01, mirrored; the port lettering check)
  E-07  details: nose with the canopy 1:20, aft wall with the ramp 1:10, the pod from above 1:20
  E-08  details: main gear 1:10 (its parts as hs_gear builds them), gun mount at the wing tip 1:10 with section 1:5

Every view draws exactly the elements the model has in it and labels each with its ID (sidecar JSON per sheet,
Tools/Tests/test_exterior_drawing.py). Tables of all elements stay on E-02; the material legend is on E-01 and
repeated where there is room.
"""
import math

from matplotlib.patches import Circle
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import draw_exterior_sheet as ds
import exterior_model as em
from draw_exterior_sheet import GREY, INK, PT, STATUS_COL, TITLE_MM, Drawer, Frame, Sheet

S30 = 1000.0 / 30.0
S20 = 1000.0 / 20.0
S10 = 1000.0 / 10.0
S5 = 1000.0 / 5.0


def view_title(sh, x, y, text, scale):
    sh.t(x, y, text, TITLE_MM, weight="bold")
    sh.t(x + sh.width(text, TITLE_MM, "bold") + 12, y, scale, TITLE_MM)


def side_notes(sh, m, x, ytop, title, lines, width=372.0):
    sh.t(x, ytop - 3, title, 3.4, weight="bold")
    y = ytop - 9
    for ln in lines:
        for k, part in enumerate(ds.wrap(sh, ln, 2.5, width, 4)):
            sh.t(x + (0 if k == 0 else 4), y, part, 2.5)
            y -= 4.0
    return y - 2


def sheet_list(sh, x, y):
    sh.t(x, y, "LISTY EXTERIÉRU", 3.0, weight="bold")
    y -= 5
    for code, (_, title) in ds.SHEETS.items():
        sh.t(x, y, code, 2.5, weight="bold")
        sh.t(x + 14, y, title, 2.5)
        y -= 4.0
    return y


def hidden_note(sh, m, d, view, x, y, width=372.0):
    """The view's elements hidden behind a nearer solid (drawn dashed), as a line of IDs."""
    hid = sorted(e.id for e in m.elements if e.sb and e.sb["hidden"] and e.cat != "panel")
    if not hid:
        return y
    txt = "Skryté za bližším tělesem (čárkovaně): " + ", ".join(hid) + "."
    for k, part in enumerate(ds.wrap(sh, txt, 2.3, width, 6)):
        sh.t(x, y, part, 2.3, GREY)
        y -= 3.6
    return y - 2


def dims_plan(sh, fr, m, view):
    """Overall length (pod tail to nose), span (gun tip to gun tip) and hull width of a plan view; metre ticks
    below the view, the length dimension under them (its text clear of the tick numbers)."""
    w = 7.35
    y = fr.P(0, -w)[1] - 11.0
    ds.dim_h(sh, fr.P(-0.5, 0)[0], fr.P(21.0, 0)[0], y, "21,50 (gondola -0,50 … příď 21,00)", fr.P(-0.5, -4.35)[1],
             fr.P(21.0, 0)[1])
    xr = fr.P(21.0, 0)[0] + 14
    ds.dim_v(sh, xr, fr.P(0, -7.35)[1], fr.P(0, 7.35)[1], "14,70 rozpětí (konce zbraní)", fr.P(12.6, -7.15)[0],
             fr.P(12.6, 7.15)[0])
    xl = fr.P(-0.5, 0)[0] - 8
    ds.dim_v(sh, xl, fr.P(0, -2.3)[1], fr.P(0, 2.3)[1], "4,60 trup", fr.P(0.0, -2.3)[0] - 3, fr.P(0.0, 2.3)[0] - 3)
    for x in range(0, 22):
        X, Y = fr.P(x, -w)
        sh.line([(X, Y - 1.0), (X, Y - 2.5)], 0.18, GREY)
        if x % 2 == 0:
            sh.t(X, Y - 5.4, "%d" % x, 2.2, GREY, ha="center")


def axis_note(sh, fr, view):
    """The centre line and which side is which."""
    X0, Y = fr.P(-0.9, 0)
    X1, _ = fr.P(21.4, 0)
    sh.line([(X0, Y), (X1, Y)], 0.18, GREY, ls="-.", z=21)
    up, dn = ("levobok", "pravobok") if view == "TOP" else ("pravobok", "levobok")
    sh.t(X1 + 1.5, Y + 3.0, up + " ↑", 2.5, GREY)
    sh.t(X1 + 1.5, Y - 5.0, dn + " ↓", 2.5, GREY)


def plan_sheet(m, dpi, out_dir, view, sheet, title, notes_lines):
    """E-03 / E-04: one plan view at 1:30 with its labels, dimensions, notes, legend and the title block."""
    sh = Sheet()
    d = Drawer(sh, m)
    W = sh.w
    ds.frame_and_zones(sh)
    m.use_view(view)
    try:
        X0 = 70.0
        Yc = 530.0
        fr = Frame(X0, Yc, S30)
        view_title(sh, 34, 822, title, "1 : 30")
        reqs = d.view_any(fr, view)
        hidden_panels, preqs = d.panel_labels(fr, view)
        d.place_labels(view, reqs + preqs + d.hidden_panel_reqs(fr, hidden_panels), 34, 776,
                       tiers_up=[789, 798.5, 808], tiers_dn=[262, 252.5, 243], split_y=Yc, bus_up=782.0, bus_dn=270.0)
        dims_plan(sh, fr, m, view)
        axis_note(sh, fr, view)
        ds.legend(sh, m, 34, 232)
        y = side_notes(sh, m, 800, 808, "POZNÁMKY K POHLEDU", notes_lines)
        y = hidden_note(sh, m, d, view, 800, y)
        sheet_list(sh, 800, y - 4)
        ds.title_block(sh, m, 800, W, sheet)
        return ds.save_sheet(sh, m, d, sheet, dpi, out_dir)
    finally:
        m.use_view("SB")


def common(legend_here):
    return [
        "1. Kreslí skript z dat stavby a dat návrhu (jeden zdroj dat); ID na výkresu = ID v datech; tabulky všech prvků "
        "jsou na E-02, legenda materiálů a značek na E-01" + (" (zde zopakovaná)." if legend_here else "."),
        "2. Zrcadlené prvky jsou nakreslené na obou stranách a mají jedno ID; popisek ukazuje na jednu kopii. Odstraněný "
        "díl: červený čárkovaný obrys s křížkem v rohu (nový díl na témže místě zůstává čitelný).",
    ]


def draw_e03(m, dpi, out_dir):
    return plan_sheet(m, dpi, out_dir, "TOP", "E-03", "SHORA – HŘBET, ZKOSENÍ, KŘÍDLA A GONDOLY", common(True) + [
        "3. Příď vpravo, levobok nahoře. Prvky boku, které leží na horním zkosení trupu (výška řezu nad 0,77), jsou "
        "promítnuté i sem: desky pásu S, podélník FR-LONG-HI, žebra FR-RIB, světla a nápisy na zkosení.",
        "4. Šipka u nápisu = směr čtení. Nápis na hřbetu se čte od bližšího boku (kopie u levoboku od levoboku, "
        "na ose od pravoboku), otočení „rot“ kolem normály (hs_decals).",
        "5. Ploutve kryjí gondolu, gondoly kryjí křídla; náběžné hrany tmavé, klapky obrysem (podíl tětivy z receptu).",
        "6. Záďový kryt Z-B-02 a deska P-B-01 jsou v datech „výška nad 2,2 m“ na zádi: střecha k zádi klesá (na zádi "
        "1,82 m), proto mají v půdorysu šikmou hranu po vrstevnici 2,2 m, ne obdélník.",
        "7. Hřbet mezi zkoseními: schválená změna P-HULL (plášť gunmetal = rám B + C) ho dělá tmavým, desky jsou jen na "
        "bocích a zkoseních; na střeše zůstávají postavené světlé pláty P-B-04/16/17 a žlab rozvodů R-B-02. K rozhodnutí "
        "autora: nechat, desky i na hřbet, nebo hřbet v laku.",
        "8. Karty špíny se nekreslí (tabulka E-02).",
    ])


def draw_e04(m, dpi, out_dir):
    return plan_sheet(m, dpi, out_dir, "BOT", "E-04", "ZESPODU – BŘICHO, PODVOZEK A RAKETNICE", common(True) + [
        "3. Pohled zespodu: příď vpravo, pravobok nahoře. Prvky boku na spodním zkosení (výška řezu pod 0,18) jsou "
        "promítnuté i sem: desky pásu K, podélník FR-LONG-LO, žebra FR-RIB.",
        "4. Podvozek vysunutý; raketnice a podvozek kryjí gondolu a trup, gondoly kryjí křídla. Desky skryté nad "
        "podvozkem mají tečkovaný odkaz; hlavní podvozek podrobně E-08 detail D.",
        "5. Šipka u nápisu = směr čtení (od bližšího boku). Karty špíny se nekreslí (tabulka E-02).",
    ])


def end_levels(sh, fr, x_paper):
    for z, name in ((0.0, "±0,00 paluba"), (-1.6, "-1,60 zem"), (3.3, "+3,30 střecha")):
        _, Y = fr.P(0, z)
        sh.line([(x_paper - 2, Y), (x_paper + 14, Y)], 0.18, INK)
        sh.t(x_paper - 2, Y + 0.8, name, 2.2)


def draw_e05(m, dpi, out_dir):
    """E-05: from behind (aft wall with the ramp, its frame and pistons, nozzles, aft markings) and from ahead, both
    at 1:20."""
    sh = Sheet()
    d = Drawer(sh, m)
    W = sh.w
    ds.frame_and_zones(sh)
    try:
        m.use_view("AFT")
        Xc = 413.5
        frA = Frame(Xc, 585.5, S20)
        view_title(sh, 34, 822, "ZEZADU – ZADNÍ STĚNA S RAMPOU, TRYSKY, ZÁĎ", "1 : 20")
        reqs = d.view_any(frA, "AFT")
        d.place_labels("AFT", reqs, 34, 790, tiers_up=[789, 798.5, 808], tiers_dn=[488, 478.5], split_y=frA.P(0, 1.2)[1],
                       bus_up=782.0, bus_dn=496.0)
        y = frA.P(0, -1.6)[1]
        ds.dim_h(sh, frA.P(-7.35, 0)[0], frA.P(7.35, 0)[0], y - 4.0, "14,70 rozpětí", frA.P(-7.35, 0.55)[1],
                 frA.P(7.35, 0.55)[1])
        end_levels(sh, frA, 36)
        sh.t(frA.P(7.35, 0)[0] + 2, frA.P(0, 3.6)[1], "pravobok →", 2.5, GREY)
        m.use_view("FWD")
        frF = Frame(Xc, 233.5, S20)
        view_title(sh, 34, 470, "ZEPŘEDU – ČELO, KABINA, SÁNÍ", "1 : 20")
        reqs = d.view_any(frF, "FWD")
        d.place_labels("FWD", reqs, 34, 790, tiers_up=[438, 447.5], tiers_dn=[136, 126.5], split_y=frF.P(0, 1.2)[1],
                       bus_up=431.0, bus_dn=144.0)
        end_levels(sh, frF, 36)
        sh.t(frF.P(7.35, 0)[0] + 2, frF.P(0, 3.6)[1], "levobok →", 2.5, GREY)
        y = side_notes(sh, m, 800, 808, "POZNÁMKY K POHLEDŮM", common(False) + [
            "3. Zezadu: pravobok vpravo; zadní stěna (řez trupu na zádi) šedým obrysem, rampa: spára D-T-05 čerchovaně, "
            "kolem ní navržený rám F-RAMP-FRAME (gunmetal), písty F-RAMP-PISTON. Gondoly stojí před zádí, kryjí kořen "
            "ploutví a křídel. Podrobně E-07 detail C.",
            "4. Zepředu: levobok vpravo; kabina se sklem, nos (Z-B-01) a sání gondol. Prvky boku a hřbetu jsou "
            "z čela vidět jen hranou: ty kreslí pravobok (E-01), levobok (E-06) a půdorysy (E-03, E-04).",
            "5. Šipka u nápisu na zadní stěně = směr čtení (osa x nápisu napříč lodí, vzhůru nahoru).",
        ])
        m.use_view("AFT")
        y = hidden_note(sh, m, d, "AFT", 800, y)
        sheet_list(sh, 800, y - 4)
        ds.title_block(sh, m, 800, W, "E-05")
        return ds.save_sheet(sh, m, d, "E-05", dpi, out_dir)
    finally:
        m.use_view("SB")


def draw_e06(m, dpi, out_dir):
    """E-06: the port side, views A (plates, materials) and B (parts, lights, decals) as on E-01, mirrored (nose
    left), with the port-only markings and the reading check of the port lettering."""
    sh = Sheet()
    d = Drawer(sh, m)
    W = sh.w
    ds.frame_and_zones(sh)
    try:
        m.use_view("PORT")
        OX = 60.0 + 21.0 * S30          # paper x of model x 0: the nose (x 21) at 60 mm
        zA = 768.0 - 3.81 * S30
        frA = Frame(OX, zA, S30, flip=True)
        view_title(sh, 34, 822, "A   LEVOBOK – DESKY A MATERIÁLOVÉ ZÓNY", "1 : 30")
        reqsA = d.view_materials(frA, "PA", label_pod_plates=True)
        hiddenA, panel_reqs = d.panel_labels(frA, "PA")
        d.place_labels("PA", reqsA + panel_reqs + d.hidden_panel_reqs(frA, hiddenA), 34, 786, tiers_up=[797, 806.5],
                       tiers_dn=[558, 549], split_y=zA + 1.4 * S30, bus_up=789.0, bus_dn=564.5)
        ds.levels(sh, frA)
        zB = 486.0 - 3.81 * S30
        frB = Frame(OX, zB, S30, flip=True)
        view_title(sh, 34, 531, "B   LEVOBOK – FUNKČNÍ PRVKY, SVĚTLA A DECALY", "1 : 30")
        reqsB = d.view_items(frB, "PB")
        ds.metre_ticks(sh, frB)
        ds.levels(sh, frB)
        d.place_labels("PB", reqsB, 34, 786, tiers_up=[503, 512.5, 522], tiers_dn=[287, 277.5, 268],
                       split_y=zB + 1.25 * S30, bus_up=495.0, bus_dn=296.0)
        y = side_notes(sh, m, 800, 808, "POZNÁMKY K POHLEDU", common(False)[:1] + [
            "2. Levobok je zrcadlo pravoboku (příď vlevo): desky, pole a stanice mají stejná čísla jako na E-01, "
            "detail gondoly je E-01 detail A. Desky skryté za křídlem a raketnicí mají tečkovaný odkaz.",
            "3. Nápisy z receptu (D-H) mají na každé straně vlastní rám (hs_decals): na levoboku se čtou stejně jako na "
            "pravoboku, šipka nahoru. Velké nápisy z nastavení UE mají levoboční kopie s vlastním ID (D-*-L) – "
            "tabulka vpravo.",
            "4. Pravoboční kopie (D-*-R) tu nejsou; prvky obrácené k trupu (mezera gondola–trup) jen v tabulce E-02.",
            "5. Odstraněný díl: červený čárkovaný obrys s křížkem v rohu; kde ho nahrazuje nový (mřížka F-GRILLE místo "
            "větráků G-VT a bloků RCS), je nový díl kreslený přes něj a v tabulce změn E-02 je, co čím nahrazuje.",
        ])
        y -= 2
        sh.t(800, y, "KONTROLA NÁPISŮ LEVOBOKU", 3.0, weight="bold")
        y -= 3
        rows = []
        for e in m.elements:
            if e.cat == "decal" and e.extra.get("setup") and e.sb and e.extra.get("text"):
                up = e.extra.get("up", (0, 1))
                ok = up[1] > 0.5
                rows.append(([e.id, ds.BIG_DECAL_CZ.get(e.extra["item"], e.extra["item"]), e.where + (" Δ" if e.change else ""),
                              "čte se" if ok else "VZHŮRU NOHAMA"], INK if ok else STATUS_COL["remove"]))
        cols = [("ID", 40, "left"), ("nápis", 40, "left"), ("umístění", 50, "left"), ("výsledek", 40, "left")]
        y = ds.table(sh, 800, y, "", cols, rows) - 6
        sheet_list(sh, 800, y)
        ds.title_block(sh, m, 800, W, "E-06")
        return ds.save_sheet(sh, m, d, "E-06", dpi, out_dir)
    finally:
        m.use_view("SB")


# ---------------------------------------------------------------------------------------------------- details
def detail_window(sh, d, m, key, view, win, sc, origin, title, scale, ups, dns, title_y=None, label_x=None):
    """One detail: a window of a view at a larger scale with every element whose anchor lies in it labelled.
    Returns the frame and the window's paper rectangle."""
    m.use_view(view)
    px, py = origin
    fr = Frame(px - win[0] * sc, py - win[1] * sc, sc, win)
    X0, Y0 = fr.P(win[0], win[1])
    X1, Y1 = fr.P(win[2], win[3])
    view_title(sh, px, title_y if title_y is not None else ups[-1] + 12, title, scale)
    wbox = box(*win)
    if view == "SB":
        reqs = d.view_materials(fr, key)
        reqs += d.view_items(fr, key, only=lambda e: wbox.intersects(e.sb["shape"]))
    else:
        reqs = d.view_any(fr, key)
    keep, seen = [], set()
    for r in reqs:
        ax_, ay_ = r["anchor"]
        if X0 + 0.5 <= ax_ <= X1 - 0.5 and Y0 + 0.5 <= ay_ <= Y1 - 0.5 and r["id"] not in seen:
            seen.add(r["id"])
            keep.append(r)
    d.drawn[key] = {r["id"] for r in keep}
    sh.rect(X0, Y0, X1, Y1, ec=INK, lw=0.35, z=44)
    lx0, lx1 = label_x if label_x else (px - 6, X1 + 6)
    d.place_labels(key, keep, lx0, lx1, tiers_up=ups, tiers_dn=dns, split_y=(Y0 + Y1) / 2, bus_up=Y1 + 3.5,
                   bus_dn=Y0 - 3.5)
    return fr, (X0, Y0, X1, Y1)


def dim_chain(sh, fr, xs, y_model, y_paper_off, fmt=None, ext_from=None):
    """A chain dimension along x through the model points xs, drawn y_paper_off mm from y_model."""
    _, Yb = fr.P(0, y_model)
    y = Yb + y_paper_off
    for x in xs:
        X, _ = fr.P(x, 0)
        ya = fr.P(0, ext_from)[1] if ext_from is not None else Yb
        sh.line([(X, ya), (X, y + (-1.8 if y_paper_off < 0 else 1.8))], 0.13, INK, z=20)
    for a, b in zip(xs, xs[1:]):
        Xa, Xb = fr.P(a, 0)[0], fr.P(b, 0)[0]
        sh.ax.annotate("", xy=(Xa, y), xytext=(Xb, y), zorder=20, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t((Xa + Xb) / 2, y + 0.8, (fmt or em.fmt)(abs(b - a)), 2.3, ha="center", bg="white", z=21)


def dim_vert(sh, fr, zs, x_model, x_paper_off, ext_from=None):
    """A chain dimension along z through the model heights zs, x_paper_off mm beside x_model."""
    Xb, _ = fr.P(x_model, 0)
    x = Xb + x_paper_off
    for z in zs:
        _, Y = fr.P(0, z)
        xa = fr.P(ext_from, 0)[0] if ext_from is not None else Xb
        sh.line([(xa, Y), (x + (1.8 if x_paper_off > 0 else -1.8), Y)], 0.13, INK, z=20)
    for a, b in zip(zs, zs[1:]):
        Ya, Yb_ = fr.P(0, a)[1], fr.P(0, b)[1]
        sh.ax.annotate("", xy=(x, Ya), xytext=(x, Yb_), zorder=20, arrowprops=dict(
            arrowstyle="<|-|>", lw=0.18 * PT, color=INK, mutation_scale=4, shrinkA=0, shrinkB=0))
        sh.t(x - 0.8, (Ya + Yb_) / 2, em.fmt(abs(b - a)), 2.3, ha="right", va="center", rot=90, bg="white", z=21)


def draw_e07(m, dpi, out_dir):
    """E-07: details - nose with the canopy (1:20), aft wall with the ramp (1:10), the pod from above (1:20)."""
    sh = Sheet()
    d = Drawer(sh, m)
    W = sh.w
    ds.frame_and_zones(sh)
    try:
        frB, (X0, Y0, X1, Y1) = detail_window(sh, d, m, "DB", "SB", (14.6, -0.75, 21.35, 3.45), S20, (40.0, 545.0),
                                              "DETAIL B – PŘÍĎ S KABINOU", "1 : 20", [783, 792.5], [522, 512.5])
        cz = m.canopy.bounds
        dim_chain(sh, frB, [cz[0], cz[2], 21.0], 3.45, 3.0, ext_from=3.3)
        dim_vert(sh, frB, [-0.6, m.canopy_lower(17.6), 3.3], 21.35, 4.0, ext_from=19.0)
        sh.t(X0, Y0 - 24.5, "kóty: sklo kabiny z boku x %s–%s, od skla ke špičce nosu (x 21,00); výška od dna trupu "
             "(-0,60) k patě skla na x 17,6 a od paty skla ke střeše (+3,30)" % (em.fmt(cz[0]), em.fmt(cz[2])), 2.3,
             bg="white", z=22)
        frC, _ = detail_window(sh, d, m, "DC", "AFT", (-2.45, -0.75, 2.45, 2.35), S10, (650.0, 470.0),
                               "DETAIL C – ZADNÍ STĚNA S RAMPOU", "1 : 10", [783, 792.5, 802], [450, 440.5])
        fr_ = m.by_id["F-RAMP-FRAME"].data
        dim_chain(sh, frC, [-1.18, -1.15, 1.15, 1.18], -0.75, -6.0, ext_from=-0.12)
        dim_chain(sh, frC, [fr_["y"][0], fr_["y"][1]], -0.75, -12.0, ext_from=-0.12)
        dim_vert(sh, frC, [-0.12, 1.35, fr_["z"][1]], 2.45, -6.0, ext_from=1.2)
        sh.t(frC.P(0, -0.75)[0], frC.P(0, -0.75)[1] - 16.5, "spára rampy 2,30 × 1,47; písty po 2,36; rám vně spáry, "
             "profil 80 mm", 2.3, ha="center", bg="white", z=22)
        detail_window(sh, d, m, "DF", "TOP", (-0.65, 2.2, 6.05, 4.55), S20, (40.0, 300.0),
                      "DETAIL F – GONDOLA SHORA", "1 : 20", [430, 439.5], [283, 273.5], title_y=450)
        m.use_view("SB")
        y = side_notes(sh, m, 650, 405, "POZNÁMKY K DETAILŮM", common(False)[:1] + [
            "2. Detail ukazuje výřez pohledu ve větším měřítku a popisuje každý prvek, jehož kotva leží ve výřezu: B "
            "z pravoboku (E-01), C zezadu (E-05), F shora (E-03). Gondola s tryskou z boku je E-01 detail A (1:20); "
            "hlavní podvozek a držák zbraně E-08.",
            "3. Detail B: kabina se sklem (sklo jen tam, kde je trup uvnitř bočního i horního obrysu kabiny – jako ve "
            "stavbě), rám s příčkami F-CANOPY-FRAME, těsnění Z-SEAL-CANOPY, tmavá špička nosu Z-B-01, senzory, příďový "
            "podvozek.",
            "4. Detail C: spára rampy D-T-05, navržený rám F-RAMP-FRAME (nese závěsy a písty), písty F-RAMP-PISTON, "
            "pracovní světlo L-RAMP, zadní RCS (odstraněné) a nápisy zadní stěny se směrem čtení.",
            "5. Detail F: gondola shora – úseky pláště, pancíře, otevřená šachta F-POD-BAY s potrubím, ploutev se "
            "zábleskovou svítilnou L-STROBE-FIN; tryska je vidět jen zezadu (E-05).",
        ], width=520.0)
        sheet_list(sh, 650, y - 4)
        ds.title_block(sh, m, 800, W, "E-07")
        return ds.save_sheet(sh, m, d, "E-07", dpi, out_dir)
    finally:
        m.use_view("SB")


def gear_parts(spec, sign=-1):
    """The landing gear leg as Tools/Blender/hs_gear.leg builds it (its numbers, not a sketch), per part: Czech name,
    material, outline from starboard (x, z), outline from behind (u = -y, z) or None, hidden behind the leg door
    in the side view. sign -1: the starboard leg."""
    x, y, _ = spec["at"]
    y *= sign
    u = -y
    lx, ly, top, bot = spec["strut"]
    plx, ply, pz, ph = spec["pad"]
    out = 1 if y >= 0 else -1
    z_ob = top - 0.12 - (top - bot) * 0.5
    z_an = bot + 0.07
    mid = (z_ob + z_an) / 2
    pad_top = pz + ph

    def rect(cx, cz, w, h):
        return box(cx - w / 2, cz - h / 2, cx + w / 2, cz + h / 2)

    def line(pts, r):
        return LineString(pts).buffer(r, cap_style=1)

    door_u = u - out * (ly * 0.5 - 0.012)
    parts = [
        ("třmen s úchytem", "MZ-DARK", rect(x, top - 0.06, lx * 0.9, 0.12), rect(u, top - 0.06, ly * 0.9, 0.12), True),
        ("čep třmene", "MZ-METAL", Point(x, top - 0.1).buffer(0.045, 24), rect(u, top - 0.1, ly, 0.09), True),
        ("vnější válec tlumiče", "MZ-DARK", box(x - 0.11, z_ob, x + 0.11, top - 0.12), box(u - 0.11, z_ob, u + 0.11, top - 0.12), True),
        ("ucpávka", "MZ-METAL", box(x - 0.118, z_ob - 0.005, x + 0.118, z_ob + 0.03),
         box(u - 0.118, z_ob - 0.005, u + 0.118, z_ob + 0.03), False),
        ("leštěný píst", "MZ-METAL", box(x - 0.07, z_an + 0.03, x + 0.07, z_ob), box(u - 0.07, z_an + 0.03, u + 0.07, z_ob), False),
        ("nůžky (vzadu)", "MZ-METAL", line([(x - 0.09, z_ob - 0.01), (x - 0.19, mid), (x - 0.07, z_an + 0.06)], 0.016),
         unary_union([box(u + k - 0.016, z_an + 0.06, u + k + 0.016, z_ob - 0.01) for k in (-0.03, 0.03)]), False),
        ("objímka pístu", "MZ-DARK", box(x - 0.09, z_an + 0.04, x + 0.09, z_an + 0.09), box(u - 0.09, z_an + 0.04, u + 0.09, z_an + 0.09), False),
        ("vzpěra (vpředu)", "MZ-DARK", line([(x + lx * 0.4, top - 0.1), (x + 0.1, (top - 0.12 + z_ob) / 2)], 0.028), None, True),
        ("hydraulika (2 trubky)", "MZ-DARK", line([(x + 0.12, top - 0.12), (x + 0.125, z_ob), (x + 0.085, z_an + 0.1)], 0.009),
         None, True),
        ("dvířka nohy (vně)", "MZ-PAINT1", box(x - lx / 2, z_ob, x + lx / 2, top - 0.02),
         box(door_u - 0.011, z_ob, door_u + 0.011, top - 0.02), False),
        ("výstražný pruh dvířek", "MZ-ORANGE", box(x - lx * 0.49, z_ob + 0.01, x + lx * 0.49, z_ob + 0.07),
         box(door_u - 0.012, z_ob + 0.01, door_u + 0.012, z_ob + 0.07), False),
        ("kotník (čep a blok)", "MZ-METAL", unary_union([Point(x, z_an).buffer(0.05, 24), box(x - 0.1, z_an - 0.07, x + 0.1, z_an + 0.01)]),
         unary_union([box(u - 0.09, z_an - 0.05, u + 0.09, z_an + 0.05), box(u - 0.08, z_an - 0.07, u + 0.08, z_an + 0.01)]), False),
        ("patka", "MZ-DARK", box(x - plx * 0.48, pz + 0.035, x + plx * 0.48, pad_top),
         box(u - ply * 0.48, pz + 0.035, u + ply * 0.48, pad_top), False),
        ("pryžová podrážka", "MZ-RUBBER", box(x - plx / 2, pz, x + plx / 2, pz + 0.035), box(u - ply / 2, pz, u + ply / 2, pz + 0.035), False),
        ("žebra patky (4)", "MZ-METAL", unary_union([box(x - plx * 0.3 + k * plx * 0.2 - 0.015, pad_top, x - plx * 0.3 + k * plx * 0.2 + 0.015,
                                                         pad_top + 0.02) for k in range(4)]),
         box(u - ply * 0.4, pad_top, u + ply * 0.4, pad_top + 0.02), False),
    ]
    return parts, {"x": x, "u": u, "top": top, "bot": bot, "z_ob": z_ob, "z_an": z_an, "pad": (plx, ply, pz, ph), "lx": lx,
                   "ly": ly, "door_u": door_u}


def balloon_column(sh, d, key, items, x_col, y_lo, y_hi, side="right"):
    """Numbered balloons in a column beside a view, leaders to the parts (items: (number, paper point))."""
    items = sorted(items, key=lambda t: -t[1][1])
    n = len(items)
    for k, (no, (ax_, ay_)) in enumerate(items):
        y = y_hi - (y_hi - y_lo) * (k + 0.5) / n
        sh.ax.add_patch(Circle((x_col, y), 2.1, fc="white", ec=INK, lw=0.2 * PT, zorder=40))
        sh.t(x_col, y, str(no), 2.2, ha="center", va="center", z=41)
        xs = x_col - 2.1 if side == "right" else x_col + 2.1
        sh.line([(xs, y), (ax_, ay_)], 0.13, INK, z=35)
        sh.ax.add_patch(Circle((ax_, ay_), 0.45, fc=INK, ec="white", lw=0.1 * PT, zorder=36))


def gear_detail(sh, d, m):
    """Detail D: the starboard main gear from the side and from behind at 1:10, its parts numbered (hs_gear), the
    belly round it from below; dimensions and the parts list."""
    e = m.by_id["F-GEAR-MAIN"]
    parts, g = gear_parts(e.data)
    sh_ = sh
    view_title(sh_, 40, 822, "DETAIL D – HLAVNÍ PODVOZEK (PRAVÝ)", "1 : 5")
    # ---- side view (starboard): the hull's underside as context, the leg; parts behind the door dashed
    fr = Frame(60.0 - 4.45 * S5, 520.0 + 1.7 * S5, S5, (4.45, -1.7, 5.95, -0.5))
    X0, Y0 = fr.P(4.45, -1.7)
    X1, Y1 = fr.P(5.95, -0.5)
    m.use_view("SB")
    hull = m.solids["hull"]["poly"]
    sh_.geom(fr.g(hull), fc="#7E848B", ec=INK, lw=0.35, z=2, hatch="x", hatch_col="#D0D0D0")
    sh_.t(X0 + 2, Y1 - 4, "trup (břicho, pás K)", 2.2, "white", z=30)
    balloons_s, balloons_r = [], []
    for k, (name, mat, side, rear, behind) in enumerate(parts, 1):
        fill, hatch, hc = d.matstyle(mat)
        if behind:
            sh_.geom(fr.g(side), fc="none", ec=INK, lw=0.22, ls="--", z=20)
        else:
            sh_.geom(fr.g(side), fc=fill, ec=INK, lw=0.3, z=10 + k * 0.1, hatch=hatch, hatch_col=hc)
        c = side.representative_point()
        balloons_s.append((k, fr.P(c.x, c.y)))
    sh_.rect(X0, Y0, X1, Y1, ec=INK, lw=0.35, z=44)
    sh_.t(X0, Y1 + 9, "z pravoboku (dvířka vpředu, za nimi čárkovaně)", 2.4, GREY)
    gx, ztop = g["x"], g["top"]
    plx, ply, pz, ph = g["pad"]
    dim_chain(sh_, fr, [gx - plx / 2, gx + plx / 2], -1.7, -5.0, ext_from=pz)
    dim_chain(sh_, fr, [gx - g["lx"] / 2, gx + g["lx"] / 2], -0.5, 4.0, ext_from=g["z_ob"])
    dim_vert(sh_, fr, [-1.6, pz + ph, g["z_ob"], ztop], 4.45, -5.0, ext_from=gx - plx / 2)
    balloon_column(sh_, d, "DD", balloons_s, X1 + 12, Y0 + 4, Y1 - 4)
    # ---- from behind
    fr2 = Frame(430.0 - (g["u"] - 0.6) * S5, 520.0 + 1.7 * S5, S5, (g["u"] - 0.6, -1.7, g["u"] + 0.6, -0.5))
    A0, B0 = fr2.P(g["u"] - 0.6, -1.7)
    A1, B1 = fr2.P(g["u"] + 0.6, -0.5)
    m.use_view("AFT")
    sh_.geom(fr2.g(m.solids["hull"]["poly"]), fc="#7E848B", ec=INK, lw=0.35, z=2, hatch="x", hatch_col="#D0D0D0")
    for k, (name, mat, side, rear, behind) in enumerate(parts, 1):
        if rear is None:
            continue
        fill, hatch, hc = d.matstyle(mat)
        sh_.geom(fr2.g(rear), fc=fill, ec=INK, lw=0.3, z=10 + k * 0.1, hatch=hatch, hatch_col=hc)
        c = rear.representative_point()
        balloons_r.append((k, fr2.P(c.x, c.y)))
    sh_.rect(A0, B0, A1, B1, ec=INK, lw=0.35, z=44)
    sh_.t(A0, B1 + 9, "zezadu (pravobok vpravo)", 2.4, GREY)
    dim_chain(sh_, fr2, [g["u"] - ply / 2, g["u"] + ply / 2], -1.7, -5.0, ext_from=pz)
    sh_.t(A0, B0 - 13, "osa nohy %s m od osy lodi (pravobok)" % em.fmt(g["u"]), 2.3)
    balloon_column(sh_, d, "DD", balloons_r, A1 + 12, B0 + 4, B1 - 4)
    m.use_view("SB")
    # ---- parts list
    rows = [([str(k), name, m.materials[mat]["name"]], INK) for k, (name, mat, side, rear, behind) in enumerate(parts, 1)]
    ds.table(sh_, 980, 808, "ČÁSTI F-GEAR-MAIN (hs_gear.leg)", [("č.", 8, "left"), ("část", 52, "left"),
                                                                    ("materiál", 40, "left")], rows, size=2.3, rowh=3.9)
    d.drawn.setdefault("DD", set()).add(e.id)
    d.labelled.setdefault("DD", set()).add(e.id)
    sh_.t(60, 496, "F-GEAR-MAIN (ks 2): noha vysunutá (zem -1,60); dvířka na vnější straně nohy kryjí z boku třmen, válec, "
                   "vzpěru a hydrauliku (čárkovaně).", 2.3)
    # ---- from below: the belly round the leg (the bay markings), a window of view E-04
    fr3, _ = detail_window(sh, d, m, "DD-BOT", "BOT", (4.25, 0.85, 6.15, 2.95), S10, (740.0, 545.0),
                           "zespodu: patka a nápisy u nohy", "1 : 10", [772, 781.5], [528, 518.5], title_y=795,
                           label_x=(712, 970))
    m.use_view("SB")


def gun_detail(sh, d, m):
    """Detail E: the gun at the wing tip from above (1:10) with its collars, and section A-A across a collar (1:5)
    showing how the gun sits on the wing tip."""
    gun = m.recipe["parts"]["gun"]["cylinders"]
    gm = m.by_id["F-GUNMOUNT-01"].data
    fr, (X0, Y0, X1, Y1) = detail_window(sh, d, m, "DE", "TOP", (5.75, 6.45, 12.85, 7.6), S10, (40.0, 300.0),
                                         "DETAIL E – KONCOVÝ DRŽÁK ZBRANĚ", "1 : 10", [428, 437.5], [262, 252.5],
                                         title_y=452)
    m.use_view("TOP")
    xs = [gun[0]["x"][0]] + gm["at"] + [gun[0]["x"][1], gun[1]["x"][1]]
    dim_chain(sh, fr, xs, 6.45, -4.0, ext_from=7.15)
    yb = gun[0]["y"]
    # section mark A-A at the middle collar
    xa = gm["at"][1]
    A, B = fr.P(xa, 7.6), fr.P(xa, 6.45)
    sh.line([(A[0], A[1] + 2), (B[0], B[1] - 2)], 0.25, INK, ls="-.", z=46)
    for P_ in (A, B):
        sh.t(P_[0] + 1.5, P_[1] + (2.5 if P_ is A else -5.0), "A", 3.0, weight="bold", z=46, bg="white")
    m.use_view("SB")
    # ---- section A-A (looking forward), 1:5: the wing's section at the tip, the gun and its collar
    win = (6.55, 0.4, 7.5, 1.1)
    fs = Frame(800.0 - win[0] * S5, 280.0 - win[1] * S5, S5, win)
    S0, T0 = fs.P(win[0], win[1])
    S1, T1 = fs.P(win[2], win[3])
    view_title(sh, 800, 452, "ŘEZ A–A (x %s, pohled dopředu)" % em.fmt(xa), "1 : 5")
    wing = Polygon(m.front["wing"]).buffer(0)
    fill, hatch, hc = d.matstyle("MZ-PAINT1")
    sh.geom(fs.g(wing), fc=fill, ec=INK, lw=0.35, z=4, hatch=hatch, hatch_col=hc)
    c = Point(yb, gun[0]["z"])
    r = gun[0]["r"]
    rc = gm["r"] + 0.03
    fill, hatch, hc = d.matstyle("MZ-DARK")
    sh.geom(fs.g(c.buffer(rc, 64).difference(c.buffer(r, 64))), fc=fill, ec=INK, lw=0.3, z=6, hatch=hatch, hatch_col=hc)
    sh.geom(fs.g(c.buffer(r, 64)), fc="#7A7F86", ec=INK, lw=0.35, z=5, hatch="//", hatch_col="#D0D0D0")
    sh.rect(S0, T0, S1, T1, ec=INK, lw=0.35, z=44)
    # dims: gun diameter, collar diameter, the axis from the wing tip, the overlap
    Cx, Cy = fs.P(yb, gun[0]["z"])
    ds.dim_h(sh, fs.P(yb - r, 0)[0], fs.P(yb + r, 0)[0], T0 + 8, "Ø %s zbraň" % em.fmt(2 * r), fs.P(0, gun[0]["z"])[1],
             fs.P(0, gun[0]["z"])[1])
    ds.dim_h(sh, fs.P(yb - rc, 0)[0], fs.P(yb + rc, 0)[0], T1 - 8, "Ø %s objímka" % em.fmt(2 * rc), fs.P(0, gun[0]["z"])[1],
             fs.P(0, gun[0]["z"])[1])
    wt = max(p[0] for p in m.front["wing"])
    ds.dim_h(sh, fs.P(wt, 0)[0], fs.P(yb, 0)[0], T0 + 16, "%s osa zbraně za koncem křídla" % em.fmt(yb - wt),
             fs.P(0, 0.85)[1], fs.P(0, gun[0]["z"])[1])
    sh.t(S0, T0 - 27, "křídlo (konec y %s), zbraň Ø %s s osou y %s: zbraň zasahuje %s m a objímka Ø %s %s m do konce "
                     "křídla – objímky ji drží na něm" % (em.fmt(wt), em.fmt(2 * r), em.fmt(yb), em.fmt(wt - (yb - r)),
                                                         em.fmt(2 * rc), em.fmt(wt - (yb - rc))), 2.3)
    sh.t(S0, T0 - 31, "tělo x %s–%s Ø %s · hlaveň x %s–%s Ø %s · ústí x %s–%s Ø %s · objímky x %s" % (
        em.fmt(gun[0]["x"][0]), em.fmt(gun[0]["x"][1]), em.fmt(2 * gun[0]["r"]), em.fmt(gun[1]["x"][0]),
        em.fmt(gun[1]["x"][1]), em.fmt(2 * gun[1]["r"]), em.fmt(gun[2]["x"][0]), em.fmt(gun[2]["x"][1]),
        em.fmt(2 * gun[2]["r"]), ", ".join(em.fmt(a) for a in gm["at"])), 2.3)
    for i in ("F-GUN-S3", "F-GUNMOUNT-01", "F-WING"):
        d.drawn.setdefault("DE-A", set()).add(i)
    reqs = [{"id": "F-WING", "text": "F-WING", "anchor": fs.P(6.75, 0.75), "col": INK, "z": 0, "hidden": False},
            {"id": "F-GUN-S3", "text": "F-GUN-S3", "anchor": fs.P(yb - 0.05, 0.7), "col": INK, "z": 0, "hidden": False},
            {"id": "F-GUNMOUNT-01", "text": "F-GUNMOUNT-01", "anchor": fs.P(yb + 0.1, 0.75 + 0.17), "col": INK, "z": 0,
             "hidden": False}]
    d.place_labels("DE-A", reqs, 800, 1100, tiers_up=[T1 + 22], tiers_dn=[T0 - 20], split_y=Cy, bus_up=T1 + 19,
                   bus_dn=T0 - 17)


def draw_e08(m, dpi, out_dir):
    """E-08: details D (main gear, 1:10: from the side and behind with its parts as hs_gear builds them, from below
    with the bay markings) and E (gun mount at the wing tip, 1:10, section A-A 1:5)."""
    sh = Sheet()
    d = Drawer(sh, m)
    W = sh.w
    ds.frame_and_zones(sh)
    try:
        gear_detail(sh, d, m)
        gun_detail(sh, d, m)
        m.use_view("SB")
        y = side_notes(sh, m, 40, 235, "POZNÁMKY K DETAILŮM", common(False)[:1] + [
            "2. Detail D: noha podvozku tak, jak ji staví hs_gear.leg (rozměry z obálky receptu gear_main: noha 0,40 × "
            "0,30, patka 1,20 × 0,80 × 0,15); čísla částí podle seznamu, z boku za dvířky čárkovaně. Zespodu výřez "
            "pohledu E-04 s nápisy u šachty.",
            "3. Detail E: zbraň S3 F-GUN-S3 na konci křídla, tři objímky F-GUNMOUNT-01; řez A–A ukazuje, že zbraň leží "
            "osou 0,15 m za koncem křídla, zasahuje do něj 3 cm a objímky 6 cm – objímky ji drží na konci křídla "
            "(pylon se nestaví).",
        ], width=740.0)
        sheet_list(sh, 40, y - 4)
        ds.title_block(sh, m, 800, W, "E-08")
        return ds.save_sheet(sh, m, d, "E-08", dpi, out_dir)
    finally:
        m.use_view("SB")
