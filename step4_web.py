# -*- coding: utf-8 -*-
"""よっつめ。ブラウザで遊べるようにする。

    python step4_web.py

Python に最初から入っている http.server だけで動きます。
起動するとブラウザが開きます。開かないときは http://localhost:8000 へ。

ゲームの中身は monban.py にあります。ここがやっているのは
「画面を配ること」と「入力を monban.py に渡すこと」だけです。
"""
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from monban import KOKORO_WIN, MAX_TURN, Monban, read_token

sys.stdout.reconfigure(encoding="utf-8")

PORT = 8000
TOKEN = read_token()

game = Monban(TOKEN)   # 遊んでいる勝負はひとつだけ（自分の手元で遊ぶ前提）


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        global game
        if self.path in ("/", "/index.html"):
            game = Monban(TOKEN)   # 画面を開き直したら、勝負も最初から
            # 毎回ファイルを読むので、index.html を直したらリロードだけで反映されます
            self._send(200, "text/html; charset=utf-8", Path("index.html").read_bytes())
        else:
            self._send(404, "text/plain; charset=utf-8", "ないです".encode("utf-8"))

    def do_POST(self):
        global game
        size = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(size).decode("utf-8") or "{}")

        if self.path == "/reset":
            game = Monban(TOKEN)
            result = {"kokoro": game.kokoro, "left": MAX_TURN, "state": "playing"}
        elif self.path == "/talk":
            result = game.talk(data.get("text", ""))
            print(f"  心証 {result['kokoro']:>3}  ({result['delta']:+d})  {result['serifu']}")
        else:
            self._send(404, "application/json", b"{}")
            return

        result["win"] = KOKORO_WIN
        self._send(200, "application/json; charset=utf-8",
                   json.dumps(result, ensure_ascii=False).encode("utf-8"))

    def _send(self, code, ctype, payload):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass   # アクセスログは静かに


print(f"門の前に立った。 http://localhost:{PORT}")
print("（止めるときは Ctrl+C）\n")
webbrowser.open(f"http://localhost:{PORT}")
try:
    HTTPServer(("localhost", PORT), Handler).serve_forever()
except KeyboardInterrupt:
    print("\n門を閉じた。")
