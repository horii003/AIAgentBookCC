# 実装タスク計画

> 06_code-generation フェーズの実装タスク一覧。
> セッション開始時にこのファイルを読み込み、`✅ 完了` のタスクは再実行しない。
> 各タスク完了後に該当行を `🔄 作業中` → `✅ 完了` に更新する。

---

## タスク進捗サマリー

| # | タスクID | 成果物 | 状態 |
|---|----------|--------|------|
| 1 | TASK-01 | `src/models/data_models.py` + テスト | 🔲 未着手 |
| 2 | TASK-02 | `src/config/model_config.py` + テスト | 🔲 未着手 |
| 3 | TASK-03 | `src/config/settings.py` + テスト | 🔲 未着手 |
| 4 | TASK-04 | `src/handlers/error_handler.py` + テスト | 🔲 未着手 |
| 5 | TASK-05 | `src/handlers/loop_control_hook.py` + テスト | 🔲 未着手 |
| 6 | TASK-06 | `src/handlers/human_approval_hook.py` + テスト | 🔲 未着手 |
| 7 | TASK-07 | `src/session/session_manager.py` + テスト | 🔲 未着手 |
| 8 | TASK-08 | `src/prompt/prompt_orchestrator.py` + テスト | 🔲 未着手 |
| 9 | TASK-09a | `src/prompt/prompt_transport.py` + テスト | 🔲 未着手 |
| 10 | TASK-09b | `src/prompt/prompt_expense.py` + テスト | 🔲 未着手 |
| 11 | TASK-10a | `src/agent_knowledge/transport_policies.py` + テスト | 🔲 未着手 |
| 12 | TASK-10b | `src/agent_knowledge/expense_policies.py` + テスト | 🔲 未着手 |
| 13 | TASK-11a | `src/tools/transport_tools.py` + テスト | 🔲 未着手 |
| 14 | TASK-11b | `src/tools/form_generator.py` + テスト | 🔲 未着手 |
| 15 | TASK-12 | `src/agents/orchestrator_agent.py` + テスト | 🔲 未着手 |
| 16 | TASK-13a | `src/agents/transport_agent.py` + テスト | 🔲 未着手 |
| 17 | TASK-13b | `src/agents/expense_agent.py` + テスト | 🔲 未着手 |
| 18 | TASK-14 | `src/main.py` + テスト | 🔲 未着手 |
| 19 | TASK-15 | `src/requirements.txt` | 🔲 未着手 |
| 20 | TASK-16 | `src/config/guardrails_cloudformation.yaml` | 🔲 未着手 |
| 21 | TASK-17a | `src/evals/eval_tool_selection.py` | 🔲 未着手 |
| 22 | TASK-17b | `src/evals/eval_goal_success_rate.py` | 🔲 未着手 |
| 23 | TASK-18 | 資材ファイルコピー | 🔲 未着手 |
| 24 | TASK-19 | `__init__.py` 一式 | 🔲 未着手 |
| 25 | TASK-20 | 結合テスト | 🔲 未着手 |
| 26 | TASK-21 | E2Eテスト | 🔲 未着手 |

---

## TASK-01: データモデル定義

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/01_skeleton_data_models.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md` §3.3.3, §5.2（TransportToolInput, TrainRouteMaster等）
- `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計.md` §5.2（TransportFormInput, ExpenseFormInput等）
- `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md` §4.2, §4.3
- `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md` §4.2, §4.3

**成果物パス**: `artifacts/06_code-generation/src/models/data_models.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_data_models.py`

**実装内容**:
- Pydantic v2 (`BaseModel`) を使用した11モデルを実装
- `TransportToolInput`: 交通費計算ツール入力バリデーション
  - `field_validator(mode="before")`: `normalize_station_name`（駅名接尾語除去）、`normalize_transportation_type`（交通手段正規化）、`strip_and_validate_not_empty`（purpose空文字禁止）
  - `model_validator(mode="after")`: `check_application_deadline`（90日超過チェック BRL-14）
  - `ConfigDict(strict=False)` で自動型変換を許容
  - `travel_date`: `date`型（文字列→date自動変換、未来日付禁止）
- `TrainRouteEntry`: `departure: str`, `destination: str`, `fare: int(ge=0)`
- `TrainRouteMaster`: `routes: list[TrainRouteEntry]`
- `FixedFareEntry`: `transportation_type: Literal["バス","タクシー","飛行機"]`, `fare: int(ge=0)`
- `FixedFareMaster`: `entries: list[FixedFareEntry]`
- `TransportSegment`: `travel_date: str`, `departure: str`, `destination: str`, `transportation_type: str`, `amount: int(ge=0)`, `purpose: str`
- `TransportFormInput`: `applicant_name: str`, `application_date: str`, `segments: list[TransportSegment]`
- `ExpenseItem`: `expense_date: str`, `store_name: str`, `amount: int(ge=0)`, `item_name: str`, `expense_category: Literal["事務用品費","宿泊費","資格精算費","その他経費"]`, `purpose: str`
- `ExpenseFormInput`: `applicant_name: str`, `application_date: str`, `items: list[ExpenseItem]`
- `InvocationState`: `session_id: str`, `applicant_name: str`, `application_date: str`

**交通手段正規化マッピング**:
- 「JR」「新幹線」「地下鉄」「モノレール」→「電車」
- 「ハイヤー」「タクシー代」→「タクシー」
- 「飛機」「航空」「ANA」「JAL」→「飛行機」
- 「路線バス」→「バス」

**テスト内容**:
- `TransportToolInput` バリデーション：正常系（全パラメータ正常入力）
- 駅名正規化：「渋谷駅」→「渋谷」、「Shibuya Station」→「Shibuya」
- 交通手段正規化：「JR」→「電車」、「ハイヤー」→「タクシー」
- 未来日付禁止：`travel_date`に翌日の日付を指定 → `ValidationError`
- 90日超過チェック：91日前の日付 → `ValidationError`
- 境界値：90日前の日付 → 正常（`ValidationError` なし）
- `purpose` 空文字禁止：`purpose=""` → `ValidationError`
- `FixedFareEntry` 異常：`fare=-1` → `ValidationError`

---

## TASK-02: モデル設定

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/02_skeleton_model_config.md`

