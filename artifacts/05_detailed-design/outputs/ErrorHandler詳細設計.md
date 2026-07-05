---
version: "2.0.0"
last_updated: "2026-07-03"
updated_by: ""
---

# ErrorHandler 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 2章（ErrorHandlerの位置づけ・主要メソッド）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針・エラー分類）
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント・ツールから発生した例外を受け取り、ユーザー向けメッセージ文字列を生成して返却する。

### 1.2 主要な責務

1. **ユーザー向け日本語メッセージ文字列の生成と返却のみ**: 例外オブジェクトを受け取り、技術的エラー詳細（スタックトレース・内部コード）を隠蔽した業務的な言葉のメッセージ文字列を返す

### 1.3 非責務
- バリデーションロジック（Pydantic モデルが担当: BD-02）
- セッション状態更新（セッションマネージャ: BD-05 が担当）
- 例外の握り潰し（呼び出し元が適切に処理する）
- ログ出力（呼び出し元が実施する）
- logging ライブラリへの依存

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`ErrorHandler`

#### 説明
AIエージェントシステム全体の例外を一元的に処理するクラス。例外オブジェクトを受け取り、ユーザー向け日本語メッセージ文字列を生成して返却する。ログ出力・セッション状態更新は一切行わない。

---

### 2.2 初期化

#### `__init__(self)`
引数なしで初期化するシンプルな初期化メソッド。

**引数**: なし

**インスタンス変数**: なし（ステートレス設計）

**外部ライブラリ依存**: なし

---

### 2.3 主要メソッド

#### 2.3.1 handle_throttling_error

##### 説明
APIレート制限（ModelThrottledException）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (ModelThrottledException): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"現在、システムへのリクエストが集中しています。しばらく経ってから再度お試しください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.2 handle_max_tokens_error

##### 説明
最大トークン数到達（MaxTokensReachedException）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (MaxTokensReachedException): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"入力内容が長すぎます。内容を分割して再度お試しください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.3 handle_context_window_error

##### 説明
コンテキストウィンドウ超過（ContextWindowOverflowException）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (ContextWindowOverflowException): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"会話履歴が上限に達しました。'reset' コマンドで最初からやり直してください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.4 handle_fare_data_error

##### 説明
運賃データ読み込み失敗（FileNotFoundError または Exception）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (FileNotFoundError | Exception): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"交通費データの読み込みに失敗しました。担当部門にお問い合わせください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.5 handle_calculation_error

##### 説明
運賃計算失敗（Exception）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (Exception): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"交通費の計算中にエラーが発生しました。手動で金額を入力してください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.6 handle_file_save_error

##### 説明
Excelファイル保存失敗（IOError、PermissionError、または Exception）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (IOError | PermissionError | Exception): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"申請書ファイルの保存に失敗しました。担当部門にお問い合わせください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.7 handle_validation_error

##### 説明
Pydanticバリデーション失敗（ValidationError）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (ValidationError): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"入力内容に不備があります。必須項目をご確認の上、再度お試しください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.8 handle_keyboard_interrupt

##### 説明
ユーザーによる中断（KeyboardInterrupt）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (KeyboardInterrupt): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"申請処理を中断しました。またのご利用をお待ちしております。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.9 handle_loop_limit_error

##### 説明
ループ上限到達（LoopLimitError）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (LoopLimitError): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"処理の繰り返し回数が上限に達しました。しばらく経ってから再度お試しください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.10 handle_runtime_error

##### 説明
その他の実行時エラー（RuntimeError）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (RuntimeError): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"申請処理中にエラーが発生しました。担当部門にお問い合わせください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

#### 2.3.11 handle_unexpected_error

##### 説明
予期しないエラー（Exception）に対するユーザー向けメッセージを生成する。

##### 引数
- `error` (Exception): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ文字列
  - 例: `"予期しないエラーが発生しました。担当部門にお問い合わせください。"`

##### 処理内容
1. メッセージ文字列を生成して返す（ログ出力・セッション状態更新は行わない）

---

## 3. ビジネスロジック

### 3.1 処理フロー

#### 概要

```
呼び出し元（エージェント・ツール）でエラー発生
  ↓
呼び出し元がログ出力（logger.warning / logger.error 等）
  ↓
ErrorHandler の該当メソッドにエラーオブジェクトを渡す
  ↓
ErrorHandler がユーザー向けメッセージ文字列を生成して返却
  ↓
呼び出し元が受け取った文字列を print / LLMコンテキストに渡す
```

