---
name: strands-06-code-generation
description: Strands Agents SDKのAIエージェント開発ワークフローのコード生成フェーズ（06_code-generation）を実行するスキル。「実装タスク計画を作って」「コード生成を始めて」「Pythonコードを生成して」「実装を始めて」「コードを書いて」など、コード生成フェーズの成果物作成・実装に関する指示があれば必ずこのスキルを使用する。AIエージェント開発、Strands、コード生成、Python実装のキーワードが出た場合にも積極的にこのスキルを適用する。
---

# 06_code-generation フェーズ スキル

Strands Agents SDKのAIエージェント開発ワークフローにおけるコード生成フェーズを実行するスキル。
詳細設計に基づいて実装タスク計画を作成し、Pythonコードを生成する。

パスはすべて `skills/` からの相対パスで記載する。

---

## セッション開始時の必須手順

このスキルが呼び出されたら、作業開始前に必ず以下を実行すること。

1. `skills/workflow-state.md` を読み込む
2. `skills/session-context.md` を読み込む
3. **「次アクション待ち状態」欄を最初に確認する**
   - `⏸️ ユーザー指示待ち` の場合 → **作業を一切開始しない**。現在の状態を報告して指示を待つ
   - `▶️ 作業中` の場合 → 次のステップへ進む
4. 「現在のフェーズ」と各成果物の状態を確認する
5. `✅ 完了` の成果物は再作成しない
6. `🔲 未着手` または `🔄 作業中` の成果物のみを作業対象とする

---

## 成果物と参照ファイル一覧

| # | 成果物名 | ID | prompt | template | 出力先 |
|---|---|---|---|---|---|
| 1 | 実装タスク計画 | IG-01 | `prompts/06_code-generation/実装タスク計画.md` | なし | `../artifacts/06_code-generation/outputs/tasks.md` |
| 2 | コード生成実行 | IG-02 | `prompts/06_code-generation/コード生成実行.md` | 下記スケルトン参照 | `../artifacts/06_code-generation/src/` |

### コード生成で使用するスケルトンテンプレート

コード生成（IG-02）では以下のスケルトンファイルを参照してコードを生成する。

| スケルトン | ファイル | 対応コンポーネント |
|---|---|---|
| 01 | `templates/06_code-generation/01_skeleton_data_models.md` | `models/data_models.py` |
| 02 | `templates/06_code-generation/02_skeleton_model_config.md` | `config/model_config.py` |
| 03 | `templates/06_code-generation/03_skeleton_error_handler.md` | `handlers/error_handler.py` |
| 04 | `templates/06_code-generation/04_skeleton_loop_control_hook.md` | `handlers/loop_control_hook.py` |
| 05 | `templates/06_code-generation/05_skeleton_human_approval_hook.md` | `handlers/human_approval_hook.py` |
| 06 | `templates/06_code-generation/06_skeleton_session_manager.md` | `session/session_manager.py` |
| 07 | `templates/06_code-generation/07_skeleton_prompt_orchestrator.md` | `prompt/prompt_orchestrator.py` |
| 08 | `templates/06_code-generation/08_skeleton_prompt_specialist.md` | `prompt/prompt_{specialist}.py` |
| 09 | `templates/06_code-generation/09_skeleton_policies.md` | `agent_knowledge/{domain}_policies.py` |
| 10 | `templates/06_code-generation/10_skeleton_tools.md` | `tools/{domain}_tools.py` |
| 11 | `templates/06_code-generation/11_skeleton_orchestrator_agent.md` | `agents/orchestrator_agent.py` |
| 12 | `templates/06_code-generation/12_skeleton_specialist_agent.md` | `agents/{specialist}_agent.py` |
| 13 | `templates/06_code-generation/13_skeleton_main.md` | `main.py` |
| 14 | `templates/06_code-generation/14_design_data_files.md` | `data/*.json` |

### 依存関係

| 成果物 | 依存する成果物ID |
|---|---|
| IG-01 | BD-02, BD-05, SD-01〜SD-07, DD-01〜DD-03 |
| IG-02 | IG-01 |

---

## プロジェクト標準ディレクトリ構造（R1）

生成コードは以下のディレクトリ構造に配置すること（`../artifacts/06_code-generation/src/` をプロジェクトルートとする）。

```
src/
├── main.py                        # アプリケーションエントリーポイント
├── requirements.txt               # Python依存パッケージ定義
├── pytest.ini                     # テスト設定
├── .env.template                  # 環境変数テンプレート
├── .gitignore                     # Git除外設定
├── config/
│   ├── __init__.py
│   └── model_config.py            # LLMモデル設定
├── models/
│   ├── __init__.py
│   └── data_models.py             # Pydanticモデル定義
├── agents/
│   ├── __init__.py
│   ├── orchestrator_agent.py      # オーケストレーターエージェント
│   └── {specialist}_agent.py     # 専門エージェント（業務ドメインに応じて命名）
├── handlers/
│   ├── __init__.py
│   ├── error_handler.py
│   ├── loop_control_hook.py
│   └── human_approval_hook.py
├── tools/
│   ├── __init__.py
│   ├── {domain}_tools.py
│   └── output_generator.py
├── prompt/
│   ├── __init__.py
│   ├── prompt_orchestrator.py
│   └── prompt_{specialist}.py
├── agent_knowledge/
│   ├── __init__.py
│   └── {domain}_policies.py
├── session/
│   ├── __init__.py
│   └── session_manager.py
├── storage/sessions/              # 実行時生成
├── data/                          # 静的データファイル（JSON）
├── template/                      # 出力テンプレートファイル（Excel等）
├── output/                        # 実行時生成
├── logs/                          # 実行時生成
├── evals/
│   └── eval_{evaluation_name}.py
└── tests/
    ├── unit/
    └── integration/
```

