---
version: "1.1.0"
last_updated: "2026-05-01"
updated_by: ""
---

# HumanApprovalHook 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 3章（HumanApprovalHook 基本設計）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 7章（詳細設計への引き渡し事項）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 9章（制約事項・前提条件）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/実行制御方針.md（APR-001 承認フロー・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的
AG-002/AG-003 が申請書生成ツール（申請書生成ツール詳細設計書に定義されたツール関数）を呼び出す直前に介入し、社員（R-EMP）に申請書生成前の確認（APR-001）を求める。承認（OK）後にはじめてツールが実行される。修正またはキャンセルの場合はツール実行をブロックする。APR-001 承認は1回のみ発生する（ABAC-001）。

### 1.2 主要な責務
- `BeforeToolCallEvent` で申請書生成ツール呼び出しを検知し APR-001 ダイアログ（OK / 修正 / キャンセル）を提示する
- 承認済みフラグ（`approval_granted = True`）を `session_{id}.json` に FileBasedSessionManager 経由で記録する
- キャンセル時にセッション状態を TERMINATED に遷移させる指示を行う
- 強化監査ログ（LOG-HI: `logs/audit_log_hi.jsonl`）に承認者・承認日時・対象申請情報を記録する
- 不正入力が3回続いた場合はキャンセルとして処理する

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | HD-002 |
| コンポーネント名 | HumanApprovalHook |
| コンポーネント種別 | ハンドラー（承認フック） |
| 説明 | 申請書生成ツール呼び出し前に APR-001 承認ダイアログを提示するフック |
| 実装ファイル | `handlers/human_approval_hook.py` |

---

### 2.2 インターフェース設計

#### 2.2.1 コンストラクタ

| 引数名 | 型 | 説明 | デフォルト値 |
|--------|-----|------|--------------|
| approval_callback | Callable[[str, dict], tuple[bool, str]] | 承認確認を行うコールバック関数。シグネチャ: `(tool_name: str, tool_params: dict) -> tuple[bool, str]` | なし（必須） |

#### 2.2.2 登録イベントとハンドラー

| イベント名 | ハンドラーメソッド名 | 発火タイミング | 処理概要 |
|-----------|-------------------|--------------|---------|
| BeforeToolCallEvent | `before_tool_call` | 申請書生成ツール呼び出し直前 | APR-001 ダイアログ提示・承認結果による実行可否制御 |

#### 2.2.3 エージェントへの登録

```python
# AG-002 / AG-003 の Agent 初期化時に hooks パラメータへ登録する
Agent(
    ...,
    hooks=[
        LoopControlHook(max_iterations=MAX_LOOP_ITERATIONS, agent_name="AG-002"),
        HumanApprovalHook(approval_callback=approval_callback),
    ],
    ...
)
```

> AG-001 には登録しない（申請書生成権限なし）

---

### 2.3 ビジネスロジック

#### 2.3.1 承認対象ツール

承認対象ツール名は申請書生成ツール詳細設計書に定義された全ツール関数名とする。

> 現在の申請書生成ツール詳細設計書が定義するツール関数: `generate_transport_application`, `generate_expense_application`

| ツール名 | 対象エージェント | 判定条件 |
|---------|----------------|---------|
| generate_transport_application | AG-002 | `event.tool_name == "generate_transport_application"` |
| generate_expense_application | AG-003 | `event.tool_name == "generate_expense_application"` |

> TOOL-001（calculate_transport_fare）は承認対象外とする。`event.tool_name` が上記以外の場合はフックを即時通過させる

#### 2.3.2 APR-001 ダイアログ

**提示メッセージ**:
```
【申請書生成の確認（APR-001）】
以下の内容で申請書を生成します。内容をご確認の上、選択してください。
---
{収集済み申請情報のサマリー}
---
> OK       → 申請書を生成します
> 修正     → 修正箇所を指定して再収集します
> キャンセル → 申請書の生成をキャンセルします

入力してください (OK / 修正 / キャンセル):
```

**コールバックシグネチャ**:
```python
def approval_callback(tool_name: str, tool_params: dict) -> tuple[bool, str]:
    ...
```

**コールバック戻り値の解釈**:

