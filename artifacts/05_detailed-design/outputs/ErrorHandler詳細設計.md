---
version: "1.1.0"
last_updated: "2026-05-02"
updated_by: ""
---

# ErrorHandler 詳細設計書

> **参照元（基本設計資料）:**
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 2章（ErrorHandlerの目的・役割定義・主要メソッド）
> - artifacts/04_basic-design/outputs/ハンドラー基本設計書.md 5章（ハンドラー間の連携設計）

> **参照元（システム設計資料）:**
> - artifacts/03_system-design/outputs/例外処理方針.md（例外処理の全体方針・エラー分類 EX-01〜EX-08）
> - artifacts/03_system-design/outputs/実行制御方針.md（リトライ・エスカレーションの方針）
> - artifacts/03_system-design/outputs/共通設定方針.md（ハンドラーの共通設定）

## 1. 概要

### 1.1 コンポーネントの目的

各エージェントおよびツールが catch した例外を受け取り、エラー種別に対応したユーザー向け日本語メッセージを返す。各エージェントが個別の except ブロックで直接呼び出す11個の専用メソッドを提供する。

### 1.2 主要な責務

1. **ユーザーメッセージ生成**: 技術詳細を隠した日本語メッセージを返す
2. **エラー種別ごとの専用メソッド提供**: 呼び出し元（エージェント/ツール）がエラー種別を把握した上で適切なメソッドを選択して呼び出す

### 1.3 非責務

- **ログ出力**: 各エージェントおよびツールが担当する（ErrorHandler の責務外）
- **セッション状態の更新**: 各エージェントおよび SessionManager（SM-001）が担当する
- **例外分類ロジック**: 呼び出し元の except ブロックで分類する（ErrorHandler は受け取ったメソッドに対応したメッセージのみ返す）
- **バリデーション実装**: Pydanticモデル（models/data_models.py）が担当

---

## 2. 設計詳細

### 2.1 クラス基本情報

#### クラス名
`ErrorHandler`

#### 説明
エラー種別ごとに専用の `handle_xxx` メソッドを持つハンドラークラス。各メソッドは例外オブジェクトのみを受け取り、ユーザー向け日本語メッセージ文字列を返す。ログ出力・セッション更新・エスカレーション判定は行わない。

---

### 2.2 初期化

#### `__init__(self)`
インスタンス変数なし。状態を持たないステートレスなクラス。

**インスタンス変数**:
- なし

---

### 2.3 主要メソッド

#### 2.3.1 `handle_throttling_error`

##### 説明
API スロットリングエラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): スロットリング例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. スロットリングエラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。現在システムが混雑しています。しばらく経ってから再度お試しください。"
```

---

#### 2.3.2 `handle_max_tokens_error`

##### 説明
LLM の最大トークン超過エラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): 最大トークン超過例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. 最大トークン超過エラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。入力内容が長すぎます。内容を短くして再度お試しください。"
```

---

#### 2.3.3 `handle_context_window_error`

##### 説明
コンテキストウィンドウ超過エラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): コンテキストウィンドウ超過例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. コンテキストウィンドウ超過エラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"
```

---

#### 2.3.4 `handle_fare_data_error`

##### 説明
交通費運賃データ（train_routes.json / fixed_fares.json）の読み込みエラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): 運賃データ読み込み例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. 運賃データ読み込みエラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。運賃データの読み込みに失敗しました。担当部門（管理部）にお問い合わせください。"
```

---

#### 2.3.5 `handle_calculation_error`

##### 説明
交通費計算処理エラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): 計算処理例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. 計算処理エラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。運賃計算中にエラーが発生しました。区間情報を確認して再度お試しください。"
```

---

#### 2.3.6 `handle_file_save_error`

##### 説明
申請書ファイル保存エラー発生時のメッセージを返す。

##### 引数
- `e` (Exception): ファイル保存例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. ファイル保存エラーに対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。申請書の保存中にエラーが発生しました。担当部門（管理部）にお問い合わせください。"
```

---

#### 2.3.7 `handle_validation_error`

##### 説明
Pydantic ValidationError 発生時のメッセージを返す。入力例外（EX-01）および業務ルール違反（EX-03: 申請期限超過）の両方に対応する。

