# 実装タスク計画書

> 規約: skills/06-code-generation/00_rule_directory_structure.md / 00_rule_project_conventions.md

---

## タスク1: データモデル定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md（TransportCalculatorInput・TransportSegmentモデル）
  - artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md（TransportApplicationInput・ExpenseApplicationInput・ExpenseItemモデル）
  - artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md（invocation_stateデータ構造）
  - artifacts/04_basic-design/outputs/データモデル基本設計.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/01_skeleton_data_models.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/models/data_models.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_data_models.py
- **実装内容**:
  - 共通バリデーター関数: `normalize_station_name`, `normalize_transport_type`, `validate_date`, `validate_business_purpose`, `validate_amount`, `normalize_expense_category`
  - エージェント状態モデル: `InvocationState`（applicant_name, application_date）
  - ツール入力モデル: `TransportCalculatorInput`（departure, destination, transport_type, travel_date）
  - 出力生成モデル: `TransportSegment`, `TransportApplicationInput`, `ExpenseItem`, `ExpenseApplicationInput`
- **単体テスト内容**:
  - `normalize_station_name`: 「駅」「Station」除去・strip確認
  - `normalize_transport_type`: 「電車」→「train」等の全マッピング確認
  - `validate_date`: YYYY-MM-DD正常・不正形式テスト
  - `validate_business_purpose`: 空文字列・空白のみで ValidationError
  - `validate_amount`: 0以下でバリデーションエラー
  - `normalize_expense_category`: 「事務用品」→「事務用品費」等のマッピング・判断不能→「その他経費」
  - `TransportCalculatorInput`: 正常・異常系（空文字・不正交通手段・不正日付）
  - `TransportApplicationInput`: segments 0件でバリデーションエラー
  - `ExpenseApplicationInput`: items 0件でバリデーションエラー

---

## タスク2: LLMモデル設定

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/03_system-design/outputs/システム基本情報.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/02_skeleton_model_config.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/config/model_config.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_model_config.py
- **実装内容**:
  - `ModelConfig` クラス（スタティックメソッドのみ）
  - `DEFAULT_MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"`
  - `GUARDRAIL_ID`・`GUARDRAIL_VERSION` を環境変数から取得
  - `get_model()` → `BedrockModel` インスタンスを返す
- **単体テスト内容**:
  - `get_model()` が `BedrockModel` を返すこと
  - 環境変数 `GUARDRAIL_ID`・`GUARDRAIL_VERSION` が正しく読み込まれること

---

## タスク3: エラーハンドラー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/ErrorHandler詳細設計書.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/03_skeleton_error_handler.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/handlers/error_handler.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_error_handler.py
- **実装内容**:
  - `ErrorHandler` クラス（全メソッド `@staticmethod`、インスタンス化不要）
  - `handle_throttling_error`, `handle_max_tokens_error`, `handle_context_window_error`
  - `handle_fare_data_error`, `handle_calculation_error`, `handle_file_save_error`
  - `handle_validation_error`（Pydantic ValidationError の日本語化）
  - `handle_keyboard_interrupt`, `handle_loop_limit_error`, `handle_runtime_error`, `handle_unexpected_error`
- **単体テスト内容**:
  - 各メソッドが日本語メッセージ（str）を返すこと
  - `handle_loop_limit_error` が max_iterations を含むメッセージを返すこと
  - `handle_validation_error` がフィールド名を含む日本語メッセージを返すこと
  - 各メソッド内で logging が呼び出されないこと
  - None を渡した場合でも例外が発生しないこと

---

## タスク4: LoopControlHook

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/LoopControlHook詳細設計書.md
  - artifacts/03_system-design/outputs/実行制御方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/04_skeleton_loop_control_hook.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/handlers/loop_control_hook.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_loop_control_hook.py
