---
version: "1.0.0"
last_updated: "2026-07-03"
updated_by: ""
---

# HumanApprovalHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 3章（HumanApprovalHookの位置づけ・処理方針）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（HumanApprovalHook の共通設定）
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針）

> **参照元（エージェント詳細設計）:**
> - artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md（AG-002: 承認対象ツール・登録対象エージェント）
> - artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md（AG-003: 承認対象ツール・登録対象エージェント）

## 1. 概要

### 1.1 コンポーネントの目的

AG-002/AG-003 において、申請書生成ツール（`generate_transport_expense_form` / `generate_general_expense_form`）の実行直前に社員確認（Human-in-the-Loop: HitL）を実施するフッククラス。Strands Agents の `HookProvider` インターフェースを実装し、`BeforeToolCallEvent` をハンドリングする。社員の「OK」承認後のみツール実行を許可する（GRD-009）。

### 1.2 主要な責務

1. **承認対象ツールの検出**: `BeforeToolCallEvent` で `tool_name` が `generate_transport_expense_form` または `generate_general_expense_form` であるかを判定する
2. **社員への承認確認**: 承認対象ツール呼び出し時に申請情報サマリーを表示して「OK / 修正 / キャンセル」を確認する
3. **承認結果に基づくツール実行制御**: 「OK」の場合のみツール実行を継続する。「修正」「キャンセル」の場合はツール実行を中止して情報収集フローへ差し戻す
4. **非対象ツールのパススルー**: 承認対象外のツールは無条件に実行を継続する

### 1.3 非責務
- 申請書生成ツール以外のツール呼び出しへの介入
- AG-001 への登録（HumanApprovalHook は AG-002/AG-003 のみに登録する）
- 承認後のツール実行結果の検証

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`HumanApprovalHook`

#### 継承元
`HookProvider`（strands-agents v1.25.0）

#### 説明
Strands Agents の `HookProvider` インターフェースを実装した HitL 承認制御フック。`BeforeToolCallEvent` を購読し、承認対象ツール（申請書生成ツール）の実行前に社員の確認を取る。承認結果によりツール実行の継続/中断を制御する。

#### 登録先エージェント
- AG-002（交通費精算申請エージェント）: `generate_transport_expense_form` のみ対象
- AG-003（経費精算申請エージェント）: `generate_general_expense_form` のみ対象

---

### 2.2 初期化

#### `__init__(self)`
引数なしで初期化するシンプルな初期化メソッド。

**引数**: なし

**インスタンス変数**: なし（ステートレス設計）

---

### 2.3 主要メソッド

#### 2.3.1 register_hooks

##### 説明
`HookProvider` インターフェースで定義された抽象メソッドの実装。フックレジストリに `BeforeToolCallEvent` ハンドラーを登録する。

##### 引数
- `hook_registry` (HookRegistry): strands-agents のフックレジストリ

##### 戻り値
- `None`

##### 処理内容
1. `hook_registry.add_hook(BeforeToolCallEvent, self.before_tool_call)` を呼び出す

---

#### 2.3.2 before_tool_call

##### 説明
`BeforeToolCallEvent` のハンドラー。承認対象ツールの実行直前に呼び出される。承認確認の実際の入出力は `approval_callback` に委譲する。

##### 引数
- `event` (BeforeToolCallEvent): ツール呼び出し直前イベント。`tool.name`・申請情報などの情報を含む

##### 戻り値
- `None`

##### 処理内容
1. `event.tool.name` を取得する
2. 承認対象ツール名（`generate_transport_expense_form` または `generate_general_expense_form`）と一致するかを判定する
3. **一致しない場合**: 処理を即座に終了してツール実行をパススルーする
4. **一致する場合**: 以下の承認確認フローを実行する
   1. `self.approval_callback(tool_name, tool_params)` を呼び出して `(approved: bool, message: str)` を取得する
      - `tool_params` は `event.tool.tool_use.input` から取得する
   2. `approved` が `True` の場合: ツール実行を継続する（処理を返す）
   3. `approved` が `False` の場合: `event.cancel_tool = message` をセットしてツール実行を中止する
      - `message` が `"CANCEL"` の場合: キャンセルメッセージをセットしてフロー終了（CLOSED）
      - `message` がその他の文字列の場合: 修正内容メッセージをセットして情報収集フローへ差し戻し

##### approval_callback のシグネチャ
```python
def approval_callback(tool_name: str, tool_params: dict) -> tuple[bool, str]:
    ...
```

- 戻り値の意味:
  - `(True, "")` → 承認OK（ツール実行される。何もしない）
  - `(False, "修正内容の文字列")` → 修正要望（`event.cancel_tool` にメッセージ文字列をセットしてツールキャンセル）
  - `(False, "CANCEL")` → キャンセル（`event.cancel_tool` にキャンセルメッセージをセットしてツールキャンセル）

