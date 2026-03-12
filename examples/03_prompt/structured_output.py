"""
構造化出力（JSON / XML）
対応章: prompt-engineering.md

LLMにJSONを確実に出力させ、パースする実装例。

実行:
    python examples/03_prompt/structured_output.py
"""
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client


@dataclass
class ArticleMeta:
    title: str
    summary: str
    keywords: list[str]
    difficulty: str  # beginner / intermediate / advanced


def extract_json(text: str) -> dict:
    """レスポンスからJSONを抽出する（コードブロック対応）。"""
    # ```json ... ``` の形式から抽出
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # プレーンJSONとして試みる
    match2 = re.search(r'\{.*\}', text, re.DOTALL)
    if match2:
        return json.loads(match2.group())
    raise ValueError(f"JSONが見つかりません: {text[:100]}")


def generate_article_meta(keyword: str) -> ArticleMeta:
    client = get_client()

    prompt = f"""以下のキーワードについての技術記事メタデータをJSON形式で返してください。

キーワード: {keyword}

以下のJSON形式で回答してください:
```json
{{
  "title": "記事タイトル（60字以内）",
  "summary": "記事の要約（120字以内）",
  "keywords": ["キーワード1", "キーワード2", "キーワード3"],
  "difficulty": "beginner または intermediate または advanced"
}}
```"""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    data = extract_json(response.content[0].text)
    return ArticleMeta(**data)


if __name__ == "__main__":
    for keyword in ["Python asyncio", "Claude API tool_use"]:
        print(f"\n=== キーワード: {keyword} ===")
        meta = generate_article_meta(keyword)
        print(f"タイトル: {meta.title}")
        print(f"要約: {meta.summary}")
        print(f"キーワード: {meta.keywords}")
        print(f"難易度: {meta.difficulty}")
