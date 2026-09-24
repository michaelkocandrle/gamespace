"""Gamespace Ship Matrix: one HTML page with every ship of the fleet, like the RSI Ship Matrix, and a
design dossier per ship that shows how it was specified and designed, step by step.

    python Tools/Design/build_ship_matrix.py              # whole fleet -> Saved/Dossier/ShipMatrix.html
    python Tools/Design/build_ship_matrix.py --ship Wayfarer   # one ship -> Saved/Dossier/Wayfarer.html

Everything comes from the ship folders, nothing is typed twice:
  ArtSource/Ships/<Ship>/<Ship>_spec.json        Ship Matrix fields (old and new spec schema both read)
  ArtSource/Ships/<Ship>/Design/                 layout JSON, drawings, guides/<Ship>_mask_*.png
  ArtSource/Ships/<Ship>/Concept/dossier.json    optional: status line, card image, concept captions,
                                                 which concepts are the front/side/top check views,
                                                 open questions or the author's decisions
  the reference set named in the spec (_reference.set, from fetch_ship_matrix.py)
The silhouette numbers (design self-check, concepts against the drawing) are measured here, with
Tools/Blender/silhouette_compare.py, every time the page is built. Images are embedded as JPEG data
URIs, so the file publishes as a single Artifact (skill ship-pipeline, section 1b).
"""
import argparse
import base64
import glob
import html
import io
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SHIPS = os.path.join(ROOT, "ArtSource", "Ships")
sys.path.insert(0, os.path.join(ROOT, "Tools", "Blender"))
import silhouette_compare as sc  # noqa: E402

# Pipeline stages, in order (skill ship-pipeline section 0). Each is detected from the files.
STAGES = [
    ("reference", "Reference ze Ship Matrix"), ("spec", "Specifikace"), ("layout", "Layout a výkresy"),
    ("check", "Kontrola siluet"), ("concepts", "Koncepty"), ("approved", "Schváleno autorem"),
    ("model", "3D model"), ("unreal", "V Unrealu"), ("flight", "Létá ve hře"),
]
STATUS_LABEL = {"flight": "létá ve hře", "unreal": "v Unrealu", "model": "3D stavba", "approved": "návrh schválen",
                "concepts": "2D návrh", "check": "2D návrh", "layout": "2D návrh", "spec": "specifikace",
                "reference": "plán", None: "plán"}


def esc(s):
    return html.escape(str(s))


def uri(img_or_path, width=1400, quality=80):
    im = Image.open(img_or_path) if isinstance(img_or_path, str) else img_or_path
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (205, 208, 212))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    im = im.convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def fig(src, caption, cls="", width=1400):
    return '<figure class="%s"><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>' % (
        cls, uri(src, width), esc(caption), esc(caption))


def num(v):
    return v if isinstance(v, (int, float)) else None


def fmt(v, unit="", scale=1.0):
    v = num(v)
    if v is None:
        return "–"
    v = v / scale
    return ("%g" % round(v, 2)) + (" " + unit if unit else "")


# ------------------------------------------------------------------ data

def load_ship(name):
    d = os.path.join(SHIPS, name)
    spec = json.load(io.open(os.path.join(d, name + "_spec.json"), encoding="utf-8"))
    ident = spec.get("identity", {})
    dims = spec.get("dimensions", {})
    fl = spec.get("flight", {})
    crew = spec.get("crew", {})

    def opt(path):
        p = os.path.join(d, path)
        return p if os.path.exists(p) else None

    layout_p = opt("Design/%s_layout.json" % name)
    dossier_p = opt("Concept/dossier.json")
    s = {
        "name": ident.get("name") or ident.get("model") or name,
        "dir": d, "spec": spec,
        "maker": ident.get("manufacturer", "–"),
        "focus": ident.get("focus", "–"),
        "size": (ident.get("size") or ident.get("size_class") or "–").capitalize(),
        "desc": ident.get("description") or " ".join(spec.get("design_notes", [])[:1]),
        "L": dims.get("length_m"), "B": dims.get("beam_m"), "H": dims.get("height_m"),
        "mass": dims.get("mass_kg"), "scu": dims.get("cargo_capacity_scu", dims.get("cargo_capacity")),
        "crew": crew.get("max_crew", crew.get("crew_size")),
        "scm": fl.get("scm_speed_ms"), "ab": fl.get("afterburner_speed_ms"),
        "pitch": fl.get("pitch_max_deg_s"), "yaw": fl.get("yaw_max_deg_s"), "roll": fl.get("roll_max_deg_s"),
        "layout": json.load(io.open(layout_p, encoding="utf-8")) if layout_p else None,
        "dossier": json.load(io.open(dossier_p, encoding="utf-8")) if dossier_p else {},
        "drawings": sorted(glob.glob(os.path.join(d, "Design", name + "_*.png"))),
        "masks": {v: opt("Design/guides/%s_mask_%s.png" % (name, v)) for v in sc.VIEWS},
    }
    status = str(spec.get("_status", ""))
    done = {
        "reference": "_reference" in spec,
        "spec": True,
        "layout": bool(s["layout"] and s["drawings"]),
        "check": all(s["masks"].values()),
        "concepts": bool(s["dossier"].get("concepts")) or bool(glob.glob(os.path.join(d, "Concept", "*.png"))),
        "approved": "approved" in status,
        "model": bool(opt(name + "_setup.json") or glob.glob(os.path.join(d, "Export", "*_manifest.json"))),
        "unreal": os.path.isdir(os.path.join(ROOT, "Content", "Ships", name)),
        "flight": str(ident.get("production_status", "")).lower() == "flight-ready",
    }
    s["done"] = done
    last = None
    for key, _ in STAGES:
        if done[key]:
            last = key
    s["stage"] = last
    s["status"] = STATUS_LABEL[last]
    return s


