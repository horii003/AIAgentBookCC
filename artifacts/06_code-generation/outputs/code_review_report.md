# コードレビュー報告書

**レビュー日**: 2026-07-03  
**対象フェーズ**: 06_code-generation  
**レビュー担当**: Claude Sonnet 4.6（IG-04 自動レビュー）

---

## 対象ファイル一覧

### 実装コード（IG-02）

| ファイル | 役割 |
|---------|------|
| `agents/base_agent.py` | 専門エージェント共通ファクトリー・呼び出しラッパー |
| `agents/orchestrator_agent.py` | AG-001 オーケストレーターエージェント |
| `agents/transport_application_agent.py` | AG-002 交通費精算申請エージェント（Agent as Tools） |
| `agents/expense_application_agent.py` | AG-003 経費精算申請エージェント（Agent as Tools） |
| `config/model_config.py` | Bedrock モデル設定 |
| `config/settings.py` | エージェント動作パラメータ一元管理（pydantic-settings） |
| `handlers/error_handler.py` | エラーメッセージ生成ヘルパー・LoopLimitError 定義 |
| `handlers/human_approval_hook.py` | HitL 承認フック（BeforeToolCallEvent） |
| `handlers/loop_control_hook.py` | ReAct ループ上限制御フック |
| `handlers/console_approval_adapter.py` | コンソール入力アダプター |
| `knowledge/transport_policies.py` | 交通費精算ポリシー文字列生成 |
| `knowledge/expense_policies.py` | 経費精算ポリシー文字列生成 |
| `main.py` | アプリケーションエントリーポイント |
| `models/data_models.py` | Pydantic データモデル群 |
| `prompt/prompt_orchestrator.py` | AG-001 システムプロンプト定数 |
| `prompt/prompt_transport.py` | AG-002 システムプロンプト生成関数 |
| `prompt/prompt_expense.py` | AG-003 システムプロンプト生成関数 |
| `session/session_manager.py` | FileSessionManager ファクトリー |
| `tools/transport_tools.py` | 交通費計算ツール（calculate_transport_fare） |
| `tools/output_generator.py` | 申請書生成ツール（generate_*_expense_form） |

### 評価テストコード（IG-03）

| ファイル | 役割 |
|---------|------|
| `evals/helpers.py` | テレメトリ・エージェント生成・ActorSimulator 共通ヘルパー |
| `evals/eval_tool_selection.py` | MET-001 評価スクリプト（シングルターン） |
| `evals/eval_goal_success_rate.py` | MET-003 評価スクリプト（マルチターン） |
| `evals/cases/tool_selection_cases.py` | TC_TOOL_001〜003 テストケース定義 |
| `evals/cases/goal_success_rate_cases.py` | TC_GOAL_001〜003 テストケース定義 |

### テストコード（IG-02 単体・結合テスト）

| ファイル | 役割 |
|---------|------|
| `tests/unit/test_*.py`（17ファイル） | 各モジュールの単体テスト（計203件） |
| `tests/integration/test_multi_agent_flow.py` | マルチエージェント連携結合テスト（10件） |

---

## CL チェックリスト結果（CL-1〜CL-5）

**指摘なし（0件）**

### CL-1 Strands SDK パターン（実装コード対象）

| チェック項目 | 結果 |
|------------|------|
| CL-1.1 Agent() コンストラクタ（callback_handler=None / SlidingWindow / ModelRetryStrategy / session_manager / hooks） | ✅ 全エージェントで設定済み |
| CL-1.2 @tool デコレータ（invocation_state アクセスツールは context=True / 不要なツールは @tool のみ） | ✅ calculate_transport_fare は @tool のみ、generate_*_form は @tool(context=True) で正しく設定 |
| CL-1.3 @tool docstring（tool_context は Args: に記述しない / list/dict 型パラメータに展開説明あり） | ✅ tool_context は Note: セクションに分離、sections/items の各フィールドが docstring に展開済み |
| CL-1.4 invocation_state 受け渡し（子エージェントには session_id を除いて渡す） | ✅ base_agent.py の child_invocation_state から session_id を除外して渡す設計通り |
| CL-1.5 HookProvider（registry.add_callback / BeforeToolCallEvent フィルタ / event.cancel_tool） | ✅ LoopControlHook・HumanApprovalHook ともに設計準拠 |