- **実装内容**:
  - `LoopLimitError` カスタム例外クラス（current_iteration, max_iterations, agent_name フィールド）
  - `LoopControlHook(HookProvider)` クラス
  - `register_hooks`: BeforeInvocationEvent, BeforeModelCallEvent, AfterModelCallEvent, BeforeToolCallEvent, AfterToolCallEvent, AfterInvocationEvent を登録
  - `_before_invocation_handler`: `_loop_count = 0` に初期化・INFOログ
  - `_before_model_call_handler`: ループ開始ログ
  - `_after_model_call_handler`: カウントアップ・上限チェック・`LoopLimitError` 発生（event.exception 存在時スキップ）
  - `_before_tool_call_handler`: ツール呼び出し開始ログ
  - `_after_tool_call_handler`: ツール呼び出し完了ログ
  - `_after_invocation_handler`: 合計ループ回数ログ（リセットなし）
  - `_get_loop_count` プロパティ
- **単体テスト内容**:
  - max_iterations=10 で9回AfterModelCallEvent後に停止しないこと
  - max_iterations=10 で10回目に LoopLimitError が発生すること
  - LoopLimitError が正しいフィールドを保持すること
  - BeforeInvocationEvent でカウンターが0にリセットされること
  - AfterInvocationEvent でカウンターがリセットされないこと
  - event.exception 存在時にカウントアップされないこと
  - max_iterations=1 で1回目に LoopLimitError が発生すること

---

## タスク5: HumanApprovalHook

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/HumanApprovalHook詳細設計書.md
  - artifacts/03_system-design/outputs/実行制御方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/05_skeleton_human_approval_hook.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/handlers/human_approval_hook.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_human_approval_hook.py
- **実装内容**:
  - `HumanApprovalHook(HookProvider)` クラス（`target_tool: str` で初期化）
  - `register_hooks`: BeforeToolCallEvent を登録
  - `_before_tool_call_handler`: ツール名チェック → target_tool 一致時のみ承認フロー
  - `_normalize_approval_result`: ok/modify/cancel/unknown への正規化（別表記含む）
  - `_approval_callback`: 最大3回再入力。(True,"")/(False,修正内容)/(False,"CANCEL") を返す
  - `event.cancel_tool` にメッセージをセット（`event.cancel()` は不使用）
  - EOFError 処理
- **単体テスト内容**:
  - target_tool 一致時のみ承認要求が実施されること
  - "OK" 入力でツール実行が継続されること
  - "修正" 入力で event.cancel_tool がセットされること
  - "キャンセル" 入力で (False, "CANCEL") が返されること
  - "yes", "はい" 等が "ok" に正規化されること
  - 認識不能入力が3回続いた場合にキャンセル扱いとなること
  - EOFError 発生時にキャンセル扱いとなること
  - event.stop_reason が使用されないこと

---

## タスク6: セッションマネージャー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/04_basic-design/outputs/セッションマネージャ基本設計.md
  - artifacts/03_system-design/outputs/セッション管理方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/06_skeleton_session_manager.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/session/session_manager.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_session_manager.py
- **実装内容**:
  - `SessionManagerFactory` クラス
  - `create(session_id, storage_path="storage/sessions/")` → `FileSessionManager` を返す
  - strands SDK の `FileSessionManager` をラップ
- **単体テスト内容**:
  - `create()` が `FileSessionManager` インスタンスを返すこと
  - `storage_path` が正しく設定されること

---

## タスク7: 申請ルール（交通費）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md（2.3.1 システムプロンプト・申請ルール）
  - artifacts/02_system-requirements/outputs/業務ルール定義.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/09_skeleton_policies.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/agent_knowledge/transportation_policies.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_transportation_policies.py
- **実装内容**:
  - `get_transportation_policies()` → 交通費申請ルール文字列を返す関数
  - BRL-01〜BRL-16 の交通費関連ルールをテキストとして定義
- **単体テスト内容**:
  - `get_transportation_policies()` が非空の文字列を返すこと
  - 返却文字列に主要なルール（BRL-05, BRL-06, BRL-07, BRL-08, BRL-10, BRL-11）が含まれること

---

