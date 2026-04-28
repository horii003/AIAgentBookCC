# ErrorHandler 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 2章（ErrorHandlerの位置づけ・主要メソッド）
> - artifacts/04_basic-design/outputs/ErrorHandler基本設計書.md 5章（マルチエージェント連携時の扱い）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針・エラー分類）
> - artifacts/03_system-design/outputs/実行制御方針.md（ループ制御・承認制御の方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

全エージェント（AG-001/AG-002/AG-003）・全ツール（TOOL-001/TOOL-002）から委譲された例外を受け取り、ユーザー向けメッセージ文字列を生成して返すクラス。`handlers/error_handler.py` に実装する。

### 1.2 主要な責務

1. **ユーザー向けメッセージ文字列の生成と返却**: 例外オブジェクトを受け取り、例外種別に応じた日本語メッセージを生成して文字列として返す

### 1.3 非責務

- **ログ出力**: ログ出力は呼び出し元モジュール（各エージェント・各ツール）が ErrorHandler 呼び出し**前**に実施する。ErrorHandler 自身はログ出力を行わない
- **セッション状態の更新**: SessionManager の呼び出し・セッション状態変更は行わない
- **例外の検知**: エージェント AG-001/AG-002/AG-003 またはツール TOOL-001/TOOL-002 が担当
- **継続可否判定・フロー制御**: 呼び出し元が担当
- **ビジネスロジックの実行**: 申請期限チェック・上長承認判定等はエージェントが担当

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`ErrorHandler`

#### 説明
エージェント・ツールから委譲された例外を受け取り、ユーザー向けメッセージ文字列を生成して返すハンドラークラス。`handlers/error_handler.py` に実装する。ログ出力・セッション状態更新は行わない。

---

### 2.2 初期化

#### `__init__(self)`
引数なしで初期化する。インスタンス変数は持たない。

**引数**: なし

**インスタンス変数**: なし

---

### 2.3 主要メソッド

#### 2.3.1 handle_throttling_error

##### 説明
APIレート制限（ModelThrottledException）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`ModelThrottledException`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. APIレート制限到達を示すメッセージ文字列を生成して返す

---

#### 2.3.2 handle_max_tokens_error

##### 説明
最大トークン数到達（MaxTokensReachedException）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`MaxTokensReachedException`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 処理テキスト量の上限到達を示すメッセージ文字列を生成して返す

---

#### 2.3.3 handle_context_window_error

##### 説明
コンテキストウィンドウ超過（ContextWindowOverflowException）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`ContextWindowOverflowException`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 会話長超過を示すメッセージ文字列を生成して返す

---

#### 2.3.4 handle_fare_data_error

##### 説明
運賃データ読み込み失敗（FileNotFoundError / Exception）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`FileNotFoundError` または `Exception`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 運賃データ読み込み失敗を示すメッセージ文字列を生成して返す

---

#### 2.3.5 handle_calculation_error

##### 説明
運賃計算失敗（Exception）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`Exception`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 運賃計算失敗を示すメッセージ文字列を生成して返す

---

#### 2.3.6 handle_file_save_error

##### 説明
Excelファイル保存失敗（IOError / PermissionError / Exception）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`IOError` または `PermissionError` または `Exception`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. ファイル生成失敗を示すメッセージ文字列を生成して返す

---

#### 2.3.7 handle_validation_error

##### 説明
Pydantic ValidationError発生時にユーザー向けバリデーションエラーメッセージを生成して返す。

