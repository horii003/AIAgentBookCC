# HumanApprovalHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 3章（HumanApprovalHookの位置づけ・処理概要）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 5章（マルチエージェント連携時の扱い）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 7章（詳細設計への引き渡し事項）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（承認制御の方針・承認結果の処理）
> - artifacts/03_system-design/outputs/共通設定方針.md（フック登録設定値）

## 1. 概要

### 1.1 コンポーネントの目的

AG-002・AG-003がTOOL-002（申請書生成）を呼び出す直前にBeforeToolCallEventで実行をブロックし、利用者（R-EMP）の明示的なOK/修正/キャンセル選択を取得する承認ゲートとして機能する。GRD-016（申請書の利用者最終確認なしに確定操作禁止）およびBRL-06（申請書確認取得）を技術的に強制する。承認操作の結果と実行時刻をDATA-009（承認ログ）に記録する。

### 1.2 主要な責務

- **TOOL-002呼び出しのブロック**: BeforeToolCallEventでTOOL-002（`generate_transport_expense_form` / `generate_expense_form`）の実行をインターセプトし、利用者確認を取得するまで停止する
- **承認コールバック呼び出し**: 登録された `approval_callback` を呼び出し、その戻り値に応じてツール実行の可否を決定する
- **OK/修正/キャンセルの3択取得**: 利用者の選択を標準入力で受け取り、選択結果に応じた後続処理へ遷移する
- **承認ログ記録**: 承認操作の選択結果・実行時刻・ツール名をDATA-009（`logs/approval.log`）として記録する

### 1.3 非責務

- **TOOL-001実行のブロック**: `calculate_transport_expense` はブロック対象外。BeforeToolCallEventでツール名がフィルタ対象外の場合はスルーする
- **AG-001へのフック登録**: AG-001はTOOL-002を利用しないため登録しない
- **申請情報の検証**: Pydanticバリデーションおよびガードレールチェックはエージェントが担当する
- **ドラフト提示（テキスト整理）**: LLMが担当する。HumanApprovalHookはツール呼び出し直前の承認ゲートのみを担う

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | `HD-002` |
| コンポーネント名 | HumanApprovalHook |
| コンポーネント種別 | ハンドラー（フッククラス） |
| 説明 | TOOL-002呼び出し前の利用者承認ゲート。BeforeToolCallEventで実行をブロックし、OK/修正/キャンセルを取得する |

---

### 2.2 初期化

#### `__init__(self, tool_names: list[str], approval_callback=None)`

承認ゲートの対象ツール名リストと承認コールバック関数を受け取り、インスタンスを初期化する。

**引数**:
- `tool_names` (list[str]): 承認必須のツール名リスト
  - AG-002: `["generate_transport_expense_form"]`
  - AG-003: `["generate_expense_form"]`
  - 承認対象ツール名は申請書生成ツール詳細設計書に定義された全ツール関数名（`generate_transport_expense_form` / `generate_expense_form`）とする
- `approval_callback` (callable, optional): 承認処理を委譲するコールバック関数。省略時はフック内部のデフォルト承認処理（標準入力による3択）を使用する

**インスタンス変数**:

| 変数名 | 型 | 説明 |
|--------|-----|------|
| `_tool_names` | `list[str]` | 承認フィルタ対象ツール名リスト |
| `_approval_callback` | `callable \| None` | 承認処理を委譲するコールバック関数 |
| `_logger` | `logging.Logger` | Pythonロガーインスタンス（`logs/approval.log` への出力） |

---

### 2.3 承認コールバック仕様

#### 2.3.1 シグネチャ

```python
def approval_callback(tool_name: str, tool_params: dict) -> tuple[bool, str]:
    ...
```

**引数**:
- `tool_name` (str): 承認対象のツール名
- `tool_params` (dict): ツール呼び出しパラメータ（ツールの引数辞書）

**戻り値**: `tuple[bool, str]`

