#!/usr/bin/env python3
"""セーターガールの見本漫画「うちの先輩は強い」のネームJSONを生成する

素材は `characters/sweater_girl/poses/` の255セル（C301-C555）だけ。
表情セルが無いかわりに、**顔のアップ（C421-C435）と手のアップ（C411-C420）**が
用意されているので、寄りのコマはそちらで作る。
男性キャラと二人のカットが約100枚あるのが この素材の強みなので、
「二人の関係」を軸にした話にした。

  python3 tools/build_sweater_girl_sample.py <出力dir>
"""
import json, os, sys


def P(pose=None, bg=None, s=None, sfx=None, x=0.5, scale=None, bg_y=None):
    d = {}
    if pose:
        d["pose_id"] = pose
        d["pose_x"] = x
        if scale:
            d["pose_scale"] = scale
    if bg:
        d["background_id"] = bg
    if bg_y is not None:
        d["bg_y"] = bg_y
    if s:
        d["serif"] = s
    if sfx:
        d["sfx"] = [{"text": t, "intensity": i} for t, i in sfx]
    return d


def N(t):  return {"t": t, "shape": "角丸"}
def SH(t): return {"t": t, "shape": "叫び"}
def TG(t): return {"t": t, "shape": "トゲ"}
def C(t):  return {"t": t, "shape": "標準"}

PAGES = [
    # p01 大学の門で待ち合わせ → 道場へ
    {"layout_id": "3段4コマ1", "panels": [
        P("C466", "BG012", [N("先輩とは、大学で知り合った。")]),
        P("C421", None, [C("今日、ひま？")]),
        P("C470", None, [C("ひまだけど")]),
        P("C476", "BG014", [C("じゃあ、道場つきあって")], sfx=[("パァァ", 2)]),
    ]},
    # p02 道場。刀を構える
    {"layout_id": "2段3コマ1", "panels": [
        P("C301", "BG064", [N("道場。")], x=0.5),
        P("C411", None, sfx=[("ギュッ", 2)]),
        P("C305", None, [C("見ててね")], sfx=[("スッ", 1)]),
    ]},
    # p03 斬撃
    {"layout_id": "3段4コマ2", "panels": [
        P("C306", "BG086", None, sfx=[("ヒュン", 3)]),
        P("C307", None, None, sfx=[("ズバッ", 3)]),
        P("C426", None, [C("……")], sfx=[("シーン", 2)]),
        P("C310", "BG088", [SH("もう一本！")], sfx=[("ドン", 3)]),
    ]},
    # p04 負ける・倒れる
    {"layout_id": "3段4コマ3", "panels": [
        P("C331", "BG064", [C("あれ")]),
        P("C336", None, [SH("わっ")], sfx=[("ドカッ", 3)]),
        P("C341", None, [C("……いたい")], sfx=[("ズーン", 2)]),
        P("C429", None, [C("見てた？")]),
    ]},
    # p05 手を差し伸べる
    {"layout_id": "2段3コマ2", "panels": [
        P("C416", "BG064", None, sfx=[("スッ", 1)]),
        P("C456", None, [C("見てました")]),
        P("C396", None, [C("転ぶとこも？"), C("転ぶとこも")]),
    ]},
    # p06 帰り道
    {"layout_id": "3段4コマ4", "panels": [
        P("C441", "BG029", None, sfx=[("タタタ", 1)]),
        P("C356", "BG059", [N("帰り道。雨だった。")], bg_y=0.45),
        P("C474", None, [C("入る？")]),
        P("C430", None, [C("……入る")], sfx=[("ポッ", 2)]),
    ]},
    # p07 引きで締める
    {"layout_id": "2段2コマ1", "panels": [
        P("C361", "BG057", [C("次は勝つから")]),
        P("C480", "BG046", [N("うちの先輩は、強い。"), N("転ぶけど。")], bg_y=0.55),
    ]},
]


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    for i, pg in enumerate(PAGES, 1):
        json.dump(pg, open(os.path.join(outdir, f"p{i:02d}.json"), "w"),
                  ensure_ascii=False, indent=1)
    print(f"{len(PAGES)}ページ分のネームを書き出した → {outdir}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "name")
