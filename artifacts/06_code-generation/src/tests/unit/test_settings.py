"""設定クラスの単体テスト"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from config.settings import ReceptionSettings, TransportSettings, ExpenseSettings, settings


class TestReceptionSettings:
    def test_デフォルト値確認(self):
        s = ReceptionSettings()
        assert s.max_iterations == 10
        assert s.max_attempts == 6
        assert s.initial_delay == 4
        assert s.max_delay == 240
        assert s.window_size == 30
        assert s.max_turn_count == 30
        assert s.max_input_length == 500

    def test_環境変数で上書きできる(self, monkeypatch):
        monkeypatch.setenv("ECAAS_RECEPTION_MAX_ITERATIONS", "15")
        s = ReceptionSettings()
        assert s.max_iterations == 15


class TestTransportSettings:
    def test_デフォルト値確認(self):
        s = TransportSettings()
        assert s.max_iterations == 10
        assert s.window_size == 20
        assert s.deadline_months == 3
        assert s.approval_threshold == 10000

    def test_環境変数で上書きできる(self, monkeypatch):
        monkeypatch.setenv("ECAAS_TRANSPORT_DEADLINE_MONTHS", "6")
        s = TransportSettings()
        assert s.deadline_months == 6


class TestExpenseSettings:
    def test_デフォルト値確認(self):
        s = ExpenseSettings()
        assert s.max_iterations == 10
        assert s.window_size == 15
        assert s.deadline_months == 3
        assert s.approval_threshold == 5000

    def test_環境変数で上書きできる(self, monkeypatch):
        monkeypatch.setenv("ECAAS_EXPENSE_APPROVAL_THRESHOLD", "10000")
        s = ExpenseSettings()
        assert s.approval_threshold == 10000


class TestSettingsAggregate:
    def test_settingsからreceptionへのアクセス(self):
        assert settings.reception.window_size == 30

    def test_settingsからtransportへのアクセス(self):
        assert settings.transport.deadline_months == 3

    def test_settingsからexpenseへのアクセス(self):
        assert settings.expense.approval_threshold == 5000
