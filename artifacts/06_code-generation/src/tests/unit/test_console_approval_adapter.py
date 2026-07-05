"""console_approval_adapterの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from unittest.mock import patch
from handlers.console_approval_adapter import console_approval_callback


class TestConsoleApprovalCallback:
    def test_OK入力で承認を返す(self):
        with patch("builtins.input", return_value="OK"):
            approved, feedback = console_approval_callback("test_tool", {"key": "value"})
        assert approved is True
        assert feedback == ""

    def test_ok小文字でも承認を返す(self):
        with patch("builtins.input", return_value="ok"):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is True

    def test_スペース混在OKでも承認を返す(self):
        with patch("builtins.input", return_value=" OK "):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is True

    def test_キャンセル入力でCANCELを返す(self):
        with patch("builtins.input", return_value="キャンセル"):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is False
        assert feedback == "CANCEL"

    def test_修正入力で修正内容を返す(self):
        with patch("builtins.input", side_effect=["修正", "送付先を変更"]):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is False
        assert feedback == "送付先を変更"

    def test_無効入力3回で修正として処理される(self):
        with patch("builtins.input", side_effect=["abc", "xyz", "123"]):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is False
        assert "入力が認識できませんでした" in feedback

    def test_EOFErrorでキャンセルを返す(self):
        with patch("builtins.input", side_effect=EOFError()):
            approved, feedback = console_approval_callback("test_tool", {})
        assert approved is False
        assert feedback == "CANCEL"

    def test_戻り値がtupleである(self):
        with patch("builtins.input", return_value="OK"):
            result = console_approval_callback("tool", {})
        assert isinstance(result, tuple)
        assert len(result) == 2
