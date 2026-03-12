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

| 項目 | 要件 |
|------|------|
| Python | 3.11 以上 |
| OS | macOS / Linux / Windows (WSL2推奨) |
| Anthropic API キー | 後述の手順で取得 |

---

## Step 1: Anthropic API キーを取得する

### 1-1. アカウント作成

1. [https://console.anthropic.com/](https://console.anthropic.com/) にアクセス
2. 「Sign Up」からアカウントを作成（Googleアカウント連携可）
3. メール認証を完了する

### 1-2. 支払い情報の登録

1. コンソール左メニュー「**Billing**」→「Add payment method」
2. クレジットカードを登録する（プリペイドカードは不可の場合あり）
3. 「**Credits**」タブで残高を確認 — 新規登録時に無料クレジット $5 が付与されることがある

> **コストの目安**: このリポジトリのサンプルを全て実行しても $0.10 未満です。
> `claude-haiku-4-5` を使用するサンプルが多いため非常に低コストです。

### 1-3. API キーの発行

1. コンソール左メニュー「**API Keys**」をクリック
2. 「**Create Key**」ボタンをクリック
3. 名前を入力（例: `sample-code-for-book`）して「Create Key」
4. 表示された `sk-ant-api03-...` の文字列を **今すぐコピーする**

> ⚠️ **重要**: API キーはこの画面でしか全体を確認できません。
> 画面を閉じると二度と表示されないため、必ずコピーしてください。

---

## Step 2: リポジトリのセットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/miya0207/SampleCodeForClaudeAPI
cd SampleCodeForClaudeAPI

# 2. 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# インストール確認
python -c "import anthropic; print('OK:', anthropic.__version__)"
```

---

## Step 3: .env ファイルを設定する

```bash
# .env.example をコピーして .env を作成
cp .env.example .env
```

`.env` をテキストエディタで開き、APIキーを貼り付ける:

```
ANTHROPIC_API_KEY=sk-ant-api03-ここに取得したキーを貼り付ける
```

### 設定の確認

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.environ.get('ANTHROPIC_API_KEY', '')
if key.startswith('sk-ant-'):
    print('✅ APIキーが正しく設定されています')
    print(f'   先頭: {key[:20]}...')
else:
    print('❌ APIキーが設定されていません。.env を確認してください')
"
```

---

## Step 4: 動作確認（最小テスト）

```bash
# APIキー不要のテスト（セキュリティ・キャッシュ・コスト計算の確認）
python -m pytest tests/ -v
```

期待される出力:

```
tests/test_client.py::test_jaccard_similarity_identical PASSED
tests/test_client.py::test_cache_hit PASSED
tests/test_client.py::test_calculate_cost PASSED
tests/test_client.py::test_path_traversal_prevention PASSED
...
9 passed in 0.12s
```

```bash
# API呼び出しの動作確認（APIキー必要・約$0.001）
python examples/01_demo/minimal_agent.py
```

期待される出力例:

```
質問: 東京の今日の天気と気温に合ったランチを提案してください

ステップ 1: stop_reason=tool_use
  → ツール呼び出し: get_weather({'city': '東京'})
  ← 結果: {'temp': 18, 'condition': '晴れ', 'humidity': 55}
ステップ 2: stop_reason=tool_use
  → ツール呼び出し: search_restaurants({'city': '東京', 'weather_condition': '晴れ'})
  ← 結果: {'city': '東京', 'suggestions': ['テラス席のあるカフェ', ...]}
ステップ 3: stop_reason=end_turn

最終回答:
今日の東京は18℃の晴れですので、テラス席のあるカフェがおすすめです...
```

---

## 各 example の実行方法

```bash
# Claude API 基本呼び出し
python examples/02_api/basic_call.py
python examples/02_api/streaming.py
python examples/02_api/tool_use.py

# プロンプトパターン
python examples/03_prompt/zero_shot_cot.py
python examples/03_prompt/structured_output.py

# ツール設計（セキュリティパターン）
python examples/04_tools/file_tools.py

# メモリシステム
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

| ファイル | 役割 |
|---------|------|
| `src/client.py` | Claude API クライアント（リトライ・フォールバック込み） |
| `src/agent.py` | ReAct エージェント基底クラス |
| `src/tools.py` | ToolManager（デコレータ登録・パストラバーサル防止） |
| `src/memory.py` | 4層メモリシステム（CoALA） + SQLite |
| `src/cost.py` | CostTracker（月次予算管理） |
| `src/cache.py` | SemanticCache（TF-IDF類似度） |

---

## セキュリティガイドライン

### .env ファイルの取り扱い

```
✅ やること
  - .env は .gitignore に含める（このリポジトリでは設定済み）
  - APIキーは .env にのみ記述する
  - チームで共有する場合は 1Password / AWS Secrets Manager 等を使う

❌ 絶対にやってはいけないこと
  - .env を git add / git commit しない
  - APIキーをソースコードに直接書かない
  - APIキーを Slack / Discord / GitHub Issues に貼り付けない
  - APIキーを含むファイルをメールで送らない
```

### .gitignore の確認

このリポジトリの `.gitignore` には `.env` が含まれています。

```bash
# .env が追跡されていないことを確認
git status
# → .env が "Changes to be committed" に表示されていなければ OK
```

**万が一 .env を誤ってコミットしてしまった場合の対処:**

```bash
# 【最重要】まずAPIキーを無効化する
# → https://console.anthropic.com/settings/keys でキーを削除

# git の追跡から外す
git rm --cached .env
git commit -m "fix: remove .env from tracking"
git push

# 新しいAPIキーを発行して .env を更新する
```

> ⚠️ `git push --force` で履歴を書き換えても、GitHub のキャッシュや
> フォーク先に残る可能性があります。**キーの無効化が最優先**です。

### 支出上限の設定（推奨）

Anthropic コンソールで月間上限を設定しておくと、バグによるコスト爆発を防げます:

1. [console.anthropic.com](https://console.anthropic.com/) → 「**Billing**」
2. 「**Usage limits**」→「Set a monthly spend limit」
3. 学習用なら月額 **$5〜$10** を設定しておくと安心

---

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `ANTHROPIC_API_KEY が設定されていません` | .env 未作成 / キー未記述 | `cp .env.example .env` して編集 |
| `AuthenticationError` | APIキーが無効 | コンソールで新しいキーを発行 |
| `RateLimitError (429)` | リクエスト過多 | 数秒待ってから再実行 |
| `ModuleNotFoundError: anthropic` | pip 未実行 | `pip install -r requirements.txt` |
| `PermissionError: アクセス禁止` | パストラバーサル防止が動作 | 正常な動作（セキュリティ機能） |
| `ModuleNotFoundError: dotenv` | pip 未実行 | `pip install python-dotenv` |

---

## 注意事項

- **本番利用不可**: 教材用コードです。本番環境に直接デプロイしないでください
- **API コスト**: 全サンプル実行しても $0.10 未満の見込みですが、`09_production/async_pipeline.py` は複数回 API を呼び出すため注意してください
- **レート制限**: 連続実行すると 429 エラーが発生することがあります。エラーが出たら数秒待ってから再実行してください

---

## ライセンス

MIT License — 教材・個人プロジェクト・商用利用いずれも可。
