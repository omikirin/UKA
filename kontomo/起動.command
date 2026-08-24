#!/bin/zsh
cd "$(dirname "$0")"
PORT=8781
if ! lsof -i ":$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 &
  sleep 1
fi
open "http://127.0.0.1:$PORT/こんとも撮影ツール.html"
