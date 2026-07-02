# クリプト忍者のウカ — ファンサイト

NFTプロジェクト『CryptoNinja』のキャラクター「ウカ」の二次創作ファンサイトです。
長編小説『空の狐と地上のウサギ』（全十章）を掲載しています。

## 構成

```
index.html          トップページ（作品紹介・章一覧・登場人物）
assets/style.css    共通スタイル
novels/chapterNN.md 小説の原稿（Markdown）
novels/chapterNN.html 読書ページ（build.py が生成）
tools/build.py      原稿から読書ページを生成するスクリプト
```

## 章の追加・更新のしかた

1. `novels/chapterNN.md` に原稿を置く（1行 = 1段落。`　　　＊` が場面区切り）
2. `tools/build.py` の `CHAPTERS` に章を登録する
3. `python3 tools/build.py` を実行する
4. `index.html` の章一覧カードを更新する

## 公開

静的サイトなので、GitHub Pages（Settings → Pages → Deploy from a branch）でそのまま公開できます。
