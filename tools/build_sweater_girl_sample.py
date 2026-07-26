#!/usr/bin/env python3
"""セーターガールの見本漫画「セーターの季節」のネームJSONを生成する

素材は `characters/sweater_girl/poses/` の555セル（C001-C555）。

**絵の中にすでに背景が描かれているカットには背景を付けない。**
机・階段・書架・大学の門などが入っているカット（poses.json で has_bg が true の
グループ）に辞書の背景を重ねると、線が二重になって「背景が透けている」ように見える。

前半（C001-C300）に**バストアップの表情カットが約90枚**あるので、寄りのコマは
そちらで作る。後半（C301-C555）には男性キャラと二人のカットが約100枚ある。

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
    # p01 秋。セーターを出す
    {"layout_id": "3段4コマ1", "panels": [
        P("C001", "BG016", [N("去年のセーターを出した。")]),
        P("C156", None, [C("……あれ")]),
        P("C161", None, [C("縮んだ？")], sfx=[("キョトン", 1)]),
        P("C151", None, [SH("わたしが育った！？")], sfx=[("ガーン", 3)]),
    ]},
    # p02 とりあえず着て出かける
    {"layout_id": "2段3コマ1", "panels": [
        P("C226", "BG019", [C("まあ、着られるし")], x=0.5),
        P("C441", None, sfx=[("タタタ", 1)]),
        P("C061", "BG028", [N("秋の匂いがした。")], bg_y=0.45),
    ]},
    # p03 大学で先輩に会う
    {"layout_id": "3段4コマ2", "panels": [
        P("C466", None, [N("大学。")]),
        P("C386", None, [C("おはようございます")]),
        P("C421", None, [C("……そのセーター")], sfx=[("ジーッ", 1)]),
        P("C166", None, [SH("見るなー！")], sfx=[("カァァ", 3)]),
    ]},
    # p04 図書館
    {"layout_id": "3段4コマ3", "panels": [
        P("C486", None, [C("去年も着てたよね")]),
        P("C171", None, [C("……覚えてるんですか")]),
        P("C481", None, [C("毎年見てるから")]),
        P("C176", None, [C("……そう")], sfx=[("ドキッ", 2)]),
    ]},
    # p05 学食
    {"layout_id": "2段3コマ2", "panels": [
        P("C491", None, [C("似合うよ、それ")], x=0.5),
        P("C161", None, None, sfx=[("ポッ", 2)]),
        P("C136", None, [C("……知ってます")]),
    ]},
    # p06 帰り道
    {"layout_id": "3段4コマ4", "panels": [
        P("C356", "BG059", [N("帰り道。雨だった。")], bg_y=0.45),
        P("C236", None, [C("傘、持ってきてよかった")]),
        P("C416", None, [C("入りますか")], sfx=[("スッ", 1)]),
        P("C401", None, [C("……入る")], sfx=[("ドキドキ", 2)]),
    ]},
    # p07 引きで締める
    {"layout_id": "2段2コマ1", "panels": [
        P("C361", "BG057", [C("来年も着ますよ、これ")]),
        P("C480", None, [N("セーターは、縮んでなかった。"), N("たぶん。")], bg_y=0.55),
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
