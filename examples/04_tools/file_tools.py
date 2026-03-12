"""
ファイル操作ツール（セキュリティパターン）
対応章: tool-system.md

パストラバーサル攻撃を防ぐ安全なファイルアクセスを実装する。

実行:
    python examples/04_tools/file_tools.py
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client import get_client
from src.tools import make_file_tools


def demo_file_agent():
    """ファイル操作ツールを持つエージェントのデモ。"""
    import tempfile

    # 一時ディレクトリを作業ルートとして使用
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = make_file_tools(allowed_root=tmpdir)
        client = get_client()

        # テストファイルを作成
        Path(tmpdir, "hello.txt").write_text("こんにちは、Claude！")

        messages = [{"role": "user", "content": "hello.txt の内容を読んで、その内容を日本語で説明してください。"}]

        print("=== ファイル操作エージェント ===")

        for step in range(1, 5):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=512,
                tools=manager.schemas,
                messages=messages,
            )
            print(f"ステップ{step}: {response.stop_reason}")

            if response.stop_reason == "end_turn":
                print(f"回答: {response.content[0].text}")
                break

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    print(f"  ツール: {block.name}({block.input})")
                    result = manager.execute(block.name, block.input)
                    print(f"  結果: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })
                messages.append({"role": "user", "content": tool_results})


def demo_path_traversal():
    """パストラバーサル攻撃が防がれることを確認する。"""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = make_file_tools(allowed_root=tmpdir)

        print("\n=== セキュリティテスト: パストラバーサル ===")

        # 正常なアクセス
        result = manager.execute("write_file", {"path": "safe.txt", "content": "安全なファイル"})
        print(f"正常な書き込み: {result}")

        # 攻撃的なパス（ルート外へのアクセス試み）
        result = manager.execute("read_file", {"path": "../../etc/passwd"})
        print(f"攻撃パスの結果: {result}")  # エラーが返るはず


if __name__ == "__main__":
    demo_path_traversal()
    demo_file_agent()
