"""
Zero-shot CoT（Chain of Thought）プロンプト
対応章: prompt-engineering.md

「ステップバイステップで考えてください」を付けるだけで精度が上がることを確認する。

実行:
    python examples/03_prompt/zero_shot_cot.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client


def simple_prompt(question: str) -> str:
    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text


def cot_prompt(question: str) -> str:
    client = get_client()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"{question}\n\nステップバイステップで考えてください。"
        }]
    )
    return response.content[0].text


if __name__ == "__main__":
    question = "太郎は15個のリンゴを持っています。3人の友達に均等に配ったとき、余ったリンゴを全員で1個ずつ食べると最終的に何個残りますか？"

    print("=== 通常プロンプト ===")
    print(simple_prompt(question))

    print("\n=== CoTプロンプト ===")
    print(cot_prompt(question))