---

### 2.4 フック設計

#### 2.4.1 購読イベント

| イベント | 目的 |
|---------|------|
| `BeforeToolCallEvent` | 承認対象ツールの実行直前に社員確認を実施する |

#### 2.4.2 承認対象ツール名

| ツール名 | 対象エージェント |
|---------|--------------|
| `generate_transport_expense_form` | AG-002（交通費精算申請エージェント） |
| `generate_general_expense_form` | AG-003（経費精算申請エージェント） |

> **重要**: 承認対象ツール名は申請書生成ツール詳細設計書に定義された全ツール関数名を参照する。
> 現在の対象: `generate_transport_expense_form` / `generate_general_expense_form`
> 上記ツール名はエージェント詳細設計書（DD-02）と完全一致させること。

#### 2.4.3 非承認対象ツール

| ツール名 | 扱い |
|---------|------|
| `calculate_transport_fare`（TOOL-001） | パススルー（承認不要） |
| その他の将来のツール | パススルー（承認不要） |

---

## 3. ビジネスロジック

### 3.1 承認確認フロー

#### 処理フロー

```
BeforeToolCallEvent 発生
  ↓
tool_name の取得（event.tool.name）
  ↓
承認対象ツール判定
  - 非対象ツール → パススルー（即時 return）
  ↓
  - 対象ツール（generate_transport_expense_form / generate_general_expense_form）
  ↓
approval_callback(tool_name, tool_params) を呼び出す
  ↓
戻り値の判定
  - (True, "") → ツール実行継続（return）
  - (False, "CANCEL") → event.cancel_tool = "CANCEL" → フロー終了（CLOSED）
  - (False, "修正内容の文字列") → event.cancel_tool = message → 情報収集フローへ差し戻し
```

#### 分岐条件の詳細
- **承認対象判定**: `event.tool.name in {"generate_transport_expense_form", "generate_general_expense_form"}` で判定する
- **コールバック呼び出し**: `self.approval_callback(tool_name, tool_params)` で `(bool, str)` のタプルを取得する
- **ツール中止方法**: `event.cancel_tool = message` でメッセージ文字列をセットする（`event.cancel_tool_call()` は使用しない）
- **再試行ロジック**: `approval_callback` の内部で実装する（`before_tool_call` は戻り値のみで判定する）

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| 無効入力（3回超） | 「OK / 修正 / キャンセル」以外の入力が3回連続 | 「修正」として処理する | `"入力が認識できませんでした。情報収集からやり直します。"` |
| EOFError | パイプ入力やテスト環境での入力終端 | 「キャンセル」として処理する | なし（ログのみ） |

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | 承認確認開始時 | `"HumanApprovalHook: 承認確認開始 tool_name={tool_name}"` |
| INFO | 承認OK時 | `"HumanApprovalHook: 承認OK tool_name={tool_name}"` |
| INFO | 修正選択時 | `"HumanApprovalHook: 修正選択 tool_name={tool_name}"` |
| INFO | キャンセル選択時 | `"HumanApprovalHook: キャンセル選択 tool_name={tool_name}"` |
| WARNING | 無効入力時 | `"HumanApprovalHook: 無効入力（{回数}回目） input={input}"` |
| WARNING | 再試行上限到達時 | `"HumanApprovalHook: 再試行上限超過 → 修正として処理"` |

---

## 6. 使用例

### 6.1 AG-002/AG-003 への登録方法

```python
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent
from handlers.human_approval_hook import HumanApprovalHook
from handlers.loop_control_hook import LoopControlHook

# AG-002（交通費精算申請エージェント）への登録例
human_approval_hook = HumanApprovalHook()
loop_control_hook = LoopControlHook(max_iterations=10)

agent = Agent(
    model=bedrock_model,
    system_prompt=system_prompt,
    tools=[calculate_transport_fare, generate_transport_expense_form],
    conversation_manager=SlidingWindowConversationManager(window_size=20),
    hooks=[human_approval_hook, loop_control_hook],  # HumanApprovalHook + LoopControlHook
)
```

---

### 6.2 approval_callback の実装例と before_tool_call での使用例

```python
def approval_callback(tool_name: str, tool_params: dict) -> tuple[bool, str]:
    print(f"申請書を生成します。よろしいですか？")
    user_input = input("承認 / 修正 / キャンセル: ")

    if user_input == "承認":
        return (True, "")
    elif user_input == "キャンセル":
        return (False, "CANCEL")
    else:
        return (False, user_input)  # 修正内容を返す


# HumanApprovalHook の before_tool_call メソッドでの処理:
def before_tool_call(self, event: BeforeToolCallEvent):
    tool_name = event.tool.name
    tool_params = event.tool.tool_use.input

    approved, message = self.approval_callback(tool_name, tool_params)

    if not approved:
        event.cancel_tool = message  # メッセージをセット（event.cancel_tool_call() は使用しない）
```

