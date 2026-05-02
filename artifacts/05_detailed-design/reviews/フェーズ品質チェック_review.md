---
version: "1.0.0"
last_updated: "2026-05-02"
updated_by: ""
---

# フェーズ品質チェック：05_detailed-design

> 文書ID：`SYS-PHASE-REVIEW-05`
> 文書名：フェーズ品質チェック（05_detailed-design）
> 版数：`v1.0`
> 作成日：2026-05-02

---

## 判定結果

**✅ 合格**

---

## 1. チェック対象成果物

| # | 成果物 | ID | 出力先 | 状態 |
|---|---|---|---|---|
| 1 | 交通費計算ツール詳細設計.md | DD-01 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 2 | 申請書生成ツール詳細設計.md | DD-01 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 3 | 申請受付窓口エージェント詳細設計.md | DD-02 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 4 | 交通費精算申請エージェント詳細設計.md | DD-02 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 5 | 経費精算申請エージェント詳細設計.md | DD-02 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 6 | ErrorHandler詳細設計.md | DD-03 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 7 | LoopControlHook詳細設計.md | DD-03 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 8 | HumanApprovalHook詳細設計.md | DD-03 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 9 | ガードレール詳細設計.md | DD-04 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |
| 10 | 評価テスト詳細設計.md | DD-05 | artifacts/05_detailed-design/outputs/ | ✅ 存在 |

---

## 2. テンプレート準拠チェック

### 2.1 ツール詳細設計

| 成果物 | テンプレート準拠 | 備考 |
|---|---|---|
| 交通費計算ツール詳細設計.md | ✅ | 関数シグネチャ・入力モデル（TransportToolInput）・処理フロー・エラー処理（EX-02/EX-04/EX-06）・出力仕様・バリデーション詳細を網羅 |
| 申請書生成ツール詳細設計.md | ✅ | TL-002a（generate_transport_expense_form）/TL-002b（generate_expense_reimbursement_form）を統合記述。入力モデル（TransportFormInput/ExpenseFormInput）・openpyxl出力処理・HumanApprovalHookとの連携設計を含む |

### 2.2 エージェント詳細設計

| 成果物 | テンプレート準拠 | 備考 |
|---|---|---|
| 申請受付窓口エージェント詳細設計.md | ✅ | システムプロンプト完全版・AG-002/AG-003 Agent as Tools登録実装詳細・_agent_instancesキャッシュパターン・SlidingWindow(30)・リセットコマンド処理・invocation_state受け渡しを含む |
| 交通費精算申請エージェント詳細設計.md | ✅ | 動的システムプロンプト生成・CF-003 17ステップ詳細・TL-001/TL-002a呼び出し詳細・高額通知（10,000円超）・SlidingWindow(20)・HumanApprovalHook連携を含む |
| 経費精算申請エージェント詳細設計.md | ✅ | 動的システムプロンプト生成・CF-004 11ステップ詳細・LLM画像読み取り（BRL-16）・経費区分自動判定ロジック・高額通知（5,000円超）・TL-002b呼び出し詳細・SlidingWindow(15)を含む |

### 2.3 ハンドラー詳細設計

| 成果物 | テンプレート準拠 | 備考 |
|---|---|---|
| ErrorHandler詳細設計.md | ✅ | HD-001。EX-01〜EX-08の分類・ERR-001〜ERR-008ログID・handle/classify/_log_error/_build_user_messageメソッド詳細・ユーザーメッセージ一覧を網羅 |
| LoopControlHook詳細設計.md | ✅ | HD-002。BeforeInvocationEvent（カウンタリセット）・AfterModelCallEvent（インクリメント+上限チェック）・LoopLimitError（RuntimeErrorサブクラス）・OPE-004ログを含む |
| HumanApprovalHook詳細設計.md | ✅ | HD-003。BeforeToolCallEvent介入・_build_confirmation_message・_log_audit（AUD-004）・OPE-003ログ・GRD-011 PIIマスキング（applicant_name[:1]+"***"）を含む |

### 2.4 ガードレール詳細設計

| 成果物 | テンプレート準拠 | 備考 |
|---|---|---|
| ガードレール詳細設計.md | ✅ | AWS Bedrock Guardrailsの設定仕様（コンテンツフィルター・単語ポリシー・機密情報ポリシー）・適用範囲・GRD-001〜GRD-015との責任分担マトリクスを含む |

