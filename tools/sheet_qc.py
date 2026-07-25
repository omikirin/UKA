#!/usr/bin/env python3
"""残存ラベル検出: 出力セル内に「余白に孤立した小成分」が残っていないか機械検品
usage: python3 check_residual.py <svgdir> [tmpdir]
"""
import sys, os, glob
import numpy as np, cairosvg
from PIL import Image
from scipy import ndimage

d = sys.argv[1]
tmp = sys.argv[2] if len(sys.argv) > 2 else "/tmp"
os.makedirs(tmp, exist_ok=True)
t = os.path.join(tmp, "qc.png")
flag = []
for f in sorted(glob.glob(d + "/*.svg")):
    cairosvg.svg2png(url=f, write_to=t, output_height=500, background_color="white")
    a = np.array(Image.open(t).convert("L"))
    ink = a < 128
    H, W = a.shape
    lab, n = ndimage.label(ink, np.ones((3, 3)))
    if n == 0:
        flag.append((os.path.basename(f)[:-4], "EMPTY"))
        continue
    sizes = ndimage.sum(ink, lab, range(1, n + 1))
    objs = ndimage.find_objects(lab)
    mi = int(np.argmax(sizes))
    mo = objs[mi]
    mmask = lab[mo[0], mo[1]] == mi + 1
    mh = mo[0].stop - mo[0].start
    for i, (s, o) in enumerate(zip(sizes, objs)):
        if i == mi or s < 8 or s > sizes[mi] * 0.05:
            continue
        y0, y1, x0, x1 = o[0].start, o[0].stop, o[1].start, o[1].stop
        if (y1 - y0) > H * 0.10:
            continue
        if not (y1 <= mo[0].start + 0.10 * mh or y0 >= mo[0].stop - 0.10 * mh):
            continue
        band = mmask[max(0, y0 - mo[0].start):max(0, y1 - mo[0].start)]
        cx = np.where(band.any(axis=0))[0] if band.size else np.array([])
        if cx.size == 0:
            gap = 1e9
        else:
            lo, hi = mo[1].start + cx.min(), mo[1].start + cx.max()
            gap = max(lo - x1, x0 - hi, 0)
        if gap > 0.8 * max(x1 - x0, y1 - y0):
            flag.append((os.path.basename(f)[:-4],
                         f"isolated@({x0/W:.2f},{(y0+y1)/2/H:.2f}) {x1-x0}x{y1-y0}"))
            break
print(f"{d}: flagged {len(flag)}/{len(glob.glob(d+'/*.svg'))}")
for a, b in flag:
    print("  ", a, b)
