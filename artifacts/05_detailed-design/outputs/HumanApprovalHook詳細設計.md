---
version: "1.1.0"
last_updated: "2026-05-02"
updated_by: ""
---

# HumanApprovalHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 4章（HumanApprovalHookの目的・役割定義・承認フロー・提示内容）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 5章（ハンドラー間の連携設計）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（人間承認制御の方針・承認フロー・適用対象）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

AG-002/AG-003 が申請書生成ツール（`generate_transport_expense_form` / `generate_expense_reimbursement_form`）を呼び出す前に介入し、社員による OK/修正/キャンセルの3択確認を取得する（GRD-014 / ABAC-001）。確認結果に応じて申請書生成の実行・修正対話への戻り・フロー終了を制御する。

### 1.2 主要な責務

1. **介入トリガー**: AG-002/AG-003 が `generate_transport_expense_form` または `generate_expense_reimbursement_form` を呼び出そうとする直前に介入する（`BeforeToolCallEvent` で判定）
2. **社員への確認提示**: 収集済み申請情報を一覧で社員に提示して OK/修正/キャンセルを求める
3. **選択結果に応じた分岐制御**: OK → ツール実行許可、修正 → 対話に戻す、キャンセル → フロー終了
4. **ログ出力**: OPE-003（承認結果）および AUD-004（HITL監査）を LOG-HI に出力する

### 1.3 非責務

- **AG-001 への適用**: AG-001 は申請書生成を行わないため対象外
- **高額申請の上長承認取得**: GRD-007 の通知は AG-002/AG-003 のシステムプロンプトが担当。HumanApprovalHook は社員向け収集情報確認のみ担当する
- **申請書提出の制御**: GRD-012 はエージェントのツール利用可能範囲から除外することで制御。HumanApprovalHook の責務外

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`HumanApprovalHook`

#### 説明
AG-002/AG-003 が申請書生成ツール（`generate_transport_expense_form` / `generate_expense_reimbursement_form`）を呼び出す直前に介入し、社員の OK/修正/キャンセル確認を取得するフッククラス。確認はコールバック関数（`approval_callback`）経由で行い、承認が得られた場合のみツール実行を許可する。修正・キャンセル時は `event.cancel_tool` を呼び出してツール実行を中止する。

---

### 2.2 初期化

#### `__init__(self, approval_callback: Callable[[str, dict], tuple[bool, str]])`
HumanApprovalHook を初期化する。承認確認はコールバック関数経由で行う。

**引数**:
- `approval_callback` (Callable[[str, dict], tuple[bool, str]]): 承認コールバック関数。`(tool_name: str, tool_params: dict) -> tuple[bool, str]` シグネチャ。戻り値の `bool` が `True` の場合は承認、`False` の場合は非承認（修正/キャンセル）。`str` は非承認時のメッセージ。

**インスタンス変数**:
- `approval_callback`: Callable[[str, dict], tuple[bool, str]] — 承認コールバック関数

---

### 2.3 主要メソッド

#### 2.3.1 `on_before_tool_call`

##### 説明
ツール呼び出し直前に発火する。ツール名が `generate_transport_expense_form` または `generate_expense_reimbursement_form` の場合のみ介入し、コールバック関数経由で社員の確認を取得する。

##### 引数
- `event` (BeforeToolCallEvent): ツール呼び出し直前イベント

##### 戻り値
- `None`

##### 処理内容
1. `event.tool_name` が `"generate_transport_expense_form"` または `"generate_expense_reimbursement_form"` か確認する
2. 対象ツールでない場合は何もせずに返す
3. 対象ツールの場合:
   a. `invocation_state` から `applicant_name` を取得する（`event.invocation_state.get("applicant_name", "")` または `event.agent.context.invocation_state.get("applicant_name", "")`）
   b. `_build_confirmation_message(event, applicant_name)` を呼び出して確認メッセージを生成する
   c. `approval_callback(event.tool_name, {"confirmation_message": confirmation_message, "tool_params": event.tool_input})` を呼び出して承認結果を取得する
      - 戻り値: `(approved: bool, message: str)`
   d. OPE-003 ログを出力する
   e. 承認結果に応じて分岐:
      - `approved=True`（OK）: `_log_audit(event, "OK")` を呼び出す。処理を継続する（ツール実行許可）
      - `approved=False`（修正/キャンセル）: `_log_audit(event, message)` を呼び出す。`event.cancel_tool(message)` を呼び出してツール実行を中止する

