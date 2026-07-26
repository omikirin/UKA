#!/usr/bin/env python3
"""発注シートPNGから通し番号ラベルだけを白く塗って消す

`sheet_extract.py` 側のラベル除去は「セルの中で絵から離れた小さな成分」を探すが、
これは1カットに1人が立っているシートを前提にしている。二人が横いっぱいに描かれた
カットや、机・階段など画面いっぱいの小物があるカットでは、ラベルが絵のbbox内に
入ってしまい落とせない（実際に240セル中156セルで数字が残った）。

こちらは**シート全体から数字の並びを直接探す**。3桁の通し番号は
  ・高さのそろった小さな成分が
  ・横一列にベースラインをそろえて
  ・3つ並び
  ・まわりが白で囲まれている
という形をしていて、絵の一部がこの条件を全部満たすことはまずない。

  python3 tools/sheet_delabel.py <in.png|dir> <out.png|dir> [行数 列数]

行数・列数を渡すと「1セルにつき最も左上の候補1個だけ」に絞る。絵の細部が
数字の条件を満たしてしまう分を落とせるので、基本は渡したほうがいい。

セル数×1個ずつ消えるのが正常（3行5列なら15個）。数が合わないときは
--debug を付けると見つけた位置を出す。
"""
import sys, os, glob
import numpy as np
from PIL import Image
from scipy import ndimage

INK = 160          # これより暗ければ線
H_MIN, H_MAX = 11, 34      # 数字1文字の高さ
W_MIN, W_MAX = 3, 20       # 数字1文字の幅
GAP = 12           # 隣の桁との間隔の上限
BASE_TOL = 5       # ベースラインのずれの許容
RING = 9           # まわりの白さを見る幅
PAD = 3            # 塗りつぶすときの余白


def find_labels(gray, rows=0, cols=0, debug=False):
    ink = gray < INK
    lab, n = ndimage.label(ink)
    objs = ndimage.find_objects(lab)
    cands = []
    for i, sl in enumerate(objs):
        ys, xs = sl
        h, w = ys.stop - ys.start, xs.stop - xs.start
        if H_MIN <= h <= H_MAX and W_MIN <= w <= W_MAX:
            cands.append((xs.start, ys.start, xs.stop, ys.stop, i + 1))
    cands.sort(key=lambda c: (c[3], c[0]))     # 下端→左端の順

    runs, used = [], set()
    for a in range(len(cands)):
        if a in used:
            continue
        run = [a]
        for b in range(a + 1, len(cands)):
            if b in used:
                continue
            last = cands[run[-1]]
            cur = cands[b]
            if abs(cur[3] - last[3]) <= BASE_TOL and 0 <= cur[0] - last[2] <= GAP:
                run.append(b)
        if len(run) >= 2:
            for r in run:
                used.add(r)
            runs.append([cands[r] for r in run])

    out = []
    for run in runs:
        x0 = min(c[0] for c in run); y0 = min(c[1] for c in run)
        x1 = max(c[2] for c in run); y1 = max(c[3] for c in run)
        hs = [c[3] - c[1] for c in run]
        if max(hs) - min(hs) > 8:              # 高さがそろっていない＝絵
            continue
        # まわりに「絵」が来ていないか。細かいゴミは無視し、大きな成分だけを見る
        # （白で囲まれていることを厳密に要求すると、数字の脇に散った点1つで落ちる）
        ry0, ry1 = max(0, y0 - RING), min(gray.shape[0], y1 + RING)
        rx0, rx1 = max(0, x0 - RING), min(gray.shape[1], x1 + RING)
        ring = lab[ry0:ry1, rx0:rx1].copy()
        ring[y0 - ry0:y1 - ry0, x0 - rx0:x1 - rx0] = 0
        near_art = False
        for cid in np.unique(ring):
            if cid == 0:
                continue
            ys2, xs2 = objs[cid - 1]
            if (ys2.stop - ys2.start) > H_MAX or (xs2.stop - xs2.start) > W_MAX * 3:
                near_art = True
                break
        if near_art:
            continue
        out.append((x0, y0, x1, y1, len(run)))
    # 1セルに1個だけ残す。ラベルはセルの中でいちばん左上にあるので、
    # セルごとに最も左上の候補を採る（絵の細部が条件を満たしても取り違えにくい）
    if rows and cols:
        H, W = gray.shape
        ch, cw = H / rows, W / cols
        best = {}
        for o in out:
            key = (min(int(o[1] // ch), rows - 1), min(int(o[0] // cw), cols - 1))
            cur = best.get(key)
            if cur is None or (o[1], o[0]) < (cur[1], cur[0]):
                best[key] = o
        out = sorted(best.values(), key=lambda o: (o[1], o[0]))
    if debug:
        for o in out:
            print("   ラベル", o)
    return out


def delabel(src, dst, rows=0, cols=0, debug=False):
    im = Image.open(src).convert("RGB")
    g = np.array(im.convert("L"))
    boxes = find_labels(g, rows, cols, debug)
    a = np.array(im)
    for x0, y0, x1, y1, _ in boxes:
        a[max(0, y0 - PAD):y1 + PAD, max(0, x0 - PAD):x1 + PAD] = 255
    Image.fromarray(a).save(dst)
    return len(boxes)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    a, b = sys.argv[1], sys.argv[2]
    dbg = "--debug" in sys.argv
    rows = int(sys.argv[3]) if len(sys.argv) > 4 and sys.argv[3].isdigit() else 0
    cols = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].isdigit() else 0
    if os.path.isdir(a):
        os.makedirs(b, exist_ok=True)
        for f in sorted(glob.glob(os.path.join(a, "*.png"))):
            n = delabel(f, os.path.join(b, os.path.basename(f)), rows, cols, dbg)
            print(f"{os.path.basename(f)}: {n}個消した")
    else:
        print(f"{os.path.basename(a)}: {delabel(a, b, rows, cols, dbg)}個消した")
