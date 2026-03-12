"""
4層メモリシステム（CoALAアーキテクチャ）
対応章: memory-system.md
"""
import json
import sqlite3
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class MemoryLayers:
    """4層メモリの状態コンテナ。"""
    # Layer 1: 作業記憶（直近N件のメッセージ）
    working: deque = field(default_factory=lambda: deque(maxlen=10))
    # Layer 2: エピソード記憶（会話の要約テキスト）
    episodes: list[str] = field(default_factory=list)
    # Layer 3: 意味記憶（キーバリューの知識ストア）
    semantic: dict[str, Any] = field(default_factory=dict)
    # Layer 4: 手続き記憶（ツールの成功/失敗統計）
    procedural: dict[str, dict] = field(default_factory=dict)


class AgentMemory:
    """
    4層メモリシステム。

    - working: APIに送るメッセージ履歴（古いものは自動削除）
    - episodes: 圧縮された過去の会話サマリー
    - semantic: ユーザーやドメインに関する知識
    - procedural: ツール使用の成功率追跡
    """

    def __init__(self, persist_path: str = "out/memory.json", maxlen: int = 10):
        self.path = Path(persist_path)
        self.layers = MemoryLayers(working=deque(maxlen=maxlen))
        self._load()

    def add_message(self, role: str, content: str):
        """作業記憶にメッセージを追加する（古いものは自動削除）。"""
        self.layers.working.append({"role": role, "content": content})

    def summarize_working(self, summary: str):
        """
        現在の作業記憶をエピソードとして保存し、作業記憶をクリアする。
        長い会話履歴のコスト削減に使う。
        """
        if summary:
            self.layers.episodes.append(summary)
            if len(self.layers.episodes) > 20:
                self.layers.episodes = self.layers.episodes[-20:]
        self.layers.working.clear()
        self._save()

    def set(self, key: str, value: Any):
        """意味記憶にキーバリューを保存する。"""
        self.layers.semantic[key] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """意味記憶からキーを取得する。"""
        return self.layers.semantic.get(key, default)

    def record_tool(self, tool_name: str, success: bool):
        """手続き記憶にツール実行結果を記録する。"""
        if tool_name not in self.layers.procedural:
            self.layers.procedural[tool_name] = {"success": 0, "failure": 0}
        self.layers.procedural[tool_name]["success" if success else "failure"] += 1

    def get_context(self) -> list[dict]:
        """Claude API に渡すメッセージリストを返す（意味記憶を先頭に挿入）。"""
        messages = list(self.layers.working)

        # 意味記憶の重要情報をコンテキストとして先頭に追加
        hints = []
        if self.layers.episodes:
            hints.append(f"過去の会話要約: {self.layers.episodes[-1]}")
        if self.layers.semantic:
            key_facts = [f"{k}={v}" for k, v in list(self.layers.semantic.items())[:3]]
            hints.append(f"既知情報: {', '.join(key_facts)}")

        if hints and messages:
            context_msg = {"role": "user", "content": " / ".join(hints)}
            messages = [context_msg] + messages

        return messages

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "episodes": self.layers.episodes,
            "semantic": self.layers.semantic,
            "procedural": self.layers.procedural,
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                self.layers.episodes = data.get("episodes", [])
                self.layers.semantic = data.get("semantic", {})
                self.layers.procedural = data.get("procedural", {})
            except json.JSONDecodeError:
                pass  # 壊れたファイルは無視して初期化


class SQLiteMemory:
    """
    SQLite を使った永続メモリ。
    キーワードパフォーマンスの長期追跡に使う。
    """

    def __init__(self, db_path: str = "out/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")  # 並列書き込み対応
            conn.execute("""
                CREATE TABLE IF NOT EXISTS keyword_stats (
                    keyword TEXT PRIMARY KEY,
                    use_count INTEGER DEFAULT 0,
                    avg_score REAL DEFAULT 0.0,
                    last_used TEXT
                )
            """)

    def record_keyword(self, keyword: str, score: float):
        """キーワードの使用を記録する。"""
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO keyword_stats (keyword, use_count, avg_score, last_used)
                VALUES (?, 1, ?, ?)
                ON CONFLICT(keyword) DO UPDATE SET
                    use_count = use_count + 1,
                    avg_score = (avg_score * use_count + ?) / (use_count + 1),
                    last_used = ?
            """, (keyword, score, now, score, now))

    def get_top_keywords(self, n: int = 5) -> list[dict]:
        """スコア上位N件のキーワードを返す。"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT keyword, use_count, avg_score
                FROM keyword_stats
                ORDER BY avg_score DESC
                LIMIT ?
            """, (n,)).fetchall()
        return [{"keyword": r[0], "use_count": r[1], "avg_score": r[2]} for r in rows]