### 2.5 評価テスト詳細設計

| 成果物 | テンプレート準拠 | 備考 |
|---|---|---|
| 評価テスト詳細設計.md | ✅ | eval_tool_selection.py（MET-010 TOOL_LEVEL）・eval_goal_success_rate.py（MET-011 SESSION_LEVEL）の2スクリプト詳細。初期化処理・テストケース定義・run_eval_task処理フロー・main処理・出力ファイル仕様・制約事項を網羅 |

---

## 3. 上流成果物との整合性チェック

### 3.1 基本設計（04_basic-design）との整合

| チェック項目 | 結果 | 備考 |
|---|---|---|
| ToolID（TL-001/TL-002a/TL-002b）の一致 | ✅ | 全ツール詳細設計書でTool IDが基本設計書と統一 |
| 入力モデル名（TransportToolInput/TransportFormInput/ExpenseFormInput）の一致 | ✅ | データモデル基本設計書の定義と一致 |
| エージェントID（AG-001/AG-002/AG-003）の一致 | ✅ | 全エージェント詳細設計書でAG-IDが統一 |
| SlidingWindow設定値の一致（AG-001=30/AG-002=20/AG-003=15） | ✅ | 各エージェント詳細設計書の設定が基本設計書と整合 |
| ハンドラークラス名（ErrorHandler/LoopControlHook/HumanApprovalHook）の一致 | ✅ | ハンドラー基本設計書（HD-001/HD-002/HD-003）と一致 |
| LoopLimitError（RuntimeErrorサブクラス）の定義場所 | ✅ | handlers/loop_control_hook.py 内に定義することを明記 |
| max_iterations=10（全エージェント共通）の一致 | ✅ | LoopControlHook詳細設計書の設定が基本設計書と整合 |
| HumanApprovalHookの介入対象（TL-002a/TL-002bのみ）の一致 | ✅ | BeforeToolCallEventで正確に2ツール名のみを対象として判定 |
| AG-001への非適用（申請書生成ツールなし）の明示 | ✅ | HumanApprovalHook詳細設計書§1.3の非責務に明記 |
| 動的プロンプト生成（AG-002/AG-003: application_date・deadline_date埋め込み）の一致 | ✅ | 各エージェント詳細設計書の動的プロンプト生成処理と整合 |

### 3.2 システム設計（03_system-design）との整合

| チェック項目 | 結果 | 備考 |
|---|---|---|
| マルチエージェント連携設計（Agent as Tools）との整合 | ✅ | AG-001詳細設計書で@tool(context=True)ファクトリ関数パターンを正確に実装 |
| invocation_state経由のセッションID伝播との整合 | ✅ | 全エージェント詳細設計書でToolContext.invocation_stateからのセッションID取得を明記 |
| 例外処理方針（EX-01〜EX-08・ユーザーメッセージ）との整合 | ✅ | ErrorHandler詳細設計書のEX分類・ユーザーメッセージがシステム設計の例外処理方針と整合 |
| ループ制御方針（max_iterations=10・AfterModelCallEvent）との整合 | ✅ | LoopControlHook詳細設計書の設計が実行制御方針と整合 |
| 人間承認制御方針（BeforeToolCallEvent・GRD-014）との整合 | ✅ | HumanApprovalHook詳細設計書の設計が実行制御方針と整合 |
| 評価テスト共通設計（strands_evals・LLM-as-Judge・SESSION_LEVEL/TOOL_LEVEL）との整合 | ✅ | 評価テスト詳細設計書がstrands_evalsフレームワークの評価テスト共通設計に準拠 |
| ガードレール要件定義（GRD-001〜GRD-015）との整合 | ✅ | ガードレール詳細設計書でGRD-001〜GRD-015の責任分担を明確化 |

### 3.3 システム要件定義（02_system-requirements）との整合

| チェック項目 | 結果 | 備考 |
|---|---|---|
| 評価指標（MET-010/MET-011）との整合 | ✅ | MET-010: ToolSelectionAccuracyEvaluator（TOOL_LEVEL）、MET-011: GoalSuccessRateEvaluator（SESSION_LEVEL）を正確に実装 |
| ガードレール要件（GRD-011: PII出力抑制）との整合 | ✅ | ガードレール詳細設計書のPIIポリシー（NAME/EMAIL/PHONE/ADDRESS）とHumanApprovalHookのマスキング（GRD-011）が要件と一致 |
| 業務ルール（BRL-14: 申請期限超過エスカレーション）との整合 | ✅ | 評価テスト詳細設計書TC-003（TC-003_deadline_exceeded_escalation）に反映 |
| ガードレール要件（GRD-005: 対話回数上限）との整合 | ✅ | 評価テスト詳細設計書TC-004（TC-004_turn_limit_escalation）に反映 |

