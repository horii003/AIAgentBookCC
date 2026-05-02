---
version: "1.1.0"
last_updated: "2026-05-02"
updated_by: ""
---

# LoopControlHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 3章（LoopControlHookの目的・役割定義・設計定義）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 5章（ハンドラー間の連携設計）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御の方針・LoopControlHook登録イベント・max_iterations設定）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント（AG-001/AG-002/AG-003）の ReActループの反復回数を監視・制御し、最大10回を超えた場合に LoopLimitError を発生させて EX-08 として処理する。

### 1.2 主要な責務

1. **ループカウンタ管理**: `BeforeInvocationEvent` でリセット、`AfterModelCallEvent` でインクリメントする（例外発生時はスキップ）
2. **上限チェック**: カウンタが `max_iterations`（10回）に達した場合に `LoopLimitError` を raise する
3. **ログ出力**: 各イベント発火時にOPE-004としてログを記録する（LOG-STD）

### 1.3 非責務

- **対話回数（ターン数）の制限**: GRD-005（30回）はシステムプロンプト側の指示で制御する。LoopControlHook は ReActループのみを対象とする
- **セッション状態の更新**: ErrorHandler 経由で SessionManager（SM-001）が担当する

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`LoopControlHook`

#### 説明
全エージェントに適用し、ReActループの反復回数を監視・制御するフッククラス。`BeforeInvocationEvent` でカウンタをリセットし、`AfterModelCallEvent` でインクリメントして max_iterations 到達時に `LoopLimitError` を raise する。また `BeforeModelCallEvent` / `BeforeToolCallEvent` / `AfterToolCallEvent` / `AfterInvocationEvent` でログのみ出力する。

---

### 2.2 初期化

#### `__init__(self, max_iterations: int = 10)`
LoopControlHook を初期化する。

**引数**:
- `max_iterations` (int): ReActループの最大許容回数（デフォルト: 10）

**インスタンス変数**:
- `max_iterations`: int — 最大ループ回数（デフォルト 10）
- `_iteration_count`: int — 現在のループカウンタ（初期値 0）

---

### 2.3 主要メソッド

#### 2.3.1 `on_before_invocation`

##### 説明
エージェント呼び出し開始時にループカウンタを 0 にリセットする。

##### 引数
- `event` (BeforeInvocationEvent): エージェント呼び出し開始イベント

##### 戻り値
- `None`

##### 処理内容
1. `self._iteration_count = 0` にリセットする

---

#### 2.3.2 `on_before_model_call`

##### 説明
LLM 推論開始直前に発火する。ログのみ出力する。

##### 引数
- `event` (BeforeModelCallEvent): LLM呼び出し開始イベント

##### 戻り値
- `None`

##### 処理内容
1. OPE-004 ログを出力する（モデル呼び出し開始）

---

#### 2.3.3 `on_after_model_call`

##### 説明
LLM 推論（モデル呼び出し）完了後にループカウンタをインクリメントし、上限に達した場合は `LoopLimitError` を raise する。ただし `event.exception` が存在する場合はカウントをスキップする。OPE-004 ログを出力する。

##### 引数
- `event` (AfterModelCallEvent): LLM呼び出し完了イベント

##### 戻り値
- `None`

##### 処理内容
1. `event.exception` が存在する場合はカウントをスキップして返す（エラー発生時はループ進行とみなさない）
2. `self._iteration_count += 1` でカウンタをインクリメントする
3. OPE-004 ログを出力する（ループ回数をインクリメント後の値で記録）
4. `self._iteration_count >= self.max_iterations` の場合:
   - WARNING レベルで上限到達ログを出力する
   - `raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self.max_iterations, agent_name=event.agent.name)`

##### 例外
- `LoopLimitError`: `_iteration_count >= max_iterations` のとき raise する

---

#### 2.3.4 `on_before_tool_call`

##### 説明
ツール呼び出し直前に発火する。ログのみ出力する。

##### 引数
- `event` (BeforeToolCallEvent): ツール呼び出し直前イベント

##### 戻り値
- `None`

##### 処理内容
1. OPE-004 ログを出力する（ツール呼び出し開始）

---

#### 2.3.5 `on_after_tool_call`

##### 説明
ツール呼び出し完了後に発火する。ログのみ出力する。

##### 引数
- `event` (AfterToolCallEvent): ツール呼び出し完了イベント