##### 引数
- `e` (`ValidationError`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けバリデーションエラーメッセージ

##### 処理内容
1. `e.errors()` からエラーメッセージを取得して返す

---

#### 2.3.8 handle_keyboard_interrupt

##### 説明
ユーザーによる中断（KeyboardInterrupt）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`KeyboardInterrupt`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 処理中断を示すメッセージ文字列を生成して返す

---

#### 2.3.9 handle_loop_limit_error

##### 説明
ループ上限到達（LoopLimitError）発生時にユーザー向けメッセージ文字列を生成して返す。LoopLimitError は `handlers/exceptions.py` で定義されるカスタム例外クラスであり、`current_iteration`・`max_iterations`・`agent_name` の3フィールドを保持する。

##### 引数
- `e` (`LoopLimitError`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. ループ上限到達を示すメッセージ文字列 `"処理が複雑すぎるため終了します。"` を返す

---

#### 2.3.10 handle_runtime_error

##### 説明
その他の実行時エラー（RuntimeError）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`RuntimeError`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 実行時エラーを示すメッセージ文字列を生成して返す

---

#### 2.3.11 handle_unexpected_error

##### 説明
予期しないエラー（Exception）発生時にユーザー向けメッセージ文字列を生成して返す。

##### 引数
- `e` (`Exception`): 発生した例外オブジェクト

##### 戻り値
- `str`: ユーザー向けメッセージ

##### 処理内容
1. 予期しないエラーを示すメッセージ文字列を生成して返す

---

## 3. ビジネスロジック

### 3.1 例外種別とメッセージの対応

ErrorHandler の各メソッドは、受け取った例外オブジェクトに応じて対応するメッセージ文字列を生成して返す。

```
例外発生（エージェント/ツールが検知）
  ↓
呼び出し元がログ出力を実施（ErrorHandler 呼び出し前）
  ↓
ErrorHandler の対応メソッドへ委譲
  ↓
例外種別に応じたユーザー向けメッセージ文字列を返す
  ↓
呼び出し元がメッセージを受け取りセッション状態を更新・ユーザーへ提示
```

### 3.2 ログ出力の責務

**ログ出力は呼び出し元（各エージェント・各ツール）の責務である。**

呼び出し元は ErrorHandler を呼び出す**前**に、適切なログレベルでログを記録する。ErrorHandler はメッセージ文字列を返すだけであり、logging モジュールの呼び出しは一切行わない。

---

## 4. エラーハンドリング

### 4.1 各メソッドの対象例外とメッセージ

| メソッド名 | 対象例外 | 用途 | 返却メッセージ |
|-----------|---------|------|--------------|
| `handle_throttling_error` | `ModelThrottledException` | APIレート制限 | `"申し訳ありません。APIの利用制限に達しました。しばらく時間をおいて再度お試しください。"` |
| `handle_max_tokens_error` | `MaxTokensReachedException` | 最大トークン数到達 | `"申し訳ありません。処理できるテキスト量の上限に達しました。入力内容を分割してお試しください。"` |
| `handle_context_window_error` | `ContextWindowOverflowException` | コンテキストウィンドウ超過 | `"申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"` |
| `handle_fare_data_error` | `FileNotFoundError` / `Exception` | 運賃データ読み込み失敗 | `"申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"` |
| `handle_calculation_error` | `Exception` | 運賃計算失敗 | `"申し訳ありません。運賃の計算に失敗しました。交通費を手動で入力してください。"` |
| `handle_file_save_error` | `IOError` / `PermissionError` / `Exception` | Excelファイル保存失敗 | `"申し訳ありません。ファイルの生成に失敗しました。システム管理者にご連絡ください。"` |
| `handle_validation_error` | `ValidationError` | Pydanticバリデーション失敗 | `e.errors()` から取得したメッセージを返す |
| `handle_keyboard_interrupt` | `KeyboardInterrupt` | ユーザーによる中断 | `"処理を中断しました。ご利用ありがとうございました。"` |
| `handle_loop_limit_error` | `LoopLimitError` | ループ上限到達 | `"処理が複雑すぎるため終了します。"` |
| `handle_runtime_error` | `RuntimeError` | その他の実行時エラー | `"申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"` |
| `handle_unexpected_error` | `Exception` | 予期しないエラー | `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"` |

---

## 5. ログ出力

**ErrorHandler 自身はログ出力を行わない。**

ログ出力は呼び出し元モジュール（各エージェント・各ツール）の責務である。呼び出し元は ErrorHandler を呼び出す**前**に、適切なログレベル（ERROR / CRITICAL / WARNING 等）でログを記録すること。

ErrorHandler は `logging` モジュールに依存しない。

---

## 6. 使用例

### 6.1 基本的な使用方法

```python
import logging
from handlers.error_handler import ErrorHandler

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()

# APIレート制限エラー
try:
    response = call_llm_api()
except ModelThrottledException as e:
    logger.error("[THROTTLING] API rate limit reached: %s", str(e))  # 呼び出し元がログ出力
    message = error_handler.handle_throttling_error(e)
    return message

# Pydantic バリデーションエラー
try:
    validated = UserInputText(content=user_input)
except ValidationError as e:
    logger.error("[VALIDATION] Validation failed: %s", str(e))  # 呼び出し元がログ出力
    message = error_handler.handle_validation_error(e)
    return message

# 運賃データ読み込みエラー
try:
    with open("data/train_fares.json") as f:
        data = json.load(f)
except FileNotFoundError as e:
    logger.error("[FARE_DATA] Fare data not found: %s", str(e))  # 呼び出し元がログ出力
    message = error_handler.handle_fare_data_error(e)
    return message
```

### 6.2 エージェントツール関数でのエラーハンドリング

```python
import logging
from handlers.error_handler import ErrorHandler
from handlers.exceptions import LoopLimitError

logger = logging.getLogger(__name__)

@tool(context=True)
def travel_application_agent_tool(query: str, tool_context: ToolContext) -> str:
    error_handler = ErrorHandler()
    try:
        # ... エージェント呼び出し ...
        pass
    except LoopLimitError as e:
        logger.error(
            "[LOOP_LIMIT] Loop limit reached: agent=%s, iteration=%d/%d",
            e.agent_name, e.current_iteration, e.max_iterations
        )  # 呼び出し元がログ出力
        return error_handler.handle_loop_limit_error(e)
    except KeyboardInterrupt as e:
        logger.warning("[KEYBOARD_INTERRUPT] Processing interrupted by user.")
        return error_handler.handle_keyboard_interrupt(e)
    except Exception as e:
        logger.critical("[UNEXPECTED] Unexpected error: %s", str(e), exc_info=True)
        return error_handler.handle_unexpected_error(e)
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **ログ出力は呼び出し元の責務**
   - ErrorHandler はログ出力を一切行わない
   - 各エージェント・各ツールは ErrorHandler を呼び出す**前**に、適切なログレベルでログを記録すること
   - スタックトレースが必要な場合（予期しないエラー・システム障害等）は、呼び出し元で `exc_info=True` を指定してログを記録すること

2. **セッション状態更新は呼び出し元の責務**
   - ErrorHandler は SessionManager を呼び出さない
   - セッション状態の更新・フロー制御は呼び出し元が担当する

3. **LoopLimitError のカスタム例外クラス**
   - `LoopLimitError` は `handlers/exceptions.py` で定義するカスタム例外クラスである
   - `current_iteration`・`max_iterations`・`agent_name` の3フィールドを保持する

4. **単一インスタンス利用**
   - 各エージェント・ツールが ErrorHandler を個別にインスタンス化して使用する
   - シングルトンパターンは不要（CLIの逐次処理のためスレッドセーフ要件なし）

5. **ユーザーメッセージへの技術的詳細の非掲載**
   - スタックトレース・SDK内部エラー詳細はユーザー向けメッセージに含めない

---

### 7.2 パフォーマンス考慮事項

1. **メッセージ生成のみのため影響は最小限**
   - ErrorHandler はメッセージ文字列の生成と返却のみを行うため、正常フローのパフォーマンスへの影響はない

---

### 7.3 セキュリティ考慮事項

1. **スタックトレースの隠蔽**
   - スタックトレース・SDK内部エラーは呼び出し元のログにのみ記録する
   - ユーザー向けメッセージには技術的詳細を含めない

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `pydantic`:
  - `ValidationError`: バリデーションエラークラス（`handle_validation_error` の引数型）

### 8.2 内部モジュール
- `handlers/error_handler.py`: 本クラスの実装ファイル（他コンポーネントからインポートされる）
- `handlers/exceptions.py`: `LoopLimitError` カスタム例外クラスの定義ファイル（LoopControlHook の依存モジュールでもある）

---

## 9. テスト観点

### 9.1 機能テスト（メッセージ生成の正確性）

- `handle_throttling_error()` を呼び出したとき、APIレート制限メッセージが返ること
  - **入力**: `ModelThrottledException` インスタンス
  - **期待結果**: `"申し訳ありません。APIの利用制限に達しました。しばらく時間をおいて再度お試しください。"`
- `handle_max_tokens_error()` を呼び出したとき、トークン上限メッセージが返ること
  - **入力**: `MaxTokensReachedException` インスタンス
  - **期待結果**: `"申し訳ありません。処理できるテキスト量の上限に達しました。入力内容を分割してお試しください。"`
- `handle_context_window_error()` を呼び出したとき、会話長超過メッセージが返ること
  - **入力**: `ContextWindowOverflowException` インスタンス
  - **期待結果**: `"申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"`
- `handle_fare_data_error()` を呼び出したとき、運賃データ読み込み失敗メッセージが返ること
  - **入力**: `FileNotFoundError` インスタンス
  - **期待結果**: `"申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"`
- `handle_calculation_error()` を呼び出したとき、運賃計算失敗メッセージが返ること
  - **入力**: `Exception` インスタンス
  - **期待結果**: `"申し訳ありません。運賃の計算に失敗しました。交通費を手動で入力してください。"`
- `handle_file_save_error()` を呼び出したとき、ファイル生成失敗メッセージが返ること
  - **入力**: `IOError` インスタンス
  - **期待結果**: `"申し訳ありません。ファイルの生成に失敗しました。システム管理者にご連絡ください。"`
- `handle_validation_error()` を呼び出したとき、`e.errors()` から取得したメッセージが返ること
  - **入力**: `ValidationError` インスタンス
  - **期待結果**: `e.errors()` の内容を含むメッセージ文字列
- `handle_keyboard_interrupt()` を呼び出したとき、中断メッセージが返ること
  - **入力**: `KeyboardInterrupt` インスタンス
  - **期待結果**: `"処理を中断しました。ご利用ありがとうございました。"`
- `handle_loop_limit_error()` を呼び出したとき、ループ制限到達メッセージが返ること
  - **入力**: `LoopLimitError` インスタンス
  - **期待結果**: `"処理が複雑すぎるため終了します。"`
- `handle_runtime_error()` を呼び出したとき、実行時エラーメッセージが返ること
  - **入力**: `RuntimeError` インスタンス
  - **期待結果**: `"申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"`
- `handle_unexpected_error()` を呼び出したとき、予期しないエラーメッセージが返ること
  - **入力**: `Exception` インスタンス
  - **期待結果**: `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"`

### 9.2 非テスト対象

- **ログ出力**: ErrorHandler はログ出力を行わないため、ログ出力のテストは対象外。ログ出力のテストは呼び出し元モジュールのテストで実施する

### 9.3 統合テスト

- TOOL-001の電車区間検索で経路未登録時、AG-002が呼び出し元でログを記録した上で ErrorHandler を経由してユーザー向け手動入力促しメッセージを提示すること
  - **テスト対象**: TOOL-001 → AG-002 → ErrorHandler
  - **期待結果**: 手動入力促しメッセージがユーザーに表示される
- TOOL-002のファイル保存失敗時、呼び出し元でログを記録した上で ErrorHandler を経由してファイル生成失敗メッセージが返ること
  - **テスト対象**: TOOL-002 → AG-003 → ErrorHandler
  - **期待結果**: ファイル生成失敗メッセージがユーザーに表示される

---

## 10. 設定値

### 10.1 エラーメッセージ定数

- `handle_throttling_error` メッセージ: `"申し訳ありません。APIの利用制限に達しました。しばらく時間をおいて再度お試しください。"`
- `handle_max_tokens_error` メッセージ: `"申し訳ありません。処理できるテキスト量の上限に達しました。入力内容を分割してお試しください。"`
- `handle_context_window_error` メッセージ: `"申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"`
- `handle_fare_data_error` メッセージ: `"申し訳ありません。運賃データの読み込みに失敗しました。システム管理者にご連絡ください。"`
- `handle_calculation_error` メッセージ: `"申し訳ありません。運賃の計算に失敗しました。交通費を手動で入力してください。"`
- `handle_file_save_error` メッセージ: `"申し訳ありません。ファイルの生成に失敗しました。システム管理者にご連絡ください。"`
- `handle_keyboard_interrupt` メッセージ: `"処理を中断しました。ご利用ありがとうございました。"`
- `handle_loop_limit_error` メッセージ: `"処理が複雑すぎるため終了します。"`
- `handle_runtime_error` メッセージ: `"申し訳ありません。処理中にエラーが発生しました。システム管理者にご連絡ください。"`
- `handle_unexpected_error` メッセージ: `"申し訳ありません。予期しないエラーが発生しました。システム管理者にご連絡ください。"`

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-04-28 | 2.0 | 新フォーマットで作成 |
| 2026-04-28 | 3.0 | ErrorHandler の責務をユーザー向けメッセージ文字列の生成と返却のみに全面改訂。ログ出力・セッション状態更新を非責務化し呼び出し元の責務として明記。コンストラクタの引数・インスタンス変数・logging 依存を廃止。メソッドを11本（handle_throttling_error / handle_max_tokens_error / handle_context_window_error / handle_fare_data_error / handle_calculation_error / handle_file_save_error / handle_validation_error / handle_keyboard_interrupt / handle_loop_limit_error / handle_runtime_error / handle_unexpected_error）に再定義。全メソッドの引数を例外オブジェクトのみ・戻り値を str のみに統一。LoopLimitError を handlers/exceptions.py のカスタム例外クラスとして定義。 |
