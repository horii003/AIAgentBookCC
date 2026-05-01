---
version: "1.1.0"
last_updated: "2026-05-01"
updated_by: ""
---

# ErrorHandler 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 2章（ErrorHandler 基本設計）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 7章（詳細設計への引き渡し事項）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 9章（制約事項・前提条件）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外分類・対応方針・メッセージ設計方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的
全エージェント（AG-001/AG-002/AG-003）およびツール（TOOL-001/TOOL-002）から発生する例外を受け取り、ユーザー向けの日本語エラーメッセージを生成して文字列で返す。ログ出力・セッション状態更新は呼び出し元が行い、ErrorHandler 自身はメッセージ生成のみを担当する。スタティックメソッドのみで構成するため、インスタンス化不要で `ErrorHandler.handle_xxx(...)` として直接呼び出せる。

### 1.2 主要な責務
- 例外オブジェクトを受け取りユーザー向け日本語エラーメッセージ文字列を生成して返す
- ログ出力は行わない（呼び出し元が責任を持って行う）
- セッション状態の更新は行わない（呼び出し元が責任を持って行う）
- コンストラクタ・インスタンス変数を持たない

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | HD-001 |
| コンポーネント名 | ErrorHandler |
| コンポーネント種別 | ハンドラー（横断的機能） |
| 説明 | 例外からユーザー向けメッセージを生成するスタティックメソッド集 |
| 実装ファイル | `handlers/error_handler.py` |

---

### 2.2 インターフェース設計

#### 2.2.1 メソッド一覧

| メソッド名 | シグネチャ | 対応する例外 | 戻り値 |
|-----------|-----------|------------|--------|
| handle_throttling_error | `handle_throttling_error(e: ModelThrottledException) -> str` | API スロットリング | ユーザー向けエラーメッセージ文字列 |
| handle_max_tokens_error | `handle_max_tokens_error(e: MaxTokensReachedException) -> str` | トークン上限超過 | ユーザー向けエラーメッセージ文字列 |
| handle_context_window_error | `handle_context_window_error(e: ContextWindowOverflowException) -> str` | コンテキストウィンドウ超過 | ユーザー向けエラーメッセージ文字列 |
| handle_fare_data_error | `handle_fare_data_error(e: FileNotFoundError \| Exception) -> str` | 運賃データファイルアクセス失敗 | ユーザー向けエラーメッセージ文字列 |
| handle_calculation_error | `handle_calculation_error(e: Exception) -> str` | 運賃計算処理エラー | ユーザー向けエラーメッセージ文字列 |
| handle_file_save_error | `handle_file_save_error(e: IOError \| PermissionError \| Exception) -> str` | ファイル保存失敗 | ユーザー向けエラーメッセージ文字列 |
| handle_validation_error | `handle_validation_error(e: ValidationError) -> str` | 入力バリデーションエラー | ユーザー向けエラーメッセージ文字列 |
| handle_keyboard_interrupt | `handle_keyboard_interrupt(e: KeyboardInterrupt) -> str` | キーボード割り込み | ユーザー向けエラーメッセージ文字列 |
| handle_loop_limit_error | `handle_loop_limit_error(e: LoopLimitError) -> str` | ループ上限到達 | ユーザー向けエラーメッセージ文字列 |
| handle_runtime_error | `handle_runtime_error(e: RuntimeError) -> str` | ランタイムエラー | ユーザー向けエラーメッセージ文字列 |
| handle_unexpected_error | `handle_unexpected_error(e: Exception) -> str` | 未分類例外 | ユーザー向けエラーメッセージ文字列 |

#### 2.2.2 共通引数

| 引数名 | 型 | 説明 | デフォルト値 |
|--------|-----|------|--------------|
| e | Exception（各メソッド対応の型） | 捕捉した例外インスタンス | なし（必須） |

#### 2.2.3 共通戻り値

**戻り値の型**: `str`

**説明**: ユーザー向けの日本語エラーメッセージ文字列。呼び出し元がそのまま表示または dict の "message" キーに設定して返却する。ログ出力は呼び出し元が行う。

---

### 2.3 ビジネスロジック