---

## 4. 技術スタック適用チェック

| 技術要素 | チェック項目 | 結果 |
|---|---|---|
| Strands Agents v1.25.0 | LoopControlHookのHookProviderサブクラス化・register_hooks実装 | ✅ |
| Strands Agents v1.25.0 | LoopLimitError（RuntimeErrorサブクラス）のhandlers/loop_control_hook.py内定義 | ✅ |
| Strands Agents v1.25.0 | HumanApprovalHookのHookProviderサブクラス化・BeforeToolCallEvent登録 | ✅ |
| Strands Agents v1.25.0 | ToolCallCancelled raiseによるツール実行中止（修正/キャンセル時） | ✅ |
| Strands Agents v1.25.0 | Agent as ToolsパターンによるAG-002/AG-003のツール登録 | ✅ |
| Strands Agents v1.25.0 | callback_handler=None設定（AG-001/AG-002/AG-003全共通） | ✅ |
| strands_evals | Case/Experiment/ToolSelectionAccuracyEvaluator/GoalSuccessRateEvaluator使用 | ✅ |
| strands_evals | StrandsInMemorySessionMapper（OpenTelemetryスパン→Session変換） | ✅ |
| strands_evals | memory_exporter.clear()による前ケーススパン消去（並列実行禁止制約） | ✅ |
| strands_evals | ActorSimulatorによるマルチターン会話実行（eval_goal_success_rate.py） | ✅ |
| strands_evals | run_actor_conversation（helpers関数）の利用 | ✅ |
| Amazon Bedrock | aws-bedrock-guardrailsのSTANDARDフィルタリング設定 | ✅ |
| Amazon Bedrock | PII検出：入力=false（業務情報許容）、出力=ANONYMIZE/BLOCK | ✅ |
| Pydantic v2 | TransportToolInput/TransportFormInput/ExpenseFormInputのバリデーション詳細 | ✅ |
| openpyxl | Excelファイル生成処理詳細（TL-002a/TL-002b） | ✅ |

---

## 5. 実装可能性チェック（詳細化レベル）

| コンポーネント | チェック項目 | 結果 |
|---|---|---|
| TL-001（calculate_transport_fare） | 関数シグネチャ・入力バリデーション・JSON検索ロジック・エラー処理が明記 | ✅ |
| TL-002a/TL-002b（申請書生成） | 入力モデル・Excel出力処理・ファイルパス自動生成（datetime.now().strftime）が明記 | ✅ |
| AG-001（申請受付窓口） | システムプロンプト全文・agent呼び出しパターン・リセット処理が明記 | ✅ |
| AG-002（交通費精算申請） | 動的プロンプト生成関数・17ステップCF-003・TL-001/TL-002a呼び出し詳細が明記 | ✅ |
| AG-003（経費精算申請） | 動的プロンプト生成関数・11ステップCF-004・LLM OCR処理・TL-002b呼び出し詳細が明記 | ✅ |
| ErrorHandler | classify/handle/log/messageメソッドのシグネチャ・分岐ロジック・全EX-IDメッセージが明記 | ✅ |
| LoopControlHook | 2イベントハンドラー・カウンタ管理・LoopLimitError raiseタイミングが明記 | ✅ |
| HumanApprovalHook | _build_confirmation_message・入力ループ・ToolCallCancelled raiseが明記 | ✅ |
| ガードレール | Bedrockコンソール設定値（カテゴリ/強度/アクション）が全項目明記 | ✅ |
| eval_tool_selection.py | 初期化順序・EVAL_CASES定義・run_eval_task・main処理フローが明記 | ✅ |
| eval_goal_success_rate.py | 初期化順序・EVAL_CASES定義・run_actor_conversation利用・main処理フローが明記 | ✅ |

---

## 6. 重要設計判断の一貫性チェック

