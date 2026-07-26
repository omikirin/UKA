#!/usr/bin/env python3
"""フルカラー版の見本漫画「まちぼうけ」のネームJSONを生成する

使える彩色素材は
  ・表情セル EXP001-015（`characters/015_uka/expr_color_line/`）
  ・全身ポーズ P001 の front / side / back
だけなので、**表情の3連ビートで話を運ぶ構成**にしてある。
EXP005 / EXP006 は彩色が線画と別の形なので使っていない。

15セルの中身（`expressions.json` の BEAT01-05 × 3ステップ）:
  001-003 泣き   004-006 驚き   007-009 照れ   010-012 怒り   013-015 じわ笑い

  python3 tools/build_color_sample.py <出力dir>
"""
import json, os, sys


def P(pose=None, expr=None, bg=None, s=None, sfx=None, x=0.5, scale=None, bg_y=None):
    d = {}
    if expr:
        d["expr_id"] = expr
    elif pose:
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
def C(t):  return {"t": t, "shape": "標準"}

PAGES = [
    # p01 待つ → 来ない
    {"layout_id": "3段4コマ1", "panels": [
        P(pose="P001_front", bg="BG043", s=[N("待ち合わせは、五時。")]),
        P(expr="EXP013", s=[C("……")]),
        P(expr="EXP004", s=[C("あれ")], sfx=[("キョトン", 1)]),
        P(pose="P001_side", bg="BG066", s=[C("もう六時なんだけど")], sfx=[("シーン", 2)]),
    ]},
    # p02 怒りの3連
    {"layout_id": "3段4コマ2", "panels": [
        P(expr="EXP010", bg="BG043", s=[C("うん、待つよ")]),
        P(expr="EXP011", s=[C("待つけどさ")], sfx=[("ピキッ", 2)]),
        P(expr="EXP012", s=[SH("おそいっ！！")], sfx=[("ガーン", 3)]),
        P(pose="P001_back", bg="BG060", s=[N("誰もいない参道に、声だけが残った。")], bg_y=0.35),
    ]},
    # p03 泣きの3連
    {"layout_id": "3段4コマ3", "panels": [
        P(expr="EXP001", bg="BG043", s=[C("べつに")]),
        P(expr="EXP002", s=[C("怒ってない")], sfx=[("プルプル", 1)]),
        P(expr="EXP003", s=[SH("怒ってないもん")], sfx=[("ザァァ", 2)]),
        P(pose="P001_front", bg="BG059", s=[N("雨まで降ってきた。")], bg_y=0.45),
    ]},
    # p04 来た → 照れ → じわ笑い
    {"layout_id": "3段4コマ4", "panels": [
        P(expr="EXP007", bg="BG043", s=[C("……来た")], sfx=[("ハッ", 2)]),
        P(expr="EXP008", s=[C("おそい")]),
        P(expr="EXP014", s=[C("って、言おうと思ってたのに")]),
        P(expr="EXP015", bg="BG057", s=[SH("もう、いいや！")], sfx=[("パァァ", 2)]),
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
