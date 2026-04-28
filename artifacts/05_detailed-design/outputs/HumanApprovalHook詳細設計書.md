# HumanApprovalHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 3章（HumanApprovalHookの位置づけ・処理概要）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針・エラー分類）
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

AG-002/AG-003がTOOL-002（申請書生成）を呼び出す直前にブロックし、利用者（R-EMP）の明示的なOK/修正/キャンセル選択を取得する。GRD-016（申請書の利用者最終確認なしに確定操作禁止）およびBRL-06（申請書確認取得）を技術的ゲートとして強制する。承認操作（OK/修正/キャンセル）の選択結果と実行時刻をDATA-009（承認ログ）として記録する。

### 1.2 主要な責務

1. **TOOL-002呼び出しのブロック**: BeforeToolCallEventでgenerate_travel_expense_form / generate_expense_formの実行をインターセプトし、利用者確認取得まで実行をブロックする
2. **OK/修正/キャンセルの3択提示**: 利用者へ確認メッセージを提示し、選択を取得する
3. **承認ログ記録**: 承認操作の選択結果・実行時刻をDATA-009として記録する

### 1.3 非責務

- **TOOL-001（calculate_travel_expense）の実行ブロック**（TOOL-001は承認不要。ツール名フィルタリングによりスルーする）
- **AG-001へのフック登録**（AG-001はTOOL-002を利用しないため登録しない）
- **申請情報の検証**（Pydanticバリデーションおよびガードレールチェックはエージェントが担当）

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`HumanApprovalHook`

#### 説明
AG-002/AG-003がTOOL-002（generate_travel_expense_form / generate_expense_form）を呼び出す直前にブロックし、利用者のOK/修正/キャンセル選択を取得するHookProviderクラス。`handlers/hooks.py` に実装する。Strands Agents SDKのHookProvider（またはCallback）として実装する。

---

### 2.2 初期化

#### `__init__(self)`
引数なしで初期化する。

**引数**: なし

**インスタンス変数**:
- `_approval_tool_names`: フィルタリング対象のツール名セット（`{"generate_travel_expense_form", "generate_expense_form"}`）

---

### 2.3 主要メソッド

#### 2.3.1 _request_approval

##### 説明
利用者へ確認メッセージを提示し、OK/修正/キャンセルの選択を取得する。選択結果に応じてタプルを返す承認コールバック。

##### 引数
- `tool_name` (`str`): 呼び出し対象ツール名
- `tool_params` (`dict`): 呼び出し対象ツールのパラメータ

##### 戻り値
- `tuple[bool, str]`:
  - `(True, "")`: ユーザーが "ok" を選択した場合（ツール実行を許可）
  - `(False, 修正内容文字列)`: ユーザーが "修正" を選択し修正内容を入力した場合（修正要望）
  - `(False, "CANCEL")`: ユーザーが "キャンセル" を選択した場合（申請キャンセル）

##### 処理内容
1. `"申請書を生成してよろしいですか？\nOK・修正・キャンセルのいずれかを入力してください。"` を標準出力に表示する
2. `input()` でユーザー入力を取得する
3. 入力文字列を `.strip().lower()` で正規化する
4. `"ok"`/`"修正"`/`"キャンセル"` のいずれかに一致するまで再入力を促す
5. 選択結果・tool_name・実行時刻を `_log_approval()` でDATA-009として記録する
6. 選択に応じた戻り値を返す:
   - "ok" → `(True, "")` を返す
   - "修正" → ユーザーに修正内容の入力を求め、`(False, 修正内容文字列)` を返す
   - "キャンセル" → `(False, "CANCEL")` を返す

---

#### 2.3.2 _log_approval

##### 説明
承認操作の選択結果・tool_name・実行時刻をDATA-009（承認ログ）として記録する。

##### 引数
- `tool_name` (`str`): 対象ツール名
- `selection` (`str`): ユーザーの選択（"ok"/"修正"/"キャンセル"）
- `timestamp` (`str`): 実行時刻（ISO 8601形式）

##### 戻り値
- `None`

##### 処理内容
1. `{"tool_name": tool_name, "selection": selection, "timestamp": timestamp}` を構築する
2. INFOレベルのログとして `logs/error.log` に記録する

---

### 2.4 フック設計

#### 2.4.1 フック登録

##### `register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None`
フックの登録

