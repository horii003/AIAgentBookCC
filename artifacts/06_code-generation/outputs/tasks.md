# 実装タスク計画書

> **参照規約**:
> - `.claude/skills/06-code-generation/00_rule_directory_structure.md`（R1〜R5）
> - `.claude/skills/06-code-generation/00_rule_project_conventions.md`（R6〜R11）

---

## タスク1: データモデル定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/04_basic-design/outputs/データモデル基本設計書.md`
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（5.3節: データモデル）
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（5.5節: データモデル）
  - `artifacts/03_system-design/outputs/バリデーション方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/01_skeleton_data_models.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/models/data_models.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_data_models.py`
- **実装内容**:
  - 共通バリデーター関数の定義（`normalize_station_name`, `normalize_transport_type`, `normalize_expense_category`, `parse_date_field`, `validate_positive_amount`, `validate_required_string`）
  - マスタデータモデル: `RailwayRouteMaster`（DATA-009: train_routes.json用）
  - ツール入力モデル: `FareCalculationInput`（TOOL-001入力, departure/destination/transport_type/travel_dateフィールド）
  - 移動区間モデル: `TransportSegment`（交通費申請の1区間情報）
  - 申請データモデル: `TransportApplicationData`（TOOL-002a入力）
  - 申請データモデル: `ExpenseApplicationData`（TOOL-002b入力, 申請期限チェックmodel_validator含む）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `normalize_station_name`: 「渋谷駅」→「渋谷」, 「渋谷駅前」→「渋谷」, 接尾語なし→そのまま
  - `normalize_transport_type`: 「JR」→「電車」, 「路線バス」→「バス」, 「taxi」→「タクシー」, 「航空機」→「飛行機」, 「新幹線」→ValidationError
  - `normalize_expense_category`: 「事務用品」→「事務用品費」, 「宿泊」→「宿泊費」, 「資格費」→「資格精算費」, 判断不可→「その他経費」（エラーなし）
  - `parse_date_field`: YYYY-MM-DD正常変換, 「abc」→ValueError
  - `validate_positive_amount`: 1以上通過, 0以下でValidationError
  - `validate_required_string`: 空文字でValidationError, 500文字以内通過, 501文字でValidationError
  - `FareCalculationInput`: departure空文字でValidationError, travel_date=Noneで通過
  - `TransportSegment`: fare=0でValidationError, fare=1で通過
  - `TransportApplicationData`: segments=[]でValidationError, segments最低1件で通過
  - `ExpenseApplicationData`: 申請期限90日差で通過, 91日差でValidationError（BRL-12）, expense_category判断不可→「その他経費」に変換

---