## タスク8: 申請ルール（経費）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md（2.3.1 システムプロンプト・申請ルール）
  - artifacts/02_system-requirements/outputs/業務ルール定義.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/09_skeleton_policies.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/agent_knowledge/receipt_policies.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_receipt_policies.py
- **実装内容**:
  - `get_receipt_policies()` → 経費申請ルール文字列を返す関数
  - BRL-07・BRL-09・BRL-11〜BRL-13 の経費関連ルールをテキストとして定義
- **単体テスト内容**:
  - `get_receipt_policies()` が非空の文字列を返すこと
  - 返却文字列に主要なルール（BRL-07, BRL-09, BRL-11, BRL-12, BRL-13）が含まれること

---

## タスク9: オーケストレータープロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md（2.3.1 システムプロンプト）
- **参照するスケルトンコード**: skills/templates/06_code-generation/07_skeleton_prompt_orchestrator.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/prompt/prompt_orchestrator.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_prompt_orchestrator.py
- **実装内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT` 定数（静的定数）
  - 設計書 2.3.1 のプロンプト全文をそのまま定義
- **単体テスト内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT` が非空の文字列であること
  - 主要なキーワード（transport_agent, expense_agent, BRL-01等）が含まれること

---

## タスク10: 専門エージェントプロンプト（交通費・経費）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md（2.3.1 システムプロンプト）
  - artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md（2.3.1 システムプロンプト）
- **参照するスケルトンコード**: skills/templates/06_code-generation/08_skeleton_prompt_specialist.md
- **成果物のファイルパス**:
  - artifacts/06_code-generation/src/prompt/prompt_transport.py
  - artifacts/06_code-generation/src/prompt/prompt_expense.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_prompt_specialist.py
- **実装内容**:
  - `prompt_transport.py`: `build_transport_prompt(applicant_name, application_date)` → 動的プロンプト生成関数
    - application_date から3ヶ月前の deadline_date を計算
    - `get_transportation_policies()` を読み込んでプロンプトに埋め込む
  - `prompt_expense.py`: `build_expense_prompt(applicant_name, application_date)` → 動的プロンプト生成関数
    - application_date から3ヶ月前の deadline_date を計算
    - `get_receipt_policies()` を読み込んでプロンプトに埋め込む
- **単体テスト内容**:
  - `build_transport_prompt()` が applicant_name・application_date・deadline_date を含む文字列を返すこと
  - `build_expense_prompt()` が applicant_name・application_date・deadline_date を含む文字列を返すこと
  - deadline_date が application_date から3ヶ月前であること

---

## タスク11: 交通費計算ツール

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md
  - artifacts/04_basic-design/outputs/データモデル基本設計.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/バリデーション方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/10_skeleton_tools.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/tools/transport_calculator.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_transport_calculator.py
- **実装内容**:
  - `TransportCalculator` クラス
  - クラス変数: `_ROUTE_FARES: dict[tuple[str,str], int]`, `_FIXED_FARES: dict[str, int]`
  - `_load_fare_data()` スタティックメソッド（train_routes.json・fixed_fares.json 読み込み、tuple[bool,str] 返却）
  - `@tool` デコレータ付き `calculate_transport_fare(departure, destination, transport_type, travel_date)` クラスメソッド
  - Pydantic `TransportCalculatorInput` でバリデーション
  - 双方向経路検索・固定運賃参照・`{"success": bool, ...}` 形式の戻り値
  - ファイルパスは `./data/fixed_fares.json` / `./data/train_fares.json`（materialsのコピー先に合わせる）
- **単体テスト内容**:
  - 電車: train_routes.json の運賃が返却されること
  - バス・タクシー・飛行機: fixed_fares.json の運賃が返却されること
  - 正常時に success=True・fare・data_source が返却されること
  - 経路不存在で {"success": False, "message": ...} が返却されること
  - departure 空文字で ValidationError が発生すること
  - transport_type "自転車" で ValidationError が発生すること
  - train_routes.json 不存在で {"success": False, "message": ...} が返却されること
  - 駅名正規化（「新宿駅」→「新宿」）が機能すること