#### 2.3.2 戻り値の意味

| 戻り値 | 意味 | フック側の動作 |
|--------|------|--------------|
| `(True, "")` | 承認OK | 何もしない → ツール実行を許可する |
| `(False, "修正内容")` | 修正要望 | `event.cancel_tool` にメッセージ文字列をセット → ツールキャンセル |
| `(False, "CANCEL")` | キャンセル | `event.cancel_tool` にキャンセルメッセージをセット → ツールキャンセル |

#### 2.3.3 ツール中止方法

- ツールを中止する場合は `event.stop_reason` ではなく **`event.cancel_tool`** にメッセージ文字列をセットする
- `event.cancel_tool` にセットしたメッセージ文字列はエージェントのLLMコンテキストに返却される

```python
# 承認コールバックの戻り値に基づくフック内処理例
approved, message = self._approval_callback(tool_name, tool_params)
if approved:
    return  # ツール実行を許可
elif message == "CANCEL":
    event.cancel_tool = "申請をキャンセルしました。"
else:
    event.cancel_tool = f"修正要望: {message}"
```

---

### 2.4 主要メソッド

#### 2.4.1 register_hooks(self, registry, \*\*kwargs) → None

##### 説明
HookRegistryにBeforeToolCallEventのコールバックを登録する。Strands Agents SDKがエージェント初期化時に自動呼び出す。

##### 引数
- `registry` (HookRegistry): Strands Agents SDKが提供するフックレジストリ
- `**kwargs` (Any): SDK提供の追加引数（使用しない）

##### 処理内容
1. `registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)` を呼び出してイベントハンドラーを登録する

---

#### 2.4.2 _on_before_tool_call(self, event) → None

##### 説明
BeforeToolCallEventのメインハンドラー。ツール名がフィルタ対象であれば承認プロセスを実行する。

##### 引数
- `event` (BeforeToolCallEvent): Strands Agents SDKが提供するイベントオブジェクト。`event.tool_use["name"]` でツール名を取得する

##### 処理内容
1. `tool_name = event.tool_use.get("name", "")` でツール名を取得する
2. `tool_name` が `_tool_names` に含まれない場合は即座にreturnする（スルー）
3. 含まれる場合:
   - `_approval_callback` が設定されている場合: `approved, message = self._approval_callback(tool_name, tool_params)` を呼び出す
     - `(True, "")` → returnしてツール実行を許可する
     - `(False, "CANCEL")` → `_log_approval(tool_name, "キャンセル")` → `event.cancel_tool = "申請をキャンセルしました。"` をセット
     - `(False, message)` → `_log_approval(tool_name, "修正")` → `event.cancel_tool = f"修正要望: {message}"` をセット
   - `_approval_callback` が設定されていない場合: 内部デフォルト承認処理（標準入力による3択）を実行する（後述）

##### デフォルト承認処理（`_approval_callback` 未設定時）
1. 承認プロンプトをユーザーへ提示する:
   - `"\n【申請書生成の確認】申請書の生成を実行します。「OK」「修正」「キャンセル」のいずれかを入力してください："`
2. 標準入力でユーザー選択を受け取り、正規化する
3. 選択結果に応じて分岐する:
   - OK → `_log_approval(tool_name, "OK")` 呼び出し → returnしてツール実行を許可する
   - 修正 → `_log_approval(tool_name, "修正")` 呼び出し → `event.cancel_tool = "修正を選択しました。収集情報を最初からやり直してください。"` をセット
   - キャンセル → `_log_approval(tool_name, "キャンセル")` 呼び出し → `event.cancel_tool = "申請をキャンセルしました。"` をセット
   - それ以外（無効入力）→ `"「OK」「修正」「キャンセル」のいずれかを入力してください。"` を提示してステップ1へ戻る（入力を繰り返す）

##### 入力正規化ルール（デフォルト承認処理）