## タスク2: モデル設定

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/システム基本情報.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/02_skeleton_model_config.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/config/model_config.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_model_config.py`
- **実装内容**:
  - `ModelConfig`クラスの実装
  - `DEFAULT_MODEL_ID`: `"jp.anthropic.claude-sonnet-4-5-20250929-v1:0"`
  - `GUARDRAIL_ID`: 環境変数`GUARDRAIL_ID`から取得（要件上未定義 - `os.getenv("GUARDRAIL_ID", "")`）
  - `GUARDRAIL_VERSION`: 環境変数`GUARDRAIL_VERSION`から取得（デフォルト`"DRAFT"`）
  - `get_model()`クラスメソッド: `BedrockModel`インスタンスを返す（guardrail_id, guardrail_version, guardrail_trace="enabled"設定）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `get_model()`がBedrockModelインスタンスを返すこと
  - DEFAULT_MODEL_IDが正しい値であること
  - 環境変数GUARDRAIL_IDが設定されない場合、デフォルト値（空文字列）が使用されること

---

## タスク3: エラーハンドラー・フック定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ハンドラー詳細設計書.md`（全章: ErrorHandler/HumanApprovalHook/LoopControlHook/LoopLimitError）
  - `artifacts/03_system-design/outputs/例外処理方針.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
- **参照するスケルトンコード**:
  - `.claude/skills/templates/06_code-generation/03_skeleton_error_handler.md`
  - `.claude/skills/templates/06_code-generation/04_skeleton_loop_control_hook.md`
  - `.claude/skills/templates/06_code-generation/05_skeleton_human_approval_hook.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/error_handler.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_error_handler.py`
- **実装内容**:
  - `LoopLimitError`カスタム例外クラス（current_iteration/max_iterations/agent_nameフィールド）
  - `ErrorHandler`クラス（ステートレス。ログ出力なし）
    - `handle_throttling_error`, `handle_max_tokens_error`, `handle_context_window_error`
    - `handle_fare_data_error`, `handle_calculation_error`, `handle_file_save_error`
    - `handle_validation_error`（Pydantic ValidationErrorのmsgを日本語メッセージとして返す）
    - `handle_keyboard_interrupt`, `handle_loop_limit_error`, `handle_runtime_error`, `handle_unexpected_error`
  - `HumanApprovalHook`クラス（HookProvider実装）
    - `register_hooks`: BeforeToolCallEventに`_before_tool_call`を登録
    - `_before_tool_call`: generate_transport_application/generate_expense_applicationのみ対象。`_approval_callback`呼び出し。`event.cancel_tool`でキャンセル
    - `_approval_callback`: CLIで1/2/3の選択肢提示。OK/修正/キャンセルのtuple返却
  - `LoopControlHook`クラス（HookProvider実装）
    - `__init__(max_iterations=10, agent_name="")`
    - `register_hooks`: 6イベント（BeforeInvocation/BeforeModel/AfterModel/AfterInvocation/BeforeTool/AfterTool）登録
    - `_before_invocation`: iteration_countリセット
    - `_after_model_call`: event.exception存在時スキップ。カウントアップ。上限到達でLoopLimitError発生
    - `_after_invocation`: 合計ループ回数ログ出力（リセットなし）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `ValidationError`を渡したとき`handle_validation_error`が日本語エラーメッセージを返すこと
  - `LoopLimitError`に全フィールドが設定されること
  - `LoopControlHook`が10回目のLLM呼び出しで`LoopLimitError`を発生させること
  - `LoopControlHook`が9回目は継続し10回目で停止すること（境界値テスト）
  - `LoopControlHook`でAfterModelCallEvent発火時にevent.exceptionが存在する場合カウントがスキップされること
  - `HumanApprovalHook`が対象外ツール（`calculate_transport_fare`）でスキップされること
  - `HumanApprovalHook`でキャンセル選択時に`event.cancel_tool`にキャンセルメッセージがセットされること
  - `HumanApprovalHook`で修正選択時に`event.cancel_tool`に修正メッセージがセットされること
  - `HumanApprovalHook`で無効入力（"4"）後に有効入力（"1"）で処理されること

---

## タスク4: セッションマネージャー

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/04_basic-design/outputs/セッション管理基本設計書.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/06_skeleton_session_manager.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/session/session_manager.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_session_manager.py`
- **実装内容**:
  - `SessionManager`クラス
  - `__init__(session_id: str, storage_path: str = "data/sessions/")`: セッションIDとストレージパスを初期化。ディレクトリを自動作成
  - `create_session()`: 初期状態でセッション状態ファイルを作成。session_statusをCREATEDで初期化
  - `load_session()`: セッション状態ファイルを読み込みdict返却。存在しない場合はNoneを返す（例外を発生させない）
  - `save_session(session_data: dict)`: セッション状態をJSONファイルに上書き保存
  - `update_status(new_status: str)`: セッションステータスを更新
  - `delete_session()`: セッション状態ファイルを削除（CLOSED/TERMINATED時）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `create_session()`でJSONファイルが作成されること（一時ディレクトリを使用）
  - `save_session()`後に`load_session()`で同一データが取得できること
  - `delete_session()`でファイルが削除されること
  - 存在しないセッションIDで`load_session()`がNoneを返すこと（例外を発生させないこと）
  - `update_status()`でセッションステータスが更新されること

---

