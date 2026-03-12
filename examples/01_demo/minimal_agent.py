"""
最小構成のClaude Agent デモ
対応章: demo-agent.md（無料公開章）

セットアップ:
    pip install anthropic python-dotenv
    cp .env.example .env  # APIキーを設定

実行:
    python examples/01_demo/minimal_agent.py
"""
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import anthropic

load_dotenv()

# ---- ツール定義 ----

def get_weather(city: str) -> dict:
    """天気情報（デモ用ダミーデータ）。"""
    dummy_data = {
        "東京": {"temp": 18, "condition": "晴れ", "humidity": 55},
        "大阪": {"temp": 20, "condition": "曇り", "humidity": 60},
    }
    return dummy_data.get(city, {"temp": 15, "condition": "不明", "humidity": 50, "city": city})


def search_restaurants(city: str, weather_condition: str) -> dict:
    """レストラン検索（デモ用ダミーデータ）。"""
    suggestions = {
        "晴れ": ["テラス席のあるカフェ", "公園近くのランチ", "オープンエアのビストロ"],
        "曇り": ["ラーメン屋", "定食屋", "カフェ"],
        "雨":   ["屋内カフェ", "デパートのフードコート", "個室レストラン"],
    }
    restaurants = suggestions.get(weather_condition, ["地元の定食屋"])
    return {"city": city, "suggestions": restaurants}


# Claude API に渡すツールスキーマ
TOOLS = [
    {
        "name": "get_weather",
        "description": "指定した都市の現在の天気と気温を取得する",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "都市名（例: 東京）"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "search_restaurants",
        "description": "都市と天気に合ったレストランを提案する",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "都市名"},
                "weather_condition": {"type": "string", "description": "天気（晴れ/曇り/雨）"}
            },
            "required": ["city", "weather_condition"]
        }
    },
]

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "search_restaurants": search_restaurants,
}


# ---- エージェントループ ----

def run_agent(user_message: str) -> str:
    """
    ReActループを実行して最終回答を返す。

    ループ:
    1. Claude にメッセージを送る
    2. ツール呼び出しがあれば実行して結果を返す
    3. end_turn になったら回答を返す
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("エラー: ANTHROPIC_API_KEY が設定されていません")
        print("  cp .env.example .env  を実行してAPIキーを設定してください")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": user_message}]

    print(f"\n質問: {user_message}\n")

    for step in range(1, 6):  # 最大5イテレーション
        response = client.messages.create(
            model="claude-haiku-4-5",  # デモなのでHaikuで十分
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        print(f"ステップ {step}: stop_reason={response.stop_reason}")

        # 終了
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        # ツール実行
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"  → ツール呼び出し: {block.name}({block.input})")

                fn = TOOL_FUNCTIONS.get(block.name)
                result = fn(**block.input) if fn else {"error": f"Unknown tool: {block.name}"}

                print(f"  ← 結果: {result}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            messages.append({"role": "user", "content": tool_results})

    return "最大イテレーションに達しました"


# ---- 実行 ----

if __name__ == "__main__":
    answer = run_agent("東京の今日の天気と気温に合ったランチを提案してください")
    print(f"\n最終回答:\n{answer}")
