"""
永続メモリ（SQLite + JSON）
対応章: memory-system.md

セッションをまたいで記憶を保持するエージェントの実装例。

実行:
    python examples/05_memory/persistent_memory.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client
from src.memory import AgentMemory, SQLiteMemory


def demo_agent_memory():
    """AgentMemory（JSON永続化）のデモ。"""
    print("=== AgentMemory デモ ===")

    memory = AgentMemory(persist_path="/tmp/demo_memory.json", maxlen=5)

    # 意味記憶に情報を登録
    memory.set("user_name", "田中太郎")
    memory.set("preferred_language", "Python")
    memory.set("experience_years", 3)

    print(f"ユーザー名: {memory.get('user_name')}")
    print(f"言語: {memory.get('preferred_language')}")

    # 手続き記憶のデモ
    memory.record_tool("fetch_trends", success=True)
    memory.record_tool("fetch_trends", success=True)
    memory.record_tool("fetch_trends", success=False)
    print(f"ツール統計: {memory.layers.procedural}")

    # コンテキスト構築
    memory.add_message("user", "Pythonの非同期処理を教えて")
    memory.add_message("assistant", "asyncioを使います")
    memory.add_message("user", "サンプルコードは？")

    context = memory.get_context()
    print(f"\nコンテキスト ({len(context)}件):")
    for msg in context:
        role = msg["role"]
        content = str(msg["content"])[:60]
        print(f"  [{role}] {content}")


def demo_sqlite_memory():
    """SQLiteMemory（キーワード追跡）のデモ。"""
    print("\n=== SQLiteMemory デモ ===")

    mem = SQLiteMemory(db_path="/tmp/demo_keywords.db")

    # キーワードのパフォーマンスを記録
    test_data = [
        ("Python asyncio", 8.5),
        ("Python asyncio", 7.2),
        ("FastAPI入門", 9.1),
        ("SQLite最適化", 6.8),
        ("FastAPI入門", 8.9),
    ]

    for keyword, score in test_data:
        mem.record_keyword(keyword, score)

    top = mem.get_top_keywords(n=3)
    print("上位キーワード:")
    for item in top:
        print(f"  {item['keyword']}: avg={item['avg_score']:.1f}, count={item['use_count']}")


def demo_memory_with_api():
    """メモリ付きエージェントのAPI呼び出しデモ。"""
    print("\n=== メモリ付きエージェント API デモ ===")

    client = get_client()
    memory = AgentMemory(maxlen=6)

    # ユーザー情報を事前に登録
    memory.set("user_skill", "Python中級者")

    def chat(user_input: str) -> str:
        memory.add_message("user", user_input)
        context = memory.get_context()

        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=256,
            system="あなたは親切なPythonチューターです。ユーザーの情報を活用して回答してください。",
            messages=context,
        )
        answer = response.content[0].text
        memory.add_message("assistant", answer)
        return answer

    # 会話のシミュレーション
    q1 = "デコレータを教えてください"
    print(f"質問1: {q1}")
    print(f"回答1: {chat(q1)[:100]}...")

    q2 = "さっきの例で @property はどう使いますか？"
    print(f"\n質問2: {q2}")
    print(f"回答2: {chat(q2)[:100]}...")


if __name__ == "__main__":
    demo_agent_memory()
    demo_sqlite_memory()
    demo_memory_with_api()
