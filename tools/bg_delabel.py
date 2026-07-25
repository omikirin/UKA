#!/usr/bin/env python3
"""背景SVGに焼き込まれたIDラベル(「BG046」等)を消す

発注シートから切り出した背景には、絵の左上にID文字がそのまま残っているものがある。
文字は隣り合う字がくっついて1成分になるため「小さな孤立成分」では拾えない。
そこで「左上の帯にある、文字の高さ・横長の成分」をラベル枠として自動検出し、
枠内のサブパスを削除したうえで、枠の周囲から拾った地色でパッチを当てる。

  python3 tools/bg_delabel.py scan  <svgdir>            # ラベルのある背景を一覧
  python3 tools/bg_delabel.py strip <in.svg> <out.svg>  # 自動検出して消す
  python3 tools/bg_delabel.py strip <in.svg> <out.svg> --box x0,y0,x1,y1   # 枠を手で指定(0-1)
"""
import sys, os, re, glob
import numpy as np
import cairosvg
from PIL import Image
from scipy import ndimage

PATH_RE = r'<path[^>]*/>|<path[^>]*>.*?</path>'
RW = 700  # 検出用ラスタ幅


def raster(p, w=RW):
    cairosvg.svg2png(url=p, write_to="/tmp/_dl.png", output_width=w, background_color="white")
    return np.array(Image.open("/tmp/_dl.png").convert("L"))


def find_label(a):
    """左上の帯からラベルの相対枠 (x0,y0,x1,y1) を返す。無ければ None"""
    H, W = a.shape
    ink = a < 150
    lab, n = ndimage.label(ink, np.ones((3, 3)))
    if n == 0:
        return None
    hits = []
    for o in ndimage.find_objects(lab):
        y0, y1, x0, x1 = o[0].start, o[0].stop, o[1].start, o[1].stop
        h, w = y1 - y0, x1 - x0
        if y0 > H * 0.14 or x0 > W * 0.30:          # 左上隅から始まっている
            continue
        if not (H * 0.035 <= h <= H * 0.20):         # 文字の高さ
            continue
        if not (W * 0.05 <= w <= W * 0.55):          # 1文字〜数文字ぶんの横幅
            continue
        hits.append((x0, y0, x1, y1))
    if not hits:
        return None
    x0 = min(h[0] for h in hits); y0 = min(h[1] for h in hits)
    x1 = max(h[2] for h in hits); y1 = max(h[3] for h in hits)
    if (x1 - x0) < W * 0.10:                         # 単独の点はラベルとみなさない
        return None
    # ID文字は太い輪郭文字なので枠内のインク密度が高い。風景の線画は薄い
    if (a[y0:y1, x0:x1] < 150).mean() < 0.25:
        return None
    m = 0.012
    return (max(0, x0 / W - m), max(0, y0 / H - m), min(1, x1 / W + m), min(1, y1 / H + m))


def patch_color(a, box):
    """枠のすぐ外側を見て地色(白/黒)を決める"""
    H, W = a.shape
    x0, y0, x1, y1 = [int(v * s) for v, s in zip(box, (W, H, W, H))]
    band = a[max(0, y0):min(H, y1 + max(4, (y1 - y0) // 3)), max(0, x0):min(W, x1)]
    return "black" if band.mean() < 110 else "white"


def subpaths(src):
    out = []
    for p in re.findall(PATH_RE, src, flags=re.S):
        dm = re.search(r'd="([^"]*)"', p)
        if not dm:
            continue
        tmpl = p[:dm.start(1) - 3] + 'd="{D}"' + p[dm.end(1) + 1:]
        tx = ty = 0.0
        tm = re.search(r'translate\(([-\d.]+)[,\s]+([-\d.]+)\)', p)
        if tm:
            tx, ty = float(tm.group(1)), float(tm.group(2))
        for sd in re.split(r'(?=M)', dm.group(1)):
            sd = sd.strip()
            if not sd:
                continue
            nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', sd)]
            xs, ys = nums[0::2], nums[1::2]
            if not xs:
                continue
            out.append((tmpl, sd, (min(xs) + tx, min(ys) + ty, max(xs) + tx, max(ys) + ty)))
    return out


def cmd_scan(args):
    for f in sorted(glob.glob(os.path.join(args[0], "*.svg"))):
        box = find_label(raster(f))
        if box:
            print(f"{os.path.basename(f)[:-4]}  枠 "
                  f"({box[0]:.3f},{box[1]:.3f})-({box[2]:.3f},{box[3]:.3f})")


def cmd_strip(args):
    src_p, out_p = args[0], args[1]
    a = raster(src_p)
    if "--box" in args:
        box = tuple(float(v) for v in args[args.index("--box") + 1].split(","))
    else:
        box = find_label(a)
    if not box:
        print(f"ラベルなし: {src_p}")
        if src_p != out_p:
            open(out_p, "w").write(open(src_p).read())
        return
    col = patch_color(a, box)
    src = open(src_p).read()
    vb = [float(v) for v in re.search(r'viewBox="([-\d.\s]+)"', src).group(1).split()]
    VX, VY, VW, VH = vb
    bx0, by0 = VX + VW * box[0], VY + VH * box[1]
    bx1, by1 = VX + VW * box[2], VY + VH * box[3]
    # パスの削除はしない。ラベルは絵に食い込んでおり、削ると背景の線まで巻き添えになる。
    # 地色のパッチを「最前面」に置いて隠すのが、絵を壊さずに確実に消せる唯一の方法。
    patch = (f'<rect x="{bx0:.2f}" y="{by0:.2f}" width="{bx1-bx0:.2f}" '
             f'height="{by1-by0:.2f}" fill="{col}"/>')
    open(out_p, "w").write(re.sub(r'</svg>\s*$', patch + '</svg>', src, flags=re.S))
    print(f"{os.path.basename(src_p)}: {col}パッチを最前面に -> {out_p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    {"scan": cmd_scan, "strip": cmd_strip}[sys.argv[1]](sys.argv[2:])
