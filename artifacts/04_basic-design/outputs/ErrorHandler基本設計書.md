# ハンドラー 基本設計書

> **参照元（システム要件定義資料）:**
> - artifacts/02_system-requirements/outputs/エージェント一覧.md（利用エージェントの特定）
> - artifacts/02_system-requirements/outputs/機能ツール一覧.md（利用ツールの特定）
> - artifacts/02_system-requirements/outputs/会話フロー一覧.md（ハンドラーが介入する会話フロー）
> - artifacts/02_system-requirements/outputs/自律度・権限定義.md（承認制御の要件）
> - artifacts/02_system-requirements/outputs/ガードレール要件定義.md（ガードレール制御の要件）
> - artifacts/02_system-requirements/outputs/ログ出力要件定義.md（ログ出力の要件）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（ErrorHandlerの設計方針）
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | HD-001 (ErrorHandler), HD-002 (HumanApprovalHook), HD-003 (LoopControlHook) |
| コンポーネント名 | ErrorHandler, HumanApprovalHook, LoopControlHook |
| コンポーネント種別 | ハンドラー（横断的機能） |
| 業務ドメイン | システム全体 |
| 対象業務 | 例外処理・エスカレーション管理（BIZ-01〜BIZ-05全体）、申請書生成前の利用者承認取得（BIZ-03）、ReActループ暴走防止（全業務） |
| 関連機能ID | FR-011（差し戻しリスク評価）、FR-012（申請期限チェック）、FR-013（上長承認要否判定）、FR-014（エスカレーション案内）、FR-016（入力文字数制限）、FR-017（対話ターン数制限） |
| 業務要件対応ID | BRL-06（申請書確認取得）、BRL-09（申請書自動提出禁止）、BRL-10（エスカレーション）、GRD-016（TOOL-002実行前確認）、GRD-018（対話ターン数制限） |

**詳細**: 詳細設計書を参照

---

## 2. ErrorHandler 基本設計

**システム設計書の方針**: システム設計書 例外処理方針.md（`artifacts/03_system-design/outputs/例外処理方針.md`）を参照してください。

### 2.1 ErrorHandlerの位置づけ

#### システム全体における役割
- 全エージェント（AG-001/AG-002/AG-003）・全ツール（TOOL-001/TOOL-002）で発生した例外を一元的に分類・処理し、ユーザー向けメッセージ生成とログ記録を担う
- 例外処理方針.md の例外分類（EX-01〜EX-08）ごとに継続可否を判定し、対応方針（代替処理・エスカレーション・中断）を決定する
- スタックトレース等の技術的詳細をログにのみ記録し、ユーザーには抽象化されたメッセージを提示する

#### 主な責務（概要）
- **例外分類・継続可否判定**: 発生した例外をEX-01〜EX-08に分類し、継続・代替処理・エスカレーション・中断を決定する
- **ユーザー向けメッセージ生成**: 例外種別に応じた日本語メッセージを生成し、次のアクション（再入力・システム管理者連絡等）を提示する
- **ログ記録**: 例外発生時のERROR/CRITICALレベルのログをlogs/error.logに記録する（error_type・error_message・context・timestamp・必要に応じてスタックトレース）

#### 非責務（やらないこと）
- **例外の検知**: エージェント（AG-001/AG-002/AG-003）またはツール（TOOL-001/TOOL-002）が担当する
- **セッション状態の直接変更**: Strands Agents SDKが担当する
- **ビジネスロジックの実行（申請期限チェック・上長承認判定等）**: エージェントが担当する

#### 詳細
詳細設計書 2章を参照

### 2.2 利用コンポーネント

