# セッションコンテキスト

## 最終保存日時
2026-05-02

## 作業中の内容
なし（06_code-generation フェーズ完了、全フェーズ完了）

## 確定した決定事項
- 06_code-generation フェーズを完了（2026-05-02）、全成果物作成済み、181テスト合格（1スキップ）
  - Agent の tools 属性は存在しない。`agent.tool_names`（list[str]）を使用すること
  - SlidingWindowConversationManager のインポートパス：`strands.agent.conversation_manager`（`strands.session` は不存在）
  - `@tool(context=True)` の ToolContext パラメータ名は必ず `tool_context`（`context` は不可）
  - AG-002/AG-003 の window_size：transport=20、expense=15（設計書通り。orchestrator=30）
  - fixed_fares.json の形式：`{"entries": [{"transportation_type": "バス", "fare": 220}, ...]}`（材料ファイルとは形式が異なるため直接作成）
  - TransportSegment/ExpenseItem に 90 日締切バリデーションを追加（form_generator テストが要求）
  - `patch_human_approval_hook()` を main.py 最上部でモジュールレベルインポートしてから `main()` 内で呼び出す（テスト用パッチ可能にするため）
  - 評価スクリプト（strands_evals）は strands_evals 未インストール環境では実行不可（構文チェックのみ済み）
- 05_detailed-design フェーズを完了（2026-05-02）、全10成果物作成済み、品質チェック合格
  - LoopLimitError：handlers/loop_control_hook.py 内に RuntimeError のサブクラスとして定義
  - HumanApprovalHook：ステートレス設計（インスタンス変数なし）、シングルトン再利用可能
  - ドラフト提示とBeforeToolCallEventの分離：テキスト応答ステップ（ドラフト提示）とツール呼び出しステップ（HumanApprovalHook介入）を明確に分離
  - GRD-011 PIIマスキング：applicant_name[:1]+"***"（HumanApprovalHookのAUD-004ログ）+ Bedrock Guardrails 出力 ANONYMIZE/BLOCK の2段構え
  - Bedrock Guardrails適用範囲：コンテンツ安全性（有害コンテンツ/GRD-011）のみ担当。業務ロジック系GRDはエージェントプロンプト/ErrorHandler/Hookが担当
  - 評価スクリプト並列実行禁止：memory_exporterのシングルトン制約。ケース実行前にclear()必須
  - patch_human_approval_hook()実行タイミング：load_dotenv()直後・エージェント生成前
  - 未決事項U-001〜U-004（タイムアウト値・ガードレールARN・ExcelセルマッピングはU-002/U-003として実装フェーズへ引継ぎ）
- 03_system-design フェーズを完了（2026-05-02）、全8成果物作成済み、品質チェック合格
  - 技術スタック：Python 3.x、Strands Agents v1.25.0、Amazon Bedrock（Claude Sonnet 4.5）
  - モデルID：jp.anthropic.claude-sonnet-4-5-20250929-v1:0（config/model_config.py に集約）
  - エントリーポイント：main.py
  - Agent as Tools パターン（AG-001→AG-002/AG-003 as tools）、ファクトリ関数方式
  - SlidingWindowConversationManager：AG-001 window_size=30、AG-002/AG-003 window_size=20
  - LoopControlHook：max_iterations=10（全エージェント共通）
  - HumanApprovalHook：AG-002/AG-003 のみ適用（TOOL-002 実行前）
  - リトライ：Bedrock=6回/4秒-240秒指数バックオフ、TOOL-001=6回、TOOL-002=1回
  - Pydantic v2+ バリデーション：models/data_models.py に一元管理
  - SessionManager：data/sessions/{YYYYMMDD}_{HHMMSS}_{uuid4[:8]}.json
  - invocation_state でエージェント間データ伝播（LLMプロンプト非経由）
  - 評価：strands_evals、LLM-as-Judge、二値スコア（1.0/0.0）、逐次実行
  - 評価スクリプト：evals/eval_tool_selection.py（MET-010）、evals/eval_goal_success_rate.py（MET-011）
  - 評価共通設計：evals/eval_common_system_design.md
- 02_system-requirements フェーズを完了（2026-05-02）、全18成果物作成済み、品質チェック合格
  - エージェント構成：AG-001（オーケストレーター/Lv2）、AG-002（交通費/Lv3）、AG-003（経費/Lv3）
  - ツール：TOOL-001（交通費計算）、TOOL-002（申請書生成）のみ
  - ガードレール：GRD-001〜GRD-015（入力/ルール検証/出力/実行の4カテゴリ）
  - 最重要制約：ACT-EXEC-01（申請書提出はAIが行わず社員のみ実施）
  - 最大自律度：Lv3（Lv4以上は禁止）
- 01_business-requirements フェーズを完了（2026-05-02）、全7成果物作成済み、品質チェック合格

## 未完了の指示
なし
