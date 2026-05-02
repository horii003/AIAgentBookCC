---
inclusion: fileMatch
fileMatchPattern: ".kiro/artifact-workflow/prompts/06_code-generation/**"
---

# プロジェクト共通規約

## R6. 技術スタック

| カテゴリ | 技術 | バージョン要件 |
|:---|:---|:---|
| 言語 | Python | 3.10以上（型ヒント・match文対応） |
| AIエージェントフレームワーク | AWS Strands SDK | strands-agents >= 0.1.0 |
| エージェントツール | AWS Strands Tools | strands-agents-tools >= 0.1.0 |
| エージェントビルダー | AWS Strands Builder | strands-agents-builder >= 0.1.0 |
| LLMプロバイダ | Amazon Bedrock (boto3) | boto3 >= 1.34.0 |
| データバリデーション | Pydantic | pydantic >= 2.0.0 |
| AIエージェント評価フレームワーク | strands-agents-evals | strands-agents-evals >= 0.1.0 |
| テストフレームワーク | pytest | pytest >= 7.4.0 |
| カバレッジ計測 | pytest-cov | pytest-cov >= 4.1.0 |
| 環境変数管理 | python-dotenv | python-dotenv >= 1.0.0 |
| 日付処理 | python-dateutil | python-dateutil >= 2.8.2 |
| ロギング | logging（標準ライブラリ） | - |

### 追加パッケージの例（業務要件に応じて選択）

| カテゴリ | 技術 | バージョン要件 | 用途 |
|:---|:---|:---|:---|
| Excel生成 | openpyxl | openpyxl >= 3.1.0 | Excel形式の帳票出力 |

---

## R7. 命名規則

| 対象 | 規則 | 例 |
|:---|:---|:---|
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

## R8. 言語ポリシー

| 対象 | 使用言語 | 備考 |
|:---|:---|:---|
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

## R9. 共通コーディングパターン

### R9.1 エラーハンドリングパターン

全コンポーネントは `ErrorHandler` クラスのインスタンスを保持し、エラー処理を委譲する。

- **クラス内での保持方法**: `self._error_handler = ErrorHandler()` をコンストラクタで初期化
- **モジュールレベルでの保持方法**: `_error_handler = ErrorHandler()` をモジュール先頭で初期化
- **エラー処理の委譲**: エラー種別ごとの `handle_*` メソッドを呼び出し、戻り値（ユーザー向けメッセージ文字列）を利用する
- **エラーハンドリングの階層**: EventLoopException（`__cause__` で LoopLimitError を判定）→ Exception の順でキャッチする。Strands SDK は Hook 内で発生した例外を EventLoopException でラップして伝搬するため、LoopLimitError を直接 catch するのではなく EventLoopException の `__cause__` を確認する
- **ツール関数のエラー返却**: 辞書形式で `{"success": False, "message": エラーメッセージ}` を返す。例外を再送出しない
- **ドメイン固有のエラーハンドラ**: 業務要件に応じて `handle_{domain}_error()` メソッドを `ErrorHandler` に追加する

### R9.2 ログ出力パターン

全てのログ出力は `ErrorHandler` クラスのログメソッド経由で行う。直接 `logging` モジュールを呼び出さない。

- **ログレベルの使い分け**:
  - `log_debug`: 開発時のデバッグ情報
  - `log_info`: 正常処理の記録（処理開始、処理完了、データ読み込み成功等）
  - `log_warning`: 注意が必要な状態（ループ制限到達等）
  - `log_error`: エラー発生（`error_type` パラメータでエラー種別を分類）
  - `log_critical`: システム継続不能な重大エラー
- **コンテキスト辞書の付与**: ログメソッドにはオプションの `context` 辞書を渡し、構造化された追加情報を記録する
- **スタックトレース出力**: `exc_info=True` パラメータで制御。バリデーションエラー、データ読み込みエラー、予期しないエラーでは有効にする

### R9.3 バリデーションパターン

外部から受け取るデータは全てPydanticモデルでバリデーションを行う。

