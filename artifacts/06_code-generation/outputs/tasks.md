# 実装タスク計画

## 共通規約
- **規約ファイル（全タスク共通参照）**:
  - `.claude/skills/phase-06-code-generation/references/00_rule_directory_structure.md`
  - `.claude/skills/phase-06-code-generation/references/00_rule_project_conventions.md`

---

## タスク1: データモデル定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/データモデル詳細設計.md`
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md`
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/01_skeleton_data_models.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/models/data_models.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_data_models.py`
- **実装内容**:
  - 共通バリデーター関数の定義（`validate_non_empty_string` 等）
  - `InvocationState` モデル（`user_name`, `request_date`, `session_id`）
  - 交通費計算マスタデータモデル（`FixedFare`, `TrainFare`, `FixedFaresData`, `TrainFaresData`）
  - 交通費計算ツール入力モデル（`TransportCalculationInput`, `RouteItem`）
  - 申請書生成ツール入力モデル（`TransportApplicationInput`, `TransportItem`, `ExpenseApplicationInput`, `ExpenseItem`）
  - 出力生成モデル（`TransportApplicationOutput`, `ExpenseApplicationOutput`）
- **単体テスト内容**:
  - `InvocationState` の各フィールドバリデーション（空文字、長さ制限等）
  - マスタデータモデルの型保証（正常・異常値）
  - ツール入力モデルのバリデーション（必須フィールド欠如、不正値）
  - 共通バリデーター関数の動作確認

---

## タスク2: Bedrockモデル設定

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/03_system-design/outputs/システム基本情報.md`
  - `artifacts/05_detailed-design/outputs/ガードレール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/02_skeleton_model_config.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/config/model_config.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_model_config.py`
- **実装内容**:
  - `ModelConfig` クラスの定義
  - `DEFAULT_MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"` の設定
  - `GUARDRAIL_ID`, `GUARDRAIL_VERSION = "DRAFT"` の設定
  - `get_model()` クラスメソッド（`@lru_cache(maxsize=1)` 付き）の実装
- **単体テスト内容**:
  - `get_model()` が `BedrockModel` インスタンスを返すこと
  - `DEFAULT_MODEL_ID` が正しく設定されること
  - `lru_cache` によるキャッシュ動作の確認

---

## タスク3: エージェント動作パラメータ設定

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/15_skeleton_settings.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/config/settings.py`, `artifacts/06_code-generation/src/config/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_settings.py`
- **実装内容**:
  - `_AgentSettings` 基底クラス（`max_iterations=10`, `max_attempts=6`, `initial_delay=4`, `max_delay=240`）
  - `ReceptionSettings`（AG-001: `window_size=30`, `max_turn_count=30`, `max_input_length=500`, 環境変数プレフィックス `ECAAS_RECEPTION_`）
  - `TransportSettings`（AG-002: `window_size=20`, `deadline_months=3`, 環境変数プレフィックス `ECAAS_TRANSPORT_`）
  - `ExpenseSettings`（AG-003: `window_size=20`, `deadline_months=3`, `approval_threshold=5000`, 環境変数プレフィックス `ECAAS_EXPENSE_`）
  - `_Settings` 集約クラスと `settings` モジュールレベル変数
  - `pyproject.toml`（依存パッケージ定義・pytest設定）
  - `.env.template`（必須環境変数テンプレート）
- **単体テスト内容**:
  - 各エージェント設定クラスのデフォルト値確認
  - 環境変数による上書き動作の確認
  - `settings` 変数からの各エージェント設定へのアクセス確認

---

## タスク4: エラーハンドリング

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ErrorHandler詳細設計.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/03_skeleton_error_handler.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/error_handler.py`, `artifacts/06_code-generation/src/handlers/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_error_handler.py`
- **実装内容**:
  - `LoopLimitError` 例外クラス（`current_iteration`, `max_iterations`, `agent_name` を保持する日本語メッセージ）
  - `ErrorHandler.handle_keyboard_interrupt()` の実装
  - `ErrorHandler.handle_loop_limit_error()` の実装
  - `ErrorHandler.handle_validation_error()` の実装（`error.errors()` を解析して日本語化）
  - `ErrorHandler.handle_runtime_error()` の実装
  - `ErrorHandler.handle_unexpected_error()` の実装
  - ドメイン固有エラーハンドラ: `handle_data_load_error()`, `handle_file_generation_error()`