#### 2.3.1 各メソッドの詳細

##### handle_throttling_error

**目的**: API スロットリングエラーを処理し、しばらく待つよう案内するメッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "APIのリクエスト制限に達しました。しばらく待ってから再度お試しください。繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
  ```

---

##### handle_max_tokens_error

**目的**: トークン上限超過エラーを処理し、入力を短くするよう案内するメッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "入力内容が長すぎます。入力内容を短くして再度お試しください。"
  ```

---

##### handle_context_window_error

**目的**: コンテキストウィンドウ超過エラーを処理し、再開を案内するメッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "会話が長くなりすぎました。最初からやり直してください。"
  ```

---

##### handle_fare_data_error

**目的**: 運賃データファイルのアクセス失敗を処理しリトライ案内メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "運賃データの読み込み中にエラーが発生しました。しばらく待ってから再度お試しください。繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
  ```

**利用タイミング**:
- TOOL-001: `/data/train_routes.json` / `/data/fixed_fares.json` の読み込み失敗時

---

##### handle_calculation_error

**目的**: 運賃計算処理のエラーを処理し管理部門確認依頼メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "運賃計算中にエラーが発生しました。管理部門（経理部）にお問い合わせください。"
  ```

**利用タイミング**:
- TOOL-001: 運賃計算処理中の予期しないエラー発生時

---

##### handle_file_save_error

**目的**: ファイル保存失敗を処理し管理部門案内メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "申請書ファイルの保存中にエラーが発生しました。管理部門（経理部）にお問い合わせください。"
  ```

**利用タイミング**:
- TOOL-002: `data/output/{session_id}/` への Excel ファイル書き込み失敗時（IOError/PermissionError/Exception）

---

##### handle_validation_error

**目的**: 入力バリデーションエラーを処理しユーザーへの再入力案内メッセージを返す

**処理内容**:
- Pydantic ValidationError の `errors()` から詳細メッセージを抽出して付加する
- 以下の形式でメッセージを返す:
  ```
  "入力内容に誤りがあります。入力内容をご確認の上、再度入力してください。{詳細メッセージ}"
  ```
  - `{詳細メッセージ}` は `e.errors()[*].msg` を抽出して連結する。技術的な型名は含めない

**利用タイミング**:
- TOOL-001/TOOL-002: Pydantic モデルのバリデーション失敗時

---

##### handle_keyboard_interrupt

**目的**: キーボード割り込み（Ctrl+C）を処理し終了案内メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "操作が中断されました。"
  ```

**利用タイミング**:
- AG-001 の REPLループ: KeyboardInterrupt 捕捉時

---

##### handle_loop_limit_error

**目的**: ループ上限到達エラーを処理し再試行案内メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "処理の上限回数に達しました。改めて最初からお試しください。"
  ```

**利用タイミング**:
- 全エージェント: LoopControlHook が LoopLimitError を発生させた場合

---

##### handle_runtime_error

**目的**: ランタイムエラーを処理し管理部門案内メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "処理中に問題が発生しました。管理部門（経理部）にお問い合わせください。"
  ```

**利用タイミング**:
- 全エージェント・全ツール: RuntimeError 発生時

---

##### handle_unexpected_error

**目的**: 未分類例外を処理し「処理できませんでした」メッセージを返す

**処理内容**:
- 以下のメッセージを返す:
  ```
  "処理できませんでした。管理部門（経理部）にお問い合わせください。"
  ```

**利用タイミング**:
- 全エージェント・全ツール: 上記に該当しない例外発生時

---

#### 2.3.2 処理フロー

```
呼び出し元コンポーネントで例外発生
  ↓
呼び出し元が例外種別を判断し対応するメソッドを呼び出す
  - ModelThrottledException → handle_throttling_error(e)
  - MaxTokensReachedException → handle_max_tokens_error(e)
  - ContextWindowOverflowException → handle_context_window_error(e)
  - FileNotFoundError（運賃データ）→ handle_fare_data_error(e)
  - Exception（運賃計算処理）→ handle_calculation_error(e)
  - IOError / PermissionError / Exception（ファイル保存）→ handle_file_save_error(e)
  - ValidationError → handle_validation_error(e)
  - KeyboardInterrupt → handle_keyboard_interrupt(e)
  - LoopLimitError → handle_loop_limit_error(e)
  - RuntimeError → handle_runtime_error(e)
  - Exception（未分類）→ handle_unexpected_error(e)
  ↓
