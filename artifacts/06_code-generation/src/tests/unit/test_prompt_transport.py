"""prompt_transportの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from prompt.prompt_transport import get_transport_system_prompt


class TestGetTransportSystemPrompt:
    def test_文字列を返す(self):
        result = get_transport_system_prompt(
            applicant_name="田中太郎",
            application_date="2026-07-03",
            deadline="2026-04-03",
            transport_rules="ルールテキスト",
        )
        assert isinstance(result, str)

    def test_application_dateが埋め込まれる(self):
        result = get_transport_system_prompt(
            applicant_name="田中",
            application_date="2026-07-03",
            deadline="2026-04-03",
            transport_rules="rules",
        )
        assert "2026-07-03" in result

    def test_deadline_dateが埋め込まれる(self):
        result = get_transport_system_prompt(
            applicant_name="田中",
            application_date="2026-07-03",
            deadline="2026-04-03",
            transport_rules="rules",
        )
        assert "2026-04-03" in result

    def test_transport_rulesが埋め込まれる(self):
        result = get_transport_system_prompt(
            applicant_name="田中",
            application_date="2026-07-03",
            deadline="2026-04-03",
            transport_rules="カスタムルールテキスト",
        )
        assert "カスタムルールテキスト" in result

    def test_プレースホルダーが残らない(self):
        result = get_transport_system_prompt(
            applicant_name="田中",
            application_date="2026-07-03",
            deadline="2026-04-03",
            transport_rules="rules",
        )
        assert "{application_date}" not in result
        assert "{deadline_date}" not in result
        assert "{transport_rules}" not in result
