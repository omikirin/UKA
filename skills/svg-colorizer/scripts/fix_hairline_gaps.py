#!/usr/bin/env python3
"""色面SVGの「隙間」を塞ぐ

写真やイラストを色数を落として色面パスに起こしたSVGは、隣り合う色面が
ぴったり接しておらず、**髪の毛ほどの隙間**が空いていることがある。縮小表示では
サブピクセルに埋もれて見えないが、コマに大きく敷くと白い罅として全面に出る。

納品SVGが `fill` と同じ色の `stroke` を持ちつつ `stroke-width="0"` になっている
場合、線幅を少し与えるだけで各色面が自分の色で膨らみ、隙間が閉じる。

  python3 tools/fix_hairline_gaps.py <in.svg|dir> <out.svg|dir> [--width 2]

線幅は2が目安。3以上にすると細部が潰れて絵が眠くなる（実測）。
fillとstrokeの色が違うパスは触らない（輪郭線として意図されている可能性があるため）。
"""
import sys, os, re, glob

# fill と stroke が同じ色で、stroke-width が 0 のパスだけを対象にする
PAT = re.compile(
    r'fill="(?P<f>[^"]+)"(?P<mid>\s+)stroke="(?P<s>[^"]+)"(?P<mid2>\s+)stroke-width="0"')


def fix_text(src, width):
    n = 0

    def rep(m):
        nonlocal n
        f, s_ = m.group("f").strip().lower(), m.group("s").strip().lower()
        if f != s_:
            return m.group(0)
        n += 1
        return (f'fill="{m.group("f")}"{m.group("mid")}stroke="{m.group("s")}"'
                f'{m.group("mid2")}stroke-width="{width}"')

    return PAT.sub(rep, src), n


def fix_file(src_p, out_p, width):
    s = open(src_p).read()
    out, n = fix_text(s, width)
    # 書き出す前に必ずXMLとして読めるか確かめる（置換ミスでSVGを壊した実績あり）
    import xml.etree.ElementTree as ET
    ET.fromstring(out)
    open(out_p, "w").write(out)
    return n


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    a, b = sys.argv[1], sys.argv[2]
    w = float(sys.argv[sys.argv.index("--width") + 1]) if "--width" in sys.argv else 2
    w = int(w) if w == int(w) else w
    if os.path.isdir(a):
        os.makedirs(b, exist_ok=True)
        tot = files = 0
        for f in sorted(glob.glob(os.path.join(a, "*.svg"))):
            n = fix_file(f, os.path.join(b, os.path.basename(f)), w)
            tot += n
            files += 1
        print(f"{files}ファイル / のべ{tot}パスの線幅を0→{w}にした")
    else:
        n = fix_file(a, b, w)
        print(f"{os.path.basename(a)}: {n}パスの線幅を0→{w}にした")
