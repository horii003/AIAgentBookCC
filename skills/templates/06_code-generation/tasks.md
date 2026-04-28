# 実装タスク計画

> 本ファイルはコード生成フェーズ（06_code-generation）の実装タスク計画書です。
> 各タスクは依存関係順（スケルトンコード番号順）に記載しています。
> 単体テストが全件パスするまで各タスクを完了にしてはなりません。
> 共通参照: `skills/06-code-generation/SKILL.md`

---

## タスク01: データモデル定義

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（TravelExpenseCalculatorInput, TrainFareRecord, TRANSPORT_TYPE_MAP）
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（TravelApplicationFormInput, TravelItem, ExpenseApplicationFormInput, ExpenseItem, EXPENSE_CATEGORY_MAP, parse_amount）
  - `artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md`（UserInputText, invocation_state仕様）
  - `artifacts/04_basic-design/outputs/データモデル基本設計.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/01_skeleton_data_models.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/models/data_models.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_data_models.py`
- **実装内容**:
  - `InvocationState` TypedDict: session_id, applicant_name, application_date フィールド
  - `UserInputText` Pydanticモデル: min_length=1, max_length=500
  - `TrainFareRecord` Pydanticモデル: departure(min_length=1), destination(min_length=1), fare(ge=0)。validate_fare field_validator(mode="before")
  - `TRANSPORT_TYPE_MAP` 定数辞書: "train"/"鉄道"/"地下鉄"→"電車", "bus"→"バス", "taxi"/"cab"→"タクシー", "airplane"/"plane"→"飛行機"
  - `TravelExpenseCalculatorInput` Pydanticモデル: travel_date(parse_date validator→datetime.date), departure(min_length=1), destination(min_length=1), transport_type(normalize_transport_type validator→Literal["電車","バス","タクシー","飛行機"])
  - `TravelItem` Pydanticモデル: travel_date(str), departure(str), destination(str), transport_type(str), fare(int, ge=0), purpose(str)
  - `TravelApplicationFormInput` Pydanticモデル: applicant_name(str), application_date(str), items(list[TravelItem], min_length=1)
  - `ExpenseItem` Pydanticモデル: expense_date(str), category(str), amount(int, ge=0), purpose(str)
  - `ExpenseApplicationFormInput` Pydanticモデル: applicant_name(str), application_date(str), items(list[ExpenseItem], min_length=1)
  - `EXPENSE_CATEGORY_MAP` 定数辞書: "文房具"/"事務用品"/"消耗品"→"事務用品費", "ホテル"/"旅館"/"宿泊"→"宿泊費", "資格"/"検定"→"資格精算費", "その他"→"その他経費"
  - `parse_amount` ヘルパー関数: "1,000円" 等の文字列をintに変換
- **単体テスト内容**:
  - UserInputText: 正常値（1文字, 500文字）, min_length=1違反（空文字）, max_length=500違反（501文字）
  - TravelExpenseCalculatorInput: travel_date正常変換（YYYY-MM-DD）, parse_dateエラー（不正形式）, normalize_transport_type（"train"→"電車", "bus"→"バス", "taxi"→"タクシー", "airplane"→"飛行機", "cab"→"タクシー", "地下鉄"→"電車"）, transport_type不正値（"自転車"）, departure/destination空文字エラー, departure/destination空白のみエラー
  - TrainFareRecord: fare=0（正常）, fare負値エラー, departure/destination空文字エラー
  - TravelApplicationFormInput: 正常値, items空リストエラー
  - ExpenseApplicationFormInput: 正常値, items空リストエラー
  - parse_amount: "1,000円"→1000, "500"→500, カンマなし整数文字列→int

---

## タスク02: モデル設定

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/03_system-design/outputs/システム基本情報.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/02_skeleton_model_config.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/config/model_config.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_model_config.py`
- **実装内容**:
  - `DEFAULT_MODEL_ID` 定数: `"jp.anthropic.claude-sonnet-4-5-20250929-v1:0"`
  - `ModelConfig` クラス: `get_model()` クラスメソッド → `BedrockModel(model_id=DEFAULT_MODEL_ID)` を返す
  - `ModelRetryStrategy` 設定: max_attempts=6, initial_delay=4, max_delay=240
  - `get_model()` は `BedrockModel` に `ModelRetryStrategy` を設定して返す
- **単体テスト内容**:
  - `get_model()` が `BedrockModel` インスタンスを返すこと
  - `BedrockModel` の model_id が `DEFAULT_MODEL_ID` と一致すること
  - 返り値の型が BedrockModel であること

---

## タスク03: エラーハンドラー・例外クラス定義

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/ErrorHandler詳細設計書.md`
  - `artifacts/03_system-design/outputs/例外処理方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/03_skeleton_error_handler.md`
