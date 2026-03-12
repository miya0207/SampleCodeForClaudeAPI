"""
コスト追跡デモ
対応章: reliability.md, bonus-cost.md

実行:
    python examples/06_reliability/cost_tracker.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client
from src.cost import CostTracker, calculate_cost, MODEL_COSTS


def demo_cost_calculation():
    """コスト計算のデモ（API呼び出しなし）。"""
    print("=== コスト計算 ===")
    print("モデル別コスト（1回の呼び出し例: input=1000, output=500 tokens）:")

    for model in ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"]:
        cost = calculate_cost(model, input_tokens=1000, output_tokens=500)
        print(f"  {model}: ${cost:.6f} ({cost * 150:.4f}円)")

    print("\nHaiku vs Sonnet のコスト比較（同じ処理）:")
    haiku_cost = calculate_cost("claude-haiku-4-5", 1000, 500)
    sonnet_cost = calculate_cost("claude-sonnet-4-6", 1000, 500)
    ratio = sonnet_cost / haiku_cost
    print(f"  Haiku: ${haiku_cost:.6f}")
    print(f"  Sonnet: ${sonnet_cost:.6f}")
    print(f"  Sonnetは Haiku の {ratio:.1f}倍のコスト")


def demo_cost_tracker():
    """CostTrackerのデモ（API呼び出しあり）。"""
    print("\n=== CostTracker デモ ===")

    tracker = CostTracker(budget_usd=1.0, save_path="/tmp/demo_cost.json")
    client = get_client()

    tasks = [
        ("記事生成", "claude-sonnet-4-6", "Pythonの非同期処理について200字の記事を書いてください"),
        ("SEO最適化", "claude-haiku-4-5", "タイトル: 'Python非同期処理入門' のSEOタイトルを1行で提案してください"),
        ("品質評価", "claude-haiku-4-5", "この記事タイトルを10点満点で評価してください: 'Python asyncio完全ガイド'"),
    ]

    for task_name, model, prompt in tasks:
        response = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        cumulative = tracker.record(
            model=model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            task_name=task_name,
        )
        print(f"  {task_name} ({model}): 累計 ${cumulative:.4f}")

    print("\n今月のサマリー:")
    for key, val in tracker.summary.items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    demo_cost_calculation()
    demo_cost_tracker()