| ユーザー入力例 | 正規化結果 |
|--------------|-----------|
| `"OK"`, `"ok"`, `"O"`, `"o"`, `"はい"`, `"1"` | `"OK"` |
| `"修正"`, `"修正する"`, `"2"` | `"修正"` |
| `"キャンセル"`, `"cancel"`, `"Cancel"`, `"3"` | `"キャンセル"` |
| 上記以外 | 無効（再入力を促す） |

---

#### 2.4.3 _log_approval(self, tool_name, choice) → None

##### 説明
承認操作の選択結果・実行時刻・ツール名をDATA-009（`logs/approval.log`）にJSON Lines形式で記録する。ログ書き込み失敗時はstderrへ出力してメッセージ処理を継続する（例外を再送出しない）。

##### 引数
- `tool_name` (str): 承認対象のツール名
- `choice` (str): 承認結果（`"OK"` / `"修正"` / `"キャンセル"`）

##### 処理内容
1. タイムスタンプ（ISO 8601形式）を取得する
2. `logs/approval.log` にJSONレコードを1行追記する（JSON Lines形式）
3. ログ書き込みに失敗した場合はstderrへ出力し、処理を継続する

---

## 3. ビジネスロジック

### 3.1 承認フロー

#### 処理フロー（承認コールバック使用時）

```
BeforeToolCallEvent発火
  ↓
ツール名取得（event.tool_use["name"]）
  ↓
ツール名が _tool_names に含まれるか？
  - 含まれない（TOOL-001等） → returnしてスルー（ツール実行を許可）
  - 含まれる（TOOL-002）    → 承認フローへ進む
  ↓
_approval_callback(tool_name, tool_params) を呼び出す
  ↓
戻り値の判定
  ↓
  (True, "")
    → _log_approval(tool_name, "OK")
    → returnしてTOOL-002実行を許可
  ↓
  (False, "CANCEL")
    → _log_approval(tool_name, "キャンセル")
    → event.cancel_tool = "申請をキャンセルしました。"（ツールキャンセル）
  ↓
  (False, "修正内容")
    → _log_approval(tool_name, "修正")
    → event.cancel_tool = "修正要望: {修正内容}"（ツールキャンセル）
```

#### 処理フロー（デフォルト承認処理：コールバック未設定時）

```
BeforeToolCallEvent発火
  ↓
ツール名が _tool_names に含まれる（TOOL-002）
  ↓
承認プロンプト提示
「申請書の生成を実行します。「OK」「修正」「キャンセル」のいずれかを入力してください：」
  ↓
ユーザー入力受け取り
  ↓
入力正規化
  ↓
  無効入力 → 「「OK」「修正」「キャンセル」のいずれかを入力してください。」を提示 → 再入力
  ↓
  OK
    → _log_approval(tool_name, "OK")
    → returnしてTOOL-002実行を許可
  ↓
  修正
    → _log_approval(tool_name, "修正")
    → event.cancel_tool = "修正を選択しました。収集情報を最初からやり直してください。"
  ↓
  キャンセル
    → _log_approval(tool_name, "キャンセル")
    → event.cancel_tool = "申請をキャンセルしました。"
```

---

## 4. データ設計

### 4.1 DATA-009 承認ログ

**出力先**: `logs/approval.log`

**フォーマット**: JSON Lines（1行1レコード）

```json
{
  "timestamp": "2026-04-28T12:34:56.789Z",
  "tool_name": "generate_transport_expense_form",
  "choice": "OK"
}
```

**フィールド定義**:

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| `timestamp` | str | 承認操作実行時刻（ISO 8601形式、UTC） |
| `tool_name` | str | 承認対象ツール名（`generate_transport_expense_form` または `generate_expense_form`） |
| `choice` | str | 承認結果（`"OK"` / `"修正"` / `"キャンセル"`） |

---

## 5. エラーハンドリング