| 戻り値 | 意味 | 処理 |
|--------|------|------|
| `(True, "")` | 承認（OK） | ツール実行を続行する |
| `(False, "修正内容の文字列")` | 修正要望 | ツール実行をキャンセルし修正フローへ戻す |
| `(False, "CANCEL")` | キャンセル | ツール実行をキャンセルしセッションを TERMINATED へ遷移 |

#### 2.3.3 処理フロー

```
BeforeToolCallEvent 発火
  ↓
[event.tool_name が承認対象ツールか？（申請書生成ツール詳細設計書で定義されたツール関数名）]
  - NO（calculate_transport_fare 等）→ フック即時通過（ツール実行を続行）
  - YES → APR-001 処理開始
  ↓
_invalid_input_count = 0 にリセット
  ↓
approval_callback(tool_name=event.tool_name, tool_params=event.tool_use.get("input", {})) を呼び出す
  ↓
[コールバック戻り値の判定]
  - (True, "")          → 承認処理へ
  - (False, "CANCEL")   → キャンセル処理へ
  - (False, "修正内容") → 修正処理へ
  - 不正入力            → 不正入力カウンタをインクリメント
                          [カウンタ >= 3？]
                            - YES → キャンセル処理へ
                            - NO  → コールバック再呼び出し
  ↓
【承認処理（(True, "")）】
  FileBasedSessionManager で session_{id}.json に approval_granted = True を記録
  強化監査ログ（audit_log_hi.jsonl）に承認情報を記録:
    {"event": "APR-001_approved", "session_id": ..., "tool_name": ..., "timestamp": ...}
  ツール実行を続行する（event.cancel_tool は設定しない）
  ↓
【修正処理（(False, "修正内容")）】
  event.cancel_tool = "修正要求: {修正内容}" をセットする
  AG-002/AG-003 の ReAct ループが修正対話を実行した後、再度 APR-001 を実施する
  ↓
【キャンセル処理（(False, "CANCEL")）】
  event.cancel_tool = "キャンセル" をセットする
  強化監査ログ（audit_log_hi.jsonl）にキャンセル情報を記録:
    {"event": "APR-001_cancelled", "session_id": ..., "tool_name": ..., "timestamp": ...}
  FileBasedSessionManager で session_{id}.json の status を TERMINATED に更新
  ↓
終了
```

---

### 2.4 設定・構成

#### 2.4.1 インスタンス変数

| 変数名 | 型 | 説明 | 初期値 |
|--------|-----|------|--------|
| `approval_callback` | Callable | 承認確認コールバック関数（コンストラクタで設定） | — |
| `_invalid_input_count` | int | 不正入力カウンタ（1回の APR-001 呼び出し中にリセット） | 0 |

> `_invalid_input_count` は `BeforeToolCallEvent` ハンドラー呼び出し開始時に 0 にリセットする（前回の不正入力カウントが持ち越されないようにする）

#### 2.4.2 ログ設定

| 設定項目 | 設定値 |
|---------|--------|
| ロガー名 | `handlers.human_approval_hook` |
| 強化監査ログファイル | `logs/audit_log_hi.jsonl` |
| 強化監査ログ形式 | JSON Lines（1行1件の JSON オブジェクト） |

---

## 3. 実装詳細

### 3.1 クラス設計

#### 3.1.1 HumanApprovalHook クラス