##### 引数
- `e` (ValidationError): Pydantic の ValidationError オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. `str(e)` に `"90日"` または `"申請期限"` が含まれる場合:
   - 申請期限超過メッセージを返す（EX-03）
2. それ以外の場合:
   - バリデーションエラーメッセージを返す（EX-01）

##### 返却メッセージ
- EX-03（申請期限超過）: `"申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"`
- EX-01（入力例外）: `"入力内容に問題があります。内容を確認して再度お試しください。"`

---

#### 2.3.8 `handle_keyboard_interrupt`

##### 説明
KeyboardInterrupt 発生時のメッセージを返す（ユーザーによる強制終了）。

##### 引数
- `e` (KeyboardInterrupt): KeyboardInterrupt オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. KeyboardInterrupt に対応したメッセージを返す

##### 返却メッセージ
```
"処理を中断しました。またいつでもご相談ください。"
```

---

#### 2.3.9 `handle_loop_limit_error`

##### 説明
LoopLimitError 発生時のメッセージを返す（EX-08: 想定外）。

##### 引数
- `e` (LoopLimitError): LoopControlHook が raise する LoopLimitError オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. LoopLimitError に対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
```

---

#### 2.3.10 `handle_runtime_error`

##### 説明
RuntimeError（LoopLimitError 以外）発生時のメッセージを返す（EX-07: システム障害）。

##### 引数
- `e` (RuntimeError): RuntimeError オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. RuntimeError に対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。システムエラーが発生しました。しばらく経ってから再度お試しください。"
```

---

#### 2.3.11 `handle_unexpected_error`

##### 説明
未分類の Exception 発生時のメッセージを返す（EX-08: 想定外）。

##### 引数
- `e` (Exception): 未分類の例外オブジェクト

##### 戻り値
- `str`: ユーザー向け日本語メッセージ

##### 処理内容
1. 想定外例外に対応したメッセージを返す

##### 返却メッセージ
```
"申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"
```

---

## 3. ビジネスロジック

### 3.1 メソッドと例外種別の対応

#### 対応表

| メソッド | 対象例外 | EX分類 | 返却メッセージ概要 |
|---------|---------|--------|-----------------|
| `handle_throttling_error` | ThrottlingException等 | EX-07 | システム混雑、しばらく後に再試行 |
| `handle_max_tokens_error` | MaxTokensException等 | EX-07 | 入力が長すぎる |
| `handle_context_window_error` | ContextWindowException等 | EX-07 | 会話が長すぎる、最初からやり直し |
| `handle_fare_data_error` | ValueError（運賃データなし）等 | EX-04 | 運賃データ読み込み失敗、管理部問い合わせ |
| `handle_calculation_error` | ValueError（計算エラー）等 | EX-01 | 運賃計算エラー、区間情報確認 |
| `handle_file_save_error` | IOError/PermissionError/Exception | EX-04 | 申請書保存エラー、管理部問い合わせ |
| `handle_validation_error` | ValidationError | EX-01/EX-03 | 入力問題 or 申請期限超過 |
| `handle_keyboard_interrupt` | KeyboardInterrupt | — | 処理中断 |
| `handle_loop_limit_error` | LoopLimitError | EX-08 | 予期しないエラー、管理部問い合わせ or やり直し |
| `handle_runtime_error` | RuntimeError | EX-07 | システムエラー、しばらく後に再試行 |
| `handle_unexpected_error` | Exception | EX-08 | 予期しないエラー、管理部問い合わせ or やり直し |

---

### 3.2 呼び出しパターン

#### 各エージェントでの使用パターン

```python
error_handler = ErrorHandler()

try:
    response = agent(user_input, invocation_state=state)
except ThrottlingException as e:
    logger.warning(f"[ERR-xxx] スロットリング: request_id={request_id}")
    return error_handler.handle_throttling_error(e)
except MaxTokensException as e:
    logger.warning(f"[ERR-xxx] トークン超過: request_id={request_id}")
    return error_handler.handle_max_tokens_error(e)
except ContextWindowException as e:
    logger.warning(f"[ERR-xxx] コンテキスト超過: request_id={request_id}")
    return error_handler.handle_context_window_error(e)
except LoopLimitError as e:
    logger.error(f"[ERR-008] ループ上限: request_id={request_id}, agent={e.agent_name}, count={e.current_iteration}")
    return error_handler.handle_loop_limit_error(e)
except RuntimeError as e:
    logger.error(f"[ERR-007] RuntimeError: request_id={request_id}")
    return error_handler.handle_runtime_error(e)
except Exception as e:
    logger.error(f"[ERR-008] 想定外例外: request_id={request_id}")
    return error_handler.handle_unexpected_error(e)
```

