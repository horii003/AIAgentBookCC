import sys
import os
import json
import tempfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from unittest.mock import MagicMock, patch
from datetime import date, timedelta


def make_context(applicant_name="田中太郎", application_date="2026-05-02", session_id="test_sess"):
    ctx = MagicMock()
    ctx.invocation_state = {
        "applicant_name": applicant_name,
        "application_date": application_date,
        "session_id": session_id,
    }
    return ctx


VALID_TRAIN_ROUTES = {
    "routes": [
        {"departure": "渋谷", "destination": "新宿", "fare": 200},
        {"departure": "東京", "destination": "品川", "fare": 170},
    ]
}

VALID_FIXED_FARES = {
    "entries": [
        {"transportation_type": "バス", "fare": 220},
        {"transportation_type": "タクシー", "fare": 2000},
        {"transportation_type": "飛行機", "fare": 50000},
    ]
}

TODAY = date.today()
VALID_DATE = (TODAY - timedelta(days=1)).isoformat()
EXPIRED_DATE = (TODAY - timedelta(days=91)).isoformat()


class TestCalculateTransportFare:
    def _call(self, departure, destination, transportation_type, travel_date, purpose, context=None):
        import tools.transport_tools as mod
        if context is None:
            context = make_context()
        return mod.calculate_transport_fare.__wrapped__(
            context, departure, destination, transportation_type, travel_date, purpose
        )

    def test_train_fare_found(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        fares_file = tmp_path / "fixed_fares.json"
        fares_file.write_text(json.dumps(VALID_FIXED_FARES), encoding="utf-8")
        import config.settings as settings
        orig_train = settings.TRAIN_ROUTES_PATH
        orig_fixed = settings.FIXED_FARES_PATH
        settings.TRAIN_ROUTES_PATH = str(routes_file)
        settings.FIXED_FARES_PATH = str(fares_file)
        import tools.transport_tools as mod
        orig_train2 = mod.TRAIN_ROUTES_PATH
        orig_fixed2 = mod.FIXED_FARES_PATH
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        mod.FIXED_FARES_PATH = str(fares_file)
        try:
            result = self._call("渋谷", "新宿", "電車", VALID_DATE, "社内会議")
            assert result["success"] is True
            assert result["fare"] == 200
            assert "train_routes.json" in result["calculation_basis"]
        finally:
            settings.TRAIN_ROUTES_PATH = orig_train
            settings.FIXED_FARES_PATH = orig_fixed
            mod.TRAIN_ROUTES_PATH = orig_train2
            mod.FIXED_FARES_PATH = orig_fixed2

    def test_train_fare_bidirectional(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        try:
            result = self._call("新宿", "渋谷", "電車", VALID_DATE, "社内会議")
            assert result["success"] is True
            assert result["fare"] == 200
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"

    def test_bus_fare(self, tmp_path):
        fares_file = tmp_path / "fixed_fares.json"
        fares_file.write_text(json.dumps(VALID_FIXED_FARES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.FIXED_FARES_PATH = str(fares_file)
        try:
            result = self._call("A", "B", "バス", VALID_DATE, "業務")
            assert result["success"] is True
            assert result["fare"] == 220
            assert "fixed_fares.json" in result["calculation_basis"]
        finally:
            mod.FIXED_FARES_PATH = "data/fixed_fares.json"

    def test_taxi_fare(self, tmp_path):
        fares_file = tmp_path / "fixed_fares.json"
        fares_file.write_text(json.dumps(VALID_FIXED_FARES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.FIXED_FARES_PATH = str(fares_file)
        try:
            result = self._call("A", "B", "タクシー", VALID_DATE, "業務")
            assert result["success"] is True
            assert result["fare"] == 2000
        finally:
            mod.FIXED_FARES_PATH = "data/fixed_fares.json"

    def test_airplane_fare(self, tmp_path):
        fares_file = tmp_path / "fixed_fares.json"
        fares_file.write_text(json.dumps(VALID_FIXED_FARES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.FIXED_FARES_PATH = str(fares_file)
        try:
            result = self._call("A", "B", "飛行機", VALID_DATE, "業務")
            assert result["success"] is True
            assert result["fare"] == 50000
        finally:
            mod.FIXED_FARES_PATH = "data/fixed_fares.json"

    def test_station_suffix_normalization(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        try:
            result = self._call("渋谷駅", "新宿駅", "電車", VALID_DATE, "業務")
            assert result["success"] is True
            assert result["fare"] == 200
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"

    def test_transportation_type_normalization_jr(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        try:
            result = self._call("渋谷", "新宿", "JR", VALID_DATE, "業務")
            assert result["success"] is True
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"

    def test_route_not_found_returns_failure(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        try:
            result = self._call("存在しない駅A", "存在しない駅B", "電車", VALID_DATE, "業務")
            assert result["success"] is False
            assert result["fare"] == 0
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"

    def test_train_routes_file_missing(self, tmp_path):
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(tmp_path / "nonexistent.json")
        try:
            result = self._call("A", "B", "電車", VALID_DATE, "業務")
            assert result["success"] is False
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"

    def test_fixed_fares_file_missing(self, tmp_path):
        import tools.transport_tools as mod
        mod.FIXED_FARES_PATH = str(tmp_path / "nonexistent.json")
        try:
            result = self._call("A", "B", "バス", VALID_DATE, "業務")
            assert result["success"] is False
        finally:
            mod.FIXED_FARES_PATH = "data/fixed_fares.json"

    def test_expired_travel_date(self):
        result = self._call("渋谷", "新宿", "電車", EXPIRED_DATE, "業務")
        assert result["success"] is False
        assert "90日" in result["message"] or "超過" in result["message"]

    def test_invalid_transportation_type(self):
        result = self._call("A", "B", "自動車", VALID_DATE, "業務")
        assert result["success"] is False

    def test_empty_departure(self):
        result = self._call("", "B", "電車", VALID_DATE, "業務")
        assert result["success"] is False

    def test_calculation_basis_present(self, tmp_path):
        routes_file = tmp_path / "train_routes.json"
        routes_file.write_text(json.dumps(VALID_TRAIN_ROUTES), encoding="utf-8")
        import tools.transport_tools as mod
        mod.TRAIN_ROUTES_PATH = str(routes_file)
        try:
            result = self._call("渋谷", "新宿", "電車", VALID_DATE, "業務")
            assert result["success"] is True
            assert len(result["calculation_basis"]) > 0
        finally:
            mod.TRAIN_ROUTES_PATH = "data/train_routes.json"
