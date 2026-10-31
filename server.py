import os
import json
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

def parse_json_result(result, fallback=None):
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        start = result.find("{")
        end = result.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(result[start:end + 1])
            except json.JSONDecodeError:
                pass
        return fallback or {}

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


@app.post("/api/score-question")
def score_question():
    try:
        data = request.get_json(silent=True) or {}

        question = str(data.get("question", "")).strip()
        level = str(data.get("level", "初級")).strip()

        # 質問が空の場合
        if not question:
            return jsonify({
                "error": "採点する質問が空です。"
            }), 400

        # 学習レベルごとの採点方針
        level_hint = {
            "初級": """
初心者がAIを使う練習として採点してください。
難しいことを要求しすぎず、
基本的な質問の分かりやすさを重視してください。
""",

            "中級": """
質問の具体性、条件、背景、出力形式などを
より詳しく評価してください。
""",

            "上級": """
目的、前提、条件、制約、出力形式、
必要な情報、曖昧さなどを詳しく分析してください。
単に質問が長いだけでは高得点にしないでください。
"""
        }.get(
            level,
            "質問を分かりやすく評価してください。"
        )

        # AI先生への採点指示
        instructions = BASE_INSTRUCTIONS + f"""
あなたは「AI先生」の質問力採点教師です。

ユーザーがAIに送ろうとしている質問を
100点満点で評価してください。

{level_hint}

【採点基準】

1. 目的の明確さ：25点
何を知りたいのか、何をしてほしいのか
明確になっているか。

2. 条件・背景：20点
対象者、状況、前提、制約など、
回答に必要な条件が書かれているか。

3. 具体性：20点
曖昧な表現が少なく、
AIが具体的な内容を理解できるか。

4. 出力形式：15点
箇条書き、表、個数、文字数、
説明方法などが指定されているか。

5. 情報の十分さ：20点
適切な回答をするために
必要な情報が十分に含まれているか。

【重要な採点ルール】

・質問が長いだけでは高得点にしない。
・短くても明確で必要な情報があれば高く評価する。
・質問の内容そのものではなく、
  「AIへの質問としてどれだけ分かりやすいか」を評価する。
・各項目の上限を超えない。
・合計点は必ず100点以下。
・5項目の点数の合計を総合点にする。
・改善できるポイントを具体的に説明する。
・改善後の質問を作成する。
・改善後の質問は、そのままコピーしてAIに送れる形にする。

【評価対象】

{question}

【JSONだけを返してください】

Markdownのコードブロックは使用しないでください。

{{
  "total": 0,
  "purpose": 0,
  "condition": 0,
  "specific": 0,
  "format": 0,
  "information": 0,
  "rank": "",
  "comment": "",
  "advice": "",
  "betterPrompt": ""
}}
"""

        # OpenAIに質問を採点させる
        result = call_ai(
            instructions,
            question
        )

        import json

        # AIのJSONを読み込む
        try:
            parsed = json.loads(result)

        except json.JSONDecodeError:
            parsed = {
                "purpose": 0,
                "condition": 0,
                "specific": 0,
                "format": 0,
                "information": 0,
                "rank": "再採点してください。",
                "comment": result,
                "advice": "AIからJSON形式の採点結果を取得できませんでした。",
                "betterPrompt": ""
            }

        # 点数を安全に処理する関数
        def safe_score(value, minimum, maximum):
            try:
                value = int(value)
            except:
                value = 0

            return max(
                minimum,
                min(maximum, value)
            )

        # 各項目の点数を制限
        purpose = safe_score(
            parsed.get("purpose", 0),
            0,
            25
        )

        condition = safe_score(
            parsed.get("condition", 0),
            0,
            20
        )

        specific = safe_score(
            parsed.get("specific", 0),
            0,
            20
        )

        format_score = safe_score(
            parsed.get("format", 0),
            0,
            15
        )

        information = safe_score(
            parsed.get("information", 0),
            0,
            20
        )

        # 5項目を合計
        total = (
            purpose
            + condition
            + specific
            + format_score
            + information
        )

        # 合計点からランクを決定
        if total >= 100:
            rank = "🏆 AIマスター級！完璧な質問です！"

        elif total >= 90:
            rank = "🔥 とても良い質問です！"

        elif total >= 75:
            rank = "⭐ 上手な質問です！"

        elif total >= 60:
            rank = "👍 かなり良い質問です！"

        elif total >= 40:
            rank = "📘 もう少し具体的にするとさらに良くなります。"

        else:
            rank = "🌱 まずは質問の基本から練習しましょう。"

        # HTML側に結果を返す
        return jsonify({
            "total": total,

            "purpose": purpose,

            "condition": condition,

            "specific": specific,

            "format": format_score,

            "information": information,

            "rank": rank,

            "comment": str(
                parsed.get("comment", "")
            ),

            "advice": str(
                parsed.get("advice", "")
            ),

            "betterPrompt": str(
                parsed.get("betterPrompt", "")
            )
        })

    except Exception as e:

        # PowerShellに詳しいエラーを表示
        print(
            "SCORE ERROR:",
            repr(e),
            flush=True
        )

        return jsonify({
            "error":
                "質問力の採点でエラーが発生しました。"
                "PowerShellに表示されたSCORE ERRORを確認してください。"
        }), 500