メソッド内部処理（ログ出力なし）
  1. ユーザー向け日本語メッセージを生成
  2. メッセージ文字列を返す
  ↓
呼び出し元コンポーネントが以下を実施
  1. 適切なレベルでログ記録（logs/agent.log）
  2. セッション状態の更新（必要な場合）
  3. メッセージの使用
     - ツール関数: {"success": False, "message": メッセージ} を返す
     - エージェント: ユーザーに提示する、または AG-001 に返却する
```

---

## 3. 実装詳細

### 3.1 クラス設計

#### 3.1.1 ErrorHandler クラス

```python
from pydantic import ValidationError
from handlers.loop_control_hook import LoopLimitError


class ErrorHandler:
    """例外からユーザー向けメッセージを生成するスタティックメソッド集。
    ログ出力・セッション更新は呼び出し元が行う。インスタンス化不要。
    """

    @staticmethod
    def handle_throttling_error(e: Exception) -> str:
        """APIスロットリングエラー処理: しばらく待つよう案内するメッセージを返す。"""
        return (
            "APIのリクエスト制限に達しました。しばらく待ってから再度お試しください。"
            "繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_max_tokens_error(e: Exception) -> str:
        """トークン上限超過エラー処理: 入力を短くするよう案内するメッセージを返す。"""
        return "入力内容が長すぎます。入力内容を短くして再度お試しください。"

    @staticmethod
    def handle_context_window_error(e: Exception) -> str:
        """コンテキストウィンドウ超過エラー処理: 再開を案内するメッセージを返す。"""
        return "会話が長くなりすぎました。最初からやり直してください。"

    @staticmethod
    def handle_fare_data_error(e: Exception) -> str:
        """運賃データファイルアクセス失敗処理: リトライ案内メッセージを返す。"""
        return (
            "運賃データの読み込み中にエラーが発生しました。しばらく待ってから再度お試しください。"
            "繰り返しエラーが発生する場合は、管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_calculation_error(e: Exception) -> str:
        """運賃計算処理エラー処理: 管理部門確認依頼メッセージを返す。"""
        return "運賃計算中にエラーが発生しました。管理部門（経理部）にお問い合わせください。"

    @staticmethod
    def handle_file_save_error(e: Exception) -> str:
        """ファイル保存失敗処理: 管理部門案内メッセージを返す。"""
        return (
            "申請書ファイルの保存中にエラーが発生しました。"
            "管理部門（経理部）にお問い合わせください。"
        )

    @staticmethod
    def handle_validation_error(e: ValidationError) -> str:
        """入力バリデーションエラー処理: 再入力案内メッセージを返す。"""
        detail = _extract_validation_detail(e)
        return f"入力内容に誤りがあります。入力内容をご確認の上、再度入力してください。{detail}"

    @staticmethod
    def handle_keyboard_interrupt(e: KeyboardInterrupt) -> str:
        """キーボード割り込み処理: 終了案内メッセージを返す。"""
        return "操作が中断されました。"

    @staticmethod
    def handle_loop_limit_error(e: LoopLimitError) -> str:
        """ループ上限到達エラー処理: 再試行案内メッセージを返す。"""
        return "処理の上限回数に達しました。改めて最初からお試しください。"

    @staticmethod
    def handle_runtime_error(e: RuntimeError) -> str:
        """ランタイムエラー処理: 管理部門案内メッセージを返す。"""
        return "処理中に問題が発生しました。管理部門（経理部）にお問い合わせください。"

    @staticmethod
    def handle_unexpected_error(e: Exception) -> str:
        """未分類例外処理: 「処理できませんでした」メッセージを返す。"""
        return "処理できませんでした。管理部門（経理部）にお問い合わせください。"


def _extract_validation_detail(e: ValidationError) -> str:
    """Pydantic ValidationError から詳細メッセージを抽出するモジュールレベルヘルパー。"""
    try:
        msgs = [err["msg"] for err in e.errors()]
        return " / ".join(msgs)
    except Exception:
        return str(e)
```

---

### 3.2 エラーハンドリング

ErrorHandler 自身のメソッド内では例外を発生させない。メッセージ文字列の返却を最優先とし、内部処理が失敗した場合でも固定の安全なメッセージを返す。

---

## 4. データ設計

ErrorHandler は永続的なデータを読み書きしない。ログ出力・セッション状態更新は呼び出し元が担当する。

---

## 5. 補足情報

### 5.1 実装上の注意点

1. **スタティックメソッドのみ（コンストラクタなし）**
   - ErrorHandler クラスはコンストラクタ・インスタンス変数を持たない。全メソッドを `@staticmethod` で定義し `ErrorHandler.handle_xxx(...)` として直接呼び出す

2. **ログ出力は呼び出し元が実施**
   - ErrorHandler 自身は `logging` モジュールをインポートしない。ログ出力・セッション更新は呼び出し元（エージェント・ツール）が責任を持って行う

3. **例外を再送出しない**
   - 各 handle_xxx メソッドは例外を捕捉するが、新たな例外を送出しない。メッセージ文字列の返却のみ行う

4. **ValidationError の詳細抽出**
   - `_extract_validation_detail` ヘルパー関数は Pydantic v2 の `errors()` メソッドを使って詳細メッセージを抽出する。抽出失敗時は `str(e)` にフォールバックする

5. **LoopLimitError のインポートパス**
   - `LoopLimitError` は `handlers/loop_control_hook.py` 内で定義されているため、`from handlers.loop_control_hook import LoopLimitError` でインポートする

### 5.2 セキュリティ考慮事項

1. **スタックトレースのユーザー非公開**
   - ユーザーに返すメッセージには技術的詳細（クラス名・ファイルパス・行番号等）を含めない。スタックトレースは呼び出し元がログに記録する

---

## 6. 依存関係

### 6.1 外部ライブラリ
- `pydantic >= 2.0`: ValidationError の詳細抽出

### 6.2 内部モジュール
- `handlers/loop_control_hook.py`
  - `LoopLimitError`: ループ上限到達カスタム例外クラス

---

## 7. テスト観点

### 7.1 機能テスト
- `handle_throttling_error` に ModelThrottledException を渡すと適切なメッセージが返却されること
- `handle_max_tokens_error` に MaxTokensReachedException を渡すと適切なメッセージが返却されること
- `handle_context_window_error` に ContextWindowOverflowException を渡すと適切なメッセージが返却されること
- `handle_fare_data_error` に FileNotFoundError を渡すと運賃データ関連メッセージが返却されること
- `handle_calculation_error` に Exception を渡すと運賃計算エラーメッセージが返却されること
- `handle_file_save_error` に IOError / PermissionError / Exception を渡すとファイル保存エラーメッセージが返却されること
- `handle_validation_error` に Pydantic ValidationError を渡すと詳細付きメッセージが返却されること
- `handle_keyboard_interrupt` に KeyboardInterrupt を渡すと終了案内メッセージが返却されること
- `handle_loop_limit_error` に LoopLimitError を渡すと上限到達メッセージが返却されること
- `handle_runtime_error` に RuntimeError を渡すと適切なメッセージが返却されること
- `handle_unexpected_error` に未分類例外を渡すと「処理できませんでした」メッセージが返却されること

### 7.2 異常系テスト
- 各 handle_xxx メソッドが例外を送出しないこと（メッセージ文字列を返すのみ）
- ログ出力が行われないこと（logging モジュールをインポートしないこと）

---

## 8. 設定値

なし（ErrorHandler はログ設定・定数を持たない）

---

## 9. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-01 | 1.0 | 初版作成 |
| 2026-05-01 | 1.1 | メソッドを旧8メソッドから新11メソッドに全面刷新、ログ出力・セッション更新を呼び出し元に移譲、コンストラクタ・loggingインポートを削除、LoopLimitErrorインポート追加 |
