"""
ReActエージェント（src/agent.py の利用例）
対応章: agent-architecture.md

実行:
    python examples/08_architecture/react_agent.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agent import ReActAgent
from src.tools import ToolManager


# ---- ツール定義 ----

manager = ToolManager()


@manager.register(
    name="get_date",
    description="今日の日付を返す",
    input_schema={"type": "object", "properties": {}}
)
def get_date() -> dict:
    return {"date": datetime.now().strftime("%Y年%m月%d日"), "weekday": datetime.now().strftime("%A")}


@manager.register(
    name="calculate",
    description="簡単な四則演算を行う",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
            "op": {"type": "string", "enum": ["+", "-", "*", "/"]},
        },
        "required": ["a", "b", "op"]
    }
)
def calculate(a: float, b: float, op: str) -> dict:
    ops = {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b != 0 else None}
    result = ops.get(op)
    return {"result": result, "expression": f"{a} {op} {b}"}


# ---- エージェント実行 ----

if __name__ == "__main__":
    agent = ReActAgent(
        tool_manager=manager,
        model="claude-haiku-4-5",
        system="あなたは数学と日付に関する質問に答えるアシスタントです。",
        max_iterations=5,
        verbose=True,
    )

    questions = [
        "今日は何日ですか？",
        "123 * 456 の答えと、今日の日付を教えてください",
    ]

    for question in questions:
        print(f"\n{'='*50}")
        answer, state = agent.run(question)
        print(f"\n最終回答: {answer}")
        print(f"イテレーション数: {state.iteration_count}")
        print(f"トークン使用量: {state.total_tokens}")