- **単体テスト内容**:
  - `LoopLimitError` の初期化・メッセージ内容の検証
  - 各 `handle_*` メソッドが日本語文字列を返すこと
  - `handle_validation_error` が ValidationError のフィールド情報を含むメッセージを返すこと
  - `None` 引数での各メソッドの動作確認

---

## タスク5: CLIコンソール承認アダプタ

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/HumanApprovalHook詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/05_skeleton_human_approval_hook.md`（アダプタ部分）
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/console_approval_adapter.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_console_approval_adapter.py`
- **実装内容**:
  - `console_approval_callback(tool_name: str, tool_params: dict) -> tuple[bool, str]` 関数の実装
  - 申請情報サマリーの表示（ツールパラメータを整形して出力）
  - `input()` による承認入力の受け付け（OK/修正/キャンセル）
  - 戻り値: `(True, "")` = 承認、`(False, "CANCEL")` = キャンセル、`(False, "修正内容")` = 修正要望
- **単体テスト内容**:
  - `input()` モックを用いた各入力パターンの動作確認（OK/キャンセル/修正）
  - 戻り値の型・内容の検証

---

## タスク6: Human-in-the-Loop承認フック

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/HumanApprovalHook詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/05_skeleton_human_approval_hook.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/human_approval_hook.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_human_approval_hook.py`
- **実装内容**:
  - `HumanApprovalHook` クラスの実装（`HookProvider` 継承）
  - `APPROVAL_REQUIRED_TOOLS` の設定（`generate_transport_application`, `generate_expense_application`）
  - `register_hooks()` で `BeforeToolCallEvent` にコールバックを登録
  - `_on_before_tool_call()` の実装（承認対象フィルタリング・コールバック呼び出し・キャンセル制御）
  - `_build_cancel_message()` の実装（CANCEL/修正要望の場合分け）
- **単体テスト内容**:
  - 承認対象外ツールはスキップされること
  - `approved=True` 時はツールがそのまま実行されること（`cancel_tool` 未設定）
  - `approved=False, feedback="CANCEL"` 時のキャンセルメッセージ確認
  - `approved=False, feedback="修正内容"` 時の修正要望メッセージ確認

---

## タスク7: ReActループ制御フック

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/LoopControlHook詳細設計.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/04_skeleton_loop_control_hook.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/loop_control_hook.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_loop_control_hook.py`
- **実装内容**:
  - `LoopControlHook` クラスの実装（`HookProvider` 継承）
  - `register_hooks()` で6イベント（`BeforeInvocationEvent`, `BeforeModelCallEvent`, `AfterModelCallEvent`, `BeforeToolCallEvent`, `AfterToolCallEvent`, `AfterInvocationEvent`）にコールバック登録
  - `on_before_invocation()`: ループカウント初期化・開始ログ
  - `on_before_model_call()`: 現在ループ回数ログ
  - `on_after_model_call()`: 例外スキップ判定・カウントインクリメント・上限チェック・`LoopLimitError` 発生
  - `on_before_tool_call()` / `on_after_tool_call()`: ツール名取得・ログ出力
  - `on_after_invocation()`: 合計ループ回数ログ
  - `_get_tool_name()` ヘルパー（`event.tool_use` が None の場合は `"unknown"`）
- **単体テスト内容**:
  - ループカウントの初期化・インクリメント動作
  - `max_iterations` 到達時に `LoopLimitError` が発生すること
  - 例外発生時（`event.exception` あり）のカウントスキップ動作
  - ログ出力の確認（モック使用）

---

