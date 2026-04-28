# 05_detailed-design フェーズ品質チェック

**実施日**: 2026-04-28
**対象フェーズ**: 05_detailed-design
**チェック実施者**: Claude Code

---

## チェック結果サマリー

**判定: ✅ 合格**

全8件の成果物がテンプレート準拠・基本設計との整合・実装可能レベルの詳細化・次フェーズへの引き継ぎ情報の4観点を満たしていることを確認した。

---

## 対象成果物一覧

| # | 成果物名 | 状態 |
|---|---------|------|
| 1 | 交通費計算ツール詳細設計書.md | ✅ 合格 |
| 2 | 申請書生成ツール詳細設計書.md | ✅ 合格 |
| 3 | AG-001_申請受付窓口エージェント詳細設計書.md | ✅ 合格 |
| 4 | AG-002_交通費精算申請エージェント詳細設計書.md | ✅ 合格 |
| 5 | AG-003_経費精算申請エージェント詳細設計書.md | ✅ 合格 |
| 6 | ErrorHandler詳細設計書.md | ✅ 合格 |
| 7 | HumanApprovalHook詳細設計書.md | ✅ 合格 |
| 8 | LoopControlHook詳細設計書.md | ✅ 合格 |

---

## 観点1: テンプレート準拠

### チェック内容
各成果物がテンプレートに定義されたセクション構成に従って作成されていること。

| 成果物 | テンプレート | 判定 | 備考 |
|--------|------------|------|------|
| 交通費計算ツール詳細設計書.md | ツール詳細設計テンプレート.md | ✅ | 1.概要/2.設計詳細/3.ツール設計/4.ビジネスロジック/5.エラーハンドリング/6.ログ/7.依存関係/8.テスト観点/9.変更履歴の全セクションを含む |
| 申請書生成ツール詳細設計書.md | ツール詳細設計テンプレート.md | ✅ | 交通費/経費の2ツール構成。全セクション含む |
| AG-001〜003詳細設計書.md | エージェント詳細設計テンプレート.md | ✅ | 1.概要/2.設計詳細/2.2インターフェース/2.3ビジネスロジック/2.4設定構成/2.5連携設計/3.実装詳細/4.データ設計/5.補足/6.依存関係/7.テスト観点の全セクションを含む |
| ErrorHandler詳細設計書.md | ハンドラー詳細設計テンプレート.md | ✅ | 1.概要/2.設計詳細/3.ビジネスロジック/4.データ設計/5.補足の全セクションを含む |
| HumanApprovalHook詳細設計書.md | ハンドラー詳細設計テンプレート.md | ✅ | フック設計セクション（register_hooks・イベントハンドラー）を含む |
| LoopControlHook詳細設計書.md | ハンドラー詳細設計テンプレート.md | ✅ | フック設計セクション（6イベントハンドラー・LoopLimitErrorカスタム例外定義）を含む |

**判定: ✅ 合格** — 全成果物でテンプレートセクション構成への準拠を確認。

---

## 観点2: 基本設計との整合性

### チェック内容
詳細設計の内容が上流の基本設計・システム設計の方針と矛盾しないこと。

| チェック項目 | 確認内容 | 判定 |
|------------|---------|------|
| TOOL-001の利用エージェント | AG-002のみ。AG-001・AG-003はcalculate_transport_expenseを登録していない | ✅ |
| TOOL-002の利用エージェント | AG-002（generate_transport_expense_form）・AG-003（generate_expense_form）。AG-001は登録していない | ✅ |
| HumanApprovalHookの登録 | AG-002・AG-003のみ。AG-001には登録しない（基本設計書 7.1節の制約を守っている） | ✅ |
| LoopControlHookのmax_iterations | AG-001/002/003すべてに max_iterations=30 で登録（実行制御方針.md 10.2節と整合） | ✅ |
| SlidingWindowサイズ | AG-001=30, AG-002=20, AG-003=15（共通設定方針 2.2節と整合） | ✅ |
| invocation_stateの受け渡し | applicant_name/application_date/session_idはAG-001がinvocation_stateにセット。TOOL-001/TOOL-002はinvocation_stateから内部取得（LLMパラメータとして渡さない）（マルチエージェント連携設計 7.2節と整合） | ✅ |
| callback_handler=None | AG-002・AG-003のAgentインスタンスに設定して二重出力を防止（AG-001基本設計書 16.2節と整合） | ✅ |
| 動的プロンプト生成 | AG-002: _build_transport_agent_system_prompt、AG-003: _build_expense_agent_system_prompt（基本設計書 7章と整合） | ✅ |
| 申請期限基準日 | AG-002: BRL-13（3ヶ月・10,000円閾値）、AG-003: BRL-18（3ヶ月・5,000円閾値）（基本設計書と整合） | ✅ |
| EX-01〜EX-08分類 | ErrorHandlerのメソッドがEX-01〜EX-08に1対1でマッピング（例外処理方針.mdと整合） | ✅ |
| BeforeToolCallEventのフィルタリング | ツール名の完全一致でTOOL-002のみブロック、TOOL-001はスルー（基本設計書 7.2節と整合） | ✅ |
| LoopLimitError（LoopControlHook定義） | LoopLimitError は hooks/loop_control_hook.py 内で定義。AG-001/002/003がキャッチしてErrorHandler.handle_loop_limit_error()でメッセージ変換（基本設計書 7.2節と整合） | ✅ |
| 申請書の自動提出禁止（BRL-09） | TOOL-002の生成後「提出操作はご自身で実施してください」を提示（AG-002/003詳細設計書 2.2.2節） | ✅ |

