# クリプト忍者のウカ — ファンサイト

NFTプロジェクト『CryptoNinja』のキャラクター「ウカ」の二次創作ファンサイトです。

- 長編小説『空の狐と地上のウサギ』（全十章・完結）
- 連作短編集『宇迦忍法帖』（甲賀の狐使い・宇迦の短編。長編とは別世界線）

## 構成

```
index.html            トップページ（作品紹介・作品一覧・登場人物）
assets/style.css      共通スタイル
novels/chapterNN.md   長編の原稿（Markdown）
novels/chapterNN.html 読書ページ（build.py が生成）
stories/storyNN.md    短編の原稿（Markdown）
stories/storyNN.html  読書ページ（build.py が生成）
tools/build.py        原稿から読書ページを生成するスクリプト
docs/                 企画資料（王道プロット50 など）
games/                CryptoNinja ゲーム集（自己完結型のHTMLゲーム）
manga/                マンガ版リーダー（右綴じ・見開き/単ページ切替）
characters/           SVG漫画メーカー用のキャラ素材（ウカのポーズ450・表情45）
tools/sheet_extract.py 発注シートPNGからセルSVGを切り出すスクリプト
```

マンガの見開き画像は `manga/img/chNN/spread01.jpg` 〜 の連番で配置します
（1枚 = 右ページ+左ページの横長見開き。単ページ表示では右半分→左半分の順に表示）。
リーダーは複数章対応です。新しい章を公開するときは、画像を配置してから
`manga/index.html` の `CHAPTERS` に `available: true` と枚数(count)を設定します。
章とびら・巻末の「つづく」カード・章セレクタ・しおり(読みかけ位置の保存)付き。
各章の表紙は `manga/img/chNN/cover.jpg` に置くと章とびらに表示されます
（無い章は自動で文字のとびらカードになります。縦長・横長どちらでも可）。

ゲームを追加するときは `games/` にHTMLを置き、`games/index.html` にカードを1枚足すだけです。

## 作品の追加・更新のしかた

1. `novels/`（長編）または `stories/`（短編）に原稿mdを置く
   （1行 = 1段落。`　　　＊` が場面区切り。末尾は `（第X章　了）` または `（了）`）
2. `tools/build.py` の `CHAPTERS` / `STORIES` に登録する
3. `python3 tools/build.py` を実行する
4. `index.html` の一覧カードを更新する

短編の新作は `docs/企画資料_王道プロット50.md` のプロット集から選んで書くのがおすすめです。

## 読書機能

読書ページ(novels/・stories/のHTML)には以下が付きます(`assets/reader.js` + CSS)。
設定はブラウザの localStorage に保存され、全ページ共通で効きます。

- 文字サイズ変更(小・中・大)
- 縦書き / 横書きの切り替え
- 夜間モード(ダークテーマ)
- 読書進捗バー(ページ上端)
- しおり: 読みかけの位置を自動保存し、再訪時に「前回の続きから読む」チップを表示
- トップページに「続きから読む」ボタン(最後に開いた章へ)
- 各章の文字数・読了目安の表示、折りたたみ目次、章送りボタン

## 公開

静的サイトなので、GitHub Pages（Settings → Pages → Deploy from a branch）でそのまま公開できます。