---

#### 2.3.2 `_build_confirmation_message`

##### 説明
社員への確認提示メッセージを生成する。ツール名に応じて交通費精算申請または経費精算申請の書式で生成する。

##### 引数
- `event` (BeforeToolCallEvent): ツール呼び出し直前イベント（ツール引数を含む）
- `applicant_name` (str): 申請者名（invocation_state から取得済み）

##### 戻り値
- `str`: 社員向け確認メッセージ

##### 処理内容
1. `event.tool_name` が `"generate_transport_expense_form"` の場合:
   - `event.tool_input` から `application_date`, `segments` リストを取得する（`applicant_name` は引数から取得）
   - 交通費精算申請の確認メッセージを生成する（以下の形式）:
     ```
     以下の申請情報をご確認ください。

     【交通費精算申請】
     申請者: {applicant_name}
     申請日: {application_date}
     区間1:
       移動日: {travel_date}  出発地: {departure}  目的地: {destination}
       交通手段: {transportation_type}  費用: {amount}円
       業務目的: {purpose}
     （以下、収集済み全区間分）

     上記の内容でよろしいですか？
     1. OK（このまま申請書を生成する）
     2. 修正する
     3. キャンセル
     ```
2. `event.tool_name` が `"generate_expense_reimbursement_form"` の場合:
   - `event.tool_input` から `application_date`, `items` リストを取得する（`applicant_name` は引数から取得）
   - 経費精算申請の確認メッセージを生成する（以下の形式）:
     ```
     以下の申請情報をご確認ください。

     【経費精算申請】
     申請者: {applicant_name}
     申請日: {application_date}
     経費1:
       発生日: {expense_date}  店舗名: {store_name}  金額: {amount}円
       品目: {item_name}  経費区分: {expense_category}
       業務目的: {purpose}
     （以下、収集済み全経費分）

     上記の内容でよろしいですか？
     1. OK（このまま申請書を生成する）
     2. 修正する
     3. キャンセル
     ```

---

#### 2.3.3 `_log_audit`

##### 説明
HITL 承認結果を AUD-004 として LOG-HI に記録する。

##### 引数
- `event` (BeforeToolCallEvent): ツール呼び出し直前イベント
- `result` (str): 承認結果（`"OK"` / 非承認時のコールバック返却メッセージ）

##### 戻り値
- `None`

##### 処理内容
1. `event.agent.context.invocation_state` から `request_id` および `applicant_name` を取得する（`applicant_name` の先頭1文字 + `"***"` でマスキング: GRD-011）
2. `logger.info(f"[AUD-004] HITL確認: request_id={request_id}, agent_id={agent_id}, 申請種別={application_type}, 結果={result}, applicant={masked_name}")`

---

### 2.4 フック設計

#### 2.4.1 フック登録

##### `register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None`
フックの登録

**登録するイベント**:
- `BeforeToolCallEvent`: `on_before_tool_call`
  - **登録タイミング**: エージェントインスタンス生成時（`hooks=[..., HumanApprovalHook()]` として渡す）
  - **依存関係**: LoopControlHook とは独立。登録順序に制約なし

**登録順序**: 登録順序は特定の順序を要件としない

---

#### 2.4.2 イベントハンドラー

##### `on_before_tool_call`

**説明**: ツール呼び出し直前に発火し、対象ツール（`generate_transport_expense_form` / `generate_expense_reimbursement_form`）の場合のみ介入する。`approval_callback` 経由で社員の OK/非承認確認を取得し、結果に応じてツール実行の許可・中止を制御する。

**処理内容**:
1. `event.tool_name` が承認対象ツール名か確認する
2. 対象外ならスキップ（return）
3. `invocation_state` から `applicant_name` を取得する
4. 確認メッセージを生成する（`_build_confirmation_message(event, applicant_name)`）
5. `approval_callback(event.tool_name, {...})` で承認結果を取得する
6. OPE-003 ログを出力する
7. 承認結果に応じて分岐:
   - `approved=True` → 処理継続（ツール実行許可）
   - `approved=False` → `event.cancel_tool(message)` 呼び出し（ツール実行中止）
