# LoopControlHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 4章（LoopControlHookの位置づけ・処理概要）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針・エラー分類）
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント（AG-001/AG-002/AG-003）のReActループのイテレーション回数を監視し、最大10回で強制停止する。LLMの暴走・同一アクション繰り返し・想定外の無限ループを防止する（実行制御方針.md 10.1節）。ループ上限到達時には `LoopLimitError`（カスタム例外）を送出し、呼び出し元でErrorHandlerを通じてユーザーへ通知する。

### 1.2 主要な責務

1. **ループカウンタ管理**: エージェント呼び出し開始時（BeforeInvocationEvent）にカウンタを0にリセットし、LLM呼び出し後（AfterModelCallEvent）にインクリメントする。ただし `event.exception` が存在する場合はカウントをスキップする
2. **上限監視・強制停止**: カウンタが `max_iterations`（デフォルト10回）に到達した時点でループを強制停止する（`LoopLimitError` 送出）
3. **ログ出力**: BeforeModelCallEvent・BeforeToolCallEvent・AfterToolCallEventに対してもINFOレベルのログを出力する
4. **合計ループ回数記録**: エージェント呼び出し完了後（AfterInvocationEvent）に合計ループ回数をINFOレベルでログ出力する（カウンタリセットは行わない）

### 1.3 非責務

- **Amazon Bedrockのリトライ制御**（Strands Agents SDK の組み込みリトライ機構が担当）
- **ユーザー向けエラーメッセージ生成（詳細）**（ErrorHandler.handle_loop_limit_error()に委譲）
- **セッション状態の直接変更**（Strands Agents SDK が担当）

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`LoopControlHook`

#### 説明
全エージェント（AG-001/AG-002/AG-003）のReActループイテレーション数を監視し、max_iterations（デフォルト10）回で強制停止するHookProviderクラス。`handlers/hooks.py` に実装する。Strands Agents SDKのHookProvider（またはCallback）として実装する。ループカウンタはインスタンス変数として管理し、エージェント間で独立している。

---

### 2.2 初期化

#### `__init__(self, max_iterations: int = 10)`
最大イテレーション数を受け取って初期化する。

**引数**:
- `max_iterations` (`int`): 最大ループイテレーション数（デフォルト: 10）

**インスタンス変数**:
- `max_iterations` (`int`): 最大ループイテレーション数（10）
- `_iteration_count` (`int`): 現在のループイテレーションカウンタ（0で初期化）

---

### 2.3 主要メソッド

#### 2.3.1 _reset_counter

##### 説明
ループカウンタを0にリセットする。BeforeInvocationEventのハンドラーから呼び出す。

##### 引数
なし

##### 戻り値
- `None`

##### 処理内容
1. `self._iteration_count = 0` でカウンタをリセットする

---

#### 2.3.2 _increment_and_check

##### 説明
ループカウンタをインクリメントし、max_iterationsに到達した場合は `LoopLimitError` を送出する。AfterModelCallEventのハンドラーから呼び出す（`event.exception` が存在しない場合のみ）。

##### 引数
- `agent_name` (`str`): イベントから取得したエージェント名（取得できない場合は `"unknown"`）

##### 戻り値
- `None`

##### 例外
- `LoopLimitError`: `_iteration_count >= max_iterations` の場合に送出する

##### 処理内容
1. `self._iteration_count += 1` でカウンタをインクリメントする
2. `_iteration_count >= max_iterations` の場合:
   a. `"[LoopControlHook] Loop limit reached: iteration_count={_iteration_count}, max_iterations={max_iterations}, agent_name={agent_name}"` をWARNINGレベルでログ記録する
   b. `raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self.max_iterations, agent_name=agent_name)` を送出する
3. それ以外の場合: 何もしない

---

### 2.4 フック設計

#### 2.4.1 フック登録

##### `register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None`
フックの登録

**登録するイベント（全6イベント）**:

