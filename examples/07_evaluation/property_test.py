"""
性質ベーステスト（Property-based testing）
対応章: evaluation.md

LLMの確率的出力に対して「満たすべき性質」でテストする。

実行:
    python examples/07_evaluation/property_test.py
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client


@dataclass
class ArticleProperties:
    """記事が満たすべき性質の定義。"""
    min_length: int = 400
    max_length: int = 3000
    required_keywords: list[str] = None
    forbidden_patterns: list[str] = None

    def __post_init__(self):
        if self.required_keywords is None:
            self.required_keywords = []
        if self.forbidden_patterns is None:
            self.forbidden_patterns = []


def check_properties(content: str, props: ArticleProperties) -> tuple[bool, list[str]]:
    """記事が性質を満たすか検証する。(合格, エラーリスト) を返す。"""
    errors = []

    length = len(content)
    if length < props.min_length:
        errors.append(f"文字数不足: {length} < {props.min_length}")
    if length > props.max_length:
        errors.append(f"文字数超過: {length} > {props.max_length}")

    for kw in props.required_keywords:
        if kw not in content:
            errors.append(f"必須キーワード欠如: '{kw}'")

    for pattern in props.forbidden_patterns:
        if re.search(pattern, content):
            errors.append(f"禁止パターン検出: '{pattern}'")

    return len(errors) == 0, errors


def run_sla_test(
    generate_fn,
    check_fn,
    n_trials: int = 5,
    sla_pass_rate: float = 0.80,
) -> dict:
    """N回実行してSLA合格率を確認する。"""
    passed = 0
    all_errors = []

    for i in range(n_trials):
        output = generate_fn()
        ok, errors = check_fn(output)
        if ok:
            passed += 1
        else:
            all_errors.extend(errors[:2])
        print(f"  試行 {i+1}/{n_trials}: {'✅' if ok else '❌'}")

    pass_rate = passed / n_trials
    meets_sla = pass_rate >= sla_pass_rate

    return {
        "passed": passed,
        "total": n_trials,
        "pass_rate": pass_rate,
        "meets_sla": meets_sla,
        "sla_target": sla_pass_rate,
        "errors": list(set(all_errors))[:3],
    }


if __name__ == "__main__":
    client = get_client()

    def generate_article() -> str:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=512,
            messages=[{"role": "user", "content": "Pythonの型ヒントについて400字以上で解説してください。"}]
        )
        return response.content[0].text

    props = ArticleProperties(
        min_length=300,
        required_keywords=["Python"],
        forbidden_patterns=[r"申し訳", r"できません"],
    )

    print("=== SLAテスト実行 (n=5, SLA=80%) ===")
    result = run_sla_test(
        generate_fn=generate_article,
        check_fn=lambda text: check_properties(text, props),
        n_trials=5,
        sla_pass_rate=0.80,
    )

    print(f"\n結果: {result['passed']}/{result['total']} 合格")
    print(f"合格率: {result['pass_rate']:.0%}")
    print(f"SLA達成: {'✅' if result['meets_sla'] else '❌'}")
    if result["errors"]:
        print(f"頻出エラー: {result['errors']}")
