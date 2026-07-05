---
version: "1.0.0"
last_updated: "2026-07-03"
updated_by: ""
---

# LoopControlHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 4章（LoopControlHookの位置づけ・処理方針）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御の方針・最大反復回数設定）
> - artifacts/03_system-design/outputs/共通設定方針.md（LoopControlHook の共通設定・全エージェント共通登録）
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針）

> **参照元（エージェント詳細設計）:**
> - artifacts/05_detailed-design/outputs/申請受付窓口エージェント詳細設計.md（AG-001: LoopControlHook登録）
> - artifacts/05_detailed-design/outputs/交通費精算申請エージェント詳細設計.md（AG-002: LoopControlHook登録）
> - artifacts/05_detailed-design/outputs/経費精算申請エージェント詳細設計.md（AG-003: LoopControlHook登録）

## 1. 概要

### 1.1 コンポーネントの目的

AG-001/AG-002/AG-003 全エージェントにおいて、ReAct ループ（エージェントの思考・ツール呼び出しの繰り返しサイクル）の反復回数を制限するフッククラス。Strands Agents の `HookProvider` インターフェースを実装し、`BeforeInvocationEvent`・`AfterModelCallEvent`・`AfterInvocationEvent` の3イベントをハンドリングする。最大反復回数 `max_iterations=10` を超過した場合に `LoopLimitError` を raise してループを強制終了する。

### 1.2 主要な責務

1. **反復カウンター管理**: `BeforeInvocationEvent` で呼び出し開始時にカウンターを0にリセットし、`AfterModelCallEvent` でモデル呼び出し後にカウンターをインクリメントする
2. **上限チェックと強制終了**: カウンターが `max_iterations` に達した場合に `LoopLimitError` を raise してループを終了する
3. **呼び出し後ログ出力**: `AfterInvocationEvent` で呼び出し完了時に合計ループ回数を INFO ログに出力する

### 1.3 非責務
- セッション状態の更新（ErrorHandler / SessionManager の責務）
- エラーメッセージ生成（ErrorHandler の責務）
- ユーザーへのメッセージ表示（呼び出し元エージェントの責務）

---

## 2. 設計詳細

### 2.0 関連クラス定義

#### LoopLimitError

##### クラス名
`LoopLimitError`

##### 継承元
`Exception`

##### 定義モジュール
`handlers/loop_control_hook.py`（`LoopControlHook` と同じファイル内）

##### 説明
LoopControlHook がループ上限到達を検知した際に raise するカスタム例外クラス。上限到達時の詳細情報（現在のループ回数・設定上限値・エージェント名）をフィールドとして保持する。

##### フィールド

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| `current_iteration` | `int` | 現在のループ回数 |
| `max_iterations` | `int` | 設定された上限値 |
| `agent_name` | `str` | エージェント名 |

##### コード例

```python
class LoopLimitError(Exception):
    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ループ上限到達: {agent_name} が {current_iteration}/{max_iterations} 回に達しました"
        )
```

---

### 2.1 クラス基本情報

#### クラス名
`LoopControlHook`

#### 継承元
`HookProvider`（strands-agents v1.25.0）

#### 説明
Strands Agents の `HookProvider` インターフェースを実装した ReAct ループ制御フック。`BeforeInvocationEvent`・`AfterModelCallEvent`・`AfterInvocationEvent` の3イベントを購読して、エージェントの ReAct ループが `max_iterations` 回を超えて継続しないよう制御する。全エージェント（AG-001/AG-002/AG-003）に共通して登録される。

#### 登録先エージェント
- AG-001（申請受付窓口エージェント）: `max_iterations=10`
- AG-002（交通費精算申請エージェント）: `max_iterations=10`
- AG-003（経費精算申請エージェント）: `max_iterations=10`

---

### 2.2 初期化

#### `__init__(self, max_iterations: int = 10)`
最大反復回数を設定してインスタンスを初期化する。

**引数**:
- `max_iterations` (int): ReAct ループの最大反復回数（デフォルト: `10`）

**インスタンス変数**:
- `max_iterations` (int): 最大反復回数
- `iteration_count` (int): 現在の反復カウンター（初期値: `0`）

---

### 2.3 主要メソッド

#### 2.3.1 register_hooks

##### 説明
`HookProvider` インターフェースで定義された抽象メソッドの実装。フックレジストリに3つのイベントハンドラーを登録する。

