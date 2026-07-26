# ウカ 彩色ポーズセル（FILL SVG）

彩色の納品は `<image href="data:image/png;base64,...">` を1枚貼っただけのSVGで、
拡張子はSVGでも**中身はラスタ**でした。`tools/raster_to_fill_svg.py` で本物の
色面SVGに起こしたものがここに入っています。

| ID | 元データ |
|---|---|
| `P001_front` / `side` / `back` | `characters/P001_*_FILL*.svg` |
| `P002_front` / `side` / `back` / `low` / `high` | `characters/P002_PNG_EMBEDDED_SVG_5views 2.zip` |

```bash
python3 tools/raster_to_fill_svg.py <in.svg|dir> <out.svg|dir> --colors 20
```

出力は `<g id="FILL">` と `<g id="LINE">` の2層で、手描きの納品SVGと同じ構造です。

## 作るときに引っかかったこと

- **線を残したまま減色すると輪郭が茶色くにじむ**。細い黒線が中間色に潰れるため。
  色面側からは線を消し（まわりの塗りで埋め）、線は別に二値でトレースして
  最前面に重ねる方式にしてあります
- **「暗い画素＝線」で判定すると赤い袴まで真っ黒になります**。暗さだけでなく
  彩度も見て「暗くて色みが無い画素」を線としています
- 元のPNGを拡大してからトレースすると、パスが増えるだけで見た目は良くなりません
  （実測: ×2で7MB。等倍なら0.4〜1.4MB）
- 色数は20が目安。12まで落とすと瞳と肌の陰が潰れます

## 残り

P001 の `low` / `high` が未着です（`P001_FILL_complete_set.zip` は壊れていて
展開できません）。上げ直してもらえれば同じコマンドで揃います。