| コンポーネントID | コンポーネント名 | 利用目的 |
|----------------|----------------|---------|
| AG-001 | 申請受付窓口エージェント | 申請種別判定不能（EX-02）・AG-002/AG-003内部エラー（EX-04〜EX-08）・ループ上限到達時のエラー処理委譲 |
| AG-002 | 交通費精算申請エージェント | TOOL-001/TOOL-002エラー（EX-01/EX-06/EX-07）・申請期限超過（EX-03）・ループ上限到達時のエラー処理委譲 |
| AG-003 | 経費精算申請エージェント | TOOL-002エラー（EX-01/EX-06/EX-07）・申請期限超過（EX-03）・ループ上限到達時のエラー処理委譲 |
| TOOL-001 | 交通費計算ツール | 経路テーブル未登録（EX-06代替処理）・バリデーションエラー（EX-01）時のエラー処理委譲 |
| TOOL-002 | 申請書生成ツール | テンプレートファイルなし（EX-07/EX-06）・バリデーションエラー（EX-01）時のエラー処理委譲 |

### 2.3 主要メソッド一覧

| メソッド名 | 目的 | 対応する例外分類 | 利用タイミング |
|-----------|-----|----------------|--------------|
| handle_input_error() | ユーザー入力不正・必須項目不足時に再入力を促すメッセージを生成してログ記録する | EX-01 | UserInputTextバリデーション失敗時・必須項目未収集時 |
| handle_ambiguous_decision() | LLM判断不能時に選択肢提示メッセージを生成してログ記録する | EX-02 | 申請種別判定不能（BRL-02）・経費区分判断不能（BRL-17）時 |
| handle_business_rule_violation() | 申請期限超過等の業務ルール違反時に通知メッセージを生成してセッション終了を促す | EX-03 | 申請期限超過（BRL-13/BRL-18）・申請書自動提出違反（BRL-09）時 |
| handle_external_api_error() | LLM接続エラー等の外部I/F例外時にエスカレーションメッセージを生成してログ記録する | EX-04 | Amazon Bedrockリトライ全失敗後 |
| handle_unauthorized_action() | 権限違反・状態不整合時にエスカレーションメッセージを生成してセッション終了を促す | EX-05 | TOOL-002の利用者確認前呼び出し試行・AG-003によるTOOL-001呼び出し試行時 |
| handle_data_inconsistency() | データ不整合時に代替処理（手動入力促し）またはエスカレーションメッセージを生成する | EX-06 | 運賃データ未登録（代替処理）・テンプレートファイルなし（エスカレーション）・Pydanticバリデーションエラー時 |
| handle_system_error() | ファイルI/Oエラー等のシステム障害時にエスカレーションメッセージを生成してログ記録する（スタックトレース必須） | EX-07 | セッション/ログ/申請書のファイルI/Oエラー時 |
| handle_unexpected_error() | 未分類の想定外例外時にエスカレーションメッセージを生成してログ記録する（スタックトレース必須） | EX-08 | except Exceptionで補足した未分類例外時 |
| log_error() | EX分類・エラーメッセージ・コンテキスト（session_id・agent_id・tool_name）・タイムスタンプをlogs/error.logにERROR/CRITICALレベルで記録する | EX-01〜EX-08（全分類） | 各例外処理メソッドの内部から呼び出す |

### 2.4 メソッドの詳細
詳細設計書 2.3章を参照

### 2.5 ErrorHandlerの設計方針と設計意図

**例外処理方針.mdへの準拠**:
- EX-01（入力例外）・EX-02（判断不能）・EX-06（バリデーションエラー）は代替処理（再入力促し・選択肢提示）で継続する
- EX-03（業務ルール違反）は対応方針マトリクスに従い申請不可通知または中断とする
- EX-04〜EX-08はエスカレーション案内→セッション終了とする

**エラー伝播の責務分担**:
- ツール関数は例外を再送出せず `{"success": False, "message": エラーメッセージ}` を返す
- エージェントは受け取ったエラーをErrorHandlerへ委譲する
- ErrorHandlerはユーザー向けメッセージを生成して呼び出し元へ返す

**主要な設計意図**:
- **ユーザーフレンドリーなエラー隠蔽**: スタックトレース・SDK内部エラーをログにのみ記録し、ユーザーには業務言語での抽象化メッセージのみを提示する
- **次アクションの必須提示**: 全エラーメッセージに再入力・再試行・システム管理者連絡等の次アクションを含め、ユーザーが迷わないようにする
- **EventLoopException対応**: EventLoopExceptionの `__cause__` でLoopLimitErrorを判定する2層構造でキャッチする（LoopControlHookとの連携）