| エラー種別 | 条件 | 対応 | 備考 |
|-----------|------|------|------|
| ログ書き込み失敗 | `logs/approval.log` への書き込みに失敗した場合 | stderr への出力のみ（承認フローは継続） | 承認ログ失敗で承認フロー自体を中断しない |
| event.tool_use キー不存在 | BeforeToolCallEventのtool_useに`"name"`キーが存在しない場合 | `tool_name = ""` として扱い、フィルタ対象外（スルー）とする | |
| ユーザー入力の無効値（デフォルト承認処理時） | OK/修正/キャンセル以外の入力 | 再入力を促し、入力ループを継続する | |
| コールバック例外 | `_approval_callback` 呼び出し時に例外が発生した場合 | ログ出力後に `event.cancel_tool` にエラーメッセージをセットしてツールをキャンセルする | |

---

## 6. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | 承認プロンプト提示時（デフォルト処理） | `"[HumanApprovalHook] 承認プロンプト提示: tool_name={tool_name}"` |
| INFO | コールバック呼び出し時 | `"[HumanApprovalHook] 承認コールバック呼び出し: tool_name={tool_name}"` |
| INFO | OK承認時 | `"[HumanApprovalHook] 承認OK: tool_name={tool_name}"` |
| INFO | 修正選択時 | `"[HumanApprovalHook] 修正選択: tool_name={tool_name}"` |
| INFO | キャンセル選択時 | `"[HumanApprovalHook] キャンセル選択: tool_name={tool_name}"` |
| INFO | ツール名スルー時 | `"[HumanApprovalHook] ツール名スルー: tool_name={tool_name} （フィルタ対象外）"` |
| WARNING | ログ書き込み失敗時 | `"[HumanApprovalHook] 承認ログ書き込み失敗: {error_detail}"` |

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **ツール名フィルタリングの厳密な一致**
   - `_tool_names` リストとツール名の比較は完全一致（`==`）で行う。部分一致やワイルドカードは使用しない
   - AG-002では `["generate_transport_expense_form"]`、AG-003では `["generate_expense_form"]` を渡す（混在しない）

2. **ツール中止方法**
   - ツールを中止する場合は `event.stop_reason` ではなく `event.cancel_tool` にメッセージ文字列をセットする
   - `event.cancel_tool` にセットしたメッセージはLLMコンテキストに返却される

3. **承認コールバックの優先**
   - `_approval_callback` が設定されている場合は、デフォルトの標準入力承認処理を使用しない
   - コールバックの戻り値 `(True, "")` / `(False, "CANCEL")` / `(False, "修正内容")` に基づいて `event.cancel_tool` を制御する

4. **承認プロンプトのタイミング（デフォルト処理）**
   - BeforeToolCallEventはLLMがツール呼び出しを決定した直後に発火する。この時点でドラフト提示（テキスト）は既にユーザーへ表示済みであるため、承認プロンプトはシンプルな確認のみで構わない

5. **無効入力の無限ループ対策（デフォルト処理）**
   - 要件上は上限回数を定義しないが、実装上は5回連続無効入力でキャンセルとして処理してもよい（要件上未定義）

6. **承認対象ツール名**
   - 承認対象ツール名は申請書生成ツール詳細設計書に定義された全ツール関数名とする
   - 現在の全ツール関数名: `generate_transport_expense_form`、`generate_expense_form`

7. **logs/approval.logのRotating設定**
   - `logs/error.log` と同様にRotatingFileHandlerを使用してファイルサイズ上限を管理する

---

### 7.2 パフォーマンス考慮事項

1. **ブロッキングI/O（デフォルト処理）**
   - 標準入力（`input()`）はブロッキングI/Oであるため、ユーザーが応答するまでエージェントループがブロックされる。Human-in-the-Loop承認待ちはWAITING状態として管理されるため許容する（実行制御方針.md 9.1節）

2. **ログI/Oの遅延**
   - `logs/approval.log` への書き込みは承認フローのたびに1件発生するが、軽微な遅延のため許容範囲内とする