1. `BeforeInvocationEvent`: `_handle_before_invocation`
   - **処理**: ループカウンタを0にリセットする
   - **登録タイミング**: AG-001/AG-002/AG-003のAgentインスタンス生成時（各エージェントのファクトリ関数またはmain関数で登録）
   - **依存関係**: HumanApprovalHookと独立（依存なし）

2. `BeforeModelCallEvent`: `_handle_before_model_call`
   - **処理**: ループ回数をINFOレベルでログ出力
   - **登録タイミング**: BeforeInvocationEventと同タイミングで登録
   - **依存関係**: BeforeInvocationEventのリセット後に発火する

3. `AfterModelCallEvent`: `_handle_after_model_call`
   - **処理**: カウントアップ・上限監視（`event.exception` が存在する場合はスキップ）
   - **登録タイミング**: BeforeInvocationEventと同タイミングで登録
   - **依存関係**: BeforeInvocationEventのリセット後に発火するため、カウンタリセットと順序整合性あり

4. `AfterInvocationEvent`: `_handle_after_invocation`
   - **処理**: 合計ループ回数をINFOレベルでログ出力（カウンタリセットは行わない）
   - **登録タイミング**: BeforeInvocationEventと同タイミングで登録
   - **依存関係**: AfterModelCallEventのカウントアップ完了後に発火

5. `BeforeToolCallEvent`: `_handle_before_tool_call`
   - **処理**: ツール名をINFOレベルでログ出力
   - **登録タイミング**: BeforeInvocationEventと同タイミングで登録
   - **依存関係**: 独立したログ用イベント

6. `AfterToolCallEvent`: `_handle_after_tool_call`
   - **処理**: ツール名をINFOレベルでログ出力
   - **登録タイミング**: BeforeInvocationEventと同タイミングで登録
   - **依存関係**: BeforeToolCallEventの後に発火

**登録順序**: 6イベントを同時登録する。発火順序はStrands Agents SDKが制御するため、登録順序の依存はない

---

#### 2.4.2 イベントハンドラー

##### _handle_before_invocation

**説明**: エージェント呼び出し開始時に発火するイベントを受信し、ループカウンタを0にリセットする。

**処理内容**:
1. `_reset_counter()` を呼び出してカウンタを0にリセットする
2. INFOレベルで `"[LoopControlHook] BeforeInvocationEvent: counter reset to 0"` をログ記録する

**ログ出力**: `"[LoopControlHook] BeforeInvocationEvent: counter reset to 0"`

---

##### _handle_before_model_call

**説明**: LLM呼び出し前に発火するイベントを受信し、現在のループ回数をINFOレベルでログ出力する。

**処理内容**:
1. イベントからエージェント名（`agent_name`）を取得する。取得できない場合は `"unknown"` を使用する
2. INFOレベルで現在のループ回数をログ記録する

**ログ出力**: `"[LoopControlHook] BeforeModelCallEvent: current_iteration={count} in agent '{agent_name}'"`

---

##### _handle_after_model_call

**説明**: LLM呼び出し完了後に発火するイベントを受信し、`event.exception` が存在しない場合のみループカウンタをインクリメントして上限到達を監視する。

**処理内容**:
1. `event.exception` が存在する場合: カウントアップをスキップして処理を終了する
2. `event.exception` が存在しない場合:
   a. イベントからエージェント名（`agent_name`）を取得する。取得できない場合は `"unknown"` を使用する
   b. `_increment_and_check(agent_name)` を呼び出す
   c. カウンタが max_iterations に到達した場合: `_increment_and_check()` 内で `LoopLimitError` が送出される

**ログ出力**:
- 上限到達時（WARNINGレベル）: `"[LoopControlHook] Loop limit reached: iteration_count={count}, max_iterations={max}, agent_name={agent_name}"`

---

##### _handle_after_invocation

**説明**: エージェント呼び出し完了後に発火するイベントを受信し、合計ループ回数をINFOレベルでログ出力する。カウンタのリセットは行わない。

**処理内容**:
1. イベントからエージェント名（`agent_name`）を取得する。取得できない場合は `"unknown"` を使用する
2. INFOレベルで合計ループ回数をログ記録する