#### 各メソッドの用途対応

| メソッド名 | 対象例外 | 用途 |
|-----------|---------|------|
| handle_throttling_error | ModelThrottledException | APIレート制限 |
| handle_max_tokens_error | MaxTokensReachedException | 最大トークン数到達 |
| handle_context_window_error | ContextWindowOverflowException | コンテキストウィンドウ超過 |
| handle_fare_data_error | FileNotFoundError / Exception | 運賃データ読み込み失敗 |
| handle_calculation_error | Exception | 運賃計算失敗 |
| handle_file_save_error | IOError / PermissionError / Exception | Excelファイル保存失敗 |
| handle_validation_error | ValidationError | Pydanticバリデーション失敗 |
| handle_keyboard_interrupt | KeyboardInterrupt | ユーザーによる中断 |
| handle_loop_limit_error | LoopLimitError | ループ上限到達 |
| handle_runtime_error | RuntimeError | その他の実行時エラー |
| handle_unexpected_error | Exception | 予期しないエラー |

---

## 4. エラーハンドリング

### 4.1 処理されるエラー

| メソッド名 | 対象例外クラス | 用途 | 戻り値型 |
|-----------|--------------|------|---------|
| handle_throttling_error | ModelThrottledException | APIレート制限 | str |
| handle_max_tokens_error | MaxTokensReachedException | 最大トークン数到達 | str |
| handle_context_window_error | ContextWindowOverflowException | コンテキストウィンドウ超過 | str |
| handle_fare_data_error | FileNotFoundError / Exception | 運賃データ読み込み失敗 | str |
| handle_calculation_error | Exception | 運賃計算失敗 | str |
| handle_file_save_error | IOError / PermissionError / Exception | Excelファイル保存失敗 | str |
| handle_validation_error | ValidationError | Pydanticバリデーション失敗 | str |
| handle_keyboard_interrupt | KeyboardInterrupt | ユーザーによる中断 | str |
| handle_loop_limit_error | LoopLimitError | ループ上限到達 | str |
| handle_runtime_error | RuntimeError | その他の実行時エラー | str |
| handle_unexpected_error | Exception | 予期しないエラー | str |

---

## 5. ログ出力

ErrorHandler 自身はログを出力しない。ログ出力は呼び出し元（各エージェント・ツール）が ErrorHandler 呼び出し前に実施する。

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
import logging
from handlers.error_handler import ErrorHandler
from exceptions import LoopLimitError

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()

try:
    result = agent(query, session_id=session_id)
except LoopLimitError as e:
    logger.warning("ループ上限到達", extra={"session_id": session_id})
    message = error_handler.handle_loop_limit_error(e)
    print(message)
    continue
except Exception as e:
    logger.error("予期しないエラー", exc_info=True, extra={"session_id": session_id})
    message = error_handler.handle_unexpected_error(e)
    print(message)
    continue
```

---

### 6.2 各種エラーの処理例

```python
from pydantic import ValidationError
from exceptions import ModelThrottledException

# APIレート制限
try:
    response = call_bedrock_api(prompt)
except ModelThrottledException as e:
    logger.warning("APIレート制限", extra={"session_id": session_id})
    message = error_handler.handle_throttling_error(e)
    print(message)

# バリデーションエラー
try:
    data = ApplicationModel(**input_data)
except ValidationError as e:
    logger.warning("バリデーション失敗", extra={"session_id": session_id})
    message = error_handler.handle_validation_error(e)
    print(message)

# ファイル保存エラー
try:
    save_excel(filepath, data)
except (IOError, PermissionError) as e:
    logger.error("Excelファイル保存失敗", exc_info=True, extra={"session_id": session_id})
    message = error_handler.handle_file_save_error(e)
    print(message)
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **ログ出力は呼び出し元が実施**
   - ErrorHandler 内でログを出力してはならない。呼び出し元（エージェント・ツール）が ErrorHandler 呼び出し前にログを出力すること

2. **ステートレス設計**
   - `ErrorHandler` はインスタンス変数を持たない。セッション状態の更新は呼び出し元（エージェント）が `SessionManager` 経由で実施する

3. **技術的エラー詳細の隠蔽**
   - スタックトレース・内部エラーコード・ファイルパス等の技術情報をユーザー向けメッセージに含めない

---

### 7.2 パフォーマンス考慮事項