---

## タスク12: 申請書生成ツール

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md
  - artifacts/04_basic-design/outputs/データモデル基本設計.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/バリデーション方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/10_skeleton_tools.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/tools/application_generator.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_application_generator.py
- **実装内容**:
  - `ApplicationGenerator` クラス
  - `@tool(context=True)` デコレータ付き `generate_transport_application(business_purpose, segments, total_fare, tool_context)` メソッド
  - `@tool(context=True)` デコレータ付き `generate_expense_application(business_purpose, items, total_amount, tool_context)` メソッド
  - `_save_file(wb, file_path)` 内部メソッド（IOError/PermissionError/Exception処理、tuple[bool,str] 返却）
  - `invocation_state` からの applicant_name・application_date・session_id 取得
  - Pydantic `TransportApplicationInput`・`ExpenseApplicationInput` でバリデーション
  - openpyxl によるテンプレート読み込み・セル書き込み（B3/B4/B5/A7+i〜G7+i/H7+n+2）
  - `data/output/{session_id}/` への出力
  - テンプレートパス: `data/templates/交通費精算申請書テンプレート.xlsx` / `data/templates/経費精算申請書テンプレート.xlsx`
- **単体テスト内容**:
  - 正常な交通費申請情報で Excel ファイルが生成されること
  - H列（承認状況）に値が書き込まれていないこと
  - A列に No（1始まり）が正しく書き込まれること
  - 生成パスが `data/output/{session_id}/交通費精算申請_{timestamp}.xlsx` 形式であること
  - テンプレート不存在で {"success": False, "message": ...} が返却されること
  - business_purpose 空文字で ValidationError が発生すること
  - segments 空リストで ValidationError が発生すること
  - segments に必須キー欠落で不足キー名を含むエラーメッセージが返却されること
  - IOError 発生時に _save_file が (False, エラーメッセージ) を返すこと

---

## タスク13: オーケストレーターエージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md
  - artifacts/03_system-design/outputs/マルチエージェント連携設計.md
  - artifacts/03_system-design/outputs/セッション管理方針.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
  - artifacts/03_system-design/outputs/バリデーション方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/11_skeleton_orchestrator_agent.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/agents/orchestrator_agent.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_orchestrator_agent.py
- **実装内容**:
  - `Orchestrator` クラス
  - `__init__(self, applicant_name: str)`: session_id生成（タイムスタンプ_UUID8形式）・application_date取得・Agent初期化（SlidingWindowConversationManager(window_size=30)・LoopControlHook・transport_agent/expense_agentツール）
  - `run(self) -> None`: ウェルカムメッセージ・対話ループ・特殊コマンド処理・invocation_state生成・エラーハンドリング
  - `_print_welcome()` 関数
  - 例外処理: KeyboardInterrupt(break)・LoopLimitError(continue)・ContextWindowOverflowException(continue)・MaxTokensReachedException(continue)・RuntimeError(continue)・Exception(continue)
  - 申請者名ログマスキング（"***"）
- **単体テスト内容**:
  - session_id が `タイムスタンプ_UUID8` 形式で生成されること
  - invocation_state に applicant_name・application_date・session_id が設定されること
  - "exit"/"quit" でループが終了すること
  - "reset"/"リセット"/"最初から" で会話履歴がリセットされること
  - 空入力で再入力促進メッセージが表示されること
  - 501文字以上の入力で文字数制限メッセージが表示されること
  - LoopLimitError 発生時に WARNING ログが出力されループが継続すること
  - ログ出力に申請者名が含まれないこと（"***"でマスキング）

---

## タスク14: 交通費精算申請エージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md
  - artifacts/03_system-design/outputs/マルチエージェント連携設計.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/12_skeleton_specialist_agent.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/agents/transport_agent.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_transport_agent.py
