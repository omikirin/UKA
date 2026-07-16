#!/usr/bin/env python3
"""原稿(*.md)から読書ページ(*.html)を生成する。

使い方:
    python3 tools/build.py

作品を追加するとき:
    1. novels/ (長編) または stories/ (短編) に原稿mdを置く
       - 1行 = 1段落。「　　　＊」が場面区切り。末尾は（第X章　了）または（了）
    2. 下の CHAPTERS / STORY_GROUPS に1行足す
    3. このスクリプトを実行する
       - 長編・短編の読書ページを生成し、index.html の短編カード一覧も
         マーカー(<!-- stories-cards:begin/end -->)の間に自動で書き込む
"""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- 長編 ----

NOVEL_WORK = "空の狐と地上のウサギ"

# 各長編: work=作品名, prefix=mdファイル名の接頭辞, chapters=[(章番号, タイトル)]
# mdファイル名は f"{prefix}chapter{n:02d}.md"
NOVELS = [
    {
        "work": NOVEL_WORK,
        "prefix": "",
        "chapters": [
            (1, "風の音のする国"),
            (2, "数式の花嫁"),
            (3, "仇の名"),
            (4, "式典の銃声"),
            (5, "墜ちた狐"),
            (6, "名前のない客"),
            (7, "二つの露見"),
            (8, "大徴収作戦"),
            (9, "第二射"),
            (10, "同じ高さの空"),
        ],
    },
    # ここに新しい長編を追加する(エージェント執筆分は後段で登録)
]

# ---- 連作短編集『宇迦忍法帖』(全50篇・プロット番号=ファイル番号) ----

STORY_WORK = "宇迦忍法帖"