## タスク8: セッション管理

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/セッションマネージャ詳細設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/06_skeleton_session_manager.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/session/session_manager.py`, `artifacts/06_code-generation/src/session/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_session_manager.py`
- **実装内容**:
  - `SessionManagerFactory.generate_session_id(prefix="")` の実装（`YYYYMMDD_HHMMSS_uuid8` 形式）
  - `SessionManagerFactory.get_storage_dir()` の実装（`storage/sessions/` 自動作成、キャッシュ）
  - `SessionManagerFactory.create_session_manager(session_id)` の実装（`FileSessionManager` 生成）
  - `SessionManagerFactory.get_session_path(session_id)` の実装
- **単体テスト内容**:
  - `generate_session_id()` の書式確認（正規表現マッチ）
  - `generate_session_id("test")` のプレフィックス付き書式確認
  - `get_storage_dir()` がディレクトリを作成すること
  - `create_session_manager()` が `FileSessionManager` を返すこと

---

## タスク9: オーケストレーターのシステムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/システムプロンプト詳細設計.md`
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/ナレッジ・業務ルール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/07_skeleton_prompt_orchestrator.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_orchestrator.py`, `artifacts/06_code-generation/src/prompt/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_orchestrator.py`
- **実装内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT` 定数の定義（詳細設計書のシステムプロンプト内容に従い実装）
  - 役割定義・処理フロー・振り分け基準テーブル（交通費精算申請 / 経費精算申請）・エラーハンドリング指示・対話ルールを含む
- **単体テスト内容**:
  - 定数が文字列型であること
  - 振り分け先エージェント名（`transport_application_agent`, `expense_application_agent`）が含まれること

---

## タスク10: 交通費精算申請エージェントのシステムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/システムプロンプト詳細設計.md`
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/ナレッジ・業務ルール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_transport.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_transport.py`
- **実装内容**:
  - `_TRANSPORT_SYSTEM_PROMPT_TEMPLATE` テンプレート定数（プレースホルダー: `applicant_name`, `application_date`, `deadline_date`, `transport_rules`）
  - `get_transport_system_prompt(applicant_name, application_date, deadline, transport_rules)` 関数の実装
- **単体テスト内容**:
  - `get_transport_system_prompt()` が文字列を返すこと
  - テンプレート内の全プレースホルダーが置換されていること

---

## タスク11: 経費精算申請エージェントのシステムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/システムプロンプト詳細設計.md`
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/ナレッジ・業務ルール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_expense.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_expense.py`
- **実装内容**:
  - `_EXPENSE_SYSTEM_PROMPT_TEMPLATE` テンプレート定数（プレースホルダー: `applicant_name`, `application_date`, `deadline_date`, `expense_rules`）
  - `get_expense_system_prompt(applicant_name, application_date, deadline, expense_rules)` 関数の実装
- **単体テスト内容**:
  - `get_expense_system_prompt()` が文字列を返すこと
  - テンプレート内の全プレースホルダーが置換されていること

---

## タスク12: 交通費申請ビジネスルール・ポリシー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ナレッジ・業務ルール詳細設計.md`
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/knowledge/transport_policies.py`, `artifacts/06_code-generation/src/knowledge/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_policies.py`
- **実装内容**:
  - `get_transport_rules(deadline_months: int, approval_threshold: int) -> str` 関数の実装
  - 交通費精算申請に関するビジネスルール（申請期限・上長承認基準・申請書記載ルール等）のマークダウン形式テキスト返却
  - 動的パラメータ（期限月数・承認閾値）の f-string 埋め込み
- **単体テスト内容**:
  - 戻り値が文字列型であること
  - `deadline_months` の値がテキストに含まれること
  - `approval_threshold` の値がテキストに含まれること

---

## タスク13: 経費精算申請ビジネスルール・ポリシー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ナレッジ・業務ルール詳細設計.md`
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/knowledge/expense_policies.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_policies.py`
- **実装内容**:
  - `get_expense_rules(deadline_months: int, approval_threshold: int) -> str` 関数の実装
  - 経費精算申請に関するビジネスルール（経費区分・申請期限・上長承認基準等）のマークダウン形式テキスト返却
  - 動的パラメータ（期限月数・承認閾値）の f-string 埋め込み
- **単体テスト内容**:
  - 戻り値が文字列型であること
  - 経費区分（事務用品費・宿泊費・資格精算費・その他経費）がテキストに含まれること

---

## タスク14: 交通費計算ツール

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md`
  - `artifacts/05_detailed-design/outputs/データモデル詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/transport_tools.py`, `artifacts/06_code-generation/src/tools/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_tools.py`