def card_image(s):
    dz = s["dossier"]
    if dz.get("card"):
        return os.path.join(s["dir"], "Concept", dz["card"])
    for c in dz.get("concepts", []):
        return os.path.join(s["dir"], "Concept", c["file"])
    ext = [p for p in s["drawings"] if p.endswith("_exterior.png")]
    if ext:
        return ext[0]
    cons = glob.glob(os.path.join(s["dir"], "Concept", "*.png"))
    if cons:
        return cons[0]
    return s["drawings"][0] if s["drawings"] else None


def placeholder(s):
    """A card image for a ship with no picture yet: its L x B box to scale, as a drawing."""
    im = Image.new("RGB", (640, 400), (13, 18, 26))
    d = ImageDraw.Draw(im)
    for x in range(0, 640, 32):
        d.line([(x, 0), (x, 400)], fill=(24, 32, 44))
    for y in range(0, 400, 32):
        d.line([(0, y), (640, y)], fill=(24, 32, 44))
    L, B = num(s["L"]) or 10, num(s["B"]) or 8
    k = min(520 / L, 300 / B)
    w, h = L * k, B * k
    d.polygon([(320 - w / 2, 200 - h * 0.12), (320 + w / 2, 200), (320 - w / 2, 200 + h * 0.12)], outline=(150, 170, 190), width=3)
    d.line([(320 - w / 4, 200 - h / 2), (320 + w / 8, 200), (320 - w / 4, 200 + h / 2)], fill=(150, 170, 190), width=3)
    return im


# ------------------------------------------------------------------ silhouette numbers

def mask_sheet(masks):
    tiles = []
    for v in sc.VIEWS:
        m, _ = sc.normalise(masks[v])
        tiles.append((v, Image.fromarray((m * 255).astype("uint8")).convert("RGB")))
    sheet = Image.new("RGB", (sc.NORM * 3, sc.NORM + 36), (13, 18, 26))
    d = ImageDraw.Draw(sheet)
    names = {"front": "zepředu", "side": "z boku", "top": "shora"}
    for i, (v, t) in enumerate(tiles):
        sheet.paste(t, (i * sc.NORM, 36))
        d.text((i * sc.NORM + 10, 10), names[v], fill=(226, 232, 238))
    return sheet


def silhouette_checks(s):
    """Design self-consistency and, when the dossier names check views, concepts vs the drawing."""
    if not s["done"]["check"]:
        return None
    dims = [num(s["L"]), num(s["B"]), num(s["H"])]
    design = {v: sc.load_render_mask(s["masks"][v]) for v in sc.VIEWS}
    out = {"design": sc.view_consistency(design, dims if all(dims) else None), "design_sheet": mask_sheet(design)}
    check = s["dossier"].get("check_views")
    if check:
        cdir = os.path.join(s["dir"], "Concept")
        concept = {v: sc.extract_reference_mask(os.path.join(cdir, check[v])) for v in sc.VIEWS}
        out["concept"] = sc.view_consistency(concept, dims if all(dims) else None)
        per, tiles = {}, []
        for v in sc.VIEWS:
            st, m, r = sc.compare_masks(design[v], concept[v])
            per[v] = st
            tiles.append(sc.diff_image(m, r))
        sheet = Image.new("RGB", (sc.NORM * 3, sc.NORM), (18, 22, 30))
        for i, t in enumerate(tiles):
            sheet.paste(t, (i * sc.NORM, 0))
        out["per_view"], out["diff_sheet"] = per, sheet
    return out


