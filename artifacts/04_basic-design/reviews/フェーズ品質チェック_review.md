# 04_basic-design フェーズ品質チェック

## チェック実施日
2026-04-28（初版）、2026-04-28（v2.1修正後再チェック）

## チェック対象成果物

| 成果物 | ファイルパス |
|--------|------------|
| 交通費計算ツール基本設計書 | artifacts/04_basic-design/outputs/交通費計算ツール基本設計書.md |
| 申請書生成ツール基本設計書 | artifacts/04_basic-design/outputs/申請書生成ツール基本設計書.md |
| データモデル基本設計書 | artifacts/04_basic-design/outputs/データモデル基本設計書.md |
| AG-001 申請受付窓口エージェント基本設計書 | artifacts/04_basic-design/outputs/AG-001_申請受付窓口エージェント基本設計書.md |
| AG-002 交通費精算申請エージェント基本設計書 | artifacts/04_basic-design/outputs/AG-002_交通費精算申請エージェント基本設計書.md |
| AG-003 経費精算申請エージェント基本設計書 | artifacts/04_basic-design/outputs/AG-003_経費精算申請エージェント基本設計書.md |
| ErrorHandler基本設計書 | artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md |
| セッションマネージャ基本設計書 | artifacts/04_basic-design/outputs/セッションマネージャ基本設計書.md |

---

## 品質チェック項目

### 1. テンプレート準拠チェック

| 成果物 | テンプレート準拠 | 確認内容 |
|--------|---------------|---------|
| 交通費計算ツール基本設計書 | ✅ 合格 | ツール基本設計テンプレートの全セクション（1.基本情報〜10.変更履歴）が含まれている |
| 申請書生成ツール基本設計書 | ✅ 合格 | ツール基本設計テンプレートの全セクションが含まれている。generate_travel_expense_form・generate_expense_formの2関数を統合設計 |
| データモデル基本設計書 | ✅ 合格 | データモデル基本設計テンプレートに準拠。Pydanticモデル一覧・バリデーション方針・変更履歴を含む |
| AG-001基本設計書 | ✅ 合格 | エージェント基本設計テンプレートの全17セクションが含まれている。オーケストレーター専用セクション（Section 5連携設計）あり |
| AG-002基本設計書 | ✅ 合格 | エージェント基本設計テンプレートの全17セクションが含まれている |
| AG-003基本設計書 | ✅ 合格 | エージェント基本設計テンプレートの全17セクションが含まれている |
| ErrorHandler基本設計書 | ✅ 合格 | ハンドラー基本設計テンプレートに準拠。HD-001/HD-002/HD-003の3ハンドラーを記載 |
| セッションマネージャ基本設計書 | ✅ 合格 | セッションマネージャ基本設計テンプレートの全15セクションが含まれている |

### 2. システム設計との整合性チェック

| チェック観点 | 結果 | 確認内容 |
|-----------|------|---------|
| 例外処理方針.mdとの整合 | ✅ 合格 | ErrorHandler基本設計書のメソッド（EX-01〜EX-08）が例外処理方針の例外分類と一致している |
| 実行制御方針.mdとの整合 | ✅ 合格 | LoopControlHookのmax_iterations=10・登録イベント（BeforeInvocationEvent/AfterModelCallEvent/AfterInvocationEvent）が実行制御方針と一致している |
| 共通設定方針.mdとの整合 | ✅ 合格 | AG-001: SlidingWindow(30)、AG-002: SlidingWindow(20)、AG-003: SlidingWindow(15)。HumanApprovalHookはAG-002/AG-003のみに適用 |
| バリデーション方針.mdとの整合 | ✅ 合格 | invocation_stateは辞書リテラル（Pydanticモデル不使用）。ツール入力はPydanticモデルで検証 |
| マルチエージェント連携設計.mdとの整合 | ✅ 合格 | Agent as Toolsパターン、invocation_stateスキーマ（session_id/applicant_name/application_date）、ファクトリ関数パターンが一致 |
| セッション管理方針.mdとの整合 | ✅ 合格 | FileSessionManager使用、data/sessions/保存先、セッション終了時削除方針が一致 |

### 3. コンポーネント間整合性チェック

