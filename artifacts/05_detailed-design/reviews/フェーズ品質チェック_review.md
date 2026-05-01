---
version: "1.0.0"
last_updated: "2026-05-01"
phase: "05_detailed-design"
result: "合格"
---

# 05_detailed-design フェーズ品質チェック

---

## 1. チェック対象成果物

| # | ファイル名 | 作成日 |
|---|-----------|--------|
| 1 | LoopControlHook詳細設計書.md | 2026-05-01 |
| 2 | ErrorHandler詳細設計書.md | 2026-05-01 |
| 3 | 申請書生成ツール詳細設計書.md | 2026-05-01 |
| 4 | HumanApprovalHook詳細設計書.md | 2026-05-01 |
| 5 | 交通費計算ツール詳細設計書.md | 2026-05-01 |
| 6 | 交通費精算申請エージェント詳細設計書.md | 2026-05-01 |
| 7 | 経費精算申請エージェント詳細設計書.md | 2026-05-01 |
| 8 | 申請受付窓口エージェント詳細設計書.md | 2026-05-01 |

---

## 2. テンプレート準拠チェック

| 成果物 | 必須セクション網羅 | 判定 |
|--------|-----------------|------|
| LoopControlHook詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・エラーハンドリング・ログ出力・データ設計・依存関係・テスト観点・設定値 | ✅ |
| ErrorHandler詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・実装詳細・データ設計・補足情報・依存関係・テスト観点 | ✅ |
| 申請書生成ツール詳細設計書.md | 概要・ツール一覧・各ツール設計（基本情報・インターフェース・ビジネスロジック・エラーハンドリング・ログ出力）・データ設計・補足情報・依存関係・テスト観点・設定値 | ✅ |
| HumanApprovalHook詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・実装詳細・エラーハンドリング・ログ出力・データ設計・補足情報・依存関係・テスト観点・設定値 | ✅ |
| 交通費計算ツール詳細設計書.md | 概要・ツール一覧・ツール設計（基本情報・インターフェース・ビジネスロジック・エラーハンドリング・ログ出力）・データ設計・補足情報・依存関係・テスト観点・設定値 | ✅ |
| 交通費精算申請エージェント詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・設定構成・連携設計・実装詳細・エラーハンドリング・ログ出力・データ設計・補足情報・依存関係・テスト観点 | ✅ |
| 経費精算申請エージェント詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・設定構成・連携設計・実装詳細・エラーハンドリング・ログ出力・データ設計・補足情報・依存関係・テスト観点 | ✅ |
| 申請受付窓口エージェント詳細設計書.md | 概要・設計詳細・インターフェース・ビジネスロジック・設定構成・連携設計・実装詳細・エラーハンドリング・ログ出力・データ設計・補足情報・依存関係・テスト観点 | ✅ |

---

## 3. 整合性チェック

### 3.1 横断的仕様の整合性

| チェック項目 | 内容 | 判定 |
|------------|------|------|
| LoopLimitError 定義場所 | `handlers/loop_control_hook.py` 内で定義され、全インポートが `from handlers.loop_control_hook import LoopLimitError` で統一されていること | ✅ |
| LoopLimitError フィールド | `current_iteration: int`, `max_iterations: int`, `agent_name: str` の3フィールドを持つこと | ✅ |
| EventLoopException への言及ゼロ | 全設計書で `EventLoopException` への言及が排除されていること | ✅ |
| ErrorHandler 11メソッド | 旧8メソッドが削除され、新11メソッドが全設計書で参照されていること | ✅ |
| ErrorHandler ログ出力なし | ErrorHandler 自身はログ出力・セッション更新を行わず、呼び出し元が責任を持つことが全設計書で明記されていること | ✅ |
| 出力ディレクトリ統一 | 全ファイルで `data/output/{session_id}/` に統一されていること（旧 `data/outputs/` 廃止） | ✅ |

### 3.2 ハンドラー整合性

