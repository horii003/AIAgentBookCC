# LoopControlHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 4章（LoopControlHookの位置づけ・処理概要）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 5章（マルチエージェント連携時の扱い）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 7章（詳細設計への引き渡し事項）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御の方針・ループ制限到達時の処理）
> - artifacts/03_system-design/outputs/共通設定方針.md（フック登録設定値）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント（AG-001/AG-002/AG-003）のReActループのイテレーション回数を監視し、最大30回で強制停止する。LLMの暴走・同一アクション繰り返し・想定外の無限ループを防止する（実行制御方針.md 10.1節）。ループ上限到達時は `raise LoopLimitError` でエラーを発生させ、呼び出し元エージェントがエラーをキャッチしてユーザーへメッセージを提示する。

### 1.2 主要な責務

- **ループカウンタ管理**: BeforeInvocationEventでカウンタを0にリセットし、AfterModelCallEventでインクリメントする（`event.exception` が存在する場合はスキップ）
- **ループ回数ログ出力**: BeforeModelCallEventでループ回数をINFOレベルでログ出力する
- **ツール呼び出しログ出力**: BeforeToolCallEvent・AfterToolCallEventでツール名をINFOレベルでログ出力する
- **上限監視・強制停止**: カウンタが上限に到達した時点で `LoopLimitError` を raise する
- **合計ループ回数ログ出力**: AfterInvocationEventで合計ループ回数をINFOレベルでログ出力する

### 1.3 非責務

- **Amazon Bedrockのリトライ制御**: Strands Agents SDKの組み込みリトライ機構が担当する
- **ユーザー向けエラーメッセージ生成**: 呼び出し元エージェントが ErrorHandler に委譲する
- **セッション状態の直接変更**: Strands Agents SDKが担当する

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | `HD-003` |
| コンポーネント名 | LoopControlHook |
| コンポーネント種別 | ハンドラー（フッククラス） |
| 説明 | ReActループのイテレーション回数を監視・制限する暴走防止フック。全エージェントに登録する |

---

### 2.2 初期化

#### `__init__(self, max_iterations: int = 30, agent_name: str = "")`

ループ上限値とエージェント名を受け取り、インスタンスを初期化する。

**引数**:
- `max_iterations` (int): ループの最大イテレーション回数（デフォルト: `30`）
- `agent_name` (str): エージェント名（ログ出力・LoopLimitErrorのフィールドに使用）

**インスタンス変数**:

| 変数名 | 型 | 説明 |
|--------|-----|------|
| `_max_iterations` | `int` | ループの最大イテレーション回数 |
| `_iteration_count` | `int` | 現在のループカウンタ（初期値: `0`） |
| `_agent_name` | `str` | エージェント名（LoopLimitError・ログ出力に使用） |
| `_logger` | `logging.Logger` | Pythonロガーインスタンス |

---

### 2.3 主要メソッド

#### 2.3.1 register_hooks(self, registry, \*\*kwargs) → None

##### 説明
HookRegistryに5つのイベントハンドラーを登録する。Strands Agents SDKがエージェント初期化時に自動呼び出す。

##### 引数
- `registry` (HookRegistry): Strands Agents SDKが提供するフックレジストリ
- `**kwargs` (Any): SDK提供の追加引数（使用しない）

##### 処理内容
1. `registry.add_callback(BeforeInvocationEvent, self._on_before_invocation)` を登録する
2. `registry.add_callback(BeforeModelCallEvent, self._on_before_model_call)` を登録する
3. `registry.add_callback(AfterModelCallEvent, self._on_after_model_call)` を登録する
4. `registry.add_callback(BeforeToolCallEvent, self._on_before_tool_call)` を登録する
5. `registry.add_callback(AfterToolCallEvent, self._on_after_tool_call)` を登録する
6. `registry.add_callback(AfterInvocationEvent, self._on_after_invocation)` を登録する

---

#### 2.3.2 _on_before_invocation(self, event) → None

##### 説明
エージェント呼び出し開始時に発火するハンドラー。ループカウンタを0にリセットする。

