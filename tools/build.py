#!/usr/bin/env python3
"""原稿(*.md)から読書ページ(*.html)を生成する。

使い方:
    python3 tools/build.py

作品を追加するとき:
    1. novels/ (長編) または stories/ (短編) に原稿mdを置く
       - 1行 = 1段落。「　　　＊」が場面区切り。末尾は（第X章　了）または（了）
    2. 下の CHAPTERS / STORIES に1行足す
    3. このスクリプトを実行して、index.html の一覧にカードを足す
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- 長編『空の狐と地上のウサギ』 ----

NOVEL_WORK = "空の狐と地上のウサギ"

# (章番号, タイトル, mdファイル名)。md が無い章は None。
CHAPTERS = [
    (1, "風の音のする国", "chapter01.md"),
    (2, "数式の花嫁", "chapter02.md"),
    (3, "仇の名", "chapter03.md"),
    (4, "式典の銃声", "chapter04.md"),
    (5, "墜ちた狐", "chapter05.md"),
    (6, "名前のない客", "chapter06.md"),
    (7, "二つの露見", "chapter07.md"),
    (8, "大徴収作戦", "chapter08.md"),
    (9, "第二射", "chapter09.md"),
    (10, "同じ高さの空", "chapter10.md"),
]

# ---- 連作短編集『宇迦忍法帖』 ----

STORY_WORK = "宇迦忍法帖"

# (mdファイル名, タイトル, ジャンル表示)
STORIES = [
    ("story01.md", "九尾の継承者", "王道バトル"),
    ("story02.md", "護符百枚", "試練"),
    ("story03.md", "イヅナとウカ", "姉妹"),
    ("story04.md", "月と狐火", "ライバル"),
    ("story05.md", "狐火の密室", "ミステリー"),
    ("story06.md", "油揚げ戦争", "日常コメディ"),
    ("story07.md", "狐の嫁入り", "和風幻想"),
    ("story08.md", "百年狐", "時とファンタジー"),
]

KANJI = "〇一二三四五六七八九十"


def kanji_no(n: int) -> str:
    return "十" if n == 10 else KANJI[n]


def md_to_paragraphs(text: str) -> str:
    """原稿mdの本文をHTML段落に変換する。"""
    out = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# 全十章"):
            out.append('<p class="fin">全十章　完</p>')
            continue
        if line.startswith("#"):
            continue  # タイトルはヘッダーで表示する
        if line == "---":
            continue
        if line.strip() == "＊":
            out.append('<p class="sep">＊</p>')
            continue
        m = re.match(r"^　*（((?:第.+章　)?了)）$", line)
        if m:
            out.append(f'<p class="chapter-end">（{html.escape(m.group(1))}）</p>')
            continue
        # 長編ch10末尾の目次は index にあるので本文からは省く
        if re.match(r"^　第[一二三四五六七八九十]+章　", line):
            continue
        if line.strip() == f"『{NOVEL_WORK}』":
            continue
        out.append(f"<p>{html.escape(line)}</p>")
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page_title} | クリプト忍者のウカ</title>
<meta name="description" content="{description}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<header class="site-header reader-header">
  <div class="header-inner">
    <p class="reader-work"><a href="../index.html">クリプト忍者のウカ</a>　『{work}』</p>
    <h1 class="reader-title">{heading}</h1>
  </div>
</header>

<article class="novel-body">
{body}
</article>

<nav class="chapter-nav">
  {prev_link}
  <a class="to-index" href="../index.html#{index_anchor}">目次へ</a>
  {next_link}
</nav>

<footer class="site-footer">
  <div class="footer-inner">
    <p>本サイトは NFTプロジェクト『CryptoNinja』のキャラクター「ウカ」の二次創作ファンサイトです。</p>
    <p>『{work}』 &copy; omikirin</p>
  </div>
</footer>
</body>
</html>
"""

EMPTY_LINK = '<a class="nav-empty" href="#">-</a>'


def render(dest_dir, fname, *, work, heading, page_title, description,
           index_anchor, prev_link, next_link):
    src = dest_dir / fname
    body = md_to_paragraphs(src.read_text(encoding="utf-8"))
    page = PAGE.format(
        work=work,
        heading=heading,
        page_title=page_title,
        description=description,
        body=body,
        index_anchor=index_anchor,
        prev_link=prev_link,
        next_link=next_link,
    )
    dest = dest_dir / fname.replace(".md", ".html")
    dest.write_text(page, encoding="utf-8")
    print(f"built {dest.relative_to(ROOT)}")


def build_novel() -> None:
    dest_dir = ROOT / "novels"
    available = [(n, t, f) for n, t, f in CHAPTERS if f]
    for i, (n, title, fname) in enumerate(available):
        label = f"第{kanji_no(n)}章"

        prev_link = EMPTY_LINK
        if i > 0:
            pn, pt, pf = available[i - 1]
            prev_link = (
                f'<a href="{pf.replace(".md", ".html")}">'
                f"&laquo;　第{kanji_no(pn)}章　{html.escape(pt)}</a>"
            )

        next_link = EMPTY_LINK
        if i < len(available) - 1:
            nn, nt, nf = available[i + 1]
            next_link = (
                f'<a href="{nf.replace(".md", ".html")}">'
                f"第{kanji_no(nn)}章　{html.escape(nt)}　&raquo;</a>"
            )

        render(
            dest_dir,
            fname,
            work=NOVEL_WORK,
            heading=f"{label}　{html.escape(title)}",
            page_title=f"{label}　{title} - {NOVEL_WORK}",
            description=(
                f"クリプト忍者のウカを主人公にした長編小説"
                f"『{NOVEL_WORK}』{label}「{title}」"
            ),
            index_anchor="novels",
            prev_link=prev_link,
            next_link=next_link,
        )


def build_stories() -> None:
    dest_dir = ROOT / "stories"
    for i, (fname, title, genre) in enumerate(STORIES):
        prev_link = EMPTY_LINK
        if i > 0:
            pf, pt, _ = STORIES[i - 1]
            prev_link = (
                f'<a href="{pf.replace(".md", ".html")}">'
                f"&laquo;　{html.escape(pt)}</a>"
            )

        next_link = EMPTY_LINK
        if i < len(STORIES) - 1:
            nf, nt, _ = STORIES[i + 1]
            next_link = (
                f'<a href="{nf.replace(".md", ".html")}">'
                f"{html.escape(nt)}　&raquo;</a>"
            )

        render(
            dest_dir,
            fname,
            work=STORY_WORK,
            heading=html.escape(title),
            page_title=f"{title} - {STORY_WORK}",
            description=(
                f"クリプト忍者のウカ(宇迦)の連作短編集『{STORY_WORK}』より"
                f"「{title}」({genre})"
            ),
            index_anchor="stories",
            prev_link=prev_link,
            next_link=next_link,
        )


if __name__ == "__main__":
    build_novel()
    build_stories()