- **実装内容**:
  - `_transport_agent_instances: dict[str, TransportAgent]` モジュールレベルキャッシュ
  - `TransportAgent` クラス
  - `__init__(self, applicant_name, application_date)`: `_build_prompt()` で動的プロンプト生成・Agent初期化（window_size=20・LoopControlHook・HumanApprovalHook(target_tool="generate_transport_application")・callback_handler=None）
  - `_build_prompt(self, applicant_name, application_date)`: `build_transport_prompt()` を使用
  - `__call__(self, query, invocation_state)`: `str(self._agent(...))` を返す
  - `@tool(context=True)` 付き `transport_agent(query, tool_context)` 関数
  - session_id をキーにキャッシュ・inner_state（session_id除外）を子エージェントへ渡す
  - 例外処理: LoopLimitError/ContextWindowOverflowException/MaxTokensReachedException/RuntimeError/Exception を str で返す
  - 申請者名ログマスキング（"***"）
- **単体テスト内容**:
  - 同一session_idで同一インスタンスが返されること（キャッシュ確認）
  - 異なるsession_idで異なるインスタンスが生成されること
  - inner_stateに session_id が含まれないこと
  - LoopLimitError 発生時に str 型のエラーメッセージが返されること
  - callback_handler=None が設定されること
  - ログ出力に申請者名が含まれないこと（"***"でマスキング）

---

## タスク15: 経費精算申請エージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md
  - artifacts/03_system-design/outputs/マルチエージェント連携設計.md
  - artifacts/03_system-design/outputs/例外処理方針.md
  - artifacts/03_system-design/outputs/共通設定方針.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/12_skeleton_specialist_agent.md
- **成果物のファイルパス**: artifacts/06_code-generation/src/agents/expense_agent.py
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_expense_agent.py
- **実装内容**:
  - `_expense_agent_instances: dict[str, ExpenseAgent]` モジュールレベルキャッシュ
  - `ExpenseAgent` クラス
  - `__init__(self, applicant_name, application_date)`: `_build_prompt()` で動的プロンプト生成・Agent初期化（window_size=15・LoopControlHook・HumanApprovalHook(target_tool="generate_expense_application")・callback_handler=None・image_reader ツール）
  - `_build_prompt(self, applicant_name, application_date)`: `build_expense_prompt()` を使用
  - `__call__(self, query, invocation_state)`: `str(self._agent(...))` を返す
  - `@tool(context=True)` 付き `expense_agent(query, tool_context)` 関数
  - session_id をキーにキャッシュ・inner_state（session_id除外）を子エージェントへ渡す
  - 例外処理: LoopLimitError/ContextWindowOverflowException/MaxTokensReachedException/RuntimeError/Exception を str で返す
  - 申請者名ログマスキング（"***"）
- **単体テスト内容**:
  - 同一session_idで同一インスタンスが返されること（キャッシュ確認）
  - inner_stateに session_id が含まれないこと
  - LoopLimitError 発生時に str 型のエラーメッセージが返されること
  - callback_handler=None が設定されること
  - ログ出力に申請者名が含まれないこと（"***"でマスキング）

---

## タスク16: エントリーポイント・プロジェクト設定

- **ステータス**: [x] 完了
- **参照する設計書**:
  - artifacts/03_system-design/outputs/システム基本情報.md
  - artifacts/03_system-design/outputs/共通設定方針.md
  - artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md（2.2.2 ウェルカムメッセージ・入力プロンプト）
- **参照するスケルトンコード**: skills/templates/06_code-generation/02_skeleton_model_config.md（requirements参照）
- **成果物のファイルパス**:
  - artifacts/06_code-generation/src/main.py
  - artifacts/06_code-generation/src/requirements.txt
  - artifacts/06_code-generation/src/pytest.ini
  - artifacts/06_code-generation/src/storage/__init__.py
  - artifacts/06_code-generation/src/output/.gitkeep
  - artifacts/06_code-generation/src/logs/.gitkeep
  - 各ディレクトリの `__init__.py`