8. AUD-004 ログを出力する（`_log_audit`）

**ログ出力**: `"[OPE-003] HumanApprovalHook介入: request_id={request_id}, tool={tool_name}, result={result}"`

---

## 3. ビジネスロジック

### 3.1 承認フロー

#### 処理フロー

```
開始: AG-002/AG-003 が申請書生成ツールを呼び出そうとする
  ↓
（前提）エージェントがステップN-1で収集済み申請情報をテキストとして整理・提示済み（ドラフト提示、ツール呼び出しなし）
  ↓
【BeforeToolCallEvent 発火】on_before_tool_call
  - event.tool_name が "generate_transport_expense_form" または "generate_expense_reimbursement_form" か確認
  ↓
対象ツールでない場合 → スキップ（return）
  ↓
対象ツールの場合:
【invocation_state から applicant_name 取得】
  - applicant_name = event.agent.context.invocation_state.get("applicant_name", "")
  ↓
【確認メッセージ生成】_build_confirmation_message(event, applicant_name)
  - ツール名に応じた交通費精算/経費精算の確認書式を生成
  ↓
【approval_callback 呼び出し】
  - approved, message = self.approval_callback(event.tool_name, {"confirmation_message": confirmation_message, "tool_params": event.tool_input})
  ↓
【OPE-003 ログ出力】
  ↓
approved=True（OK）
  → 【AUD-004 ログ出力（OK）】_log_audit(event, "OK")
  → ツール実行を許可（処理継続）
  → generate_transport_expense_form / generate_expense_reimbursement_form が実行される
  ↓
approved=False（修正/キャンセル）
  → 【AUD-004 ログ出力】_log_audit(event, message)
  → event.cancel_tool(message)（ツール実行中止）
  → エージェントが修正対話またはフロー終了へ
  ↓
終了
```

#### 分岐条件の詳細
- **対象ツール判定**: `event.tool_name in {"generate_transport_expense_form", "generate_expense_reimbursement_form"}`
- **OK判定**: `approval_callback` の戻り値 `approved == True`
- **非承認判定**: `approval_callback` の戻り値 `approved == False`（修正/キャンセルの区別はコールバック側で制御）

---

### 3.2 ドラフト提示とBeforeToolCallEventの分離

#### 処理の詳細
- エージェントは収集済み申請情報を**テキストとして整理・提示するステップ（ドラフト提示）**と、**申請書生成ツールを呼び出すステップ**を明確に分離する
- ドラフト提示ステップでは、エージェントがシステムプロンプトの指示に従い、申請情報をテキスト形式で社員に提示する（ツール呼び出しなし）
- ドラフト提示後に申請書生成ツールを呼び出そうとした際に `BeforeToolCallEvent` が発火し、HumanApprovalHook が介入する
- これにより、社員はドラフト提示（エージェントの対話）と HumanApprovalHook 介入（システム制御）の2段階の確認を受ける

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| 非承認（修正） | `approval_callback` が `(False, message)` を返し、message が修正を示す | `event.cancel_tool(message)` 呼び出し → エージェントの修正対話ループに戻る | コールバック返却 message |
| 非承認（キャンセル） | `approval_callback` が `(False, message)` を返し、message がキャンセルを示す | `event.cancel_tool(message)` 呼び出し → セッション CLOSED に遷移してフロー終了 | コールバック返却 message |

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | BeforeToolCallEvent 介入時（承認取得後） | `"[OPE-003] HumanApprovalHook介入: request_id={request_id}, tool={tool_name}, result={result}"` |
| INFO | HITL確認完了時（OK/修正/キャンセル後） | `"[AUD-004] HITL確認: request_id={request_id}, agent_id={agent_id}, 申請種別={application_type}, 結果={result}, applicant={masked_name}"` |

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
from handlers.human_approval_hook import HumanApprovalHook
from handlers.loop_control_hook import LoopControlHook
from strands import Agent
from strands.models import BedrockModel

