---
version: "1.1.0"
last_updated: "2026-05-01"
updated_by: ""
---

# LoopControlHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 4章（LoopControlHook 基本設計）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 7章（詳細設計への引き渡し事項）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 9章（制約事項・前提条件）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御方針・上限値の根拠）
> - artifacts/03_system-design/outputs/共通設定方針.md（LoopControlHook 最大回数の共通設定）

## 1. 概要

### 1.1 コンポーネントの目的
全エージェント（AG-001/AG-002/AG-003）の ReActループ回数を監視し、上限（30回）到達時にループを強制停止する。ループ暴走によるシステムコスト（API コール数）の増加とユーザーへの無応答状態を防止する。上限到達時は `LoopLimitError` を発生させ、呼び出し元がエラーとして処理する。

### 1.2 主要な責務
- エージェント呼び出し開始時（`BeforeInvocationEvent`）にループカウンタを 0 にリセットする
- LLM 呼び出し完了後（`AfterModelCallEvent`）にループカウンタをインクリメントし上限到達時に `LoopLimitError` を発生させる
- エラーが発生した LLM 呼び出しはカウントしない（`event.exception` が存在する場合スキップ）
- LLM 呼び出し開始前（`BeforeModelCallEvent`）にループ回数を INFO ログ出力する
- ツール呼び出し開始前（`BeforeToolCallEvent`）にツール名を INFO ログ出力する
- ツール呼び出し完了後（`AfterToolCallEvent`）にツール名を INFO ログ出力する
- エージェント呼び出し完了後（`AfterInvocationEvent`）に合計ループ回数を INFO ログ出力する（リセットは行わない）

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | HD-003 |
| コンポーネント名 | LoopControlHook |
| コンポーネント種別 | ハンドラー（ループ制御フック） |
| 説明 | ReActループ回数を監視し上限到達時にループを強制停止するフック |
| 実装ファイル | `handlers/loop_control_hook.py` |

---

### 2.2 インターフェース設計

#### 2.2.1 コンストラクタ

| 引数名 | 型 | 説明 | デフォルト値 |
|--------|-----|------|--------------|
| max_iterations | int | ループ上限回数 | なし（必須） |
| agent_name | str | エージェント名（LoopLimitError に付与） | なし（必須） |

#### 2.2.2 登録イベントとハンドラー

| イベント名 | ハンドラーメソッド名 | 発火タイミング | 処理概要 |
|-----------|-------------------|--------------|---------|
| BeforeInvocationEvent | `before_invocation` | エージェント呼び出し開始時 | ループカウンタを 0 にリセットし INFO ログ出力する |
| AfterModelCallEvent | `after_model_call` | LLM 呼び出し（1 ReActステップ）完了後 | ループカウンタをインクリメントし上限監視する |
| BeforeModelCallEvent | `before_model_call` | LLM 呼び出し開始前 | ループ回数を INFO ログ出力する |
| BeforeToolCallEvent | `before_tool_call` | ツール呼び出し開始前 | ツール名を INFO ログ出力する |
| AfterToolCallEvent | `after_tool_call` | ツール呼び出し完了後 | ツール名を INFO ログ出力する |
| AfterInvocationEvent | `after_invocation` | エージェント呼び出し完了後 | 合計ループ回数を INFO ログ出力する（リセットは行わない） |

#### 2.2.3 エージェントへの登録

```python
# AG-001 / AG-002 / AG-003 すべてに登録する
Agent(
    ...,
    hooks=[
        LoopControlHook(max_iterations=MAX_LOOP_ITERATIONS, agent_name="AG-001"),
        # AG-002/AG-003 はさらに HumanApprovalHook() を追加
    ],
    ...
)
```

> `MAX_LOOP_ITERATIONS = 30` は `config/model_config.py` で定義し、全エージェントで共通の値を使用する

---

### 2.3 ビジネスロジック

#### 2.3.1 処理フロー

