"""CLIコンソール承認アダプタ

HumanApprovalHook に渡すコールバック関数の実装。
input() でユーザーから承認入力を受け付ける。
"""
import logging

_logger = logging.getLogger(__name__)

_MAX_RETRY = 3


def console_approval_callback(tool_name: str, tool_params: dict) -> tuple:
    """CLIコンソールで承認確認を行うコールバック関数。

    Args:
        tool_name: ツール名
        tool_params: ツールパラメータ

    Returns:
        tuple: (approved: bool, feedback: str)
            (True, "")         : 承認
            (False, "CANCEL")  : キャンセル
            (False, "修正内容") : 修正要望
    """
    print("\n" + "=" * 50)
    print("申請情報を確認してください。")
    print(f"ツール: {tool_name}")
    if tool_params:
        for key, value in tool_params.items():
            print(f"  {key}: {value}")
    print("=" * 50)

    invalid_count = 0
    while True:
        try:
            user_input = input("承認しますか？（OK / 修正 / キャンセル）\n> ").strip()
        except EOFError:
            _logger.warning("HumanApprovalHook: EOFError発生 → キャンセルとして処理")
            return (False, "CANCEL")

        normalized = user_input.lower()

        if normalized == "ok":
            _logger.info("HumanApprovalHook: 承認OK tool_name=%s", tool_name)
            return (True, "")

        if normalized in ("キャンセル", "cancel"):
            _logger.info("HumanApprovalHook: キャンセル選択 tool_name=%s", tool_name)
            return (False, "CANCEL")

        if normalized == "修正":
            feedback = input("修正内容を入力してください: ").strip()
            _logger.info("HumanApprovalHook: 修正選択 tool_name=%s", tool_name)
            return (False, feedback if feedback else "入力が認識できませんでした。情報収集からやり直します。")

        invalid_count += 1
        _logger.warning(
            "HumanApprovalHook: 無効入力（%d回目） input=%s", invalid_count, user_input
        )
        if invalid_count >= _MAX_RETRY:
            _logger.warning("HumanApprovalHook: 再試行上限超過 → 修正として処理")
            return (False, "入力が認識できませんでした。情報収集からやり直します。")

        print("「OK」「修正」「キャンセル」のいずれかを入力してください。")