**登録するイベント**:
- `BeforeToolCallEvent`: `_handle_before_tool_call`
  - **登録タイミング**: AG-002/AG-003のAgentインスタンス生成時（ファクトリ関数 `_get_travel_agent` / `_get_expense_agent` の `hooks=[HumanApprovalHook(), LoopControlHook()]` により登録される）
  - **依存関係**: LoopControlHookと独立（依存なし）

**登録順序**: BeforeToolCallEventのみ登録するため、順序は問わない

---

#### 2.4.2 イベントハンドラー

##### _handle_before_tool_call

**説明**: ToolCallEventを受信し、ツール名が承認対象（generate_travel_expense_form / generate_expense_form）の場合に利用者確認を取得してツール実行の継続・停止を制御する。

**処理内容**:
1. `event.tool_name`（またはイベントオブジェクトから取得したツール名）を確認する
2. ツール名が `_approval_tool_names` に含まれない場合（TOOL-001等）: 何もせずイベントをスルーする
3. ツール名が `_approval_tool_names` に含まれる場合（TOOL-002）:
   a. 承認コールバック関数を呼び出す: `result = self._request_approval(tool_name, event.tool_params)`
   b. `result == (True, "")` の場合: ツール実行を許可する（何もしない）
   c. `result[0] == False かつ result[1] != "CANCEL"` の場合: `event.cancel_tool = result[1]`（修正要望メッセージ）をセット
   d. `result[0] == False かつ result[1] == "CANCEL"` の場合: `event.cancel_tool = "申請をキャンセルしました。"` をセット

**ログ出力**: `"[HumanApprovalHook] BeforeToolCallEvent: tool_name={tool_name}, selection={selection}"`

---

## 3. ビジネスロジック

### 3.1 TOOL-002承認制御フロー

#### 処理フロー

```
AG-002/AG-003がgenerate_travel_expense_form/generate_expense_formを呼び出し
  ↓
BeforeToolCallEventが発火
  ↓
_handle_before_tool_call が受信
  ↓
tool_nameの確認
  ↓
tool_name が "calculate_travel_expense" の場合（TOOL-001）
  → スルー（ブロックしない）。TOOL-001は通常通り実行される
  ↓
tool_name が "generate_travel_expense_form" または "generate_expense_form" の場合（TOOL-002）
  ↓
_request_approval(tool_name, event.tool_params) を呼び出す
  ↓
ユーザーへ確認メッセージを表示:
  "申請書を生成してよろしいですか？
   OK・修正・キャンセルのいずれかを入力してください。"
  ↓
ユーザー入力を取得（正規化: strip().lower()）
  ↓
入力が "ok"/"修正"/"キャンセル" 以外の場合
  → "OK・修正・キャンセルのいずれかで入力してください。" と表示して再入力を促す
  ↓
"ok" 選択の場合
  → _log_approval(tool_name, "ok", timestamp) で承認ログ記録
  → _request_approval が (True, "") を返す
  → _handle_before_tool_call は何もしない（ツール実行を許可）
  → generate_travel_expense_form/generate_expense_form が実行される
  ↓
"修正" 選択の場合
  → ユーザーに修正内容を入力させる
  → _log_approval(tool_name, "修正", timestamp) で承認ログ記録
  → _request_approval が (False, 修正内容文字列) を返す
  → event.cancel_tool = 修正内容文字列 をセット（ツールキャンセル）
  → エージェントが修正ループを継続する（ACTIVE継続）
  ↓
"キャンセル" 選択の場合
  → _log_approval(tool_name, "キャンセル", timestamp) で承認ログ記録
  → _request_approval が (False, "CANCEL") を返す
  → event.cancel_tool = "申請をキャンセルしました。" をセット（ツールキャンセル）
  → セッション終了（TERMINATED）
```

#### 分岐条件の詳細

- **スルー条件**: `event.tool_name not in {"generate_travel_expense_form", "generate_expense_form"}`
- **ブロック解除条件**: `_request_approval` が `(True, "")` を返した場合（何もしない）
- **修正ループ継続条件**: `_request_approval` が `(False, 修正内容文字列)` を返した場合（`event.cancel_tool` に修正内容をセット）
- **キャンセル条件**: `_request_approval` が `(False, "CANCEL")` を返した場合（`event.cancel_tool` に `"申請をキャンセルしました。"` をセット）

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| 入力値不正 | "ok"/"修正"/"キャンセル" 以外の入力 | 再入力を促す | `"OK・修正・キャンセルのいずれかで入力してください。"` |
| EOFError | 標準入力が閉じられた場合（CI環境等） | キャンセルとして扱う（`(False, "CANCEL")` を返す） | なし（セッション終了） |

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | BeforeToolCallEvent受信時（TOOL-001スルー） | `"[HumanApprovalHook] Skipped: tool_name={tool_name}"` |
| INFO | TOOL-002ブロック開始時 | `"[HumanApprovalHook] Waiting for approval: tool_name={tool_name}"` |
| INFO | 承認操作完了時 | `"[HumanApprovalHook] Approval result: tool_name={tool_name}, selection={selection}, timestamp={timestamp}"` |

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
from handlers.hooks import HumanApprovalHook, LoopControlHook
from strands import Agent

