#!/usr/bin/env python3
"""読み切り「かげぶんしん」のネームJSONを生成する

素材はロング髪ウカの225セル（`characters/037_izuna/poses_line/` = P046-P090）だけを使う。
表情セル（EXP系）はショート髪のウカなので、髪型が変わってしまうため混ぜない。
寄りのコマは P087（上半身の寄り）、P083/P084（手のアップ）、P089（脚のアップ）で作る。

二人組ポーズが12種あるのを活かして「分身」の話にした。同じ姿が2人並ぶ絵が
最初から用意されているので、分身ものは この素材にいちばん噛み合う題材。

  python3 tools/build_kagebunshin.py <出力dir>
"""
import json, os, sys

A = ["front", "side", "back", "low", "high"]


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


def N(t):  return {"t": t, "shape": "角丸"}     # ナレーション
def SH(t): return {"t": t, "shape": "叫び"}
def TG(t): return {"t": t, "shape": "トゲ"}
def C(t):  return {"t": t, "shape": "標準"}

PAGES = [
    # p01 --- つかみ：印を結ぶ、そして2人になる
    {"layout_id": "3段4コマ1", "panels": [
        P("P065_front", "BG065", [N("修行、三十七日目。")], x=0.5),
        P("P065_low",  None, [C("今日こそ、できる")], x=0.55, sfx=[("ゴゴゴゴ", 2)]),
        P("P083_front", None, sfx=[("ギュッ", 2)]),
        P("P079_front", "BG088", [SH("かげぶんしんっ！")], sfx=[("ドン", 3)]),
    ]},
    # p02 --- 分身が出た。喜ぶ
    {"layout_id": "2段3コマ1", "panels": [
        P("P073_front", "BG065", [C("……出た")], x=0.5),
        P("P087_front", None, [C("出たー！！")], sfx=[("パァァ", 2)]),
        P("P066_front", None, [SH("やった！")], sfx=[("キラキラ", 1)]),
    ]},
    # p03 --- 分身のほうが有能だと気づく
    {"layout_id": "3段4コマ2", "panels": [
        P("P080_front", "BG065", [C("よろしくね、わたし")], x=0.5),
        P("P082_side", None, [C("うん、よろしく、わたし")]),
        P("P062_side", None, [C("（分身）じゃあ、素振り千本ね")], sfx=[("ヒュン", 2)]),
        P("P087_front", None, [C("……え")], sfx=[("キョトン", 1)]),
    ]},
    # p04 --- 見開き気味の1コマ：分身の圧倒的な技
    {"layout_id": "2段2コマ1", "panels": [
        P("P062_front", "BG086", [SH("はやっ！？")], sfx=[("ズバッ", 3), ("ヒュン", 2)]),
        P("P061_side", None, [C("（分身）まだ三百本")], sfx=[("キン", 2)]),
    ]},
    # p05 --- 落ち込む
    {"layout_id": "3段4コマ3", "panels": [
        P("P070_front", "BG065", [C("なんで")], sfx=[("ズーン", 2)]),
        P("P067_side", None, [C("わたしの分身なのに")]),
        P("P084_front", None, sfx=[("プルプル", 1)]),
        P("P069_front", None, [C("わたしより、つよい")], sfx=[("シーン", 2)]),
    ]},
    # p06 --- 分身が手を差し伸べる
    {"layout_id": "2段3コマ2", "panels": [
        P("P076_side", "BG065", [C("（分身）ねえ")], x=0.5),
        P("P084_front", None, [C("（分身）立って")], sfx=[("スッ", 1)]),
        P("P077_front", None, [C("（分身）わたしが強いなら"), C("あなたも強いんだよ")]),
    ]},
    # p07 --- 二人で並んで構える
    {"layout_id": "3段4コマ4", "panels": [
        P("P087_front", "BG058", [C("……そっか")], sfx=[("ハッ", 2)]),
        P("P078_front", None, [C("そうだね")]),
        P("P089_front", None, sfx=[("ダッ", 2)]),
        P("P072_front", "BG065", [C("じゃあ、二千本だ")], sfx=[("タタタ", 2)]),
    ]},
    # p08 --- 引きで締める
    {"layout_id": "2段2コマ2", "panels": [
        P("P075_front", "BG057", [C("（分身）消えるまで、つきあうよ")]),
        P("P088_back", "BG046", [N("修行、三十八日目。"), N("まだ、二人でいる。")], bg_y=0.55),
    ]},
]


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    for i, pg in enumerate(PAGES, 1):
        pg = dict(pg)
        pg.setdefault("title", "かげぶんしん" if i == 1 else None)
        json.dump(pg, open(os.path.join(outdir, f"p{i:02d}.json"), "w"),
                  ensure_ascii=False, indent=1)
    print(f"{len(PAGES)}ページ分のネームを書き出した → {outdir}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "name")