- **成果物のファイルパス**:
  - `artifacts/06_code-generation/src/handlers/error_handler.py`
  - `artifacts/06_code-generation/src/handlers/exceptions.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_error_handler.py`
- **実装内容**:
  - `handlers/exceptions.py`: `LoopLimitError(Exception)` クラス。__init__(self, current_iteration: int, max_iterations: int, agent_name: str)。current_iteration, max_iterations, agent_name インスタンス変数を持つ
  - `handlers/error_handler.py`: `ErrorHandler` クラス（インスタンス変数なし、__init__不要）
  - `ErrorHandler` 11メソッド（すべてロギングなし、メッセージ文字列を生成して返すのみ）:
    - `handle_throttling_error(e)` → スロットリングエラーメッセージ返却
    - `handle_max_tokens_error(e)` → 最大トークン数エラーメッセージ返却
    - `handle_context_window_error(e)` → コンテキストウィンドウエラーメッセージ返却
    - `handle_fare_data_error(message)` → 運賃データエラーメッセージ返却
    - `handle_calculation_error(e)` → 計算エラーメッセージ返却
    - `handle_file_save_error(e)` → ファイル保存エラーメッセージ返却
    - `handle_validation_error(e)` → バリデーションエラー詳細メッセージ返却
    - `handle_keyboard_interrupt()` → Ctrl+C終了メッセージ返却
    - `handle_loop_limit_error(e)` → `"処理が複雑すぎるため終了します。"` 返却
    - `handle_runtime_error(e)` → ランタイムエラーメッセージ返却
    - `handle_unexpected_error(e)` → `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"` 返却
  - **注意**: ErrorHandler 自身はログ出力を行わない。呼び出し元が ErrorHandler 呼び出し前にログを記録する
- **単体テスト内容**:
  - LoopLimitError: current_iteration=5, max_iterations=10, agent_name="test_agent" で生成し各フィールドが正しいこと
  - LoopLimitError が Exception のサブクラスであること
  - ErrorHandler.handle_loop_limit_error() が `"処理が複雑すぎるため終了します。"` を返すこと
  - ErrorHandler.handle_unexpected_error() が `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"` を返すこと
  - ErrorHandler.handle_validation_error() が ValidationError から生成したメッセージ文字列を返すこと（空でないこと）
  - ErrorHandler の各メソッドが文字列を返すこと（戻り値の型チェック）

---

## タスク04: LoopControlHook実装

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/LoopControlHook詳細設計書.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/04_skeleton_loop_control_hook.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/hooks.py`（LoopControlHook部分）
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_loop_control_hook.py`
- **実装内容**:
  - `handlers/hooks.py` に `LoopControlHook` クラスを実装（`HookProvider` プロトコル準拠）
  - `__init__(self, max_iterations: int = 10)`: max_iterations, _iteration_count=0 インスタンス変数
  - `register_hooks(self, registry: HookRegistry, **kwargs)`: 6イベントを登録
  - `_handle_before_invocation(event)`: _iteration_count=0 にリセット（INFOログ）
  - `_handle_before_model_call(event)`: 現在のイテレーション数をDEBUGログ
  - `_handle_after_model_call(event)`: event.exception が None の場合のみ `_increment_and_check(agent_name)` 呼び出し
  - `_handle_after_invocation(event)`: 総イテレーション数をINFOログ（カウンタリセットしない）
  - `_handle_before_tool_call(event)`: ツール名をDEBUGログ
  - `_handle_after_tool_call(event)`: ツール名をDEBUGログ
  - `_increment_and_check(agent_name)`: _iteration_count+=1、max_iterations超過時に `LoopLimitError(current_iteration, max_iterations, agent_name)` を送出
