# SampleCodeForClaudeAPI

書籍「**Pythonで作るClaudeエージェント実践入門**」(Zenn) の教材サンプルコードです。

> 書籍: https://zenn.dev/miya0207/books/python-claude-agent-vol1

---

## このリポジトリの目的

- 書籍の各章で解説するコードを **実際に動かして理解する** ための教材
- 書籍本文の詳細解説を補完する **動く最小実装** を提供
- コピー&改変して自分のプロジェクトに応用するための **スターターコード**

---

## 前提環境

- Python 3.11 以上
- Anthropic API キー（[console.anthropic.com](https://console.anthropic.com/) で取得）

---

## セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/miya0207/SampleCodeForClaudeAPI
cd SampleCodeForClaudeAPI

# 2. 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. .env を設定
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定する
```

---

## .env の設定

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

`.env` ファイルは `.gitignore` に含まれており、**絶対にGitにコミットしないでください**。

---

## 各 example の実行方法

```bash
# 書籍 demo-agent 章（無料公開章）に対応
python examples/01_demo/minimal_agent.py

# Claude API 基本呼び出し
python examples/02_api/basic_call.py
python examples/02_api/streaming.py
python examples/02_api/tool_use.py

# プロンプトパターン
python examples/03_prompt/zero_shot_cot.py
python examples/03_prompt/few_shot.py
python examples/03_prompt/structured_output.py

# ツール設計
python examples/04_tools/file_tools.py
python examples/04_tools/web_tools.py

# メモリシステム
python examples/05_memory/working_memory.py
python examples/05_memory/persistent_memory.py

# 信頼性設計
python examples/06_reliability/retry_fallback.py
python examples/06_reliability/cost_tracker.py

# 評価・テスト
python examples/07_evaluation/property_test.py
python examples/07_evaluation/llm_judge.py

# アーキテクチャパターン
python examples/08_architecture/react_agent.py
python examples/08_architecture/planact_agent.py

# 本番スケール
python examples/09_production/semantic_cache.py
python examples/09_production/async_pipeline.py
```

---

## 書籍との対応

| examples/ | 対応する章 |
|-----------|----------|
| `01_demo/` | demo-agent.md（無料公開） |
| `02_api/` | claude-api.md |
| `03_prompt/` | prompt-engineering.md |
| `04_tools/` | tool-system.md |
| `05_memory/` | memory-system.md |
| `06_reliability/` | reliability.md |
| `07_evaluation/` | evaluation.md |
| `08_architecture/` | agent-architecture.md |
| `09_production/` | production-template.md / bonus-cost.md |

---

## src/ の再利用可能コア

複数の example から共通利用するコアモジュール:

| ファイル | 役割 |
|---------|------|
| `src/client.py` | Claude API クライアント（リトライ込み） |
| `src/agent.py` | ReAct エージェント基底クラス |
| `src/tools.py` | ToolManager（デコレータ登録） |
| `src/memory.py` | 4層メモリシステム |
| `src/cost.py` | CostTracker（月次予算管理） |
| `src/cache.py` | SemanticCache（TF-IDF類似度） |

---

## 注意事項

- **本番利用不可**: このコードは教材用です。本番環境に直接デプロイしないでください
- **API コスト**: 実行にはAnthropicのAPI料金が発生します。`claude-haiku-4-5` は最もコストが低いです
- **レート制限**: 連続実行すると429エラーが発生することがあります。`time.sleep(1)` を挟んでください
- **note.com自動化**: `production-template.md` で紹介するSeleniumを使ったnote.com投稿は、note.comの利用規約を必ず確認の上で行ってください

---

## ライセンス

MIT License — 教材・個人プロジェクト・商用利用いずれも可。