# (ジャンル名, [(番号, タイトル, ティーザー), ...])
STORY_GROUPS = [
    ("王道バトル・成長譚", [
        (1, "九尾の継承者", "尾が一本しか灯らない落ちこぼれが宣言する。「九本、灯す」。尾は絆の数だけ増える。"),
        (2, "護符百枚", "護符百枚で秘宝を奪還せよ。一枚ごとに減る残数。最後の一枚を、何に使う?"),
        (3, "兎と狐", "精鋭の座を懸けた長期試験。助け合っては減点される二人に、仕組まれた罠。"),
        (4, "焔の学び舎", "実技最下位、筆記首位。「頭でっかち」と嘲笑された知が、実戦の壁を破る。"),
        (5, "九本目の尾", "八本まで灯せる天才に、最後の一本だけが灯らない。その理由は、心の奥に。"),
        (6, "初午の約束", "初午の日にだけ現れる伝説の大狐に弟子入り。課題は、なぜか雑用ばかり。"),
        (7, "敗北の味", "無敗の宇迦が新人に完敗。相手は、幼き日の自分に憧れた少女だった。"),
        (8, "焔と水", "火を消す水遁の一族が宣戦布告。濡れても消えない狐火は、あるのか。"),
        (9, "使い魔失格", "「弱い主はいらない」。パートナーの狐が家出した。その嘘の、本当の理由。"),
        (10, "火継ぎ", "九尾の焔の継承は、先代の命を燃やす。命を消費しない新術式を求めて。"),
    ]),
    ("姉妹・家族", [
        (11, "イヅナとウカ", "月のない夜、敵味方として再会した姉妹。十年ぶりの再会が、これか!"),
        (12, "姉の背中", "消息を絶った姉は、記憶を封じて敵に潜入していた。呼び覚ますのは、妹だけが知る思い出。"),
        (13, "社の火を絶やすな", "実家の社が取り壊しの危機。守りたいのは力の源か、家族の記憶か。"),
        (14, "母の護符", "形見の護符が突然発火し、母の残した暗号が浮かび上がる。"),
        (15, "妹ができた日", "宇迦を「師匠」と呼ぶ戦災孤児の少女。その正体は、敵の間者だった。"),
        (16, "二つのクランの子", "伊賀と甲賀の合同任務で姉妹がバディに。噛み合わないまま、勝つ。"),
        (17, "祖母の九尾", "伝説の九尾使いだった祖母が呆けはじめ、狐火が記憶ごと漏れ出していく。"),
        (18, "名前の重さ", "「宇迦」は稲荷神の名。名前負けと囁かれる娘の前に、偽者が現れる。"),
    ]),
    ("ライバル・於兎", [
        (19, "月と狐火", "於兎が里を出た。追討を命じられた宇迦は、逃走経路に二人だけの暗号を見つける。"),
        (20, "百番勝負", "通算九十九勝九十九敗。決着の百戦目、その日に限って里が襲撃される。"),
        (21, "兎の恩返し", "身を挺して宇迦を救った於兎。その傷は、治らない呪いだった。"),
        (22, "入れ替わり", "敵の術で身体が入れ替わった二人。戻る条件は「相手の弱さを守り抜くこと」。"),
        (23, "二人の師匠", "新人二人の教育係を押し付け合う宇迦と於兎。方針は真逆、新人は大混乱。"),
        (24, "最後の勝負", "老いて引退した二人の、縁側の盤上での最終戦。生涯のライバル物語の大団円。"),
    ]),
    ("ミステリー・サスペンス", [
        (25, "狐火の密室", "閂の掛かった書庫、長老の変死、現場には宇迦の狐火の痕跡。無実の証明は「右回り」。"),
        (26, "消えた誕生日", "里の記録から二月十一日だけが消えている。宇迦の誕生日も、「存在しない」。"),
        (27, "九人目の忍", "八人任務のはずが、帰還者は九人。閉ざされた砦の疑心暗鬼。"),
        (28, "祟り神の正体", "狐の祟りと噂される連続失踪。祟りより怖いのは人、でも救えるのも人。"),
        (29, "護符の遺言", "暗殺された護符職人の最後の一枚。遺言の宛先は、犯人本人だった。"),
        (30, "二重スパイの狐", "風魔への潜入任務。両組織の間者同士が結ぶ、第三の道。"),
    ]),
    ("ラブコメ・日常", [
        (31, "恋する護符", "恋文の護符が誤発動。狐火が想い人の周りを飛び回る大惨事。"),
        (32, "油揚げ戦争", "名店最後の一枚を巡り、狐と兎が全面戦争。里を二分する大騒動の、あたたかい着地。"),
        (33, "九尾の家政婦", "任務失敗の罰は、一般家庭への住み込み奉公。忍術を家事に誤用する日々。"),
        (34, "狐の嫁入り", "晴れているのに、雨。婚礼の行列に迷い込んだ青年は、白無垢に亡き妻の面影を見る。"),
        (35, "バレンタイン大作戦", "誕生日とバレンタインが毎年まとめて祝われる宇迦の、空回りの二月。"),
        (36, "社カフェ、はじめました", "社の維持費のため境内でカフェ開業。人気が出すぎて、氏神が家出。"),
    ]),
    ("ダークファンタジー・シリアス", [
        (37, "焔の代償", "九尾の焔は、使うほど人でなくなる。最弱になった最強が、護符一枚で立つ。"),
        (38, "鬼喰いの里", "鬼は、かつて人だった。討伐ではなく、看取るための焔。"),
        (39, "偽りの英雄", "戦争を終わらせた英雄と讃えられる宇迦。本当の功労者は、死んだ姉だった。"),
        (40, "百年狐", "術の暴走で百年後へ。滅びた世界で待っていたのは、神になった相棒だった。"),
        (41, "声を失くした術者", "呪詛で詠唱を奪われた。呪いの主は、自分自身の言霊だった。"),
        (42, "焔の裁判", "任務の犠牲を巡り、宇迦が忍法廷に立つ。正義と贖罪の法廷劇。"),
    ]),
    ("競技・お仕事", [
        (43, "忍者甲子園", "クラン対抗の若手忍術大会。決勝の相手は、姉率いる伊賀チーム。"),
        (44, "護符職人への道", "戦いから離れ、護符職人に弟子入り。使う側から、作る側へ。"),
        (45, "狐火リレー", "里同士を結ぶ伝統の狐火駅伝。本番のコース上で、土砂崩れが起きる。"),
        (46, "忍務保育園", "忍者の卵を預かる保育所に配属。バトルより過酷な毎日と、攫われた園児。"),
        (47, "引退試合", "第一線を退く先輩の最後の任務に同行。経験という「見えない術」を学ぶ。"),
    ]),
    ("大河・起源譚", [
        (48, "九尾大戦記", "千年に一度、九尾の焔が完全覚醒する年が来る。全クランを巻き込む大戦へ。"),
        (49, "稲荷千年記", "教わる側から、教える側へ。三代にわたる継承の物語。"),
        (50, "最初の狐", "千年前、人と狐が敵だった時代。最初の護符が生まれた日。"),
    ]),
    ("番外・魔法少女", [
        (51, "狐火の魔法少女", "中学生の宇迦、喋る小狐と契約して魔法少女に。優等生の於兎に正体がばれかける。"),
        (52, "変身が解けない", "魔法の暴走で狐耳と尻尾が戻らない。帽子で隠して登校する朝が始まる。"),
        (53, "最後のステッキ", "魔法の源が尽きる日。最後の変身を灯すのは、町中の「ありがとう」。"),
        (54, "敵の魔法少女", "影を操る黒い魔法少女。彼女が守っていたのは、影の世界の妹だった。"),
        (55, "マネージャーは狐", "「魔法少女はプロデュースの時代!」相棒のプロデュース計画に、まさかの本物襲来。"),
    ]),
    ("番外・空想科学", [
        (56, "星狐", "宇宙航路の操縦士・宇迦。拾った脱出艇には、敵国の撃墜王・於兎が乗っていた。"),
        (57, "機械の尾", "事故で失った尾の代わりは、正確無比な機械の尾。でも、風が読めない。"),
        (58, "百年航路", "移民船で一人だけ途中覚醒。針路を正すには、目的地に着く未来を捨てるしかない。"),
        (59, "複製の私", "任務用に作られた複製体が願う。「消される前に、一日だけ自由に生きたい」。"),
        (60, "星に願いを撃つ", "彗星迎撃の巨砲は九発きり。最後の一発の照準は、風を読む勘に託された。"),
    ]),
    ("番外・異世界", [
        (61, "異世界の油揚げ", "召喚されたのは勇者ではなく「食の伝道師」。魔王が本当に求めていたもの。"),
        (62, "竜の輪守", "嵐の夜、地に落ちた仔竜を拾った。返さなければ、人と竜の戦争になる。"),
        (63, "勇者は兎", "魔王軍幹部に転生した宇迦。討伐に来た勇者は、見覚えのある白兎だった。"),
        (64, "神様のアルバイト", "稲荷神の代理を命じられた宇迦。賽銭は少なく、願いは重い。"),
        (65, "逆さの忍", "鏡の国に吸い込まれた。そこでは「宇迦」が、里を裏切った悪党だった。"),
    ]),
    ("番外・怪異譚", [
        (66, "夜市", "妖の夜市の通貨は「名前」。子の名を買い戻す代価は、宇迦自身の名。"),
        (67, "影踏み", "子どもらの影が一人ずつ薄くなる。唄の最後の一節は「九つ目は誰の影」。"),
        (68, "骨の笛", "廃村で拾った笛を吹くと、夜、行列がついてくる。"),
        (69, "鏡文字の文", "姉からの文が、ある日から鏡文字に。それは内側からの救難信号だった。"),
        (70, "百物語の九十九", "百物語は九十九話で止める掟。百話目を語った新人が、消えた。"),
    ]),
]