def pct(v):
    return ("%.1f %%" % v).replace(".", ",")


def dec(v, n=2):
    return ("%.*f" % (n, v)).replace(".", ",")


# ------------------------------------------------------------------ html pieces

def pipeline_html(s):
    items = []
    for key, label in STAGES:
        cls = "done" if s["done"][key] else ""
        items.append('<li class="%s"><span></span>%s</li>' % (cls, esc(label)))
    return '<ol class="pipeline">%s</ol>' % "".join(items)


def spec_rows(s, med):
    def m(k, unit="", scale=1.0):
        return fmt(med.get(k), unit, scale) if med else ""
    rows = [
        ("Délka", fmt(s["L"], "m"), m("length_m", "m")), ("Šířka", fmt(s["B"], "m"), m("beam_m", "m")),
        ("Výška", fmt(s["H"], "m"), m("height_m", "m")), ("Hmotnost", fmt(s["mass"], "t", 1000), m("mass_kg", "t", 1000)),
        ("Náklad", fmt(s["scu"], "SCU"), m("cargo_scu", "SCU")), ("Posádka", fmt(s["crew"]), m("crew")),
        ("SCM", fmt(s["scm"], "m/s"), m("scm_ms", "m/s")), ("Afterburner", fmt(s["ab"], "m/s"), m("afterburner_ms", "m/s")),
        ("Pitch / yaw / roll", "%s / %s / %s °/s" % (fmt(s["pitch"]), fmt(s["yaw"]), fmt(s["roll"])),
         ("%s / %s / %s °/s" % (m("pitch_deg_s"), m("yaw_deg_s"), m("roll_deg_s"))) if med else ""),
    ]
    head = "<tr><th>Hodnota</th><th>%s</th>%s</tr>" % (esc(s["name"]), "<th>Medián referencí</th>" if med else "")
    body = "".join("<tr><th>%s</th><td>%s</td>%s</tr>" % (esc(a), esc(b), ("<td>%s</td>" % esc(c)) if med else "")
                   for a, b, c in rows)
    return '<div class="table-wrap"><table class="spec"><thead>%s</thead><tbody>%s</tbody></table></div>' % (head, body)


def kv_lists(spec):
    comps, weapons = [], []
    for group, items in (spec.get("components") or spec.get("systems") and {"systems": spec["systems"]} or {}).items():
        if isinstance(items, dict):
            for k, v in items.items():
                if v:
                    comps.append((k.replace("_", " "), v))
    for k, v in (spec.get("weapons") or spec.get("weaponry") or {}).items():
        for w in v or []:
            weapons.append((k.replace("_", " "), w))
    li = lambda xs: "".join("<li><span>%s</span>%s</li>" % (esc(a), esc(b)) for a, b in xs)
    return li(comps), li(weapons)


def step(n, eyebrow, title, body):
    return ('<section class="step"><div class="n">%d</div><div class="body"><div class="eyebrow">%s</div>'
            '<h2>%s</h2>%s</div></section>' % (n, esc(eyebrow), esc(title), body))


