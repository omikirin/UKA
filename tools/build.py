#!/usr/bin/env python3
"""novels/*.md から読書ページ (novels/*.html) を生成する。

使い方:
    python3 tools/build.py

新しい章を追加するとき:
    1. novels/chapterNN.md を置く
    2. 下の CHAPTERS に1行足す
    3. このスクリプトを実行して、index.html の一覧にカードを足す
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOVELS = ROOT / "novels"

WORK_TITLE = "空の狐と地上のウサギ"

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
    (9, "第二射", None),
    (10, "同じ高さの空", "chapter10.md"),
]

KANJI = "〇一二三四五六七八九十"


def kanji_no(n: int) -> str:
    return "十" if n == 10 else KANJI[n]


def md_to_paragraphs(text: str) -> str:
    """小説mdの本文をHTML段落に変換する。"""
    out = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# 全十章"):
            out.append('<p class="fin">全十章　完</p>')
            continue
        if line.startswith("#"):
            continue  # 章タイトルはヘッダーで表示する
        if line == "---":
            continue
        if line.strip() == "＊":
            out.append('<p class="sep">＊</p>')
            continue
        m = re.match(r"^　*（(第.+章　了)）$", line)
        if m:
            out.append(f'<p class="chapter-end">（{html.escape(m.group(1))}）</p>')
            continue
        # ch10末尾の目次は index にあるので本文からは省く
        if re.match(r"^　第[一二三四五六七八九十]+章　", line):
            continue
        if line.strip() == f"『{WORK_TITLE}』":
            continue
        out.append(f"<p>{html.escape(line)}</p>")
    return "\n".join(out)


PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{chapter_label}　{title} - {work} | クリプト忍者のウカ</title>
<meta name="description" content="クリプト忍者のウカを主人公にした長編小説『{work}』{chapter_label}「{title}」">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<header class="site-header reader-header">
  <div class="header-inner">
    <p class="reader-work"><a href="../index.html">クリプト忍者のウカ</a>　『{work}』</p>
    <h1 class="reader-title">{chapter_label}　{title}</h1>
  </div>
</header>

<article class="novel-body">
{body}
</article>

<nav class="chapter-nav">
  {prev_link}
  <a class="to-index" href="../index.html#novels">目次へ</a>
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


def build() -> None:
    available = [(n, t, f) for n, t, f in CHAPTERS if f]
    for i, (n, title, fname) in enumerate(available):
        src = NOVELS / fname
        body = md_to_paragraphs(src.read_text(encoding="utf-8"))
        label = f"第{kanji_no(n)}章"

        if i > 0:
            pn, pt, pf = available[i - 1]
            prev_link = (
                f'<a href="{pf.replace(".md", ".html")}">'
                f"&laquo;　第{kanji_no(pn)}章　{html.escape(pt)}</a>"
            )
        else:
            prev_link = '<a class="nav-empty" href="#">-</a>'

        if i < len(available) - 1:
            nn, nt, nf = available[i + 1]
            next_link = (
                f'<a href="{nf.replace(".md", ".html")}">'
                f"第{kanji_no(nn)}章　{html.escape(nt)}　&raquo;</a>"
            )
        else:
            next_link = '<a class="nav-empty" href="#">-</a>'

        page = PAGE.format(
            work=WORK_TITLE,
            title=html.escape(title),
            chapter_label=label,
            body=body,
            prev_link=prev_link,
            next_link=next_link,
        )
        dest = NOVELS / fname.replace(".md", ".html")
        dest.write_text(page, encoding="utf-8")
        print(f"built {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    build()
