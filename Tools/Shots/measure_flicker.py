"""Flicker map for Tools/Shots/flicker_check.json: python Tools/Shots/measure_flicker.py <shots folder> <out.png>.
Prints FLICKER lines (share of pixels changing by more than 8 %% between identical frames)."""
import sys, glob, os
import numpy as np
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]
os.chdir(d)
groups={}
for f in sorted(glob.glob("*.png"))[1:]:
    groups.setdefault(f[3:].rsplit("_",1)[0],[]).append(f)
sheets=[]
for g,fs in groups.items():
    stack=np.stack([np.asarray(Image.open(f).convert("L")).astype(float)/255 for f in fs[1:]])  # skip first (settling)
    stack[:, :60, 1350:]=stack[:, :60, 1350:].mean(0)       # FPS counter
    diff=np.abs(np.diff(stack,axis=0)).max(0)                # biggest frame-to-frame change per pixel
    flicker=(diff>0.08).mean()*100
    print("FLICKER %-12s pixels changing >8%%: %.2f %%   mean change %.4f   max %.2f" % (g, flicker, diff.mean(), diff.max()))
    base=np.asarray(Image.open(fs[-1]).convert("RGB")).astype(float)
    heat=base*0.35; m=diff>0.08
    heat[m]=[255,40,40]
    sheets.append(Image.fromarray(heat.astype("uint8")).resize((800,450)))
s=Image.new("RGB",(1600,450*((len(sheets)+1)//2)))
for i,im in enumerate(sheets): s.paste(im,((i%2)*800,(i//2)*450))
s.save(out)