def dossier_html(s):
    spec, dz, lay = s["spec"], s["dossier"], s["layout"]
    ref = spec.get("_reference")
    refset = None
    if ref and os.path.exists(os.path.join(ROOT, ref.get("set", ""))):
        refset = json.load(io.open(os.path.join(ROOT, ref["set"]), encoding="utf-8"))
    parts, n = [], 0

    if refset:
        n += 1
        imgs = "".join('<figure><img src="%s" alt="%s" loading="lazy"><figcaption>%s</figcaption></figure>' % (
            uri(os.path.join(ROOT, r["image"]), 600, 72), esc(r["name"]), esc(r["name"])) for r in refset["ships"] if r.get("image"))
        rows = "".join("<tr><td>%s</td><td>%s</td><td>%g</td><td>%g</td><td>%g</td><td>%g</td><td>%g</td></tr>" % (
            esc(r["name"]), esc(r["manufacturer"]), r["length"], r["beam"], r["height"], r["cargocapacity"] or 0, r["scm_speed"] or 0)
            for r in refset["ships"])
        parts.append(step(n, "Reference ze Ship Matrix", "Z čeho návrh vychází",
            "<p>Referenční sada %s: %d letuschopných lodí z RSI Ship Matrix. Jejich medián je výchozí bod pro každé číslo. "
            "Obrázky jsou jen ke studiu, do AI generátoru nikdy nejdou.</p><div class=\"gallery\">%s</div>"
            "<div class=\"table-wrap\"><table><thead><tr><th>Loď</th><th>Výrobce</th><th>L m</th><th>B m</th><th>H m</th>"
            "<th>SCU</th><th>SCM m/s</th></tr></thead><tbody>%s</tbody></table></div>" % (
                esc(refset["class"]), len(refset["ships"]), imgs, rows)))

    n += 1
    comps, weapons = kv_lists(spec)
    cols = ""
    if comps or weapons:
        cols = '<div class="cols"><div><h3>Komponenty</h3><ul class="kv">%s</ul></div><div><h3>Zbraně a vybavení</h3><ul class="kv">%s</ul></div></div>' % (
            comps or "<li>zatím neurčeno</li>", weapons or "<li>žádné</li>")
    parts.append(step(n, "Specifikace", "Čísla lodi" + (" proti mediánu referencí" if ref else ""),
                      spec_rows(s, ref.get("median") if ref else None) + cols))

    ext = [p for p in s["drawings"] if p.endswith("_exterior.png")]
    if ext:
        n += 1
        parts.append(step(n, "Exteriér", "Celkové uspořádání",
                          "<p>Obrysy ve třech pohledech jsou data v layoutu, výkres kreslí skript a rozměry měří přímo z obrysů.</p>"
                          + fig(ext[0], "Exteriér ve třech pohledech, v měřítku.", "wide")))
    decks = [p for p in s["drawings"] if "_deck_" in p]
    cut = [p for p in s["drawings"] if p.endswith("_cutaway.png")]
    if decks or cut:
        n += 1
        body = "".join(fig(p, "Půdorys paluby: místnosti podle zón, očíslované objekty a jejich účel.", "wide") for p in decks)
        body += "".join(fig(p, "Boční řez: výšky palub, přechody, co je pod podlahou.", "wide") for p in cut)
        if lay:
            rooms = "".join("<li><b>%s</b> %s</li>" % (esc(r["name"]), esc(r["purpose"])) for r in lay["rooms"])
            objs = "".join("<li><b>%s</b> %s</li>" % (esc(o["name"]), esc(o["purpose"])) for o in lay["objects"])
            body += ('<div class="cols"><div><h3>Místnosti</h3><ul class="list">%s</ul></div><div><details><summary>'
                     'Všech %d objektů a jejich účel</summary><ul class="list">%s</ul></details></div></div>' % (rooms, len(lay["objects"]), objs))
        parts.append(step(n, "Interiér", "Paluby a řez: každá místnost a každý objekt má účel", body))

    chk = silhouette_checks(s)
    if chk:
        n += 1
        d = chk["design"]
        note = "Výkres: chyba uzávěru %s, symetrie zepředu %s a shora %s" % (
            pct(d["closure_error_pct"]), dec(d["symmetry_front"]), dec(d["symmetry_top"]))
        if "beam_error_pct" in d:
            note += ", šířka a výška proti specifikaci %s / %s" % (pct(d["beam_error_pct"]), pct(d["height_error_pct"]))
        parts.append(step(n, "Kontrola výkresu", "Sedí pohledy k sobě?",
            "<p>Každý pohled ukazuje dva ze tří rozměrů, takže bok a pohled shora musí předpovědět poměr stran zepředu. "
            "Stejné masky jsou vodítka pro AI a měřítko pro 3D model.</p>"
            + fig(chk["design_sheet"], "Masky siluet z výkresu.", "wide") + '<p class="note">%s.</p>' % esc(note)))

    concepts = dz.get("concepts") or [{"file": os.path.basename(p), "caption": os.path.basename(p)}
                                      for p in sorted(glob.glob(os.path.join(s["dir"], "Concept", "*.png")))]
    if concepts:
        n += 1
        body = ""
        if chk and "per_view" in chk:
            pv, c = chk["per_view"], chk["concept"]
            names = {"front": "Zepředu", "side": "Bok", "top": "Shora"}
            rows = [("%s proti výkresu" % names[v], "IoU %s" % dec(pv[v]["iou"]),
                     "sedí" if pv[v]["iou"] >= 0.88 else "pod cílem 0,88") for v in ("side", "front", "top")]
            rows.append(("Uzávěr mezi pohledy konceptu", pct(c["closure_error_pct"]),
                         "sedí (≤ 10 %)" if c["closure_error_pct"] <= 10 else "nad limitem 10 %"))
            if "beam_error_pct" in c:
                for k, lbl in (("beam_error_pct", "Šířka proti specifikaci"), ("height_error_pct", "Výška proti specifikaci")):
                    rows.append((lbl, pct(c[k]), "sedí (≤ 5 %)" if c[k] <= 5 else "nad limitem 5 %"))
            rows.append(("Symetrie zepředu / shora", "%s / %s" % (dec(c["symmetry_front"]), dec(c["symmetry_top"])),
                         "sedí (≥ 0,9)" if min(c["symmetry_front"], c["symmetry_top"]) >= 0.9 else "pod 0,9"))
            table = "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(x)) for a, b, x in rows)
            guide = os.path.join(s["dir"], "Design", "guides", "guide_side.png")
            body += '<div class="cols">%s%s</div>' % (
                fig(guide, "Vodítko pro obrázkový model: silueta boku z výkresu.") if os.path.exists(guide) else "",
                fig(chk["diff_sheet"], "Koncept proti výkresu: šedá = shoda, červená = výkres má navíc, tyrkys = koncept má navíc."))
            body += ('<div class="table-wrap"><table><thead><tr><th>Měření</th><th>Výsledek</th><th>Hodnocení</th></tr>'
                     '</thead><tbody>%s</tbody></table></div>' % table)
        figs = "".join(fig(os.path.join(s["dir"], "Concept", c["file"]), c["caption"]) for c in concepts)
        parts.append(step(n, "Koncepty", "Jak má loď vypadat",
                          "<p>%s</p>" % esc(dz.get("concepts_note", "Koncepty z Higgsfieldu s vodicí siluetou z výkresu; každý pohled se měří a prohlíží.")) + '<div class="concepts">%s</div>' % figs + body))

    model = dz.get("model")
    if model:
        n += 1
        body = "<p>%s</p>" % esc(model.get("note", ""))
        renders = "".join(fig(os.path.join(s["dir"], r["file"]), r["caption"]) for r in model.get("renders", []))
        if renders:
            body += '<div class="concepts">%s</div>' % renders
        masks = {v: os.path.join(s["dir"], "Renders", "model_%s.png" % v) for v in sc.VIEWS}
        if s["done"]["check"] and all(os.path.exists(m) for m in masks.values()):
            rows, tiles = [], []
            names = {"front": "Zepředu", "side": "Bok", "top": "Shora"}
            for v in ("side", "front", "top"):
                st, mm, rr = sc.compare_masks(sc.load_render_mask(masks[v]), sc.load_render_mask(s["masks"][v]), False)
                rows.append(("%s: model proti výkresu" % names[v], "IoU %s" % dec(st["iou"]),
                             "sedí" if st["iou"] >= 0.88 else "odchylka – viz poznámka"))
                tiles.append(sc.diff_image(mm, rr))
            sheet = Image.new("RGB", (sc.NORM * 3, sc.NORM), (18, 22, 30))
            for i, t in enumerate(tiles):
                sheet.paste(t, (i * sc.NORM, 0))
            body += fig(sheet, "3D model proti výkresu (bok, zepředu, shora): šedá = shoda, červená = model má navíc, tyrkys = modelu chybí.", "wide")
            body += ('<div class="table-wrap"><table><thead><tr><th>Měření</th><th>Výsledek</th><th>Hodnocení</th></tr></thead><tbody>%s</tbody></table></div>'
                     % "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b), esc(c)) for a, b, c in rows))
        shots = "".join(fig(os.path.join(ROOT, r["file"]), r["caption"]) for r in model.get("shots", []))
        if shots:
            body += "<h3>Ve hře (zabalená hra, 1920 × 1080)</h3>" + '<div class="concepts">%s</div>' % shots
        if model.get("known"):
            body += '<h3>Známé nedostatky</h3><ul class="list">%s</ul>' % "".join("<li>%s</li>" % esc(k) for k in model["known"])
        parts.append(step(n, "3D model", model.get("title", "Model ve hře"), body))

    if dz.get("decisions") or dz.get("questions"):
        n += 1
        if dz.get("decisions"):
            lis = "".join("<li><b>%s</b> %s</li>" % (esc(q), esc(a)) for q, a in dz["decisions"])
            parts.append(step(n, "Rozhodnutí autora", dz.get("decided", "Schváleno"), '<ul class="list">%s</ul>' % lis))
        else:
            lis = "".join("<li>%s</li>" % esc(q) for q in dz["questions"])
            parts.append(step(n, "Na autorovi", "Otázky ke schválení", "<p>Dokud návrh není schválený, nic se nestaví ve 3D.</p><ol class=\"q\">%s</ol>" % lis))

    meta = "".join("<span>%s <b>%s</b></span>" % (a, esc(b)) for a, b in (
        ("délka", fmt(s["L"], "m")), ("šířka", fmt(s["B"], "m")), ("výška", fmt(s["H"], "m")),
        ("náklad", fmt(s["scu"], "SCU")), ("posádka", fmt(s["crew"])), ("SCM", fmt(s["scm"], "m/s"))))
    head = ('<header class="dossier-head"><div class="eyebrow">%s · %s · %s</div><h1>%s</h1><p>%s</p>'
            '<div class="status">%s</div><div class="meta">%s</div>%s</header>' % (
                esc(s["maker"]), esc(s["focus"]), esc(s["size"]), esc(s["name"]), esc(s["desc"]),
                esc(dz.get("status", s["status"])), meta, pipeline_html(s)))
    return head + "".join(parts)


def card_html(s):
    img = card_image(s)
    src = uri(img, 640, 76) if img else uri(placeholder(s), 640, 76)
    return ('<a class="card" href="#%s" data-size="%s" data-stage="%s"><img src="%s" alt="%s"><div class="c-body">'
            '<div class="eyebrow">%s</div><h3>%s</h3><div class="focus">%s</div>'
            '<dl><div><dt>délka</dt><dd>%s</dd></div><div><dt>posádka</dt><dd>%s</dd></div>'
            '<div><dt>náklad</dt><dd>%s</dd></div><div><dt>SCM</dt><dd>%s</dd></div></dl>'
            '<span class="pill s-%s">%s</span></div></a>' % (
                esc(s["name"]), esc(s["size"]), esc(s["stage"] or "plan"), src, esc(s["name"]), esc(s["maker"]),
                esc(s["name"]), esc(s["focus"]), fmt(s["L"], "m"), fmt(s["crew"]), fmt(s["scu"], "SCU"),
                fmt(s["scm"], "m/s"), esc(s["stage"] or "plan"), esc(s["status"])))


def table_html(ships):
    cols = [("name", "Loď"), ("maker", "Výrobce"), ("focus", "Role"), ("size", "Velikost"), ("L", "L m"), ("B", "B m"),
            ("H", "H m"), ("crew", "Posádka"), ("scu", "SCU"), ("scm", "SCM"), ("status", "Stav")]
    head = "".join('<th><button type="button" data-col="%d">%s</button></th>' % (i, esc(l)) for i, (_, l) in enumerate(cols))
    rows = ""
    for s in ships:
        cells = []
        for k, _ in cols:
            v = s[k]
            if k == "name":
                cells.append('<td><a href="#%s">%s</a></td>' % (esc(v), esc(v)))
            elif isinstance(v, (int, float)):
                cells.append('<td data-v="%s">%g</td>' % (v, v))
            else:
                cells.append("<td>%s</td>" % esc(v if v is not None else "–"))
        rows += "<tr>%s</tr>" % "".join(cells)
    return '<div class="table-wrap"><table id="fleet"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, rows)


# ------------------------------------------------------------------ page

def build(ships, single=False):
    title = "%s Design Dossier" % ships[0]["name"] if single else "Gamespace Ship Matrix"
    if single:
        body = '<article class="dossier">%s</article>' % dossier_html(ships[0])
    else:
        sizes = sorted({s["size"] for s in ships})
        chips = '<button type="button" class="chip on" data-f="all">Vše</button>' + "".join(
            '<button type="button" class="chip" data-f="%s">%s</button>' % (esc(z), esc(z)) for z in sizes)
        cards = "".join(card_html(s) for s in ships)
        dossiers = "".join('<article class="dossier" id="d-%s" hidden><a class="back" href="#">← Ship Matrix</a>%s</article>' % (
            esc(s["name"]), dossier_html(s)) for s in ships)
        body = ('<main id="matrix"><header class="matrix-head"><div class="eyebrow">Flotila gamespace</div><h1>Ship Matrix</h1>'
                '<p>Všechny lodě hry: specifikace ve tvaru RSI Ship Matrix a u každé dossier s celým postupem návrhu. '
                'Stránku generuje <span class="mono">Tools/Design/build_ship_matrix.py</span> z dat lodí.</p></header>'
                '<div class="toolbar"><div class="chips" role="group" aria-label="Velikost">%s</div>'
                '<div class="views"><button type="button" class="chip on" data-view="grid">Karty</button>'
                '<button type="button" class="chip" data-view="table">Tabulka</button></div></div>'
                '<div class="grid" id="grid">%s</div><div id="tableview" hidden>%s</div></main>%s' % (
                    chips, cards, table_html(ships), dossiers))
    return TEMPLATE.replace("{{TITLE}}", esc(title)).replace("{{BODY}}", body)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ship", default="")
    args = ap.parse_args()
    names = [args.ship] if args.ship else sorted(
        os.path.basename(p) for p in glob.glob(os.path.join(SHIPS, "*")) if os.path.exists(os.path.join(p, os.path.basename(p) + "_spec.json")))
    ships = [load_ship(n) for n in names]
    order = [k for k, _ in STAGES]
    ships.sort(key=lambda s: (-(order.index(s["stage"]) if s["stage"] else -1), s["name"]))
    out = os.path.join(ROOT, "Saved", "Dossier")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, (args.ship if args.ship else "ShipMatrix") + ".html")
    io.open(path, "w", encoding="utf-8").write(build(ships, bool(args.ship)))
    for s in ships:
        print("%-10s stage %-10s %s" % (s["name"], s["stage"], ", ".join(k for k, _ in STAGES if s["done"][k])))
    print("wrote", path, "%.1f MB" % (os.path.getsize(path) / 1e6))


