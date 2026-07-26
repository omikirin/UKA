#!/usr/bin/env python3
"""着色済みベクターシートを1カットずつのセルSVGに切り分ける

彩色シートは「1536×1024に3行×5列＝15カット」で納品される。ラスタ用の
`sheet_extract.py` は二値化してトレースする白黒専用なので、カラーには使えない。
こちらはSVGのパスをそのまま扱い、色（fill）を保ったままセルに分ける。

  python3 tools/slice_color_sheet.py <sheet.svg> <ids.json> <rows> <cols> <outdir>

やること:
  1. キャンバス全面を覆う白パス（BACKGROUND群）を捨てる。残すとコマの背景を覆う
  2. 残りのパスを bbox の中心でグリッドのセルに振り分ける
  3. セルごとに、絵から離れた小さな成分（通し番号）を落とす
  4. セルの実寸に viewBox を合わせて書き出す（レンダラはこれで正しい大きさに置く）
"""
import sys, os, re, json
import numpy as np

PATH_RE = r'<path[^>]*/>|<path[^>]*>.*?</path>'


def path_bbox(p):
    d = re.search(r'd="([^"]*)"', p)
    if not d:
        return None
    nums = [float(v) for v in re.findall(r'-?\d+\.?\d*', d.group(1))]
    xs, ys = nums[0::2], nums[1::2]
    if not xs or not ys:
        return None
    tx = ty = 0.0
    tm = re.search(r'translate\(([-\d.]+)[,\s]+([-\d.]+)\)', p)
    if tm:
        tx, ty = float(tm.group(1)), float(tm.group(2))
    return (min(xs) + tx, min(ys) + ty, max(xs) + tx, max(ys) + ty)


def is_canvas_white(p, W, H):
    """キャンバス全面の白い下敷きか"""
    f = re.search(r'fill="(?:#([0-9a-fA-F]{6})|rgb\((\d+),\s*(\d+),\s*(\d+)\))"', p)
    if not f:
        return False
    if f.group(1):
        r, g, b = (int(f.group(1)[i:i+2], 16) for i in (0, 2, 4))
    else:
        r, g, b = int(f.group(2)), int(f.group(3)), int(f.group(4))
    if min(r, g, b) < 245:
        return False
    bb = path_bbox(p)
    return bb is not None and (bb[2] - bb[0]) > W * 0.9 and (bb[3] - bb[1]) > H * 0.9


def main():
    sheet, ids_json, rows, cols, outdir = sys.argv[1:6]
    rows, cols = int(rows), int(cols)
    ids = json.load(open(ids_json))
    os.makedirs(outdir, exist_ok=True)
    src = open(sheet).read()
    vb = re.search(r'viewBox="([-\d.\s]+)"', src)
    VX, VY, W, H = [float(v) for v in vb.group(1).split()]
    paths = re.findall(PATH_RE, src, flags=re.S)
    kept, dropped_bg = [], 0
    for p in paths:
        bb = path_bbox(p)
        if bb is None:
            continue
        if is_canvas_white(p, W, H):
            dropped_bg += 1
            continue
        kept.append((p, bb))

    ch, cw = H / rows, W / cols
    cells = {}
    for p, bb in kept:
        cy, cx = (bb[1] + bb[3]) / 2, (bb[0] + bb[2]) / 2
        r = min(int((cy - VY) // ch), rows - 1)
        c = min(int((cx - VX) // cw), cols - 1)
        cells.setdefault(r * cols + c, []).append((p, bb))

    made = 0
    for idx, cid in enumerate(ids):
        mem = cells.get(idx, [])
        if not mem:
            print(f"  EMPTY {cid}")
            continue
        # bboxが接している者どうしを束ね、いちばん大きい塊をキャラ本体とする。
        # 通し番号や隣のカットの食い込みは別の塊になるので自然に落ちる。
        # (「最大パスのbbox外を捨てる」方式は、色ごとにパスが分かれた絵で
        #  頭の花や顔まで巻き添えにする。実際に一度消した)
        par = list(range(len(mem)))

        def find(a):
            while par[a] != a:
                par[a] = par[par[a]]
                a = par[a]
            return a

        order = sorted(range(len(mem)), key=lambda i: mem[i][1][0])
        for ii in range(len(order)):
            i = order[ii]
            bi = mem[i][1]
            for jj in range(ii + 1, len(order)):
                j = order[jj]
                bj = mem[j][1]
                if bj[0] > bi[2]:
                    break
                if not (bi[2] < bj[0] or bj[2] < bi[0] or bi[3] < bj[1] or bj[3] < bi[1]):
                    ra, rb = find(i), find(j)
                    if ra != rb:
                        par[rb] = ra
        groups = {}
        for i in range(len(mem)):
            groups.setdefault(find(i), []).append(i)

        def span(g):
            xs = [mem[i][1][0] for i in g] + [mem[i][1][2] for i in g]
            ys = [mem[i][1][1] for i in g] + [mem[i][1][3] for i in g]
            return (max(xs) - min(xs)) * (max(ys) - min(ys))

        main = max(groups.values(), key=span)
        body = [mem[i] for i in sorted(main)]
        drop = len(mem) - len(body)
        x0 = min(b[0] for _, b in body); y0 = min(b[1] for _, b in body)
        x1 = max(b[2] for _, b in body); y1 = max(b[3] for _, b in body)
        pad = max(4.0, min(x1 - x0, y1 - y0) * 0.03)
        x0 -= pad; y0 -= pad; x1 += pad; y1 += pad
        out = (f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'viewBox="{x0:.1f} {y0:.1f} {x1-x0:.1f} {y1-y0:.1f}" '
               f'width="{x1-x0:.0f}" height="{y1-y0:.0f}">'
               + "".join(p for p, _ in body) + "</svg>")
        open(os.path.join(outdir, f"{cid}.svg"), "w").write(out)
        made += 1
    print(f"{os.path.basename(sheet)}: {made}/{len(ids)}カット  "
          f"全面白を除去{dropped_bg}  → {outdir}")


if __name__ == "__main__":
    if len(sys.argv) < 6:
        raise SystemExit(__doc__)
    main()