## タスク5: オーケストレーター用システムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計書.md`（2.3.1節: システムプロンプト全文）
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/07_skeleton_prompt_orchestrator.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_orchestrator.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_orchestrator.py`
- **実装内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT`定数（静的定数。申請種別判断ルール・処理フロー・禁止事項を含む全文）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT`が空でないこと
  - プロンプトに必須セクション（「役割」「申請種別判断ルール」「処理フロー」「禁止事項」）が含まれること
  - プロンプトに「BRL-01」キーワードが含まれること

---

## タスク6: 交通費精算申請エージェント用システムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計書.md`（2.3.1節: システムプロンプト全文・動的生成関数）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_transport.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_transport.py`
- **実装内容**:
  - `get_transport_system_prompt(applicant_name: str, application_date: str) -> str`関数
  - `application_date`をdateに変換し`deadline_date = application_date - timedelta(days=90)`を計算
  - `agent_knowledge/transportation_policies.py`を読み込んで`transportation_policies`変数に格納
  - `applicant_name`・`application_date`・`deadline_date`・`transportation_policies`をプロンプトテンプレートに埋め込み
  - 申請期限チェック（BRL-12）・一括収集指示・ツール呼び出しルール・禁止事項を含む全文
  - `__init__.py`の作成
- **単体テスト内容**:
  - `get_transport_system_prompt("山田太郎", "2026-05-06")`が空でないこと
  - 戻り値に`applicant_name`が含まれること
  - 戻り値に`application_date`が含まれること
  - 戻り値に`deadline_date`（申請日の90日前）が含まれること
  - 戻り値に`transportation_policies`の内容が含まれること

---

## タスク7: 経費精算申請エージェント用システムプロンプト

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計書.md`（2.3.1節: システムプロンプト全文・動的生成関数）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_expense.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_expense.py`
- **実装内容**:
  - `get_expense_system_prompt(applicant_name: str, application_date: str) -> str`関数
  - `application_date`をdateに変換し`deadline_date = application_date - timedelta(days=90)`を計算
  - `agent_knowledge/receipt_policies.py`を読み込んで`receipt_policies`変数に格納
  - `applicant_name`・`application_date`・`deadline_date`・`receipt_policies`をプロンプトテンプレートに埋め込み
  - 申請期限チェック（BRL-12）・一括収集指示・image_reader使用指示・TOOL-001禁止・禁止事項を含む全文
- **単体テスト内容**:
  - `get_expense_system_prompt("山田太郎", "2026-05-06")`が空でないこと
  - 戻り値に`applicant_name`が含まれること
  - 戻り値に`deadline_date`（申請日の90日前）が含まれること
  - 戻り値に`receipt_policies`の内容が含まれること
  - 戻り値に「TOOL-001」または「calculate_transport_fare」の禁止指示が含まれること

---

## タスク8: 交通費ポリシー定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計書.md`（2.3.1節: 妥当性チェックルール参照）
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/knowledge/transportation_policies.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transportation_policies.py`
- **実装内容**:
  - `TRANSPORTATION_POLICIES`定数（交通費申請の妥当性チェックルールを記述した文字列）
  - BRL-03（申請書チェック義務）・BRL-06（必須項目）・BRL-11（上長承認要否: 合計10,000円超）・BRL-12（申請期限: 90日以内）等のルールを含む
  - `get_transportation_policies() -> str`関数（定数を返す）
  - `__init__.py`の作成
- **単体テスト内容**:
  - `get_transportation_policies()`が空でないこと
  - 戻り値に上長承認基準（10,000円）に関する記述が含まれること
  - 戻り値に申請期限（90日）に関する記述が含まれること

---

## タスク9: 経費ポリシー定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計書.md`（2.3.1節: 妥当性チェックルール参照）
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/knowledge/receipt_policies.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_receipt_policies.py`
- **実装内容**:
  - `RECEIPT_POLICIES`定数（経費申請の妥当性チェックルールを記述した文字列）
  - BRL-03（申請書チェック義務）・BRL-07（必須項目）・BRL-12（申請期限: 90日以内）・BRL-17（経費区分自動判断）・BRL-18（上長承認要否: 5,000円超）等のルールを含む
  - `get_receipt_policies() -> str`関数（定数を返す）
- **単体テスト内容**:
  - `get_receipt_policies()`が空でないこと
  - 戻り値に上長承認基準（5,000円）に関する記述が含まれること
  - 戻り値に申請期限（90日）に関する記述が含まれること
  - 戻り値に経費区分（事務用品費/宿泊費/資格精算費/その他経費）に関する記述が含まれること

---

## タスク10: 交通費計算ツール

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（全章）
  - `artifacts/04_basic-design/outputs/データモデル基本設計書.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
  - `artifacts/03_system-design/outputs/バリデーション方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/transport_tools.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_tools.py`