```python
import json
import logging
from datetime import datetime
from typing import Callable
from strands.hooks import BeforeToolCallEvent

logger = logging.getLogger("handlers.human_approval_hook")

APPROVAL_TOOL_NAMES = {
    "generate_transport_application",
    "generate_expense_application",
}
APPROVAL_INVALID_MAX = 3
AUDIT_LOG_HI_PATH = "logs/audit_log_hi.jsonl"


class HumanApprovalHook:
    """申請書生成ツール呼び出し前に APR-001 承認ダイアログを提示するフック。"""

    def __init__(self, approval_callback: Callable[[str, dict], tuple[bool, str]]) -> None:
        self.approval_callback = approval_callback
        self._invalid_input_count: int = 0

    def before_tool_call(self, event: BeforeToolCallEvent) -> None:
        """BeforeToolCallEvent ハンドラー: 申請書生成ツール呼び出し前に APR-001 を実施する。"""
        if event.tool_name not in APPROVAL_TOOL_NAMES:
            return  # 承認対象外ツールはスキップ

        self._invalid_input_count = 0  # カウンタリセット
        tool_params = event.tool_use.get("input", {}) if hasattr(event, "tool_use") else {}

        while True:
            approved, detail = self.approval_callback(event.tool_name, tool_params)

            if approved:
                self._handle_approved(event)
                return

            elif not approved and detail == "CANCEL":
                self._handle_cancelled(event)
                return

            elif not approved and detail:
                self._handle_modify(event, detail)
                return

            else:
                self._invalid_input_count += 1
                if self._invalid_input_count >= APPROVAL_INVALID_MAX:
                    logger.warning(
                        f"APR-001: 不正入力が{APPROVAL_INVALID_MAX}回に達したためキャンセル処理: "
                        f"tool_name={event.tool_name}"
                    )
                    self._handle_cancelled(event)
                    return

    def _handle_approved(self, event: BeforeToolCallEvent) -> None:
        """承認（OK）時の処理: approval_granted を記録してツール実行を続行する。"""
        logger.info(f"APR-001 承認: tool_name={event.tool_name}")
        self._write_audit_log("APR-001_approved", event.tool_name)
        # event.cancel_tool は設定しない → ツール実行を続行

    def _handle_modify(self, event: BeforeToolCallEvent, modify_detail: str) -> None:
        """修正時の処理: ツール実行をキャンセルして修正フローへ戻す。"""
        logger.info(f"APR-001 修正要求: tool_name={event.tool_name}, detail={modify_detail}")
        event.cancel_tool = f"修正要求: {modify_detail}"

    def _handle_cancelled(self, event: BeforeToolCallEvent) -> None:
        """キャンセル時の処理: ツール実行をキャンセルしセッションを TERMINATED へ遷移する。"""
        logger.warning(f"APR-001 キャンセル: tool_name={event.tool_name}")
        self._write_audit_log("APR-001_cancelled", event.tool_name)
        event.cancel_tool = "キャンセル"

    def _write_audit_log(self, event_name: str, tool_name: str) -> None:
        """強化監査ログ（audit_log_hi.jsonl）に承認情報を記録する。"""
        try:
            entry = {
                "event": event_name,
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat(),
            }
            with open(AUDIT_LOG_HI_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"監査ログ書き込み失敗: {str(e)}", exc_info=True)
```

---

### 3.2 エラーハンドリング

| エラー種別 | 条件 | 対応 | メッセージ |
|-----------|------|------|-----------|
| 監査ログ書き込み失敗 | `logs/audit_log_hi.jsonl` への書き込みが失敗した場合 | ログ記録のみ（エラーを握りつぶさず `logger.error` で記録）。ツール実行の可否判断は継続 | `"監査ログ書き込み失敗: {error_message}"` |
| `event.cancel_tool` セット失敗 | Strands SDK の cancel_tool 属性へのセットが例外を発生させた場合 | `logger.error` で記録 | `"event.cancel_tool セット失敗: {error_message}"` |

---

### 3.3 ログ出力

| レベル | タイミング | メッセージ |
|--------|-----------|-----------|
| INFO | APR-001 承認（OK）時 | `"APR-001 承認: tool_name={tool_name}"` |
| INFO | APR-001 修正要求時 | `"APR-001 修正要求: tool_name={tool_name}, detail={modify_detail}"` |
| WARNING | APR-001 キャンセル時 | `"APR-001 キャンセル: tool_name={tool_name}"` |
| WARNING | 不正入力3回に達したとき | `"APR-001: 不正入力が3回に達したためキャンセル処理: tool_name={tool_name}"` |
| ERROR | 監査ログ書き込み失敗時 | `"監査ログ書き込み失敗: {error_message}"` |

---

## 4. データ設計

### 4.1 強化監査ログ（audit_log_hi.jsonl）

**データソース**: `logs/audit_log_hi.jsonl`

**書き込みタイミング**:
- APR-001 承認（OK）時
- APR-001 キャンセル時

**レコード構造**:
```json
{
  "event": "APR-001_approved",
  "tool_name": "generate_transport_application",
  "timestamp": "2026-05-01T14:30:22.123456"
}
```

---

## 5. 補足情報

### 5.1 実装上の注意点

1. **APR-001 は1回のみ発生する**
   - HumanApprovalHook は BeforeToolCallEvent で1回のみ発火する。承認（OK）後にツールが実行されるため、同一ツール呼び出しに対して2回 APR-001 が発生することはない
   - 修正の場合はエージェントが情報再収集ループを実行し、再度ツールを呼び出す際に改めて BeforeToolCallEvent が発火する