#### ツールからの使用パターン

```python
error_handler = ErrorHandler()

try:
    validated = TransportToolInput(...)
except ValidationError as e:
    return {"success": False, "message": error_handler.handle_validation_error(e)}
```

---

## 4. エラーハンドリング

### 4.1 ErrorHandler 自身のエラー

ErrorHandler のメソッドは例外を raise しない。例外が発生した場合は安全なデフォルトメッセージを返す設計とする。

---

## 5. ログ出力

ErrorHandler はログを出力しない。ログ出力は各エージェントおよびツールが担当する。

---

## 6. 使用例

### 6.1 エージェントからの使用例

```python
from handlers.error_handler import ErrorHandler
from handlers.loop_control_hook import LoopLimitError

error_handler = ErrorHandler()

try:
    response = agent(user_input, invocation_state=state)
except ThrottlingException as e:
    logger.warning(f"[ERR-xxx] スロットリング: request_id={state.get('request_id')}, query={user_input[:50]}")
    message = error_handler.handle_throttling_error(e)
    return message
except LoopLimitError as e:
    logger.error(f"[ERR-008] ループ上限: request_id={state.get('request_id')}, agent={e.agent_name}, count={e.current_iteration}/{e.max_iterations}")
    message = error_handler.handle_loop_limit_error(e)
    return message
except RuntimeError as e:
    logger.error(f"[ERR-007] RuntimeError: request_id={state.get('request_id')}, error={str(e)[:100]}")
    message = error_handler.handle_runtime_error(e)
    return message
except Exception as e:
    logger.error(f"[ERR-008] 想定外例外: request_id={state.get('request_id')}, error={str(e)[:100]}")
    message = error_handler.handle_unexpected_error(e)
    return message
```

### 6.2 ツールからの使用例

```python
from handlers.error_handler import ErrorHandler
from pydantic import ValidationError

error_handler = ErrorHandler()

try:
    validated = TransportToolInput(
        departure=departure,
        destination=destination,
        transportation_type=transportation_type,
        travel_date=travel_date,
        purpose=purpose,
    )
except ValidationError as e:
    message = error_handler.handle_validation_error(e)
    return {"success": False, "fare": 0, "calculation_basis": "", "message": message}
```

---

## 7. 補足情報

### 7.1 実装上の注意点

1. **ユーザーメッセージへの技術詳細非公開**
   - すべての `handle_xxx` メソッドは技術的なエラー詳細（スタックトレース、例外メッセージ）をユーザーメッセージに含めない。

2. **ログ出力の分離**
   - ErrorHandler はログを出力しない。呼び出し元（エージェント/ツール）が except ブロックで適切なログを出力した上で ErrorHandler のメソッドを呼び出す。これにより、ログのコンテキスト情報（request_id、query等）を呼び出し元が制御できる。

3. **ValidationError の EX-01/EX-03 分類**
   - `handle_validation_error` 内でメッセージ内容により分岐する（EX-01 と EX-03 の両方を1メソッドで処理）。

4. **ステートレス設計**
   - ErrorHandler はインスタンス変数を持たないステートレスなクラスとして実装する。アプリケーション起動時に1インスタンスを生成して再利用する。

---

### 7.2 パフォーマンス考慮事項

1. **メッセージ生成のオーバーヘッド**
   - すべてのメソッドは文字列リテラルを返すのみのため、処理時間は無視できるレベルである。

---

### 7.3 セキュリティ考慮事項

1. **個人情報の非公開**
   - ユーザーメッセージに個人情報（申請者名、金額等）を含めない。
   - 個人情報のマスキングログ出力は呼び出し元の責務とする（GRD-011）。

2. **スタックトレース非公開**
   - 例外の技術的詳細をユーザーメッセージに含めない。

---

## 8. 依存関係

### 8.1 外部ライブラリ
- `pydantic`: データバリデーション（v2系）
  - `ValidationError`: `handle_validation_error` の引数型