### CL-2 コード品質

| チェック項目 | 結果 |
|------------|------|
| CL-2.1 DRY 原則 | ✅ 申請書生成の共通処理は _load_template / _save_file ヘルパーに抽出済み。専門エージェント共通処理は base_agent.py で集約 |
| CL-2.2 例外処理（LoopLimitError → Exception の順） | ✅ base_agent.py・orchestrator_agent.py ともに LoopLimitError を先にキャッチしてから Exception をキャッチ |
| CL-2.3 Pydantic バリデーター（classmethod で直接渡す） | ✅ `classmethod(_cls_xxx)` パターンで正しく定義されている |
| CL-2.4 キャッシュ・遅延ロード（None チェックで「未ロード」判定） | ✅ transport_tools.py で `_train_fares_cache is None` で判定。ModelConfig.get_model() は @lru_cache(maxsize=1) でキャッシュ |
| CL-2.5 未使用コード・インポート | ✅ 各ファイルのインポートはすべて使用済み |
| CL-2.6 エラー返却キー名 | ✅ ツール関数のエラー返却は `{"success": False, "message": ...}` で統一。出力 Pydantic モデルとの不一致なし |

### CL-3 ディレクトリ・ファイル名規約

| チェック項目 | 結果 |
|------------|------|
| knowledge/ ディレクトリ名 | ✅ |
| 静的マスタデータは data/ に配置 | ✅ train_fares.json / fixed_fares.json を data/ にも配置（運用時の参照先は template/ に正規化済みコピー） |
| テンプレートファイルは template/ に配置 | ✅ |
| 出力ファイルは output(s)/ に配置 | ✅ output_generator.py の _OUTPUT_DIR = "outputs" |
| ファイル名命名規則 | ✅ スネークケース、エージェントは *_agent.py、ツールは *_tools.py |

### CL-4 設定・環境変数

| チェック項目 | 結果 |
|------------|------|
| .env.template に必要な環境変数が記載されているか | ✅ pyproject.toml 内の .env.template に AWS_* / ECAAS_* / LOG_LEVEL / JUDGE_MODEL_ID を記載 |
| ビジネスルール値を settings.py で一元管理 | ✅ deadline_months / approval_threshold / window_size / max_iterations を settings.py で管理 |
| ポリシー関数は設定値を引数で受け取る | ✅ get_transport_rules(deadline_months, approval_threshold) / get_expense_rules(deadline_months, approval_threshold) で動的展開 |

### CL-5 ログ出力

