"""Screen atlas for the kit's wall displays (batch 1, 26. 9. 2026): ArtSource/Kit/Textures/T_Kit_Screens.png,
1024 x 1024, drawn with the project's fonts in the cool UI colours. Regions (Blender UV, v = 0 at the bottom):
  status   (0.0, 0.5, 1.0, 1.0)     environment status page (hold / section systems)
  gauge    (0.0, 0.0, 0.125, 0.5)   vertical power gauge
  panel    (0.125, 0.0, 0.5, 0.25)  small two-line status
  reactor  (0.5, 0.25, 0.75, 0.5)   power plant status (component bay A, batch 4)
  cooler   (0.75, 0.25, 1.0, 0.5)   cooler status (component bay B)
  shield   (0.5, 0.0, 0.75, 0.25)   shield generator status (component bay C)
The material is M_Ship_Screen (masked glass: pixels under GlassThreshold show the dark back plate).

    python Tools/Kit/kit_screens.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "ArtSource", "Kit", "Textures")
FONTS = os.path.join(ROOT, "Content", "UI", "Fonts")
BLUE, WHITE, ORANGE, DIM, BG = (115, 184, 255), (225, 235, 245), (255, 150, 40), (60, 95, 140), (4, 8, 14)
REGIONS = {"status": (0.0, 0.5, 1.0, 1.0), "gauge": (0.0, 0.0, 0.125, 0.5), "panel": (0.125, 0.0, 0.5, 0.25),
           "reactor": (0.5, 0.25, 0.75, 0.5), "cooler": (0.75, 0.25, 1.0, 0.5), "shield": (0.5, 0.0, 0.75, 0.25)}


def component_page(d, x0, y0, title, rows, state, warn=False):
    """A 256 px component status page at image (x0, y0): the component's name, two bars, its state."""
    mid, small, big = font("Rajdhani-SemiBold.ttf", 44), font("ShareTechMono-Regular.ttf", 24), font("Rajdhani-SemiBold.ttf", 36)
    d.rectangle([x0 + 4, y0 + 4, x0 + 251, y0 + 251], outline=DIM, width=3)
    d.text((x0 + 16, y0 + 8), title, font=mid, fill=WHITE)
    d.line([(x0 + 14, y0 + 60), (x0 + 242, y0 + 60)], fill=BLUE, width=2)
    for i, (k, v, frac) in enumerate(rows):
        y = y0 + 72 + i * 58
        d.text((x0 + 16, y), k, font=small, fill=BLUE)
        d.text((x0 + 150, y - 6), v, font=big, fill=WHITE)
        n, bx0, bx1 = 10, x0 + 16, x0 + 240
        lit = int(frac * n + 0.5)
        for s in range(n):
            sx = bx0 + s * (bx1 - bx0) / n
            hot = warn and s >= 7
            d.rectangle([sx, y + 32, sx + (bx1 - bx0) / n - 4, y + 44], fill=(ORANGE if hot else BLUE) if s < lit else (18, 30, 46))
    d.text((x0 + 16, y0 + 212), state, font=small, fill=BLUE)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def main():
    img = Image.new("RGB", (1024, 1024), BG)
    d = ImageDraw.Draw(img)
    big, mid, small = font("Rajdhani-SemiBold.ttf", 64), font("Rajdhani-SemiBold.ttf", 40), font("ShareTechMono-Regular.ttf", 28)
    # status page: image rows 0..512 (Blender v 0.5..1)
    d.rectangle([6, 6, 1017, 505], outline=DIM, width=3)
    d.text((28, 16), "SECTION 02  //  ENV", font=mid, fill=WHITE)
    d.line([(24, 70), (1000, 70)], fill=BLUE, width=3)
    rows = [("O2", "21.0 %", 0.84), ("PRESS", "101 kPa", 0.72), ("TEMP", "21 C", 0.55), ("CO2", "0.04 %", 0.12)]
    for i, (k, v, frac) in enumerate(rows):
        y = 96 + i * 92
        d.text((30, y), k, font=small, fill=BLUE)
        d.text((190, y - 14), v, font=big, fill=WHITE)
        x0, x1 = 520, 980
        d.rectangle([x0, y + 8, x1, y + 36], outline=DIM, width=2)
        n = 18
        lit = int(frac * n + 0.5)
        for s in range(n):
            sx = x0 + 6 + s * (x1 - x0 - 12) / n
            d.rectangle([sx, y + 13, sx + (x1 - x0 - 12) / n - 5, y + 31], fill=(ORANGE if (k == "CO2" and s < lit) else BLUE) if s < lit else (18, 30, 46))
    d.text((30, 466), "LIFE SUPPORT NOMINAL", font=small, fill=BLUE)
    d.text((720, 466), "HF-0417", font=small, fill=DIM)
    # gauge: image cols 0..128, rows 512..1024 (Blender (0, 0, 0.125, 0.5))
    d.rectangle([4, 516, 123, 1019], outline=DIM, width=3)
    d.text((22, 524), "PWR", font=small, fill=WHITE)
    for s in range(12):
        y1 = 1004 - s * 36
        on = s < 8
        d.rectangle([22, y1 - 26, 106, y1], fill=(ORANGE if s >= 7 and on else BLUE) if on else (18, 30, 46))
    # small panel: cols 128..512, rows 768..1024 (Blender (0.125, 0, 0.5, 0.25))
    d.rectangle([132, 772, 507, 1019], outline=DIM, width=3)
    d.text((150, 790), "HATCH 02-B", font=mid, fill=WHITE)
    d.text((150, 860), "SEALED", font=big, fill=BLUE)
    d.text((150, 950), "SERVICE 14 D", font=small, fill=DIM)
    # component pages (batch 4): what the component in the bay is doing, readable at arm's length
    component_page(d, 512, 512, "PP-S1", [("OUT", "86 %", 0.86), ("TEMP", "412 K", 0.62)], "ONLINE", warn=True)
    component_page(d, 768, 512, "CL-S1", [("FLOW", "74 %", 0.74), ("DELTA", "38 K", 0.45)], "LOOP A OK")
    component_page(d, 512, 768, "SG-S1", [("FIELD", "100 %", 1.0), ("REGEN", "12 /s", 0.55)], "BUBBLE UP")
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, "T_Kit_Screens.png"))
    json.dump(REGIONS, open(os.path.join(OUT, "screens_index.json"), "w"), indent=1)
    print("SCREENS", os.path.join(OUT, "T_Kit_Screens.png"))


if __name__ == "__main__":
    main()