### 8.2 内部モジュール
- `handlers.loop_control_hook`: ループ制御フック
  - `LoopLimitError`: `handle_loop_limit_error` の引数型

---

## 9. テスト観点

### 9.1 機能テスト
- `handle_throttling_error(e)` が str 型を返すこと
  - **期待結果**: 日本語メッセージ文字列が返る
- `handle_validation_error(ValidationError(...))` が EX-01 メッセージを返すこと
  - **入力**: 通常の ValidationError
  - **期待結果**: `"入力内容に問題があります..."` を含む文字列
- `handle_validation_error(ValidationError("申請期限..."))` が EX-03 メッセージを返すこと
  - **入力**: "90日" を含む ValidationError
  - **期待結果**: `"申請期限（経費発生日から90日以内）を超過しています..."` を含む文字列
- `handle_loop_limit_error(LoopLimitError(...))` が EX-08 メッセージを返すこと
  - **期待結果**: `"予期しないエラーが発生しました..."` を含む文字列
- 全11メソッドが str 型を返すこと
  - **期待結果**: 各メソッドの戻り値が str 型

### 9.2 異常系テスト
- すべての `handle_xxx` メソッドでユーザーメッセージにスタックトレースが含まれないこと
  - **入力**: RuntimeError("Internal error details")
  - **期待結果**: `"Internal error details"` がユーザーメッセージに含まれない
- `handle_validation_error` で "申請期限" を含む ValidationError が EX-03 メッセージを返すこと
  - **境界値**: メッセージに "申請期限" を含む / 含まない

### 9.3 性能テスト（該当する場合のみ）
- 各 `handle_xxx` メソッドの応答時間が 1ms 以内であること
  - **測定指標**: 処理時間
  - **期待値**: 1ms以内

### 9.4 境界値テスト
- ValidationError のメッセージが "90日" を含む場合に EX-03 メッセージが返ること
  - **境界値**: メッセージ文字列に "90日" を含む / 含まない
  - **期待結果**: 含む → EX-03メッセージ、含まない → EX-01メッセージ

### 9.5 統合テスト
- 各エージェントが except ブロックで対応する `handle_xxx` を呼び出し、日本語メッセージが返ること
  - **テスト対象**: ErrorHandler + 各エージェント（AG-001/AG-002/AG-003）
  - **期待結果**: 例外種別に応じた日本語メッセージが返る

---

## 10. 設定値

### 10.1 返却メッセージ定数

| メソッド | メッセージ |
|---------|-----------|
| `handle_throttling_error` | `"申し訳ありません。現在システムが混雑しています。しばらく経ってから再度お試しください。"` |
| `handle_max_tokens_error` | `"申し訳ありません。入力内容が長すぎます。内容を短くして再度お試しください。"` |
| `handle_context_window_error` | `"申し訳ありません。会話が長くなりすぎました。最初からやり直してください。"` |
| `handle_fare_data_error` | `"申し訳ありません。運賃データの読み込みに失敗しました。担当部門（管理部）にお問い合わせください。"` |
| `handle_calculation_error` | `"申し訳ありません。運賃計算中にエラーが発生しました。区間情報を確認して再度お試しください。"` |
| `handle_file_save_error` | `"申し訳ありません。申請書の保存中にエラーが発生しました。担当部門（管理部）にお問い合わせください。"` |
| `handle_validation_error`（EX-01） | `"入力内容に問題があります。内容を確認して再度お試しください。"` |
| `handle_validation_error`（EX-03） | `"申請期限（経費発生日から90日以内）を超過しています。担当部門にご確認ください。"` |
| `handle_keyboard_interrupt` | `"処理を中断しました。またいつでもご相談ください。"` |
| `handle_loop_limit_error` | `"申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"` |
| `handle_runtime_error` | `"申し訳ありません。システムエラーが発生しました。しばらく経ってから再度お試しください。"` |
| `handle_unexpected_error` | `"申し訳ありません。予期しないエラーが発生しました。担当部門（管理部）にお問い合わせいただくか、最初からやり直してください。"` |

---

## 11. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-05-02 | 1.0 | 新フォーマットで初版作成 |
| 2026-05-02 | 1.1 | 修正7: クラス設計を全面改訂。汎用handle/classify/should_escalate構造を廃止し、11個の専用メソッド群に置換。ログ出力・セッション更新を各エージェントの責務に移管 |