- **実装内容**:
  - `load_fare_data(train_routes_path, fixed_fares_path) -> tuple`補助関数
    - os.path.exists()による事前チェック。失敗時は(False, エラーメッセージ文字列)を返す
  - モジュールレベル静的読み込み（`_railway_routes: list[dict]`, `_fixed_fares: dict[str, int]`）
  - `_error_handler = ErrorHandler()`モジュールレベル初期化
  - `@tool(context=True)`デコレータ付き`calculate_transport_fare`ツール関数
    - invocation_stateからapplicant_name・application_dateを取得
    - `FareCalculationInput`でバリデーション・正規化
    - 交通手段別分岐（電車: リスト線形探索 / バス・タクシー・飛行機: 固定運賃参照）
    - 戻り値: `{"success": bool, "fare": int, "calculation_method": str, "message": str}`
    - 例外を再送出せず必ず辞書を返す
  - `__init__.py`の作成
- **単体テスト内容**:
  - 電車区間（渋谷→新宿）でtrain_routes.jsonに存在する区間の運賃が正しく返ること
  - バスでfixed_fares.jsonの固定運賃（230円）が返ること
  - タクシーで10,000円が返ること
  - 飛行機で50,000円が返ること
  - `calculation_method`に「電車経路テーブル検索」または「固定運賃参照」が含まれること
  - DATA-009に存在しない電車区間で`success: False`が返ること（ValueError）
  - transport_typeに「新幹線」でValidationErrorに基づく日本語エラーメッセージが返ること
  - departure/destinationに空文字でValidationErrorメッセージが返ること
  - DATA-009が存在しない状態でload_fare_dataを呼んだとき`(False, エラーメッセージ)`が返ること
  - departure/destinationが500文字でバリデーション通過すること（境界値）
  - 「渋谷駅」→「渋谷」として正規化されて正しく検索されること

---

## タスク11: 申請書生成ツール

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（全章）
  - `artifacts/04_basic-design/outputs/データモデル基本設計書.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/output_generator.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_output_generator.py`
- **実装内容**:
  - `_error_handler = ErrorHandler()`モジュールレベル初期化
  - `@tool(context=True)`デコレータ付き`generate_transport_application`ツール関数
    - invocation_stateからapplicant_name・application_date・session_idを取得
    - `TransportApplicationData`でバリデーション（segmentsの必須キーガード含む）
    - 申請書IDとファイルパスの自律生成（`datetime.now().strftime('%Y%m%d%H%M%S')`ベース）
    - `data/output/{session_id}/`ディレクトリ自動作成
    - os.path.exists()によるテンプレート存在チェック
    - openpyxlでDATA-002テンプレート読み込み・A〜H列定義に従ったセルマッピング
    - Excelファイル保存（最大2回リトライ）
    - 監査ログ（audit.log）への記録
    - 戻り値: `{"success": bool, "file_path": str, "application_data": dict, "message": str}`
  - `@tool(context=True)`デコレータ付き`generate_expense_application`ツール関数
    - invocation_stateからapplicant_name・application_date・session_idを取得
    - `ExpenseApplicationData`でバリデーション（申請期限チェックBRL-12含む）
    - 申請書IDとファイルパスの自律生成
    - `data/output/{session_id}/`ディレクトリ自動作成
    - openpyxlでDATA-003テンプレート読み込み・A〜H列定義に従ったセルマッピング
    - Excelファイル保存（最大2回リトライ）
    - 監査ログへの記録
    - 戻り値: `{"success": bool, "file_path": str, "application_data": dict, "message": str}`