##### 引数
- `hook_registry` (HookRegistry): strands-agents のフックレジストリ

##### 戻り値
- `None`

##### 処理内容
1. `hook_registry.add_hook(BeforeInvocationEvent, self.before_invocation)` を呼び出す
2. `hook_registry.add_hook(AfterModelCallEvent, self.after_model_call)` を呼び出す
3. `hook_registry.add_hook(AfterInvocationEvent, self.after_invocation)` を呼び出す

---

#### 2.3.2 before_invocation

##### 説明
`BeforeInvocationEvent` のハンドラー。エージェントの呼び出し開始時に反復カウンターを0にリセットする。

##### 引数
- `event` (BeforeInvocationEvent): エージェント呼び出し開始イベント

##### 戻り値
- `None`

##### 処理内容
1. `self.iteration_count = 0` にリセットする
2. `"LoopControlHook: 反復カウンタリセット"` を DEBUG レベルでログ出力する

---

#### 2.3.3 after_model_call

##### 説明
`AfterModelCallEvent` のハンドラー。LLM モデル呼び出し後に反復カウンターをインクリメントし、上限超過時に `LoopLimitError` を raise する。`event.exception` が存在する場合はカウントをスキップする。

##### 引数
- `event` (AfterModelCallEvent): LLM モデル呼び出し後イベント

##### 戻り値
- `None`

##### 処理内容
1. `event.exception` が存在する場合 → カウントをスキップして return する
2. `self.iteration_count += 1` でカウンターをインクリメントする
3. `self.iteration_count > self.max_iterations` を判定する
4. **上限超過の場合**:
   1. `"LoopControlHook: 上限超過 iteration_count={self.iteration_count} max_iterations={self.max_iterations}"` を WARNING レベルでログ出力する
   2. `raise LoopLimitError(current_iteration=self.iteration_count, max_iterations=self.max_iterations, agent_name=self.agent_name)` を raise する
5. **上限未満の場合**: `"LoopControlHook: 反復カウント更新 count={self.iteration_count}/{self.max_iterations}"` を INFO レベルでログ出力する

---

#### 2.3.4 after_invocation

##### 説明
`AfterInvocationEvent` のハンドラー。エージェントの呼び出し完了後に合計ループ回数を INFO ログに出力する。カウンターのリセットは行わない（次回の `before_invocation` でリセットされる）。

##### 引数
- `event` (AfterInvocationEvent): エージェント呼び出し完了イベント

##### 戻り値
- `None`

##### 処理内容
1. `"LoopControlHook: 呼び出し完了 合計{iteration_count}ループ agent={agent_name}"` を INFO レベルでログ出力する
2. カウンターのリセットは行わない

---

### 2.4 フック設計

#### 2.4.1 購読イベントと役割

| イベント | 役割 |
|---------|------|
| `BeforeInvocationEvent` | エージェント呼び出し開始時にカウンターを0にリセットする |
| `AfterModelCallEvent` | LLM モデル呼び出し後にカウンターをインクリメントし上限を確認する |
| `AfterInvocationEvent` | エージェント呼び出し完了後に合計ループ回数を INFO ログに出力する |

#### 2.4.2 設定値

| 設定項目 | 設定値 | 説明 |
|---------|--------|------|
| `max_iterations` | `10` | ReAct ループの最大反復回数（AG-001/AG-002/AG-003 共通: 共通設定方針 2.1節） |

---

## 3. ビジネスロジック

### 3.1 ループ制御フロー

#### 処理フロー

```
エージェント呼び出し開始（BeforeInvocationEvent）
  ↓
iteration_count = 0 にリセット
  ↓
ReAct ループ（繰り返し）
  ↓
LLM モデル呼び出し後（AfterModelCallEvent）
  ↓
event.exception が存在する?
  - YES → カウントをスキップして return
  - NO  → iteration_count += 1
              ↓
            iteration_count > max_iterations (10)?
              - NO  → ReAct ループ継続（次のターン）
              - YES → WARNING ログ出力
                        ↓
                       raise LoopLimitError(current_iteration, max_iterations, agent_name)
                        ↓
                       呼び出し元エージェントの例外ハンドラーへ
  ↓
エージェント呼び出し完了（AfterInvocationEvent）
  ↓
合計ループ回数を INFO ログ出力
```