- **バリデーション実行タイミング**: ツール関数の入口、エージェント呼び出し時の`invocation_state`受取時
- **共通バリデータ関数**: 複数モデルで共有するバリデータを関数として定義し、`field_validator` で各モデルに適用する。業務要件に応じて追加のバリデータを定義する
- **バリデーションエラー処理**: `ValidationError` をキャッチし、`ErrorHandler.handle_validation_error()` に委譲
- **バリデーション済みデータの利用**: バリデーション後はPydanticモデルのインスタンス属性またはmodel_dump()を通じてデータにアクセスする

#### R9.3.1 モデルカテゴリと用途

| カテゴリ | 用途 | 定義元 | 利用先 |
|:---|:---|:---|:---|
| マスタデータモデル | `data/`配下のJSONファイルの型保証 | JSONデータ構造に対応 | `tools/{domain}_tools.py` |
| ツール入力モデル | ツール関数の入力パラメータの型保証 | ツール関数の引数に対応 | `tools/{domain}_tools.py` |
| エージェント状態モデル | `invocation_state`の型保証 | エージェント間の状態受け渡し | `agents/`, `tools/` |
| 出力生成モデル | 出力ファイル生成時のデータ型保証 | 出力内容の構造に対応 | `tools/output_generator.py` |

#### R9.3.2 Field定義パターン

| パターン | 用途 | 例 |
|:---|:---|:---|
| `Field(..., description="説明")` | 必須フィールド | `name: str = Field(..., description="名称")` |
| `Field(None, description="説明")` | 任意フィールド（デフォルトNone） | `notes: Optional[str] = Field(None, description="備考")` |
| `Field(..., min_length=1)` | 空文字禁止 | `name: str = Field(..., min_length=1, description="名称")` |
| `Field(..., gt=0)` | 正の数値のみ | `amount: float = Field(..., gt=0, description="金額")` |
| `Field(..., ge=0)` | 0以上の数値 | `cost: float = Field(..., ge=0, description="費用")` |
| `Literal[...]` | 許可値の列挙 | `category: Literal["A", "B", "C"]` |

#### R9.3.3 バリデーターの適用パターン

| パターン | 用途 | 例 |
|:---|:---|:---|
| 共通バリデーター関数の適用 | 複数モデルで共有するバリデーション | `_validate_xxx = field_validator("field_name")(validate_xxx)` |
| クラスメソッドバリデーター | モデル固有のバリデーション | `@field_validator("items")` + `@classmethod` |

#### R9.3.4 バリデーション実行タイミング

| タイミング | 実行箇所 |
|:---|:---|
| ツール関数の入口 | `tools/{domain}_tools.py` |
| invocation_state受取時 | `agents/orchestrator_agent.py` |
| invocation_stateの再バリデーション | `tools/output_generator.py` |
| マスタデータ読み込み時 | `tools/{domain}_tools.py` |

### R9.4 デコレータの使い分け

AWS Strandsフレームワークのツールデコレータは以下の基準で使い分ける。

| デコレータ | 使用条件 | 例 |
|:---|:---|:---|
| `@tool` | `invocation_state` やツールコンテキストを参照しないツール | `search_data`, `calculate_value` |
| `@tool(context=True)` | `invocation_state` を参照する、または `ToolContext` が必要なツール | `specialist_a_agent`, `output_generator` |

- `@tool(context=True)` を使用する場合、関数の最後の引数に `tool_context: ToolContext` を追加する
- デコレータは関数シグネチャの直前に配置する

### R9.5 Agent()コンストラクタの共通パラメータ

全エージェントは `strands.Agent()` コンストラクタで以下の共通パラメータを設定する。

#### R9.5.1 Agent()パラメータ一覧

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

#### R9.5.2 ModelConfig.get_model() の内部パラメータ

`config/model_config.py` の `ModelConfig.get_model()` が返す `BedrockModel` の構成：