**詳細**: 詳細設計書 2.5章を参照

---

## 3. HumanApprovalHook 基本設計

**システム設計書の方針**: システム設計書 実行制御方針.md（`artifacts/03_system-design/outputs/実行制御方針.md`）を参照してください。

### 3.1 HumanApprovalHookの位置づけ

#### システム全体における役割
- AG-002/AG-003がTOOL-002（申請書生成）を呼び出す直前にブロックし、利用者（R-EMP）の明示的なOK/修正/キャンセル選択を取得する
- GRD-016（申請書の利用者最終確認なしに確定操作禁止）およびBRL-06（申請書確認取得）を技術的に強制する
- 承認操作（OK/修正/キャンセル）の結果と実行時刻をDATA-009（承認ログ）として記録する

#### 主な責務（概要）
- **TOOL-002呼び出しのブロック**: BeforeToolCallEventでTOOL-002の実行をインターセプトし、利用者確認を取得するまでブロックする
- **OK/修正/キャンセルの3択提示**: 収集済み申請情報サマリーを提示し、利用者の選択を取得する
- **承認ログ記録**: 承認操作の選択結果・実行時刻をDATA-009として記録する

#### 非責務（やらないこと）
- **TOOL-002以外のツール実行のブロック**: TOOL-001は承認不要。TOOL-001の実行はブロックしない
- **AG-001へのフック登録**: AG-001はTOOL-002を利用しないため登録しない
- **申請情報の検証**: Pydanticバリデーションおよびガードレールチェック（GRD-002/GRD-010等）はエージェントが担当する

#### 詳細
詳細設計書 3章を参照

### 3.2 利用エージェント

| エージェントID | エージェント名 | 利用目的 |
|---------------|---------------|---------|
| AG-002 | 交通費精算申請エージェント | generate_travel_expense_form（TOOL-002）呼び出し前の利用者確認取得（BRL-06、GRD-016） |
| AG-003 | 経費精算申請エージェント | generate_expense_form（TOOL-002）呼び出し前の利用者確認取得（BRL-06、GRD-016） |

> ※ 承認必須アクション（△）の特定根拠:
> - 自律度・権限定義.md エージェント×アクションマトリクス: AG-002・AG-003のACT-GEN-01（申請書ドラフト生成）が最大自律度Lv3（承認者ロール: R-EMP）
> - ガードレール要件定義.md GRD-016: 対象エージェント = AG-002, AG-003
> - AG-001: ACT-GEN-01が×（実行不可）のためHumanApprovalHookを登録しない

### 3.3 フック登録の概要

**フックの目的**: TOOL-002（申請書生成）の実行前に利用者の明示的な承認を取得し、AIによる申請書の自動生成を防止する（GRD-016、BRL-06）

**登録するイベント**:
- `BeforeToolCallEvent`: TOOL-002（generate_travel_expense_form / generate_expense_form）の呼び出し直前に発火。ツール実行をブロックし、利用者へ確認メッセージを提示する。ツール名で対象ツール（TOOL-002）のみをフィルタリングし、TOOL-001（calculate_travel_expense）はスルーする

### 3.4 フック登録の詳細
詳細設計書 3.4章を参照

### 3.5 HumanApprovalHookの処理概要

**処理の流れ**:
1. BeforeToolCallEventを受信し、呼び出しツール名を確認する（TOOL-002対象外はスルー）
2. 収集済み申請情報サマリーとOK/修正/キャンセルの3択をユーザーへ提示する
3. ユーザー選択を取得する：OK→ブロック解除（TOOL-002実行許可）、修正→修正対象の再収集ループへ戻す（ACTIVE維持）、キャンセル→セッション終了（TERMINATED）
4. 承認操作の選択結果・実行時刻をDATA-009（承認ログ）として記録する

**処理の目的**: HumanApprovalHookを利用者確認の技術的ゲートとして機能させ、申請書生成前の確認取得を強制する

