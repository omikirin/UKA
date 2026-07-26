#!/usr/bin/env python3
"""PNGを埋め込んだだけのSVGを、本物の色面SVG（FILL SVG）に起こす

彩色の納品で `<image href="data:image/png;base64,...">` だけのSVGが来ることがある。
拡張子はSVGでも中身はラスタなので、拡大すると眠くなるしファイルも重い。

  python3 tools/raster_to_fill_svg.py <in.svg|in.png|dir> <out.svg|dir> [--colors 12]

ディレクトリを渡すと、**全部の画素から共通のパレットを1つ作って全カットで使う**。
1枚ずつ減色すると同じ髪や袴がカットごとに違う色に丸められ、並べたときに
色味が揃わない。カットごとに最適化したいときだけ --per-file を付ける。

やること:
  1. 埋め込みPNG（またはPNGそのもの）を取り出す
  2. **外周につながる白**だけを透明にする（キャラの中の白は残す。装束や靴下が
     白いので、白を一律に抜くと体に穴が空く）
  3. 絵の外形でタイトに切り抜く
  4. **線画と色面を分けて起こす**。線を残したまま減色すると、細い黒線が中間色に
     潰れて輪郭が茶色くにじむ。色面側からは線を消し（まわりの塗りで埋め）、
     線は別に二値でトレースして最前面に重ねる
  5. 色数を落としてから vtracer を colormode="color" でかける
  6. 隣り合う色面の隙間を、fillと同色のstrokeで塞ぐ

出力は `<g id="FILL">` と `<g id="LINE">` の2層で、手描きの納品SVGと同じ構造。
色数は12が目安。増やすと陰影は残るがパスが増えて重くなる。
"""
import sys, os, re, io, base64, glob, tempfile
import numpy as np
import vtracer
from PIL import Image, ImageFilter
from scipy import ndimage

WHITE = 243        # これ以上明るければ「白」
SPECKLE = 20       # これより小さい色の粒は捨てる
INK_LEVEL = 110    # これより暗ければ線画とみなす


def _load(path):
    """SVG(PNG埋め込み) か PNG を RGBA で読む"""
    if path.lower().endswith(".png"):
        return Image.open(path).convert("RGBA")
    s = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r'(?:xlink:)?href="data:image/png;base64,([^"]+)"', s)
    if not m:
        raise SystemExit(f"{os.path.basename(path)}: 埋め込みPNGが見つからない")
    return Image.open(io.BytesIO(base64.b64decode(re.sub(r"\s", "", m.group(1))))).convert("RGBA")


def _cut_background(im):
    """外周につながる白だけ透明にして、絵の外形で切り抜く"""
    a = np.array(im)
    white = a[..., :3].min(axis=2) >= WHITE
    lab, _ = ndimage.label(white)
    edge = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    edge.discard(0)
    a[..., 3] = np.where(np.isin(lab, list(edge)), 0, 255)
    out = Image.fromarray(a)
    bb = out.getbbox()
    return out.crop(bb) if bb else out


def _inpaint_lines(rgb, ink):
    """線の画素を、まわりの塗りの色で埋める

    線を残したまま減色すると、細い黒線が中間色に潰れて輪郭が茶色くにじむ。
    色面と線は別々に起こして重ねるのが正解なので、色面側からは線を消しておく。
    """
    a = rgb.astype(np.int16)
    m = ink.copy()
    for _ in range(24):
        if not m.any():
            break
        # 未確定画素を、確定している近傍の平均で埋める（1画素ずつ外から浸食）
        known = (~m).astype(np.float32)
        acc = np.zeros(a.shape, np.float32)
        for ch in range(3):
            acc[..., ch] = ndimage.uniform_filter(a[..., ch] * known, 3)
        cnt = ndimage.uniform_filter(known, 3)
        fill = np.zeros_like(acc)
        ok = cnt > 0.01
        for ch in range(3):
            fill[..., ch] = np.where(ok, acc[..., ch] / np.maximum(cnt, 1e-6), 255)
        newly = m & ok
        a[newly] = fill[newly].astype(np.int16)
        m &= ~newly
    a[m] = 255
    return a.astype(np.uint8)


def _trace(img, out, **kw):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    vtracer.convert_image_to_svg_py(tmp.name, out, **kw)
    os.unlink(tmp.name)
    s = open(out).read()
    inner = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S)
    return re.sub(r"</svg>\s*$", "", inner, flags=re.S).strip()


def build_palette(srcs, colors):
    """複数枚から共通のパレットを作る

    1枚ずつ減色すると、同じ髪・同じ袴でもカットごとに色が少しずつ違う色に
    丸められ、並べたときに色味が揃わない。全部の画素をまとめて1回だけ
    減色し、そのパレットを全カットで使い回す。
    """
    px = []
    for s in srcs:
        im = _cut_background(_load(s))
        a = np.array(im)
        mx = a[..., :3].max(axis=2).astype(np.int16)
        mn = a[..., :3].min(axis=2).astype(np.int16)
        ink = (mx < INK_LEVEL) & ((mx - mn) < 50) & (a[..., 3] > 0)
        body = _inpaint_lines(a[..., :3], ink)[a[..., 3] > 0]
        # 大きい絵に引きずられないよう、1枚あたり同じ枚数だけ抜く
        idx = np.linspace(0, len(body) - 1, min(len(body), 200000)).astype(int)
        px.append(body[idx])
    allpx = np.concatenate(px)
    strip = Image.fromarray(allpx.reshape(-1, 1, 3).astype(np.uint8))
    return strip.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)


