"""
リトライ・フォールバック実装
対応章: reliability.md

指数バックオフでリトライし、失敗時にHaikuへフォールバックする。

実行:
    python examples/06_reliability/retry_fallback.py
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client, call_with_retry, call_with_fallback, FALLBACK_CHAIN


def demo_basic_retry():
    """正常なリトライ動作の確認（実際には429は発生しない）。"""
    print("=== リトライ付きAPI呼び出し ===")
    client = get_client()

    start = time.time()
    response = call_with_retry(
        client,
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "1+1は？"}],
        max_tokens=64,
        max_retries=3,
    )
    elapsed = time.time() - start
    print(f"回答: {response.content[0].text.strip()}")
    print(f"所要時間: {elapsed:.2f}秒")


def demo_fallback_chain():
    """フォールバックチェーンのデモ。"""
    print("\n=== フォールバックチェーン ===")
    print(f"チェーン: {FALLBACK_CHAIN}")

    client = get_client()

    response, used_model = call_with_fallback(
        client,
        messages=[{"role": "user", "content": "Pythonの型ヒントとは？1文で答えてください。"}],
        max_tokens=128,
    )
    print(f"使用モデル: {used_model}")
    print(f"回答: {response.content[0].text.strip()}")


def demo_resilient_client():
    """
    本番用のResilientClientパターン。

    - プライマリ: claude-sonnet-4-6
    - フォールバック: claude-haiku-4-5
    - 429/529 エラーは自動リトライ
    """
    print("\n=== ResilientClient パターン ===")

    client = get_client()

    # Haiku (低コスト) で試みる
    response, model = call_with_fallback(
        client,
        messages=[{"role": "user", "content": "fastAPIの特徴を1行で"}],
        max_tokens=128,
        fallback_chain=["claude-haiku-4-5"],  # Haikuのみのチェーン
    )
    print(f"Haikuで回答 ({model}): {response.content[0].text.strip()}")


if __name__ == "__main__":
    demo_basic_retry()
    demo_fallback_chain()
    demo_resilient_client()
