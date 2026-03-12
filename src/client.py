"""
Claude API クライアント（リトライ・フォールバック込み）
対応章: reliability.md
"""
import os
import time
import random
from dotenv import load_dotenv
import anthropic

load_dotenv()

# フォールバックチェーン（コスト低い順）
FALLBACK_CHAIN = [
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]


def get_client() -> anthropic.Anthropic:
    """環境変数からAPIキーを取得してクライアントを返す。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY が設定されていません。\n"
            ".env.example をコピーして .env を作成し、APIキーを設定してください。\n"
            "  cp .env.example .env"
        )
    return anthropic.Anthropic(api_key=api_key)


def call_with_retry(
    client: anthropic.Anthropic,
    model: str,
    messages: list[dict],
    system: str = "",
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> anthropic.types.Message:
    """
    指数バックオフ + ジッターでリトライするAPI呼び出し。

    429（レート制限）と 529（過負荷）を自動リトライする。
    それ以外のエラーは即座に再raiseする。
    """
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    for attempt in range(max_retries + 1):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            if attempt == max_retries:
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            print(f"  [retry] 429 rate limit. {wait:.1f}秒待機 (試行 {attempt+1}/{max_retries})")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < max_retries:
                wait = (2 ** attempt) + random.uniform(0, 1)
                print(f"  [retry] 529 overloaded. {wait:.1f}秒待機 (試行 {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                raise


def call_with_fallback(
    client: anthropic.Anthropic,
    messages: list[dict],
    system: str = "",
    max_tokens: int = 1024,
    fallback_chain: list[str] = None,
) -> tuple[anthropic.types.Message, str]:
    """
    モデルチェーンを順番に試す。成功したモデル名も返す。

    Returns:
        (Messageオブジェクト, 使用したモデル名)
    """
    chain = fallback_chain or FALLBACK_CHAIN

    last_error = None
    for model in chain:
        try:
            response = call_with_retry(client, model, messages, system, max_tokens)
            return response, model
        except Exception as e:
            print(f"  [fallback] {model} failed: {e}")
            last_error = e

    raise RuntimeError(f"全モデルが失敗しました: {last_error}")
