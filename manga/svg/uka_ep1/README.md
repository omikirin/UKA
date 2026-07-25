# 九尾の焔は記憶を喰う 第一話「初午の夜」— SVG漫画版

ネーム全集（CryptoNinja 42冊コマ割りビューア）の宇迦編・第一話を、
`characters/015_uka/` のSVG素材で実際のページに起こしたものです。全9ページ。

| | |
|---|---|
| `name/p01.json` 〜 `p09.json` | ページごとのネームJSON（辞書IDのみで記述） |
| `page/p01.png` 〜 `p09.png` | レンダ結果 |
| `contact.png` | 右綴じ（P1が右上）のコンタクトシート |

## ネームJSONの書き方

自由記述はせず、辞書のIDを選ぶだけで書きます（だから必ずレンダできる）。

- `layout_id` … コマ割り38種から選ぶ。**panels配列の1番目がページ右上**
- `pose_id` … 基本ポーズ90 × 5アングル（`P029_front` など）
- `chars` … 1コマに複数人。`x`(0-1の横位置)/`scale`/`flip`、後ろの要素ほど手前
- `background_id` … 実景85 + 効果背景15（`BG086`=集中線 など）
- `serif` … 1コマ2個まで。`{"t":"…","shape":"叫び"}` で形状指定（標準/叫び/トゲ/震え/ひそひそ/角丸）
- `sfx` … 描き文字。素材が無い語はフォントをパス化して描く

ナレーション枠は無いので、モノローグは `角丸` のフキダシで表現しています。

## レンダのしかた

`svg_manga_kit.zip` を展開した作業ディレクトリで、素材をこう繋いでから実行します。

```bash
ln -s <repo>/characters/015_uka/poses vectors_svg
ln -s <repo>/characters/015_uka/expr  vectors_expr
ln -s <kit>/vectors_bg vectors_bg     # 背景100（ディレクトリ名は vectors_bg）
ln -s <kit>/sfx_lib    sfx_lib        # 描き文字100
python3 render.py name/p01.json p01.svg
python3 -c "import cairosvg;cairosvg.svg2png(url='p01.svg',write_to='p01.png',output_width=760,background_color='white')"
```

縦書きセリフは Noto Serif CJK JP のグリフをパス化して埋め込むので、
レンダ環境に日本語フォントが要ります（`apt-get install fonts-noto-cjk`）。

## この版での割り切り

- **登場人物は全員ウカのセルで代用**しています。原作ネームの姉イズナ・於兎の素材が
  同じ絵柄で存在しないため、2人コマ（P071〜P082）は「ウカ2体」で撮っています。
  姉妹の場面としては読めますが、描き分けはされていません。
- 白玉・玄（狐二匹）は素材が無いので、該当コマは人物の芝居に置き換えました。
- 心象空間の背景（BG085/BG095）は実素材が寄りのコマで破綻したため、白地にしています。
- 原作P7・P8-9の見開き2枚は、単ページ2枚（P7=溜め、P8=決めの大ゴマ）に畳んでいます。