**参照設計書**:
- `artifacts/03_system-design/outputs/共通設定方針.md` §3（BedrockModel設定）
- `artifacts/03_system-design/outputs/実行制御方針.md` §6.1（リトライ戦略）

**成果物パス**: `artifacts/06_code-generation/src/config/model_config.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_model_config.py`

**実装内容**:
- `BedrockModel` インスタンスを返すファクトリ関数 `get_bedrock_model()` を実装
- モデルID: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0`
- `ModelRetryStrategy`: `max_attempts=6`, `initial_delay=4`, `max_delay=240`（指数バックオフ）
- AWS リージョン・認証情報は環境変数（`.env`）から `python-dotenv` 経由で読み込む
  - `AWS_REGION`: デフォルト `ap-northeast-1`
  - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`

**テスト内容**:
- `get_bedrock_model()` が `BedrockModel` インスタンスを返すこと
- モデルIDが期待値と一致すること
- `ModelRetryStrategy` の `max_attempts=6` が設定されていること

---

## TASK-03: 設定値（settings.py）

**状態**: 🔲 未着手

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md` §9.1（ファイルパス定数）
- `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計.md` §9.1（テンプレートパス）

**成果物パス**: `artifacts/06_code-generation/src/config/settings.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_settings.py`

**実装内容**:
- ファイルパス定数を定義（Pathlib または文字列定数）:
  - `TRAIN_ROUTES_PATH = "data/train_routes.json"`
  - `FIXED_FARES_PATH = "data/fixed_fares.json"`
  - `TRANSPORT_TEMPLATE_PATH = "data/templates/交通費精算申請書テンプレート.xlsx"`
  - `EXPENSE_TEMPLATE_PATH = "data/templates/経費精算申請書テンプレート.xlsx"`
  - `OUTPUT_DIR = "data/output"`
  - `SESSION_DIR = "data/sessions"`

**テスト内容**:
- 各定数が文字列型であること
- パスが期待値と一致すること

---

## TASK-04: エラーハンドラー

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/03_skeleton_error_handler.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/ErrorHandler詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/handlers/error_handler.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_error_handler.py`

**実装内容**:
- `ErrorHandler` クラス（完全ステートレス、インスタンス変数なし）
- 11の `handle_xxx` メソッドを実装:
  - `handle_throttling_error(e)` → "申し訳ありません。現在システムが混雑しています。しばらく経ってから再度お試しください。"
  - `handle_max_tokens_error(e)` → "申し訳ありません。入力内容が長すぎます。内容を短くして再度お試しください。"
  - `handle_context_window_error(e)` → "申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"
  - `handle_fare_data_error(e)` → "申し訳ありません。運賃データの読み込みに失敗しました。担当部門（管理部）にお問い合わせください。"
  - `handle_calculation_error(e)` → "申し訳ありません。運賃計算中にエラーが発生しました。区間情報を確認して再度お試しください。"
  - `handle_file_save_error(e)` → "申し訳ありません。申請書の保存に失敗しました。担当部門（管理部）にお問い合わせください。"
  - `handle_validation_error(e)` → str(e) に「90日」または「申請期限」が含まれる場合は EX-03 メッセージ、それ以外は EX-01 メッセージ
  - `handle_keyboard_interrupt(e)` → "申請フローを中断しました。またいつでもご利用ください。"
  - `handle_loop_limit_error(e)` → "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
  - `handle_runtime_error(e)` → "申し訳ありません。システムエラーが発生しました。しばらく経ってから再度お試しください。"
  - `handle_unexpected_error(e)` → "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
- ロギングは行わない（ステートレス設計）

**テスト内容**:
- 各 `handle_xxx` メソッドが期待するメッセージ文字列を返すこと
- `handle_validation_error`: str(e) に「90日」を含む場合は EX-03 メッセージ、含まない場合は EX-01 メッセージが返ること
- `handle_validation_error`: str(e) に「申請期限」を含む場合は EX-03 メッセージが返ること

---