### カスタマイズガイド

- `agents/` 配下の専門エージェントは業務ドメインに応じて追加・命名する
- `tools/` 配下のツールは業務要件に応じて追加する
- `agent_knowledge/` 配下のポリシーファイルは業務ルールごとに追加する
- `data/` 配下のデータファイルは必要なマスタデータに応じて追加する

---

## ファイル配置ルール（R2）

| コンポーネント種別 | 配置先 | ファイル命名規則 | 例 |
|---|---|---|---|
| エージェント定義 | `agents/` | `{機能名}_agent.py` | `orchestrator_agent.py`, `order_agent.py` |
| ツール関数 | `tools/` | `{機能名}_tools.py` または `{機能名}_generator.py` | `search_tools.py`, `report_generator.py` |
| データモデル | `models/` | `{対象}_models.py` | `data_models.py`, `order_models.py` |
| 設定クラス | `config/` | `{対象}_config.py` | `model_config.py` |
| エラー処理・フック | `handlers/` | `{機能名}_handler.py` または `{機能名}_hook.py` | `error_handler.py`, `loop_control_hook.py` |
| システムプロンプト | `prompt/` | `prompt_{エージェント名}.py` | `prompt_orchestrator.py`, `prompt_order.py` |
| ビジネスルール | `agent_knowledge/` | `{対象}_policies.py` | `order_policies.py`, `approval_policies.py` |
| セッション管理 | `session/` | `{機能名}_manager.py` | `session_manager.py` |
| 静的データ | `data/` | `{データ名}.json` | `master_data.json`, `config_data.json` |
| テンプレートファイル | `template/` | `{テンプレート名}.{拡張子}` | `申請書_template.xlsx`, `report_template.xlsx` |
| エントリーポイント | プロジェクトルート | `main.py` | `main.py` |
| パッケージ初期化 | 各ディレクトリ | `__init__.py` | `__init__.py` |

---

## ファイル間の依存関係ルール（R3）

依存の方向は上位層から下位層への一方向とする。同一層間の参照は許可するが、下位層から上位層への参照は禁止する。

### 依存関係の方向

```
[上位層]
  agents/     → tools/, prompt/, handlers/, session/, config/, models/, agent_knowledge/
  main.py     → agents/, handlers/, config/

[中間層]
  tools/      → models/, handlers/
  prompt/     → agent_knowledge/
  session/    → （外部ライブラリのみ: strands.session）

[下位層]
  handlers/   → handlers/（同一層内参照: loop_control_hook → error_handler）
  config/     → （外部ライブラリのみ: strands.models）
  models/     → （標準ライブラリ + pydantic のみ）
  agent_knowledge/ → （依存なし: 純粋なテキスト返却）
```

### 禁止される依存方向

- `models/` → `agents/`, `tools/`, `handlers/` への参照
- `config/` → `agents/`, `tools/` への参照
- `handlers/` → `agents/`, `tools/` への参照
- `tools/` → `agents/` への参照
- `agent_knowledge/` → 他の全モジュールへの参照

---

## データファイルの配置ルール（R4）

| 分類 | 配置先 | 説明 |
|---|---|---|
| 静的マスタデータ | `data/` | アプリケーション動作に必要な参照データ。JSON形式。 |
| テンプレートファイル | `template/` | 出力生成（Excel・PDF等）に使用するテンプレートファイル。ツールから参照する。 |
| サンプルデータ | `sample/` | テスト・デモ用のファイル。本番動作には不要。 |
| セッション永続化データ | `storage/sessions/` | 実行時に自動生成。セッションIDごとのサブディレクトリに格納。 |
| ログファイル | `logs/` | 実行時に自動生成。UTF-8エンコーディング。 |

---

## 出力ファイルの配置ルール（R5）

| 出力種別 | 配置先 | ファイル命名規則 | 例 |
|---|---|---|---|
| 出力ファイル（Excel/PDF等） | `output/` | `{出力種別}_{YYYYMMDD_HHMMSS}.{拡張子}` | `報告書_20260210_143022.xlsx` |
| ログファイル | `logs/` | `error.log` | `error.log` |
| セッションデータ | `storage/sessions/` | `session_{セッションID}/` | `session_20260210_143022_a1b2c3d4/` |

---

## 技術スタック（R6）

