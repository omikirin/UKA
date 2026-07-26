#!/usr/bin/env python3
"""行×列シート抽出(通し番号ラベル自動除去・高精細トレース)
usage: python3 extract_sheet.py <sheet.png> <ids.json> <rows> <cols> <outdir> <tmpdir>
env: TARGET_W(作業解像度の目標幅,4600) INK_LEVEL(線とみなす明度,160)
     INK_ADAPTIVE(まわりとの明度差で線を拾う。薄い線画向け。6〜10が目安) DUMP_DROPPED(除去成分のPNG出力先)

番号除去のルール(位置は絵に対する相対で判定する。グリッド座標は当てにしない):
  1) 小型成分で、キャラ本体(最大成分)の上端より上/下端より下の余白帯にある
  2) 自分の行帯にキャラの線が無い、または文字幅以上離れて孤立している
  3) シート全体の番号文字の高さ中央値と揃っている(絵の効果線・汗などを守る)
  4) 1〜3を満たす種から、同じ高さで横に隣接する成分を数珠つなぎに回収(3桁を丸ごと)
"""
import sys, os, re, json
import numpy as np
from PIL import Image
from scipy import ndimage
import vtracer

Image.MAX_IMAGE_PIXELS = None
png, ids_json, rows, cols, outdir, tmpdir = sys.argv[1:7]
rows, cols = int(rows), int(cols)
ids = json.load(open(ids_json))
os.makedirs(outdir, exist_ok=True)
os.makedirs(tmpdir, exist_ok=True)
TARGET_W = int(os.environ.get("TARGET_W", "4600"))
DUMP = os.environ.get("DUMP_DROPPED")

pil = Image.open(png).convert("L")
SC = max(1, round(TARGET_W / pil.width))
pil = pil.resize((pil.width * SC, pil.height * SC), Image.LANCZOS)
a = np.array(pil)
dark = (a < 128).mean()
assert 0.005 < dark < 0.5, f"入力異常: dark={dark:.2%}"
# 線の濃さの閾値。細かい模様(セーターのリブ編みなど)が薄いグレーで描かれている
# 素材では、160だと模様が丸ごと落ちる。INK_LEVELで上げられるようにしてある。
INK_LEVEL = int(os.environ.get("INK_LEVEL", "160"))
# INK_ADAPTIVE=<差> を渡すと、明度の絶対値ではなく「まわりの紙の白さとの差」で
# 線を拾う。全身のカットは頭が小さく、髪の輪郭が薄い細線になるため、固定閾値だと
# 濃いところ(前髪)だけ残って髪型が角のように崩れる。局所差なら薄い輪郭も拾える。
ADAPT = os.environ.get("INK_ADAPTIVE")
if ADAPT:
    win = max(15, 10 * SC) | 1
    bg = ndimage.uniform_filter(a.astype(np.float32), size=win)
    ink = ndimage.binary_closing(bg - a > float(ADAPT), np.ones((3, 3)))
else:
    ink = a < INK_LEVEL
H, W = a.shape
lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
sizes = ndimage.sum(ink, lab, range(1, n + 1))
objs = ndimage.find_objects(lab)
ch, cw = H / rows, W / cols
MIN_PX = (SC * SC) * 20  # 元解像度で20px相当未満はノイズ