```
BeforeInvocationEvent 発火（エージェント呼び出し開始時）
  ↓
_loop_count を 0 にリセットする
INFO ログ: "エージェント呼び出し開始: ループカウンタをリセット (エージェント={agent_name})"
  ↓
（エージェントの ReAct ループ開始）

  ↓ ← ここから ReAct ループ

BeforeModelCallEvent 発火
  ↓
INFO ログ: "LLM 呼び出し開始 (ループ={_loop_count}, エージェント={agent_name})"
  ↓
LLM が推論を実行（1 ReActステップ）
  ↓
AfterModelCallEvent 発火
  ↓
[event.exception が存在する？]
  - YES → カウントしない（誤カウント防止）→ ループ先頭に戻る
  - NO  → _loop_count をインクリメント
  ↓
[_loop_count >= max_iterations（30）？]
  - NO  → ループ先頭に戻る（次の ReActステップへ）
  - YES → WARNING ログ出力
           raise LoopLimitError(
               current_iteration=self._loop_count,
               max_iterations=self.max_iterations,
               agent_name=self.agent_name,
           )
           （エージェントループが停止し呼び出し元の例外ハンドラに制御が移る）
  ↓
（ツール呼び出し時）
BeforeToolCallEvent 発火
  ↓
INFO ログ: "ツール呼び出し開始 (ツール名={tool_name}, エージェント={agent_name})"
  ↓
ツール実行
  ↓
AfterToolCallEvent 発火
  ↓
INFO ログ: "ツール呼び出し完了 (ツール名={tool_name}, エージェント={agent_name})"
  ↓
（エージェント呼び出し完了時）
AfterInvocationEvent 発火
  ↓
INFO ログ: "エージェント呼び出し完了: 合計ループ回数={_loop_count} (エージェント={agent_name})"
（リセットは行わない）
```

#### 2.3.2 カウントの管理

| タイミング | 操作 | 理由 |
|-----------|------|------|
| `BeforeInvocationEvent` 発火時 | `_loop_count = 0` にリセット | エージェントが再呼び出しされるたびに前回のカウントが持ち越されないようにする |
| `AfterModelCallEvent` 発火時（正常） | `_loop_count += 1` | 1 ReActステップが完了するたびにカウントアップ |
| `AfterModelCallEvent` 発火時（`event.exception` が存在する場合） | カウントしない | API エラー等による失敗ステップは ReAct の有効な1ステップとして扱わない |
| `AfterInvocationEvent` 発火時 | リセットしない（ログ出力のみ） | 合計ループ回数を記録するためにリセットせずに保持する |

---

### 2.4 設定・構成

#### 2.4.1 インスタンス変数

| 変数名 | 型 | 説明 | 初期値 |
|--------|-----|------|--------|
| `max_iterations` | int | ループ上限回数（コンストラクタで設定） | — |
| `agent_name` | str | エージェント名（コンストラクタで設定） | — |
| `_loop_count` | int | 現在のループカウンタ | 0 |

#### 2.4.2 設定値

| 設定項目 | 設定値 | 定義場所 |
|---------|--------|---------|
| `MAX_LOOP_ITERATIONS` | 30 | `config/model_config.py` |
| 全エージェント共通のループ上限 | 30回 | 共通設定方針.md 4.2 |

#### 2.4.3 ログ設定

| 設定項目 | 設定値 |
|---------|--------|
| ロガー名 | `handlers.loop_control_hook` |

---

## 3. 実装詳細

### 3.1 クラス設計

#### 3.1.1 LoopControlHook クラス