- **単体テスト内容**:
  - 正しい交通費申請情報でExcelファイルが生成され`success: True`が返ること（テンプレートファイルのモックを使用）
  - 正しい経費申請情報でExcelファイルが生成されること
  - DATA-002が存在しない場合、`success: False`とエラーメッセージが返ること
  - segmentsに必須キーが不足した辞書が含まれる場合、不足キー名を明示したエラーメッセージが返ること
  - `amount`に0でValidationErrorに基づく日本語エラーメッセージが返ること
  - 申請期限（90日）を超過したexpense_dateでValidationErrorが発生すること
  - ファイル書き込みが2回失敗した場合（IOErrorモック）、`success: False`が返ること
  - segments空リストで「移動区間情報のエラー」が返ること
  - invocation_stateからapplicant_name・application_date・session_idが正しく取得されること

---

## タスク12: オーケストレーターエージェント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/11_skeleton_orchestrator_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/orchestrator_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_orchestrator_agent.py`
- **実装内容**:
  - `OrchestratorAgent`クラス
  - `__init__(applicant_name: str)`: SessionManager初期化、session_id生成（`{タイムスタンプ}_{UUID8文字}`形式）、Agentインスタンス生成（ORCHESTRATOR_SYSTEM_PROMPT使用。LoopControlHookのみ）
  - `run()`: ウェルカムメッセージ表示、対話ループ、特殊コマンド（exit/quit/終了/reset/リセット/最初から）処理、入力バリデーション（空文字・500文字超）、invocation_state構築、エージェント呼び出し
  - `_validate_input(user_input: str) -> str | None`: 空文字→エラーメッセージ、500文字超→エラーメッセージ、正常→None
  - `_get_invocation_state() -> dict`: `{applicant_name, application_date, session_id}`辞書を返す
  - `transport_agent_tool`と`expense_agent_tool`の`@tool(context=True)`関数（各エージェントファイルから読み込み）
  - 例外処理: KeyboardInterrupt(break)/LoopLimitError(continue)/ContextWindowOverflowException(continue)/MaxTokensReachedException(continue)/RuntimeError(continue)/Exception(continue)の6種類
  - `__init__.py`の作成
- **単体テスト内容**:
  - `_validate_input("")`がエラーメッセージを返すこと（空文字バリデーション）
  - `_validate_input("a" * 501)`がエラーメッセージを返すこと（文字数超過バリデーション）
  - `_validate_input("正常な入力")`がNoneを返すこと
  - `_get_invocation_state()`がapplicant_name/application_date/session_idを含む辞書を返すこと
  - セッションIDが`{タイムスタンプ}_{UUID8文字}`形式であること

---

## タスク13: 交通費精算申請エージェント（transport_agent_tool）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/transport_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_agent.py`
- **実装内容**:
  - `_agent_instances: dict[str, Agent] = {}`モジュールレベルキャッシュ
  - `_error_handler = ErrorHandler()`モジュールレベル初期化
  - `@tool(context=True)`デコレータ付き`transport_agent_tool(query: str, tool_context: ToolContext) -> str`関数
    - invocation_stateからsession_id/applicant_name/application_dateを取得
    - session_id未登録時のみ新規Agentインスタンス生成（get_transport_system_promptを使用、HumanApprovalHook+LoopControlHookを登録、SessionManager、callback_handler=None）
    - `invocation_state`からsession_idを除外してagent呼び出し
    - 戻り値: str（AG-001に返す）
    - 例外処理: LoopLimitError(WARNING)/ContextWindowOverflowException(WARNING)/MaxTokensReachedException(WARNING)/RuntimeError(ERROR exc_info=True)/Exception(ERROR exc_info=True)の5種類。全てstr戻り値
- **単体テスト内容**:
  - `transport_agent_tool`が同じsession_idで呼び出された場合、Agentインスタンスが再利用されること（キャッシュ確認）
  - `LoopLimitError`発生時WARNINGログ出力後エラーメッセージstrが返ること（モック使用）
  - `Exception`発生時ERRORログ（exc_info=True）出力後エラーメッセージstrが返ること（モック使用）
  - invocation_stateにsession_idが含まれていないこと（子エージェントへの伝播確認）