**ログ出力**: `"[LoopControlHook] AfterInvocationEvent: total_iterations={count} in agent '{agent_name}'"`

---

##### _handle_before_tool_call

**説明**: ツール呼び出し前に発火するイベントを受信し、ツール名をINFOレベルでログ出力する。

**処理内容**:
1. イベントからツール名（`tool_name`）を取得する
2. INFOレベルでツール名をログ記録する

**ログ出力**: `"[LoopControlHook] BeforeToolCallEvent: tool_name={tool_name}"`

---

##### _handle_after_tool_call

**説明**: ツール呼び出し完了後に発火するイベントを受信し、ツール名をINFOレベルでログ出力する。

**処理内容**:
1. イベントからツール名（`tool_name`）を取得する
2. INFOレベルでツール名をログ記録する

**ログ出力**: `"[LoopControlHook] AfterToolCallEvent: tool_name={tool_name}"`

---

## 3. ビジネスロジック

### 3.1 ループカウンタ管理フロー

#### 処理フロー

```
エージェント呼び出し開始
  ↓
BeforeInvocationEvent 発火
  → _handle_before_invocation()
  → _reset_counter(): _iteration_count = 0
  ↓
LLM推論（1 ReActイテレーション）
  ↓
BeforeModelCallEvent 発火
  → _handle_before_model_call()
  → INFOログ: current_iteration={count} in agent '{agent_name}'
  ↓
AfterModelCallEvent 発火（LLM正常レスポンス後）
  → _handle_after_model_call()
  → event.exception が存在する場合: スキップ（カウントアップしない）
  → event.exception が存在しない場合:
      → _increment_and_check(agent_name): _iteration_count += 1
  ↓
_iteration_count < max_iterations(10) の場合
  → 正常: ツール実行へ継続
  ↓
BeforeToolCallEvent 発火
  → _handle_before_tool_call()
  → INFOログ: tool_name={tool_name}
  ↓
（ツール実行）
  ↓
AfterToolCallEvent 発火
  → _handle_after_tool_call()
  → INFOログ: tool_name={tool_name}
  ↓
次のReActイテレーションへ継続
  ↓
_iteration_count >= max_iterations(10) の場合
  → WARNINGログ: "[LoopControlHook] Loop limit reached: iteration_count={count}, max_iterations={max}, agent_name={agent_name}"
  → raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self.max_iterations, agent_name=agent_name)
  → Strands Agents SDKがエラーをキャッチしEventLoopExceptionとして伝播
  → 呼び出し元（エージェントツール関数またはmain.py）でキャッチ
  → ErrorHandler.handle_loop_limit_error(e) を呼び出す
  → "処理が複雑すぎるため終了します。" をユーザーへ表示
  ↓
エージェント呼び出し完了（正常 or 異常）
  ↓
AfterInvocationEvent 発火
  → _handle_after_invocation()
  → INFOログ: total_iterations={count} in agent '{agent_name}'
  （カウンタリセットは行わない）
```

#### カウントアップ対象・非対象

- **カウントアップ対象**: AfterModelCallEvent（LLMが正常にレスポンスを返した後、かつ `event.exception` が存在しない場合）
- **カウントアップ非対象**:
  - LLMコール自体が失敗した場合（Amazon Bedrock接続エラー等）: `event.exception` が存在するためスキップ
  - Strands Agents SDKのリトライ中（リトライはSDK内部で処理されAfterModelCallEventに到達しない）

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| LoopLimitError（ループ上限） | `_iteration_count >= max_iterations` 到達時（かつ `event.exception` なし） | `LoopLimitError` 送出 → 呼び出し元でErrorHandler.handle_loop_limit_error()に委譲 | `"処理が複雑すぎるため終了します。"` |

### 4.2 LoopLimitError クラス仕様

`handlers/exceptions.py` に定義するカスタム例外クラス。

**フィールド**:
- `current_iteration` (`int`): 上限到達時のイテレーション回数
- `max_iterations` (`int`): 設定された最大イテレーション数
- `agent_name` (`str`): 上限に到達したエージェントの名前