## TASK-05: LoopControlHook

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/04_skeleton_loop_control_hook.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/LoopControlHook詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/handlers/loop_control_hook.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_loop_control_hook.py`

**実装内容**:
- `LoopLimitError(RuntimeError)` クラスを定義（このファイルで定義、error_handler.py では定義しない）:
  - `__init__(self, current_iteration: int, max_iterations: int, agent_name: str = "")`:
    - `self.current_iteration = current_iteration`
    - `self.max_iterations = max_iterations`
    - `self.agent_name = agent_name`
- `LoopControlHook(HookProvider)` クラス:
  - `__init__(self, max_iterations: int = 10)`: `self._max_iterations = max_iterations`, `self._iteration_count = 0`
  - `register_hooks(self, registry, **kwargs)`: 6イベント登録
    - `BeforeInvocationEvent`: `on_before_invocation` → `_iteration_count = 0` リセット
    - `BeforeModelCallEvent`: `on_before_model_call` → カウントアップ（`_iteration_count += 1`）、上限超過時に `LoopLimitError` raise
    - `AfterModelCallEvent`: `on_after_model_call` → `event.exception` がある場合はカウントをデクリメント（スキップ）
    - `BeforeToolCallEvent`: `on_before_tool_call` → OPE-001 ログ出力
    - `AfterToolCallEvent`: `on_after_tool_call` → OPE-001 ログ出力（完了）
    - `AfterInvocationEvent`: `on_after_invocation` → OPE-001 ログ出力（完了）

**テスト内容**:
- `max_iterations=3` で4回 `on_before_model_call` を呼んだ場合に `LoopLimitError` が raise されること
- `on_before_invocation` 後に `_iteration_count` が 0 にリセットされること
- `AfterModelCallEvent` で `event.exception` がある場合はカウントがインクリメントされないこと
- `LoopLimitError` の `current_iteration`, `max_iterations`, `agent_name` 属性が正しいこと

---

## TASK-06: HumanApprovalHook

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/05_skeleton_human_approval_hook.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/HumanApprovalHook詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/handlers/human_approval_hook.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_human_approval_hook.py`

**実装内容**:
- `HumanApprovalHook(HookProvider)` クラス:
  - `__init__(self, approval_callback: Callable[[str, dict], tuple[bool, str]])`: コールバック注入
  - 承認対象ツール: `{"generate_transport_expense_form", "generate_expense_reimbursement_form"}`
  - `on_before_tool_call(self, event: BeforeToolCallEvent)`:
    1. `event.tool_name` が承認対象か確認
    2. 対象外は即 return
    3. `event.agent.context.invocation_state.get("applicant_name", "")` を取得
    4. `_build_confirmation_message(event, applicant_name)` で確認メッセージ生成
    5. `approval_callback(event.tool_name, {"confirmation_message": msg, "tool_params": event.tool_input})` で承認結果取得
    6. OPE-003 ログ出力
    7. 承認(True): `_log_audit(event, "OK")`、処理継続
    8. 非承認(False): `_log_audit(event, message)`、`event.cancel_tool(message)` でツール中止
  - `_build_confirmation_message(event, applicant_name)`: ツール名に応じた確認メッセージ生成
  - `_log_audit(event, result)`: AUD-004 ログ出力（`applicant_name[:1] + "***"` でマスキング）
- `patch_human_approval_hook(auto_approve: bool = True)` 関数:
  - テスト・評価用のモック差し替え関数
  - `auto_approve=True` の場合、常に `(True, "OK")` を返すコールバックを設定
  - `human_approval_hook` モジュールの `approval_callback` グローバル変数を差し替える

**テスト内容**:
- 対象ツール(`generate_transport_expense_form`)で `approval_callback=(True, "OK")` を返す場合、`event.cancel_tool` が呼ばれないこと
- 対象ツールで `approval_callback=(False, "修正")` を返す場合、`event.cancel_tool` が呼ばれること
- 対象外ツール(`calculate_transport_fare`)では介入しないこと（`approval_callback` が呼ばれないこと）
- AUD-004 ログで `applicant_name` が `"田***"` のようにマスキングされること
- `patch_human_approval_hook()` 呼び出し後に自動承認されること

---

## TASK-07: セッション管理

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/06_skeleton_session_manager.md`

**参照設計書**:
- `artifacts/04_basic-design/outputs/セッション管理基本設計書.md`（全章）
- `artifacts/03_system-design/outputs/セッション管理方針.md`

**成果物パス**: `artifacts/06_code-generation/src/session/session_manager.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_session_manager.py`

**実装内容**:
- `SessionState` Enum: `CREATED`, `ACTIVE`, `WAITING`, `CLOSED`, `TERMINATED`
- `SessionData` dataclass または Pydantic モデル: `session_id`, `status`, `applicant_name`, `application_date`, `created_at`, `updated_at`
- `FileBasedSessionManager` クラス:
  - `__init__(self, storage_path: str = "data/sessions")`: ストレージパス設定
  - `create_session(applicant_name: str, application_date: str) -> str`: セッション作成
    - `session_id` 形式: `{YYYYMMDD}_{HHMMSS}_{uuid4()[:8]}`
    - ステータス `CREATED` でJSONファイル保存
  - `get_session(session_id: str) -> SessionData | None`: セッション取得
  - `update_status(session_id: str, status: SessionState) -> None`: ステータス更新
- `SessionManagerFactory` クラス:
  - `create(storage_path: str = "data/sessions") -> FileBasedSessionManager`: ファクトリメソッド

**テスト内容**:
- `create_session` でセッションが作成され、`session_id` が正規形式(`YYYYMMDD_HHMMSS_xxxxxxxx`)であること
- `get_session` で作成済みセッションが取得できること
- `update_status` でステータスが更新されること
- 存在しない session_id の `get_session` が `None` を返すこと

---

## TASK-08: オーケストレータープロンプト

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/07_skeleton_prompt_orchestrator.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md` §2.3.1（プロンプト全文）