- **単体テスト内容**:
  - BeforeInvocationEvent発火で _iteration_count が 0 にリセットされること
  - AfterModelCallEvent発火（exception=None）で _iteration_count が 1 増加すること
  - AfterModelCallEvent発火（exception有り）で _iteration_count が増加しないこと
  - max_iterations=3 の場合、3回のAfterModelCallEvent後に LoopLimitError が送出されること
  - LoopLimitError の current_iteration と max_iterations が正しい値を持つこと
  - register_hooks が 6種のイベントを登録すること

---

## タスク05: HumanApprovalHook実装

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/HumanApprovalHook詳細設計書.md`
  - `artifacts/03_system-design/outputs/実行制御方針.md`
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/05_skeleton_human_approval_hook.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/handlers/hooks.py`（HumanApprovalHook部分をLoopControlHookと同ファイルに追記）
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_human_approval_hook.py`
- **実装内容**:
  - `handlers/hooks.py` に `HumanApprovalHook` クラスを追記（`HookProvider` プロトコル準拠）
  - `__init__(self)`: `_approval_tool_names = {"generate_travel_expense_form", "generate_expense_form"}` インスタンス変数
  - `register_hooks(self, registry: HookRegistry, **kwargs)`: BeforeToolCallEvent のみ登録
  - `_handle_before_tool_call(event)`: ツール名が `_approval_tool_names` 外ならスルー（INFOログ）。対象ツールなら `_request_approval(tool_name, event.tool_params)` 呼び出し
  - `_request_approval(tool_name, tool_params) → tuple[bool, str]`: "申請書を生成してよろしいですか？\nOK・修正・キャンセルのいずれかを入力してください。" を表示。strip().lower()で正規化。"ok"→(True,""), "修正"→修正内容入力→(False,修正内容), "キャンセル"→(False,"CANCEL")。不正入力は再入力促し。EOFError→(False,"CANCEL")
  - `_log_approval(tool_name, selection, timestamp)`: INFOレベルでDATA-009（tool_name, selection, timestamp）を `logs/error.log` に記録
  - ブロック解除: result==(True,"") → 何もしない
  - キャンセル: result[1]=="CANCEL" → `event.cancel_tool = "申請をキャンセルしました。"`
  - 修正: result[0]==False and result[1]!="CANCEL" → `event.cancel_tool = result[1]`
- **単体テスト内容**:
  - TOOL-001（calculate_travel_expense）でスルーされること（event.cancel_toolが設定されないこと）
  - TOOL-002（generate_travel_expense_form）でブロックされること
  - "ok"入力 → (True,"") が返り event.cancel_tool が設定されないこと
  - "修正"入力 → (False,"修正内容") が返り event.cancel_tool に修正内容がセットされること
  - "キャンセル"入力 → (False,"CANCEL") が返り event.cancel_tool="申請をキャンセルしました。" がセットされること
  - 無効入力後に"ok"入力 → 再入力プロセスが動作し最終的に(True,"") が返ること
  - EOFError → (False,"CANCEL") が返ること
  - register_hooks が BeforeToolCallEvent のみ登録すること

---

## タスク06: セッションマネージャー

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md`（セッションID生成方法, FileSessionManager設定）
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/06_skeleton_session_manager.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/session/session_manager.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_session_manager.py`
- **実装内容**:
  - `SessionManagerFactory` クラス
  - `generate_session_id() → str`: `datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]` 形式（例: `20260323153045_a1b2c3d4`）
  - `get_storage_dir() → str`: `"data/sessions/"` を返す
  - `create_session_manager(session_id: str) → FileSessionManager`: `FileSessionManager(session_id=session_id, storage_path="data/sessions/")` を返す
  - `get_session_path(session_id: str) → str`: セッションファイルの完全パスを返す（`data/sessions/{session_id}.json` 等）
- **単体テスト内容**:
  - generate_session_id() がパターン `\d{14}_[a-f0-9]{8}` に一致すること
  - 複数回呼び出しで異なるIDが生成されること（一意性確認）
  - get_storage_dir() が "data/sessions/" を返すこと
  - create_session_manager() が FileSessionManager インスタンスを返すこと

---

## タスク07: オーケストレータープロンプト

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md`（2.3.1節 プロンプト全文）
- **参照するスケルトンコード**: `skills/templates/06_code-generation/07_skeleton_prompt_orchestrator.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_orchestrator.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_orchestrator.py`
- **実装内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT` 定数（静的文字列）: AG-001詳細設計書 2.3.1節のプロンプト全文をそのまま定義
  - 動的生成不要（申請期限チェックはAG-002/AG-003が担当するため）
- **単体テスト内容**:
  - `ORCHESTRATOR_SYSTEM_PROMPT` が非空文字列であること
  - "travel_application_agent_tool" という文字列が含まれること
  - "expense_application_agent_tool" という文字列が含まれること
  - "BRL-01" または "申請種別" に関するキーワードが含まれること

---

## タスク08a: 交通費精算申請エージェントプロンプト

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md`（プロンプト設計章）
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_travel.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_travel.py`
- **実装内容**:
  - `build_travel_system_prompt(application_date: str) → str` 関数（Pattern B: 動的生成）
  - application_date から申請期限（application_date - 3ヶ月）を `relativedelta` で計算して deadline_date を生成
  - `agent_knowledge/transportation_policies.py` を `open()` でテキスト読み込みして transportation_policies として埋め込む
  - application_date, deadline_date, transportation_policies をプロンプト本文にf-string埋め込み
  - AG-002詳細設計書のプロンプト仕様に従ったシステムプロンプト文字列を返す
- **単体テスト内容**:
  - `build_travel_system_prompt("2026-04-28")` が文字列を返すこと
  - 返り値に application_date("2026-04-28") が含まれること
  - 返り値に deadline_date（3ヶ月前の日付）が含まれること
  - 返り値が非空文字列であること

---

## タスク08b: 経費精算申請エージェントプロンプト

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md`（プロンプト設計章）
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/prompt/prompt_expense.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_expense.py`
- **実装内容**:
  - `build_expense_system_prompt(application_date: str) → str` 関数（Pattern B: 動的生成）
  - application_date から申請期限（application_date - 3ヶ月）を `relativedelta` で計算して deadline_date を生成
  - `agent_knowledge/receipt_policies.py` を `open()` でテキスト読み込みして receipt_policies として埋め込む
  - application_date, deadline_date, receipt_policies をプロンプト本文にf-string埋め込み
  - AG-003詳細設計書のプロンプト仕様に従ったシステムプロンプト文字列を返す
- **単体テスト内容**:
  - `build_expense_system_prompt("2026-04-28")` が文字列を返すこと
  - 返り値に deadline_date（3ヶ月前の日付）が含まれること
  - 返り値が非空文字列であること

---

## タスク09a: 交通費ポリシー定義

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md`（業務ルール章・申請ルールチェック仕様）
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agent_knowledge/transportation_policies.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_transportation_policies.py`
- **実装内容**:
  - `TRANSPORTATION_POLICIES` 定数（文字列）: 交通費精算に関する業務ルール（BRL-13 申請期限, BRL-14 上長承認, BRL-08 差し戻しリスク, BRL-15 駅名正規化ルール, BRL-11 一括収集方針, BRL-12 自動計算優先等）をテキストで定義
  - AG-002のプロンプトに埋め込むためのエージェントナレッジとして整理
- **単体テスト内容**:
  - `TRANSPORTATION_POLICIES` が非空文字列であること
  - 申請期限に関するキーワードが含まれること（"申請期限" または "BRL-13"）
  - 上長承認に関するキーワードが含まれること（"上長" または "BRL-14"）

---

## タスク09b: 領収書ポリシー定義

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md`（業務ルール章）
  - `artifacts/02_system-requirements/outputs/業務ルール定義.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/09_skeleton_policies.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agent_knowledge/receipt_policies.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_receipt_policies.py`
