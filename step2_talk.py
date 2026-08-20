# -*- coding: utf-8 -*-
"""ふたつめ。AI に「門番」の人格を与えて、会話を続けてみる。

    python step2_talk.py

step1 との違いは2つだけです。
  1. system という役割のメッセージで、AI に「あなたは門番です」と教える
  2. これまでのやりとりを messages に積んでいく（AI に記憶はないので、毎回ぜんぶ渡す）
"""
import json
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")  # この2行がないと Windows で日本語が化けます

TOKEN = ""
try:
    for line in open(".env", encoding="utf-8"):
        if line.startswith("SAKURA_AI_TOKEN="):
            TOKEN = line.split("=", 1)[1].strip()
except FileNotFoundError:
    sys.exit(".env がありません。.env.example をコピーして .env にし、トークンを貼ってください")
if not TOKEN:
    sys.exit(".env に SAKURA_AI_TOKEN= の行がありません")

# これが「人格」。AI はこの指示を、会話のいちばん上に置かれた前提として読む
SYSTEM = """あなたは城門を守る門番です。無愛想でぶっきらぼう、簡単には人を通しません。
ただし筋の通った話には弱く、心を動かされることがあります。
返事は40文字以内の、門番のセリフだけにしてください。"""

# 会話の記録。最初に system を1つ入れておく
messages = [{"role": "system", "content": SYSTEM}]


def ask():
    """今までの会話を丸ごと送って、門番の返事をもらう"""
    body = {"model": "preview/gemma-4-31B-it", "messages": messages, "max_tokens": 2000}
    req = urllib.request.Request(
        "https://api.ai.sakura.ad.jp/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            data = json.loads(res.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "（.env のトークンが違うようです）"
        if e.code == 429:
            return "（今月の無料枠を使い切ったか、続けて呼びすぎです。少し待ってね）"
        return f"（HTTPエラー {e.code}）"


print("門番「ここから先は通せん。用件を申せ」")
print("（何か話しかけてください。Enter だけで終わります）\n")

while True:
    you = input("> ").strip()
    if not you:
        break
    messages.append({"role": "user", "content": you})
    serifu = ask()
    messages.append({"role": "assistant", "content": serifu})  # 返事も記録に積む
    print(f"門番「{serifu}」\n")

print("門番「二度と来るな」")
