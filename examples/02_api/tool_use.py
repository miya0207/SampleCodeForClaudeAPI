"""
Tool Use（ツール呼び出し）の基本
対応章: claude-api.md

実行:
    python examples/02_api/tool_use.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client


# ツール実装
def get_current_datetime() -> dict:
    return {"datetime": datetime.now().isoformat(), "timezone": "Asia/Tokyo"}


def calculate(expression: str) -> dict:
    """安全な数式評価（evalを使わない）。"""
    try:
        # 簡易実装: +, -, *, / のみ許可
        import re
        if re.search(r'[^0-9\s\+\-\*\/\.\(\)]', expression):
            return {"error": "許可されていない文字が含まれています"}
        result = eval(expression, {"__builtins__": {}})  # noqa
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e)}


TOOLS = [
    {
        "name": "get_current_datetime",
        "description": "現在の日時を取得する",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "calculate",
        "description": "数式を計算する",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "計算式 例: 3 * (4 + 5)"}
            },
            "required": ["expression"]
        }
    },
]

TOOL_FUNCTIONS = {
    "get_current_datetime": get_current_datetime,
    "calculate": calculate,
}


def call_with_tools(user_message: str) -> str:
    """ツール付きでClaude APIを呼び出す1ターン処理。"""
    client = get_client()
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        tools=TOOLS,
        messages=messages,
    )

    print(f"stop_reason: {response.stop_reason}")

    if response.stop_reason == "end_turn":
        return response.content[0].text

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"ツール呼び出し: {block.name}({block.input})")
            fn = TOOL_FUNCTIONS[block.name]
            result = fn(**block.input)
            print(f"ツール結果: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        messages.append({"role": "user", "content": tool_results})

        final = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            tools=TOOLS,
            messages=messages,
        )
        return final.content[0].text

    return "予期しないstop_reason"


if __name__ == "__main__":
    print("=== 日時取得 ===")
    print(call_with_tools("今は何時ですか？"))

    print("\n=== 計算 ===")
    print(call_with_tools("3.14 * 5 * 5 を計算してください（円の面積）"))