| カテゴリ | 技術 | バージョン要件 |
|---|---|---|
| 言語 | Python | 3.10以上 |
| AIエージェントフレームワーク | AWS Strands SDK | strands-agents >= 0.1.0 |
| エージェントツール | AWS Strands Tools | strands-agents-tools >= 0.1.0 |
| LLMプロバイダ | Amazon Bedrock (boto3) | boto3 >= 1.34.0 |
| データバリデーション | Pydantic | pydantic >= 2.0.0 |
| テストフレームワーク | pytest | pytest >= 7.4.0 |
| 環境変数管理 | python-dotenv | python-dotenv >= 1.0.0 |
| 日付処理 | python-dateutil | python-dateutil >= 2.8.2 |
| ロギング | logging（標準ライブラリ） | - |

### 追加パッケージの例（業務要件に応じて選択）

| カテゴリ | 技術 | バージョン要件 | 用途 |
|---|---|---|---|
| Excel生成 | openpyxl | openpyxl >= 3.1.0 | Excel形式の帳票出力 |

---

## 命名規則（R7）

| 対象 | 規則 | 例 |
|---|---|---|
| ファイル名 | snake_case | `search_tools.py`, `error_handler.py` |
| クラス名 | PascalCase | `ErrorHandler`, `OutputGenerator` |
| 関数名 | snake_case | `search_data`, `load_master_data` |
| メソッド名 | snake_case | `generate_session_id`, `get_model` |
| プライベートメソッド | `_`接頭辞 + snake_case | `_get_applicant_info`, `_initialize_user_info` |
| プライベートインスタンス変数 | `_`接頭辞 + snake_case | `self._error_handler`, `self._session_id` |
| モジュールレベルプライベート変数 | `_`接頭辞 + snake_case | `_error_handler`, `_storage_dir` |
| 定数（クラス変数） | UPPER_SNAKE_CASE | `DEFAULT_MODEL_ID`, `COLUMN_WIDTHS` |
| 定数（モジュールレベル） | UPPER_SNAKE_CASE | `ORCHESTRATOR_SYSTEM_PROMPT` |
| エージェントID | snake_case | `orchestrator_agent`, `specialist_a_agent` |
| エージェント表示名 | 日本語 | `受付窓口エージェント`, `{ドメインA}エージェント` |

---

## 言語ポリシー（R8）

| 対象 | 使用言語 | 備考 |
|---|---|---|
| 識別子（変数名、関数名、クラス名） | 英語 | snake_case / PascalCase |
| モジュールdocstring | 日本語 | ファイル先頭の説明 |
| クラスdocstring | 日本語 | クラスの目的と機能説明 |
| メソッド/関数docstring | 日本語 | Args, Returns, Raisesの説明も日本語 |
| インラインコメント | 日本語 | セクション区切りコメント含む |
| ユーザー向けメッセージ（print, input） | 日本語 | ユーザーとのインタラクション |
| ログメッセージ | 日本語 | ErrorHandler経由の全ログ |
| エラーメッセージ（ユーザー向け） | 日本語 | handle_*メソッドの戻り値 |
| システムプロンプト | 日本語 | LLMへの指示テキスト |
| JSONデータファイルのキー | 英語 | `name`, `value`, `type` 等 |

---

## 共通コーディングパターン（R9）

### エラーハンドリング（R9.1）

- **クラス内での保持方法**: `self._error_handler = ErrorHandler()` をコンストラクタで初期化
- **モジュールレベルでの保持方法**: `_error_handler = ErrorHandler()` をモジュール先頭で初期化
- **エラー処理の委譲**: エラー種別ごとの `handle_*` メソッドを呼び出し、戻り値（ユーザー向けメッセージ文字列）を利用する
- **エラーハンドリングの階層**: EventLoopException（`__cause__` で LoopLimitError を判定）→ Exception の順でキャッチする。Strands SDK は Hook 内で発生した例外を EventLoopException でラップして伝搬するため、LoopLimitError を直接 catch するのではなく EventLoopException の `__cause__` を確認する
- **ツール関数のエラー返却**: 辞書形式で `{"success": False, "message": エラーメッセージ}` を返す。例外を再送出しない
- **ドメイン固有のエラーハンドラ**: 業務要件に応じて `handle_{domain}_error()` メソッドを `ErrorHandler` に追加する

### ログ出力（R9.2）

全てのログ出力は `ErrorHandler` クラスのログメソッド経由で行う。直接 `logging` モジュールを呼び出さない。

- **ログレベルの使い分け**:
  - `log_debug`: 開発時のデバッグ情報
  - `log_info`: 正常処理の記録（処理開始、処理完了、データ読み込み成功等）
  - `log_warning`: 注意が必要な状態（ループ制限到達等）
  - `log_error`: エラー発生（`error_type` パラメータでエラー種別を分類）
  - `log_critical`: システム継続不能な重大エラー
- **コンテキスト辞書の付与**: ログメソッドにはオプションの `context` 辞書を渡し、構造化された追加情報を記録する
- **スタックトレース出力**: `exc_info=True` パラメータで制御。バリデーションエラー、データ読み込みエラー、予期しないエラーでは有効にする

### バリデーション（R9.3）

外部から受け取るデータは全てPydanticモデルでバリデーションを行う。

