# 音声の置き場

こんともの口パク用の音声(と台本)を、このフォルダに置く。

1. GitHubのこのフォルダで **Add file → Upload files** から音声をアップロードする
   (wav / mp3 / m4a。Webからのアップロードは1ファイル25MBまで)
2. Actions の **「こんとも 口パクタイミング生成 (音声→母音)」** を開いて
   **Run workflow** を押す
3. `audio` に `kontomo/audio/ファイル名.wav` と入れる
   (ネット上の音声URLでもよい)
4. `script_text` に台本をそのまま貼る(漢字のままでOK。入れると精度が上がる)
5. 実行すると `kontomo/cues/ファイル名.json` ができてコミットされる
6. こんとも撮影ツールを開くと、タイミングJSONのプルダウンから選べる

台本をファイルで置きたいときは、同じ名前の `.txt` を置いて
`script_path` に `kontomo/audio/ファイル名.txt` と入れる。