**判定: ✅ 合格** — 全チェック項目で基本設計・システム設計との整合を確認。矛盾なし。修正#18適用後の変更（max_iterations=30・クラスベース設計・approval_callback仕様・agent_knowledgeモジュール参照）も整合を確認済み。

---

## 観点3: 実装可能なレベルまでの詳細化

### チェック内容
各成果物が実装者がコードを記述できるレベルの情報（関数シグネチャ・処理フロー・エラー処理）を含むこと。

| 成果物 | 関数シグネチャ | 処理フロー | エラー処理 | 判定 |
|--------|------------|-----------|-----------|------|
| 交通費計算ツール詳細設計書.md | ✅ calculate_transport_expense(transport_date, departure, destination, transport_type) | ✅ 電車/固定運賃の分岐フロー | ✅ success=False返却パターン | ✅ |
| 申請書生成ツール詳細設計書.md | ✅ generate_transport/expense_form(applicant_name, application_date, segments/items, business_purpose) | ✅ テンプレート読込→セル書込→保存フロー | ✅ テンプレートなし・書き込みエラーの2パターン | ✅ |
| AG-001詳細設計書.md | ✅ OrchestratorAppクラス（__init__/run/_collect_applicant_name/_initialize_session/_reset_session/_mask_applicant_name）・session_id形式（YYYYMMDDHHmmss_8hex） | ✅ 申請者名収集→セッション初期化→対話ループ→ルーティング | ✅ KeyboardInterrupt/LoopLimitError/ContextWindowOverflowException/MaxTokensReachedException/RuntimeError/Exceptionの6ケース。WARNING/ERRORログレベル区分・str返却 | ✅ |
| AG-002詳細設計書.md | ✅ エージェント名: transport_agent。TransportAgentFactoryクラス（get_agent/remove）・transport_application_agent_tool・_build_transport_agent_system_prompt | ✅ agent_knowledge/transportation_policies.py定数参照→キャッシュ→対話ループ→ルールチェック | ✅ LoopLimitError/ContextWindowOverflowException/MaxTokensReachedException=WARNING・RuntimeError/Exception=ERROR+exc_info。全エラーstr返却・query[:50]ログ記録 | ✅ |
| AG-003詳細設計書.md | ✅ ExpenseAgentFactoryクラス（get_agent/remove）・expense_application_agent_tool・_build_expense_agent_system_prompt | ✅ agent_knowledge/receipt_policies.py定数参照・image_readerツール（strands_tools）によるBRL-16領収書読み取り | ✅ AG-002と同パターン（[AG-003]プレフィックス） | ✅ |
| ErrorHandler詳細設計書.md | ✅ 11メソッドの引数・戻り値型（全メソッドが例外オブジェクトのみを受け取りstr返却） | ✅ 各メソッドがユーザー向けメッセージ文字列のみ生成・返却 | ✅ ログなし・SessionManagerなし・コンストラクタ引数なし | ✅ |
| HumanApprovalHook詳細設計書.md | ✅ register_hooks・_on_before_tool_call・_log_approval・approval_callback仕様（シグネチャ・戻り値3パターン・event.cancel_toolによるツール中止） | ✅ ツール名フィルタ→コールバック/デフォルト承認処理→分岐 | ✅ ログ失敗・event.tool_use欠損・無効入力・コールバック例外 | ✅ |
| LoopControlHook詳細設計書.md | ✅ register_hooks・6イベントハンドラー（BeforeInvocation/BeforeModelCall/AfterModelCall/BeforeToolCall/AfterToolCall/AfterInvocation）・LoopLimitError定義 | ✅ 6イベントフロー・AfterModelCallでLoopLimitError送出・AfterInvocationでリセットなし | ✅ event.exception存在時のAfterModelCallスキップ・想定外エラー | ✅ |