def _snap_colors(svg, palette):
    """SVG中の塗り色を、いちばん近いパレット色に置き換える"""
    # int16 だと (0-255)^2 が桁あふれして負になり、色が逆に吸着する
    pal = np.array(palette.getpalette()).reshape(-1, 3).astype(np.int32)
    used = sorted({i for _, i in (palette.getcolors() or [])})
    if used:
        pal = pal[used]

    def rep(m):
        h = m.group(1)
        c = np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.int32)
        k = int(np.argmin(((pal - c) ** 2).sum(axis=1)))
        return 'fill="#%02x%02x%02x"' % tuple(pal[k])

    return re.sub(r'fill="(#[0-9a-fA-F]{6})"', rep, svg)


def convert(src, dst, colors=12, palette=None):
    im = _cut_background(_load(src))
    W, H = im.size
    a = np.array(im)
    alpha = a[..., 3]
    # 線画は「暗くて色みが無い」画素。平均輝度だけで見ると、赤い袴のような
    # 濃い色面まで線と判定して真っ黒になる（実際になった）ので彩度も見る。
    mx = a[..., :3].max(axis=2).astype(np.int16)
    mn = a[..., :3].min(axis=2).astype(np.int16)
    ink = (mx < INK_LEVEL) & ((mx - mn) < 50) & (alpha > 0)

    # --- 色面レイヤ（線を消してから減色）
    flat = _inpaint_lines(a[..., :3], ink)
    rgb = Image.fromarray(flat).filter(ImageFilter.MedianFilter(3))
    if palette is not None:
        q = rgb.quantize(palette=palette, dither=Image.NONE)
    else:
        q = rgb.quantize(colors=colors, method=Image.MEDIANCUT, dither=Image.NONE)
    fill_rgba = np.array(q.convert("RGB").convert("RGBA"))
    fill_rgba[..., 3] = alpha
    fill = _trace(Image.fromarray(fill_rgba), dst + ".tmp1",
                  colormode="color", mode="spline", filter_speckle=SPECKLE,
                  color_precision=6, layer_difference=16,
                  corner_threshold=60, length_threshold=4.0, splice_threshold=45)
    # vtracer は指定した色をそのまま使わず、面ごとに色を作り直す。
    # 共通パレットを渡した意味が無くなるので、出力の色をパレットに吸着させる。
    if palette is not None:
        fill = _snap_colors(fill, palette)
    # 色面どうしの髪の毛ほどの隙間を、自分の色のstrokeで塞ぐ
    fill = re.sub(r'fill="(#[0-9a-fA-F]{6})"', r'fill="\1" stroke="\1" stroke-width="1"', fill)

    # --- 線画レイヤ（二値でトレースして最前面に載せる）
    li = np.zeros((H, W, 4), np.uint8)
    li[..., :3] = np.where(ink[..., None], 0, 255)
    li[..., 3] = 255
    line = _trace(Image.fromarray(li), dst + ".tmp2",
                  colormode="binary", mode="spline", filter_speckle=4,
                  corner_threshold=55, length_threshold=3.5)

    for t in (dst + ".tmp1", dst + ".tmp2"):
        if os.path.exists(t):
            os.unlink(t)
    open(dst, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}">'
        f'<g id="FILL">{fill}</g><g id="LINE">{line}</g></svg>')
    return im.size, os.path.getsize(dst)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    a, b = sys.argv[1], sys.argv[2]
    n = int(sys.argv[sys.argv.index("--colors") + 1]) if "--colors" in sys.argv else 12
    if os.path.isdir(a):
        os.makedirs(b, exist_ok=True)
        files = []
        for f in sorted(glob.glob(os.path.join(a, "*.svg")) + glob.glob(os.path.join(a, "*.png"))):
            base = os.path.splitext(os.path.basename(f))[0]
            if f.endswith(".png") and os.path.exists(os.path.join(a, base + ".svg")):
                continue          # 同名のSVGがあるならそちらを使う
            files.append((f, base))
        pal = None if "--per-file" in sys.argv else build_palette([f for f, _ in files], n)
        if pal is not None:
            print(f"共通パレット{n}色を{len(files)}枚から作成")
        for f, base in files:
            sz, by = convert(f, os.path.join(b, base + ".svg"), n, pal)
            print(f"{base}: {sz[0]}x{sz[1]} → {by/1024:.0f}KB")
    else:
        sz, by = convert(a, b, n)
        print(f"{os.path.basename(a)}: {sz[0]}x{sz[1]} → {by/1024:.0f}KB")
