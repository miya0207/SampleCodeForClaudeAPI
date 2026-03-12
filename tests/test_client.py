"""
最小限のテスト（APIキー不要）
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cache import SemanticCache, jaccard_similarity
from src.cost import calculate_cost, MODEL_COSTS
from src.tools import make_file_tools
from src.memory import AgentMemory


def test_jaccard_similarity_identical():
    assert jaccard_similarity("Pythonの型ヒント", "Pythonの型ヒント") == 1.0


def test_jaccard_similarity_different():
    sim = jaccard_similarity("Pythonの型ヒント", "SQLiteの使い方")
    assert sim < 0.5


def test_cache_hit():
    cache = SemanticCache(threshold=0.85)
    cache.set("Pythonの型ヒントとは", "型ヒントはコードの可読性を高めます")
    result = cache.get("Pythonの型ヒントとは")
    assert result == "型ヒントはコードの可読性を高めます"


def test_cache_miss():
    cache = SemanticCache(threshold=0.85)
    cache.set("Pythonの型ヒントとは", "型ヒントの説明")
    result = cache.get("SQLiteとは")
    assert result is None


def test_calculate_cost():
    cost = calculate_cost("claude-haiku-4-5", input_tokens=1000, output_tokens=500)
    assert cost > 0
    assert cost < 0.01  # 1000+500トークンは1セント未満のはず


def test_haiku_cheaper_than_sonnet():
    haiku_cost = calculate_cost("claude-haiku-4-5", 1000, 500)
    sonnet_cost = calculate_cost("claude-sonnet-4-6", 1000, 500)
    assert haiku_cost < sonnet_cost


def test_path_traversal_prevention():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = make_file_tools(allowed_root=tmpdir)
        result = manager.execute("read_file", {"path": "../../etc/passwd"})
        assert "error" in result


def test_memory_basic():
    memory = AgentMemory(maxlen=3)
    memory.add_message("user", "メッセージ1")
    memory.add_message("user", "メッセージ2")
    assert len(list(memory.layers.working)) == 2

    memory.set("name", "太郎")
    assert memory.get("name") == "太郎"
    assert memory.get("nonexistent", "default") == "default"


def test_memory_maxlen():
    memory = AgentMemory(maxlen=3)
    for i in range(5):
        memory.add_message("user", f"メッセージ{i}")
    # maxlen=3なので最大3件
    assert len(list(memory.layers.working)) == 3