```python
import logging
from strands.hooks import (
    BeforeInvocationEvent,
    AfterInvocationEvent,
    AfterModelCallEvent,
    BeforeModelCallEvent,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)

logger = logging.getLogger("handlers.loop_control_hook")


class LoopLimitError(Exception):
    """ReActループ上限到達時に発生するカスタム例外。"""

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str) -> None:
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        super().__init__(
            f"ReActループの上限（{max_iterations}回）に達しました。"
            f"エージェント: {agent_name}, 現在のループ回数: {current_iteration}"
        )


class LoopControlHook:
    """ReActループ回数を監視し上限到達時にループを強制停止するフック。"""

    def __init__(self, max_iterations: int, agent_name: str) -> None:
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        self._loop_count: int = 0

    def before_invocation(self, event: BeforeInvocationEvent) -> None:
        """BeforeInvocationEvent ハンドラー: ループカウンタを 0 にリセットする。"""
        self._loop_count = 0
        logger.info(
            f"エージェント呼び出し開始: ループカウンタをリセット"
            f" (エージェント={self.agent_name}, 上限={self.max_iterations})"
        )

    def after_invocation(self, event: AfterInvocationEvent) -> None:
        """AfterInvocationEvent ハンドラー: 合計ループ回数をINFOログ出力する（リセットは行わない）。"""
        logger.info(
            f"エージェント呼び出し完了: 合計ループ回数={self._loop_count}"
            f" (エージェント={self.agent_name})"
        )

    def before_model_call(self, event: BeforeModelCallEvent) -> None:
        """BeforeModelCallEvent ハンドラー: ループ回数をINFOログ出力する。"""
        logger.info(
            f"LLM 呼び出し開始 (ループ={self._loop_count}, エージェント={self.agent_name})"
        )

    def after_model_call(self, event: AfterModelCallEvent) -> None:
        """AfterModelCallEvent ハンドラー: ループカウンタをインクリメントし上限監視する。"""
        if getattr(event, "exception", None) is not None:
            return

        self._loop_count += 1
        logger.info(
            f"LLM 呼び出し完了: ループ={self._loop_count}/{self.max_iterations}"
            f" (エージェント={self.agent_name})"
        )

        if self._loop_count >= self.max_iterations:
            logger.warning(
                f"ループ上限に達しました"
                f" (ループ={self._loop_count}, 上限={self.max_iterations},"
                f" エージェント={self.agent_name})"
            )
            raise LoopLimitError(
                current_iteration=self._loop_count,
                max_iterations=self.max_iterations,
                agent_name=self.agent_name,
            )

    def before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """BeforeToolCallEvent ハンドラー: ツール名をINFOログ出力する。"""
        tool_name = getattr(event, "tool_name", "unknown")
        logger.info(
            f"ツール呼び出し開始 (ツール名={tool_name}, エージェント={self.agent_name})"
        )

    def after_tool_call(self, event: AfterToolCallEvent) -> None:
        """AfterToolCallEvent ハンドラー: ツール名をINFOログ出力する。"""
        tool_name = getattr(event, "tool_name", "unknown")
        logger.info(
            f"ツール呼び出し完了 (ツール名={tool_name}, エージェント={self.agent_name})"
        )
```

---

### 3.2 エラーハンドリング

| エラー種別 | 条件 | 対応 |
|-----------|------|------|
| LoopLimitError | `_loop_count >= max_iterations` 時 | `raise LoopLimitError(current_iteration=..., max_iterations=..., agent_name=...)` でエージェントループを停止する。呼び出し元エージェントがエラーとして処理する |
| `BeforeInvocationEvent` ハンドラー内の例外 | リセット処理中に予期しない例外が発生した場合 | `logger.error` で記録し、例外を再送出せずにリセット処理を継続する |
| `AfterModelCallEvent` ハンドラー内の例外（LoopLimitError 以外） | カウントアップ処理中に予期しない例外が発生した場合 | `logger.error` で記録し、例外を再送出せずにループを継続する |

---

### 3.3 ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | `BeforeInvocationEvent` でカウンタリセット時 | `"エージェント呼び出し開始: ループカウンタをリセット (エージェント={agent_name}, 上限={max_iterations})"` |
| INFO | `AfterInvocationEvent` で呼び出し完了時 | `"エージェント呼び出し完了: 合計ループ回数={_loop_count} (エージェント={agent_name})"` |
| INFO | `BeforeModelCallEvent` で LLM 呼び出し開始時 | `"LLM 呼び出し開始 (ループ={_loop_count}, エージェント={agent_name})"` |
| INFO | `AfterModelCallEvent` でカウントアップ時 | `"LLM 呼び出し完了: ループ={n}/{max_iterations} (エージェント={agent_name})"` |
| WARNING | ループ上限到達時 | `"ループ上限に達しました (ループ={n}, 上限={max_iterations}, エージェント={agent_name})"` |
| INFO | `BeforeToolCallEvent` でツール呼び出し開始時 | `"ツール呼び出し開始 (ツール名={tool_name}, エージェント={agent_name})"` |
| INFO | `AfterToolCallEvent` でツール呼び出し完了時 | `"ツール呼び出し完了 (ツール名={tool_name}, エージェント={agent_name})"` |
| ERROR | ハンドラー内予期しない例外時 | `"ハンドラー内で予期しないエラーが発生しました ({handler_name}): {error_message}"` |

---

## 4. データ設計

LoopControlHook は永続的なデータを読み書きしない。ループカウンタ（`_loop_count`）はインスタンス変数としてメモリ上にのみ保持し、セッション終了時に消去される。

---

## 5. 補足情報

### 5.1 実装上の注意点

1. **各エージェントが独立したインスタンスを持つ**
   - AG-001/AG-002/AG-003 それぞれが個別の LoopControlHook インスタンスを保持する
   - インスタンス間でカウンタを共有しない（各エージェントのループカウンタは独立して管理される）

