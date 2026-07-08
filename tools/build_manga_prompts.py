# ネームJSON(docs/ネーム_第N章.json)から画像生成プロンプト(JSONL)を作る
# 使い方: python3 tools/build_manga_prompts.py
import json, os

RAW = "https://raw.githubusercontent.com/omikirin/UKA/claude/uka-crypto-ninja-site-0pi8j9/"

CHAR_DESC = {
    "uka":    "UKA, a young fox woman: wavy orange-blonde hair, orange fox ears on top of her head, amber eyes, simple worn clothes",
    "shinra": "SHINRA, a tall scruffy human mechanic: messy dark-brown hair, tired unshaven face, stained green coveralls",
    "oto":    "OTO, a petite rabbit woman: chin-length pink bob hair, amber eyes, white rabbit ears, black mourning dress",
    "kon":    "KON, a 10-year-old rabbit girl: black high ponytail with a purple ribbon, big round dark eyes, white rabbit ears with one folded tip, a small white fox mask worn on the side of her head, patched brown jacket",
    "izuna":  "IZUNA, a fox woman in her late 20s: long straight black hair with blue-tinted inner locks, violet-purple eyes, a small beauty mark under her left eye, black fox ears with gray inner fur, black-gray fox tail, white miko-style robe with a crimson red hakama",
    "garen":  "GAREN, a stern middle-aged officer: swept-back gray hair, gray rabbit ears, weathered angular face, dark navy double-breasted military uniform",
    "ganji":  "GANJI, a gaunt elderly rabbit man: long white bushy eyebrows, narrow dry measuring eyes, drooping white rabbit ears, worn work clothes with a leather tool vest, wooden cane",
    "sekishu":"SEKISHU, an elderly fox admiral: spiky dark-gray hair with a white forelock streak, sharp orange eyes, gray goatee, navy admiral dress uniform with gold braid",
    "sion":   "SION, a rabbit propaganda officer: slicked-back pale ash-blond hair, narrow half-closed smiling eyes, small round pince-nez glasses, olive-drab uniform",
}
# キャラ→参照画像(優先順)
CHAR_REF = {
    "izuna":  RAW + "manga/img/design/izuna.jpg",
    "ganji":  RAW + "manga/img/design/ganji.jpg",
    "kon":    RAW + "manga/img/design/kon.jpg",
    "sekishu":RAW + "manga/img/design/sekishu.jpg",
    "sion":   RAW + "manga/img/design/sion.jpg",
    "shinra": RAW + "manga/img/ch01/spread01.jpg",
    "uka":    RAW + "manga/img/ch05/spread03.jpg",
    "oto":    RAW + "manga/img/ch05/spread10.jpg",
    "garen":  RAW + "manga/img/ch02/spread02.jpg",
}
STYLE_REF = RAW + "manga/img/ch01/spread01.jpg"

SPEAKER2CHAR = {"ウカ":"uka","シンラ":"shinra","オト":"oto","コン":"kon","イヅナ":"izuna",
                "ガレン":"garen","ガンジ":"ganji","セキシュウ":"sekishu","シオン":"sion"}
POS = ["RIGHT PAGE TOP","RIGHT PAGE MIDDLE","RIGHT PAGE BOTTOM",
       "LEFT PAGE TOP","LEFT PAGE MIDDLE","LEFT PAGE BOTTOM"]
BTYPE = {"normal":"speech balloon","thought":"thought balloon (cloud-shaped)",
         "shout":"shouting balloon (spiky)","narration":"narration caption box",
         "radio":"radio-voice jagged balloon"}

def balloon_txt(d):
    who = d.get("speaker","")
    typ = BTYPE.get(d.get("type","normal"), "speech balloon")
    pos = d.get("balloon","top_left").replace("_","-")
    label = "narration" if d.get("type")=="narration" else (
        SPEAKER2CHAR.get(who, "").upper() or who)
    return f"{label} {typ} {pos}: 「{d['text']}」"

def build(chapter_no, json_path, out_path, start_spread):
    d = json.load(open(json_path))
    lines = []
    for s in d["spreads"]:
        if s["spread"] < start_spread:
            continue
        panels = sorted(s["panels"], key=lambda p: p["no"])
        chars = set()
        for p in panels:
            for c in p.get("chars", []): chars.add(c)
            for dl in p.get("dialogue", []):
                c = SPEAKER2CHAR.get(dl.get("speaker",""))
                if c: chars.add(c)
        desc = "; ".join(CHAR_DESC[c] for c in sorted(chars) if c in CHAR_DESC)
        refs, seen = [], set()
        for c in ["izuna","ganji","kon","sekishu","sion","shinra","uka","oto","garen"]:
            if c in chars and CHAR_REF[c] not in seen:
                refs.append(CHAR_REF[c]); seen.add(CHAR_REF[c])
            if len(refs) >= 3: break
        if not refs: refs = [STYLE_REF]
        if len(refs) == 1 and refs[0] != STYLE_REF: refs.append(STYLE_REF)

        parts = []
        parts.append("The attached reference images show the exact art style and character designs. Copy that crisp Japanese anime cel-shading style with muted colors.")
        if desc: parts.append("Characters (keep on-model in every panel): " + desc + ".")
        parts.append("IMPORTANT: all characters are HUMAN-shaped people with animal ears and tails (kemonomimi); NEVER draw them as real animals.")
        parts.append("Draw a NEW Japanese full-color manga two-page spread, 16:9 landscape, read right-to-left: RIGHT page = 3 vertically stacked panels (top, middle, bottom), LEFT page = 3 vertically stacked panels (top, middle, bottom), thin white gutters. All text in Japanese, copied EXACTLY character-for-character; draw ONLY the balloons, captions and sound effects listed below, nothing else.")
        for i, p in enumerate(panels[:6]):
            scene = p["prompt"]
            for k in CHAR_DESC:
                scene = scene.replace("{"+k+"}", k.upper())
            seg = f"{POS[i]} panel: {scene}"
            for dl in p.get("dialogue", []):
                seg += "; " + balloon_txt(dl)
            if p.get("sfx"):
                seg += f"; sound-effect lettering: {p['sfx']}"
            if not p.get("dialogue") and not p.get("sfx"):
                seg += "; no text in this panel"
            parts.append(seg + ".")
        prompt = " ".join(parts)
        lines.append({
            "path": f"manga/img/ch{chapter_no:02d}/spread{s['spread']:02d}.jpg",
            "prompt": prompt,
            "aspect_ratio": "16:9",
            "image_urls": refs,
        })
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        for l in lines:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    print(out_path, len(lines), "prompts")

if __name__ == "__main__":
    build(6,  "docs/ネーム_第六章.json",  "prompts/ch06.jsonl", 3)
    build(7,  "docs/ネーム_第七章.json",  "prompts/ch07.jsonl", 3)
    build(8,  "docs/ネーム_第八章.json",  "prompts/ch08.jsonl", 3)
    build(9,  "docs/ネーム_第九章.json",  "prompts/ch09.jsonl", 3)
    build(10, "docs/ネーム_第十章.json", "prompts/ch10.jsonl", 3)