```python
BedrockModel(
    model_id=cls.DEFAULT_MODEL_ID,       # str: LLMモデルID（R10参照）
    guardrail_id=cls.GUARDRAIL_ID,       # str: ガードレールID（R10参照）
    guardrail_version=cls.GUARDRAIL_VERSION,  # str: ガードレールバージョン
    guardrail_trace="enabled"            # str: ガードレールトレース（全エージェント共通: "enabled"）
)
```

#### R9.5.3 ウィンドウサイズの目安

| エージェント種別 | window_size | 理由 |
|:---|:---|:---|
| オーケストレーター | 30（大） | 複数の専門エージェントとのやり取りを保持する必要があるため |
| 専門エージェント（複雑な処理） | 20（中） | 複数ステップの情報収集・処理を行うため |
| 専門エージェント（単純な処理） | 15（小） | 特定タスクに集中した短い対話のため |

#### R9.5.4 フック構成

| エージェント種別 | hooks | 理由 |
|:---|:---|:---|
| オーケストレーター | `[LoopControlHook]` | ループ制御のみ（出力生成は専門エージェントが担当） |
| 専門エージェント（出力生成あり） | `[HumanApprovalHook, LoopControlHook]` | 出力前の人間承認 + ループ制御 |
| 専門エージェント（出力生成なし） | `[LoopControlHook]` | ループ制御のみ |

#### R9.5.5 エージェント種別ごとのパラメータ差分

全エージェントで共通のパラメータ（`model`, `callback_handler`, `retry_strategy`, `should_truncate_results`, `per_turn`）を除き、エージェント種別ごとに異なるパラメータは以下の通り：

| パラメータ | オーケストレーター | 専門エージェント |
|:---|:---|:---|
| `system_prompt` | 定数（`ORCHESTRATOR_SYSTEM_PROMPT`） | 定数または動的生成関数 |
| `tools` | 専門エージェントのツール関数 | ドメイン固有ツール + 出力生成ツール |
| `agent_id` | `"orchestrator_agent"` | `"{specialist_name}_agent"` |
| `name` | `"受付窓口エージェント"` 等 | `"{ドメイン}エージェント"` 等 |
| `description` | 振り分け役割の説明 | ドメイン固有処理の説明 |
| `window_size` | 30 | 15〜20 |
| `hooks` | `[LoopControlHook]` | `[HumanApprovalHook, LoopControlHook]` |
| `session_manager` | `self._session_manager`（インスタンス変数） | ファクトリ関数内で都度作成 |

### R9.6 invocation_stateとagent()呼び出しパターン

`Agent()` コンストラクタで生成したエージェントインスタンスを実行する際のパラメータを定義する。

#### R9.6.1 invocation_stateとは

`invocation_state` は `ToolContext` を通じてアクセスできる辞書で、エージェント呼び出し時に渡されたコンテキスト情報を保持する。

- **LLMのプロンプトには含まれない**（コンテキストウィンドウを消費しない）
- **ツール関数の内部でのみ参照できる**（`@tool(context=True)` + `tool_context.invocation_state`）
- **リクエスト単位で有効**（セッションをまたがない）
- 機密情報やシステム内部情報の受け渡しに適している

#### R9.6.2 データの受け渡しアプローチの使い分け

| アプローチ | 用途 | 例 |
|:---|:---|:---|
| ツールパラメータ | LLMが推論・判断して渡すデータ | 検索クエリ、ファイルパス、ユーザーの回答 |
| `invocation_state` | プロンプトに含めたくないが動作に影響するコンテキスト | ユーザーID、セッションID、申請日 |
| クラスベースツール | リクエスト間で変わらない設定 | APIキー、DB接続文字列 |

#### R9.6.3 ツール関数内でのinvocation_stateの参照

`@tool(context=True)` を付けたツール関数内で `tool_context.invocation_state` から辞書として取得する：

```python
from strands import tool, ToolContext

@tool(context=True)
def output_generator(data: list, tool_context: ToolContext) -> dict:
    """出力ファイルを生成する。

    Args:
        data: 出力データのリスト
    """
    # invocation_stateからコンテキスト情報を取得（.get()で安全にアクセス）
    user_name = tool_context.invocation_state.get("user_name")
    request_date = tool_context.invocation_state.get("request_date")
    # ... 出力生成処理 ...
```