| チェック項目 | 内容 | 判定 |
|------------|------|------|
| LoopControlHook 新ハンドラー | `BeforeModelCallEvent`, `BeforeToolCallEvent`, `AfterToolCallEvent`, `AfterInvocationEvent` の4ハンドラーが追加されていること | ✅ |
| LoopControlHook event.exception | `event.has_error` への言及がゼロで、全て `getattr(event, "exception", None) is not None` に変更されていること | ✅ |
| LoopControlHook max_iterations | AG-001/AG-002/AG-003 全て `max_iterations=30` に統一されていること | ✅ |
| LoopControlHook agent_name | AG-001="AG-001"、AG-002="transport_agent"、AG-003="expense_agent" が設定されていること | ✅ |
| HumanApprovalHook コールバックシグネチャ | `(tool_name: str, tool_params: dict) -> tuple[bool, str]` が全設計書で統一されていること | ✅ |
| HumanApprovalHook event.cancel_tool | ツール中止方法が `event.cancel_tool` へのメッセージセットで統一され、`event.stop_reason`/`event.cancel()` への言及がゼロであること | ✅ |
| HumanApprovalHook 承認対象 | 「申請書生成ツール詳細設計書に定義された全ツール関数名」への参照が明記されていること（`generate_transport_application`, `generate_expense_application`） | ✅ |

### 3.3 ツール整合性

| チェック項目 | 内容 | 判定 |
|------------|------|------|
| applicant_name/application_date 取得方式 | 申請書生成ツール・エージェント設計書の両方で「invocation_state から取得」に統一されていること（LLMパラメータとして渡す記述が排除されていること） | ✅ |
| 交通費申請書セルマッピング | A=No, B=移動日, C=出発地, D=目的地, E=交通手段, F=費用, G=業務目的, H=承認状況（空欄）で統一されていること | ✅ |
| 経費申請書セルマッピング | A=No, B=購入日, C=店舗名, D=品目, E=経費区分, F=金額, G=業務目的, H=承認状況（空欄）で統一されていること | ✅ |
| ファイル保存エラー戻り値 | `(False, エラーメッセージ)` タプルに統一されていること | ✅ |
| generate() エラー戻り値 | `{"success": False, "message": エラーメッセージ}` dict に統一されていること | ✅ |
| os.path.exists() 事前チェック | 全データファイルアクセスで `os.path.exists()` 事前チェックが使用され、`open()` 時の `FileNotFoundError` 捕捉との併用が禁止されていること | ✅ |
| 交通費計算ツール ファイルパス | `/data/train_routes.json`, `/data/fixed_fares.json` に統一されていること | ✅ |
| 固定運賃JSONキー | `{"バス": int, "タクシー": int, "飛行機": int}` の日本語キー形式に統一されていること | ✅ |
| リスト線形探索 | 交通費計算ツールの経路検索がリスト線形探索で統一されていること（辞書キー参照不使用） | ✅ |
| ValueError 使用 | 経路未存在/キー不存在の異常系が `ValueError` で統一されていること（`KeyError` 不使用） | ✅ |
| FileNotFoundError ログレベル | ファイル不存在時のログレベルが WARNING に統一されていること | ✅ |
| image_reader 使用 | AG-003 が領収書 OCR に `strands_tools` の `image_reader` を使用することが明記されていること | ✅ |

### 3.4 エージェント整合性

| チェック項目 | 内容 | 判定 |
|------------|------|------|
| AG-002 実装命名 | `transport_agent` で統一されていること | ✅ |
| AG-003 実装命名 | `expense_agent` で統一されていること | ✅ |
| 専門エージェント 個別例外捕捉 | AG-002/AG-003 が LoopLimitError/ContextWindowOverflowException/MaxTokensReachedException/RuntimeError/Exception を個別に捕捉し、エラー戻り値型が `str` であること | ✅ |
| AG-001 個別例外捕捉 | AG-001 が KeyboardInterrupt(INFO+break)/LoopLimitError(WARNING+continue)/ContextWindowOverflowException(WARNING+continue)/MaxTokensReachedException(WARNING+continue)/RuntimeError(ERROR+continue)/Exception(ERROR+continue) を個別に捕捉していること | ✅ |
| ログクエリ先頭50文字 | AG-002/AG-003 の例外捕捉時ログに `query[:50]` が含まれること | ✅ |
| 全ログ session_id 含む | AG-001 の例外捕捉時ログに `session_id` が含まれること | ✅ |
| 日本語ログ | 全エージェント・全ツールのログメッセージが日本語化されていること | ✅ |
| 申請者名マスキング | 全エージェントのログで申請者名が `****` でマスキングされることが明記されていること | ✅ |
| 妥当性チェックルール外部参照 | AG-002 が `agent_knowledge/transportation_policies.py`、AG-003 が `agent_knowledge/receipt_policies.py` を参照することが明記されていること | ✅ |
| AG-001 ウェルカムメッセージ | 起動時ウェルカムメッセージが定義されていること（内容・フォーマット仕様準拠） | ✅ |
| AG-001 入力プロンプト | `\n\n入力内容（終了時はquit）: ` に変更されていること | ✅ |
| session_id 生成方式 | `datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex[:8]` が AG-001 設計書に明記されていること | ✅ |

