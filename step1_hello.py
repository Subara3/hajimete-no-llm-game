# -*- coding: utf-8 -*-
"""はじめの一歩。さくらのAI Engine に、一言だけ話しかけてみる。

    python step1_hello.py

pip install は要りません。Python に最初から入っているものだけで動きます。
"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")  # Windows のコンソールで日本語を化けさせない

# .env ファイルから、さくらのAI Engine のトークンを読む
TOKEN = ""
for line in open(".env", encoding="utf-8"):
    if line.startswith("SAKURA_AI_TOKEN="):
        TOKEN = line.split("=", 1)[1].strip()

# AI に送る内容。messages が会話の中身、model がどのAIに聞くか
body = {
    "model": "preview/gemma-4-31B-it",
    "messages": [
        {"role": "user", "content": "こんにちは。あなたは誰ですか？　20文字くらいで答えてね"}
    ],
}

req = urllib.request.Request(
    "https://api.ai.sakura.ad.jp/v1/chat/completions",
    data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req) as res:
    answer = json.loads(res.read().decode("utf-8"))

# 返ってきた JSON の、この場所に AI の返事が入っている
print(answer["choices"][0]["message"]["content"])