##### 引数
- `event` (BeforeInvocationEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. `self._iteration_count = 0` にリセットする
2. ログを記録する: `INFO "[LoopControlHook] ループカウンタリセット: agent_name={agent_name}"`

---

#### 2.3.3 _on_before_model_call(self, event) → None

##### 説明
LLM呼び出し前に発火するハンドラー。現在のループ回数をINFOレベルでログ出力する。

##### 引数
- `event` (BeforeModelCallEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. ログを記録する: `INFO "[LoopControlHook] ループ回数: count={count}/{max}, agent_name={agent_name}"`

---

#### 2.3.4 _on_after_model_call(self, event) → None

##### 説明
LLM呼び出し完了後に発火するハンドラー。`event.exception` が存在する場合はカウントをスキップする。上限到達時は `LoopLimitError` を raise してループを強制停止する。

##### 引数
- `event` (AfterModelCallEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. `event.exception` が存在する場合はカウント処理をスキップしてreturnする
2. `self._iteration_count += 1` でカウンタをインクリメントする
3. カウンタが `_max_iterations` 未満の場合: returnする
4. カウンタが `_max_iterations` 以上の場合:
   - `WARNING "[LoopControlHook] ループ上限到達: count={count}/{max}, agent_name={agent_name}"`
   - `raise LoopLimitError(current_iteration=self._iteration_count, max_iterations=self._max_iterations, agent_name=self._agent_name)`

---

#### 2.3.5 _on_before_tool_call(self, event) → None

##### 説明
ツール呼び出し前に発火するハンドラー。ツール名をINFOレベルでログ出力する。

##### 引数
- `event` (BeforeToolCallEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. `tool_name = event.tool_use.get("name", "")` でツール名を取得する
2. ログを記録する: `INFO "[LoopControlHook] ツール呼び出し開始: tool_name={tool_name}, agent_name={agent_name}"`

---

#### 2.3.6 _on_after_tool_call(self, event) → None

##### 説明
ツール呼び出し完了後に発火するハンドラー。ツール名をINFOレベルでログ出力する。

##### 引数
- `event` (AfterToolCallEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. `tool_name = event.tool_use.get("name", "")` でツール名を取得する
2. ログを記録する: `INFO "[LoopControlHook] ツール呼び出し完了: tool_name={tool_name}, agent_name={agent_name}"`

---

#### 2.3.7 _on_after_invocation(self, event) → None

##### 説明
エージェント呼び出し完了後に発火するハンドラー。合計ループ回数をINFOレベルでログ出力する。ループカウンタのリセットは行わない。

##### 引数
- `event` (AfterInvocationEvent): Strands Agents SDKが提供するイベントオブジェクト

##### 処理内容
1. ログを記録する: `INFO "[LoopControlHook] 呼び出し完了: total_iterations={count}, agent_name={agent_name}"`

---

## 3. LoopLimitError カスタム例外クラス

### 3.1 定義モジュール

`hooks/loop_control_hook.py` 内で定義する。

```python
class LoopLimitError(Exception):
    """ループ上限到達を表すカスタム例外クラス。"""

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ループ上限に達しました: {current_iteration}/{max_iterations} (agent: {agent_name})"
        )
```

### 3.2 フィールド定義

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| `current_iteration` | `int` | ループ上限到達時の現在のイテレーション数 |
| `max_iterations` | `int` | 設定されたループ上限値 |
| `agent_name` | `str` | ループ上限に達したエージェント名 |

### 3.3 使用例

```python
# LoopControlHook 内での raise
raise LoopLimitError(
    current_iteration=self._iteration_count,
    max_iterations=self._max_iterations,
    agent_name=self._agent_name,
)

# 呼び出し元エージェントでのキャッチ（例: AG-001）
except LoopLimitError as e:
    logger.warning(
        "[AG-001] ループ上限到達: %s/%s",
        e.current_iteration, e.max_iterations,
        extra={"session_id": session_id},
    )
    message = error_handler.handle_loop_limit_error(e)
    print(message)
    continue
```

### 3.4 インポートパス

他モジュールからのインポートは以下のパスを使用する:

```python
from hooks.loop_control_hook import LoopLimitError
```

---

## 4. ビジネスロジック

### 4.1 ループカウントの仕組み

#### 処理フロー

```
エージェント呼び出し開始
  ↓
BeforeInvocationEvent発火
  → _iteration_count = 0 にリセット
  → INFO ログ: ループカウンタリセット
  ↓
[ReActループ開始]
  ↓
LLM呼び出し前
  ↓
BeforeModelCallEvent発火
  → INFO ログ: 現在のループ回数（count/max）
  ↓
LLMが思考・ツール選択を実行
  ↓
AfterModelCallEvent発火
  → event.exception が存在する場合: スキップ（カウントしない）
  → event.exception がない場合: _iteration_count += 1
    → _iteration_count < max_iterations: ループ継続
    → _iteration_count >= max_iterations:
        WARNING ログ: ループ上限到達
        raise LoopLimitError(current_iteration, max_iterations, agent_name)
  ↓
ツール実行（LoopLimitErrorが発生しなかった場合）
  ↓
BeforeToolCallEvent発火
  → INFO ログ: ツール呼び出し開始（tool_name）
  ↓
（ツール実行）
  ↓
AfterToolCallEvent発火
  → INFO ログ: ツール呼び出し完了（tool_name）
  ↓
[追加区間がある場合 → LLM呼び出しへ戻る]
  ↓
[全区間処理完了またはループ停止]
  ↓
AfterInvocationEvent発火
  → INFO ログ: 合計ループ回数（total_iterations）
  ↓
エージェント呼び出し完了
```

### 4.2 LoopLimitErrorの伝播

`LoopLimitError` は `hooks/loop_control_hook.py` で定義するカスタム例外クラス。LoopControlHookが raise すると、呼び出し元エージェントの対話ループ内で直接キャッチされる。

```python
# 呼び出し元エージェントでのキャッチパターン（AG-001/AG-002/AG-003 共通）
from hooks.loop_control_hook import LoopLimitError

except LoopLimitError as e:
    logger.warning(
        "[AG-XXX] ループ上限到達: %s/%s, agent_name=%s",
        e.current_iteration, e.max_iterations, e.agent_name,
        extra={"session_id": session_id},
    )
    message = error_handler.handle_loop_limit_error(e)
    print(message)
    continue  # AG-001: ループ継続 / AG-002/AG-003: str を return
```

### 4.3 カウントアップ対象の定義

**カウントアップする**（AfterModelCallEventが発火し `event.exception` がない）ケース:
- LLMが思考・ツール選択のレスポンスを正常に返した後

**カウントアップしない**ケース:
- `event.exception` が存在する場合（LLMコール自体が失敗した場合等）
- Strands Agents SDKの組み込みリトライ中: リトライはAfterModelCallEvent発火前に処理されるためカウントアップされない

---

## 5. エラーハンドリング

| エラー種別 | 条件 | 対応 | 備考 |
|-----------|------|------|------|
| LoopLimitError raise失敗 | LoopLimitErrorの送出自体に失敗した場合 | ログ出力後にraise（再送出） | フレームワーク異常として扱う |
| BeforeInvocationEvent処理失敗 | カウンタリセット中に例外が発生した場合 | ログ出力して処理継続（カウンタは0を維持） | リセット失敗でループを中断しない |

---

## 6. ログ出力

| レベル | イベント | メッセージ |
|--------|---------|-----------|
| INFO | BeforeInvocationEvent（カウンタリセット） | `"[LoopControlHook] ループカウンタリセット: agent_name={agent_name}"` |
| INFO | BeforeModelCallEvent（ループ回数） | `"[LoopControlHook] ループ回数: count={count}/{max}, agent_name={agent_name}"` |
| INFO | BeforeToolCallEvent（ツール呼び出し開始） | `"[LoopControlHook] ツール呼び出し開始: tool_name={tool_name}, agent_name={agent_name}"` |
| INFO | AfterToolCallEvent（ツール呼び出し完了） | `"[LoopControlHook] ツール呼び出し完了: tool_name={tool_name}, agent_name={agent_name}"` |
| WARNING | AfterModelCallEvent（ループ上限到達） | `"[LoopControlHook] ループ上限到達: count={count}/{max}, agent_name={agent_name}"` |
| INFO | AfterInvocationEvent（合計ループ回数） | `"[LoopControlHook] 呼び出し完了: total_iterations={count}, agent_name={agent_name}"` |

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **インスタンスは各エージェントに独立して割り当てる**
   - AG-001・AG-002・AG-003それぞれにLoopControlHookの独立したインスタンスを割り当てる
   - `_iteration_count` はインスタンス変数であるため、エージェント間でカウンタが共有されることはない
   - シングルスレッド処理のため、同一インスタンスへの同時アクセスは発生しない

2. **AfterModelCallEventの発火タイミングとevent.exception**
   - AfterModelCallEventはLLMが正常レスポンスを返した後に発火する
   - `event.exception` が存在する場合はカウントをスキップする（LLMコール失敗時の誤カウントを防止する）

3. **AfterInvocationEventではカウンタリセットを行わない**
   - `AfterInvocationEvent` のハンドラーでは「合計ループ回数のINFOログ出力」のみ行う
   - ループカウンタのリセットは `BeforeInvocationEvent` のみで行う

4. **LoopLimitErrorのフィールド**
   - `raise LoopLimitError(...)` では `current_iteration`・`max_iterations`・`agent_name` の3フィールドすべてを引数として渡すこと

5. **テンプレートファイルのパスと出力ディレクトリ**
   - テンプレートファイルのパスは `data/templates/` を使用する
   - 出力ディレクトリは `data/output/{session_id}/` を使用する

---

### 7.2 パフォーマンス考慮事項

1. **軽量な実装の維持**
   - LoopControlHookはカウンタのインクリメントと比較のみを行う軽量な処理とする
   - 各イベントハンドラーの処理時間は1ms以下を目標とする

---

### 7.3 セキュリティ考慮事項

1. **ループ上限の不変性**
   - `_max_iterations` は `__init__` で設定後、変更できないようにする（必要に応じてsetterを設けない）
   - 実行中の `max_iterations` 変更を防止し、一貫した上限制御を保証する

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `strands.hooks`:
  - `HookProvider`: フックプロバイダー基底クラス
  - `HookRegistry`: フックレジストリ
  - `BeforeInvocationEvent`: エージェント呼び出し開始イベント
  - `BeforeModelCallEvent`: LLM呼び出し前イベント
  - `AfterModelCallEvent`: LLM呼び出し完了後イベント
  - `BeforeToolCallEvent`: ツール呼び出し前イベント
  - `AfterToolCallEvent`: ツール呼び出し完了後イベント
  - `AfterInvocationEvent`: エージェント呼び出し完了後イベント
- `logging`: Pythonの標準ロギングモジュール

### 8.2 内部モジュール
- `hooks/loop_control_hook.py`:
  - `LoopLimitError`: ループ上限到達を表すカスタム例外クラス（同ファイル内で定義）

---

## 9. テスト観点

### 9.1 機能テスト
- BeforeInvocationEvent発火時にループカウンタが0にリセットされること
- BeforeModelCallEvent発火時に現在のループ回数がINFOレベルでログ出力されること
- AfterModelCallEvent発火ごとにループカウンタが1ずつインクリメントされること（`event.exception` がない場合）
- BeforeToolCallEvent発火時にツール名がINFOレベルでログ出力されること
- AfterToolCallEvent発火時にツール名がINFOレベルでログ出力されること
- AfterInvocationEvent発火時に合計ループ回数がINFOレベルでログ出力されること（カウンタリセットは行わないこと）
- カウンタが30（max_iterations）に達した時点で `LoopLimitError` が raise されること
- 29回目のAfterModelCallEventでは `LoopLimitError` が raise されないこと（上限未到達）
- `raise LoopLimitError(...)` に `current_iteration`・`max_iterations`・`agent_name` の3フィールドが渡されること

### 9.2 異常系テスト
- `event.exception` が存在するAfterModelCallEventでカウンタがインクリメントされないこと
- LLMコール失敗時（event.exceptionあり）にカウンタがインクリメントされないこと
- AfterInvocationEvent発火後にカウンタがリセットされないこと（BeforeInvocationEventでのみリセット）

### 9.3 性能テスト
- 各イベントハンドラーの処理時間が1ms以下であること

### 9.4 境界値テスト
- `max_iterations=1` でAfterModelCallEventが1回発火した時点で `LoopLimitError` が raise されること
- `max_iterations=30` でAfterModelCallEventが30回発火した時点で `LoopLimitError` が raise されること

### 9.5 統合テスト
- AG-001でLoopControlHookが登録された状態で30回ループするシナリオで `LoopLimitError` が raise されること
- AG-002でLoopControlHookが登録された状態で、AG-002インスタンスと独立したカウンタが機能すること（AG-001のループカウントに影響されない）
- 呼び出し元エージェントが `LoopLimitError` をキャッチして ErrorHandler に委譲し、ユーザー向けメッセージが生成されること

---

## 10. 設定値

### 10.1 ループ制御設定

| 設定項目 | 設定値 | 適用エージェント |
|---------|--------|----------------|
| max_iterations | `30` | AG-001, AG-002, AG-003（全エージェント共通） |

### 10.2 テンプレート・出力パス

| 項目 | パス |
|------|------|
| テンプレートファイル | `data/templates/` |
| 出力ディレクトリ | `data/output/{session_id}/` |

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 1.0 | 新フォーマットで作成 |
| 2026-04-28 | 1.1 | 修正#6：LoopLimitErrorをカスタム例外クラスとして定義・定義モジュール明示、BeforeModelCallEvent/BeforeToolCallEvent/AfterToolCallEventのINFOログ追加、AfterInvocationEventをリセットなし・ログのみに変更、AfterModelCallEventのevent.exception存在時スキップ追加、max_iterations=30に変更、ループ上限到達時raise LoopLimitError対応、LoopLimitErrorの3フィールド定義 |
