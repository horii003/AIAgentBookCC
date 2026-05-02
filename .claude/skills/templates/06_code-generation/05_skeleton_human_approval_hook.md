# スケルトン: Human-in-the-Loop承認フック (handlers/human_approval_hook.md)

## 概要

出力生成等の重要なツール実行前に人間の承認を求めるフック。
承認対象のツール名を業務ドメインに応じて設定する。

## ファイル配置

`handlers/human_approval_hook.py`

## スケルトンコード

```python
"""
Human-in-the-Loop承認フック

{対象ツール名}の実行前に人間の承認を求め、
修正要望があれば修正を実行するフック。
"""

from typing import Any
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent
from handlers.error_handler import ErrorHandler


class HumanApprovalHook(HookProvider):
    """
    指定ツール実行前に人間の承認を求めるフック

    このフックは以下の機能を提供します：
    1. 対象ツール実行前に承認を求める
    2. 承認された場合はツールを実行
    3. 修正要望がある場合はツール実行をキャンセルし、修正を促す
    4. 拒否された場合はツール実行をキャンセル
    """

    # TODO: 承認対象のツール名を業務ドメインに応じて設定する
    APPROVAL_REQUIRED_TOOLS: list[str] = ["{tool_name_a}", "{tool_name_b}"]

    def __init__(self, approval_callback=None):
        """
        初期化

        Args:
            approval_callback: 承認を求めるコールバック関数
                               引数: tool_name (str), tool_params (dict)
                               戻り値: tuple (approved: bool, feedback: str)
                               - approved: True=承認, False=拒否または修正要望
                               - feedback: 修正要望の内容（承認時は空文字列、キャンセル時は"CANCEL"）
        """
        self.approval_callback = approval_callback or self._default_approval_callback
        self._error_handler = ErrorHandler()

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """フックの登録。

        BeforeToolCallEventは全ツール呼び出しで発火するため、
        ハンドラー内で対象ツールを必ずフィルタリングすること（R9.8.3参照）。
        """
        # add_callback()でイベントとハンドラーを登録する
        registry.add_callback(BeforeToolCallEvent, self.request_approval)

    def request_approval(self, event: BeforeToolCallEvent) -> None:
        """
        ツール実行前に承認を求める。

        Args:
            event: BeforeToolCallEvent
                - event.tool_use["name"]  : ツール名 (str)
                - event.tool_use["input"] : ツール入力パラメータ (dict)
                - event.cancel_tool       : キャンセル制御。文字列またはTrueを設定するとキャンセル
                                            （event.cancel()は存在しない）
        """
        # TODO: 詳細設計書に従い実装
        # - ツール名・入力パラメータの取得（R9.8.3参照）
        #   tool_name = event.tool_use["name"]
        #   tool_params = event.tool_use.get("input", {})
        # - APPROVAL_REQUIRED_TOOLS に含まれないツールはreturnでスキップ
        #   （BeforeToolCallEventは全ツール呼び出しで発火するため、このフィルタリングは必須）
        # - ログ出力
        # - approval_callbackを呼び出し (approved, feedback) を受け取る
        # - approved=Trueの場合: ログ出力してreturn（ツールがそのまま実行される）
        # - approved=Falseの場合: _build_cancel_message()でメッセージを生成し
        #   event.cancel_tool に設定してキャンセル（event.cancel()は存在しない）
        pass

    def _build_cancel_message(self, tool_name: str, feedback: str) -> str:
        """
        キャンセルメッセージを生成する。

        event.cancel_toolに設定した文字列はツール結果としてLLMに返却される。
        LLMへの指示として機能するため、次のアクションを明示的に記述すること。

        Args:
            tool_name: ツール名
            feedback: ユーザーからのフィードバック（"CANCEL"=拒否、それ以外=修正要望、空=拒否）

        Returns:
            str: LLMへ返却するキャンセルメッセージ
        """
        # TODO: 詳細設計書に従い実装
        # - feedbackが"CANCEL"または空の場合: 申請中止メッセージを返す
        # - feedbackに修正内容がある場合: 修正要望をLLMに伝えて再生成を促すメッセージを返す
        pass

    def _default_approval_callback(self, tool_name: str, tool_params: dict) -> tuple:
        """
        デフォルトの承認コールバック（コンソール入力）

        Args:
            tool_name: ツール名
            tool_params: ツール入力パラメータ

        Returns:
            tuple: (approved: bool, feedback: str)
                   (True, "")          : 承認
                   (False, "CANCEL")   : キャンセル
                   (False, "修正内容") : 修正要望
        """
        # TODO: 詳細設計書に従い実装
        # - ツールパラメータの表示（ツール名に応じてカスタマイズ）
        # - 3択（OK/修正/キャンセル）の入力受付
        # - 選択に応じた戻り値の返却
        pass
```

## カスタマイズガイド

1. **承認対象ツール**: `request_approval` 内のツール名フィルタリング条件を業務ドメインに応じて変更する。`BeforeToolCallEvent` は全ツール呼び出しで発火するため、対象外ツールは必ず `return` でスキップすること
2. **承認コールバック**: コンソール以外のUI（Web、Slack等）で承認を受ける場合、カスタムコールバックを `approval_callback` に渡す
3. **パラメータ表示**: `_default_approval_callback` のTODO箇所でツールごとのパラメータ表示をカスタマイズする
4. **キャンセルメッセージ**: `event.cancel_tool` に設定した文字列がツール結果としてLLMに返却される。LLMへの指示として機能するため、次のアクションを明示的に記述する