---

## タスク14: 経費精算申請エージェント（expense_agent_tool）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/expense_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_agent.py`
- **実装内容**:
  - `_agent_instances: dict[str, Agent] = {}`モジュールレベルキャッシュ
  - `_error_handler = ErrorHandler()`モジュールレベル初期化
  - `@tool(context=True)`デコレータ付き`expense_agent_tool(query: str, tool_context: ToolContext) -> str`関数
    - invocation_stateからsession_id/applicant_name/application_dateを取得
    - session_id未登録時のみ新規Agentインスタンス生成（get_expense_system_promptを使用、image_reader追加、HumanApprovalHook+LoopControlHookを登録、SessionManager、callback_handler=None）
    - `invocation_state`からsession_idを除外してagent呼び出し
    - 戻り値: str（AG-001に返す）
    - 例外処理: LoopLimitError(WARNING)/ContextWindowOverflowException(WARNING)/MaxTokensReachedException(WARNING)/RuntimeError(ERROR exc_info=True)/Exception(ERROR exc_info=True)の5種類
- **単体テスト内容**:
  - `expense_agent_tool`が同じsession_idで呼び出された場合、Agentインスタンスが再利用されること（キャッシュ確認）
  - `LoopLimitError`発生時WARNINGログ出力後エラーメッセージstrが返ること（モック使用）
  - Agentのtoolsリストに`calculate_transport_fare`が含まれないこと（TOOL-001禁止確認）
  - invocation_stateにsession_idが含まれていないこと（子エージェントへの伝播確認）

---

## タスク15: メインエントリーポイント

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計書.md`（2.2.2節: ウェルカムメッセージ・入力プロンプト）
  - `artifacts/03_system-design/outputs/共通設定方針.md`
  - `artifacts/03_system-design/outputs/システム基本情報.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/13_skeleton_main.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/main.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_main.py`
- **実装内容**:
  - `load_dotenv()`による.envファイル読み込み
  - ログ設定（LOG_LEVELは環境変数で制御。フォーマット`%(asctime)s [%(levelname)s] %(name)s - %(message)s`）
  - ログファイル出力先: `logs/error.log`（UTF-8エンコーディング）
  - `warnings.filterwarnings("ignore")`
  - Strandsイベントループログレベル: CRITICAL（スタックトレース抑制）
  - `main()`関数: `OrchestratorAgent`生成・`run()`実行
  - `if __name__ == "__main__": main()`
  - テスト・設定ファイル:
    - `pytest.ini`の作成（testpaths, python_files, python_classes, python_functions設定）
    - `requirements.txt`の作成（strands-agents, strands-agents-tools, strands-agents-evals, boto3, pydantic, python-dotenv, python-dateutil, openpyxl, pytest, pytest-cov）
    - `tests/__init__.py`と`tests/unit/__init__.py`と`tests/integration/__init__.py`の作成
- **単体テスト内容**:
  - `main()`が例外を発生させずに実行できること（OrchestratorAgentをモック使用）
  - ログ設定が正しく適用されること

---

## タスク16: 静的データファイルのコピー配置

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（5.1節: DATA-009, 5.2節: DATA-010）
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（5.1節: DATA-002, 5.2節: DATA-003）
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/14_design_data_files.md`
- **成果物のファイルパス**:
  - `artifacts/06_code-generation/src/data/fixed_fares.json`（コピー元: `.claude/materials/06_code-generation/fixed_fares.json`）
  - `artifacts/06_code-generation/src/data/train_routes.json`（コピー元: `.claude/materials/06_code-generation/train_fares.json`）
  - `artifacts/06_code-generation/src/data/templates/交通費精算申請書テンプレート.xlsx`（コピー元: `.claude/materials/06_code-generation/交通費申請書_template.xlsx`）
  - `artifacts/06_code-generation/src/data/templates/経費精算申請書テンプレート.xlsx`（コピー元: `.claude/materials/06_code-generation/経費精算申請書_template.xlsx`）
  - `artifacts/06_code-generation/src/.gitignore`（コピー元: `.claude/materials/06_code-generation/.gitignore`）
  - `artifacts/06_code-generation/src/.env.template`（コピー元: `.claude/materials/06_code-generation/.env.template`）