- **実装内容**:
  - `RECEIPT_POLICIES` 定数（文字列）: 経費精算に関する業務ルール（BRL-16 経費申請期限, BRL-17 領収書要件, BRL-18 上限金額, BRL-19 禁止経費等）をテキストで定義
  - AG-003のプロンプトに埋め込むためのエージェントナレッジとして整理
- **単体テスト内容**:
  - `RECEIPT_POLICIES` が非空文字列であること
  - 領収書に関するキーワードが含まれること（"領収書" または "BRL-17"）

---

## タスク10a: 交通費計算ツール

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（全章）
  - `artifacts/04_basic-design/outputs/交通費計算ツール基本設計書.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/travel_tools.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_travel_tools.py`
- **実装内容**:
  - モジュールレベル変数: `_train_fares: list[TrainFareRecord] = []`, `_fixed_fares: dict[str, int] = {}`
  - `load_fare_data() → tuple[bool, str]`: アプリ起動時に1回呼び出す。`os.path.exists()` で事前チェック（FileNotFoundError捕捉との併用禁止）。train_routes.jsonをTrainFareRecordでバリデーション後 `_train_fares` に格納。fixed_fares.jsonを `_fixed_fares` に格納。成功時 `(True,"")`, 失敗時 `(False, エラーメッセージ)` を返す（例外を再送出しない）
  - `calculate_travel_expense` 関数: `@tool(context=True)` デコレーター。引数: travel_date, departure, destination, transport_type（`applicant_name`/`application_date` は引数に含めない、invocation_stateから取得）
  - `TravelExpenseCalculatorInput` でバリデーション。ValidationError → `{"success": False, "message": ...}` 返却
  - 電車: `_train_fares` から線形検索。未発見 → ValueError送出 → `{"success": False, "message": "指定された経路の運賃データが見つかりませんでした。交通費を手動で入力してください。"}` 返却
  - バス/タクシー/飛行機: `_fixed_fares` から取得
  - 成功: `{"success": True, "fare": int, "calculation_basis": str}` 返却
  - INFOログ（開始時・成功時）、ERRORログ（ValidationError・経路未発見）
  - データパス: `data/templates/train_routes.json`, `data/templates/fixed_fares.json`
