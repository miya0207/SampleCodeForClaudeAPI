"""
LLM-as-Judge（AIが記事を採点する）
対応章: evaluation.md

Claude Haiku を採点官として使い、記事を4軸で評価する。

実行:
    python examples/07_evaluation/llm_judge.py
"""
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client


@dataclass
class JudgeScore:
    readability: int    # 読みやすさ 1-10
    accuracy: int       # 正確さ 1-10
    engagement: int     # 引きつけ度 1-10
    compliance: int     # 指示準拠度 1-10
    overall: float
    improvement: str


JUDGE_PROMPT = """技術記事を4軸で評価してください。

## 記事
キーワード: {keyword}
{content}

## 評価 (JSON形式で回答)
  {{
    "readability": <1-10>,
    "accuracy": <1-10>,
    "engagement": <1-10>,
    "compliance": <1-10>,
    "improvement": "<改善点を1つ>"
  }}"""

WEIGHTS = {"readability": 0.3, "accuracy": 0.3, "engagement": 0.2, "compliance": 0.2}


def judge_article(keyword: str, content: str) -> JudgeScore:
    client = get_client()

    response = client.messages.create(
        model="claude-haiku-4-5",  # 評価はHaikuで十分
        max_tokens=512,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            keyword=keyword, content=content[:2000]
        )}]
    )

    text = response.content[0].text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"JSONが見つかりません: {text[:100]}")

    data = json.loads(match.group())

    r, a, e, c = (
        data.get("readability", 5),
        data.get("accuracy", 5),
        data.get("engagement", 5),
        data.get("compliance", 5),
    )
    overall = r * WEIGHTS["readability"] + a * WEIGHTS["accuracy"] + \
              e * WEIGHTS["engagement"] + c * WEIGHTS["compliance"]

    return JudgeScore(
        readability=r, accuracy=a, engagement=e, compliance=c,
        overall=round(overall, 2),
        improvement=data.get("improvement", ""),
    )


if __name__ == "__main__":
    client = get_client()

    # 評価対象の記事を生成
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": "Pythonのデコレータについて500字で解説してください"}]
    )
    article = response.content[0].text
    print(f"記事（先頭100字）: {article[:100]}...")

    # 評価
    print("\n=== LLM-as-Judge 評価 ===")
    score = judge_article("Pythonデコレータ", article)
    print(f"readability:  {score.readability}/10")
    print(f"accuracy:     {score.accuracy}/10")
    print(f"engagement:   {score.engagement}/10")
    print(f"compliance:   {score.compliance}/10")
    print(f"overall:      {score.overall}/10")
    print(f"改善提案:     {score.improvement}")