##### 戻り値
- `None`

##### 処理内容
1. OPE-004 ログを出力する（ツール呼び出し完了）

---

#### 2.3.6 `on_after_invocation`

##### 説明
エージェント呼び出し完了後に発火する。ログのみ出力する。

##### 引数
- `event` (AfterInvocationEvent): エージェント呼び出し完了イベント

##### 戻り値
- `None`

##### 処理内容
1. OPE-004 ログを出力する（エージェント呼び出し完了）

---

### 2.4 フック設計

#### 2.4.1 フック登録

##### `register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None`
フックの登録

**登録するイベント**:
- `BeforeInvocationEvent`: `on_before_invocation`
  - **登録タイミング**: エージェントインスタンス生成時（`hooks=[LoopControlHook(...)]` として渡す）
  - **依存関係**: なし
- `BeforeModelCallEvent`: `on_before_model_call`
  - **登録タイミング**: エージェントインスタンス生成時
  - **依存関係**: なし
- `AfterModelCallEvent`: `on_after_model_call`
  - **登録タイミング**: エージェントインスタンス生成時
  - **依存関係**: なし
- `BeforeToolCallEvent`: `on_before_tool_call`
  - **登録タイミング**: エージェントインスタンス生成時
  - **依存関係**: なし
- `AfterToolCallEvent`: `on_after_tool_call`
  - **登録タイミング**: エージェントインスタンス生成時
  - **依存関係**: なし
- `AfterInvocationEvent`: `on_after_invocation`
  - **登録タイミング**: エージェントインスタンス生成時
  - **依存関係**: なし

**登録順序**: 登録順序は特定の順序を要件としない

---

#### 2.4.2 イベントハンドラー

##### `on_before_invocation`

**説明**: エージェント呼び出し開始時に発火し、ループカウンタを 0 にリセットする。

**処理内容**:
1. `self._iteration_count = 0` にリセットする

**ログ出力**: なし（リセット時のログ出力は不要）

---

##### `on_before_model_call`

**説明**: LLM 推論開始直前に発火し、OPE-004 ログを出力する。

**処理内容**:
1. `logger.info(f"[OPE-004] モデル呼び出し開始: count={self._iteration_count}, max={self.max_iterations}")`

**ログ出力**: `"[OPE-004] モデル呼び出し開始: count={count}, max={max_iterations}"`

---

##### `on_after_model_call`

**説明**: LLM 呼び出し後に発火し、ループカウンタをインクリメントする。`event.exception` が存在する場合はスキップする。max_iterations 到達時は `LoopLimitError` を raise する。

**処理内容**:
1. `if event.exception: return`（エラー発生時はカウントをスキップ）
2. `self._iteration_count += 1`
3. `logger.info(f"[OPE-004] ループカウント: count={self._iteration_count}, max={self.max_iterations}")`
4. `if self._iteration_count >= self.max_iterations:` の場合
   - `logger.warning(f"[OPE-004] ループ上限到達: count={self._iteration_count}, max={self.max_iterations}")`
   - `raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self.max_iterations, agent_name=event.agent.name)`

**ログ出力**:
- 通常時: `"[OPE-004] ループカウント: count={count}, max={max_iterations}"`
- 上限到達時: `"[OPE-004] ループ上限到達: count={count}, max={max_iterations}"` （WARNING レベル）

---

##### `on_before_tool_call`

**説明**: ツール呼び出し直前に発火し、OPE-004 ログを出力する。

**処理内容**:
1. `logger.info(f"[OPE-004] ツール呼び出し開始: tool={event.tool_name}, count={self._iteration_count}")`

**ログ出力**: `"[OPE-004] ツール呼び出し開始: tool={tool_name}, count={count}"`

---

##### `on_after_tool_call`

**説明**: ツール呼び出し完了後に発火し、OPE-004 ログを出力する。

**処理内容**:
1. `logger.info(f"[OPE-004] ツール呼び出し完了: tool={event.tool_name}, count={self._iteration_count}")`

**ログ出力**: `"[OPE-004] ツール呼び出し完了: tool={tool_name}, count={count}"`

---

##### `on_after_invocation`

**説明**: エージェント呼び出し完了後に発火し、OPE-004 ログを出力する。

**処理内容**:
1. `logger.info(f"[OPE-004] エージェント呼び出し完了: final_count={self._iteration_count}, max={self.max_iterations}")`