- **単体テストコードのファイルパス**: artifacts/06_code-generation/src/tests/unit/test_main.py
- **実装内容**:
  - `main.py`:
    - `load_dotenv()` 実行
    - `warnings.filterwarnings("ignore")`
    - logging 設定（フォーマット・ファイルハンドラ・Strandsイベントループ CRITICAL 抑制）
    - アプリ起動時の申請者名入力（空欄不可）
    - `TransportCalculator._load_fare_data()` 実行・失敗時にエラー表示して終了
    - `Orchestrator(applicant_name).run()` 呼び出し
  - `requirements.txt`: 規約 R6 の依存パッケージ（strands-agents, boto3, pydantic, openpyxl, python-dotenv, python-dateutil, pytest, pytest-cov, strands-agents-tools 等）
  - `pytest.ini`: テストディレクトリ設定
- **単体テスト内容**:
  - 空欄の申請者名で再入力が促されること
  - `TransportCalculator._load_fare_data()` 失敗時にエラーメッセージが表示されること

---

## タスク17: データファイル・資材コピー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - skills/prompts/06_code-generation/実装タスク計画.md（materialsフォルダの各ファイルの配置）
  - skills/templates/06_code-generation/14_design_data_files.md
- **参照するスケルトンコード**: skills/templates/06_code-generation/14_design_data_files.md
- **成果物のファイルパス**:
  - artifacts/06_code-generation/src/data/fixed_fares.json
  - artifacts/06_code-generation/src/data/train_fares.json
  - artifacts/06_code-generation/src/data/templates/交通費精算申請書テンプレート.xlsx
  - artifacts/06_code-generation/src/data/templates/経費精算申請書テンプレート.xlsx
  - artifacts/06_code-generation/src/.gitignore
  - artifacts/06_code-generation/src/.env.template
- **単体テストコードのファイルパス**: N/A（資材コピータスクのためテスト不要）
- **実装内容**:
  - `materials/06_code-generation/fixed_fares.json` → `artifacts/06_code-generation/src/data/fixed_fares.json`
  - `materials/06_code-generation/train_fares.json` → `artifacts/06_code-generation/src/data/train_fares.json`
  - `materials/06_code-generation/交通費申請書_template.xlsx` → `artifacts/06_code-generation/src/data/templates/交通費精算申請書テンプレート.xlsx`
  - `materials/06_code-generation/経費精算申請書_template.xlsx` → `artifacts/06_code-generation/src/data/templates/経費精算申請書テンプレート.xlsx`
  - `materials/06_code-generation/.gitignore` → `artifacts/06_code-generation/src/.gitignore`
  - `materials/06_code-generation/.env.template` → `artifacts/06_code-generation/src/.env.template`
- **単体テスト内容**: N/A

---

## タスク18: 結合テスト

- **ステータス**: [x] 完了
- **テスト対象**:
  - TransportCalculator + ApplicationGenerator の連携（ツール間連携）
  - Orchestrator → TransportAgent / ExpenseAgent の呼び出しフロー（Agent as Tools）
  - ErrorHandler + LoopControlHook + HumanApprovalHook の協調動作
  - invocation_state の AG-001 → AG-002/AG-003 への伝播
- **結合テストコードのファイルパス**: artifacts/06_code-generation/src/tests/integration/test_application_flow.py
- **結合テスト内容**:
  - Orchestrator 初期化時に session_id が正しく生成されること
  - transport_agent ツール関数が LLM API モック環境で呼び出され、str 型の応答を返すこと
  - expense_agent ツール関数が LLM API モック環境で呼び出され、str 型の応答を返すこと
  - invocation_state の applicant_name・application_date・session_id が AG-002/AG-003 へ正しく伝播すること
  - LoopLimitError 発生時に Orchestrator の対話ループが継続すること（break しないこと）
  - TransportCalculator の _load_fare_data() 成功後に calculate_transport_fare が正しく動作すること
  - ApplicationGenerator が指定セル位置に正しく書き込んだ Excel ファイルを生成すること