**成果物パス**: `artifacts/06_code-generation/src/prompt/prompt_orchestrator.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_orchestrator.py`

**実装内容**:
- `ORCHESTRATOR_SYSTEM_PROMPT: str` 定数として静的プロンプトを定義
  - AG-001の役割・申請種別判断ルール（BRL-01）
  - 委譲パラメータ構造（transport_agent_tool / expense_agent_tool）
  - GRD-001（空入力禁止）・GRD-004（500文字制限）の文言
  - GRD-005（30回対話制限）の文言
  - 禁止事項（申請書生成・提出禁止）
  - 特殊コマンド（reset / リセット / 最初から）
- `get_orchestrator_system_prompt() -> str` 関数: 定数を返す

**テスト内容**:
- プロンプトが空でないこと
- `"transport_agent_tool"` がプロンプトに含まれること
- `"expense_agent_tool"` がプロンプトに含まれること
- `"GRD-001"` または空入力禁止の文言が含まれること
- `"500"` が含まれること（文字数制限）

---

## TASK-09a: 交通費専門エージェントプロンプト

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md` §2.3.1（プロンプト全文）

**成果物パス**: `artifacts/06_code-generation/src/prompt/prompt_transport.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_transport.py`

**実装内容**:
- `build_transport_agent_system_prompt(application_date: str) -> str` 関数:
  - `deadline_date = (date.fromisoformat(application_date) - timedelta(days=90)).isoformat()` を計算
  - `from agent_knowledge.transport_policies import get_transportation_policies` でポリシー取得
  - `application_date`, `deadline_date`, `policies` を埋め込んだプロンプト文字列を返す
  - 移動情報一括収集指示、BRL-14申請期限チェック、BRL-10高額通知（10,000円超）、BRL-11/12交通手段制限
  - `calculate_transport_fare` 呼び出しパラメータ例示
  - `generate_transport_expense_form` 呼び出しパラメータ例示（segments 構造）

**テスト内容**:
- `build_transport_agent_system_prompt("2026-05-02")` が文字列を返すこと
- プロンプトに `"2026-05-02"` が含まれること（申請日）
- プロンプトに `"2026-02-01"` が含まれること（90日前の期限日）
- `"10,000"` または `"10000"` が含まれること（BRL-10高額閾値）
- `"generate_transport_expense_form"` が含まれること

---

## TASK-09b: 経費専門エージェントプロンプト

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/08_skeleton_prompt_specialist.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md` §2.3.1（プロンプト全文）

**成果物パス**: `artifacts/06_code-generation/src/prompt/prompt_expense.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_prompt_expense.py`

**実装内容**:
- `build_expense_agent_system_prompt(application_date: str) -> str` 関数:
  - `deadline_date = (date.fromisoformat(application_date) - timedelta(days=90)).isoformat()` を計算
  - `from agent_knowledge.expense_policies import get_expense_policies` でポリシー取得
  - `application_date`, `deadline_date`, `policies` を埋め込んだプロンプト文字列を返す
  - 領収書処理（BRL-16, GRD-003）、申請期限チェック（BRL-14）、高額通知（5,000円超 BRL-10）
  - 経費区分自動判断と提案ルール（BRL-17, GRD-010）
  - `generate_expense_reimbursement_form` 呼び出しパラメータ例示（items 構造）

**テスト内容**:
- `build_expense_agent_system_prompt("2026-05-02")` が文字列を返すこと
- プロンプトに申請日が含まれること
- `"5,000"` または `"5000"` が含まれること（BRL-10高額閾値）
- `"generate_expense_reimbursement_form"` が含まれること
- `"GRD-010"` または経費区分自動確定禁止の文言が含まれること

---

## TASK-10a: 交通費申請ポリシー

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/09_skeleton_policies.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md` §2.3.1（ポリシー参照）

**成果物パス**: `artifacts/06_code-generation/src/agent_knowledge/transport_policies.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_policies.py`

**実装内容**:
- `get_transportation_policies() -> str` 関数:
  - 交通費申請に関するドメイン知識文字列を返す
  - 対応交通手段（電車/バス/タクシー/飛行機）の説明
  - 別表記マッピング（BRL-12）
  - 申請期限ルール（BRL-14: 90日以内）
  - 高額申請ルール（BRL-10: 10,000円超は上長承認要）
  - 駅名正規化ルール（BRL-15）

**テスト内容**:
- `get_transportation_policies()` が空でない文字列を返すこと
- 「電車」「バス」「タクシー」「飛行機」が含まれること

---

## TASK-10b: 経費精算ポリシー

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/09_skeleton_policies.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md` §2.3.1（ポリシー参照）