# AG-002/AG-003のAgentインスタンス生成時にフック登録
agent = Agent(
    agent_id="travel_agent",
    name="交通費精算申請エージェント",
    model=get_model(),
    system_prompt=system_prompt,
    tools=[calculate_travel_expense, generate_travel_expense_form],
    hooks=[HumanApprovalHook(), LoopControlHook(max_iterations=10)],
    callback_handler=None,
)
```

### 6.2 フック動作確認

```python
# TOOL-002呼び出し時、HumanApprovalHookが自動的に介入し
# 標準入力からユーザー確認を取得する。
#
# _request_approval の戻り値の例:
#   ユーザーが "ok" を入力        → (True, "")
#   ユーザーが "修正" を選択し
#   "金額を10000円に変更" と入力  → (False, "金額を10000円に変更")
#   ユーザーが "キャンセル" を入力 → (False, "CANCEL")
#
# _handle_before_tool_call の処理:
#   (True, "")            → 何もしない（ツール実行を許可）
#   (False, "修正内容")   → event.cancel_tool = "修正内容" をセット
#   (False, "CANCEL")     → event.cancel_tool = "申請をキャンセルしました。" をセット
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **承認対象ツール名の完全一致**
   - `_approval_tool_names` に登録するツール名は、エージェント詳細設計書の「利用ツール」に記載されたツール名と完全一致させる
   - AG-002: `"generate_travel_expense_form"`、AG-003: `"generate_expense_form"`
   - ツール名の不一致により承認ダイアログが表示されず申請書が無承認で生成されるリスクを排除する

2. **AG-001への登録禁止**
   - AG-001はTOOL-002を利用しないため、HumanApprovalHookを登録してはならない
   - AG-001の `create_orchestrator_agent()` 関数で `hooks=[LoopControlHook(max_iterations=10)]` のみを指定する

3. **インスタンスの独立性**
   - AG-002とAG-003それぞれに独立したHumanApprovalHookインスタンスを生成する
   - 同一セッション内でAG-002とAG-003は逐次実行されるため、インスタンス間の競合は発生しない

4. **Strands Agents SDK HookProvider API**
   - `register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None` を実装してHookProviderプロトコルに準拠する
   - `BeforeToolCallEvent` のみを登録する

5. **ツール中止方法（event.cancel_tool の使用）**
   - ツールのキャンセルは `event.stop_reason` ではなく `event.cancel_tool` にメッセージ文字列をセットすることで行う
   - 修正要望の場合: `event.cancel_tool = result[1]`（修正内容文字列）
   - キャンセルの場合: `event.cancel_tool = "申請をキャンセルしました。"`
   - `(True, "")` の場合は `event.cancel_tool` を一切セットしない（何もしない）

---

### 7.2 パフォーマンス考慮事項

1. **承認待ち時間**
   - HumanApprovalHookはユーザーの明示的な応答があるまでブロックする（タイムアウトなし）
   - CLIのシングルスレッド実行のため、他の処理への影響はない

---

### 7.3 セキュリティ考慮事項

1. **ツール実行の強制ゲート**
   - BeforeToolCallEventによるブロックにより、LLMが意図せずTOOL-002を呼び出しても必ず利用者確認を取得する
   - GRD-016（TOOL-002実行前確認）を技術的に強制する

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: フックフレームワーク
  - `HookProvider`: フックプロバイダーインターフェース
  - `HookRegistry`: フックレジストリ
  - `BeforeToolCallEvent`: ツール呼び出し前イベント
- `datetime`:
  - `datetime.datetime.now().isoformat()`: 承認ログのタイムスタンプ生成

### 8.2 内部モジュール
- `handlers/hooks.py`: 本クラスの実装ファイル（LoopControlHookと同ファイル）

---

## 9. テスト観点

