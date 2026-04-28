
# スケルトン: エラーハンドリング (handlers/error_handler.py)

## 概要

アプリケーション全体のエラーハンドリングとログ出力を一元管理するモジュール。
業務ドメインに応じてエラーハンドリングメソッドを追加する。

## ファイル配置

`handlers/error_handler.py`

## スケルトンコード

```python
"""エラーハンドリング関連のモジュール"""
import logging
from datetime import datetime
from typing import Optional


class LoopLimitError(RuntimeError):
    """
    エージェントReActループの制限エラー

    エージェントのループが最大回数に達した場合に発生します。
    """

    def __init__(self, current_iteration: int, max_iterations: int, agent_name: str):
        """
        初期化

        Args:
            current_iteration: 現在のループ回数
            max_iterations: 最大ループ回数
            agent_name: エージェント名
        """
        self.current_iteration = current_iteration
        self.max_iterations = max_iterations
        self.agent_name = agent_name
        # TODO: 詳細設計書に従い実装
        # - エージェント名とループ回数情報を含むメッセージを生成
        # - 親クラスの__init__にメッセージを渡す
        pass


class ErrorHandler:
    """エラーハンドリング + ログ出力ヘルパー関数クラス"""

    def __init__(self):
        """
        エラーハンドラーの初期化

        Note:
            ログ設定はmain.pyで実施済み
        """
        self.logger = None         # TODO: 詳細設計書に従い実装

    # ============ ログ出力メソッド ============

    def log_debug(self, message: str, context: Optional[dict] = None):
        """
        デバッグログを出力

        Args:
            message: ログメッセージ
            context: コンテキスト情報（オプション）
        """
        # TODO: 詳細設計書に従い実装
        # - contextの有無で出力形式を切り替え
        pass

    def log_info(self, message: str, context: Optional[dict] = None):
        """
        情報ログを出力

        Args:
            message: ログメッセージ
            context: コンテキスト情報（オプション）
        """
        # TODO: 詳細設計書に従い実装
        pass

    def log_warning(self, message: str, context: Optional[dict] = None):
        """
        警告ログを出力

        Args:
            message: ログメッセージ
            context: コンテキスト情報（オプション）
        """
        # TODO: 詳細設計書に従い実装
        pass

    def log_error(self, error_type: str, message: str, context: Optional[dict] = None, exc_info: bool = False):
        """
        エラーログを出力

        Args:
            error_type: エラータイプ
            message: エラーメッセージ
            context: エラーコンテキスト（オプション）
            exc_info: スタックトレースをログに含めるか
        """
        # TODO: 詳細設計書に従い実装
        # - error_typeをメッセージに付加
        # - exc_infoに応じてスタックトレースを含める
        pass

    def log_critical(self, message: str, context: Optional[dict] = None, exc_info: bool = False):
        """
        重大なエラーログを出力

        Args:
            message: ログメッセージ
            context: コンテキスト情報（オプション）
            exc_info: スタックトレースをログに含めるか
        """
        # TODO: 詳細設計書に従い実装
        pass

    # ============ 共通エラーハンドリングメソッド ============

    def handle_bedrock_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """
        Bedrock接続エラーの処理

        Args:
            error: エラーオブジェクト
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - エラーメッセージのログ出力
        # - AWS認証・接続・権限確認を促すメッセージの生成
        # - メッセージの返却
        pass

    def handle_data_load_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """
        データ読み込みエラーの処理

        Args:
            error: エラーオブジェクト
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - スタックトレース付きエラーログ出力
        # - FileNotFoundErrorかどうかで分岐
        # - エラー種別に応じたメッセージ生成
        # - メッセージの返却
        pass

    def handle_processing_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """
        処理エラー（計算、変換等）の処理

        Args:
            error: エラーオブジェクト
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - スタックトレース付きエラーログ出力
        # - 入力確認を促すメッセージ生成
        # - メッセージの返却
        pass

    def handle_file_save_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """
        ファイル保存エラーの処理

        Args:
            error: エラーオブジェクト
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - エラーログ出力
        # - 書き込み権限・ディスク容量確認を促すメッセージ生成
        # - メッセージの返却
        pass

    def handle_validation_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """
        入力検証エラーの処理

        Args:
            error: エラーオブジェクト
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - スタックトレース付きエラーログ出力
        # - 再入力を促すメッセージ生成
        # - メッセージの返却
        pass

    def handle_keyboard_interrupt(self, context: Optional[dict] = None) -> str:
        """
        キーボード中断（Ctrl+C）の処理

        Args:
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - INFOレベルでログ出力
        # - 終了メッセージの返却
        pass

    def handle_loop_limit_error(self, error: LoopLimitError, context: Optional[dict] = None) -> str:
        """
        エージェントループ制限エラーの処理

        Args:
            error: LoopLimitErrorオブジェクト
            context: エラーコンテキスト

        Returns:
            str: 構造化されたエラーレスポンス
        """
        # TODO: 詳細設計書に従い実装
        # - エラーメッセージのログ出力
        # - エージェント名に基づく具体的アドバイスの生成
        # - タスク分割・具体的指示・不要情報削除の提案メッセージ生成
        # - メッセージの返却
        pass

    def handle_runtime_error(self, error: Exception, agent_name: str, context: Optional[dict] = None) -> str:
        """
        RuntimeErrorの処理

        Args:
            error: エラーオブジェクト
            agent_name: エージェント名
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - エラーメッセージ（先頭100文字）をWARNINGレベルでログ出力
        # - 再試行を促すメッセージ生成
        # - メッセージの返却
        pass

    def handle_unexpected_error(self, error: Exception, agent_name: str, context: Optional[dict] = None) -> str:
        """
        予期しないエラーの処理

        Args:
            error: エラーオブジェクト
            agent_name: エージェント名
            context: エラーコンテキスト

        Returns:
            str: ユーザー向けエラーメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - スタックトレース付きERRORレベルログ出力
        # - システム再起動・管理者連絡を促すメッセージ生成
        # - メッセージの返却
        pass

    # ============ ドメイン固有エラーハンドリングメソッド ============
    # 業務ドメインに応じてエラーハンドリングメソッドを追加する

    # TODO: 業務ドメイン固有のエラーハンドラを追加
    # 例:
    # def handle_{domain}_error(self, error: Exception, context: Optional[dict] = None) -> str:
    #     """
    #     {ドメイン固有}エラーの処理
    #
    #     Args:
    #         error: エラーオブジェクト
    #         context: エラーコンテキスト
    #
    #     Returns:
    #         str: ユーザー向けエラーメッセージ
    #     """
    #     pass
```

## カスタマイズガイド

1. **共通エラーハンドラ**: `handle_bedrock_error`, `handle_data_load_error`, `handle_validation_error` 等は全プロジェクト共通で使用する
2. **ドメイン固有エラーハンドラ**: 業務要件に応じて `handle_{domain}_error()` メソッドを追加する
3. **エラーメッセージ**: ユーザー向けメッセージは全て日本語で、技術的な詳細を含めない
4. **ログ出力**: 技術的な詳細はログに出力し、ユーザーには簡潔なメッセージを返す