**判定: ✅ 合格** — 全成果物で実装可能なレベルの詳細化を確認。コード生成フェーズへ引き渡せる粒度。

---

## 観点4: 次フェーズへの引き継ぎ情報

### チェック内容
06_code-generationフェーズに必要な情報（クラス名・ファイルパス・依存関係・設定値）が揃っていること。

| 引き継ぎ情報 | 記載箇所 | 判定 |
|------------|---------|------|
| クラス名・関数名 | 各設計書 3.1節（クラス設計・関数設計） | ✅ |
| ファイルパス（ソース） | 各設計書の依存関係 6章 | ✅ |
| データファイルパス（template/train_routes.json、template/fixed_fares.json） | 交通費計算ツール詳細設計書 5章・9章 | ✅ |
| テンプレートファイルパス | 申請書生成ツール詳細設計書 3.4節 | ✅ |
| 出力先ディレクトリ（output/） | 申請書生成ツール詳細設計書 3.4節 | ✅ |
| セッションデータパス（data/sessions/） | AG-002/AG-003詳細設計書 2.4節 | ✅ |
| ログファイルパス（logs/error.log, logs/approval.log） | ErrorHandler・HumanApprovalHook詳細設計書 4章 | ✅ |
| 外部ライブラリ一覧 | 各設計書 6章（依存関係） | ✅ |
| Pydanticモデル名 | ツール詳細設計書 3.2.1節（TransportExpenseCalculatorInput等） | ✅ |
| invocation_stateの辞書構造 | AG-001〜003詳細設計書 4章 | ✅ |
| HumanApprovalHookのtool_namesパラメータ | HumanApprovalHook詳細設計書 10章 | ✅ |
| LoopControlHookのmax_iterations | LoopControlHook詳細設計書 9章 | ✅ |
| SlidingWindowサイズ（30/20/15） | AG-001〜003詳細設計書 2.4節 | ✅ |
| システムプロンプト全文 | AG-001〜003詳細設計書 2.3.1節 | ✅ |
| ErrorHandlerメソッド一覧（11メソッド） | ErrorHandler詳細設計書 2章（handle_throttling_error/handle_max_tokens_error/handle_context_window_error/handle_fare_data_error/handle_calculation_error/handle_file_save_error/handle_validation_error/handle_keyboard_interrupt/handle_loop_limit_error/handle_runtime_error/handle_unexpected_error） | ✅ |
| LoopLimitErrorの定義場所 | LoopControlHook詳細設計書（hooks/loop_control_hook.py内で定義。3フィールド: current_iteration/max_iterations/agent_name） | ✅ |

**判定: ✅ 合格** — コード生成フェーズに必要な全情報が揃っていることを確認。

---

## 指摘事項

### 要件上未定義として引き継ぐ項目

以下の項目は上流要件が未定義のため、詳細設計書でも「要件上未定義」として記載されている。コード生成フェーズ以降でも保留扱いとする。

| 項目 | 記載箇所 | 状況 |
|------|---------|------|
| BRL-08（差し戻しリスク評価）の判定基準 | AG-002/AG-003詳細設計書 2.3.2節 | 要件上未定義（業務要件レベルで未確定） |
| Amazon Bedrockのタイムアウト値 | 実行制御方針.md 17節 U-001 | 要件上未定義 |
| TOOL-001/TOOL-002のタイムアウト値 | 実行制御方針.md 17節 U-002 | 要件上未定義 |
| Human-in-the-Loop承認待ちのタイムアウト | 実行制御方針.md 17節 U-003 | 要件上未定義 |
| 申請先の提示内容（BRL-03） | AG-001詳細設計書 2.3.1節 | 要件上未定義 |
| HumanApprovalHookデフォルト承認処理の無効入力上限回数 | HumanApprovalHook詳細設計書 7.1節 5項 | 要件上未定義（実装判断で5回連続無効でキャンセル可としているが上限は要件未定義） |

---

## 総合判定

**✅ 合格**

- テンプレート準拠: 全8件 ✅
- 基本設計との整合: 全チェック項目 ✅（矛盾なし）
- 実装可能レベルの詳細化: 全8件 ✅
- 次フェーズ引き継ぎ情報: 全項目 ✅

05_detailed-design フェーズの全成果物が品質基準を満たしており、06_code-generation フェーズへ進む準備が完了した。