- **実装内容**:
  - `_load_fixed_fares()` / `_load_train_fares()` データ読み込み関数（キャッシュフラグ方式）
  - `calculate_transport_cost(routes: list) -> dict` ツール関数（`@tool` デコレータ）の実装
    - `data/fixed_fares.json`（定額交通費）と `data/train_fares.json`（電車運賃）を参照
    - 各ルートの区間・交通手段・日付・往復フラグから運賃を計算
    - 申請期限チェック（移動日から3ヶ月以内）
    - 合計金額・上長承認要否（10,000円超）の算出
  - `ValidationError`, `Exception` の2層エラーハンドリング
- **単体テスト内容**:
  - データ読み込みの成功・失敗パターン
  - 定額交通費（タクシー等）の計算ロジック
  - 電車運賃の計算ロジック（往復・片道）
  - 不明区間の処理
  - バリデーションエラー時の `success=False` 返却確認

---

## タスク15: 申請書生成ツール（出力生成ツール）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計.md`
  - `artifacts/05_detailed-design/outputs/データモデル詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/output_generator.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_output_generator.py`
- **実装内容**:
  - `generate_transport_application(records: list, tool_context: ToolContext) -> dict` ツール関数（`@tool(context=True)`）の実装
    - `invocation_state` から `user_name`, `request_date` を取得
    - `template/交通費精算申請書テンプレート.xlsx` を読み込みセル書き込み・保存
    - 出力先: `output/交通費精算申請書_YYYYMMDD_HHMMSS.xlsx`
  - `generate_expense_application(records: list, tool_context: ToolContext) -> dict` ツール関数（`@tool(context=True)`）の実装
    - `invocation_state` から `user_name`, `request_date` を取得
    - `template/経費精算申請書テンプレート.xlsx` を読み込みセル書き込み・保存
    - 出力先: `output/経費精算申請書_YYYYMMDD_HHMMSS.xlsx`
  - 共通ヘルパー `_generate_form(template_path, validated, write_detail_rows, output_filename)` による DRY 実装
  - `ValidationError`, `Exception` の2層エラーハンドリング
- **単体テスト内容**:
  - テンプレートファイル不在時の `success=False` 返却確認
  - `invocation_state` からの情報取得確認（モック使用）
  - バリデーションエラー時のエラーメッセージ確認
  - 正常系での Excel ファイル生成確認（一時ディレクトリ使用）

---

## タスク16: データファイルの資材配置

- **ステータス**: [x] 完了
- **参照する設計書**: `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/14_design_data_files.md`
- **成果物のファイルパス**:
  - `artifacts/06_code-generation/src/data/fixed_fares.json`
  - `artifacts/06_code-generation/src/data/train_fares.json`
  - `artifacts/06_code-generation/src/template/交通費精算申請書テンプレート.xlsx`
  - `artifacts/06_code-generation/src/template/経費精算申請書テンプレート.xlsx`
- **単体テストコードのファイルパス**: なし（資材配置タスクのため）
- **実装内容**:
  - `materials/06_code-generation/fixed_fares.json` → `artifacts/06_code-generation/src/data/fixed_fares.json` にコピー
  - `materials/06_code-generation/train_fares.json` → `artifacts/06_code-generation/src/data/train_fares.json` にコピー
  - `materials/06_code-generation/交通費申請書_template.xlsx` → `artifacts/06_code-generation/src/template/交通費精算申請書テンプレート.xlsx` にコピー
  - `materials/06_code-generation/経費精算申請書_template.xlsx` → `artifacts/06_code-generation/src/template/経費精算申請書テンプレート.xlsx` にコピー