| チェック観点 | 結果 | 確認内容 |
|-----------|------|---------|
| AG-001のinvocation_state定義 | ✅ 合格 | AG-001が送出する`{session_id, applicant_name, application_date}`がAG-002/AG-003の受信定義と一致 |
| AG-002のTOOL-001/TOOL-002利用 | ✅ 合格 | AG-002はTOOL-001(calculate_travel_expense)とTOOL-002(generate_travel_expense_form)のみ使用。generate_expense_formは不使用 |
| AG-003のTOOL-002利用 | ✅ 合格 | AG-003はTOOL-002(generate_expense_form)のみ使用。TOOL-001および generate_travel_expense_form は不使用 |
| HumanApprovalHookの対象エージェント | ✅ 合格 | 自律度・権限定義のAG-002/AG-003（ACT-GEN-01, Lv3, 承認者R-EMP）およびGRD-016（対象AG-002/AG-003）と一致。AG-001には登録しない |
| LoopControlHookの全エージェント適用 | ✅ 合格 | AG-001/AG-002/AG-003の全エージェントにLoopControlHook(max_iterations=10)を適用 |
| ErrorHandlerの委譲チェーン | ✅ 合格 | ツール→エージェント→ErrorHandlerの3層伝播設計が例外処理方針7.1節と一致 |
| AG-003のimage_reader記載 | ✅ 合格 | image_readerはStrands SDK フレームワーク提供機能（TOOL-XXX未登録）のため利用ツールに記載なし。注意書きとして言及 |
| システムプロンプト生成方式 | ✅ 合格 | AG-001: 静的定数（CF-001/CF-002に日付判断なし）、AG-002: 動的生成（BRL-13要件）、AG-003: 動的生成（BRL-18要件）が正しく設計されている |
| ファクトリ関数パターン | ✅ 合格 | _get_travel_agent(session_id) / _get_expense_agent(session_id)がAG-002/AG-003基本設計書とセッションマネージャ基本設計書で一致 |

### 4. 次フェーズへの引き継ぎ情報の完備チェック

| チェック観点 | 結果 | 確認内容 |
|-----------|------|---------|
| 詳細設計への引き渡し事項 | ✅ 合格 | 全成果物に「詳細設計書X章を参照」の参照先が記載されている |
| プロンプト全文の引き渡し | ✅ 合格 | AG-001/AG-002/AG-003の各プロンプト全文は「詳細設計書 2.3.1章を参照」として引き渡している |
| ツール実装の引き渡し | ✅ 合格 | TOOL-001/TOOL-002の関数シグネチャ・バリデーション詳細は詳細設計書への引き渡し事項として明記 |
| クラス名・メソッド名の確定 | ✅ 合格 | ErrorHandler・HumanApprovalHook・LoopControlHookのクラス名が英語で確定済み。FileSessionManagerの利用方針も確定 |
| コンポーネントIDの付与 | ✅ 合格 | HD-001(ErrorHandler)/HD-002(HumanApprovalHook)/HD-003(LoopControlHook)/SM-001(FileSessionManager)/DM-001(data_models)が付与されている |

---

## 総合評価

**結果: ✅ 合格**

全8成果物がテンプレートに準拠しており、システム設計との整合性・コンポーネント間整合性・次フェーズへの引き継ぎ情報の完備を確認した。

---

## 未定義項目（要件上未定義として引き継ぐ事項）

以下の項目は上流要件で未定義のため、詳細設計フェーズでも「要件上未定義」として扱う。

| 項目 | 出典 | 備考 |
|-----|------|------|
| エスカレーション先（システム管理者連絡先） | 業務ルール定義 BRL-10 | 要件確定後に定義 |
| 差し戻しリスク判定基準の詳細 | 業務ルール定義 BRL-08 | 要件上未定義のまま |
| Amazon Bedrockタイムアウト値 | 実行制御方針 U-001 | Strands Agents SDKデフォルト値を使用 |
| ログの保存期間 | セッション管理方針 U-001 | 要件確定後に設定 |
| TOOL-001/TOOL-002のタイムアウト値 | 実行制御方針 U-002/U-003 | 要件確定後に設定 |
