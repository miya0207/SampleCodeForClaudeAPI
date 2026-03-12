"""
Claude API 基本呼び出し
対応章: claude-api.md

実行:
    python examples/02_api/basic_call.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client

def main():
    client = get_client()

    print("=== 基本的なメッセージ送信 ===")
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[
            {"role": "user", "content": "Pythonのリスト内包表記を1行で説明してください。"}
        ]
    )

    print(f"回答: {response.content[0].text}")
    print(f"入力トークン: {response.usage.input_tokens}")
    print(f"出力トークン: {response.usage.output_tokens}")
    print(f"stop_reason: {response.stop_reason}")

    print("\n=== system プロンプト付き ===")
    response2 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        system="あなたは簡潔に答えるPythonチューターです。答えは3行以内にしてください。",
        messages=[
            {"role": "user", "content": "デコレータとは何ですか？"}
        ]
    )
    print(f"回答: {response2.content[0].text}")

    print("\n=== マルチターン会話 ===")
    messages = [
        {"role": "user", "content": "Pythonの型ヒントの書き方を教えてください"},
        {"role": "assistant", "content": "型ヒントは `変数名: 型` の形式で書きます。例: `def greet(name: str) -> str:`"},
        {"role": "user", "content": "Optional型はどう書きますか？"},
    ]
    response3 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=messages,
    )
    print(f"回答: {response3.content[0].text}")


if __name__ == "__main__":
    main()