#### 分岐条件の詳細
- **上限判定**: `self.iteration_count > self.max_iterations` で判定する
- **例外スキップ**: `event.exception` が存在する場合はカウントをスキップする（既に例外が発生しているターンでのカウントを避けるため）
- **カウンターの意味**: `iteration_count` は LLM モデル呼び出し回数（≒ ReAct ターン数）を表す。1回の ReAct ターン = 1回のモデル呼び出し

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| LoopLimitError（ループ上限超過） | `iteration_count > max_iterations` | `LoopLimitError` を raise する | `"ループ上限到達: {agent_name} が {current_iteration}/{max_iterations} 回に達しました"` |

### 4.2 LoopLimitError の受け取り先

- **AG-001**: `reception_agent_loop` 関数の `try/except LoopLimitError` でキャッチして TERMINATED 処理
- **AG-002**: `handle_transport_expense_application` 関数の `try/except LoopLimitError` でキャッチして AG-001 にエラー要約を返す
- **AG-003**: `handle_general_expense_application` 関数の `try/except LoopLimitError` でキャッチして AG-001 にエラー要約を返す

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| DEBUG | before_invocation 実行時 | `"LoopControlHook: 反復カウンタリセット"` |
| INFO | after_model_call（上限未満）時 | `"LoopControlHook: 反復カウント更新 count={iteration_count}/{max_iterations}"` |
| WARNING | after_model_call（上限超過）時 | `"LoopControlHook: 上限超過 iteration_count={iteration_count} max_iterations={max_iterations}"` |
| INFO | after_invocation 実行時 | `"LoopControlHook: 呼び出し完了 合計{iteration_count}ループ agent={agent_name}"` |
| INFO | BeforeModelCallEvent 受信時 | `"LoopControlHook: iteration={iteration_count}/{max_iterations} agent={agent_name}"` |
| INFO | BeforeToolCallEvent 受信時 | `"LoopControlHook: tool_call={tool_name} agent={agent_name}"` |
| INFO | AfterToolCallEvent 受信時 | `"LoopControlHook: tool_done={tool_name} agent={agent_name}"` |

---

## 6. 使用例

### 6.1 全エージェントへの登録方法

```python
from strands.agent.conversation_manager import SlidingWindowConversationManager
from strands import Agent
from handlers.loop_control_hook import LoopControlHook

# AG-001（申請受付窓口エージェント）への登録例
loop_control_hook = LoopControlHook(max_iterations=10)

agent = Agent(
    model=bedrock_model,
    system_prompt=RECEPTION_AGENT_SYSTEM_PROMPT,
    tools=[handle_transport_expense_application, handle_general_expense_application],
    conversation_manager=SlidingWindowConversationManager(window_size=30),
    hooks=[loop_control_hook],  # LoopControlHook のみ（AG-001 は HumanApprovalHook なし）
)

# AG-002（交通費精算申請エージェント）への登録例
from handlers.human_approval_hook import HumanApprovalHook

human_approval_hook = HumanApprovalHook()
loop_control_hook = LoopControlHook(max_iterations=10)

agent = Agent(
    model=bedrock_model,
    system_prompt=system_prompt,
    tools=[calculate_transport_fare, generate_transport_expense_form],
    conversation_manager=SlidingWindowConversationManager(window_size=20),
    hooks=[human_approval_hook, loop_control_hook],  # 両フック登録
)
```

---

### 6.2 LoopLimitError のキャッチ例