TEMPLATE = r"""<title>{{TITLE}}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  --ground:#e9edf1; --panel:#f7f9fb; --ink:#14202b; --muted:#566574; --rule:#c9d2db;
  --accent:#c24e0e; --holo:#1f7fa6; --plate:#0d121a; --ok:#2f7d4f;
  color-scheme: light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0d121a; --panel:#141b25; --ink:#e3e8ee; --muted:#8b9aab; --rule:#243040;
    --accent:#e2702e; --holo:#5fc8eb; --plate:#0a0e14; --ok:#5cc28a; color-scheme: dark;
  }
}
:root[data-theme="dark"]{
  --ground:#0d121a; --panel:#141b25; --ink:#e3e8ee; --muted:#8b9aab; --rule:#243040;
  --accent:#e2702e; --holo:#5fc8eb; --plate:#0a0e14; --ok:#5cc28a; color-scheme: dark;
}
*{box-sizing:border-box}
body{background:var(--ground);color:var(--ink);font:16px/1.6 "IBM Plex Sans",system-ui,sans-serif;padding-inline:clamp(16px,4vw,56px);padding-block:32px 72px}
main,.dossier{max-width:1180px;margin:0 auto;display:flex;flex-direction:column;gap:48px}
h1,h2,h3{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:600;letter-spacing:.01em;text-wrap:balance;margin:0;line-height:1.05}
h1{font-size:clamp(48px,8vw,96px);font-weight:700}
h2{font-size:clamp(28px,3.4vw,40px)}
h3{font-size:22px;margin-bottom:8px}
p{margin:0;max-width:68ch}
a{color:var(--holo)}
.eyebrow{font:500 12px/1.3 "IBM Plex Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
.mono{font-family:"IBM Plex Mono",monospace;font-size:.9em}
.matrix-head,.dossier-head{display:grid;gap:16px;padding-bottom:26px;border-bottom:2px solid var(--ink)}
.meta{display:flex;flex-wrap:wrap;gap:8px 28px;font:500 13px/1.4 "IBM Plex Mono",monospace;color:var(--muted)}
.meta b{color:var(--ink);font-weight:500}
.status{display:inline-flex;align-items:center;gap:8px;font:500 13px/1.3 "IBM Plex Mono",monospace;color:var(--accent);border:1px solid var(--accent);padding:7px 12px;width:fit-content}
.status::before{content:"";width:8px;height:8px;background:var(--accent);border-radius:50%;flex:none}
.pipeline{list-style:none;margin:6px 0 0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:6px}
.pipeline li{font:500 11px/1.3 "IBM Plex Mono",monospace;color:var(--muted);border-top:3px solid var(--rule);padding-top:7px;display:flex;gap:6px}
.pipeline li.done{color:var(--ink);border-top-color:var(--ok)}
.pipeline li span::before{content:"○"}
.pipeline li.done span::before{content:"●";color:var(--ok)}
.toolbar{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px}
.chips,.views{display:flex;flex-wrap:wrap;gap:8px}
.chip{font:500 13px/1 "IBM Plex Mono",monospace;background:transparent;color:var(--ink);border:1px solid var(--rule);padding:9px 14px;cursor:pointer}
.chip.on{border-color:var(--accent);color:var(--accent)}
.chip:focus-visible,.card:focus-visible,button:focus-visible,summary:focus-visible,a:focus-visible{outline:2px solid var(--holo);outline-offset:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px}
.card{display:flex;flex-direction:column;background:var(--panel);border:1px solid var(--rule);color:inherit;text-decoration:none;transition:border-color .15s}
.card:hover{border-color:var(--accent)}
.card img{width:100%;aspect-ratio:16/10;object-fit:cover;display:block;background:var(--plate)}
.c-body{padding:14px 16px 16px;display:grid;gap:6px}
.c-body h3{font-size:30px;margin:0}
.focus{font-size:14px;color:var(--muted)}
dl{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0 4px;font-variant-numeric:tabular-nums}
dl div{display:grid;gap:2px}
dt{font:500 10px/1 "IBM Plex Mono",monospace;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
dd{margin:0;font:500 13px/1.2 "IBM Plex Mono",monospace}
.pill{justify-self:start;font:500 11px/1 "IBM Plex Mono",monospace;padding:6px 9px;border:1px solid var(--rule);color:var(--muted)}
.pill.s-approved,.pill.s-model,.pill.s-unreal{border-color:var(--ok);color:var(--ok)}
.pill.s-flight{background:var(--ok);color:var(--panel);border-color:var(--ok)}
.pill.s-concepts,.pill.s-check,.pill.s-layout{border-color:var(--accent);color:var(--accent)}
.back{font:500 13px/1 "IBM Plex Mono",monospace;text-decoration:none}
section{display:grid;gap:22px}
.step{display:grid;grid-template-columns:72px 1fr;gap:8px 24px;align-items:baseline}
.step .n{font:700 56px/0.9 "Barlow Condensed",sans-serif;color:var(--accent);font-variant-numeric:tabular-nums}
.step .body{display:grid;gap:14px;min-width:0}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}
figure{margin:0;display:grid;gap:8px}
figure img{width:100%;height:auto;display:block;background:var(--plate);border:1px solid var(--rule)}
figcaption{font-size:13px;color:var(--muted)}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.gallery figcaption{font:500 12px/1.3 "IBM Plex Mono",monospace;color:var(--ink)}
.concepts{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}
.table-wrap{overflow-x:auto;border-top:1px solid var(--rule)}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:14px}
th,td{text-align:left;padding:9px 12px 9px 0;border-bottom:1px solid var(--rule);vertical-align:top}
thead th{font:500 11px/1.2 "IBM Plex Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
thead th button{all:unset;cursor:pointer}
tbody th{font-weight:500}
.spec td:nth-child(3){color:var(--muted)}
ul.kv{list-style:none;margin:0;padding:0;display:grid;gap:8px;font-size:14px}
ul.kv li{display:grid;grid-template-columns:150px 1fr;gap:12px;border-bottom:1px solid var(--rule);padding-bottom:8px}
ul.kv span{font:500 12px/1.6 "IBM Plex Mono",monospace;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
ul.list{margin:0;padding-left:18px;display:grid;gap:6px;font-size:14px;max-width:80ch}
ul.list b{font-weight:600}
.note{border-left:3px solid var(--holo);padding:4px 0 4px 16px;color:var(--muted);font-size:14px}
ol.q{margin:0;padding-left:22px;display:grid;gap:10px;max-width:80ch}
details summary{cursor:pointer;font-weight:600;color:var(--holo)}
@media (max-width:640px){.step{grid-template-columns:1fr}.step .n{font-size:40px}ul.kv li{grid-template-columns:1fr}dl{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
{{BODY}}
<script>
(function(){
  var matrix=document.getElementById('matrix');
  if(!matrix) return;
  function route(){
    var id=(location.hash||'').slice(1);
    var target=id?document.getElementById('d-'+id):null;
    document.querySelectorAll('.dossier').forEach(function(d){d.hidden=d!==target;});
    matrix.hidden=!!target;
    window.scrollTo(0,0);
  }
  window.addEventListener('hashchange',route); route();
  document.querySelectorAll('.chips .chip').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.chips .chip').forEach(function(x){x.classList.toggle('on',x===b);});
    var f=b.dataset.f;
    document.querySelectorAll('.card').forEach(function(c){c.hidden=!(f==='all'||c.dataset.size===f);});
    document.querySelectorAll('#fleet tbody tr').forEach(function(r){r.hidden=!(f==='all'||r.children[3].textContent===f);});
  });});
  document.querySelectorAll('.views .chip').forEach(function(b){b.addEventListener('click',function(){
    document.querySelectorAll('.views .chip').forEach(function(x){x.classList.toggle('on',x===b);});
    document.getElementById('grid').hidden=b.dataset.view!=='grid';
    document.getElementById('tableview').hidden=b.dataset.view!=='table';
  });});
  var dir={};
  document.querySelectorAll('#fleet thead button').forEach(function(b){b.addEventListener('click',function(){
    var i=+b.dataset.col, body=document.querySelector('#fleet tbody');
    dir[i]=-(dir[i]||-1);
    Array.from(body.rows).sort(function(a,c){
      var x=a.cells[i], y=c.cells[i];
      var vx=x.dataset.v!==undefined?+x.dataset.v:x.textContent, vy=y.dataset.v!==undefined?+y.dataset.v:y.textContent;
      return (vx>vy?1:vx<vy?-1:0)*dir[i];
    }).forEach(function(r){body.appendChild(r);});
  });});
})();
</script>
"""

if __name__ == "__main__":
    main()