KANJI = "〇一二三四五六七八九"


def kanji_num(n: int) -> str:
    """1〜99 を漢数字にする。"""
    tens, ones = divmod(n, 10)
    s = ""
    if tens == 1:
        s += "十"
    elif tens > 1:
        s += KANJI[tens] + "十"
    if ones:
        s += KANJI[ones]
    return s or "〇"


def md_to_paragraphs(text: str, work: str = NOVEL_WORK) -> str:
    """原稿mdの本文をHTML段落に変換する。"""
    out = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^# (全[一二三四五六七八九十]+章)", line)
        if m:
            out.append(f'<p class="fin">{html.escape(m.group(1))}　完</p>')
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
        if line.strip() == f"『{work}』":
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
<script>(function () {{ try {{ var r = document.documentElement, g = function (k, d) {{ return localStorage.getItem(k) || d; }}; r.setAttribute("data-fontsize", g("uka-fontsize", "medium")); r.setAttribute("data-theme", g("uka-theme", "light")); r.setAttribute("data-writing", g("uka-writing", "yoko")); }} catch (e) {{}} }})();</script>
</head>
<body>
<div class="reading-progress"><span id="reading-progress-bar"></span></div>
<header class="site-header reader-header">
  <div class="header-inner">
    <p class="reader-work"><a href="../index.html">クリプト忍者のウカ</a>　『{work}』</p>
    <h1 class="reader-title">{heading}</h1>
    <p class="reader-meta">約{chars}字　読了目安 約{minutes}分</p>
  </div>