- **単体テスト内容**: なし

---

## タスク17: エージェント共通ユーティリティ（base_agent）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md`
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md`
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/17_skeleton_base_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/base_agent.py`, `artifacts/06_code-generation/src/agents/__init__.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_base_agent.py`
- **実装内容**:
  - `calculate_deadline(application_date, deadline_months)` 関数（`dateutil.relativedelta` 使用、パース失敗時は `"要確認"`）
  - `create_specialist_agent(session_id, system_prompt, tools, agent_name, window_size, max_iterations, max_attempts, initial_delay, max_delay)` ファクトリー関数（Session/HumanApprovalHook/LoopControlHook 生成・Agent 組み立て）
  - `invoke_specialist_agent(query, tool_context, agent_id, deadline_months, build_agent)` 呼び出しラッパー（invocation_state 取得・deadline 計算・build_agent 呼び出し・例外処理）
- **単体テスト内容**:
  - `calculate_deadline("2026-01-15", 3)` が `"2026-04-15"` を返すこと
  - 不正な日付文字列で `"要確認"` を返すこと
  - `invoke_specialist_agent` での `LoopLimitError` ハンドリング確認

---

## タスク18: オーケストレーターエージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md`
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/11_skeleton_orchestrator_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/orchestrator_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_orchestrator_agent.py`
- **実装内容**:
  - `OrchestratorAgent` クラスの実装
  - `_initialize()`: 申請者名収集（バリデーション: 空・500文字超）、セッションID生成、`SessionManagerFactory`・`LoopControlHook`・`Agent` 生成
  - `run()`: 対話ループ（ユーザー入力受付・終了判定・`InvocationState` 構築・エージェント呼び出し・応答表示）
  - エージェント設定（`agent_id="reception_agent"`, `window_size=settings.reception.window_size`, `max_iterations=settings.reception.max_iterations`）
- **単体テスト内容**:
  - 申請者名バリデーション（空・超過長）の動作確認
  - 終了コマンド入力時のループ終了確認
  - `InvocationState` の構築内容確認

---

## タスク19: 交通費精算申請エージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md`
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/transport_application_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_application_agent.py`
- **実装内容**:
  - `_build_transport_application_agent(session_id, applicant_name, application_date, deadline)` ビルド関数
    - `settings.transport` から設定取得
    - `get_transport_system_prompt()` でシステムプロンプト生成（transport_rules は `get_transport_rules()` から取得）
    - `create_specialist_agent()` でエージェント生成（tools: `calculate_transport_cost`, `generate_transport_application`）
  - `transport_application_agent(query, tool_context)` ツール関数（`@tool(context=True)`）
    - `invoke_specialist_agent()` 呼び出し（`agent_id="AG-002"`, `deadline_months=settings.transport.deadline_months`）
- **単体テスト内容**:
  - ビルド関数が `Agent` インスタンスを返すこと（モック使用）
  - `invoke_specialist_agent` への引数の確認

---

## タスク20: 経費精算申請エージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md`
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/expense_application_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_application_agent.py`
- **実装内容**:
  - `_build_expense_application_agent(session_id, applicant_name, application_date, deadline)` ビルド関数
    - `settings.expense` から設定取得
    - `get_expense_system_prompt()` でシステムプロンプト生成（expense_rules は `get_expense_rules()` から取得）
    - `create_specialist_agent()` でエージェント生成（tools: `generate_expense_application`）
  - `expense_application_agent(query, tool_context)` ツール関数（`@tool(context=True)`）
    - `invoke_specialist_agent()` 呼び出し（`agent_id="AG-003"`, `deadline_months=settings.expense.deadline_months`）
- **単体テスト内容**:
  - ビルド関数が `Agent` インスタンスを返すこと（モック使用）
  - `invoke_specialist_agent` への引数の確認

---

## タスク21: メインエントリーポイント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/03_system-design/outputs/ログ出力方式設計.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/13_skeleton_main.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/main.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_main.py`
- **実装内容**:
  - `.env` 読み込み（`load_dotenv()`）
  - ログ設定（3ハンドラー構成: コンソール・`logs/app.log`・`logs/error.log`、`RotatingFileHandler: 10MB × 5世代`）
  - Strands ライブラリのログレベル制御（`logging.WARNING`）
  - `main()` 関数（システム起動ログ・`OrchestratorAgent().run()`・`KeyboardInterrupt` / `Exception` ハンドリング）