---

### 6.3 承認確認フローの動作例

```
# generate_transport_expense_form 呼び出し直前に発火
HumanApprovalHook: 承認確認開始 tool_name=generate_transport_expense_form

申請情報を確認してください。
  申請者名: 山田太郎
  申請日: 2026-07-03
  移動区間: 渋谷→新宿（電車、780円）
  合計: 780円
承認しますか？（OK / 修正 / キャンセル）
> OK
HumanApprovalHook: 承認OK tool_name=generate_transport_expense_form
# ツール実行が継続される
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **承認対象ツール名の厳格一致**
   - 承認対象ツール名は `"generate_transport_expense_form"` および `"generate_general_expense_form"` と完全一致させること
   - エージェント詳細設計書（DD-02）のツール名定義と同一であること

2. **AG-001 への登録禁止**
   - AG-001 は TOOL-002（申請書生成ツール）を呼び出さないため、`HumanApprovalHook` を登録しない
   - AG-002/AG-003 のみに登録すること

3. **ステートレス設計**
   - `HumanApprovalHook` はインスタンス変数を持たない。複数エージェントへの同一インスタンス共有は避け、エージェントごとに新しいインスタンスを生成することを推奨する

4. **`event.cancel_tool` の使用方法**
   - ツール実行をキャンセルする場合は `event.cancel_tool = message` でメッセージ文字列をセットする
   - `event.stop_reason` や `event.cancel_tool_call()` は使用しない
   - strands-agents v1.25.0 の `BeforeToolCallEvent` において、`event.cancel_tool` にメッセージをセットするとツール実行がキャンセルされ、エージェントの ReAct ループに制御が戻る

---

### 7.2 パフォーマンス考慮事項

1. **ブロッキング I/O**
   - `input()` はブロッキング呼び出しであるため、テスト環境では `monkeypatch` 等でモック化すること

---

### 7.3 セキュリティ考慮事項

1. **GRD-009 の保証**
   - フックレベルで申請書生成ツール実行前に承認を必須化することで、システムプロンプトへの指示のみによる保証よりも強固な二重保証を実現する

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: `HookProvider`, `HookRegistry`, `BeforeToolCallEvent`（strands-agents v1.25.0）
- `logging`: 標準ライブラリ、ログ出力

### 8.2 内部モジュール
- なし

---

## 9. テスト観点

### 9.1 機能テスト
- `generate_transport_expense_form` 呼び出し時に承認確認が1回のみ実施されること
  - **入力**: `event.tool.name="generate_transport_expense_form"`, `approval_callback` が `(True, "")` を返す
  - **期待結果**: ツール実行が継続される
- `generate_general_expense_form` 呼び出し時に承認確認が1回のみ実施されること
  - **入力**: `event.tool.name="generate_general_expense_form"`, `approval_callback` が `(True, "")` を返す
  - **期待結果**: ツール実行が継続される
- `calculate_transport_fare` 呼び出し時に承認確認が実施されないこと（パススルー）
  - **入力**: `event.tool.name="calculate_transport_fare"`
  - **期待結果**: 承認確認なしでツール実行が継続される

### 9.2 異常系テスト
- 「修正」選択時に `event.cancel_tool` に修正内容メッセージがセットされてツール実行がキャンセルされること
  - **入力**: `approval_callback` が `(False, "修正内容の文字列")` を返す
  - **期待結果**: `event.cancel_tool` に修正内容の文字列がセットされる
- 「キャンセル」選択時に `event.cancel_tool` に `"CANCEL"` がセットされること
  - **入力**: `approval_callback` が `(False, "CANCEL")` を返す
  - **期待結果**: `event.cancel_tool` に `"CANCEL"` がセットされる
- 無効入力が3回連続した場合に `approval_callback` 内で「修正」として処理されること
  - **入力**: `approval_callback` 内で無効入力 `"abc"` × 3回
  - **期待結果**: `approval_callback` が `(False, "修正内容の文字列")` を返し、`event.cancel_tool` にメッセージがセットされる

### 9.3 境界値テスト
- 入力が大文字・スペース混在（例: `" OK "`, `"ok"`, `"OK"`）の場合も承認OKとして処理されること
  - **期待結果**: いずれもツール実行が継続される

---

## 10. 設定値

### 10.1 定数値
- 承認対象ツール名: `{"generate_transport_expense_form", "generate_general_expense_form"}`
- 無効入力の再試行上限回数: `3`

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-07-03 | 2.0 | 新フォーマットで作成 |
