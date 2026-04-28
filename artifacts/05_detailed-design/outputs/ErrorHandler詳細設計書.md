# ErrorHandler 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 2章（ErrorHandler基本設計）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 2.3節（主要メソッド一覧）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 2.5節（設計方針と設計意図）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（EX-01〜EX-08分類・対応方針マトリクス）
> - artifacts/03_system-design/outputs/共通設定方針.md（ログ設定の詳細）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント（AG-001/AG-002/AG-003）・全ツール（TOOL-001/TOOL-002）で発生した例外を受け取り、ユーザー向けメッセージ文字列を生成して返す。ログ出力・セッション状態更新は呼び出し元モジュールが責務を持ち、ErrorHandler 自身は行わない。

### 1.2 主要な責務

- **ユーザー向けメッセージ生成と返却**: 例外種別に応じた日本語メッセージを生成し、次のアクション（再入力・システム管理者連絡等）を含めて返す

### 1.3 非責務

- ログ出力（呼び出し元モジュールが ErrorHandler 呼び出し前に実施する）
- セッション状態更新（SessionManager の呼び出しは禁止）

---

## 2. 設計詳細

### 2.1 基本情報

| 項目 | 内容 |
|------|------|
| コンポーネントID | `HD-001` |
| コンポーネント名 | ErrorHandler |
| コンポーネント種別 | ハンドラー（横断的機能） |
| 説明 | 全エージェント・ツールで発生した例外に対してユーザー向けメッセージ文字列を生成して返す共通ハンドラー |

---

### 2.2 インターフェース設計

#### 2.2.1 入力

各メソッドの引数:

| メソッド名 | 引数 | 説明 |
|-----------|------|------|
| `handle_throttling_error(e)` | `e: ModelThrottledException` | APIレート制限 |
| `handle_max_tokens_error(e)` | `e: MaxTokensReachedException` | 最大トークン数到達 |
| `handle_context_window_error(e)` | `e: ContextWindowOverflowException` | コンテキストウィンドウ超過 |
| `handle_fare_data_error(e)` | `e: FileNotFoundError \| Exception` | 運賃データ読み込み失敗 |
| `handle_calculation_error(e)` | `e: Exception` | 運賃計算失敗 |
| `handle_file_save_error(e)` | `e: IOError \| PermissionError \| Exception` | Excelファイル保存失敗 |
| `handle_validation_error(e)` | `e: ValidationError` | Pydanticバリデーション失敗 |
| `handle_keyboard_interrupt(e)` | `e: KeyboardInterrupt` | ユーザーによる中断 |
| `handle_loop_limit_error(e)` | `e: LoopLimitError` | ループ上限到達 |
| `handle_runtime_error(e)` | `e: RuntimeError` | その他の実行時エラー |
| `handle_unexpected_error(e)` | `e: Exception` | 予期しないエラー |

> 全メソッドの引数は例外オブジェクトのみ。コンストラクタの引数はなし。

#### 2.2.2 出力

**戻り値の型**: `str`（ユーザー向けメッセージ文字列）

全メソッドが日本語のユーザー向けメッセージ文字列のみを返す。呼び出し元（エージェント・ツール）がこのメッセージをユーザーへ提示する。

---

### 2.3 ビジネスロジック

#### 2.3.1 メソッド設計詳細

**handle_throttling_error(e) → str**
- 対象例外: `ModelThrottledException`
- 用途: APIレート制限
- 返却メッセージ: `"申し訳ありません。AIサービスへの接続が混雑しています。しばらく時間をおいて再度お試しください。"`

**handle_max_tokens_error(e) → str**
- 対象例外: `MaxTokensReachedException`
- 用途: 最大トークン数到達
- 返却メッセージ: `"申し訳ありません。処理できる情報量の上限に達しました。入力内容を短くして再度お試しください。"`

**handle_context_window_error(e) → str**
- 対象例外: `ContextWindowOverflowException`
- 用途: コンテキストウィンドウ超過
- 返却メッセージ: `"申し訳ありません。会話履歴が長くなりすぎました。「reset」と入力してセッションをリセットしてください。"`

**handle_fare_data_error(e) → str**
- 対象例外: `FileNotFoundError` / `Exception`
- 用途: 運賃データ読み込み失敗
- 返却メッセージ: `"申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"`