| 設計判断 | チェック内容 | 結果 |
|---|---|---|
| LoopLimitError定義場所 | handlers/loop_control_hook.py内（RuntimeErrorサブクラス）で統一 | ✅ |
| HumanApprovalHookのステートレス設計 | インスタンス変数なし・シングルトン再利用可能として明記 | ✅ |
| ドラフト提示とBeforeToolCallEventの分離 | テキスト応答ステップ（ドラフト提示）とツール呼び出しステップ（HumanApprovalHook介入）が明確に分離 | ✅ |
| GRD-011 PIIマスキング方式 | applicant_name[:1]+"***"（HumanApprovalHookのAUD-004ログ）とBedrock Guardrails出力ANONYMIZE/BLOCKの2段構えで保護 | ✅ |
| 評価スクリプトの並列実行禁止 | memory_exporterのシングルトン制約に起因。両スクリプトの制約事項に明記 | ✅ |
| patch_human_approval_hook()の実行タイミング | load_dotenv()直後・エージェント生成より前に実行することをスクリプト初期化順序に明記 | ✅ |
| Bedrock Guardrailsの適用範囲 | コンテンツ安全性（GRD-011・有害コンテンツ）のみ担当。業務ロジック系（GRD-001〜010/012〜015）はエージェントプロンプト/ErrorHandler/Hookが担当 | ✅ |
| eval_goal_success_rate TC-004（GRD-005対話回数上限） | input文字列を「申請について相談したいことがあります」とし、ActorSimulatorが30ターンの上限に達することを確認するシナリオとして設計 | ✅ |
| 高額申請通知閾値の差異維持 | AG-002: 10,000円超（BRL-10交通費）、AG-003: 5,000円超（BRL-10経費）を各エージェント詳細設計で維持 | ✅ |

---

## 7. 未決事項一覧（次フェーズ以降で対処）

| ID | 内容 | 参照元 | 対応フェーズ |
|----|------|-------|-----------|
| U-001 | セッションタイムアウト・APIタイムアウト値が要件上未定義（04_basic-designから引継ぎ） | 03_system-design | 運用要件確定後 |
| U-002 | ガードレールARN・ガードレールバージョン（Bedrock Guardrails）が実装時に確定（04_basic-designから引継ぎ） | ガードレール詳細設計.md | 実装フェーズ |
| U-003 | 申請書Excelテンプレートのセル位置定義（交通費/経費）が要件上未定義（04_basic-designから引継ぎ） | 申請書生成ツール詳細設計.md | 実装フェーズ |
| U-004 | train_fares.json/fixed_fares.jsonのデータ内容（路線・運賃テーブル）が要件上未定義 | 交通費計算ツール詳細設計.md | 実装フェーズ |

---

## 8. 判定根拠まとめ

### 合格とする根拠

1. **全10成果物が artifacts/05_detailed-design/outputs/ に存在する**こと
2. **全成果物がテンプレートの全セクションを含む**こと（ツール・エージェント・ハンドラー・ガードレール・評価テストの各テンプレートに準拠）
3. **実装可能なレベルまで詳細化されている**こと（関数シグネチャ・処理フロー・エラー処理・ログID・メッセージ文字列を全成果物に明記）
4. **基本設計（04_basic-design）との完全な整合性**が確認された（ToolID・モデル名・AG-ID・SlidingWindow・ハンドラークラス名・設定値が統一）
5. **strands_evalsフレームワークの評価テスト共通設計（03_system-design/SD-08）への準拠**が確認された（Case/Experiment/evaluators/StrandsInMemorySessionMapper使用パターン）
6. **評価スクリプトのシングルトン制約（memory_exporter.clear()必須）**が両スクリプトの制約事項に明記されている
7. **GRD-001〜GRD-015の責任分担マトリクス**がガードレール詳細設計書に明示されており、コンテンツ安全性とビジネスロジック保護の役割分担が明確
8. **LoopLimitError定義場所（handlers/loop_control_hook.py）とHumanApprovalHookのステートレス設計**が明確に文書化されており、コード生成フェーズで迷いなく実装できる
9. **MET-010/MET-011の評価テストケース（計7件）**がユーザーシナリオ（交通費精算・経費精算・申請期限超過・対話回数上限・申請種別不明）を網羅している
10. **次フェーズ（06_code-generation）への引き継ぎに必要な情報**（関数シグネチャ・処理フロー・設定値・ファイルパス・ログフォーマット）が全成果物に記述されている

---

## 9. 変更履歴

| 日付 | 版 | 変更内容 | 担当 |
|-----|---|---------|------|
| 2026-05-02 | v1.0 | 初版作成 | - |
