#!/usr/bin/env python3
"""彩色セルに元の線画を戻し、色のずれを詰める

彩色を外注すると、返ってくるSVGは色面だけで**線画が入っていない**ことがある。
輪郭が線として描かれていないため、色面と色面の境目が白く抜けて
「線が白い」ように見える。目や口だけ黒パスで入っていることも多い。

さらに色面は線画をなぞり直したものなので、元の線画とは数pxずれている。
そのまま線画を重ねると輪郭の外に色がはみ出す。

  python3 tools/color_line_merge.py <彩色dir> <線画dir> <出力dir>

やること:
  1. 彩色SVGから色面レイヤ(FILL)だけを取り出す(彩色側の黒パスは捨てる。
     線画を重ねるので二重になるし、位置もずれている)
  2. 縦800pxでラスタして、色面が線画のシルエットから一番はみ出さない
     平行移動を総当たりで探し、その分だけ色面をずらす
  3. 色面をキャラのシルエット(CHARACTER_CLIP)でクリップする。
     ずらしても残るはみ出しはこれで切れる
  4. 元の線画の黒パスを最前面に載せる

彩色SVGと線画SVGは viewBox が一致している前提(同じ発注シート由来)。
出力後、線画シルエットに対する「はみ出し率」を出す。20%を超えるセルは
平行移動では直らない = 彩色側が別の形に描き直しているので、発注し直すのが早い。
"""
import sys, os, re, glob
import xml.etree.ElementTree as ET
import numpy as np, cairosvg
from PIL import Image
from scipy import ndimage

SEARCH = 14      # 平行移動の探索範囲(縦800px換算のpx)
MEAS_H = 800     # 計測用のラスタ高さ
BAD = 20.0       # これを超えるはみ出し率は「彩色し直し推奨」


def _rast(text, h=MEAS_H):
    open("/tmp/_clm.svg", "w").write(text)
    cairosvg.svg2png(url="/tmp/_clm.svg", write_to="/tmp/_clm.png",
                     output_height=h, background_color="white")
    return np.array(Image.open("/tmp/_clm.png").convert("RGB"))


def _silhouette(line_svg):
    b = _rast(line_svg)
    ink = b.min(axis=2) < 120
    return ndimage.binary_fill_holes(ndimage.binary_closing(ink, np.ones((5, 5))))


def merge(color_p, line_p, out_p):
    col = open(color_p).read()
    lin = open(line_p).read()
    vb = re.search(r'viewBox="([\d.\s]+)"', col).group(1)
    vbl = re.search(r'viewBox="([\d.\s]+)"', lin).group(1)
    if vb != vbl:
        raise SystemExit(f"viewBoxが違う: {color_p} {vb} / {line_p} {vbl}")
    w, h = vb.split()[2], vb.split()[3]
    scale = float(h) / MEAS_H

    fill = re.search(r'(<g id="FILL".*?</g>)\s*<g id="LINE">', col, flags=re.S).group(1)
    base = re.search(r'<g id="BASE_WHITE".*?</g>', col, flags=re.S).group(0)
    clip = re.search(r'<clipPath id="CHARACTER_CLIP">.*?</clipPath>', col, flags=re.S).group(0)
    # 白下敷きは動かさない(背景に対する下敷きなので線画側の位置が正)
    fill_only = fill.replace(base, "")

    sil = _silhouette(lin)
    a = _rast(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" '
              f'width="{w}" height="{h}">{fill_only}</svg>')
    colmask = a.min(axis=2) < 235
    best = None
    for dy in range(-SEARCH, SEARCH + 1):
        for dx in range(-SEARCH, SEARCH + 1):
            s = np.roll(np.roll(colmask, dy, 0), dx, 1)
            o = int((s & ~sil).sum())
            if best is None or o < best[0]:
                best = (o, dx, dy)
    _, dx, dy = best

    black = "".join(p for p in re.findall(r'<path[^>]*/>', lin) if 'fill="#000000"' in p)
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}">'
           f'<defs>{clip}</defs>{base}'
           f'<g clip-path="url(#CHARACTER_CLIP)" '
           f'transform="translate({dx*scale:.2f} {dy*scale:.2f})">{fill_only}</g>'
           f'<g id="LINEART">{black}</g></svg>')
    ET.fromstring(out)          # 壊れたSVGを書き出さない
    open(out_p, "w").write(out)

    a2 = _rast(out)
    col2 = a2.min(axis=2) < 235
    over = (col2 & ~ndimage.binary_dilation(sil, np.ones((5, 5)))).sum() / sil.sum() * 100
    return dx, dy, over


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    cdir, ldir, odir = sys.argv[1:4]
    os.makedirs(odir, exist_ok=True)
    bad = []
    for f in sorted(glob.glob(os.path.join(cdir, "*.svg"))):
        cid = os.path.basename(f)[:-4]
        lp = os.path.join(ldir, cid + ".svg")
        if not os.path.exists(lp):
            print(f"  線画なし {cid}")
            continue
        dx, dy, over = merge(f, lp, os.path.join(odir, cid + ".svg"))
        mark = "  ★彩色し直し推奨" if over > BAD else ""
        print(f"{cid} ずれ補正 dx={dx:+3d} dy={dy:+3d}  はみ出し{over:5.2f}%{mark}")
        if over > BAD:
            bad.append(cid)
    if bad:
        print(f"\n形が合っていないセル({BAD}%超): {', '.join(bad)}")
