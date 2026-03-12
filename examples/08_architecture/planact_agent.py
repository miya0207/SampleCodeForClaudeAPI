"""
PlanActエージェント（計画→実行の2フェーズ）
対応章: agent-architecture.md

ReActと異なり、先に計画を立ててからツールを実行する。
複雑なタスクで中間経路のブレを防ぐのに有効。

実行:
    python examples/08_architecture/planact_agent.py
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client
from src.tools import ToolManager
from datetime import datetime


manager = ToolManager()


@manager.register(
    name="get_date",
    description="今日の日付を取得する",
    input_schema={"type": "object", "properties": {}}
)
def get_date() -> dict:
    return {"date": datetime.now().strftime("%Y年%m月%d日")}


@manager.register(
    name="search_info",
    description="キーワードで情報を検索する（デモ用ダミー）",
    input_schema={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "検索キーワード"}
        },
        "required": ["keyword"]
    }
)
def search_info(keyword: str) -> dict:
    # デモ用のダミーデータ
    dummy = {
        "Python": "Python 3.12がリリース。型ヒントとパフォーマンスが改善された。",
        "Claude": "Claude 4系は長文脈処理と推論能力が大幅に向上した。",
    }
    result = next((v for k, v in dummy.items() if k.lower() in keyword.lower()), f"{keyword}の情報はありません")
    return {"keyword": keyword, "result": result}


class PlanActAgent:
    """
    2フェーズエージェント:
    Phase 1 (Plan): タスクを分析して実行計画を立てる
    Phase 2 (Act):  計画に従ってツールを実行する
    """

    def __init__(self, tool_manager: ToolManager, model: str = "claude-haiku-4-5"):
        self.client = get_client()
        self.tool_manager = tool_manager
        self.model = model

    def run(self, task: str) -> str:
        print(f"\n[PlanAct] タスク: {task}")

        # Phase 1: 計画
        plan = self._plan(task)
        print(f"\n[Plan] 計画:\n{plan}")

        # Phase 2: 実行
        result = self._act(task, plan)
        return result

    def _plan(self, task: str) -> str:
        available_tools = [s["name"] for s in self.tool_manager.schemas]
        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": (
                    f"タスク: {task}\n"
                    f"利用可能ツール: {available_tools}\n"
                    "このタスクを解決するためのステップバイステップの計画を箇条書きで作成してください。"
                )
            }]
        )
        return response.content[0].text

    def _act(self, task: str, plan: str) -> str:
        messages = [{
            "role": "user",
            "content": f"タスク: {task}\n\n計画:\n{plan}\n\n上記の計画に従ってタスクを実行してください。"
        }]

        for step in range(1, 6):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                tools=self.tool_manager.schemas,
                messages=messages,
            )
            print(f"[Act] ステップ{step}: {response.stop_reason}")

            if response.stop_reason == "end_turn":
                return response.content[0].text

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    print(f"  ツール: {block.name}({block.input})")
                    result = self.tool_manager.execute(block.name, block.input)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                messages.append({"role": "user", "content": results})

        return "最大ステップ数に達しました"


if __name__ == "__main__":
    agent = PlanActAgent(tool_manager=manager)
    answer = agent.run("今日の日付とPythonの最新情報を調べてまとめてください")
    print(f"\n最終回答:\n{answer}")