1. **ステートレス設計によるオーバーヘッドなし**
   - インスタンス変数を持たないためメモリオーバーヘッドが最小

---

### 7.3 セキュリティ考慮事項

1. **技術的エラー詳細の隠蔽**
   - スタックトレース・内部エラーコード・ファイルパス等の技術情報をユーザー向けメッセージに含めない

---

## 8. 依存関係

### 8.1 外部ライブラリ
- なし（ErrorHandler 自身は logging を使用しない）

### 8.2 内部モジュール
- なし（ErrorHandler はシステム横断的コンポーネントのため内部モジュールに依存しない）

---

## 9. テスト観点

### 9.1 機能テスト（正常系）
- handle_throttling_error: `ModelThrottledException` を渡す → `str` が返却されること
  - **入力**: `error=ModelThrottledException(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_max_tokens_error: `MaxTokensReachedException` を渡す → `str` が返却されること
  - **入力**: `error=MaxTokensReachedException(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_context_window_error: `ContextWindowOverflowException` を渡す → `str` が返却されること
  - **入力**: `error=ContextWindowOverflowException(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_fare_data_error: `FileNotFoundError` を渡す → `str` が返却されること
  - **入力**: `error=FileNotFoundError(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_calculation_error: `Exception` を渡す → `str` が返却されること
  - **入力**: `error=Exception("計算エラー")`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_file_save_error: `IOError` を渡す → `str` が返却されること
  - **入力**: `error=IOError(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_file_save_error: `PermissionError` を渡す → `str` が返却されること
  - **入力**: `error=PermissionError(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_validation_error: `ValidationError` を渡す → `str` が返却されること
  - **入力**: `error=ValidationError(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_keyboard_interrupt: `KeyboardInterrupt` を渡す → `str` が返却されること
  - **入力**: `error=KeyboardInterrupt()`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_loop_limit_error: `LoopLimitError` を渡す → `str` が返却されること
  - **入力**: `error=LoopLimitError(...)`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_runtime_error: `RuntimeError` を渡す → `str` が返却されること
  - **入力**: `error=RuntimeError("実行時エラー")`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される
- handle_unexpected_error: `Exception` を渡す → `str` が返却されること
  - **入力**: `error=Exception("予期しないエラー")`
  - **期待結果**: ユーザー向け日本語メッセージ文字列（str）が返される

### 9.2 非機能テスト
- 全メソッドにおいて、ログ出力が行われないこと（ErrorHandler 内でログが呼ばれないこと）
- 全メソッドにおいて、例外が再 raise されないこと（メッセージ文字列が返却されること）

### 9.3 境界値テスト
- handle_unexpected_error: いかなる例外クラスを渡しても `str` が返却されること
  - **期待結果**: 例外の型にかかわらず日本語メッセージ文字列が返される

---

## 10. 設定値

### 10.1 定数値
- レート制限メッセージ: `"現在、システムへのリクエストが集中しています。しばらく経ってから再度お試しください。"`
- 最大トークンメッセージ: `"入力内容が長すぎます。内容を分割して再度お試しください。"`
- コンテキスト超過メッセージ: `"会話履歴が上限に達しました。'reset' コマンドで最初からやり直してください。"`
- 運賃データエラーメッセージ: `"交通費データの読み込みに失敗しました。担当部門にお問い合わせください。"`
- 計算エラーメッセージ: `"交通費の計算中にエラーが発生しました。手動で金額を入力してください。"`
- ファイル保存エラーメッセージ: `"申請書ファイルの保存に失敗しました。担当部門にお問い合わせください。"`
- バリデーションエラーメッセージ: `"入力内容に不備があります。必須項目をご確認の上、再度お試しください。"`
- 中断メッセージ: `"申請処理を中断しました。またのご利用をお待ちしております。"`
- ループ上限メッセージ: `"処理の繰り返し回数が上限に達しました。しばらく経ってから再度お試しください。"`
- 実行時エラーメッセージ: `"申請処理中にエラーが発生しました。担当部門にお問い合わせください。"`
- 予期しないエラーメッセージ: `"予期しないエラーが発生しました。担当部門にお問い合わせください。"`

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-07-03 | 1.0 | 新フォーマットで作成 |
| 2026-07-03 | 2.0 | ErrorHandler の責務を「ユーザー向けメッセージ文字列の生成と返却のみ」に縮小する全面再設計。ログ出力・セッション状態更新を非責務化し、メソッドを11個に再構成 |
