"""Cockpit v2 design sheet C-01 from ArtSource/Ships/<Ship>/Design/<Ship>_cockpit_v2.json (author 4. 10. 2026).

    python Tools/Design/draw_cockpit_v2_sheet.py Wayfarer

One sheet for the author's approval before the build: today's pilot view with every proposed element as a numbered
callout (ID from the data), a section through a holo projector with its dimensions, the style concepts, the measured
targets, the material zones, the element table and the open questions. Everything on it comes from the data file;
the sheet draws nothing that is not there. Writes Design/Drawings/<Ship>_C01_cockpit_v2.png and a JSON sidecar.
"""

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
W, H = 4200, 2970          # A3-ish landscape at ~250 dpi, as one image the author can zoom
BLUE = (30, 90, 200)
INK = (25, 28, 32)
GREY = (120, 126, 134)
PAPER = (250, 250, 247)


def font(size, bold=False):
    for name in (("bahnschrift.ttf", "segoeuib.ttf") if bold else ("bahnschrift.ttf", "segoeui.ttf")):
        try:
            return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", name), size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textlength(test, font=fnt) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def paste_fit(sheet, img, box):
    x0, y0, x1, y1 = box
    img = img.convert("RGB")
    scale = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    sheet.paste(img, (x0, y0))
    return x0, y0, img.width, img.height