- **バリデーション実行タイミング**: ツール関数の入口、エージェント呼び出し時の`invocation_state`受取時
- **共通バリデータ関数**: 複数モデルで共有するバリデータを関数として定義し、`field_validator` で各モデルに適用する
- **バリデーションエラー処理**: `ValidationError` をキャッチし、`ErrorHandler.handle_validation_error()` に委譲
- **バリデーション済みデータの利用**: バリデーション後はPydanticモデルのインスタンス属性またはmodel_dump()を通じてデータにアクセスする

#### モデルカテゴリと用途（R9.3.1）

| カテゴリ | 用途 | 定義元 | 利用先 |
|---|---|---|---|
| マスタデータモデル | `data/`配下のJSONファイルの型保証 | JSONデータ構造に対応 | `tools/{domain}_tools.py` |
| ツール入力モデル | ツール関数の入力パラメータの型保証 | ツール関数の引数に対応 | `tools/{domain}_tools.py` |
| エージェント状態モデル | `invocation_state`の型保証 | エージェント間の状態受け渡し | `agents/`, `tools/` |
| 出力生成モデル | 出力ファイル生成時のデータ型保証 | 出力内容の構造に対応 | `tools/output_generator.py` |

#### Field定義パターン（R9.3.2）

| パターン | 用途 | 例 |
|---|---|---|
| `Field(..., description="説明")` | 必須フィールド | `name: str = Field(..., description="名称")` |
| `Field(None, description="説明")` | 任意フィールド（デフォルトNone） | `notes: Optional[str] = Field(None, description="備考")` |
| `Field(..., min_length=1)` | 空文字禁止 | `name: str = Field(..., min_length=1, description="名称")` |
| `Field(..., gt=0)` | 正の数値のみ | `amount: float = Field(..., gt=0, description="金額")` |
| `Field(..., ge=0)` | 0以上の数値 | `cost: float = Field(..., ge=0, description="費用")` |
| `Literal[...]` | 許可値の列挙 | `category: Literal["A", "B", "C"]` |

#### バリデーターの適用パターン（R9.3.3）

| パターン | 用途 | 例 |
|---|---|---|
| 共通バリデーター関数の適用 | 複数モデルで共有するバリデーション | `_validate_xxx = field_validator("field_name")(validate_xxx)` |
| クラスメソッドバリデーター | モデル固有のバリデーション | `@field_validator("items")` + `@classmethod` |

#### バリデーション実行タイミング（R9.3.4）

| タイミング | 実行箇所 |
|---|---|
| ツール関数の入口 | `tools/{domain}_tools.py` |
| invocation_state受取時 | `agents/orchestrator_agent.py` |
| invocation_stateの再バリデーション | `tools/output_generator.py` |
| マスタデータ読み込み時 | `tools/{domain}_tools.py` |

### @tool デコレータの使い分け（R9.4）

| デコレータ | 使用条件 | 例 |
|---|---|---|
| `@tool` | `invocation_state` やツールコンテキストを参照しないツール | `search_data`, `calculate_value` |
| `@tool(context=True)` | `invocation_state` を参照する、または `ToolContext` が必要なツール | `specialist_a_agent`, `output_generator` |

- `@tool(context=True)` を使用する場合、関数の最後の引数に `tool_context: ToolContext` を追加する
- デコレータは関数シグネチャの直前に配置する

### Agent()コンストラクタ共通パラメータ（R9.5）

```python
from strands import Agent, ModelRetryStrategy
from strands.agent.conversation_manager import SlidingWindowConversationManager

agent = Agent(
    # ---- 必須パラメータ ----
    model=ModelConfig.get_model(),
    system_prompt=SYSTEM_PROMPT,       # str: システムプロンプト（prompt/モジュールから取得）
    tools=[tool_a, tool_b],            # List: エージェントが利用するツール関数のリスト

    # ---- エージェント識別パラメータ ----
    agent_id="agent_id_snake_case",    # str: エージェントの一意識別子（snake_case）
    name="エージェント表示名",            # str: エージェントの日本語表示名
    description="エージェントの役割説明",  # str: エージェントの役割を簡潔に説明

    # ---- 会話管理パラメータ ----
    conversation_manager=SlidingWindowConversationManager(
        window_size=20,                # int: 保持するメッセージ数（下記サイズ目安表参照）
        should_truncate_results=True,  # bool: ウィンドウ超過時に結果を切り詰め（全エージェント共通: True）
        per_turn=False                 # bool: メッセージ単位でカウント（全エージェント共通: False）
    ),

    # ---- ストリーミング制御 ----
    callback_handler=None,             # None: ストリーミング出力を無効化（全エージェント共通）

    # ---- リトライ戦略 ----
    retry_strategy=ModelRetryStrategy(
        max_attempts=6,                # int: モデル呼び出しの最大リトライ回数（全エージェント共通: 6）
        initial_delay=4,               # int: 指数バックオフの初期遅延秒数（全エージェント共通: 4）
        max_delay=240                  # int: 指数バックオフの最大遅延秒数（全エージェント共通: 240）
    ),

    # ---- セッション管理 ----
    session_manager=session_manager,   # FileSessionManager: SessionManagerFactoryで作成

    # ---- フック ----
    hooks=[loop_control_hook]          # List[HookProvider]: 下記フック構成表参照
)
```

#### ModelConfig.get_model() の内部パラメータ（R9.5.2）

