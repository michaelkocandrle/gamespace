"""Compare sheets for the visual critic (.claude/agents/visual-critic.md): reference left, our result right,
same resolution, labelled; plus brief.md with the goal, the style and the checklist from a skill.

    python Tools/Review/make_compare_sheet.py <review.json>

review.json:
  {
    "topic": "wayfarer_cockpit",            # file names; the review folder is Docs/Reviews/<date>_<topic>/
    "date": "2026-09-25",                   # optional, today by default
    "goal": "What it is meant to be (one or two sentences).",
    "style": "In which style (e.g. Star Citizen, clean Origin-like ship, warm dark architecture ...).",
    "checklist": "cockpit",                 # section of the critic checklist in the skill (see below); null = none
    "skill": ".claude/skills/ship-pipeline/SKILL.md",   # optional, this by default
    "out": "Docs/Reviews/2026-09-25_wayfarer_cockpit",  # optional
    "notes": ["Text vpravo nahoře (FPS, stat unit) je měřicí overlay, ne součást výsledku."],   # optional
    "pairs": [
      {"title": "Pilot view", "distance": "mid", "light": "day",
       "ref": "starcitizenreference/cockpit_reference_2.png", "ref_label": "SC reference 2",
       "ours": "Saved/Shots/.../01_pilot_view_day.png", "ours_label": "in-game, packaged, 1080p"}
    ]
  }
distance: close | mid | far; light: day | night | space | studio. "ref" may be a list of images (tiled).
The checklist is the text between "<!-- critic-checklist:<name> -->" and "<!-- /critic-checklist -->"
in the skill.

Output (in "out"): sheet_NN_<slug>.jpg (2 x 1280x720 panels under a label bar) and brief.md.
The brief says nothing about how the work was done or what was intended - the critic must not know.
"""
import datetime
import json
import os
import re
import sys
import unicodedata

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PW, PH, BAR = 1280, 720, 64
DIST = {"close": "zblízka", "mid": "střední vzdálenost", "far": "zdálky"}
LIGHT = {"day": "den", "night": "noc", "space": "vesmír", "studio": "studiové světlo"}


def font(size):
    for f in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
              os.path.join(ROOT, "Content", "UI", "Fonts", "Rajdhani-SemiBold.ttf")):
        if os.path.isfile(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def path(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def panel(src):
    """One image or a tile of several, letterboxed into PW x PH."""
    srcs = src if isinstance(src, list) else [src]
    canvas = Image.new("RGB", (PW, PH), (18, 18, 20))
    n = len(srcs)
    cols = 1 if n == 1 else 2
    rows = (n + cols - 1) // cols
    cw, ch = PW // cols, PH // rows
    for i, s in enumerate(srcs):
        im = Image.open(path(s)).convert("RGB")
        im.thumbnail((cw, ch), Image.LANCZOS)
        x = (i % cols) * cw + (cw - im.width) // 2
        y = (i // cols) * ch + (ch - im.height) // 2
        canvas.paste(im, (x, y))
    return canvas


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def checklist(skill, name):
    text = open(path(skill), encoding="utf-8").read()
    m = re.search(r"<!-- critic-checklist:%s -->(.*?)<!-- /critic-checklist -->" % re.escape(name), text, re.S)
    if not m:
        raise SystemExit("checklist %r not found in %s" % (name, skill))
    return m.group(1).strip()


def main():
    spec = json.load(open(path(sys.argv[1]), encoding="utf-8"))
    date = spec.get("date") or datetime.date.today().isoformat()
    out = os.path.normpath(path(spec.get("out") or os.path.join("Docs", "Reviews", "%s_%s" % (date, spec["topic"]))))
    os.makedirs(out, exist_ok=True)
    f_big, f_small = font(26), font(19)
    sheets = []
    for i, p in enumerate(spec["pairs"], 1):
        sheet = Image.new("RGB", (PW * 2 + 8, PH + BAR), (8, 8, 9))
        d = ImageDraw.Draw(sheet)
        cond = "%s · %s" % (DIST.get(p.get("distance", ""), p.get("distance", "")), LIGHT.get(p.get("light", ""), p.get("light", "")))
        for k, (side, label, x) in enumerate((("REFERENCE", p.get("ref_label", ""), 0), ("NÁŠ VÝSLEDEK", p.get("ours_label", ""), PW + 8))):
            d.rectangle([x, 0, x + PW, BAR - 4], fill=(40, 40, 46) if k == 0 else (46, 36, 28))
            d.text((x + 14, 6), "%s  –  %s" % (side, p.get("title", "")), font=f_big, fill=(235, 235, 235))
            d.text((x + 14, 38), "%s  |  %s" % (label, cond), font=f_small, fill=(190, 190, 190))
        sheet.paste(panel(p["ref"]), (0, BAR))
        sheet.paste(panel(p["ours"]), (PW + 8, BAR))
        # JPEG: a review keeps a dozen sheets in git (PNG was ~5 MB each)
        name = "sheet_%02d_%s.jpg" % (i, slug(p.get("title", "pair")))
        sheet.save(os.path.join(out, name), quality=90)
        sheets.append((name, p, cond))
    lines = ["# Brief pro vizuálního kritika", "", "## Co to má být", spec["goal"], "", "## Styl", spec["style"], "",
             "## Srovnávací listy", "Vlevo reference, vpravo náš výsledek. Reference ukazuje cílovou úroveň a styl, ne nutně"
             " stejný objekt.", ""]
    for note in spec.get("notes", []):
        lines.insert(len(lines) - 1, "- Pozn.: " + note)
    for name, p, cond in sheets:
        lines.append("- `%s` – %s (%s); reference: %s; výsledek: %s" % (os.path.join(out, name).replace("\\", "/"), p.get("title", ""), cond,
                                                                       p.get("ref_label", ""), p.get("ours_label", "")))
    if spec.get("checklist"):
        lines += ["", "## Checklist", checklist(spec.get("skill", ".claude/skills/ship-pipeline/SKILL.md"), spec["checklist"]), ""]
    open(os.path.join(out, "brief.md"), "w", encoding="utf-8").write("\n".join(lines))
    print("SHEETS " + json.dumps({"out": out, "sheets": [s[0] for s in sheets]}))


if __name__ == "__main__":
    main()