- **単体テスト内容**:
  - load_fare_data(): train_routes.jsonが存在する場合に(True,"")を返すこと（テスト用モックデータ使用）
  - load_fare_data(): train_routes.jsonが存在しない場合に(False, エラーメッセージ)を返すこと
  - calculate_travel_expense(): 電車区間（DATA-011に存在する経路）でsuccess=True, 正しいfare, calculation_basis="電車経路テーブル参照"を返すこと
  - calculate_travel_expense(): バスでsuccess=True, fare=230, calculation_basis="固定運賃参照"を返すこと
  - calculate_travel_expense(): タクシーでsuccess=True, fare=10000を返すこと
  - calculate_travel_expense(): 飛行機でsuccess=True, fare=50000を返すこと
  - calculate_travel_expense(): transport_type="train"が正規化されて電車処理されること
  - calculate_travel_expense(): 存在しない電車区間でsuccess=False, メッセージが返ること
  - calculate_travel_expense(): transport_type="自転車"でsuccess=Falseが返ること
  - calculate_travel_expense(): departure=""でsuccess=Falseが返ること
  - calculate_travel_expense(): travel_date不正形式でsuccess=Falseが返ること

---

## タスク10b: 申請書生成ツール

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（全章）
  - `artifacts/04_basic-design/outputs/申請書生成ツール基本設計書.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/10_skeleton_tools.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/tools/output_generator.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_output_generator.py`
- **実装内容**:
  - `generate_travel_expense_form` 関数: `@tool(context=True)` デコレーター。invocation_stateからapplicant_name, application_date, session_idを取得
  - テンプレートパス: `data/templates/交通費申請書_template.xlsx`。出力先: `data/output/{session_id}/交通費精算申請書_{timestamp}.xlsx`
  - openpyxl でテンプレートを開き、B3=申請者名, B4=申請日。行7+i に各移動区間（A=No, B=移動日, C=出発地, D=目的地, E=交通手段, F=金額, G=業務目的, H=空白）。合計金額を最終行+2のH列に記入
  - `TravelApplicationFormInput` でバリデーション。ValidationError → `{"success": False, "message": ...}` 返却
  - 成功: `{"success": True, "file_path": str, "total_fare": int}` 返却
  - `generate_expense_form` 関数: `@tool(context=True)` デコレーター。同様の構造
  - テンプレートパス: `data/templates/経費精算申請書_template.xlsx`。出力先: `data/output/{session_id}/経費精算申請書_{timestamp}.xlsx`
  - `EXPENSE_CATEGORY_MAP` でカテゴリー正規化
  - `ExpenseApplicationFormInput` でバリデーション
  - 成功: `{"success": True, "file_path": str, "total_amount": int}` 返却
  - `data/output/{session_id}/` ディレクトリを `os.makedirs(..., exist_ok=True)` で自動生成