cells = {}
for i, (s, o) in enumerate(zip(sizes, objs), 1):
    if s < MIN_PX:
        continue
    cy = (o[0].start + o[0].stop) / 2
    cx = (o[1].start + o[1].stop) / 2
    r = min(int(cy // ch), rows - 1)
    co = min(int(cx // cw), cols - 1)
    cells.setdefault(r * cols + co, []).append({"id": i, "size": s, "bbox": o})


def rect(c):
    return (c["bbox"][0].start, c["bbox"][0].stop, c["bbox"][1].start, c["bbox"][1].stop)


def analyze(idx):
    """セルの (main, 番号候補リスト) を返す"""
    mem = cells.get(idx, [])
    if not mem:
        return None, [], []
    main = max(mem, key=lambda c: c["size"])
    my0, my1, mx0, mx1 = rect(main)
    mh = my1 - my0
    mainmask = lab[my0:my1, mx0:mx1] == main["id"]

    def isolated(c):
        y0, y1, x0, x1 = rect(c)
        band = mainmask[max(0, y0 - my0):max(0, y1 - my0)]
        colsx = np.where(band.any(axis=0))[0] if band.size else np.array([])
        if colsx.size == 0:
            return True
        lo, hi = mx0 + colsx.min(), mx0 + colsx.max()
        return max(lo - x1, x0 - hi, 0) > 0.8 * max(x1 - x0, y1 - y0)

    cand = []
    for c in mem:
        if c is main:
            continue
        y0, y1, x0, x1 = rect(c)
        if (y1 - y0) > ch * 0.10 or c["size"] > main["size"] * 0.25:
            continue
        margin = (y1 <= my0 + 0.15 * mh) or (y0 >= my1 - 0.12 * mh)
        if margin and isolated(c):
            cand.append(c)
    return main, mem, cand


# --- pass1: シート全体で番号文字の高さ中央値を求める ---
pre = {i: analyze(i) for i in range(len(ids))}
hs = [rect(c)[1] - rect(c)[0] for _, _, cand in pre.values() for c in cand]
HD = float(np.median(hs)) if hs else 0.0

report = []
for idx, cid in enumerate(ids):
    main, mem, cand = pre[idx]
    if main is None:
        report.append(f"EMPTY {cid}")
        continue

    def digit_like(c):
        h = rect(c)[1] - rect(c)[0]
        return HD == 0 or 0.6 * HD <= h <= 1.45 * HD

    labels = [c for c in cand if digit_like(c)]
    # 種から同じ高さ・横に隣接する成分を回収(桁が絵に近くて孤立判定に落ちた分の救済)
    pool = [c for c in mem if c is not main and c not in labels and digit_like(c)
            and c["size"] <= main["size"] * 0.25]
    changed = True
    while changed:
        changed = False
        for c in list(pool):
            y0, y1, x0, x1 = rect(c)
            for g in labels:
                gy0, gy1, gx0, gx1 = rect(g)
                if min(y1, gy1) - max(y0, gy0) <= 0.5 * min(y1 - y0, gy1 - gy0):
                    continue
                if max(gx0 - x1, x0 - gx1, 0) < 1.2 * max(gy1 - gy0, y1 - y0):
                    labels.append(c)
                    pool.remove(c)
                    changed = True
                    break

    lab_ids = {c["id"] for c in labels}
    sel_cs = [c for c in mem if c["id"] not in lab_ids]
    if not sel_cs:
        report.append(f"EMPTY {cid} (全成分が番号判定)")
        continue
    if DUMP and lab_ids:
        dy0 = min(rect(c)[0] for c in labels); dy1 = max(rect(c)[1] for c in labels)
        dx0 = min(rect(c)[2] for c in labels); dx1 = max(rect(c)[3] for c in labels)
        dsel = np.isin(lab[dy0:dy1, dx0:dx1], list(lab_ids))
        Image.fromarray(np.pad(np.where(dsel, 0, 255).astype(np.uint8), 12,
                               constant_values=255)).save(os.path.join(DUMP, f"{cid}.png"))

    y0 = min(rect(c)[0] for c in sel_cs); y1 = max(rect(c)[1] for c in sel_cs)
    x0 = min(rect(c)[2] for c in sel_cs); x1 = max(rect(c)[3] for c in sel_cs)
    sel = np.isin(lab[y0:y1, x0:x1], [c["id"] for c in sel_cs])
    pad = max(10, int(min(y1 - y0, x1 - x0) * 0.03))
    crop = np.pad(np.where(sel, 0, 255).astype(np.uint8), pad, constant_values=255)
    tmp = os.path.join(tmpdir, "c.png")
    Image.fromarray(crop).save(tmp)
    if os.environ.get("DUMP_CROP"):
        Image.fromarray(crop).save(os.path.join(os.environ["DUMP_CROP"], f"{cid}.png"))
    out = os.path.join(outdir, f"{cid}.svg")
    vtracer.convert_image_to_svg_py(tmp, out, colormode="binary", mode="spline",
                                    filter_speckle=8, corner_threshold=55,
                                    length_threshold=3.5)
    s2 = open(out).read()
    s2 = re.sub(r"(\d+\.\d{2})\d+", r"\1", s2)
    w2 = float(re.search(r'width="([\d.]+)', s2).group(1))
    h2 = float(re.search(r'height="([\d.]+)', s2).group(1))
    s2 = s2.replace(f'width="{w2:g}"', f'viewBox="0 0 {w2:g} {h2:g}" width="{w2:g}"', 1)
    open(out, "w").write(s2)
    report.append(f"OK {cid} {x1-x0}x{y1-y0}px drop={len(lab_ids)}")

print(f"{os.path.basename(png)} SC={SC} digitH={HD:.0f}")
for r in report:
    print("  ", r)