### 9.1 機能テスト
- TOOL-002（generate_travel_expense_form）呼び出し時、HumanApprovalHookがブロックし確認メッセージを表示すること
  - **入力**: BeforeToolCallEvent（tool_name="generate_travel_expense_form"）
  - **期待結果**: 確認メッセージが標準出力に表示される
- ユーザーが "ok" を入力した場合、`_request_approval` が `(True, "")` を返し、TOOL-002の実行が許可されること
  - **入力**: BeforeToolCallEvent + ユーザー入力 "ok"
  - **期待結果**: `_request_approval` の戻り値が `(True, "")`。`event.cancel_tool` はセットされず、TOOL-002が実行される
- ユーザーが "修正" を入力した場合、`_request_approval` が `(False, 修正内容文字列)` を返し、`event.cancel_tool` に修正内容がセットされること
  - **入力**: BeforeToolCallEvent + ユーザー入力 "修正" + 修正内容入力
  - **期待結果**: `_request_approval` の戻り値が `(False, 修正内容文字列)`。`event.cancel_tool` = 修正内容文字列
- ユーザーが "キャンセル" を入力した場合、`_request_approval` が `(False, "CANCEL")` を返し、`event.cancel_tool` に "申請をキャンセルしました。" がセットされること
  - **入力**: BeforeToolCallEvent + ユーザー入力 "キャンセル"
  - **期待結果**: `_request_approval` の戻り値が `(False, "CANCEL")`。`event.cancel_tool` = `"申請をキャンセルしました。"`
- TOOL-001（calculate_travel_expense）呼び出し時、HumanApprovalHookがスルーし実行されること
  - **入力**: BeforeToolCallEvent（tool_name="calculate_travel_expense"）
  - **期待結果**: ブロックなしでTOOL-001が実行される
- 承認操作結果（選択・実行時刻）がDATA-009として記録されること
  - **入力**: BeforeToolCallEvent + ユーザー入力 "ok"
  - **期待結果**: logs/error.logにINFOレベルで承認ログが記録される

### 9.2 異常系テスト
- 無効な入力（"1"/"yes"等）を受け取った場合、再入力が促されること
  - **入力**: BeforeToolCallEvent + ユーザー入力 "yes"
  - **期待結果**: `"OK・修正・キャンセルのいずれかで入力してください。"` が表示され再入力待ちになる
- AG-001でHumanApprovalHookが登録されていないこと（TOOL-002呼び出し時に承認ダイアログが表示されないこと）
  - **テスト対象**: AG-001のAgentインスタンス生成
  - **期待結果**: hooks=[LoopControlHook(max_iterations=10)] のみ

### 9.5 統合テスト
- AG-002のgenerate_travel_expense_form実行前にHumanApprovalHookがブロックし、"ok" 選択後にExcelドラフトが生成されること
  - **テスト対象**: AG-002 → HumanApprovalHook → generate_travel_expense_form
  - **期待結果**: data/output/{session_id}/ディレクトリにExcelファイルが生成される
- AG-003のgenerate_expense_form実行前にHumanApprovalHookがブロックし、"ok" 選択後にExcelドラフトが生成されること
  - **テスト対象**: AG-003 → HumanApprovalHook → generate_expense_form
  - **期待結果**: data/output/{session_id}/ディレクトリにExcelファイルが生成される

---

## 10. 設定値

### 10.1 承認対象ツール名
- AG-002対象: `"generate_travel_expense_form"`
- AG-003対象: `"generate_expense_form"`

### 10.2 承認選択肢
- OK: `"ok"`（入力後 strip().lower() で正規化）
- 修正: `"修正"`
- キャンセル: `"キャンセル"`

### 10.3 承認ログ
- 記録先: `logs/error.log`（INFOレベル）
- 記録項目: tool_name・selection・timestamp（ISO 8601形式）

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 2.0 | 新フォーマットで作成 |
| 2026-04-28 | 3.0 | 承認コールバック仕様を改訂。_request_approvalの引数にtool_paramsを追加、戻り値をtuple[bool, str]に変更（"ok"→(True,"")、"修正"→(False,修正内容文字列)、"キャンセル"→(False,"CANCEL")）。ツール中止方法をevent.stop_reasonからevent.cancel_toolへ変更。_handle_before_tool_callの処理をresultタプル判定に基づくcancel_toolセットに更新。処理フロー・分岐条件・使用例・実装上の注意点・テスト観点を対応仕様に合わせて全面更新。 |
| 2026-04-28 | 3.1 | 統合テストの出力ディレクトリパス変更（9.5節）: `output/` → `data/output/{session_id}/` |