**定義**:
```python
class LoopLimitError(Exception):
    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"Loop limit reached: {current_iteration}/{max_iterations} iterations in agent '{agent_name}'"
        )
```

**送出方法**:
```python
raise LoopLimitError(
    current_iteration=self._iteration_count,
    max_iterations=self.max_iterations,
    agent_name=agent_name
)
```

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | BeforeInvocationEvent受信時（カウンタリセット） | `"[LoopControlHook] BeforeInvocationEvent: counter reset to 0"` |
| INFO | BeforeModelCallEvent受信時（ループ回数） | `"[LoopControlHook] BeforeModelCallEvent: current_iteration={count} in agent '{agent_name}'"` |
| INFO | AfterInvocationEvent受信時（合計ループ回数） | `"[LoopControlHook] AfterInvocationEvent: total_iterations={count} in agent '{agent_name}'"` |
| INFO | BeforeToolCallEvent受信時（ツール名） | `"[LoopControlHook] BeforeToolCallEvent: tool_name={tool_name}"` |
| INFO | AfterToolCallEvent受信時（ツール名） | `"[LoopControlHook] AfterToolCallEvent: tool_name={tool_name}"` |
| WARNING | ループ上限到達時（LoopLimitError送出前） | `"[LoopControlHook] Loop limit reached: iteration_count={count}, max_iterations={max}, agent_name={agent_name}"` |

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
from handlers.hooks import LoopControlHook, HumanApprovalHook
from strands import Agent

# AG-001（オーケストレーター）
orchestrator_agent = Agent(
    agent_id="orchestrator_agent",
    name="申請受付窓口エージェント",
    model=get_model(),
    system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
    tools=[travel_application_agent_tool, expense_application_agent_tool],
    hooks=[LoopControlHook(max_iterations=10)],
    session_manager=session_manager,
)

# AG-002（交通費精算申請エージェント）
travel_agent = Agent(
    agent_id="travel_agent",
    name="交通費精算申請エージェント",
    model=get_model(),
    system_prompt=system_prompt,
    tools=[calculate_travel_expense, generate_travel_expense_form],
    hooks=[HumanApprovalHook(), LoopControlHook(max_iterations=10)],
    session_manager=session_manager,
    callback_handler=None,
)
```

### 6.2 呼び出し元でのエラーキャッチ

```python
from handlers.exceptions import LoopLimitError

# main.py またはエージェントツール関数での例外ハンドリング
error_handler = ErrorHandler()
try:
    response = agent(user_input, invocation_state=invocation_state)
except LoopLimitError as e:
    message = error_handler.handle_loop_limit_error(e, context={"session_id": session_id})
    print(message)
except Exception as e:
    message = error_handler.handle_unexpected_error(e, context={"session_id": session_id})
    print(message)
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **カウンタはインスタンス変数で管理**
   - `_iteration_count` はインスタンス変数として管理し、エージェント間でカウンタが共有されない
   - AG-001/AG-002/AG-003それぞれに独立したLoopControlHookインスタンスを生成する

2. **BeforeInvocationEventのみでリセット**
   - カウンタリセットはBeforeInvocationEventのみで行う
   - AfterInvocationEventでは合計ループ回数のログ出力のみを行い、カウンタリセットは行わない
   - これにより、AfterInvocationEvent時点でのカウンタ値が合計ループ回数として記録される

3. **AfterModelCallEventのevent.exceptionチェック**
   - `event.exception` が存在する場合（LLMコール失敗時等）はカウントアップをスキップする
   - エラー発生時のイテレーションを誤ってカウントしないための安全策

4. **agent_nameの取得**
   - AfterModelCallEvent・BeforeModelCallEvent・AfterInvocationEventにおいて、イベントオブジェクトに `agent_name` 属性があればそれを使用する
   - 属性が存在しない場合は `"unknown"` を使用する