recent_training_questions = []

@app.post("/api/training-question")
def training_question():
    try:
        data = request.get_json(silent=True) or {}
        level = str(data.get("level", "初級")).strip()

        level_hint = {
            "初級": "目的を明確にする基本的な問題",
            "中級": "背景・条件・具体性・出力形式を考える問題",
            "上級": "複数の制約や前提を整理する難しい問題"
        }.get(level, "質問力を鍛える問題")

        instructions = """
あなたはAI質問力トレーニングゲームの出題者です。
AIに伝わりやすい質問文を作る練習問題を1問作成してください。
英語、数学、歴史、自由研究、作文、旅行、プログラミングなど、
幅広いテーマを使ってください。
過去の問題と同じ、または非常によく似た問題は避けてください。
改善後の質問文の正解例は出題文に含めないでください。
JSONだけを返してください。
形式：
{"question": "出題する問題文"}
"""

        prompt = (
            "難易度：" + level_hint
            + "\n過去の問題：\n"
            + json.dumps(recent_training_questions, ensure_ascii=False)
            + "\n過去の問題を避け、新しい問題を1問作ってください。"
        )

        result = call_ai(instructions, prompt)
        parsed = parse_json_result(result, {})
        new_question = str(parsed.get("question", "")).strip()

        if not new_question:
            raise ValueError("AIが問題を返しませんでした。")

        recent_training_questions.append(new_question)
        del recent_training_questions[:-20]

        return jsonify({"question": new_question})

    except Exception as e:
        print("TRAINING QUESTION ERROR:", repr(e), flush=True)
        return jsonify({
            "error": "新しい問題を作成できませんでした。"
        }), 500

@app.post("/api/training-score")
def training_score():
    try:
        data = request.get_json(silent=True) or {}
        question = str(data.get("question", "")).strip()
        answer = str(data.get("answer", "")).strip()
        level = str(data.get("level", "初級")).strip()

        if not question or not answer:
            return jsonify({"error": "問題と回答を入力してください。"}), 400

        instructions = """
あなたはAI質問力トレーニングゲームの採点者です。
ユーザーが作った質問文を100点満点で評価してください。

採点基準：
- 目的の明確さ：25点
- 対象や背景の具体性：25点
- 条件や制約：25点
- 回答の形式の指定：25点

問題文の状況に合った質問かどうかも評価してください。
短い質問でも、必要な情報が明確なら適切に評価してください。
問題文に関係のない条件を付けても高得点にしないでください。
各項目は0〜25点の整数、totalは4項目の合計にしてください。
改善のアドバイスは具体的に書いてください。
betterPromptには改善例を入れてください。
必ずJSONだけを返し、Markdownは使わないでください。

形式：
{
  "total": 0,
  "purpose": 0,
  "target": 0,
  "condition": 0,
  "format": 0,
  "advice": "改善アドバイス",
  "betterPrompt": "改善した質問文"
}
"""
        result = call_ai(
            instructions + "\n学習レベル：" + level,
            "【出題された問題】\n" + question
            + "\n【ユーザーの回答】\n" + answer
        )
        parsed = parse_json_result(result, {})

        def points(name):
            try:
                value = int(parsed.get(name, 0))
            except (TypeError, ValueError):
                value = 0
            return max(0, min(25, value))

        purpose = points("purpose")
        target = points("target")
        condition = points("condition")
        output_format = points("format")
        total = purpose + target + condition + output_format

        return jsonify({
            "total": total,
            "purpose": purpose,
            "target": target,
            "condition": condition,
            "format": output_format,
            "advice": str(parsed.get("advice", "")),
            "betterPrompt": str(parsed.get("betterPrompt", ""))
        })

    except Exception as e:
        print("TRAINING SCORE ERROR:", repr(e), flush=True)
        return jsonify({"error": "採点に失敗しました。サーバーのエラー表示を確認してください。"}), 500

if __name__ == "__main__":
    print("AI先生を起動しています。")
    print("ブラウザで http://127.0.0.1:5000 を開いてください。")
    print("終了するときは Ctrl+C")
    app.run(host="127.0.0.1", port=5000, debug=True)
