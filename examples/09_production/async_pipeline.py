"""
非同期並列実行パイプライン
対応章: production-template.md

ThreadPoolExecutorで複数キーワードの記事を並列生成する。
逐次実行に比べて3〜5倍の高速化が期待できる。

実行:
    python examples/09_production/async_pipeline.py
"""
import asyncio
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client
from src.cost import CostTracker

MAX_WORKERS = 3  # 同時並列数（レート制限に合わせて調整）


def generate_one(keyword: str, tracker: CostTracker) -> dict:
    """
    1キーワードの記事を生成する（スレッド内で実行）。
    Anthropic SDKは同期なので ThreadPoolExecutor で並列化する。
    """
    client = get_client()  # スレッドごとに新しいクライアントを作成
    start = time.time()

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": f"「{keyword}」について3文で解説してください。"
        }]
    )

    elapsed = time.time() - start
    tracker.record(
        model="claude-haiku-4-5",
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        task_name=keyword,
    )

    return {
        "keyword": keyword,
        "content": response.content[0].text,
        "elapsed": elapsed,
    }


async def generate_parallel(keywords: list[str]) -> list[dict]:
    """複数キーワードを並列に生成する。"""
    tracker = CostTracker(save_path="/tmp/async_cost.json")
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, generate_one, kw, tracker)
            for kw in keywords
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # 例外を除外
    valid = [r for r in results if isinstance(r, dict)]
    print(f"\nコスト: {tracker.summary['total_cost_usd']} USD")
    return valid


def generate_sequential(keywords: list[str]) -> list[dict]:
    """比較用: 同じキーワードを逐次生成する。"""
    tracker = CostTracker(save_path="/tmp/seq_cost.json")
    results = []
    for kw in keywords:
        results.append(generate_one(kw, tracker))
    return results


if __name__ == "__main__":
    keywords = [
        "Python asyncio",
        "FastAPI入門",
        "SQLite WALモード",
        "Pythonデコレータ",
        "Claude API tool_use",
    ]

    print("=== 逐次実行 ===")
    start = time.time()
    seq_results = generate_sequential(keywords)
    seq_time = time.time() - start
    print(f"完了: {len(seq_results)}件 / {seq_time:.1f}秒")
    for r in seq_results:
        print(f"  {r['keyword']}: {r['elapsed']:.1f}秒")

    print("\n=== 並列実行（ThreadPoolExecutor） ===")
    start = time.time()
    par_results = asyncio.run(generate_parallel(keywords))
    par_time = time.time() - start
    print(f"完了: {len(par_results)}件 / {par_time:.1f}秒")
    for r in par_results:
        print(f"  {r['keyword']}: {r['elapsed']:.1f}秒")

    if seq_time > 0:
        speedup = seq_time / par_time
        print(f"\n速度向上: {speedup:.1f}倍")
