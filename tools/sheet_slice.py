#!/usr/bin/env python3
"""発注シートPNGを、実際の余白を見て1カットずつのPNGに切り分ける

`sheet_extract.py` はシートを行×列で等分するが、納品シートは**行の高さが
揃っていないことがある**（実測で1行目348px・2行目288px など）。等分で切ると
隣のカットの足が入り込み、通し番号も1つ上の升目に落ちて消し漏れる。

こちらは縦横の投影から「インクが1画素も無い帯」を探し、広い順に必要な数だけ
選んで切る。等分しないので行の高さが違っても正しく割れる。

  python3 tools/sheet_slice.py <sheet.png> <行数> <列数> <出力dir> [接頭辞]
  python3 tools/sheet_slice.py <sheet.png> auto <カット数> <出力dir> [接頭辞]

**行×列は枚によって違う**（5行3列のシートと3行5列のシートが混在していた）。
auto を渡すと、割り方を両方試してインク量が揃っているほうを選ぶ。

出力は `<接頭辞>r<行>c<列>.png`。読み順（左上から右へ）に並ぶ。
"""
import sys, os
import numpy as np
from PIL import Image

INK = 160


def _cuts(profile, k, min_band=6):
    """インクの薄い帯の中央を切り位置として k-1 個返す

    完全に真っ白な帯を要求すると、隣のカットの線が境界をわずかに越えている
    シートで割れなくなる。閾値を少しずつ緩めて、必要な本数が取れたところで止める。
    """
    L = len(profile)
    ideal = [L * i / k for i in range(1, k)]
    win = L / k * 0.35          # 等分位置からこれ以上離れた帯は切れ目とみなさない
    for tol in (0, 1, 2, 4, 8, 16, 32, 64):
        bands = _bands(profile <= tol, min_band)
        picked = []
        for t in ideal:
            near = [b for b in bands if abs((b[1] + b[2]) / 2 - t) <= win]
            if not near:
                break
            b = max(near)       # いちばん広い帯
            picked.append((b[1] + b[2]) // 2)
        if len(picked) == k - 1 and len(set(picked)) == k - 1:
            return sorted(picked)
    return []


def _bands(empty, min_band):
    out, s = [], None
    for i, e in enumerate(empty):
        if e and s is None:
            s = i
        elif not e and s is not None:
            out.append((i - s, s, i)); s = None
    if s is not None:
        out.append((len(empty) - s, s, len(empty)))
    return [b for b in out if b[1] > 0 and b[2] < len(empty) and b[0] >= min_band]


def _cuts_at(profile, k, min_band, tol):
    empty = profile <= tol
    bands, s = [], None
    for i, e in enumerate(empty):
        if e and s is None:
            s = i
        elif not e and s is not None:
            bands.append((i - s, s, i)); s = None
    if s is not None:
        bands.append((len(empty) - s, s, len(empty)))
    # 端の帯は余白なので候補から外す
    inner = [b for b in bands if b[1] > 0 and b[2] < len(empty) and b[0] >= min_band]
    inner.sort(reverse=True)
    picked = sorted((b[1] + b[2]) // 2 for b in inner[:k - 1])
    return picked


def slice_sheet(path, rows, cols, outdir, prefix=""):
    im = Image.open(path).convert("RGB")
    g = np.array(im.convert("L"))
    ink = (g < INK).astype(np.uint8)
    ry = _cuts(ink.sum(axis=1), rows)
    rx = _cuts(ink.sum(axis=0), cols)
    if len(ry) != rows - 1 or len(rx) != cols - 1:
        raise SystemExit(f"{os.path.basename(path)}: 切れ目が見つからない "
                         f"(縦{len(ry)+1}行/横{len(rx)+1}列)。余白が繋がっていない可能性")
    ys = [0] + ry + [g.shape[0]]
    xs = [0] + rx + [g.shape[1]]
    os.makedirs(outdir, exist_ok=True)
    made = []
    for r in range(rows):
        for c in range(cols):
            im.crop((xs[c], ys[r], xs[c + 1], ys[r + 1])).save(
                os.path.join(outdir, f"{prefix}r{r}c{c}.png"))
            made.append((r, c))
    return made


def guess_grid(path, n=15):
    """行×列を当てる

    納品シートは枚によって 5行3列だったり 3行5列だったりする。
    決め打ちで切ると、隣のカットが2つ入ったセルと空のセルができる。
    両方で切ってみて、セルごとのインク量が揃っているほうを採る。
    """
    im = Image.open(path).convert("L")
    g = np.array(im)
    ink = (g < INK).astype(np.uint8)
    best = None
    for rows in range(1, n + 1):
        if n % rows:
            continue
        cols = n // rows
        ry = _cuts(ink.sum(axis=1), rows)
        rx = _cuts(ink.sum(axis=0), cols)
        if len(ry) != rows - 1 or len(rx) != cols - 1:
            continue
        ys = [0] + ry + [g.shape[0]]
        xs = [0] + rx + [g.shape[1]]
        fr = []
        for r in range(rows):
            for c in range(cols):
                cell = ink[ys[r]:ys[r + 1], xs[c]:xs[c + 1]]
                fr.append(cell.mean() if cell.size else 0)
        fr = np.array(fr)
        if fr.min() < 0.004:          # ほぼ空のセルがある＝割り方が違う
            continue
        score = fr.std() / max(fr.mean(), 1e-6)
        if best is None or score < best[0]:
            best = (score, rows, cols)
    return best[1:] if best else (0, 0)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    p, outdir = sys.argv[1], sys.argv[4]
    if sys.argv[2] == "auto":
        rows, cols = guess_grid(p, int(sys.argv[3]))
        if not rows:
            raise SystemExit(f"{os.path.basename(p)}: 割り方が決まらない")
    else:
        rows, cols = int(sys.argv[2]), int(sys.argv[3])
    pre = sys.argv[5] if len(sys.argv) > 5 else ""
    n = slice_sheet(p, rows, cols, outdir, pre)
    print(f"{os.path.basename(p)}: {rows}行{cols}列 / {len(n)}カットに切った → {outdir}")
