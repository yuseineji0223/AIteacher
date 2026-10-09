import os
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR)

API_KEY = os.environ.get("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY が設定されていません。PowerShellで "
        '$env:OPENAI_API_KEY="あなたのAPIキー" '
        "を設定してから起動してください。"
    )

client = OpenAI(api_key=API_KEY)

# OpenAI APIで利用するモデル。
# 2026-10時点の公式料金ページに掲載されているモデルです。
MODEL = "gpt-6-luna"

BASE_INSTRUCTIONS = """あなたは「AI先生」です。
中高生にも分かりやすく、丁寧に日本語で説明してください。
あなたの役割は、AIの使い方、質問の仕方、プロンプトの作り方を教えることです。
質問に答えるだけでなく、必要に応じて「AIにどう質問するとよいか」も説明してください。
分からないことを事実のように断定せず、必要なら「分かりません」と伝えてください。
"""

def call_ai(instructions, user_input):
    response = client.responses.create(
        model=MODEL,
        instructions=instructions,
        input=user_input
    )
    return response.output_text

@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.post("/api/chat")
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        level = str(data.get("level", "初級")).strip()

        if not message:
            return jsonify({"error": "質問が空です。"}), 400

        level_hint = {
            "初級": "初心者向けに、難しい言葉を避けて小学生でもわかる言葉で説明してください。",
            "中級": "基礎知識がある人向けに、理由も含めて説明してください。",
            "上級": """- 初心者向けの簡単な説明だけで終わらせない
- 背景、原因、仕組み、関連事項まで詳しく説明する
- 必要に応じて専門用語を使用し、その意味も説明する
- 具体例を複数示す
- 「なぜそうなるのか」を説明する
- 複数の視点から考えられる場合は、それぞれ説明する
- 表面的な説明ではなく、深い理解につながる回答にする
- 質問に関連する重要な知識があれば補足する
- ただし、質問から大きく脱線しない
- 事実と推測を区別する
- 確実でない情報は断定しない
- 物語であれば背景、前提、登場人物同士の関係、物語の設定がなぜそのようになっているのか、その設定が物語の展開にどう作用するのかを考える
- 原因と結果を表示する
- 最後に要点を整理する
- 事実と推測の区別ができるようにする"""
        }.get(level, "分かりやすく説明してください。")

        answer = call_ai(
            BASE_INSTRUCTIONS + "\n" + level_hint,
            message
        )
        return jsonify({"answer": answer})

    except Exception as e:
        print("CHAT ERROR:", repr(e), flush=True)
        return jsonify({
            "error": "AIへの接続でエラーが発生しました。PowerShellに表示されたCHAT ERRORを確認してください。"
        }), 500

@app.post("/api/improve")
def improve():
    try:
        data = request.get_json(silent=True) or {}
        question = str(data.get("question", "")).strip()
        level = str(data.get("level", "初級")).strip()

        if not question:
            return jsonify({"error": "質問が空です。"}), 400

        level_hint = {
            "初級": "初心者にも分かる表現で改善してください。",
            "中級": "具体性と条件を増やし、使いやすい質問にしてください。",
            "上級": "目的、前提、制約、出力形式まで明確なプロンプトにしてください。"
        }.get(level, "分かりやすく改善してください。")

        instructions = BASE_INSTRUCTIONS + f"""
次の質問を分析して、よりAIに伝わりやすい質問へ改善してください。
{level_hint}
必ず次のJSONだけを返してください。Markdownのコードブロックは付けないでください。
{{
  "diagnosis": "現在の質問の良い点・不足点を簡潔に説明",
  "advice": "改善するとよいポイント",
  "betterPrompt": "そのままコピーして使える改善後の質問"
}}
"""

        result = call_ai(instructions, question)

        import json
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            # 万一JSONにならなかった場合も画面を止めない
            parsed = {
                "diagnosis": "AIから改善案を受け取りました。",
                "advice": "下の改善後の質問を参考にしてください。",
                "betterPrompt": result
            }

        return jsonify(parsed)

    except Exception as e:
        print("IMPROVE ERROR:", repr(e), flush=True)
        return jsonify({
            "error": "質問改善でエラーが発生しました。PowerShellに表示されたIMPROVE ERRORを確認してください。"
        }), 500

if __name__ == "__main__":
    print("AI先生を起動しています。")
    print("ブラウザで http://127.0.0.1:5000 を開いてください。")
    print("終了するときは Ctrl+C")
    app.run(host="127.0.0.1", port=5000, debug=True)