def main(ship):
    path = os.path.join(REPO, "ArtSource", "Ships", ship, "Design", "%s_cockpit_v2.json" % ship)
    data = json.load(open(path, encoding="utf-8"))
    sheet = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(sheet)
    f_title, f_h, f_b, f_s = font(64, True), font(38, True), font(28), font(24)
    margin = 60
    d.rectangle([20, 20, W - 20, H - 20], outline=INK, width=4)
    d.text((margin, 40), "%s – KOKPIT v2: NÁVRH (C-01)" % ship.upper(), font=f_title, fill=INK)
    d.text((margin, 120), "Stav: %s · data %s · modře = návrh" % (data["status"], os.path.relpath(path, REPO).replace("\\", "/")), font=f_s, fill=GREY)

    # --- the pilot view with callouts ------------------------------------------------------------------------------
    view_box = (margin, 180, 2350, 1480)
    drawn = []
    if os.path.isfile(data["base_shot"]):
        x, y, w, h = paste_fit(sheet, Image.open(data["base_shot"]), view_box)
        d.text((x, y + h + 8), "Dnes (pohled pilota, balená hra) s prvky návrhu", font=f_s, fill=GREY)
        for n, e in enumerate(data["elements"], 1):
            if "callout_uv" not in e:
                continue
            cx, cy = x + e["callout_uv"][0] * w, y + e["callout_uv"][1] * h
            r = 30
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLUE, outline=(255, 255, 255), width=3)
            label = str(n)
            d.text((cx - d.textlength(label, font=f_b) / 2, cy - 17), label, font=f_b, fill=(255, 255, 255))
            drawn.append(e["id"])
    else:
        d.text(view_box[:2], "chybí snímek %s" % data["base_shot"], font=f_b, fill=(200, 0, 0))

    # --- section through a holo projector (from the element's data) -------------------------------------------------
    hp = next(e for e in data["elements"] if e["kind"] == "holo_projector")
    sx0, sy0, sx1, sy1 = 2420, 180, 4140, 1000
    d.text((sx0, sy0), "Řez holoprojektorem %s (1:5)" % hp["id"], font=f_h, fill=INK)
    scale = 620.0         # px per metre on the sheet (1:5 at the print size)
    ex, ey = data["eye"][0], data["eye"][2]
    px, pz = hp["at"][0], hp["at"][2]
    base_x, base_y = sx0 + 1150, sy1 - 150

    def P(x, z):
        return base_x + (x - px) * scale, base_y - (z - pz) * scale
    # today's dash top (grey), the emitter bar (blue box), the image plane facing the eye (blue dashed), the sight line
    d.line([P(px - 0.45, pz - 0.01), P(px + 0.35, pz - 0.01)], fill=GREY, width=4)
    d.text((P(px + 0.05, pz - 0.03)[0], P(px + 0.05, pz - 0.03)[1] + 4), "horní hrana pultu", font=f_s, fill=GREY)
    bw, bh = hp["size"][1], hp["size"][2]
    x0, y0 = P(px - bw * 0.5, pz + bh)
    x1, y1 = P(px + bw * 0.5, pz)
    d.rectangle([x0, y0, x1, y1], outline=BLUE, width=5)
    d.text((x1 + 14, y0 - 6), "emitor %d × %d × %d mm" % (hp["size"][0] * 1000, hp["size"][1] * 1000, hp["size"][2] * 1000), font=f_s, fill=BLUE)
    img_h = hp["image"][1]
    cx, cz = px, pz + bh + 0.03 + img_h * 0.5
    vx, vz = ex - cx, ey - cz
    norm = (vx * vx + vz * vz) ** 0.5
    tx, tz = -vz / norm, vx / norm          # along the image plane, perpendicular to the sight line
    if tz < 0:
        tx, tz = -tx, -tz
    a = (cx - tx * img_h * 0.5, cz - tz * img_h * 0.5)
    b = (cx + tx * img_h * 0.5, cz + tz * img_h * 0.5)
    for k in range(10):
        f0, f1 = k / 10.0, (k + 0.55) / 10.0
        d.line([P(a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0), P(a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1)], fill=BLUE, width=5)
    d.polygon([P(px, pz + bh), P(*a), P(*b)], outline=(130, 175, 240))
    d.text((P(*b)[0] + 18, P(*b)[1] - 10), "obraz %d × %d mm, kolmo k pohledu" % (hp["image"][0] * 1000, img_h * 1000), font=f_s, fill=BLUE)
    d.text((P(*b)[0] + 18, P(*b)[1] + 22), "bez desky a rámu: skrz je vidět kokpit", font=f_s, fill=BLUE)
    eye_pt, mid = P(ex, ey), P(cx, cz)
    for k in range(24):
        f0, f1 = k / 24.0, (k + 0.5) / 24.0
        d.line([(eye_pt[0] + (mid[0] - eye_pt[0]) * f0, eye_pt[1] + (mid[1] - eye_pt[1]) * f0),
                (eye_pt[0] + (mid[0] - eye_pt[0]) * f1, eye_pt[1] + (mid[1] - eye_pt[1]) * f1)], fill=GREY, width=2)
    d.ellipse([eye_pt[0] - 12, eye_pt[1] - 12, eye_pt[0] + 12, eye_pt[1] + 12], fill=INK)
    d.text((eye_pt[0] - 30, eye_pt[1] - 50), "oko pilota (%.2f m za emitorem, %.2f m nad ním)" % (px - ex, ey - pz), font=f_s, fill=INK)
    d.text((sx0 + 20, sy1 - 40), "Nahrazuje: %s" % hp.get("replaces", ""), font=f_s, fill=GREY)

    # --- concepts ---------------------------------------------------------------------------------------------------
    cdir = os.path.join(REPO, data["references"]["concepts"])
    names = sorted(f for f in os.listdir(cdir) if f.lower().endswith(".png")) if os.path.isdir(cdir) else []
    cy0 = 1060
    d.text((2420, cy0), "Koncepty stylu (AI, jen reference)", font=f_h, fill=INK)
    for i, n in enumerate(names[:4]):
        bx = 2420 + (i % 2) * 870
        by = cy0 + 60 + (i // 2) * 520
        x, y, w, h = paste_fit(sheet, Image.open(os.path.join(cdir, n)), (bx, by, bx + 850, by + 478))
        d.text((x, y + h + 2), "%s  %s" % ("ABCD"[i], n), font=f_s, fill=GREY)

    # --- element table ------------------------------------------------------------------------------------------------
    ty = 1560
    d.text((margin, ty), "Prvky návrhu", font=f_h, fill=INK)
    ty += 56
    col = [margin, margin + 70, margin + 260, margin + 900]
    for n, e in enumerate(data["elements"], 1):
        lines = wrap(d, e["purpose"], f_s, 2330 - col[3])
        d.text((col[0], ty), str(n), font=f_b, fill=BLUE)
        d.text((col[1], ty), e["id"], font=f_b, fill=INK)
        d.text((col[2], ty), "\n".join(wrap(d, e["name"], f_s, col[3] - col[2] - 20)), font=f_s, fill=INK)
        d.text((col[3], ty), "\n".join(lines), font=f_s, fill=INK)
        ty += max(len(lines), len(wrap(d, e["name"], f_s, col[3] - col[2] - 20))) * 30 + 12

    # --- targets, materials, questions -------------------------------------------------------------------------------
    rx, ry = 2420, 2240
    d.text((rx, ry), "Měřené cíle", font=f_h, fill=INK)
    ry += 54
    for t in data["targets"]:
        text = "%s %s: %s" % (t["id"], t["what"], t["value"])
        for line in wrap(d, text, f_s, 1720):
            d.text((rx, ry), line, font=f_s, fill=INK)
            ry += 29
    ry += 14
    d.text((rx, ry), "Materiálové zóny", font=f_h, fill=INK)
    ry += 54
    for m in data["materials"]:
        c = tuple(int(255 * min(1.0, v ** (1 / 2.2))) for v in m["colour"])
        d.rectangle([rx, ry + 4, rx + 30, ry + 30], fill=c, outline=INK)
        d.text((rx + 44, ry), "%s %s · drsnost %.2f–%.2f%s" % (m["id"], m["name"], m["roughness"][0], m["roughness"][1],
               " · kov" if m.get("metallic") else ""), font=f_s, fill=INK)
        ry += 34
    qy = max(ty + 20, 2700)
    d.text((margin, qy), "Otázky pro autora", font=f_h, fill=INK)
    qy += 50
    for i, q in enumerate(data["questions"], 1):
        for line in wrap(d, "%d. %s" % (i, q), f_s, 2280):
            d.text((margin, qy), line, font=f_s, fill=BLUE)
            qy += 29

    out_dir = os.path.join(REPO, "ArtSource", "Ships", ship, "Design", "Drawings")
    out = os.path.join(out_dir, "%s_C01_cockpit_v2.png" % ship)
    sheet.save(out)
    json.dump({"sheet": "C-01", "elements": [e["id"] for e in data["elements"]], "callouts": drawn,
               "concepts": names, "targets": [t["id"] for t in data["targets"]]},
              open(out.replace(".png", ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("C01 %s (%d elements, %d callouts, %d concepts)" % (out, len(data["elements"]), len(drawn), len(names)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "Wayfarer")
