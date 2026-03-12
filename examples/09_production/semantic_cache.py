"""
セマンティックキャッシュ効果測定
対応章: bonus-cost.md

類似プロンプトをキャッシュすることでAPI呼び出しを削減する効果を確認する。

実行:
    python examples/09_production/semantic_cache.py
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cache import SemanticCache, jaccard_similarity
from src.client import get_client


def demo_similarity():
    """Jaccard類似度の動作確認（API呼び出しなし）。"""
    print("=== Jaccard類似度 ===")
    pairs = [
        ("Pythonの型ヒントとは", "Pythonの型ヒントを教えて"),
        ("Pythonの型ヒントとは", "Pythonの例外処理について"),
        ("FastAPIの使い方", "FastAPIの基本的な使い方"),
        ("SQLiteとは", "MongoDBとは"),
    ]
    for t1, t2 in pairs:
        sim = jaccard_similarity(t1, t2)
        hit = "✅ ヒット" if sim >= 0.85 else ("🟡 微妙" if sim >= 0.5 else "❌ ミス")
        print(f"  {sim:.2f} {hit}: '{t1}' vs '{t2}'")


def demo_cache_with_api():
    """キャッシュ付きAPI呼び出しのデモ。"""
    print("\n=== セマンティックキャッシュ効果測定 ===")

    cache = SemanticCache(threshold=0.75, max_size=50)
    client = get_client()

    def cached_generate(prompt: str) -> tuple[str, bool]:
        cached = cache.get(prompt)
        if cached:
            return cached, True  # キャッシュヒット

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=128,
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.content[0].text
        cache.set(prompt, result)
        return result, False  # キャッシュミス（新規API呼び出し）

    # 類似したプロンプトを複数回送る
    prompts = [
        "Pythonの型ヒントとは何ですか？",
        "Pythonの型ヒントを教えてください",    # 類似 → キャッシュヒット期待
        "Pythonの型ヒントの書き方は？",          # 類似 → キャッシュヒット期待
        "Pythonのデコレータとは何ですか？",      # 別トピック → ミス
        "Pythonの型ヒントについて詳しく",        # 類似 → ヒット期待
    ]

    api_calls = 0
    for prompt in prompts:
        start = time.time()
        result, from_cache = cached_generate(prompt)
        elapsed = time.time() - start

        if not from_cache:
            api_calls += 1

        status = "✅ キャッシュ" if from_cache else "🔄 API呼び出し"
        print(f"  {status} ({elapsed*1000:.0f}ms): {prompt[:30]}...")

    print(f"\nAPI呼び出し回数: {api_calls}/{len(prompts)}")
    print(f"キャッシュ統計: {cache.stats}")
    print(f"コスト削減率（推定）: {(1 - api_calls/len(prompts)):.0%}")


if __name__ == "__main__":
    demo_similarity()
    demo_cache_with_api()
