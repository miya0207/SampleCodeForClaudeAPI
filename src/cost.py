"""
CostTracker — 月次APIコスト追跡・予算管理
対応章: reliability.md, bonus-cost.md

価格は 2026年3月時点。Anthropicの価格改定時は更新してください。
https://www.anthropic.com/pricing
"""
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# USD per 1M tokens (2026年3月時点)
MODEL_COSTS: dict[str, dict[str, float]] = {
    "claude-haiku-4-5":            {"input": 0.80,  "output": 4.00},
    "claude-haiku-4-5-20251001":   {"input": 0.80,  "output": 4.00},
    "claude-sonnet-4-6":           {"input": 3.00,  "output": 15.00},
    "claude-opus-4-6":             {"input": 15.00, "output": 75.00},
}

DEFAULT_MONTHLY_BUDGET_USD = 20.0
ALERT_THRESHOLD = 0.80  # 予算の80%でアラート


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """APIコール1回のコスト（USD）を計算する。"""
    # 不明なモデルはSonnetのコストで計算（保守的な見積もり）
    costs = MODEL_COSTS.get(model, MODEL_COSTS["claude-sonnet-4-6"])
    return (
        input_tokens * costs["input"] / 1_000_000 +
        output_tokens * costs["output"] / 1_000_000
    )


@dataclass
class MonthlySummary:
    month: str  # "2026-03"
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    model_breakdown: dict = field(default_factory=dict)


class CostTracker:
    """
    月次APIコストをスレッドセーフに追跡する。

    使い方:
        tracker = CostTracker()
        tracker.record("claude-haiku-4-5", input_tokens=100, output_tokens=200)
        print(tracker.summary)
    """

    def __init__(
        self,
        budget_usd: float = DEFAULT_MONTHLY_BUDGET_USD,
        save_path: str = "out/cost.json",
    ):
        self.budget_usd = budget_usd
        self.save_path = Path(save_path)
        self._lock = threading.Lock()
        self._summary = self._load_or_create()

    def record(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_name: str = "unknown",
    ) -> float:
        """
        1回のAPIコールを記録する。

        Returns:
            今月の累積コスト (USD)
        """
        cost = calculate_cost(model, input_tokens, output_tokens)

        with self._lock:
            self._summary.total_input_tokens += input_tokens
            self._summary.total_output_tokens += output_tokens
            self._summary.total_cost_usd += cost
            self._summary.call_count += 1

            if model not in self._summary.model_breakdown:
                self._summary.model_breakdown[model] = 0.0
            self._summary.model_breakdown[model] += cost

            self._save()

            if self._summary.total_cost_usd >= self.budget_usd * ALERT_THRESHOLD:
                self._alert()

        return self._summary.total_cost_usd

    @property
    def summary(self) -> dict:
        """現在の月次サマリーを辞書で返す。"""
        with self._lock:
            return {
                "month": self._summary.month,
                "total_cost_usd": round(self._summary.total_cost_usd, 4),
                "budget_usd": self.budget_usd,
                "usage_pct": f"{self._summary.total_cost_usd / self.budget_usd * 100:.1f}%",
                "call_count": self._summary.call_count,
                "total_tokens": (
                    self._summary.total_input_tokens + self._summary.total_output_tokens
                ),
                "model_breakdown": {
                    k: round(v, 4) for k, v in self._summary.model_breakdown.items()
                },
            }

    def _alert(self):
        pct = self._summary.total_cost_usd / self.budget_usd * 100
        print(
            f"⚠️  予算アラート: ${self._summary.total_cost_usd:.3f} / "
            f"${self.budget_usd:.0f} ({pct:.0f}%使用)"
        )

    def _load_or_create(self) -> MonthlySummary:
        current_month = datetime.now().strftime("%Y-%m")
        if self.save_path.exists():
            try:
                data = json.loads(self.save_path.read_text())
                if data.get("month") == current_month:
                    return MonthlySummary(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return MonthlySummary(month=current_month)

    def _save(self):
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "month": self._summary.month,
            "total_input_tokens": self._summary.total_input_tokens,
            "total_output_tokens": self._summary.total_output_tokens,
            "total_cost_usd": self._summary.total_cost_usd,
            "call_count": self._summary.call_count,
            "model_breakdown": self._summary.model_breakdown,
        }
        self.save_path.write_text(json.dumps(data, indent=2))