| チェック項目 | 結果 |
|------------|------|
| ログを出力するモジュール先頭に _logger = logging.getLogger(__name__) | ✅ 全モジュールで設定済み |
| ログを出力しない薄いラッパーモジュールに _logger を定義しない | ✅ prompt/*.py / models/data_models.py 等の薄いモジュールには _logger なし |
| ErrorHandler クラス内でログ出力しない | ✅ ErrorHandler は文字列生成のみ。ログ出力は呼び出し元の責務として分離されている |
| エラー時 _logger.error() に exc_info=True | ✅ base_agent.py / orchestrator_agent.py / transport_tools.py / output_generator.py で exc_info=True を適切に設定 |

---

## 熟練技術者視点レビュー結果（3.1〜3.6）

**指摘なし（0件）**

### 3.1 設計・アーキテクチャ

- **責務の分離**: OrchestratorAgent（対話ループ）・SpecialistAgent（申請フロー）・Tool（計算・生成）が明確に分離されている。base_agent.py が共通ロジックを集約し、各専門エージェントは設定とビルド関数のみを定義する薄いラッパーになっている。
- **依存関係**: 設計書通り。AG-001 → AG-002/AG-003 の委譲が @tool(context=True) パターンで実現されており、LLM のツール選択に委ねる設計と一致している。
- **抽象化レベル**: Agent レイヤー（invoke_specialist_agent）・ツールレイヤー（calculate_transport_fare）・インフラレイヤー（_load_fare_data）の3層が適切に分離されている。
- **設計書に記載のない仕様の追加**: 確認できない。

### 3.2 セキュリティ

- **外部入力バリデーション**: ユーザー入力はすべて Pydantic モデル（TransportSectionInput / TransportExpenseFormInput / GeneralExpenseFormInput）で検証されており、ValidationError は ErrorHandler でユーザー向け日本語メッセージに変換される。内部実装の詳細（スタックトレース・フィールド名等）はユーザーに露出しない。
- **機密情報のログ出力**: APIキー・認証情報はログに出力していない。applicant_name はログに含まれるが、業務上の申請者名であり問題ない範囲。
- **エラーメッセージの情報漏洩**: ErrorHandler は固定文字列のみ返す設計のため、内部エラーの詳細が漏洩しない。

### 3.3 堅牢性・信頼性

- **想定外入力への対処**: Pydantic バリデーターが None・空文字・型不一致を適切に処理している。`validate_non_empty_string` / `parse_date` / `normalize_transport_type` 等で境界値処理を実装。
- **無限ループ防止**: LoopControlHook が max_iterations（AG-001: 10、AG-002/AG-003: 設定値）で LoopLimitError を raise。ModelRetryStrategy でリトライ上限（最大 max_attempts=6）を設定。
- **外部 API エラーハンドリング**: ContextWindowOverflowException / MaxTokensReachedException を orchestrator_agent.py で個別にキャッチしてユーザーメッセージを提示。
- **セッション整合性**: session_id は OrchestratorAgent が管理し、子エージェントには session_id を渡さない設計（base_agent.py の child_invocation_state から除外）により、セッション境界が明確に保たれている。

### 3.4 保守性・可読性

- **単一責務**: 各関数・クラスが単一の責務を持っており、30行の目安を超える関数でも複数の明確なセクション（バリデーション → データ取得 → 書き込み → 保存）に分かれている。
- **マジックナンバー・マジック文字列**: ビジネスルール値（deadline_months / approval_threshold / window_size 等）は settings.py で一元管理されている。セル番地（B3、B4等）は Excel テンプレートの構造を直接反映しており、設計書のテンプレート定義と整合する。
- **コメント**: 重要な設計上の判断（HumanApprovalHook の2層承認構造、LoopControlHook のリセットタイミング等）に適切にコメントが付いている。

### 3.5 パフォーマンス

- **ループ内の重い処理**: `_load_fare_data()` は `_train_fares_cache is None` のガードにより初回のみファイルを読み込む。ModelConfig.get_model() は `@lru_cache(maxsize=1)` でキャッシュ。
- **エージェントインスタンスの再生成**: transport_application_agent/@tool が呼ばれるたびに Agent インスタンスを生成するが、これは FileSessionManager による会話履歴の継続性を保つための設計上の意図的な選択（docstring に明記）。

### 3.6 テストの妥当性

- **正常系・異常系・境界値の網羅**: 各単体テストは正常系に加え、バリデーションエラー・空文字・不正形式・境界値のケースを網羅。TransportSectionInput・validate_non_empty_string 等の Pydantic バリデーターテストは境界条件を充実。
- **モックの妥当性**: openpyxl.load_workbook・os.path.exists 等の外部依存は適切にモックされており、テスト対象の処理に集中できる構成。invocation_state の伝播テストは実際のコールバック関数を使ったキャプチャパターンで実際の挙動を模倣。
- **結合テストのカバレッジ**: test_multi_agent_flow.py がセッションマネージャー初期化・ツール→フォーム生成フロー・HumanApprovalHook キャンセル・LoopLimitError 伝播・invocation_state 伝播の5つの主要連携パスをカバー。

---

## 指摘事項一覧

なし。

---

## サマリー

- 重要度「高」: **0件**
- 重要度「中」: **0件**
- 重要度「低」: **0件**

---

## 総評

生成コードは詳細設計書との整合性・命名規則・Strands SDK の使用パターン・セキュリティ・堅牢性・テストカバレッジのすべての観点で設計意図を正確に実装している。指摘事項は0件であり、修正は不要。

✅ コードレビュー完了：指摘事項は0件でした。