</header>

<article class="novel-body">
{body}
</article>

<details class="reader-toc">
  <summary>目次　『{work}』</summary>
  <ol>
{toc}
  </ol>
</details>

<nav class="chapter-nav">
  {prev_link}
  <a class="to-index" href="../index.html#{index_anchor}">一覧へ</a>
  {next_link}
</nav>

<div class="reader-tools" role="group" aria-label="読書設定">
  <button type="button" id="tool-fs-plus" title="文字を大きく">大</button>
  <button type="button" id="tool-fs-minus" title="文字を小さく">小</button>
  <button type="button" id="tool-writing" title="縦書き/横書きを切り替え">縦</button>
  <button type="button" id="tool-theme" title="夜間モードを切り替え">夜</button>
</div>

<footer class="site-footer">
  <div class="footer-inner">
    <p>本サイトは NFTプロジェクト『CryptoNinja』のキャラクター「ウカ」の二次創作ファンサイトです。</p>
    <p>『{work}』 &copy; omikirin</p>
  </div>
</footer>
<script src="../assets/reader.js" defer></script>
</body>
</html>
"""
EMPTY_LINK = '<a class="nav-empty" href="#">-</a>'


def render(dest_dir, fname, *, work, heading, page_title, description,
           index_anchor, prev_link, next_link, toc=""):
    src = dest_dir / fname
    raw = src.read_text(encoding="utf-8")
    body = md_to_paragraphs(raw, work)
    chars = len(re.sub(r"\s", "", re.sub(r"^#.*$", "", raw, flags=re.M)))
    minutes = max(1, round(chars / 600))
    page = PAGE.format(
        work=work,
        heading=heading,
        page_title=page_title,
        description=description,
        body=body,
        chars=f"{round(chars, -2):,}",
        minutes=minutes,
        toc=toc,
        index_anchor=index_anchor,
        prev_link=prev_link,
        next_link=next_link,
    )
    dest = dest_dir / fname.replace(".md", ".html")
    dest.write_text(page, encoding="utf-8")
    print(f"built {dest.relative_to(ROOT)}")


def make_toc(entries, current_href):
    """entries: [(href, label)]。current_href はリンクにしない。"""
    lines = []
    for href, label in entries:
        if href == current_href:
            lines.append(f'    <li class="current">{html.escape(label)}</li>')
        else:
            lines.append(f'    <li><a href="{href}">{html.escape(label)}</a></li>')
    return "\n".join(lines)


def build_novels() -> None:
    dest_dir = ROOT / "novels"
    for novel in NOVELS:
        work = novel["work"]
        prefix = novel["prefix"]
        available = [
            (n, t, f"{prefix}chapter{n:02d}.md")
            for n, t in novel["chapters"]
            if (dest_dir / f"{prefix}chapter{n:02d}.md").exists()
        ]
        missing = [
            n for n, _ in novel["chapters"]
            if not (dest_dir / f"{prefix}chapter{n:02d}.md").exists()
        ]
        if missing:
            print(f"skip (原稿なし) 『{work}』: {missing}")
        toc_entries = [
            (f.replace(".md", ".html"), f"第{kanji_num(n)}章　{t}")
            for n, t, f in available
        ]
        for i, (n, title, fname) in enumerate(available):
            label = f"第{kanji_num(n)}章"

            prev_link = EMPTY_LINK
            if i > 0:
                pn, pt, pf = available[i - 1]
                prev_link = (
                    f'<a href="{pf.replace(".md", ".html")}">'
                    f"&laquo;　第{kanji_num(pn)}章　{html.escape(pt)}</a>"
                )

            next_link = EMPTY_LINK
            if i < len(available) - 1:
                nn, nt, nf = available[i + 1]
                next_link = (
                    f'<a href="{nf.replace(".md", ".html")}">'
                    f"第{kanji_num(nn)}章　{html.escape(nt)}　&raquo;</a>"
                )

            render(
                dest_dir,
                fname,
                work=work,
                heading=f"{label}　{html.escape(title)}",
                page_title=f"{label}　{title} - {work}",
                description=(
                    f"クリプト忍者のウカを主人公にした長編小説"
                    f"『{work}』{label}「{title}」"
                ),
                index_anchor="novels",
                prev_link=prev_link,
                next_link=next_link,
                toc=make_toc(toc_entries, fname.replace(".md", ".html")),
            )


def story_fname(n: int) -> str:
    return f"story{n:02d}.md"


def build_stories() -> list[int]:
    """短編ページを生成し、原稿の存在した番号のリストを返す。"""
    dest_dir = ROOT / "stories"
    flat = [
        (n, title, genre)
        for genre, items in STORY_GROUPS
        for n, title, _ in items
    ]
    available = [
        (n, t, g) for n, t, g in flat if (dest_dir / story_fname(n)).exists()
    ]
    missing = [n for n, _, _ in flat if not (dest_dir / story_fname(n)).exists()]
    if missing:
        print(f"skip (原稿なし): {missing}")

    toc_entries = [
        (f"story{n:02d}.html", f"其の{kanji_num(n)}　{t}")
        for n, t, _ in available
    ]
    for i, (n, title, genre) in enumerate(available):
        prev_link = EMPTY_LINK
        if i > 0:
            pn, pt, _ = available[i - 1]
            prev_link = (
                f'<a href="story{pn:02d}.html">'
                f"&laquo;　其の{kanji_num(pn)}　{html.escape(pt)}</a>"
            )

        next_link = EMPTY_LINK
        if i < len(available) - 1:
            nn, nt, _ = available[i + 1]
            next_link = (
                f'<a href="story{nn:02d}.html">'
                f"其の{kanji_num(nn)}　{html.escape(nt)}　&raquo;</a>"
            )

        render(
            dest_dir,
            story_fname(n),
            work=STORY_WORK,
            heading=f"其の{kanji_num(n)}　{html.escape(title)}",
            page_title=f"其の{kanji_num(n)}　{title} - {STORY_WORK}",
            description=(
                f"クリプト忍者のウカ(宇迦)の連作短編集『{STORY_WORK}』より"
                f"「{title}」({genre})"
            ),
            index_anchor="stories",
            prev_link=prev_link,
            next_link=next_link,
            toc=make_toc(toc_entries, f"story{n:02d}.html"),
        )
    return [n for n, _, _ in available]


MARK_BEGIN = "<!-- stories-cards:begin -->"
MARK_END = "<!-- stories-cards:end -->"


def build_story_index(available: list[int]) -> None:
    """index.html のマーカー間に短編カード一覧を書き込む。"""
    index = ROOT / "index.html"
    text = index.read_text(encoding="utf-8")
    if MARK_BEGIN not in text or MARK_END not in text:
        print("index.html にマーカーが無いため、短編カードは更新しません")
        return

    blocks = []
    for genre, items in STORY_GROUPS:
        cards = []
        for n, title, teaser in items:
            if n not in available:
                cards.append(
                    '      <div class="chapter-card coming">\n'
                    f'        <p class="chapter-no">其の{kanji_num(n)}</p>\n'
                    f'        <p class="chapter-name">{html.escape(title)}</p>\n'
                    f'        <p class="chapter-teaser">{html.escape(teaser)}</p>\n'
                    '        <span class="badge-soon">近日公開</span>\n'
                    "      </div>"
                )
                continue
            cards.append(
                f'      <a class="chapter-card" href="stories/story{n:02d}.html">\n'
                f'        <p class="chapter-no">其の{kanji_num(n)}</p>\n'
                f'        <p class="chapter-name">{html.escape(title)}</p>\n'
                f'        <p class="chapter-teaser">{html.escape(teaser)}</p>\n'
                "      </a>"
            )
        blocks.append(
            f'    <h3 class="story-group">{html.escape(genre)}</h3>\n'
            '    <div class="chapter-grid">\n'
            + "\n".join(cards)
            + "\n    </div>"
        )

    new_block = MARK_BEGIN + "\n" + "\n".join(blocks) + "\n    " + MARK_END
    text = re.sub(
        re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
        lambda _: new_block,
        text,
        flags=re.S,
    )
    index.write_text(text, encoding="utf-8")
    print("updated index.html (短編カード一覧)")


if __name__ == "__main__":
    build_novels()
    built = build_stories()
    build_story_index(built)