**ログ出力**: `"[OPE-004] エージェント呼び出し完了: final_count={count}, max={max_iterations}"`

---

## 3. ビジネスロジック

### 3.1 ループカウント制御フロー

#### 処理フロー

```
開始: AG-001/AG-002/AG-003 のエージェント呼び出し
  ↓
【BeforeInvocationEvent 発火】on_before_invocation
  - _iteration_count = 0 にリセット
  ↓
【ReActループ開始】
  ↓
【BeforeModelCallEvent 発火】on_before_model_call
  - OPE-004 ログ出力（モデル呼び出し開始）
  ↓
LLM 推論実行（1回目）
  ↓
【AfterModelCallEvent 発火】on_after_model_call
  - event.exception が存在する場合 → スキップ（return）
  - _iteration_count += 1  → count = 1
  - OPE-004 ログ出力（INFO）
  - count(1) >= max_iterations(10) ? NO → 続行
  ↓
【BeforeToolCallEvent 発火】on_before_tool_call
  - OPE-004 ログ出力（ツール呼び出し開始）
  ↓
ツール呼び出し（あれば）
  ↓
【AfterToolCallEvent 発火】on_after_tool_call
  - OPE-004 ログ出力（ツール呼び出し完了）
  ↓
【BeforeModelCallEvent 発火】on_before_model_call
  - OPE-004 ログ出力（モデル呼び出し開始）
  ↓
LLM 推論実行（2回目〜）
  ↓
【AfterModelCallEvent 発火】on_after_model_call
  - _iteration_count += 1  → count = N
  - OPE-004 ログ出力
  - count(N) >= max_iterations(10) ? NO → 続行（count < 10 の間）
  ↓
...（ReActループ繰り返し）
  ↓
LLM 推論実行（10回目）
  ↓
【AfterModelCallEvent 発火】on_after_model_call
  - _iteration_count += 1  → count = 10
  - OPE-004 ログ出力（INFO）
  - count(10) >= max_iterations(10) ? YES
    → WARNING ログ出力
    → raise LoopLimitError(current_iteration=10, max_iterations=10, agent_name=...)
  ↓
LoopLimitError がエージェントのループ例外として伝播
  ↓
各エージェントが catch して ErrorHandler.handle_loop_limit_error(e) へ委譲
  ↓
ErrorHandler が EX-08 として分類 → CF-006 誘導メッセージを返す
  ↓
【AfterInvocationEvent 発火】on_after_invocation
  - OPE-004 ログ出力（エージェント呼び出し完了）
  ↓
終了（エスカレーション）
```

#### 処理の詳細
- LoopLimitError 発生時、ErrorHandler が EX-08（想定外）として分類し、CF-006 誘導メッセージを社員に提示する
- エージェントが AG-001 から委譲された AG-002/AG-003 の場合、それぞれ独立してカウントを管理する
- `event.exception` が存在する場合のカウントスキップにより、LLM エラー時の誤カウントを防止する

#### 分岐条件の詳細
- **event.exception 存在**: カウントスキップ（AfterModelCallEvent）
- **count < max_iterations**: ループ継続
- **count >= max_iterations**: `LoopLimitError` を raise（WARNING ログ出力後）

---

### 3.2 LoopLimitError 発生後の連携フロー

#### 処理フロー

```
LoopLimitError raise
  ↓
エージェントが例外を catch
  ↓
error_handler.handle_loop_limit_error(LoopLimitError) 呼び出し
  ↓
ErrorHandler が EX-08 対応メッセージを生成
  - "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
  ↓
エージェントが社員向けメッセージを返す
  ↓
SessionManager がセッション状態を TERMINATED に更新
```

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| エラー種別 | 発生条件 | 対応 | メッセージ |
|-----------|---------|------|-----------|
| LoopLimitError（EX-08） | `_iteration_count >= max_iterations` | `raise LoopLimitError` → エージェントが catch して ErrorHandler.handle_loop_limit_error(e) に委譲 | "申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。" |

---