### 3.6 処理フローの詳細
詳細設計書 3.5章を参照

---

## 4. LoopControlHook 基本設計

**システム設計書の方針**: システム設計書 実行制御方針.md（`artifacts/03_system-design/outputs/実行制御方針.md`）を参照してください。

### 4.1 LoopControlHookの位置づけ

#### システム全体における役割
- 全エージェント（AG-001/AG-002/AG-003）のReActループのイテレーション回数を監視し、最大10回で強制停止する
- LLMの暴走・同一アクション繰り返し・想定外の無限ループを防止する（実行制御方針.md 10.1節）
- ループ上限到達時にエラーメッセージをユーザーに提示してセッションをTERMINATEDに遷移させる

#### 主な責務（概要）
- **ループカウンタ管理**: エージェント呼び出し開始時にカウンタをリセット（0）し、LLM呼び出し後にインクリメントする
- **上限監視・強制停止**: カウンタが10回に到達した時点でループを強制停止する
- **ユーザー通知**: 「申し訳ありません。処理が複雑になりすぎたため、一旦終了します。もう一度最初から申請をやり直してください。」をユーザーへ提示する

#### 非責務（やらないこと）
- **Amazon Bedrockのリトライ制御**: Strands Agents SDKの組み込みリトライ機構が担当する
- **ユーザー向けエラーメッセージ生成（詳細）**: ErrorHandler.handle_unexpected_error()に委譲する
- **セッション状態の直接変更**: Strands Agents SDKが担当する

#### 詳細
詳細設計書 4章を参照

### 4.2 利用エージェント

| エージェントID | エージェント名 | 利用目的 |
|---------------|---------------|---------|
| AG-001 | 申請受付窓口エージェント | 申請種別判定・専門エージェント委任フローのループ暴走防止 |
| AG-002 | 交通費精算申請エージェント | 移動情報収集・交通費計算・申請書生成フローのループ暴走防止 |
| AG-003 | 経費精算申請エージェント | 経費情報収集・申請書生成フローのループ暴走防止 |

### 4.3 フック登録の概要

**フックの目的**: ReActループのイテレーション数を監視し、最大10回で強制停止することで、LLMの暴走・無限ループを防止する（実行制御方針.md 10.1節）

**登録するイベント**:
- `BeforeInvocationEvent`: エージェント呼び出し開始時に発火。ループカウンタをリセット（0）する
- `AfterModelCallEvent`: LLM呼び出し完了後に発火。ループカウンタをインクリメントし、上限（10回）到達を監視する。上限到達時はループを強制停止してユーザーへエラーメッセージを提示する
- `AfterInvocationEvent`: エージェント呼び出し完了後に発火。ループカウンタをリセット（0）する

### 4.4 フック登録の詳細
詳細設計書 4.4章を参照

### 4.5 LoopControlHookの処理概要

**処理の流れ**:
1. BeforeInvocationEventでカウンタを0にリセットする
2. AfterModelCallEventでカウンタをインクリメントする（1ReActイテレーション = 思考→ツール選択→ツール実行→観察を1カウント）
3. カウンタが10に到達した場合、ループを強制停止してErrorHandlerを通じてユーザーへ通知する
4. AfterInvocationEventでカウンタを0にリセットする（正常完了・異常終了問わず）

**処理の目的**: フレームワークレベルでReActループ上限を強制し、エージェント任せの無限ループを排除する

> ※ エラー・例外発生時のカウント扱い: AfterModelCallEventはLLMが正常にレスポンスを返した後に発火するため、LLMコール自体が失敗した場合（Bedrock接続エラー等）はカウントアップしない。Strands Agents SDKのリトライ機構によるリトライはカウントアップ対象外とする

### 4.6 処理フローの詳細
詳細設計書 4.5章を参照

---

## 5. マルチエージェント連携時の扱い

### 5.1 ErrorHandler