`config/model_config.py` の `ModelConfig.get_model()` が返す `BedrockModel` の構成：

```python
BedrockModel(
    model_id=cls.DEFAULT_MODEL_ID,       # str: LLMモデルID（R10参照）
    guardrail_id=cls.GUARDRAIL_ID,       # str: ガードレールID（R10参照）
    guardrail_version=cls.GUARDRAIL_VERSION,  # str: ガードレールバージョン
    guardrail_trace="enabled"            # str: ガードレールトレース（全エージェント共通: "enabled"）
)
```

#### ウィンドウサイズの目安（R9.5.3）

| エージェント種別 | window_size | 理由 |
|---|---|---|
| オーケストレーター | 30（大） | 複数の専門エージェントとのやり取りを保持する必要があるため |
| 専門エージェント（複雑な処理） | 20（中） | 複数ステップの情報収集・処理を行うため |
| 専門エージェント（単純な処理） | 15（小） | 特定タスクに集中した短い対話のため |

#### フック構成（R9.5.4）

| エージェント種別 | hooks | 理由 |
|---|---|---|
| オーケストレーター | `[LoopControlHook]` | ループ制御のみ（出力生成は専門エージェントが担当） |
| 専門エージェント（出力生成あり） | `[HumanApprovalHook, LoopControlHook]` | 出力前の人間承認 + ループ制御 |
| 専門エージェント（出力生成なし） | `[LoopControlHook]` | ループ制御のみ |

#### エージェント種別ごとのパラメータ差分（R9.5.5）

| パラメータ | オーケストレーター | 専門エージェント |
|---|---|---|
| `system_prompt` | 定数（`ORCHESTRATOR_SYSTEM_PROMPT`） | 定数または動的生成関数 |
| `tools` | 専門エージェントのツール関数 | ドメイン固有ツール + 出力生成ツール |
| `agent_id` | `"orchestrator_agent"` | `"{specialist_name}_agent"` |
| `name` | `"受付窓口エージェント"` 等 | `"{ドメイン}エージェント"` 等 |
| `window_size` | 30 | 15〜20 |
| `hooks` | `[LoopControlHook]` | `[HumanApprovalHook, LoopControlHook]` |
| `session_manager` | `self._session_manager`（インスタンス変数） | ファクトリ関数内で都度作成 |

### invocation_stateとagent()呼び出しパターン（R9.6）

#### invocation_stateとは（R9.6.1）

`invocation_state` は `ToolContext` を通じてアクセスできる辞書で、エージェント呼び出し時に渡されたコンテキスト情報を保持する。

- **LLMのプロンプトには含まれない**（コンテキストウィンドウを消費しない）
- **ツール関数の内部でのみ参照できる**（`@tool(context=True)` + `tool_context.invocation_state`）
- **リクエスト単位で有効**（セッションをまたがない）
- 機密情報やシステム内部情報の受け渡しに適している

#### データの受け渡しアプローチの使い分け（R9.6.2）

| アプローチ | 用途 | 例 |
|---|---|---|
| ツールパラメータ | LLMが推論・判断して渡すデータ | 検索クエリ、ファイルパス、ユーザーの回答 |
| `invocation_state` | プロンプトに含めたくないが動作に影響するコンテキスト | ユーザーID、セッションID、申請日 |
| クラスベースツール | リクエスト間で変わらない設定 | APIキー、DB接続文字列 |

#### ツール関数内でのinvocation_stateの参照（R9.6.3）

```python
from strands import tool, ToolContext

@tool(context=True)
def output_generator(data: list, tool_context: ToolContext) -> dict:
    """出力ファイルを生成する。

    Args:
        data: 出力データのリスト
    """
    user_name = tool_context.invocation_state.get("user_name")
    request_date = tool_context.invocation_state.get("request_date")
```

| 参照方法 | 説明 |
|---|---|
| `tool_context.invocation_state` | 辞書全体を取得 |
| `tool_context.invocation_state.get("key")` | 安全にキーを取得（存在しない場合は `None`） |
| `tool_context.invocation_state["key"]` | キーを取得（存在しない場合は `KeyError`） |

#### オーケストレーターからのエージェント呼び出し（R9.6.4）

```python
invocation_state = InvocationState(
    user_name=self._user_name,
    request_date=datetime.now().strftime("%Y-%m-%d"),
    session_id=self._session_id
)

response = self.agent(
    user_input,
    invocation_state=invocation_state.model_dump()
)
```

| パラメータ | 型 | 説明 |
|---|---|---|
| 第1引数（位置引数） | `str` | ユーザーからの入力テキスト |
| `invocation_state` | `dict` | エージェント間で共有する状態データ。Pydanticモデルの `model_dump()` で辞書化して渡す |

#### 専門エージェント（Agent as Tool）からのエージェント呼び出し（R9.6.5）

```python
state = tool_context.invocation_state
agent = _get_specialist_a_agent(session_id=state["session_id"])

child_invocation_state = {
    "user_name": state["user_name"],
    "request_date": state["request_date"]
}

response = agent(
    query,
    invocation_state=child_invocation_state
)
```

#### invocation_stateの伝播ルール（R9.6.6）