- **単体テスト内容**:
  - `KeyboardInterrupt` 時の正常終了確認
  - `Exception` 時の `sys.exit(1)` 確認
  - ログ設定の確認

---

## タスク22: ガードレール CloudFormation テンプレート

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ガードレール詳細設計.md`
- **参照するスケルトンコード**: `.claude/skills/phase-06-code-generation/assets/16_guardrails_cloudformation_yaml.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/guardrails/guardrails_cloudformation.yaml`
- **単体テストコードのファイルパス**: なし（YAML ファイルのため）
- **実装内容**:
  - CloudFormation テンプレートの作成
  - `BlockedInputMessaging` / `BlockedOutputsMessaging` の設定（詳細設計書のフォールバック応答に従う）
  - `ContentPolicyConfig`: VIOLENCE/HATE/SEXUAL/INSULTS/MISCONDUCT/PROMPT_ATTACK の設定
  - `SensitiveInformationPolicyConfig`: 詳細設計書の PII 対象種別の設定
  - `WordPolicyConfig`: PROFANITY の設定
  - `CrossRegionConfig` / `Tags` の設定
- **単体テスト内容**: なし

---

## タスク23: ディレクトリ構造検証

- **ステータス**: [x] 完了
- **参照する規約**: `.claude/skills/phase-06-code-generation/references/00_rule_directory_structure.md`
- **検証対象ディレクトリ**: `artifacts/06_code-generation/src/`
- **検証内容**:
  - R1準拠確認: `src/` 直下のディレクトリが許可リスト（`config/`, `interfaces/`, `models/`, `agents/`, `handlers/`, `tools/`, `prompt/`, `knowledge/`, `session/`, `storage/`, `data/`, `template/`, `sample/`, `output/`, `logs/`, `evals/`, `docs/`, `tests/`）のみであること
  - R2準拠確認: 各ファイルが正しいディレクトリに配置され、命名規則に従っていること（`*_agent.py` → `agents/`、`*_tools.py` / `*_generator.py` → `tools/`、`*_policies.py` → `knowledge/`、`prompt_*.py` → `prompt/`）
- **違反時の報告形式**:
  - `⚠️ [違反種別]: [ファイルパス] → [修正方法]`
- **違反時の対応**: 検出された違反をすべて修正してからステータスを完了にすること

---

## タスク24: 結合テスト

- **ステータス**: [x] 完了
- **テスト対象**:
  - セッションマネージャ × LoopControlHook × オーケストレーターエージェントの連携
  - 交通費計算ツール × 申請書生成ツール × 交通費精算申請エージェントの連携
  - HumanApprovalHook × コンソール承認アダプタ × 申請書生成ツールの連携
  - ErrorHandler × LoopLimitError の上位伝播
- **結合テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/integration/test_multi_agent_flow.py`
- **結合テスト内容**:
  - セッションID生成からセッションマネージャ作成・エージェント初期化までの連携確認（モック使用）
  - `calculate_transport_cost` → `generate_transport_application` の連携フロー確認
  - `HumanApprovalHook` でのキャンセル時に申請書生成がスキップされること
  - `LoopControlHook` の `LoopLimitError` が `OrchestratorAgent.run()` で適切にハンドリングされること
  - `invocation_state` がオーケストレーターから専門エージェントへ正しく伝播すること