- **単体テスト内容**:
  - generate_travel_expense_form(): 正常データ（2区間）でsuccess=True, file_pathが返ること（モックopenpyxl使用）
  - generate_travel_expense_form(): テンプレートファイルが存在しない場合にsuccess=Falseが返ること
  - generate_travel_expense_form(): バリデーションエラー（items空リスト）でsuccess=Falseが返ること
  - generate_expense_form(): 正常データでsuccess=True, file_pathが返ること
  - generate_expense_form(): EXPENSE_CATEGORY_MAP変換（"文房具"→"事務用品費"）が正しく行われること
  - 出力ファイルのファイル名フォーマット（タイムスタンプ含む）が正しいこと

---

## タスク11: オーケストレーターエージェント

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/11_skeleton_orchestrator_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/orchestrator_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_orchestrator_agent.py`
- **実装内容**:
  - `create_orchestrator_agent(session_id, applicant_name, application_date) → Agent` ファクトリ関数
  - FileSessionManager(session_id=session_id, storage_path="data/sessions/") 生成
  - Agent 生成: system_prompt=ORCHESTRATOR_SYSTEM_PROMPT（静的定数）, tools=[travel_application_agent_tool, expense_application_agent_tool], conversation_manager=SlidingWindowConversationManager(window_size=30, should_truncate_results=True, per_turn=False), hooks=[LoopControlHook(max_iterations=10)], callback_handler省略（デフォルト）, session_manager=FileSessionManager
  - HumanApprovalHook は AG-001 に登録しない
  - `main()` 関数: ウェルカムメッセージ表示（起動時1回のみ）。申請者名ループ収集（空文字は再促し）。application_date=datetime.date.today().isoformat()。session_id生成。FileSessionManager・Agentインスタンス生成。対話ループ: `input("\n\n入力内容（終了時はquit）: ")`でユーザー入力取得。"exit"/"quit"でbreak。"reset"/"リセット"/"最初から"でAgent再生成・申請者名再収集。UserInputTextバリデーション失敗→エラーメッセージ表示・continue。agent(user_input, invocation_state={session_id, applicant_name, application_date})呼び出し
  - 例外ハンドリング（6種): KeyboardInterrupt(INFO,break), LoopLimitError(WARNING,continue), ContextWindowOverflowException(WARNING,continue), MaxTokensReachedException(WARNING,continue), RuntimeError(ERROR,exc_info=True,continue), Exception(ERROR,exc_info=True,continue)
  - 全例外ログにsession_idを付加。全例外でErrorHandlerを呼び出しprint()でメッセージ表示
- **単体テスト内容**:
  - create_orchestrator_agent() が Agent インスタンスを返すこと（モック使用）
  - Agent生成時のtools=[travel_application_agent_tool, expense_application_agent_tool] が設定されること
  - SlidingWindowConversationManager(window_size=30) が設定されること
  - hooks に HumanApprovalHook が含まれないこと
  - hooks に LoopControlHook(max_iterations=10) が含まれること

---

## タスク12a: 交通費精算申請エージェント

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-002_交通費精算申請エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/travel_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_travel_agent.py`
- **実装内容**:
  - `_agent_instances: dict[str, Agent] = {}` モジュールレベルキャッシュ
  - `_get_travel_agent(session_id, applicant_name, application_date) → Agent` ファクトリ関数（プライベート）
  - Agent生成: system_prompt=build_travel_system_prompt(application_date), tools=[calculate_travel_expense, generate_travel_expense_form], model=get_model(), conversation_manager=SlidingWindowConversationManager(window_size=20, should_truncate_results=True, per_turn=False), hooks=[HumanApprovalHook(), LoopControlHook(max_iterations=10)], callback_handler=None, session_manager=FileSessionManager(session_id=session_id, storage_path="data/sessions/")
  - `_agent_instances[session_id]` にキャッシュ（セッション内再利用）
  - `travel_application_agent_tool` 関数: `@tool(context=True)` デコレーター。ToolContextから session_id, applicant_name, application_date を取得。`_get_travel_agent(...)` でエージェント取得。`agent(query, invocation_state={session_id, applicant_name, application_date})` 呼び出し
  - 例外ハンドリング（5種): LoopLimitError(WARNING), ContextWindowOverflowException(WARNING), MaxTokensReachedException(WARNING), RuntimeError(ERROR,exc_info=True), Exception(ERROR,exc_info=True)
  - ログメッセージに `query[:50]` と `session_id` を含める