**共有方法**:
- `ErrorHandler` クラスのインスタンスを各エージェント（AG-001/AG-002/AG-003）・各ツール（TOOL-001/TOOL-002）で個別にインスタンス化して使用する
- `handlers/error_handler.py` に集約し、全コンポーネントが共通モジュールをインポートする

**スレッドセーフ性**:
- 本システムはシングルスレッド・CLIベースの逐次処理であるため、インスタンス間の競合は発生しない

### 5.2 HumanApprovalHook

**共有方法**:
- AG-002・AG-003それぞれに独立したHumanApprovalHookインスタンスを割り当てる（ファクトリ関数 `_get_travel_agent` / `_get_expense_agent` 内で初期化）
- AG-001には登録しない

**競合防止**:
- AG-002とAG-003は同一セッション内で同時実行しない（Agent as Toolsの逐次呼び出し構造で自然に排他）。HumanApprovalHookの競合は発生しない

### 5.3 LoopControlHook

**共有方法**:
- AG-001・AG-002・AG-003それぞれに独立したLoopControlHookインスタンスを割り当てる（各エージェント初期化時・ファクトリ関数内で初期化）
- ループカウンタはインスタンスごとに独立して管理する

**競合防止**:
- 各エージェントのループカウンタは独立しているため、エージェント間での競合は発生しない

---

## 6. テスト観点

### 6.1 ErrorHandler
- **正常系**: EX-01（UserInputTextバリデーション失敗）時にhandle_input_error()が再入力促しメッセージを返し、logs/error.logにERRORレベルで記録されること
- **正常系**: EX-03（申請期限超過）時にhandle_business_rule_violation()が申請不可通知を返すこと
- **正常系**: EX-08（想定外例外）時にhandle_unexpected_error()がエスカレーションメッセージを返し、スタックトレースがlogs/error.logに記録されること
- **異常系**: ツール関数が `{"success": False, "message": ...}` を返した場合にエージェントがErrorHandlerへ委譲し、ユーザー向けメッセージが生成されること

### 6.2 HumanApprovalHook
- **正常系（OK）**: TOOL-002呼び出し前にHumanApprovalHookがブロックし、利用者がOKを選択するとTOOL-002が実行されること
- **正常系（修正）**: 利用者が修正を選択するとTOOL-002が実行されず、修正対象の再収集ループへ戻ること
- **正常系（キャンセル）**: 利用者がキャンセルを選択するとTOOL-002が実行されずセッションが終了すること
- **正常系**: TOOL-001呼び出し時にHumanApprovalHookがスルーし（ブロックしない）TOOL-001が実行されること
- **正常系**: 承認操作結果と実行時刻がDATA-009として記録されること

### 6.3 LoopControlHook
- **正常系**: 10回以内のループでBeforeInvocationEvent時にカウンタが0にリセットされ、AfterInvocationEvent後もカウンタが0であること
- **異常系**: AfterModelCallEventで10回目のカウントアップ時にループが強制停止され、「処理が複雑になりすぎたため」メッセージがユーザーへ提示されること
- **正常系**: エラー・例外発生時（LLMコール失敗時）にカウントアップされないこと

### 6.4 技術的なテスト詳細
詳細設計書 7章を参照

---

## 7. 詳細設計への引き渡し事項

### 7.1 実装時の識別子

- **クラス名**: `ErrorHandler`（`handlers/error_handler.py`）、`HumanApprovalHook`（`handlers/hooks.py`）、`LoopControlHook`（`handlers/hooks.py`）
- **HookProvider**: HumanApprovalHookおよびLoopControlHookはStrands Agents SDKのHookProvider（またはCallback）として実装する

### 7.2 SDK実装時の注意事項