**成果物パス**: `artifacts/06_code-generation/src/agent_knowledge/expense_policies.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_policies.py`

**実装内容**:
- `get_expense_policies() -> str` 関数:
  - 経費精算申請に関するドメイン知識文字列を返す
  - 経費区分定義（BRL-17）: 事務用品費・宿泊費・資格精算費・その他経費
  - 経費区分判断キーワード一覧（品目→経費区分のマッピング）
  - 申請期限ルール（BRL-14: 90日以内）
  - 高額申請ルール（BRL-10: 5,000円超は上長承認要）
  - 経費区分自動確定禁止（GRD-010）

**テスト内容**:
- `get_expense_policies()` が空でない文字列を返すこと
- 「事務用品費」「宿泊費」「資格精算費」「その他経費」が含まれること

---

## TASK-11a: 交通費計算ツール

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/10_skeleton_tools.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費計算ツール詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/tools/transport_tools.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_tools.py`

**実装内容**:
- `@tool(context=True)` デコレータを付与した `calculate_transport_fare` 関数:
  - 引数: `context: ToolContext`, `departure: str`, `destination: str`, `transportation_type: str`, `travel_date: str`, `purpose: str`
  - 戻り値: `dict[str, bool | int | str]` = `{"success": bool, "fare": int, "calculation_basis": str, "message": str}`
  - 処理フロー:
    1. `TransportToolInput` バリデーション（ValidationError → `handle_validation_error`）
    2. 交通手段が「電車」の場合:
       - `os.path.exists(TRAIN_ROUTES_PATH)` チェック → 不在時は EX-04 エラー返却
       - `_load_train_routes()` で `train_routes.json` 読み込み
       - `(departure, destination)` または `(destination, departure)` で双方向検索
       - 見つかった場合: `fare`, `calculation_basis = f"電車経路テーブル（train_routes.json）より: {departure}→{destination} {fare}円"`
       - 見つからない場合: ValueError raise → EX-02 エラー返却
    3. バス/タクシー/飛行機の場合:
       - `os.path.exists(FIXED_FARES_PATH)` チェック → 不在時は EX-04 エラー返却
       - `_load_fixed_fares()` で `fixed_fares.json` 読み込み
       - `transportation_type` で検索
       - `calculation_basis = f"固定運賃テーブル（fixed_fares.json）より: {transportation_type} {fare}円"`
  - OPE-002 ログ（開始/完了）
  - 内部関数:
    - `_load_train_routes() -> TrainRouteMaster`
    - `_load_fixed_fares() -> FixedFareMaster`

**テスト内容**:
- `train_routes.json` にある区間で `success=True, fare=200` が返ること
- 双方向検索（逆方向区間）で運賃が返ること
- `bus/taxi/airplane` で `fixed_fares.json` から運賃が返ること
- `train_routes.json` にない区間で `success=False` が返ること
- `train_routes.json` が存在しない場合に `success=False` が返ること（EX-04）
- `fixed_fares.json` が存在しない場合に `success=False` が返ること（EX-04）
- JSON不正ファイルで `success=False` が返ること（EX-06）
- 「渋谷駅」入力で正規化後の「渋谷」で検索されること
- 「JR」入力で「電車」に正規化されること
- 91日前の `travel_date` で `success=False, message` に期限超過メッセージが含まれること

---

## TASK-11b: 申請書生成ツール

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/10_skeleton_tools.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/申請書生成ツール詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/tools/form_generator.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_form_generator.py`

**実装内容**:
- `@tool(context=True)` デコレータを付与した `generate_transport_expense_form` 関数:
  - 引数: `context: ToolContext`, `application_date: str`, `segments: list[dict]`
  - `applicant_name`, `application_date` は `context.invocation_state` から取得
  - openpyxl でテンプレート読み込み (`TRANSPORT_TEMPLATE_PATH`)
  - セル書き込み: `B3=applicant_name`, `B4=application_date`、行7以降に `segments` の各区間データを書き込み
  - 出力パス: `data/output/{session_id}/{safe_name}_{type}_{timestamp}.xlsx`
  - 戻り値: `{"success": bool, "file_path": str, "message": str}`
- `@tool(context=True)` デコレータを付与した `generate_expense_reimbursement_form` 関数:
  - 引数: `context: ToolContext`, `application_date: str`, `items: list[dict]`
  - `applicant_name`, `application_date` は `context.invocation_state` から取得
  - openpyxl でテンプレート読み込み (`EXPENSE_TEMPLATE_PATH`)
  - 同様のセル書き込みパターン
  - 出力パス: `data/output/{session_id}/{safe_name}_{type}_{timestamp}.xlsx`
  - 戻り値: `{"success": bool, "file_path": str, "message": str}`
- エラー時: `success=False`, `file_path=""`, `message=error_handler.handle_file_save_error(e)`

