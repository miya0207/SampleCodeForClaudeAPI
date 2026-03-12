"""
ToolManager — デコレータベースのツール登録・実行
対応章: tool-system.md
"""
import functools
import json
from pathlib import Path
from typing import Any, Callable


class ToolNotFoundError(Exception):
    pass


class ToolManager:
    """
    ツールを登録・実行するマネージャー。

    使い方:
        manager = ToolManager()

        @manager.register(
            name="get_time",
            description="現在時刻を返す",
            input_schema={"type": "object", "properties": {}}
        )
        def get_time() -> dict:
            from datetime import datetime
            return {"time": datetime.now().isoformat()}
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._schemas: list[dict] = []

    def register(self, name: str, description: str, input_schema: dict):
        """ツール登録デコレータ。"""
        def decorator(fn: Callable) -> Callable:
            self._tools[name] = fn
            self._schemas.append({
                "name": name,
                "description": description,
                "input_schema": input_schema,
            })
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    @property
    def schemas(self) -> list[dict]:
        """Claude APIに渡すツールスキーマ一覧。"""
        return self._schemas

    def execute(self, name: str, inputs: dict) -> Any:
        """
        ツールを実行する。エラーはJSONで返す（例外を伝播しない）。

        エージェントループでtool_resultとして返す場合、
        例外を投げるとループが壊れるためJSONエラーを返す設計にする。
        """
        if name not in self._tools:
            return {"error": f"ツールが見つかりません: {name}", "available": list(self._tools)}
        try:
            return self._tools[name](**inputs)
        except TypeError as e:
            return {"error": f"引数エラー: {e}", "tool": name}
        except Exception as e:
            return {"error": str(e), "tool": name}

    def list_tools(self) -> list[str]:
        """登録済みツール名の一覧。"""
        return list(self._tools.keys())


# ---- ファイル操作ツール（セキュリティ: パストラバーサル防止）----

ALLOWED_ROOT = Path(".").resolve()


def _safe_path(relative_path: str) -> Path:
    """
    相対パスを安全な絶対パスに変換する。
    ALLOWED_ROOT 外へのアクセスを防ぐ。
    """
    resolved = (ALLOWED_ROOT / relative_path).resolve()
    if not str(resolved).startswith(str(ALLOWED_ROOT)):
        raise PermissionError(f"アクセス禁止: {relative_path} はルート外を指しています")
    return resolved


def make_file_tools(allowed_root: str = ".") -> ToolManager:
    """ファイル操作ツールを持つ ToolManager を返す。"""
    global ALLOWED_ROOT
    ALLOWED_ROOT = Path(allowed_root).resolve()

    manager = ToolManager()

    @manager.register(
        name="read_file",
        description="テキストファイルの内容を読む",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相対ファイルパス"}
            },
            "required": ["path"]
        }
    )
    def read_file(path: str) -> dict:
        safe = _safe_path(path)
        if not safe.exists():
            return {"error": f"ファイルが存在しません: {path}"}
        return {"content": safe.read_text(encoding="utf-8"), "path": str(path)}

    @manager.register(
        name="write_file",
        description="テキストファイルに内容を書き込む",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相対ファイルパス"},
                "content": {"type": "string", "description": "書き込む内容"}
            },
            "required": ["path", "content"]
        }
    )
    def write_file(path: str, content: str) -> dict:
        safe = _safe_path(path)
        safe.parent.mkdir(parents=True, exist_ok=True)
        safe.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(path), "bytes": len(content)}

    @manager.register(
        name="list_files",
        description="ディレクトリ内のファイル一覧を返す",
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "相対ディレクトリパス", "default": "."}
            }
        }
    )
    def list_files(path: str = ".") -> dict:
        safe = _safe_path(path)
        if not safe.is_dir():
            return {"error": f"ディレクトリではありません: {path}"}
        files = [str(p.relative_to(ALLOWED_ROOT)) for p in safe.iterdir()]
        return {"files": sorted(files), "count": len(files)}

    return manager