| 段階 | 伝播の流れ | 渡すフィールド | 説明 |
|---|---|---|---|
| ① | オーケストレーター → オーケストレーターagent() | 全フィールド（`model_dump()`） | Pydanticモデルを辞書化して渡す |
| ② | 専門エージェントツール関数 → 子agent() | 業務に必要なフィールドのみ | `session_id`はファクトリ関数で消費済みのため除外 |
| ③ | 専門エージェント内のツール | `tool_context.invocation_state`で参照 | `@tool(context=True)`のツールのみアクセス可能 |

### Agent as Toolsパターン（R9.7）

専門エージェントはオーケストレーターからツールとして呼び出される。

- **ファクトリ関数**: `_get_{エージェント名}_agent(session_id)` という命名の関数でエージェントインスタンスを生成する
- **ツール関数化**: `@tool(context=True)` でデコレートした関数内でファクトリ関数を呼び出し、エージェントを実行する
- **invocation_stateの伝播**: R9.6.6の伝播ルールに従い、`tool_context.invocation_state` から必要な情報のみを子エージェントに伝播する
- **エラーハンドリング**: EventLoopException（`__cause__` で LoopLimitError を判定）→ Exception の2層構造でキャッチし、ErrorHandlerの対応メソッドに委譲。戻り値は文字列（エラーメッセージ）

```python
from strands.types.exceptions import EventLoopException

@tool(context=True)
def specialist_a_agent(query: str, tool_context: ToolContext) -> str:
    """専門エージェントAツール"""
    _error_handler = ErrorHandler()
    _error_handler.log_info("[specialist_a_agent] ツールが呼び出されました")

    try:
        state = tool_context.invocation_state
        agent = _get_specialist_a_agent(session_id=state["session_id"])
        child_state = {
            "user_name": state["user_name"],
            "request_date": state["request_date"]
        }
        response = agent(query, invocation_state=child_state)
        return str(response)

    except EventLoopException as e:
        if isinstance(e.__cause__, LoopLimitError):
            return _error_handler.handle_loop_limit_error(e.__cause__, context={"agent": "specialist_a_agent", "query": query[:100]})
        return _error_handler.handle_unexpected_error(e, agent_name="specialist_a_agent", context={"query": query[:100]})
    except Exception as e:
        return _error_handler.handle_unexpected_error(e, agent_name="specialist_a_agent", context={"query": query[:100]})
```

### HookProvider実装（R9.8）

#### 利用可能なイベントクラス（R9.8.1）

```python
from strands.hooks import (
    BeforeInvocationEvent,   # エージェント呼び出し開始前
    AfterInvocationEvent,    # エージェント呼び出し完了後
    BeforeModelCallEvent,    # LLMモデル呼び出し前
    AfterModelCallEvent,     # LLMモデル呼び出し後
    BeforeToolCallEvent,     # ツール実行前
    AfterToolCallEvent,      # ツール実行後
)
```

#### register_hooksの実装（R9.8.2）

フックの登録には `registry.add_callback()` を使用する（`add_hook()` は存在しない）。

```python
def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
    registry.add_callback(BeforeToolCallEvent, self._handle_before_tool_call)
    registry.add_callback(AfterToolCallEvent, self._handle_after_tool_call)
```

#### BeforeToolCallEventの属性（R9.8.3）

`BeforeToolCallEvent` はツール実行前に発火する。全ツール呼び出しで発火するため、ハンドラー内で対象ツールを必ずフィルタリングすること。

```python
@dataclass
class BeforeToolCallEvent:
    selected_tool: AgentTool | None  # 実行されるツールオブジェクト（ツール検索失敗時はNone）
    tool_use: ToolUse                # ツール呼び出しパラメータ（TypedDict）
    invocation_state: dict           # エージェント呼び出し時のinvocation_state
    cancel_tool: bool | str          # キャンセル制御（デフォルト: False）
```

`ToolUse` の構造（TypedDict）：

```python
class ToolUse(TypedDict):
    name: str        # ツール名
    input: Any       # ツールへの入力パラメータ（dict）
    toolUseId: str   # ツール呼び出しの一意ID
```

アクセス方法とフィルタリング例：

```python
def _handle_before_tool_call(self, event: BeforeToolCallEvent) -> None:
    tool_name = event.tool_use["name"]
    tool_input = event.tool_use["input"] or {}
    tool_use_id = event.tool_use["toolUseId"]

    # 対象ツール以外はスキップ（全ツール呼び出しで発火するため必須）
    if tool_name not in self.target_tools:
        return
```

#### ツール呼び出しのキャンセル方法（R9.8.4）

`event.cancel()` は存在しない。`event.cancel_tool` にメッセージ文字列を設定してキャンセルする。

```python
# キャンセル: cancel_toolにメッセージを設定する
event.cancel_tool = "ユーザーによりキャンセルされました。"

# Trueを設定するとStrands標準のキャンセルメッセージが使用される
event.cancel_tool = True
```

#### AfterToolCallEventの属性（R9.8.5）

```python
@dataclass
class AfterToolCallEvent:
    selected_tool: AgentTool | None  # 実行されたツールオブジェクト
    tool_use: ToolUse                # ツール呼び出しパラメータ
    invocation_state: dict           # エージェント呼び出し時のinvocation_state
    result: ToolResult               # ツール実行結果
    exception: Exception | None      # 例外（正常時はNone）
    cancel_message: str | None       # キャンセルメッセージ（キャンセル時のみ）
```