**テスト内容**:
- テンプレートファイルが存在する場合に `success=True` かつ `file_path` が `".xlsx"` で終わること
- テンプレートファイルが存在しない場合に `success=False` が返ること（EX-04）
- `invocation_state` から `applicant_name` が取得されること（LLM パラメータからではないこと）
- `segments` が空リストの場合に `success=True` が返ること（境界値）

---

## TASK-12: オーケストレーターエージェント

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/11_skeleton_orchestrator_agent.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/agents/orchestrator_agent.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_orchestrator_agent.py`

**実装内容**:
- `create_orchestrator_agent(session_id: str) -> Agent` 関数:
  - `BedrockModel(model_id=...)` インスタンス生成
  - `system_prompt = get_orchestrator_system_prompt()`（静的）
  - `tools = [transport_agent_tool, expense_agent_tool]`
  - `conversation_manager = SlidingWindowConversationManager(window_size=30)`
  - `hooks = [LoopControlHook(max_iterations=10)]`（HumanApprovalHook は AG-001には不要）
  - `session_manager = SessionManagerFactory.create()`
- `create_invocation_state(session_id: str, applicant_name: str = "", application_date: str = "") -> dict` 関数:
  - `InvocationState` を作成して `model_dump()` を返す
  - `application_date` のデフォルト: `date.today().isoformat()`

**テスト内容**:
- `create_orchestrator_agent` が `Agent` インスタンスを返すこと
- `create_invocation_state` が必要なキーを持つ dict を返すこと
- `session_id`, `applicant_name`, `application_date` キーが含まれること

---

## TASK-13a: 交通費専門エージェント

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/12_skeleton_specialist_agent.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/agents/transport_agent.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_transport_agent.py`

**実装内容**:
- モジュールレベル: `_agent_instances: dict[str, Agent] = {}`
- `approval_callback` グローバル変数（`human_approval_hook.py` からインポートして使用）
- `_build_transport_agent_system_prompt(application_date: str) -> str` 関数（`prompt/prompt_transport.py` に委譲）
- `@tool(context=True)` デコレータ付き `transport_agent_tool` 関数:
  - 引数: `application_type: str`, `applicant_name: str`, `user_input_text: str`, `tool_context: ToolContext`
  - `session_id = tool_context.invocation_state.get("session_id", "")`
  - `session_id` が `_agent_instances` にない場合のみ `Agent` インスタンスを生成:
    - `tools = [calculate_transport_fare, generate_transport_expense_form]`
    - `conversation_manager = SlidingWindowConversationManager(window_size=20)`
    - `hooks = [LoopControlHook(max_iterations=10), HumanApprovalHook(approval_callback=approval_callback)]`
    - `callback_handler = None`
  - `response = _agent_instances[session_id](user_input_text, invocation_state=state)`
  - 例外処理: ThrottlingException, MaxTokensException, ContextWindowException, LoopLimitError, RuntimeError, Exception 個別ハンドリング
  - OPE-002 ログ（開始/新規生成/キャッシュ再利用/完了）

**テスト内容**:
- `transport_agent_tool` がモジュールに定義されていること（`@tool` デコレータ付き）
- 同一 `session_id` で2回呼んだ場合に同一インスタンスが再利用されること
- 異なる `session_id` では別インスタンスが生成されること

---

## TASK-13b: 経費専門エージェント

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/12_skeleton_specialist_agent.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/agents/expense_agent.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_expense_agent.py`

**実装内容**:
- モジュールレベル: `_agent_instances: dict[str, Agent] = {}`
- `_build_expense_agent_system_prompt(application_date: str) -> str` 関数（`prompt/prompt_expense.py` に委譲）
- `@tool(context=True)` デコレータ付き `expense_agent_tool` 関数:
  - 引数: `application_type: str`, `applicant_name: str`, `user_input_text: str`, `tool_context: ToolContext`
  - `tools = [image_reader, generate_expense_reimbursement_form]`（`strands_tools` の `image_reader`）
  - `conversation_manager = SlidingWindowConversationManager(window_size=15)`
  - `callback_handler = None`
  - 例外処理: transport_agent.py と同様の6種類

**テスト内容**:
- `expense_agent_tool` がモジュールに定義されていること（`@tool` デコレータ付き）
- 同一 `session_id` で2回呼んだ場合に同一インスタンスが再利用されること

---

## TASK-14: メインエントリーポイント

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/13_skeleton_main.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md` §2.3.3（処理フロー）

**成果物パス**: `artifacts/06_code-generation/src/main.py`

**単体テストパス**: `artifacts/06_code-generation/src/tests/unit/test_main.py`

**実装内容**:
- `load_dotenv()` 呼び出し（最初に実行）
- `patch_human_approval_hook()` 呼び出し（`load_dotenv()` の直後、エージェント生成前）
- `main()` 関数:
  - `applicant_name = input("お名前を入力してください: ")` で申請者名取得
  - `SessionManagerFactory.create().create_session(applicant_name, date.today().isoformat())` でセッション作成
  - `agent = create_orchestrator_agent(session_id)`
  - 対話ループ:
    - `user_input = input("\n\n入力内容（終了時はquit）: ")`
    - `"quit"` 入力でループ終了
    - `reset` / `リセット` / `最初から` コマンド処理
    - `response = agent(user_input, invocation_state=state)`
    - `print(response)` で応答表示
  - KeyboardInterrupt → `error_handler.handle_keyboard_interrupt(e)` を表示

