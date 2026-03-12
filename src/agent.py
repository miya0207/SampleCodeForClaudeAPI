"""
ReActエージェント基底クラス
対応章: agent-architecture.md, why-agent.md
"""
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
import anthropic

# src/ を import パスに追加（examples/ から呼ばれた場合に備えて）
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.client import get_client, call_with_retry
from src.tools import ToolManager


@dataclass
class AgentState:
    """エージェント実行状態のスナップショット。"""
    messages: list[dict] = field(default_factory=list)
    iteration_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens


class ReActAgent:
    """
    ReAct（Reasoning + Acting）パターンのエージェント。

    ループ:
      1. Claude に messages を渡す
      2. stop_reason == "tool_use" なら tool を実行して results を messages に追加
      3. stop_reason == "end_turn" なら最終回答を返す
      4. max_iterations に達したら強制終了（無限ループ防止）
    """

    def __init__(
        self,
        tool_manager: ToolManager,
        model: str = "claude-sonnet-4-6",
        system: str = "",
        max_iterations: int = 10,
        max_tokens: int = 4096,
        verbose: bool = True,
    ):
        self.client = get_client()
        self.tool_manager = tool_manager
        self.model = model
        self.system = system
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.verbose = verbose

    def run(self, user_message: str) -> tuple[str, AgentState]:
        """
        ユーザーメッセージを処理して最終回答を返す。

        Returns:
            (最終テキスト回答, AgentState)
        """
        state = AgentState()
        state.messages.append({"role": "user", "content": user_message})

        if self.verbose:
            print(f"\n[agent] 開始: {user_message[:80]}")

        while state.iteration_count < self.max_iterations:
            state.iteration_count += 1

            response = call_with_retry(
                self.client,
                model=self.model,
                messages=state.messages,
                system=self.system,
                max_tokens=self.max_tokens,
            )

            state.total_input_tokens += response.usage.input_tokens
            state.total_output_tokens += response.usage.output_tokens

            if self.verbose:
                print(
                    f"[agent] イテレーション {state.iteration_count}: "
                    f"stop_reason={response.stop_reason}, "
                    f"tokens={response.usage.output_tokens}"
                )

            # 終了条件
            if response.stop_reason == "end_turn":
                state.messages.append({"role": "assistant", "content": response.content})
                final = self._extract_text(response)
                if self.verbose:
                    print(f"[agent] 完了: {state.total_tokens} tokens使用")
                return final, state

            # ツール実行
            if response.stop_reason == "tool_use":
                state.messages.append({"role": "assistant", "content": response.content})
                tool_results = self._execute_tools(response)
                state.messages.append({"role": "user", "content": tool_results})

        # 最大イテレーション到達
        warning = f"[警告] 最大イテレーション({self.max_iterations})に達しました"
        if self.verbose:
            print(warning)
        return warning, state

    def _execute_tools(self, response) -> list[dict]:
        """レスポンス内の全ツール呼び出しを実行してresultsリストを返す。"""
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if self.verbose:
                print(f"  [tool] {block.name}({json.dumps(block.input, ensure_ascii=False)[:60]})")

            result = self.tool_manager.execute(block.name, block.input)

            if self.verbose:
                result_preview = str(result)[:80]
                status = "❌" if "error" in str(result).lower() else "✅"
                print(f"  [tool] {status} → {result_preview}")

            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, ensure_ascii=False),
            })
        return results

    def _extract_text(self, response) -> str:
        """レスポンスのテキストブロックを結合して返す。"""
        texts = []
        for block in response.content:
            if hasattr(block, "text"):
                texts.append(block.text)
        return "\n".join(texts)
