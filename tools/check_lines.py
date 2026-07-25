#!/usr/bin/env python3
"""線の欠落検査: 元シートの二値クロップと、最終SVGのラスタを画素で突き合わせる
usage: python3 check_lines.py <cropdir> <svgdir1> [svgdir2...] [--tmp DIR]
出力: 欠落率(元にあって出力に無いインク) と 最大欠落塊のサイズ・位置
"""
import sys, os, glob
import numpy as np, cairosvg
from PIL import Image
from scipy import ndimage

args = [a for a in sys.argv[1:] if not a.startswith("--")]
tmp = "/tmp/q1"
if "--tmp" in sys.argv:
    tmp = sys.argv[sys.argv.index("--tmp") + 1]
os.makedirs(tmp, exist_ok=True)
cropdir, svgdirs = args[0], args[1:]
t = os.path.join(tmp, "cl.png")
rows = []
for cf in sorted(glob.glob(cropdir + "/*.png")):
    cid = os.path.basename(cf)[:-4]
    svg = None
    for d in svgdirs:
        p = os.path.join(d, cid + ".svg")
        if os.path.exists(p):
            svg = p
            break
    if not svg:
        continue
    src = np.array(Image.open(cf).convert("L"))
    H, W = src.shape
    # 検査は最大900pxに縮小(元は数千px)。線の連続性は縮小でも保たれる
    sc = min(1.0, 900 / max(H, W))
    h2, w2 = max(1, int(H * sc)), max(1, int(W * sc))
    s = np.array(Image.open(cf).convert("L").resize((w2, h2), Image.LANCZOS)) < 150
    cairosvg.svg2png(url=svg, write_to=t, output_width=w2, output_height=h2,
                     background_color="white")
    o = np.array(Image.open(t).convert("L")) < 150
    # 1px のにじみは許容
    od = ndimage.binary_dilation(o, np.ones((3, 3)))
    miss = s & ~od
    if miss.sum() == 0:
        rows.append((0.0, 0, cid, 0, 0))
        continue
    lab, n = ndimage.label(miss, np.ones((3, 3)))
    sz = ndimage.sum(miss, lab, range(1, n + 1))
    k = int(np.argmax(sz))
    o2 = ndimage.find_objects(lab)[k]
    cy = (o2[0].start + o2[0].stop) / 2 / h2
    cx = (o2[1].start + o2[1].stop) / 2 / w2
    rows.append((miss.sum() / max(s.sum(), 1), int(sz[k]), cid, cx, cy))
rows.sort(reverse=True)
print(f"{len(rows)}セル検査  欠落率 平均{np.mean([r[0] for r in rows]):.2%} "
      f"中央値{np.median([r[0] for r in rows]):.2%}")
print("欠落率が大きい順:")
for r, big, cid, cx, cy in rows[:40]:
    print(f"  {cid:14s} 欠落{r:6.2%} 最大塊{big:5d}px @({cx:.2f},{cy:.2f})")