---

## 4. 04_basic-design 残存未定義項目の解決状況

| 項目 | 04_basic-design での状態 | 詳細設計での解決状況 |
|-----|------------------------|-------------------|
| 対話回数上限チェック実装方法 | 「AG-001 が入力カウンタを管理する方式を想定」として持ち越し | ✅ 解決: `_run_repl` 関数内の対話カウンタで管理。上限30回到達時に上限メッセージ表示・終了として明記 |
| 文字列フィールドの最大長 | 要件上未定義 | ⚠️ 未解決: 申請者名・業務目的・店舗名・品目の最大長は実装フェーズで確定 |
| セッションタイムアウト | 要件上未定義 | ⚠️ 未解決: セッションファイルの保持期間・タイムアウト処理は実装フェーズで確定 |

---

## 5. 品質チェック結果

| チェック分類 | 結果 |
|------------|------|
| テンプレート準拠 | ✅ 全8ファイル合格 |
| 横断的仕様整合性 | ✅ 合格 |
| ハンドラー整合性 | ✅ 合格 |
| ツール整合性 | ✅ 合格 |
| エージェント整合性 | ✅ 合格 |
| 04_basic-design 残存項目の引き継ぎ | ✅ 確認済み（2件は実装フェーズへ継続） |

**総合判定: ✅ 合格**

---

## 6. 残存する未定義項目（要件上未定義・実装フェーズで確定）

| 項目 | 内容 | 詳細 |
|-----|------|------|
| 文字列フィールドの最大長 | 申請者名・業務目的・店舗名・品目の文字列フィールドに対する上限文字数が要件上未定義 | Pydantic モデルの `max_length` バリデーターを実装フェーズで追加する |
| セッションタイムアウト | セッションファイル（`data/sessions/session_{id}.json`）の保持期間・タイムアウト自動クローズ処理が未定義 | 実装フェーズで定義する（例: 24時間無操作で TERMINATED 遷移） |
| agent_knowledge ポリシーファイルの内容 | `agent_knowledge/transportation_policies.py` および `agent_knowledge/receipt_policies.py` のファイル内容（具体的なルール記述）が未定義 | 実装フェーズで作成する（BRL-10〜BRL-18 等の業務ルールをコードまたはドキュメントとして定義） |
| invocation_state 受け渡し時の `approved` フラグ | HumanApprovalHook が承認後に `session_{id}.json` へ `approval_granted=True` を記録するが、エージェントが该フラグを読み取るタイミング・用途が未明示 | 実装フェーズで FileBasedSessionManager の読み取り仕様として確定 |

---

## 7. 備考

- `image_reader`（strands_tools）は AG-003 の `tools` リストに追加済みとして設計。実装時に `strands_tools` パッケージの正確なインポート方法を確認すること
- `agent_knowledge/transportation_policies.py` および `agent_knowledge/receipt_policies.py` は本フェーズで参照先として定義されたが、ファイル本体の作成は実装フェーズに持ち越し
- `FileBasedSessionManager` の `approval_granted` 書き込みは `HumanApprovalHook._handle_approved()` から呼び出される設計だが、読み取り側の実装詳細は実装フェーズで確定
- v1.0 (初版): 18項目の仕様変更（LoopLimitError 追加、ErrorHandler 11メソッド刷新、セルマッピング変更、invocation_state 取得方式変更、os.path.exists() 事前チェック、日本語ログ・申請者名マスキング等）をすべて詳細設計書に反映済み