**テスト内容**:
- `main.py` がインポートエラーなしで読み込めること
- `main()` 関数が定義されていること

---

## TASK-15: 依存関係定義

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/14_design_data_files.md`

**成果物パス**: `artifacts/06_code-generation/src/requirements.txt`

**実装内容**:
```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
boto3>=1.34.0
pydantic>=2.0.0
pytest>=7.4.0
python-dotenv
openpyxl
strands-agents-evals
```

---

## TASK-16: Bedrock Guardrails CloudFormation テンプレート

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/15_guardrails_cloudformation_yaml.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/ガードレール詳細設計.md`（全章）

**成果物パス**: `artifacts/06_code-generation/src/config/guardrails_cloudformation.yaml`

**実装内容**:
- `AWS::Bedrock::Guardrail` リソース定義
- ガードレール名: `expense-agent-guardrail`
- コンテンツフィルタ（STANDARD層）:
  - VIOLENCE HIGH/HIGH, PROMPT_ATTACK HIGH/NONE, MISCONDUCT HIGH/HIGH
  - HATE HIGH/HIGH, SEXUAL HIGH/HIGH, INSULTS MEDIUM/MEDIUM
- 単語ポリシー: PROFANITY BLOCK（入出力両方）
- PII ポリシー:
  - NAME: 出力のみ ANONYMIZE
  - EMAIL: 出力のみ BLOCK
  - PHONE: 出力のみ BLOCK
  - ADDRESS: 出力のみ ANONYMIZE
- ブロックメッセージ（日本語）

---

