#!/usr/bin/env python3
"""音声（と任意で台本）から、口パク用の母音タイムラインを作る。

Brainの口パクアドオンと同じ考え方: faster-whisper で発話のタイミングを取り、
pykakasi で読みを母音（n/a/i/u/e/o）へ落とす。認識文ではなく台本を優先する。

出力: {"duration":秒, "cues":[{"t":秒,"v":"a"},...]} の JSON。
プレイヤー.html がこれを読んで口を動かす。
"""
import argparse, json, os, re, sys

ENV_HINT = '/Users/harukanegishi/Documents/Codex/_共通/Blender/口パクアドオン/work/atlas-whisper-env/bin/python'

ap = argparse.ArgumentParser()
ap.add_argument('--audio', required=True)
ap.add_argument('--script', default=None, help='正式な台本のテキストファイル（あれば認識文より優先）')
ap.add_argument('--out', required=True)
ap.add_argument('--model', default='small')
ap.add_argument('--close-silence', type=float, default=0.25,
                help='この秒数以上の無音で口を閉じる')
ap.add_argument('--lead', type=float, default=0.04, help='口を音より何秒先に動かすか')
a = ap.parse_args()

try:
    from faster_whisper import WhisperModel
    import pykakasi
except ImportError:
    sys.exit(f'faster-whisper / pykakasi が要ります。次のPythonで実行してください:\n  {ENV_HINT} {sys.argv[0]} ...')

kks = pykakasi.kakasi()
VOWEL = {'a': 'a', 'i': 'i', 'u': 'u', 'e': 'e', 'o': 'o'}


def to_vowels(text):
    """日本語テキスト → 母音の並び。撥音・促音・長音は 'n' / 直前維持 で扱う"""
    out = []
    for item in kks.convert(text):
        roma = item['hepburn']
        # ヘボン式のローマ字から母音を拾う
        i = 0
        while i < len(roma):
            c = roma[i]
            if c in VOWEL:
                out.append(VOWEL[c]); i += 1
            elif c == 'n' and (i+1 >= len(roma) or roma[i+1] not in 'aiueoy'):
                out.append('n'); i += 1
            else:
                i += 1
    return out


model = WhisperModel(a.model, device='cpu', compute_type='int8')
segments, info = model.transcribe(a.audio, language='ja', word_timestamps=True)
segments = list(segments)

script_vowels = None
if a.script:
    script_vowels = to_vowels(open(a.script, encoding='utf-8').read())

cues = []
words = [w for s in segments for w in (s.words or [])]
if not words:
    sys.exit('発話が検出できませんでした。音声を確認してください。')

if script_vowels:
    # 台本の母音列を、認識できた発話区間の長さに比例して割り当てる
    total = sum(w.end - w.start for w in words)
    n = len(script_vowels)
    per = total / max(1, n)
    idx, t = 0, None
    for w in words:
        cnt = max(1, round((w.end - w.start) / per))
        for k in range(cnt):
            if idx >= n:
                break
            tt = w.start + (w.end - w.start) * k / cnt
            cues.append({'t': round(max(0, tt - a.lead), 3), 'v': script_vowels[idx]})
            idx += 1
else:
    for w in words:
        vs = to_vowels(w.word)
        if not vs:
            continue
        for k, v in enumerate(vs):
            tt = w.start + (w.end - w.start) * k / len(vs)
            cues.append({'t': round(max(0, tt - a.lead), 3), 'v': v})

# 無音で口を閉じる
closed = []
prev_end = 0.0
for w in words:
    if w.start - prev_end >= a.close_silence:
        closed.append({'t': round(prev_end, 3), 'v': 'n'})
    prev_end = w.end
closed.append({'t': round(prev_end, 3), 'v': 'n'})
cues = sorted(cues + closed, key=lambda c: c['t'])

dur = max(w.end for w in words) + 0.4
json.dump({'audio': os.path.basename(a.audio), 'duration': round(dur, 3), 'cues': cues},
          open(a.out, 'w'), indent=1, ensure_ascii=False)
print(f'{len(cues)} キュー / {dur:.2f}秒 -> {a.out}')