```python
from handlers.loop_control_hook import LoopControlHook, LoopLimitError

loop_control_hook = LoopControlHook(max_iterations=10)

try:
    response = agent(query, invocation_state=invocation_state)
    return response
except LoopLimitError as e:
    # LoopControlHook による強制終了
    logger.warning(
        f"LoopControlHook LoopLimitError: {e} "
        f"(agent={e.agent_name}, {e.current_iteration}/{e.max_iterations})"
    )
    return error_handler.handle_execution_blocked(action="LoopControlHook上限超過")
except Exception as e:
    logger.error(f"Exception: {e}")
    return error_handler.handle_unexpected_error(error=e)
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **インスタンスの再利用**
   - `LoopControlHook` インスタンスは `iteration_count` インスタンス変数を持つため、複数エージェントへの同一インスタンス共有は避け、エージェントごとに新しいインスタンスを生成すること

2. **AfterInvocationEvent の扱い**
   - `AfterInvocationEvent` ではカウンターリセットを行わない。合計ループ回数のみを INFO ログに出力する
   - 次回の `BeforeInvocationEvent` でカウンターがリセットされるため、前回の呼び出し状態を引き継がない

3. **カウンターのスコープ**
   - `iteration_count` は「1回のエージェント呼び出し（`agent(query, ...)`）」のスコープで管理する
   - `BeforeInvocationEvent` で0にリセットされるため、前回の呼び出し状態を引き継がない

4. **max_iterations の意味**
   - `max_iterations=10` は LLM モデル呼び出し回数（ReAct ターン数）の上限であり、ユーザーとの対話回数（FR-012: 30回）とは別のカウンターである

---

### 7.2 パフォーマンス考慮事項

1. **軽量な実装**
   - ループ制御はインクリメントと比較のみであるため処理負荷は無視できる

---

### 7.3 セキュリティ考慮事項

1. **無限ループ防止**
   - `max_iterations` による上限設定で、LLM がツール呼び出しを無限に繰り返すシナリオ（例: 循環ロジック・ハルシネーションによる過剰なツール呼び出し）を防止する

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: `HookProvider`, `HookRegistry`, `BeforeInvocationEvent`, `AfterModelCallEvent`, `AfterInvocationEvent`（strands-agents v1.25.0）
- `logging`: 標準ライブラリ、ログ出力

### 8.2 内部モジュール
- `handlers/loop_control_hook.py`: `LoopLimitError`（`LoopControlHook` と同ファイルに定義）
  - 外部モジュールからは `from handlers.loop_control_hook import LoopLimitError` でインポートする

---

## 9. テスト観点

### 9.1 機能テスト
- `BeforeInvocationEvent` 受信時に `iteration_count` が0にリセットされること
  - **入力**: `iteration_count=5`（前回の残り）の状態で BeforeInvocationEvent 発火
  - **期待結果**: `iteration_count == 0`
- `AfterModelCallEvent` 受信のたびに `iteration_count` がインクリメントされること
  - **入力**: AfterModelCallEvent を連続5回発火（`event.exception` は None）
  - **期待結果**: `iteration_count == 5`
- `iteration_count` が `max_iterations(=10)` を超えた時点で `LoopLimitError` が raise されること
  - **入力**: AfterModelCallEvent を連続11回発火
  - **期待結果**: 11回目で `LoopLimitError` が raise される
- `LoopLimitError` の3フィールドが正しく設定されること
  - **入力**: `LoopControlHook(max_iterations=10, agent_name="AG-001")`, AfterModelCallEvent を11回発火
  - **期待結果**: `e.current_iteration == 11`, `e.max_iterations == 10`, `e.agent_name == "AG-001"`
- `event.exception` が存在する場合にカウントがスキップされること
  - **入力**: `event.exception` に例外オブジェクトを設定した AfterModelCallEvent を発火
  - **期待結果**: `iteration_count` がインクリメントされない（カウントがスキップされる）
- `AfterInvocationEvent` 受信後もカウンターがリセットされないこと
  - **入力**: `iteration_count=7` の状態で AfterInvocationEvent 発火
  - **期待結果**: `iteration_count == 7`（リセットされない）

### 9.2 異常系テスト
- 10回目の `AfterModelCallEvent` では `LoopLimitError` が raise されないこと
  - **入力**: AfterModelCallEvent を連続10回発火
  - **期待結果**: `LoopLimitError` は raise されない（`iteration_count == 10`）
- 11回目の `AfterModelCallEvent` で `LoopLimitError` が raise されること
  - **入力**: AfterModelCallEvent を連続11回発火
  - **期待結果**: 11回目で `LoopLimitError` が raise される

### 9.3 境界値テスト
- `max_iterations=1` の場合に2回目の `AfterModelCallEvent` で `LoopLimitError` が raise されること
  - **入力**: `LoopControlHook(max_iterations=1)`, AfterModelCallEvent を2回発火
  - **期待結果**: 2回目で `LoopLimitError` が raise される

---

## 10. 設定値

### 10.1 定数値
- デフォルト最大反復回数: `10`（`__init__` のデフォルト引数）
- 適用エージェント: AG-001/AG-002/AG-003 全エージェント共通（共通設定方針 2.1節）

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-07-03 | 2.0 | 新フォーマットで作成 |