**handle_calculation_error(e) → str**
- 対象例外: `Exception`
- 用途: 運賃計算失敗
- 返却メッセージ: `"申し訳ありません。運賃の計算中にエラーが発生しました。交通費を手動で入力してください。"`

**handle_file_save_error(e) → str**
- 対象例外: `IOError` / `PermissionError` / `Exception`
- 用途: Excelファイル保存失敗
- 返却メッセージ: `"申し訳ありません。申請書ファイルの保存に失敗しました。システム管理者にご連絡ください。"`

**handle_validation_error(e) → str**
- 対象例外: `ValidationError`
- 用途: Pydanticバリデーション失敗
- 返却メッセージ: `"申請情報に不足している項目があります。{フィールド名}を入力してください。"`（最初のエラーフィールドを提示）

**handle_keyboard_interrupt(e) → str**
- 対象例外: `KeyboardInterrupt`
- 用途: ユーザーによる中断
- 返却メッセージ: `"システムを終了します。"`

**handle_loop_limit_error(e) → str**
- 対象例外: `LoopLimitError`
- 用途: ループ上限到達
- 返却メッセージ: `"処理が複雑になりすぎたため終了します。最初からやり直すには「reset」と入力してください。"`

**handle_runtime_error(e) → str**
- 対象例外: `RuntimeError`
- 用途: その他の実行時エラー
- 返却メッセージ: `"申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"`

**handle_unexpected_error(e) → str**
- 対象例外: `Exception`
- 用途: 予期しないエラー
- 返却メッセージ: `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"`

#### 2.3.2 例外と対応メソッドの対応表

| メソッド名 | 対象例外クラス | 用途 |
|-----------|--------------|------|
| `handle_throttling_error` | `ModelThrottledException` | APIレート制限 |
| `handle_max_tokens_error` | `MaxTokensReachedException` | 最大トークン数到達 |
| `handle_context_window_error` | `ContextWindowOverflowException` | コンテキストウィンドウ超過 |
| `handle_fare_data_error` | `FileNotFoundError` / `Exception` | 運賃データ読み込み失敗 |
| `handle_calculation_error` | `Exception` | 運賃計算失敗 |
| `handle_file_save_error` | `IOError` / `PermissionError` / `Exception` | Excelファイル保存失敗 |
| `handle_validation_error` | `ValidationError` | Pydanticバリデーション失敗 |
| `handle_keyboard_interrupt` | `KeyboardInterrupt` | ユーザーによる中断 |
| `handle_loop_limit_error` | `LoopLimitError` | ループ上限到達 |
| `handle_runtime_error` | `RuntimeError` | その他の実行時エラー |
| `handle_unexpected_error` | `Exception` | 予期しないエラー |

---

## 3. 実装詳細

### 3.1 クラス設計

#### 3.1.1 ErrorHandlerクラス

##### コンストラクタ

```python
class ErrorHandler:
    def __init__(self):
        pass  # 依存注入なし・インスタンス変数なし
```

- コンストラクタの引数はなし
- `logger` インスタンス変数は定義しない
- `SessionManager` 等の依存注入は行わない

##### 主要メソッド

| メソッド名 | 引数 | 戻り値 | 説明 |
|-----------|------|--------|------|
| `handle_throttling_error(e)` | `e: ModelThrottledException` | `str` | APIレート制限時のメッセージ生成 |
| `handle_max_tokens_error(e)` | `e: MaxTokensReachedException` | `str` | 最大トークン数到達時のメッセージ生成 |
| `handle_context_window_error(e)` | `e: ContextWindowOverflowException` | `str` | コンテキストウィンドウ超過時のメッセージ生成 |
| `handle_fare_data_error(e)` | `e: FileNotFoundError \| Exception` | `str` | 運賃データ読み込み失敗時のメッセージ生成 |
| `handle_calculation_error(e)` | `e: Exception` | `str` | 運賃計算失敗時のメッセージ生成 |
| `handle_file_save_error(e)` | `e: IOError \| PermissionError \| Exception` | `str` | ファイル保存失敗時のメッセージ生成 |
| `handle_validation_error(e)` | `e: ValidationError` | `str` | バリデーション失敗時のメッセージ生成 |
| `handle_keyboard_interrupt(e)` | `e: KeyboardInterrupt` | `str` | ユーザー中断時のメッセージ生成 |
| `handle_loop_limit_error(e)` | `e: LoopLimitError` | `str` | ループ上限到達時のメッセージ生成 |
| `handle_runtime_error(e)` | `e: RuntimeError` | `str` | 実行時エラー時のメッセージ生成 |
| `handle_unexpected_error(e)` | `e: Exception` | `str` | 予期しないエラー時のメッセージ生成 |