2. **ツール中止方法: event.cancel_tool を使用する**
   - ツール実行のキャンセル・修正には `event.cancel_tool` に文字列をセットする
   - `event.stop_reason` ではなく `event.cancel_tool` を使用すること
   - `event.cancel()` メソッドへの言及は本設計書では使用しない

3. **承認対象ツール名は申請書生成ツール詳細設計書に従う**
   - `APPROVAL_TOOL_NAMES` に含めるツール関数名は申請書生成ツール詳細設計書に定義されたツール関数名と一致させること
   - 申請書生成ツール詳細設計書が更新された場合は本設定も同期すること

4. **session_id の取得方法**
   - 監査ログへの session_id 記録は `event` オブジェクトまたは ToolContext 経由で取得する
   - SDK バージョンによって取得方法が異なる場合は ToolContext の invocation_state から取得すること

5. **AG-001 への非登録**
   - AG-001 は申請書生成権限を持たないため HumanApprovalHook を登録しない（基本設計書 9.2 制約事項準拠）

### 5.2 セキュリティ考慮事項

1. **APR-001 の必須化**
   - HumanApprovalHook が登録されていない場合は申請書生成ツールを実行してはならない（ABAC-001）
   - AG-002/AG-003 の Agent 初期化コードで HumanApprovalHook が hooks リストに含まれていることをテストで確認すること

---

## 6. 依存関係

### 6.1 外部ライブラリ
- `strands`: Strands Agents SDK
  - `BeforeToolCallEvent`: フックイベントクラス
- `logging`: Python 標準ライブラリ
- `json`: Python 標準ライブラリ（監査ログの JSON Lines 形式出力）
- `datetime`: Python 標準ライブラリ（監査ログのタイムスタンプ記録）
- `typing`: Python 標準ライブラリ（Callable 型ヒント）

### 6.2 内部モジュール
- `agents/session/file_based_session_manager.py`
  - `FileBasedSessionManager`: approval_granted フラグ・TERMINATED 遷移の記録

---

## 7. テスト観点

### 7.1 機能テスト
- `BeforeToolCallEvent` で `tool_name="generate_transport_application"` のとき APR-001 コールバックが呼び出されること
- `BeforeToolCallEvent` で `tool_name="calculate_transport_fare"` のときフックが即時通過すること（コールバック呼び出しなし）
- コールバックが `(True, "")` を返した場合にツール実行が継続され、`approval_granted=True` が session_{id}.json に記録されること
- コールバックが `(False, "修正箇所のテキスト")` を返した場合に `event.cancel_tool` が "修正要求: 修正箇所のテキスト" にセットされること
- コールバックが `(False, "CANCEL")` を返した場合に `event.cancel_tool` が "キャンセル" にセットされること

### 7.2 Human-in-the-Loop テスト
- APR-001 承認が BeforeToolCallEvent で1回のみ発生し、承認（OK）後にはじめてツールが実行されること
- 承認前にツールが実行されないこと（ABAC-001）
- コールバックシグネチャ `(tool_name: str, tool_params: dict) -> tuple[bool, str]` が正しく動作すること

### 7.3 異常系テスト
- 不正入力（コールバックが期待外の値を返す）が3回続いた場合にキャンセルとして処理されること
- 監査ログ書き込み失敗時にも APR-001 の処理フローが継続されること
- `event.cancel_tool` セット失敗時に `logger.error` で記録されること

---

## 8. 設定値

### 8.1 定数
- 承認対象ツール名: 申請書生成ツール詳細設計書に定義された全ツール関数名（現在: `{"generate_transport_application", "generate_expense_application"}`）
- 不正入力最大回数: `3`
- 強化監査ログファイルパス: `logs/audit_log_hi.jsonl`

---

## 9. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-01 | 1.0 | 初版作成 |
| 2026-05-01 | 1.1 | 承認対象ツールを「申請書生成ツール詳細設計書に定義された全ツール関数名」への参照に変更、コールバックシグネチャを `(tool_name: str, tool_params: dict) -> tuple[bool, str]` に明示、ツール中止方法を `event.cancel_tool` に変更（`event.stop_reason`・`event.cancel()` は不使用）、コンストラクタに approval_callback 引数を追加、ログメッセージ日本語化 |