5. **LoopLimitErrorの送出**
   - `raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self.max_iterations, agent_name=agent_name)` のように3フィールドをすべてキーワード引数として渡す
   - LoopControlHook自身はユーザー向けメッセージを表示しない。LoopLimitErrorを送出し、呼び出し元（main.pyまたはエージェントツール関数）でErrorHandler.handle_loop_limit_error()を呼び出す

---

### 7.2 パフォーマンス考慮事項

1. **軽量な実装**
   - LoopControlHookはループカウンタのインクリメントと比較のみを行い、重い処理は行わない
   - ReActループのスループットへの影響を最小化する

---

### 7.3 セキュリティ考慮事項

1. **LLM暴走防止**
   - max_iterations=10 でループを強制停止し、LLMによる意図しない多量API呼び出しを防止する

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: フックフレームワーク
  - `HookProvider`: フックプロバイダーインターフェース
  - `HookRegistry`: フックレジストリ
  - `BeforeInvocationEvent`: エージェント呼び出し開始イベント
  - `BeforeModelCallEvent`: LLM呼び出し前イベント
  - `AfterModelCallEvent`: LLM呼び出し後イベント
  - `AfterInvocationEvent`: エージェント呼び出し完了後イベント
  - `BeforeToolCallEvent`: ツール呼び出し前イベント
  - `AfterToolCallEvent`: ツール呼び出し後イベント
- `logging`: Python標準ロギング

### 8.2 内部モジュール
- `handlers/hooks.py`: 本クラスの実装ファイル（HumanApprovalHookと同ファイル）
- `handlers/exceptions.py`: `LoopLimitError` カスタム例外クラスの定義ファイル
- `handlers/error_handler.py`: ErrorHandlerクラス（呼び出し元でhandle_loop_limit_error()を使用）

---

## 9. テスト観点

### 9.1 機能テスト
- BeforeInvocationEvent発火時にループカウンタが0にリセットされること
  - **入力**: BeforeInvocationEvent
  - **期待結果**: `_iteration_count == 0`
- AfterModelCallEvent発火ごとにループカウンタがインクリメントされること（`event.exception` なしの場合）
  - **入力**: AfterModelCallEvent（n回発火、`event.exception` なし）
  - **期待結果**: `_iteration_count == n`
- AfterModelCallEvent発火時に `event.exception` が存在する場合、カウンタがインクリメントされないこと
  - **入力**: AfterModelCallEvent（`event.exception` あり）
  - **期待結果**: `_iteration_count` は変化しない
- AfterInvocationEvent発火時にカウンタがリセットされないこと
  - **入力**: AfterModelCallEventを5回発火後、AfterInvocationEvent発火
  - **期待結果**: `_iteration_count == 5`（リセットされず維持）
- BeforeModelCallEvent発火時にINFOレベルのログが出力されること
  - **入力**: BeforeModelCallEvent
  - **期待結果**: `"[LoopControlHook] BeforeModelCallEvent: current_iteration={count} in agent '{agent_name}'"` がINFOレベルで記録される
- BeforeToolCallEvent発火時にINFOレベルのログが出力されること
  - **入力**: BeforeToolCallEvent（ツール名あり）
  - **期待結果**: `"[LoopControlHook] BeforeToolCallEvent: tool_name={tool_name}"` がINFOレベルで記録される
- AfterToolCallEvent発火時にINFOレベルのログが出力されること
  - **入力**: AfterToolCallEvent（ツール名あり）
  - **期待結果**: `"[LoopControlHook] AfterToolCallEvent: tool_name={tool_name}"` がINFOレベルで記録される
- AfterInvocationEvent発火時に合計ループ回数がINFOレベルでログ出力されること
  - **入力**: AfterModelCallEventをn回発火後、AfterInvocationEvent発火
  - **期待結果**: `"[LoopControlHook] AfterInvocationEvent: total_iterations={n} in agent '{agent_name}'"` がINFOレベルで記録される

### 9.2 異常系テスト
- AfterModelCallEventが10回発火した時点で `LoopLimitError` が送出されること
  - **入力**: AfterModelCallEventを10回発火（max_iterations=10、各回 `event.exception` なし）
  - **期待結果**: `LoopLimitError(current_iteration=10, max_iterations=10, agent_name=...)` が送出される