## TASK-17a: ツール選択精度評価スクリプト

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/16_eval_test.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/評価テスト詳細設計.md` Part 1

**成果物パス**: `artifacts/06_code-generation/src/evals/eval_tool_selection.py`

**実装内容**:
- UTF-8エンコーディング設定（`sys.stdout.reconfigure`）
- `sys.path` 設定（プロジェクトルートを追加）
- `load_dotenv()` → `patch_human_approval_hook()` の順で実行
- ログ設定（INFO、コンソール + `evals/logs/eval_tool_selection.log`）
- SDK ログ抑制（`strands` → WARNING, `strands.event_loop.event_loop` → CRITICAL）
- `EVAL_CASES` リスト（3テストケース）:
  - TC-001: `"先日、新幹線で出張しました。交通費を精算したいです。"` → `expected_tool="transport_agent_tool"`
  - TC-002: `"コンビニで業務用の文房具を買いました。経費精算をお願いします。"` → `expected_tool="expense_agent_tool"`
  - TC-003: `"申請の手続きをお願いします。"` → `expected_tool=""`
- `run_eval_task(case: Case) -> dict` 関数:
  - `memory_exporter.clear()` → エージェント生成 → シングルターン実行 → スパン取得 → `Session` 変換
  - 戻り値: `{"output": str, "trajectory": Session}`
- `main()` 関数: `ToolSelectionAccuracyEvaluator` → `Experiment` → レポート保存

---

## TASK-17b: ゴール達成率評価スクリプト

**状態**: 🔲 未着手

**参照スケルトン**: `.claude/skills/templates/06_code-generation/16_eval_test.md`

**参照設計書**:
- `artifacts/05_detailed-design/outputs/評価テスト詳細設計.md` Part 2

**成果物パス**: `artifacts/06_code-generation/src/evals/eval_goal_success_rate.py`

**実装内容**:
- TASK-17a と同様の初期設定（UTF-8, sys.path, load_dotenv, patch_human_approval_hook, ログ設定）
- `EVAL_CASES` リスト（4テストケース）:
  - TC-001: 交通費精算申請E2E → `goal="交通費精算申請書（下書き）の生成が完了し、エージェントが申請書の場所を案内していること"`
  - TC-002: 経費精算申請E2E → `goal="経費精算申請書（下書き）の生成が完了し、エージェントが申請書の場所を案内していること"`
  - TC-003: 申請期限超過 → `goal="申請期限超過として申請不可を通知し、担当部門への問い合わせを案内していること（BRL-14）"`
  - TC-004: 対話回数上限 → `goal="対話ターン数上限（30回）に達した旨を通知し、担当部門への問い合わせを案内していること（GRD-005）"`
- `run_eval_task(case: Case) -> dict` 関数:
  - `memory_exporter.clear()` → エージェント生成 → `run_actor_conversation` によるマルチターン実行 → スパン取得 → `Session` 変換
  - 戻り値: `{"output": str, "trajectory": Session}`
- `main()` 関数: `GoalSuccessRateEvaluator` → `Experiment` → レポート保存

---

## TASK-18: 資材ファイルコピー

**状態**: 🔲 未着手

**参照元**:
- `.claude/materials/06_code-generation/` 配下のファイル

**コピー対象**:

| コピー元 | コピー先 | 備考 |
|---------|---------|------|
| `.claude/materials/06_code-generation/fixed_fares.json` | `artifacts/06_code-generation/src/data/fixed_fares.json` | |
| `.claude/materials/06_code-generation/train_fares.json` | `artifacts/06_code-generation/src/data/train_routes.json` | ファイル名変更（routes キーを確認） |
| `.claude/materials/06_code-generation/交通費申請書_template.xlsx` | `artifacts/06_code-generation/src/data/templates/交通費精算申請書テンプレート.xlsx` | |
| `.claude/materials/06_code-generation/経費精算申請書_template.xlsx` | `artifacts/06_code-generation/src/data/templates/経費精算申請書テンプレート.xlsx` | |
| `.claude/materials/06_code-generation/.gitignore` | `artifacts/06_code-generation/src/.gitignore` | ファイルが存在する場合のみコピー |
| `.claude/materials/06_code-generation/.env.template` | `artifacts/06_code-generation/src/.env.template` | ファイルが存在する場合のみコピー |

> **注意**: `.gitignore` と `.env.template` が `.claude/materials/06_code-generation/` に存在しない場合は作成する

---

## TASK-19: `__init__.py` ファイル一式

**状態**: 🔲 未着手

**成果物パス（空ファイル）**:
- `src/__init__.py`
- `src/models/__init__.py`
- `src/config/__init__.py`
- `src/handlers/__init__.py`
- `src/session/__init__.py`
- `src/prompt/__init__.py`
- `src/agent_knowledge/__init__.py`
- `src/tools/__init__.py`
- `src/agents/__init__.py`
- `src/evals/__init__.py`
- `src/tests/__init__.py`
- `src/tests/unit/__init__.py`
- `src/tests/integration/__init__.py`
- `src/tests/e2e/__init__.py`

---

## TASK-20: 結合テスト

**状態**: 🔲 未着手

**前提**: TASK-01〜TASK-18 が完了していること

**成果物パス**: `artifacts/06_code-generation/src/tests/integration/test_integration.py`

**テスト内容**:
- `calculate_transport_fare` + `train_routes.json` の統合動作（実ファイル参照）
- `calculate_transport_fare` + `fixed_fares.json` の統合動作
- `generate_transport_expense_form` + テンプレートファイルの統合動作（申請書 xlsx 生成）
- `generate_expense_reimbursement_form` + テンプレートファイルの統合動作
- `LoopControlHook` が Strands Agent に組み込まれた場合の動作
- `HumanApprovalHook` が `patch_human_approval_hook()` でモック差し替えされた場合の自動承認動作

**実行コマンド**:
```bash
cd artifacts/06_code-generation/src
pytest tests/integration/ -v
```

---

## TASK-21: E2Eテスト

**状態**: 🔲 未着手

**前提**: TASK-20 が完了していること

**成果物パス**: `artifacts/06_code-generation/src/tests/e2e/test_e2e.py`

**テスト内容**:
- AG-001 → AG-002 の連携（交通費精算申請フロー）: モック化した API で申請書生成まで完了すること
- AG-001 → AG-003 の連携（経費精算申請フロー）: モック化した API で申請書生成まで完了すること
- reset コマンド: セッションリセット後に新規 session_id が発行されること
- HumanApprovalHook キャンセル時: フローが終了し申請書が生成されないこと

**実行コマンド**:
```bash
cd artifacts/06_code-generation/src
pytest tests/e2e/ -v
```

---

## 実装順序（依存関係）

```
TASK-01(models) 
  └→ TASK-03(settings)
       ├→ TASK-04(error_handler)
       │    ├→ TASK-05(loop_control_hook)
       │    │    └→ TASK-06(human_approval_hook)
       │    └→ TASK-07(session_manager)
       ├→ TASK-11a(transport_tools) ←→ TASK-01, TASK-04
       └→ TASK-11b(form_generator)  ←→ TASK-01, TASK-04
TASK-02(model_config)
TASK-08(prompt_orchestrator)
TASK-09a(prompt_transport) ←→ TASK-10a(transport_policies)
TASK-09b(prompt_expense)   ←→ TASK-10b(expense_policies)
TASK-12(orchestrator_agent) ←→ TASK-02, TASK-08, TASK-05
TASK-13a(transport_agent)   ←→ TASK-02, TASK-09a, TASK-05, TASK-06, TASK-07, TASK-11a, TASK-11b
TASK-13b(expense_agent)     ←→ TASK-02, TASK-09b, TASK-05, TASK-06, TASK-07, TASK-11b
TASK-14(main)               ←→ TASK-12, TASK-13a, TASK-13b
TASK-15(requirements.txt)
TASK-16(guardrails yaml)
TASK-17a(eval_tool_selection) ←→ TASK-12, TASK-13a, TASK-13b
TASK-17b(eval_goal_success)   ←→ TASK-12, TASK-13a, TASK-13b
TASK-18(材料コピー)
TASK-19(__init__.py)
TASK-20(結合テスト) ←→ 全タスク完了
TASK-21(E2Eテスト)  ←→ TASK-20完了
```