# approval_callback の実装例（CLI での確認）
def approval_callback(tool_name: str, params: dict) -> tuple[bool, str]:
    confirmation_message = params.get("confirmation_message", "")
    print(confirmation_message)
    max_retries = 3
    for _ in range(max_retries):
        choice = input("選択してください (1/2/3): ").strip()
        if choice == "1":
            return True, "OK"
        elif choice == "2":
            return False, "修正"
        elif choice == "3":
            print("申請をキャンセルしました。またいつでもご相談ください。")
            return False, "キャンセル"
        else:
            print("1、2、3 のいずれかを入力してください。")
    print("入力が3回無効でした。申請をキャンセルします。")
    return False, "キャンセル"

# AG-002 エージェント初期化時に hooks パラメータで登録する
agent = Agent(
    model=BedrockModel(model_id="jp.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    system_prompt="...",
    tools=[calculate_transport_fare, generate_transport_expense_form],
    hooks=[LoopControlHook(max_iterations=10), HumanApprovalHook(approval_callback=approval_callback)],
    callback_handler=None,
)

# エージェント呼び出し
# → エージェントが generate_transport_expense_form を呼び出そうとした際に
#   BeforeToolCallEvent が発火し、HumanApprovalHook が介入する
response = agent("交通費を申請します", invocation_state=state)
```

---

### 6.2 承認フロー実行時の出力例（OK選択）

```python
# approval_callback が呼び出された際の動作例（OK選択時）
# confirmation_message の内容:
"""
以下の申請情報をご確認ください。

【交通費精算申請】
申請者: 田中太郎
申請日: 2026-05-02
区間1:
  移動日: 2026-04-28  出発地: 渋谷  目的地: 新宿
  交通手段: 電車  費用: 200円
  業務目的: 営業訪問

上記の内容でよろしいですか？
1. OK（このまま申請書を生成する）
2. 修正する
3. キャンセル

選択してください (1/2/3): 1
"""
# approval_callback 返却値: (True, "OK")
# → event.cancel_tool は呼ばれない。ツール実行許可。generate_transport_expense_form が呼び出される
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **ドラフト提示ステップとBeforeToolCallEventの分離**
   - エージェントのシステムプロンプトに「申請情報の提示（ドラフト提示）と申請書生成ツールの呼び出しは別ステップで行うこと」を明示する必要がある
   - ドラフト提示はツール呼び出しなしのテキスト応答として行い、その後の申請書生成ツール呼び出し時に HumanApprovalHook が介入する

2. **event.cancel_tool の扱い**
   - `event.cancel_tool(message)` は Strands Agents SDK の `BeforeToolCallEvent` が提供するメソッド。呼び出すことでツール実行を中止できる。
   - 修正選択時はエージェントの対話ループに戻るため、エージェントが次の入力を待機する
   - キャンセル選択時はセッション状態が CLOSED に遷移する

3. **コールバック設計**
   - `approval_callback` はコンストラクタで受け取り、テスト時にモック関数を注入できる設計とする
   - コールバックシグネチャ: `(tool_name: str, tool_params: dict) -> tuple[bool, str]`
   - `bool` が True の場合は承認（ツール実行許可）、False の場合は非承認（event.cancel_tool呼び出し）

4. **applicant_name の取得元変更**
   - `applicant_name` は `event.tool_input` ではなく `event.agent.context.invocation_state` から取得する（修正10）
   - これにより LLM が applicant_name をパラメータとして渡す設計から分離される

5. **承認前のツール実行禁止**
   - HumanApprovalHook が未適用のエージェント（AG-001）は申請書生成ツールを toolsリストに登録しない設計とし、二重の保護を提供する

---

### 7.2 パフォーマンス考慮事項

1. **`input()` のブロッキング**
   - `input()` による同期的な社員入力待機は意図した設計。申請書生成前の社員確認は必須要件（GRD-014）であり、非同期化は対象外。

---

### 7.3 セキュリティ考慮事項

1. **個人情報のログマスキング**
   - AUD-004 ログに申請者名を記録する際は `applicant_name[:1] + "***"` 形式でマスキングする（GRD-011）
   - 収集情報サマリ（D-010）の申請内容詳細は AUD-004 には含めない（項目名のみ記録）

2. **承認対象ツール名の固定**
   - 承認対象ツール名は `{"generate_transport_expense_form", "generate_expense_reimbursement_form"}` としてハードコーディングし、外部から変更できないようにする

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: フックフレームワーク
  - `HookProvider`: フックプロバイダー基底クラス
  - `HookRegistry`: フックレジストリ
  - `BeforeToolCallEvent`: ツール呼び出し直前イベント
  - `ToolCallCancelled`: ツール実行中止例外
- `logging`: ログ出力（Python標準）

### 8.2 内部モジュール
- なし（HumanApprovalHook は Strands Agents SDK のフックのみに依存）

---

## 9. テスト観点

### 9.1 機能テスト
- `"1"` OK 選択時に TL-002a/TL-002b が実行されること
  - **入力**: `on_before_tool_call` で `"generate_transport_expense_form"` イベント + 入力 `"1"`
  - **期待結果**: `ToolCallCancelled` が raise されない（ツール実行許可）
- `"2"` 修正選択時に TL-002a/TL-002b が実行されないこと
  - **入力**: `on_before_tool_call` で `"generate_transport_expense_form"` イベント + 入力 `"2"`
  - **期待結果**: `ToolCallCancelled` が raise される
- `"3"` キャンセル選択時に TL-002a/TL-002b が実行されないこと
  - **入力**: `on_before_tool_call` で `"generate_expense_reimbursement_form"` イベント + 入力 `"3"`
  - **期待結果**: `ToolCallCancelled` が raise される
- `calculate_transport_fare` など対象外ツールの呼び出しでは HumanApprovalHook が介入しないこと
  - **入力**: `on_before_tool_call` で `"calculate_transport_fare"` イベント
  - **期待結果**: 何も実行されず（介入しない）

### 9.2 異常系テスト
- 無効入力（`"4"`, `""` など）を3回連続した場合にキャンセルとして扱われること
  - **入力**: 無効入力を3回連続
  - **期待結果**: `ToolCallCancelled` が raise される（キャンセル扱い）
- AUD-004 ログに申請者名がマスキングされて記録されること
  - **入力**: `applicant_name="田中太郎"` でOK選択
  - **期待結果**: ログに `"田***"` が記録される（`"田中太郎"` は含まれない）

### 9.3 性能テスト（該当する場合のみ）
- `on_before_tool_call` の確認メッセージ生成処理が 5ms 以内であること（`input()` 待機時間は除く）
  - **測定指標**: 処理時間（`input()` 待機前まで）
  - **期待値**: 5ms以内

### 9.4 境界値テスト
- 入力リトライが3回目で無効入力の場合にキャンセルとして処理されること
  - **境界値**: 無効入力の3回目
  - **期待結果**: `ToolCallCancelled` raise（キャンセル扱い）
- 区間数が1区間の交通費精算申請で確認メッセージが正しく表示されること
  - **境界値**: segments リストの要素数 = 1
  - **期待結果**: 1区間分の情報が正しく表示される

### 9.5 統合テスト
- エージェントが収集済み申請情報をドラフト提示した後、申請書生成ツール呼び出し時に HumanApprovalHook が介入すること（ドラフト提示ステップとツール呼び出しステップが分離されていること）
  - **テスト対象**: HumanApprovalHook + AG-002
  - **期待結果**: ドラフト提示（テキスト応答）→ BeforeToolCallEvent 発火 → HumanApprovalHook 介入の順で実行される
- OK 選択後に申請書ファイルが生成されること
  - **テスト対象**: HumanApprovalHook + generate_transport_expense_form
  - **期待結果**: OK選択 → ツール実行許可 → 申請書 Excel ファイルが生成される

---

## 10. 設定値

### 10.1 承認対象ツール名
- `"generate_transport_expense_form"`: 交通費精算申請書生成ツール（AG-002 で利用）
- `"generate_expense_reimbursement_form"`: 経費精算申請書生成ツール（AG-003 で利用）

### 10.2 無効入力リトライ上限
- 最大リトライ回数: `3`（超過時はキャンセルとして扱う）

### 10.3 ガードレール関連設定
- GRD-014: 申請書生成前の社員確認承認必須（`BeforeToolCallEvent` による介入で保証）
- GRD-011: 申請者名のマスキング方式: `applicant_name[:1] + "***"`

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-02 | 1.0 | 新フォーマットで初版作成 |
| 2026-05-02 | 1.1 | 修正8: approval_callbackパターンに変更（ToolCallCancelled raise → event.cancel_tool呼び出し）、コールバックシグネチャ定義追加。修正10: applicant_nameをevent.tool_inputからinvocation_stateへ取得元変更 |