| 参照方法 | 説明 |
|:---|:---|
| `tool_context.invocation_state` | 辞書全体を取得 |
| `tool_context.invocation_state.get("key")` | 安全にキーを取得（存在しない場合は `None`） |
| `tool_context.invocation_state["key"]` | キーを取得（存在しない場合は `KeyError`） |

#### R9.6.4 オーケストレーターからのエージェント呼び出し

オーケストレーターの対話ループ内で、ユーザー入力に対してエージェントを実行する：

```python
# invocation_stateをPydanticモデルでバリデーションしてから渡す
invocation_state = InvocationState(
    user_name=self._user_name,
    request_date=datetime.now().strftime("%Y-%m-%d"),
    session_id=self._session_id
)

response = self.agent(
    user_input,                                  # str: ユーザーからの入力テキスト
    invocation_state=invocation_state.model_dump()  # dict: Pydanticモデルを辞書に変換して渡す
)
```

| パラメータ | 型 | 説明 |
|:---|:---|:---|
| 第1引数（位置引数） | `str` | ユーザーからの入力テキスト |
| `invocation_state` | `dict` | エージェント間で共有する状態データ。Pydanticモデルの `model_dump()` で辞書化して渡す |

#### R9.6.5 専門エージェント（Agent as Tool）からのエージェント呼び出し

`@tool(context=True)` でラップされた専門エージェントのツール関数内で、子エージェントを実行する：

```python
# invocation_stateから必要な情報のみを抽出して子エージェントに伝播
state = tool_context.invocation_state  # オーケストレーターから渡されたstate

# ファクトリ関数でエージェント生成
agent = _get_specialist_a_agent(session_id=state["session_id"])

# 子エージェントにはsession_idを含めず、業務に必要な情報のみを伝播
child_invocation_state = {
    "user_name": state["user_name"],
    "request_date": state["request_date"]
}

response = agent(
    query,                                      # str: オーケストレーターからの質問・指示
    invocation_state=child_invocation_state      # dict: 子エージェント用の状態データ
)
```

#### R9.6.6 invocation_stateの伝播ルール

| 段階 | 伝播の流れ | 渡すフィールド | 説明 |
|:---|:---|:---|:---|
| ① | オーケストレーター → オーケストレーターagent() | 全フィールド（`model_dump()`） | Pydanticモデルを辞書化して渡す |
| ② | 専門エージェントツール関数 → 子agent() | 業務に必要なフィールドのみ | `session_id`はファクトリ関数で消費済みのため除外 |
| ③ | 専門エージェント内のツール | `tool_context.invocation_state`で参照 | `@tool(context=True)`のツールのみアクセス可能 |

### R9.7 Agent as Toolsパターン

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

---

## R10. 共通設定値

| 設定項目 | 値 | 適用対象 | 備考 |
|:---|:---|:---|:---|
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
| セッション保存先 | `data/sessions/` | セッション管理 | プロジェクトルートからの相対パス |

### カスタマイズガイド

- LLMモデルIDはリージョンとモデルファミリーに応じて変更する
- ガードレールIDはAmazon Bedrockで作成したガードレールに応じて設定する
- 業務要件に応じて固有の設定値（期間制限、金額閾値等）を追加する

---

## R9.8 HookProviderの実装パターン

`HookProvider` を継承してフックを実装する際は、以下のStrands SDK仕様に従う。

### R9.8.1 利用可能なイベントクラス

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

### R9.8.2 register_hooksの実装

フックの登録には `registry.add_callback()` を使用する（`add_hook()` は存在しない）。

```python
def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
    registry.add_callback(BeforeToolCallEvent, self._handle_before_tool_call)
    registry.add_callback(AfterToolCallEvent, self._handle_after_tool_call)
```

### R9.8.3 BeforeToolCallEventの属性

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

アクセス方法：

