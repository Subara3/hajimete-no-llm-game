"""門番ゲームに使うモデルを選ぶための実測。

各モデルに同じ「門番システムプロンプト＋プレイヤーの説得」を投げ、
 - JSONを素直に返すか（response_format あり／なし）
 - セリフの質と長さ
 - 応答時間
を比べる。OpenAI互換 /v1/chat/completions のみを使う。
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent

MODELS = [
    "gpt-oss-120b",
    "preview/gemma-4-31B-it",
    "preview/Qwen3.6-35B-A3B",
    "preview/Kimi-K2.6",
    "preview/Kimi-K2.7-Code",
    "llm-jp-3.1-8x13b-instruct4",
]

SYSTEM = """あなたは城門を守る門番です。無愛想でぶっきらぼう、簡単には人を通しません。
ただし筋の通った話には弱く、心を動かされることがあります。

プレイヤーの言葉に対して、必ず次のJSONだけを返してください。前置きも説明も不要です。
{"serifu": "門番のセリフ。40文字以内", "kokoro": 0から100の整数, "reason": "心証が動いた理由。20文字以内"}

kokoro は門番の心証です。今の心証から、話の説得力に応じて増減させてください。
くだらない話や脅しでは下がります。80以上になったら門を開けます。"""

USER = "現在の心証: 30\nプレイヤーの言葉: 「この先の村に、母が一人で待っているんです。薬を届けたい」"


def load_env():
    env = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def ask(base, token, model, json_mode):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        "max_tokens": 2000,
        "temperature": 0.8,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        base + "/v1/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"status": 200, "sec": round(time.time() - t0, 2), "data": data}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "sec": round(time.time() - t0, 2),
                "body": e.read().decode("utf-8", errors="replace")[:300]}
    except Exception as e:
        return {"status": None, "sec": round(time.time() - t0, 2), "body": str(e)[:200]}


def main():
    env = load_env()
    base, token = env["SAKURA_AI_BASE_URL"], env["SAKURA_AI_TOKEN"]
    out = []
    for model in MODELS:
        for json_mode in (False, True):
            r = ask(base, token, model, json_mode)
            label = f"{model} json_mode={json_mode}"
            rec = {"model": model, "json_mode": json_mode,
                   "status": r["status"], "sec": r["sec"]}
            if r["status"] == 200:
                ch = r["data"]["choices"][0]
                text = (ch["message"].get("content") or "").strip()
                rec["finish"] = ch.get("finish_reason")
                rec["usage"] = r["data"].get("usage")
                rec["text"] = text
                try:
                    rec["parsed"] = json.loads(text)
                    rec["json_ok"] = True
                except Exception:
                    rec["json_ok"] = False
                print(f"[{label}] {r['sec']}s json_ok={rec['json_ok']} finish={rec['finish']}")
                print(f"    {text[:200]}")
            else:
                rec["body"] = r.get("body")
                print(f"[{label}] status={r['status']} {r['sec']}s {r.get('body','')[:150]}")
            out.append(rec)
            time.sleep(1.5)
    dest = ROOT / "logs" / "probe_gate.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n保存: {dest}")


if __name__ == "__main__":
    main()