- **フックのイベント登録（使用可能イベント名）**: Strands Agents SDKで使用可能なイベントは `BeforeInvocationEvent`・`BeforeModelCallEvent`・`AfterModelCallEvent`・`BeforeToolCallEvent`・`AfterToolCallEvent`・`AfterInvocationEvent` の6種類。LoopControlHookは`BeforeInvocationEvent`/`AfterModelCallEvent`/`AfterInvocationEvent`の3イベントを使用する。HumanApprovalHookは`BeforeToolCallEvent`を使用する
- **LoopControlHookのカウントアップ例外処理**: AfterModelCallEventはLLM正常レスポンス後に発火するため、LLMコール失敗時はカウントアップしない。Bedrockリトライ中のカウントアップも対象外とする
- **HumanApprovalHookのツール名フィルタリング**: BeforeToolCallEventのイベントオブジェクトからツール名を取得し、`generate_travel_expense_form` / `generate_expense_form` のみをブロック対象とする（`calculate_travel_expense` はスルー）
- **ErrorHandlerのEventLoopException処理**: LoopControlHookが強制停止したループのエラーはEventLoopException（`__cause__` = LoopLimitError）として伝播する。ErrorHandlerはこの2層構造でキャッチする

### 7.3 モック／スタブ要否

- **ErrorHandler**: `logs/error.log` への書き込みをモック化して、メソッド呼び出し・ログ内容の検証をユニットテストで実施する
- **HumanApprovalHook**: ユーザー入力（OK/修正/キャンセル）をモック化して、各選択結果の後続処理を検証する
- **LoopControlHook**: AfterModelCallEventの繰り返し発火をシミュレートして、10回カウント時の強制停止動作を検証する

---

## 8. 他設計書との対応関係

| 設計書 | 本設計での関係 |
|--------|---------------|
| 詳細設計書（`artifacts/05_detailed-design/outputs/`） | メソッド詳細・実装コード・フック登録詳細・イベントハンドラ実装を参照 |
| AG-001_申請受付窓口エージェント基本設計書.md | LoopControlHookの利用エージェント。ErrorHandler委譲メソッドを参照 |
| AG-002_交通費精算申請エージェント基本設計書.md | HumanApprovalHook・LoopControlHookの利用エージェント。ErrorHandler委譲メソッドを参照 |
| AG-003_経費精算申請エージェント基本設計書.md | HumanApprovalHook・LoopControlHookの利用エージェント。ErrorHandler委譲メソッドを参照 |
| データモデル基本設計書.md | `UserInputText`・`ExpenseApplicationFormInput`等のValidationError発生元モデルを参照 |
| セッションマネージャ基本設計.md | セッション状態（TERMINATED）遷移のトリガーを参照 |
| artifacts/03_system-design/outputs/例外処理方針.md | EX-01〜EX-08の分類・対応方針・エラーメッセージ方針の基準を参照 |
| artifacts/03_system-design/outputs/実行制御方針.md | LoopControlHookの最大ループ回数（10回）・HumanApprovalHookの承認フロー・フック登録イベントを参照 |
| artifacts/03_system-design/outputs/共通設定方針.md | 各エージェントへのフック登録設定値を参照 |

---

## 9. 制約事項・前提条件

### 9.1 技術的制約
- LoopControlHookはStrands Agents SDK v1.25.0のHookProvider APIを使用する。登録するイベント名は `BeforeInvocationEvent`・`AfterModelCallEvent`・`AfterInvocationEvent` の実在するイベントのみを使用する
- HumanApprovalHookの登録対象は AG-002・AG-003 のみ。AG-001には登録しない（申請書生成はAG-002/AG-003の責務）
- ツール関数（TOOL-001/TOOL-002）はValidationErrorを再送出しない。`{"success": False, "message": ...}` 形式で返す

### 9.2 業務的制約
- HumanApprovalHookによる承認（OK）なしにTOOL-002（申請書生成）を呼び出すことはできない（GRD-016、BRL-06）
- LoopControlHook強制停止後のセッションは自動再試行しない。ユーザーが新規セッションで再開する

### 9.3 前提条件
- `logs/` ディレクトリが書き込み可能な状態でアプリ起動時に存在すること
- Strands Agents SDK v1.25.0のHookProvider APIが利用可能であること
- 各エージェントのファクトリ関数（`_get_travel_agent` / `_get_expense_agent`）でHumanApprovalHookおよびLoopControlHookのインスタンスをエージェント初期化時に登録すること

---

## 10. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 2.0 | 新フォーマットで作成 |
