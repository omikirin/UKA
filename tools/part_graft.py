#!/usr/bin/env python3
"""セルSVGのパーツ移植(目・口などの1パーツだけ足す)

元シートの時点で目や口が欠けているセルを、別セル(ドナー)の同じパーツで補修する。
座標はすべて 0-1 の相対値で指定するので、セルの実寸を知らなくていい。

  # 1) ドナーから切り出す(左上x,左上y,右下x,右下y)
  python3 tools/part_graft.py cut characters/015_uka/expr/EXP001.svg 0.34 0.40 0.50 0.50 parts/eye_r.svg

  # 2) 直したいセルに重ねる(中心x, 中心y, 幅。--flip で左右反転)
  python3 tools/part_graft.py paste characters/015_uka/expr/EXP021.svg parts/eye_r.svg \
      0.58 0.45 0.16 out.svg [--flip] [--white]

  # 位置合わせ用に、当たり枠を描いた確認PNGを出す
  python3 tools/part_graft.py grid characters/015_uka/expr/EXP021.svg grid.png

--white を付けると、パーツの下に白い矩形を敷いてから重ねる(古い線を隠したいとき)。
"""
import sys, os, re

PATH_RE = r'<path[^>]*/>|<path[^>]*>.*?</path>'


def read_svg(p):
    s = open(p).read()
    vb = re.search(r'viewBox="([-\d.\s]+)"', s)
    if not vb:
        raise SystemExit(f"viewBoxがありません: {p}")
    return s, [float(v) for v in vb.group(1).split()]


def subpaths(src):
    """<path>をサブパスに分解して [(属性テンプレ, d, bbox)] を返す"""
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
            nums = [float(n) for n in re.findall(r'-?\d+\.?\d*', sd)]
            xs, ys = nums[0::2], nums[1::2]
            if not xs or not ys:
                continue
            out.append((tmpl, sd, (min(xs) + tx, min(ys) + ty, max(xs) + tx, max(ys) + ty)))
    return out


def cmd_cut(args):
    src_p, x0, y0, x1, y1, out_p = args[0], *map(float, args[1:5]), args[5]
    src, (VX, VY, VW, VH) = read_svg(src_p)
    bx0, by0 = VX + VW * x0, VY + VH * y0
    bx1, by1 = VX + VW * x1, VY + VH * y1
    groups = {}
    for tmpl, d, bb in subpaths(src):
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        if bx0 <= cx <= bx1 and by0 <= cy <= by1:
            groups.setdefault(tmpl, []).append(d)
    if not groups:
        raise SystemExit("その範囲にパスがありません。範囲を広げてください")
    body = "".join(t.replace("{D}", " ".join(ds)) for t, ds in groups.items())
    os.makedirs(os.path.dirname(out_p) or ".", exist_ok=True)
    open(out_p, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{bx0:.2f} {by0:.2f} '
        f'{bx1-bx0:.2f} {by1-by0:.2f}" width="{bx1-bx0:.0f}" height="{by1-by0:.0f}">{body}</svg>')
    print(f"切り出し: {sum(len(v) for v in groups.values())}サブパス -> {out_p}")


def cmd_paste(args):
    tgt_p, part_p = args[0], args[1]
    cx, cy, pw = map(float, args[2:5])
    out_p = args[5]
    flip = "--flip" in args
    white = "--white" in args
    tgt, (VX, VY, VW, VH) = read_svg(tgt_p)
    part, (PX, PY, PW, PH) = read_svg(part_p)
    inner = re.sub(r'^.*?<svg[^>]*>', '', part, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, flags=re.S)
    w = VW * pw
    h = w * (PH / PW)
    x = VX + VW * cx - w / 2
    y = VY + VH * cy - h / 2
    frag = (f'<svg x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'viewBox="{PX:.2f} {PY:.2f} {PW:.2f} {PH:.2f}" '
            f'preserveAspectRatio="xMidYMid meet">{inner}</svg>')
    if flip:
        frag = f'<g transform="translate({2*x+w:.2f},0) scale(-1,1)">{frag}</g>'
    if white:
        frag = (f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
                f'fill="white"/>') + frag
    open(out_p, "w").write(re.sub(r'</svg>\s*$', frag + '</svg>', tgt, flags=re.S))
    print(f"移植: {part_p} -> {out_p} (中心 {cx},{cy} 幅{pw})")


def cmd_grid(args):
    """位置合わせ用: 0.1刻みの目盛りを重ねたPNGを出す"""
    import cairosvg
    from PIL import Image, ImageDraw
    tgt_p, out_p = args[0], args[1]
    tmp = out_p + ".tmp.png"
    cairosvg.svg2png(url=tgt_p, write_to=tmp, output_height=700, background_color="white")
    im = Image.open(tmp).convert("RGB")
    dr = ImageDraw.Draw(im)
    for i in range(1, 10):
        gx, gy = im.width * i / 10, im.height * i / 10
        dr.line([(gx, 0), (gx, im.height)], fill="#f0a0a0")
        dr.line([(0, gy), (im.width, gy)], fill="#a0c0f0")
        dr.text((gx + 2, 2), f"{i/10:.1f}", fill="#c04040")
        dr.text((2, gy + 2), f"{i/10:.1f}", fill="#4060c0")
    im.save(out_p)
    os.remove(tmp)
    print(f"目盛り付き確認画像: {out_p}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    {"cut": cmd_cut, "paste": cmd_paste, "grid": cmd_grid}[sys.argv[1]](sys.argv[2:])