- **単体テストコードのファイルパス**: なし（ファイルコピータスクのためテストコード不要）
- **実装内容**:
  - 上記ファイルを指定のコピー先にコピーする
  - `data/sessions/`, `data/output/`, `logs/`ディレクトリの作成（`.gitkeep`ファイル配置）
- **単体テスト内容**:
  - なし（ファイルコピーのため）

---

## タスク17: ガードレールCloudFormation定義

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ガードレール詳細設計書.md`（全章）
  - `artifacts/02_system-requirements/outputs/ガードレール要件定義.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/15_guardrails_cloudformation_yaml.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/guardrails/guardrails_cloudformation.yaml`
- **単体テストコードのファイルパス**: なし（YAMLファイルのためテストコード不要）
- **実装内容**:
  - ガードレール名: `expense-application-guardrail`
  - コンテンツフィルター: VIOLENCE/PROMPT_ATTACK/MISCONDUCT/HATE/SEXUAL/INSULTSのHIGH強度設定
  - 単語ポリシー: PROFANITY（BLOCK）
  - 機密情報ポリシー: PII（NAME/EMAIL/PHONE/ADDRESS/CREDIT_DEBIT_CARD_NUMBER/BANK_ACCOUNT_NUMBER）の入力/出力別アクション定義
  - ブロックメッセージ（入力ブロック時・出力ブロック時）の日本語メッセージ
- **単体テスト内容**:
  - なし（YAMLファイルのため）

---

## タスク18: 評価テスト - ツール選択精度（eval_tool_selection.py）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ツール選択精度・ゴール達成率評価テスト詳細設計書.md`（3章: 初期設定、4章: ログ設定、5章: テストケース定義TC-001〜005、6.2〜6.3節: シングルターン処理フロー、7.1節: main処理フロー）
  - `artifacts/03_system-design/outputs/評価テスト共通設計.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/16_eval_test.md`（シングルターン評価版）
- **成果物のファイルパス**: `artifacts/06_code-generation/src/evals/eval_tool_selection.py`
- **単体テストコードのファイルパス**: なし（評価テストスクリプト自体のためテストコード不要）
- **実装内容**:
  - UTF-8設定・sys.path設定・load_dotenv・patch_human_approval_hook（順序固定）
  - ログ設定（INFO, `evals/logs/eval_tool_selection.log`, UTF-8）
  - SDK ログ抑制（strands: WARNING, event_loop: CRITICAL）
  - `EVAL_CASES`: TC-001〜TC-005（5件）の`Case`オブジェクトリスト
    - TC-001: name=`"TC-001-transport-clear"`, input=`"タクシー代を精算したい"`, expected_tool=`"transport_agent_tool"`
    - TC-002: name=`"TC-002-transport-train"`, input=`"電車の交通費を申請したい"`, expected_tool=`"transport_agent_tool"`
    - TC-003: name=`"TC-003-expense-hotel"`, input=`"ホテルの宿泊費を精算したい"`, expected_tool=`"expense_agent_tool"`
    - TC-004: name=`"TC-004-expense-dining"`, input=`"取引先との会食費を申請したい"`, expected_tool=`"expense_agent_tool"`
    - TC-005: name=`"TC-005-expense-supplies"`, input=`"事務用品を購入したので申請したい"`, expected_tool=`"expense_agent_tool"`
  - `run_eval_task(case: Case) -> dict`: memory_exporter.clear() → create_reception_agent → create_invocation_state → シングルターン実行（agent(case.input, ...)） → スパン取得 → Session変換 → return
  - `main()`: ToolSelectionAccuracyEvaluatorでExperiment実行・JSONレポート保存（`evals/logs/eval_tool_selection_report.json`）
  - `evals/__init__.py`の作成
- **単体テスト内容**:
  - なし（評価スクリプトのため）

---