### ツール関数のdocstringとtool spec（R9.9）

#### tool spec自動生成の制約（R9.9.1）

Strandsの `@tool` デコレータは関数シグネチャとdocstringからtool spec（JSON Schema）を自動生成し、LLMに渡す。LLMはこのtool specを手がかりにツール呼び出しのパラメータを構築する。

ただし、`list` 等の構造型パラメータは内部構造（要素のプロパティ）がtool specに反映されず空になる。LLMがフィールド名を正しく認識できるよう、docstringの `Args:` セクションに要素構造を明記すること。

#### 構造型パラメータの記述ルール（R9.9.2）

`list` や `dict` など内部に構造を持つパラメータは、要素のフィールド名・型・必須/任意をdocstringに展開して記述する。フィールド名はPydanticモデルの定義と完全一致させること。

```python
@tool(context=True)
def generate_output(records: list, tool_context: ToolContext) -> dict:
    """出力ファイルを生成する。

    Args:
        records: データのリスト。各要素は以下のフィールドを持つ辞書:
            - field_a (str): 説明【必須】
            - field_b (int): 説明【必須】
            - field_c (str|null): 説明【任意、省略可】
        tool_context: ツールコンテキスト（invocation_stateを含む）
    """
```

---

## 共通設定値（R10）

| 設定項目 | 値 | 適用対象 | 備考 |
|---|---|---|---|
| LLMモデルID | `{geography}.{provider}.{model-id}:{version}` | 全エージェント | jp.anthropic.claude-sonnet-4-5-20250929-v1:0 |
| ガードレールID | `{guardrail_id}` | 全エージェント | コンテンツポリシー制御用（任意） |
| ガードレールバージョン | `DRAFT` | 全エージェント | ドラフトまたは公開バージョン |
| ガードレールトレース | `enabled` | 全エージェント | トレース有効 |
| 最大ループ回数 | `10` | 全エージェント | ReActループの上限 |
| リトライ最大試行回数 | `6` | 全エージェント | モデル呼び出しのリトライ回数 |
| リトライ初期遅延 | `4`秒 | 全エージェント | 指数バックオフの初期値 |
| リトライ最大遅延 | `240`秒 | 全エージェント | 指数バックオフの上限 |
| ストリーミング | 無効（`callback_handler=None`） | 全エージェント | エンドユーザー向けアプリのため |
| 会話履歴の切り詰め | `should_truncate_results=True` | 全エージェント | ウィンドウ超過時に結果を切り詰め |
| 会話履歴のターン単位 | `per_turn=False` | 全エージェント | メッセージ単位でカウント |
| ログフォーマット | `%(asctime)s [%(levelname)s] %(name)s - %(message)s` | main.py | 全ログ出力に適用 |
| ログファイルエンコーディング | `utf-8` | main.py | 日本語対応 |
| ログファイルパス | `logs/error.log` | main.py | エラーログ出力先 |
| Strandsイベントループログレベル | `CRITICAL` | main.py | スタックトレースを抑制 |
| 警告メッセージ | 非表示 (`warnings.filterwarnings("ignore")`) | main.py | エンドユーザー向け |
| Excel出力先 | `output/` | 出力生成ツール | 実行時自動作成 |
| セッション保存先 | `storage/sessions/` | セッション管理 | プロジェクトルートからの相対パス |

### カスタマイズガイド

- LLMモデルIDはリージョンとモデルファミリーに応じて変更する
- ガードレールIDはAmazon Bedrockで作成したガードレールに応じて設定する
- 業務要件に応じて固有の設定値（期間制限、金額閾値等）を追加する

---

## 環境変数の規約（R10）

### `.env.template` の定義（R10.1）

プロジェクトルートに `.env.template` を配置し、アプリケーション動作に必要な環境変数の一覧を定義する。
`.env` ファイルは `.env.template` をコピーして作成し、実際の値を設定する。

### 必須環境変数（R10.2）

| 環境変数名 | 用途 |
|---|---|
| `LOG_LEVEL` | ログ出力レベル（DEBUG / INFO / WARNING / ERROR / CRITICAL） |
| `AWS_ACCESS_KEY_ID` | AWS認証用アクセスキーID |
| `AWS_SECRET_ACCESS_KEY` | AWS認証用シークレットアクセスキー |
| `AWS_DEFAULT_REGION` | AWSデフォルトリージョン（例: `ap-northeast-1`） |
| `GUARDRAIL_ID` | Amazon Bedrockガードレールの識別子 |
| `GUARDRAIL_VERSION` | Amazon Bedrockガードレールのバージョン（例: `DRAFT`） |

### `.env` ファイルの作成手順（R10.3）

1. `.env.template` をコピーして `.env` ファイルを作成する
2. `.env` ファイルを開き、利用者独自の設定値（AWS認証情報・ガードレールID等）を入力する

### 運用ルール（R10.4）