2. **BeforeInvocationEvent によるリセットの重要性**
   - `_agent_instances` キャッシュにより AG-002/AG-003 の Agent インスタンスは再利用される
   - `BeforeInvocationEvent` でカウンタを 0 にリセットすることで、前回のセッションのカウントが持ち越されず、毎回正しく30回から監視を開始できる

3. **LLM エラー時のカウント除外**
   - Bedrock API エラー時に LLM 呼び出しが失敗した場合は `event.exception` が存在する
   - `getattr(event, "exception", None) is not None` でチェックすることで、例外属性が存在しない SDK バージョンでも安全に動作する

4. **LoopLimitError の定義場所**
   - `LoopLimitError` は `handlers/loop_control_hook.py` 内で定義する
   - 他のモジュールからインポートする場合は `from handlers.loop_control_hook import LoopLimitError` を使用する

5. **AfterInvocationEvent でのリセット禁止**
   - `AfterInvocationEvent` ハンドラーでは合計ループ回数のINFOログ出力のみ行い、`_loop_count` のリセットは行わない
   - リセットは次回の `BeforeInvocationEvent` 発火時にのみ行う

### 5.2 パフォーマンス考慮事項

1. **ハンドラーのオーバーヘッド**
   - 全ハンドラーはカウンタの整数操作とログ出力のみであり、処理時間への影響は無視できる

---

## 6. 依存関係

### 6.1 外部ライブラリ
- `strands`: Strands Agents SDK
  - `BeforeInvocationEvent`: フックイベントクラス
  - `AfterInvocationEvent`: フックイベントクラス
  - `AfterModelCallEvent`: フックイベントクラス
  - `BeforeModelCallEvent`: フックイベントクラス
  - `BeforeToolCallEvent`: フックイベントクラス
  - `AfterToolCallEvent`: フックイベントクラス
- `logging`: Python 標準ライブラリ

### 6.2 内部モジュール
- `config/model_config.py`
  - `MAX_LOOP_ITERATIONS`: ループ上限回数（全エージェント共通値 = 30）

---

## 7. テスト観点

### 7.1 機能テスト
- `BeforeInvocationEvent` 発火時にループカウンタが 0 にリセットされること
- `AfterModelCallEvent` が29回発火してもループが継続すること（カウンタ = 29）
- `AfterModelCallEvent` が30回目に発火したとき `LoopLimitError` が発生すること
- `LoopLimitError` が `current_iteration=30`, `max_iterations=30`, `agent_name` の3フィールドを持つこと
- `BeforeModelCallEvent` 発火時に INFO ログが出力されること
- `BeforeToolCallEvent` 発火時にツール名が INFO ログに出力されること
- `AfterToolCallEvent` 発火時にツール名が INFO ログに出力されること
- `AfterInvocationEvent` 発火時に合計ループ回数が INFO ログに出力されること（リセットされないこと）

### 7.2 異常系テスト
- `event.exception` が存在する場合に `AfterModelCallEvent` が発火してもカウンタがインクリメントされないこと
- `BeforeInvocationEvent` 後に `AfterModelCallEvent` が30回発火し、その後再度 `BeforeInvocationEvent` が発火するとカウンタが 0 にリセットされること（前回カウントの持ち越しなし）

### 7.3 境界値テスト
- カウンタが 29 のとき（上限-1）`AfterModelCallEvent` が発火してもループが継続すること
- カウンタが 30 のとき（上限到達）`LoopLimitError` が発生すること
- `LoopLimitError` 発生時のログレベルが WARNING であること

### 7.4 性能テスト
- LoopControlHook によって ReActループが30回で終了することを確認（各エージェントで個別に測定）

---

## 8. 設定値

### 8.1 定数
- ループ上限回数: `MAX_LOOP_ITERATIONS = 30`（`config/model_config.py` で定義）
- `LoopLimitError` の定義場所: `handlers/loop_control_hook.py`

---

## 9. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-01 | 1.0 | 初版作成 |
| 2026-05-01 | 1.1 | LoopLimitError カスタム例外クラスに変更、新イベントハンドラー追加（BeforeModelCallEvent/BeforeToolCallEvent/AfterToolCallEvent/AfterInvocationEvent）、event.exception チェックに変更、ログメッセージ日本語化、MAX_LOOP_ITERATIONS を 30 に変更 |
