"""Contact sheet of a shot folder: python Tools/Shots/sheet.py <folder> <out.png> [columns] [width]"""
import glob
import os
import sys

from PIL import Image, ImageDraw

folder, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 2
w = int(sys.argv[4]) if len(sys.argv) > 4 else 800
h = w * 9 // 16
files = sorted(glob.glob(os.path.join(folder, "*.png")))
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (w * cols, h * rows))
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((w, h))
    ImageDraw.Draw(im).text((8, 8), os.path.basename(f), fill=(255, 255, 0))
    sheet.paste(im, ((i % cols) * w, (i // cols) * h))
sheet.save(out)