- `.env` ファイルは `.gitignore` に登録し、リポジトリにコミットしない
- `.env.template` は値を空欄またはデフォルト値のみ記載し、秘密情報を含めない
- アプリケーション起動時に `python-dotenv` の `load_dotenv()` で `.env` ファイルを読み込む
- 環境変数の参照は `os.getenv("変数名", "デフォルト値")` で行う

---

## 基本方針

### 0. 不明点は必ずユーザーに確認すること
- 指示が不明確・曖昧な場合は、推測や補完を行わず、必ずユーザーに確認してから作業を開始する

### 1. 失敗時はユーザーに報告して停止すること
- 処理が失敗した場合は、即座に作業を停止する
- 自動リトライや続行は行わず、必ずユーザーの指示を待つ

### 2. 出力ルール
- すべてのコメント・docstring は日本語で記述する
- 識別子（変数名・関数名・クラス名）は英語（R7準拠）
- 実装対象外の未定義項目を推測・補完してはならない
- 詳細設計と命名・構成・責務分割を一致させること

### 3. フェーズ完了の宣言
- コード生成が完了したら以下を提示して待機する

```
✅ 06_code-generation が完了しました。
次の実装・テスト作業へ引き継ぐ情報が完備しています。
```

---

## 成果物作成手順

### Step 1: 前フェーズ成果物の確認

`../artifacts/05_detailed-design/outputs/` 配下の全成果物が揃っていることを確認する。
不足がある場合はユーザーに報告して停止する。

### Step 2: workflow-state.md を「作業中」に更新

成果物の作成開始直前に、該当行を `🔲 未着手` → `🔄 作業中` に変更する。

### Step 3: prompt の読み込み

対象成果物の **prompt ファイル** を読み込む。
- コード生成（IG-02）の場合は、生成対象コンポーネントに対応するスケルトンテンプレートを1ファイルずつ読み込む
- フェーズ開始時に全スケルトンを一括読み込みしてはならない

### Step 4: 実装タスク計画（IG-01）

`prompts/06_code-generation/実装タスク計画.md` の指示に従い、
詳細設計・基本設計・システム設計の成果物をもとに `../artifacts/06_code-generation/outputs/tasks.md` を作成する。

tasks.md の内容：
- 実装対象コンポーネントの一覧と実装順序
- 各コンポーネントの実装概要
- 依存関係（どのコンポーネントを先に実装するか）

### Step 5: コード生成実行（IG-02）

`prompts/06_code-generation/コード生成実行.md` の指示に従い、tasks.md の計画順にコードを生成する。

各コンポーネントの生成手順：
1. 対応するスケルトンテンプレートを読み込む
2. 詳細設計書の内容をスケルトンに当てはめてコードを生成する
3. 上記「プロジェクト標準ディレクトリ構造（R1）」に従ってファイルを配置する
4. 「命名規則（R7・R8）」・「共通コーディングパターン（R9）」に準拠していることを確認する

### Step 6: workflow-state.md を「完了」に更新

コード生成が完了したら、該当行を `🔄 作業中` → `✅ 完了` に変更する。

---

## フェーズ完了時の品質チェック

- 生成コードが詳細設計と整合していること
- 命名・構成・責務分割が設計と一致していること
- 実装対象外の未定義項目を推測補完していないこと
- ディレクトリ構造が R1 に準拠していること
- 次の実装・テスト作業へ引き継げる情報が完備していること

合格後、workflow-state.md を以下のように更新する。
- 「品質チェック」列を `✅ 合格` に変更
- 「次アクション待ち状態」を `⏸️ ユーザー指示待ち` に変更

---

## テスト規約（R11）

生成コードに合わせてテストコードも作成する場合の規約：

| 項目 | ルール |
|---|---|
| テストディレクトリ | `tests/unit/`（単体）、`tests/integration/`（結合） |
| テストファイル命名 | `test_{対象モジュール名}.py` |
| テストクラス命名 | `Test{対象クラス名}` |
| テスト関数命名 | `test_{テスト内容}` |

単体テストの観点は、対応する詳細設計書の「テスト観点」セクションを参照する。

### 結合テスト（R11.2）

複数モジュールを組み合わせた連携動作を検証するテストファイルを作成する。
モジュールの依存関係はR3（ファイル間の依存関係ルール）を参照する。

---

## セッション終了時の必須手順（Record Design Decisions）

作業が終了・中断する際（エージェント停止前）に、次セッションへの引き継ぎ情報を
`skills/session-context.md` に上書き更新すること。

記録する内容：
1. 作業中だったタスク・フェーズ（中断した場合は途中状態も含む）
2. このセッションで確定した重要な決定事項（ユーザーが明示的に採用/却下/修正/指示したもの）
3. このセッションで指示されたが、まだ実行されていない未完了の指示

フォーマット：

```markdown
# セッションコンテキスト

## 最終保存日時
YYYY-MM-DD

## 作業中の内容
[フェーズ名・成果物名・進捗状況を簡潔に。作業がなければ「なし」]

## 確定した決定事項
[箇条書きで。なければ「なし」]

## 未完了の指示
[このセッションで指示されたが、まだ実行されていないもの。なければ「なし」]
```

注意：
- 議論中・提案段階のものは記録しない
- 完了済みの指示は記録しない
- ユーザーへのメッセージ出力は不要
