# セッションコンテキスト

## 最終保存日時
2026-05-06

## 作業中の内容
なし（03_system-design フェーズ完了）

## 確定した決定事項
- 03_system-design フェーズを完了（2026-05-06）
- 技術スタック：Python 3.x, strands-agents 1.25.0, Amazon Bedrock (Claude Sonnet 4.5), pydantic v2+, openpyxl
- アーキテクチャ：Agent as Tools（階層型マルチエージェント）
  - AG-001（申請受付窓口・オーケストレーター）→ AG-002（交通費精算申請）/ AG-003（経費精算申請）
- ツール：TOOL-001（交通費計算・JSONファイル参照）・TOOL-002（申請書生成・Excel）
- 申請ルールナレッジ：システムプロンプト直接埋め込み（RAG不使用）
- セッション管理：ファイル永続化（data/sessions/）・SessionManager（カスタム実装）
- 会話管理：SlidingWindowConversationManager（AG-001: window_size=30、AG-002/AG-003: window_size=20）
- ループ制御：LoopControlHook（max_iterations=10）
- 人間承認：HumanApprovalHook（OK/修正/キャンセル）
- モデル設定はconfig/model_config.pyに集約
- 評価スクリプト：eval_tool_selection.py（ツール選択精度）・eval_goal_success.py（ゴール達成率）
- 評価共通ヘルパー：helpers.py（patch_human_approval_hook・create_reception_agent等）

## 未完了の指示
なし