- `LoopLimitError` 送出時にWARNINGレベルのログが記録されること
  - **入力**: AfterModelCallEventを10回発火
  - **期待結果**: `"[LoopControlHook] Loop limit reached: iteration_count=10, max_iterations=10, agent_name={agent_name}"` がWARNINGレベルで記録される
- 9回目のAfterModelCallEvent発火後は `LoopLimitError` が送出されないこと（境界値）
  - **入力**: AfterModelCallEventを9回発火（max_iterations=10）
  - **期待結果**: `LoopLimitError` 未送出、`_iteration_count == 9`
- `LoopLimitError` の全フィールドが正しく設定されること
  - **入力**: AfterModelCallEventを10回発火（agent_name="test_agent"）
  - **期待結果**: `e.current_iteration == 10`、`e.max_iterations == 10`、`e.agent_name == "test_agent"`

### 9.3 性能テスト
- LoopControlHookのカウントアップ処理が1ms以内に完了すること
  - **測定指標**: AfterModelCallEventハンドラーの処理時間
  - **期待値**: 1ms以内

### 9.4 境界値テスト
- `max_iterations=1` でAfterModelCallEventが1回発火した時点で `LoopLimitError` が送出されること
  - **境界値**: max_iterations=1
  - **期待結果**: 1回目のAfterModelCallEventで `LoopLimitError` 送出
- AfterInvocationEvent後にBeforeInvocationEventが発火した場合、カウンタが0にリセットされること（セッション再開時）
  - **境界値**: AfterInvocationEvent → BeforeInvocationEventの順で発火
  - **期待結果**: BeforeInvocationEvent後 `_iteration_count == 0`
- `event.exception` ありのAfterModelCallEventが10回発火してもLoopLimitErrorが送出されないこと
  - **境界値**: `event.exception` ありで10回発火
  - **期待結果**: `LoopLimitError` 未送出、`_iteration_count == 0`

### 9.5 統合テスト
- AG-001でループ上限到達時に `"処理が複雑すぎるため終了します。"` がユーザーへ表示されること
  - **テスト対象**: AG-001 → LoopControlHook（LoopLimitError） → main.py → ErrorHandler
  - **期待結果**: ユーザーへのループ制限通知メッセージが表示される
- AG-002でループ上限到達時に `"処理が複雑すぎるため終了します。"` がAG-001経由でユーザーへ表示されること
  - **テスト対象**: AG-002 → LoopControlHook（LoopLimitError） → travel_application_agent_tool → ErrorHandler → AG-001
  - **期待結果**: エラーメッセージがCLIに表示される

---

## 10. 設定値

### 10.1 ループ制御設定
- デフォルト最大イテレーション数: `max_iterations = 10`
- AG-001: `LoopControlHook(max_iterations=10)`
- AG-002: `LoopControlHook(max_iterations=10)`
- AG-003: `LoopControlHook(max_iterations=10)`

### 10.2 登録イベント（全6イベント）
1. `BeforeInvocationEvent`: カウンタリセット
2. `BeforeModelCallEvent`: ループ回数をINFOログ
3. `AfterModelCallEvent`: カウントアップ・上限監視（`event.exception` 存在時はスキップ）
4. `AfterInvocationEvent`: 合計ループ回数をINFOログ（リセットしない）
5. `BeforeToolCallEvent`: ツール名をINFOログ
6. `AfterToolCallEvent`: ツール名をINFOログ

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 2.0 | 新フォーマットで作成 |
| 2026-04-28 | 3.0 | LoopLimitErrorカスタム例外への移行・AfterModelCallEventのexceptionスキップ追加・BeforeModelCallEvent/BeforeToolCallEvent/AfterToolCallEventハンドラー新規追加・AfterInvocationEventをログ出力のみに変更（リセット廃止）・依存関係にhandlers/exceptions.py追加・テスト観点・ログ仕様を新仕様に合わせて全面更新 |
