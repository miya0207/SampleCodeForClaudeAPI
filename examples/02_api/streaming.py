"""
ストリーミングレスポンス
対応章: claude-api.md

実行:
    python examples/02_api/streaming.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client

def stream_response(prompt: str, model: str = "claude-haiku-4-5") -> str:
    """
    ストリーミングで回答を受け取り、文字単位で表示する。
    長い回答の体感待ち時間を短縮できる。
    """
    client = get_client()
    collected = []

    print(f"[streaming] モデル: {model}")
    print("--- 回答 ---")

    with client.messages.stream(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            collected.append(text)

    print("\n--- 終了 ---")

    final = stream.get_final_message()
    print(f"入力: {final.usage.input_tokens} tokens")
    print(f"出力: {final.usage.output_tokens} tokens")

    return "".join(collected)


if __name__ == "__main__":
    stream_response(
        "Pythonの非同期処理（asyncio）を初心者向けに200字で説明してください。"
    )