---

### 7.3 セキュリティ考慮事項

1. **承認バイパスの防止**
   - `_tool_names` に登録されたツールはHumanApprovalHookを経由しなければ実行できない（GRD-016）
   - AG-002/AG-003のAgent初期化時にHumanApprovalHookを必ず登録することで技術的に強制する

2. **承認ログの改ざん防止**
   - `logs/approval.log` はアプリケーション書き込みのみ許可する（読み取り・削除はシステム管理者のみ）

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`:
  - `HookProvider`: フックプロバイダー基底クラス
  - `HookRegistry`: フックレジストリ
  - `BeforeToolCallEvent`: ツール呼び出し前イベント
- `logging`: Pythonの標準ロギングモジュール

### 8.2 内部モジュール
- なし（HumanApprovalHookは外部カスタム例外に依存しない。ツール中止は `event.cancel_tool` で行う）

---

## 9. テスト観点

### 9.1 機能テスト
- TOOL-002（`generate_transport_expense_form`）呼び出し時にBeforeToolCallEventが発火し、承認コールバックが呼び出されること
- コールバックが `(True, "")` を返した場合にTOOL-002の実行が許可されること
- コールバックが `(False, "CANCEL")` を返した場合に `event.cancel_tool` にキャンセルメッセージがセットされること
- コールバックが `(False, "修正内容")` を返した場合に `event.cancel_tool` に修正要望メッセージがセットされること
- TOOL-001（`calculate_transport_expense`）呼び出し時にBeforeToolCallEventがスルーされること（承認処理不実行）
- 承認操作後にDATA-009（`logs/approval.log`）に正しい内容（timestamp/tool_name/choice）が記録されること

### 9.2 デフォルト承認処理テスト（コールバック未設定時）
- 利用者がOKを選択した場合にTOOL-002の実行が許可されること（ブロック解除）
- 利用者が修正を選択した場合に `event.cancel_tool` に修正メッセージがセットされること
- 利用者がキャンセルを選択した場合に `event.cancel_tool` にキャンセルメッセージがセットされること
- 無効入力（OK/修正/キャンセル以外）で再入力プロンプトが表示されること

### 9.3 異常系テスト
- `logs/approval.log` への書き込みに失敗した場合にstderrへ出力し、承認フローが継続されること
- `event.tool_use` に `"name"` キーが存在しない場合にスルーされること（例外送出なし）
- コールバック呼び出し時に例外が発生した場合に `event.cancel_tool` にエラーメッセージがセットされること

### 9.4 統合テスト
- AG-002がHumanApprovalHookを登録した状態でTOOL-002呼び出し前に承認処理が実行されること
- AG-003がHumanApprovalHookを登録した状態でTOOL-002呼び出し前に承認処理が実行されること
- AG-001にHumanApprovalHookが登録されていないこと（TOOL-002を呼び出さないため）

---

## 10. 設定値

### 10.1 フィルタ対象ツール名（申請書生成ツール詳細設計書に定義された全ツール関数名）

| エージェント | tool_names パラメータ |
|------------|---------------------|
| AG-002 | `["generate_transport_expense_form"]` |
| AG-003 | `["generate_expense_form"]` |

### 10.2 承認ログ設定
- 出力先: `logs/approval.log`
- フォーマット: JSON Lines
- RotatingFileHandler: `logs/error.log` と同じ設定を適用（共通設定方針参照）

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 1.0 | 新フォーマットで作成 |
| 2026-04-28 | 1.1 | 修正#2：承認コールバック仕様追加（シグネチャ・戻り値・event.cancel_toolによるツール中止）、修正#8：承認対象ツール名を申請書生成ツール詳細設計書定義の全ツール関数名に変更 |
| 2026-04-28 | 1.2 | 修正#19：命名規則統一（travel→transport）。ツール名参照箇所をtransportに変更 |