- **単体テスト内容**:
  - _get_travel_agent() が Agent インスタンスを返すこと（モック使用）
  - SlidingWindowConversationManager(window_size=20) が設定されること
  - tools に calculate_travel_expense と generate_travel_expense_form が含まれること
  - hooks に HumanApprovalHook と LoopControlHook が含まれること
  - callback_handler=None が設定されること
  - _agent_instances キャッシュ: 同一session_idで2回呼び出すと同じインスタンスが返ること

---

## タスク12b: 経費精算申請エージェント

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-003_経費精算申請エージェント詳細設計書.md`（全章）
  - `artifacts/03_system-design/outputs/マルチエージェント連携設計.md`
  - `artifacts/03_system-design/outputs/セッション管理方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/12_skeleton_specialist_agent.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/agents/expense_agent.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_agent.py`
- **実装内容**:
  - `_agent_instances: dict[str, Agent] = {}` モジュールレベルキャッシュ
  - `_get_expense_agent(session_id, applicant_name, application_date) → Agent` ファクトリ関数
  - Agent生成: system_prompt=build_expense_system_prompt(application_date), tools=[generate_expense_form]（TOOL-001は含めない）, model=get_model(), conversation_manager=SlidingWindowConversationManager(window_size=15, should_truncate_results=True, per_turn=False), hooks=[HumanApprovalHook(), LoopControlHook(max_iterations=10)], callback_handler=None, session_manager=FileSessionManager(session_id=session_id, storage_path="data/sessions/")
  - `expense_application_agent_tool` 関数: `@tool(context=True)` デコレーター。travel_application_agent_toolと同パターン
  - 例外ハンドリング（5種）: travel_agentと同様
- **単体テスト内容**:
  - _get_expense_agent() が Agent インスタンスを返すこと
  - SlidingWindowConversationManager(window_size=15) が設定されること（AG-002の20ではなく15）
  - tools に generate_expense_form のみが含まれること（calculate_travel_expense が含まれないこと）
  - hooks に HumanApprovalHook と LoopControlHook が含まれること
  - callback_handler=None が設定されること

---

## タスク13: アプリケーションエントリーポイント

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/AG-001_申請受付窓口エージェント詳細設計書.md`（3.1.1節 main関数）
  - `artifacts/03_system-design/outputs/共通設定方針.md`