## タスク19: 評価テスト - ゴール達成率（eval_goal_success.py）

- **ステータス**: [x] 完了
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ツール選択精度・ゴール達成率評価テスト詳細設計書.md`（3章: 初期設定、4章: ログ設定、5.3節: テストケース定義TC-001〜003、6.4〜6.5節: マルチターン処理フロー、7.2節: main処理フロー）
  - `artifacts/03_system-design/outputs/評価テスト共通設計.md`
- **参照するスケルトンコード**: `.claude/skills/templates/06_code-generation/16_eval_test.md`（マルチターン評価版）
- **成果物のファイルパス**: `artifacts/06_code-generation/src/evals/eval_goal_success.py`
- **単体テストコードのファイルパス**: なし（評価テストスクリプト自体のためテストコード不要）
- **実装内容**:
  - UTF-8設定・sys.path設定・load_dotenv・patch_human_approval_hook（順序固定）
  - ログ設定（INFO, `evals/logs/eval_goal_success.log`, UTF-8）
  - SDK ログ抑制
  - `EVAL_CASES`: TC-001〜TC-003（3件）の`Case`オブジェクトリスト
    - TC-001: name=`"TC-001-transport-flow-success"`, input=`"交通費を精算したい。先週の出張で電車代がかかりました。"`, goal=`"チェック合格済みの交通費精算申請書..."`
    - TC-002: name=`"TC-002-expense-flow-success"`, input=`"先日の取引先との会食費を申請したいです。"`, goal=`"チェック合格済みの経費精算申請書..."`
    - TC-003: name=`"TC-003-expense-deadline-exceeded"`, input=`"半年前の事務用品購入費を申請したい"`, goal=`"申請期限（経費発生日から90日以内）を超過しているため申請が停止され..."`
  - `run_eval_task(case: Case) -> dict`: memory_exporter.clear() → create_reception_agent → create_invocation_state → マルチターン実行（run_actor_conversation） → スパン取得 → Session変換 → return
  - `main()`: GoalSuccessRateEvaluatorでExperiment実行・JSONレポート保存（`evals/logs/eval_goal_success_report.json`）
- **単体テスト内容**:
  - なし（評価スクリプトのため）

---

## タスク20: 結合テスト

- **ステータス**: [x] 完了
- **テスト対象**:
  - `transport_tools.calculate_transport_fare` + `models.data_models.FareCalculationInput`（モデルとツールの連携）
  - `output_generator.generate_transport_application` + `models.data_models.TransportApplicationData`（モデルとツールの連携）
  - `output_generator.generate_expense_application` + `models.data_models.ExpenseApplicationData`（モデルとツールの連携）
  - `handlers.error_handler.ErrorHandler` + `handlers.error_handler.LoopControlHook`（ハンドラー連携）
  - `handlers.error_handler.HumanApprovalHook` + `handlers.error_handler.LoopControlHook`（AG-002/AG-003でのフック併用）
  - `session.session_manager.SessionManager` + `agents.orchestrator_agent.OrchestratorAgent`（セッション管理とエージェントの連携）
- **結合テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/integration/test_agent_flow.py`
- **結合テスト内容**:
  - `calculate_transport_fare`が`FareCalculationInput`のバリデーション後に正しく運賃を返すこと（train_routes.jsonを使用した実際のファイル読み込みを含む）
  - `generate_transport_application`が`TransportApplicationData`バリデーション後にExcelファイルを生成すること（テンプレートファイルのモック使用）
  - `generate_expense_application`が`ExpenseApplicationData`バリデーション後にExcelファイルを生成すること
  - `HumanApprovalHook`と`LoopControlHook`が同じAgentに登録されたとき、BeforeToolCallEventでHumanApprovalHookが発火し、AfterModelCallEventでLoopControlHookのカウントが進むこと
  - `SessionManager`でセッションを作成後、`OrchestratorAgent`が同じsession_idを使用してセッションを管理できること
  - `ErrorHandler`の`handle_validation_error`がPydanticモデルのバリデーション失敗時に適切なメッセージを返すこと（実際のValidationErrorを使用）