---

### 3.2 呼び出し元での責務分担

ErrorHandler はメッセージ生成のみを担う。ログ出力・セッション状態更新は呼び出し元が実施する。

```python
# 呼び出し元の実装例（AG-001の対話ループ内）
except LoopLimitError as e:
    logger.warning("[AG-001] ループ上限到達", extra={"session_id": session_id})  # ← 呼び出し元でログ出力
    message = error_handler.handle_loop_limit_error(e)  # ← メッセージ生成のみ
    print(message)
    continue  # ← ループ制御も呼び出し元

except KeyboardInterrupt as e:
    logger.info("[AG-001] ユーザーによる中断", extra={"session_id": session_id})
    message = error_handler.handle_keyboard_interrupt(e)
    print(message)
    break
```

---

## 4. データ設計

なし（ErrorHandler はメッセージ文字列を生成して返すのみ。永続化データなし）

---

## 5. 補足情報

### 5.1 実装上の注意点

1. **メソッドの責務は「ユーザー向けメッセージ文字列の生成と返却」のみ**
   - 各メソッド内でのログ出力（`logging.error` / `logging.warning` 等）は禁止する
   - 各メソッド内でのセッション状態更新（SessionManager の呼び出し）は禁止する
   - ログ出力は呼び出し元モジュール（各エージェント・各ツール）が ErrorHandler 呼び出し前に実施する

2. **インスタンス化の方法**
   - `ErrorHandler` クラスのインスタンスを各エージェント・各ツールで個別にインスタンス化する
   - `handlers/error_handler.py` に集約し、全コンポーネントが共通モジュールをインポートする

3. **スレッドセーフ性**
   - 本システムはシングルスレッド・CLIベースの逐次処理のため、インスタンス間の競合は発生しない

4. **ToolのValidationError処理**
   - ツール関数（TOOL-001/TOOL-002）はValidationErrorをキャッチして `handle_validation_error()` に委譲し、`{"success": False, "message": メッセージ}` を返す。例外を再送出しない

---

### 5.2 パフォーマンス考慮事項

なし（文字列生成のみのため無視できるレベル）

---

### 5.3 セキュリティ考慮事項

1. **スタックトレースの非公開**
   - スタックトレース・SDK内部エラーはログファイルにのみ記録（呼び出し元が実施）し、ユーザー向けメッセージには含めない

---

## 6. 依存関係

### 6.1 外部ライブラリ
- `pydantic`:
  - `ValidationError`: Pydanticバリデーションエラー
- `strands.exceptions`:
  - `ModelThrottledException`: APIレート制限例外
  - `MaxTokensReachedException`: 最大トークン数到達例外
  - `ContextWindowOverflowException`: コンテキストウィンドウ超過例外

### 6.2 内部モジュール
- `handlers/exceptions.py`:
  - `LoopLimitError`: ループ上限到達カスタム例外（`hooks/loop_control_hook.py` で定義）

---

## 7. テスト観点

### 7.1 機能テスト
- `handle_throttling_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_max_tokens_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_context_window_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_fare_data_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_calculation_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_file_save_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_validation_error(e)` がPydanticのValidationErrorから不足フィールド名を抽出してメッセージに含めること
- `handle_keyboard_interrupt(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_loop_limit_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_runtime_error(e)` が正しいユーザー向けメッセージ文字列を返すこと
- `handle_unexpected_error(e)` が正しいユーザー向けメッセージ文字列を返すこと

### 7.2 異常系テスト
- 各メソッドがログ出力を行わないこと（ログ出力は呼び出し元の責務）
- 各メソッドがSessionManagerを呼び出さないこと
- 各メソッドが例外を再送出しないこと（str を返すのみ）

### 7.3 性能テスト
- 各メソッドの処理時間が1ms以下であること

---

## 8. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 1.0 | 新フォーマットで作成 |
| 2026-04-28 | 1.1 | メソッド仕様を刷新（修正#7）：責務をユーザー向けメッセージ生成のみに限定、ログ出力・セッション管理を除外、コンストラクタ引数なし、メソッド引数を例外オブジェクトのみに統一 |