```python
def _handle_before_tool_call(self, event: BeforeToolCallEvent) -> None:
    tool_name = event.tool_use["name"]          # ツール名
    tool_input = event.tool_use["input"] or {}  # ツール入力パラメータ
    tool_use_id = event.tool_use["toolUseId"]   # ツール呼び出しID

    # 対象ツール以外はスキップ（全ツール呼び出しで発火するため必須）
    if tool_name not in self.target_tools:
        return
```

### R9.8.4 ツール呼び出しのキャンセル方法

`event.cancel()` は存在しない。`event.cancel_tool` にメッセージ文字列を設定してキャンセルする。

```python
# キャンセル: cancel_toolにメッセージを設定する（event.cancel()は存在しない）
event.cancel_tool = "ユーザーによりキャンセルされました。"

# Trueを設定するとStrands標準のキャンセルメッセージが使用される
event.cancel_tool = True
```

### R9.8.5 AfterToolCallEventの属性

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

---

## R9.9 ツール関数のdocstringとtool spec

### R9.9.1 tool spec自動生成の制約

Strandsの `@tool` デコレータは関数シグネチャとdocstringからtool spec（JSON Schema）を自動生成し、LLMに渡す。LLMはこのtool specを手がかりにツール呼び出しのパラメータを構築する。

ただし、`list` 等の構造型パラメータは内部構造（要素のプロパティ）がtool specに反映されず空になる。LLMがフィールド名を正しく認識できるよう、docstringの `Args:` セクションに要素構造を明記すること。

### R9.9.2 構造型パラメータの記述ルール

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

## R10. 環境変数の規約

### R10.1 `.env.template` の定義

プロジェクトルートに `.env.template` を配置し、アプリケーション動作に必要な環境変数の一覧を定義する。
`.env` ファイルは `.env.template` をコピーして作成し、実際の値を設定する。

### R10.2 必須環境変数

| 環境変数名 | 用途 | 設定例 |
|:---|:---|:---|:---|
| `LOG_LEVEL` | ログ出力レベル（DEBUG / INFO / WARNING / ERROR / CRITICAL） | `INFO` |
| `AWS_ACCESS_KEY_ID` | AWS認証用アクセスキーID | — |
| `AWS_SECRET_ACCESS_KEY` | AWS認証用シークレットアクセスキー | — |
| `AWS_DEFAULT_REGION` | AWSデフォルトリージョン | `ap-northeast-1` |
| `GUARDRAIL_ID` | Amazon Bedrockガードレールの識別子 | — |
| `GUARDRAIL_VERSION` | Amazon Bedrockガードレールのバージョン | `DRAFT` |

### R10.3 `.env` ファイルの作成手順

1. `.env.template` をコピーして `.env` ファイルを作成する
2. `.env` ファイルを開き、利用者独自の設定値（AWS認証情報・ガードレールID等）を入力する

### R10.4 運用ルール

- `.env` ファイルは `.gitignore` に登録し、リポジトリにコミットしない
- `.env.template` は値を空欄またはデフォルト値のみ記載し、秘密情報を含めない
- アプリケーション起動時に `python-dotenv` の `load_dotenv()` で `.env` ファイルを読み込む
- 環境変数の参照は `os.getenv("変数名", "デフォルト値")` で行う

---

## R11. テストの規約

| 項目 | ルール |
|:---|:---|
| テストディレクトリ | `tests/unit/`（単体）、`tests/integration/`（結合） |
| テストファイル命名 | `test_{対象モジュール名}.py` |
| テストクラス命名 | `Test{対象クラス名}` |
| テスト関数命名 | `test_{テスト内容}` |

### R11.1 単体テスト

各モジュール（機能単位）ごとに独立したテストファイルを作成する。
- テスト観点は対応する設計書の「テスト観点」セクションを参照する

### R11.2 結合テスト

複数モジュールを組み合わせた連携動作を検証するテストファイルを作成する。
- モジュールの依存関係は「00_rule_directory_structure.md内のR3. ファイル間の依存関係ルール」セクションを参照する
