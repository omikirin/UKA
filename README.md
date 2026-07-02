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
```

## 作品の追加・更新のしかた

1. `novels/`（長編）または `stories/`（短編）に原稿mdを置く
   （1行 = 1段落。`　　　＊` が場面区切り。末尾は `（第X章　了）` または `（了）`）
2. `tools/build.py` の `CHAPTERS` / `STORIES` に登録する
3. `python3 tools/build.py` を実行する
4. `index.html` の一覧カードを更新する

短編の新作は `docs/企画資料_王道プロット50.md` のプロット集から選んで書くのがおすすめです。

## 公開

静的サイトなので、GitHub Pages（Settings → Pages → Deploy from a branch）でそのまま公開できます。