## 5. ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | BeforeModelCallEvent 発火時（毎回） | `"[OPE-004] モデル呼び出し開始: count={count}, max={max_iterations}"` |
| INFO | AfterModelCallEvent 発火時（毎回、exception なし） | `"[OPE-004] ループカウント: count={count}, max={max_iterations}"` |
| WARNING | AfterModelCallEvent 発火時（上限到達） | `"[OPE-004] ループ上限到達: count={count}, max={max_iterations}"` |
| INFO | BeforeToolCallEvent 発火時（毎回） | `"[OPE-004] ツール呼び出し開始: tool={tool_name}, count={count}"` |
| INFO | AfterToolCallEvent 発火時（毎回） | `"[OPE-004] ツール呼び出し完了: tool={tool_name}, count={count}"` |
| INFO | AfterInvocationEvent 発火時（毎回） | `"[OPE-004] エージェント呼び出し完了: final_count={count}, max={max_iterations}"` |

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
from handlers.loop_control_hook import LoopControlHook
from strands import Agent
from strands.models import BedrockModel

# エージェント初期化時に hooks パラメータで登録する
agent = Agent(
    model=BedrockModel(model_id="jp.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    system_prompt="...",
    tools=[...],
    hooks=[LoopControlHook(max_iterations=10)],
)

# エージェント呼び出し（BeforeInvocationEvent でカウンタリセット）
response = agent("申請します")
# → ReActループ中に AfterModelCallEvent が発火してカウントインクリメント
# → 10回に達すると LoopLimitError が raise される
```

---

### 6.2 LoopLimitError を受けたエラーハンドリング

```python
from handlers.loop_control_hook import LoopControlHook, LoopLimitError
from handlers.error_handler import ErrorHandler

error_handler = ErrorHandler()
agent = Agent(
    model=...,
    hooks=[LoopControlHook(max_iterations=10)],
)

try:
    response = agent(user_input, invocation_state=state)
except LoopLimitError as e:
    # e.current_iteration, e.max_iterations, e.agent_name を参照可能
    message = error_handler.handle_loop_limit_error(e)
    return message
except RuntimeError as e:
    message = error_handler.handle_runtime_error(e)
    return message
except Exception as e:
    message = error_handler.handle_unexpected_error(e)
    return message
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **インスタンス変数のスレッド安全性**
   - `_iteration_count` はインスタンス変数であるため、各エージェントインスタンスが独自の LoopControlHook を持つ設計が前提。複数スレッドで同一エージェントを共有する場合は排他制御を検討する。

2. **AG-002/AG-003 のカウント独立性**
   - AG-001 が AG-002/AG-003 をツールとして呼び出す際も、AG-002/AG-003 は独自の LoopControlHook インスタンスを保持するため、カウントは独立して管理される。

3. **LoopLimitError の定義**
   - `LoopLimitError` は `handlers/loop_control_hook.py` 内に `RuntimeError` のサブクラスとして定義する。`current_iteration`、`max_iterations`、`agent_name` の3フィールドを持つ。ErrorHandler の `handle_loop_limit_error` メソッドで処理される。

4. **event.exception チェック**
   - `AfterModelCallEvent` の `event.exception` 存在チェックにより、LLM 呼び出し中にエラーが発生した場合はループ進行とみなさない。これによりエラーリトライ時の誤カウントを防止する。

---

### 7.2 パフォーマンス考慮事項

1. **ログ出力のオーバーヘッド**
   - 6種類のイベントで INFO ログが出力されるが、LLM 推論時間に比べて無視できるレベルのオーバーヘッドである。

---

### 7.3 セキュリティ考慮事項

1. **max_iterations の設定値保護**
   - `max_iterations` はエージェント初期化時に設定し、実行中に外部から変更されないよう保護すること。

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`: フックフレームワーク
  - `HookProvider`: フックプロバイダー基底クラス
  - `HookRegistry`: フックレジストリ
  - `BeforeInvocationEvent`: エージェント呼び出し開始イベント
  - `BeforeModelCallEvent`: LLM呼び出し開始イベント
  - `AfterModelCallEvent`: LLM呼び出し完了イベント
  - `BeforeToolCallEvent`: ツール呼び出し直前イベント
  - `AfterToolCallEvent`: ツール呼び出し完了イベント
  - `AfterInvocationEvent`: エージェント呼び出し完了イベント
- `logging`: ログ出力（Python標準）

### 8.2 内部モジュール
- `handlers.loop_control_hook`: 本モジュール
  - `LoopLimitError`: LoopControlHook が raise するエラー（RuntimeError のサブクラス）

---

## 9. テスト観点

### 9.1 機能テスト
- 10回以内のループで LoopLimitError が発生しないこと
  - **入力**: max_iterations=10 でエージェントを初期化し、9回の AfterModelCallEvent を発火
  - **期待結果**: LoopLimitError が発生しない
- `BeforeInvocationEvent` でカウンタが 0 にリセットされること
  - **入力**: カウンタが 5 の状態で BeforeInvocationEvent を発火
  - **期待結果**: `_iteration_count == 0`
- OPE-004 ログが AfterModelCallEvent 時に出力されること
  - **入力**: AfterModelCallEvent を1回発火
  - **期待結果**: `[OPE-004]` を含む INFO ログが出力される
- `event.exception` が存在する場合に AfterModelCallEvent でカウントがスキップされること
  - **入力**: `event.exception` が設定された AfterModelCallEvent を発火
  - **期待結果**: `_iteration_count` がインクリメントされない
- 6種類の全イベントでログが出力されること
  - **入力**: BeforeModelCallEvent / BeforeToolCallEvent / AfterToolCallEvent / AfterInvocationEvent を各1回発火
  - **期待結果**: 各イベントに対応する `[OPE-004]` ログが出力される

### 9.2 異常系テスト
- 10回目の AfterModelCallEvent で LoopLimitError が発生すること
  - **入力**: max_iterations=10 で 10回 AfterModelCallEvent を発火
  - **期待結果**: 10回目の発火で `LoopLimitError` が raise される
- LoopLimitError が3フィールドを正しく持つこと
  - **入力**: max_iterations=10 で 10回 AfterModelCallEvent を発火（agent_name="AG-001"）
  - **期待結果**: `e.current_iteration == 10`, `e.max_iterations == 10`, `e.agent_name == "AG-001"`
- LoopLimitError 発生時に WARNING ログが出力されること
  - **入力**: 上限到達時
  - **期待結果**: WARNING レベルの `[OPE-004]` ログが出力される

### 9.3 性能テスト（該当する場合のみ）
- `on_after_model_call` の処理時間が 1ms 以内であること
  - **測定指標**: 処理時間
  - **期待値**: 1ms以内

### 9.4 境界値テスト
- max_iterations=10 のとき、10回目の AfterModelCallEvent で LoopLimitError が発生すること
  - **境界値**: count == max_iterations（10回目）
  - **期待結果**: 10回目で `LoopLimitError` が raise される
- max_iterations=10 のとき、9回目の AfterModelCallEvent では LoopLimitError が発生しないこと
  - **境界値**: count == max_iterations - 1（9回目）
  - **期待結果**: 9回目では例外が発生しない
- `event.exception` が None の場合はカウントがインクリメントされること
  - **境界値**: event.exception == None
  - **期待結果**: `_iteration_count` がインクリメントされる

### 9.5 統合テスト
- AG-001/AG-002/AG-003 それぞれで max_iterations 到達時に LoopLimitError が発生し、ErrorHandler が CF-006 誘導メッセージを返すこと
  - **テスト対象**: LoopControlHook + ErrorHandler + Agent
  - **期待結果**: LoopLimitError → ErrorHandler(EX-08) → CF-006誘導メッセージが返る

---

## 10. 設定値

### 10.1 ループ制御設定
- `max_iterations`: `10`（全エージェント共通）

### 10.2 LoopLimitError クラス定義
- クラス名: `LoopLimitError`
- 基底クラス: `RuntimeError`
- 定義場所: `handlers/loop_control_hook.py`
- フィールド:
  - `current_iteration: int` — 上限到達時の現在のループ回数
  - `max_iterations: int` — 設定された最大ループ回数
  - `agent_name: str` — 上限に達したエージェントの名前

```python
class LoopLimitError(RuntimeError):
    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ループ上限({max_iterations}回)に達しました。"
            f"agent={agent_name}, count={current_iteration}"
        )
```

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-02 | 1.0 | 新フォーマットで初版作成 |
| 2026-05-02 | 1.1 | 修正6: 登録イベントを6種類に拡張（BeforeModelCallEvent/BeforeToolCallEvent/AfterToolCallEvent/AfterInvocationEvent追加）、AfterModelCallEventでevent.exception存在時スキップ追加、LoopLimitErrorに3フィールド追加、上限到達時ログをWARNINGに変更 |