- **参照するスケルトンコード**: `skills/templates/06_code-generation/13_skeleton_main.md`
- **成果物のファイルパス**: `artifacts/06_code-generation/src/main.py`
- **単体テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/unit/test_main.py`
- **実装内容**:
  - `load_dotenv()` でenv読み込み
  - ロギング設定: `logs/` ディレクトリへの出力, ファイルハンドラー（`logs/error.log`）とコンソールハンドラー設定, ログレベル設定
  - `load_fare_data()` 呼び出し: 失敗（`(False, msg)`）の場合はエラーメッセージ表示してアプリ起動を中断（sys.exit or return）
  - `os.makedirs(f"data/output/{session_id}", exist_ok=True)` でセッション別出力ディレクトリ生成
  - `main()` 関数: `agents/orchestrator_agent.py` の main() を呼び出すか、または直接メインロジックを持つ
  - `if __name__ == "__main__": main()` エントリーポイント
- **単体テスト内容**:
  - main.pyがimport可能であること（構文エラーなし）
  - load_fare_data()失敗時にアプリが起動中断すること（モック使用）
  - loggingの設定が正しく初期化されること

---

## タスク14: データファイルおよび資材配置

- **ステータス**: [ ] 未着手
- **参照する設計書**:
  - `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計書.md`（4章 データ設計）
  - `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計書.md`（データ設計章）
- **参照するスケルトンコード**: `skills/templates/06_code-generation/14_design_data_files.md`
- **成果物のファイルパス**:
  - `artifacts/06_code-generation/src/data/templates/train_routes.json`（materials/06_code-generation/train_fares.json をコピー・リネーム）
  - `artifacts/06_code-generation/src/data/templates/fixed_fares.json`（materials/06_code-generation/fixed_fares.json をコピー）
  - `artifacts/06_code-generation/src/data/templates/交通費精算申請書テンプレート.xlsx`（materials/06_code-generation/交通費申請書_template.xlsx をコピー・リネーム）
  - `artifacts/06_code-generation/src/data/templates/経費精算申請書テンプレート.xlsx`（materials/06_code-generation/経費精算申請書_template.xlsx をコピー・リネーム）
  - `artifacts/06_code-generation/src/.gitignore`（materials/06_code-generation/.gitignore をコピー）
  - `artifacts/06_code-generation/.env.template`（materials/06_code-generation/.env.template をコピー）
- **単体テストコードのファイルパス**: なし（ファイル配置タスクのため単体テスト不要）
- **実装内容**:
  - `artifacts/06_code-generation/src/data/templates/` ディレクトリを作成
  - `artifacts/06_code-generation/src/data/` ディレクトリを作成（固定運賃・経路データは templates/ 配下に配置）
  - materials/06_code-generation/train_fares.json → src/data/templates/train_routes.json にコピー（ファイル名変更）
  - materials/06_code-generation/fixed_fares.json → src/data/templates/fixed_fares.json にコピー
  - materials/06_code-generation/交通費申請書_template.xlsx → src/data/templates/交通費精算申請書テンプレート.xlsx にコピー（ファイル名変更）
  - materials/06_code-generation/経費精算申請書_template.xlsx → src/data/templates/経費精算申請書テンプレート.xlsx にコピー（ファイル名変更）
  - materials/06_code-generation/.gitignore → src/.gitignore にコピー
  - materials/06_code-generation/.env.template → artifacts/06_code-generation/.env.template にコピー
  - `artifacts/06_code-generation/src/data/output/` ディレクトリ（セッション別出力先、.gitkeep等で構造定義）
  - `artifacts/06_code-generation/src/data/sessions/` ディレクトリ（セッション管理用、.gitkeep等で構造定義）
  - `artifacts/06_code-generation/src/logs/` ディレクトリ（ログ出力先、.gitkeep等で構造定義）
- **単体テスト内容**:
  - 単体テスト不要（ファイル配置タスク）

---

## タスク15: 結合テスト

- **ステータス**: [ ] 未着手
- **テスト対象**:
  - AG-001 → AG-002 → TOOL-001 → TOOL-002 の連携フロー（交通費精算申請）
  - AG-001 → AG-003 → TOOL-002 の連携フロー（経費精算申請）
  - HumanApprovalHook によるTOOL-002実行前ブロック
  - LoopControlHook による最大イテレーション制御
  - load_fare_data() → calculate_travel_expense → generate_travel_expense_form の一連フロー
  - invocation_state の各エージェントへの正しい伝播
- **結合テストコードのファイルパス**: `artifacts/06_code-generation/src/tests/integration/test_agent_integration.py`
- **結合テスト内容**:
  - load_fare_data()が正常完了し、_train_fares/_fixed_faresに正しくデータが読み込まれること
  - calculate_travel_expense()でDATA-011の既存経路（例: "渋谷"→"新宿"）の運賃が正しく返ること
  - generate_travel_expense_form()で正常データから `data/output/{session_id}/交通費精算申請書_*.xlsx` が生成されること
  - generate_expense_form()で正常データから `data/output/{session_id}/経費精算申請書_*.xlsx` が生成されること
  - HumanApprovalHook: "ok"入力でTOOL-002が実行されること（モック標準入力使用）
  - HumanApprovalHook: "キャンセル"入力でTOOL-002がキャンセルされ `event.cancel_tool` が設定されること
  - LoopControlHook: max_iterations超過時にLoopLimitErrorが送出されること
  - ErrorHandler: 各エラー種別のメッセージが正しく生成されること
  - invocation_state: session_id, applicant_name, application_dateがTOOL-001・TOOL-002でToolContext経由で正しく取得できること
