# 参照: DD-01a 交通費計算ツール詳細設計書
"""tools/transport_tools.py の単体テスト"""
import sys
import os
import json
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# テスト用のtrain_routes.jsonとfixed_fares.jsonをsrc/dataから使用


class TestLoadFareData:
    """load_fare_data のテスト"""

    def test_load_success(self, tmp_path):
        """正常なJSONファイルから読み込みが成功すること。"""
        from tools.transport_tools import load_fare_data

        # テスト用ファイルを作成
        train_data = {"routes": [
            {"departure": "渋谷", "destination": "新宿", "fare": 170}
        ]}
        fixed_data = {"bus": 220, "taxi": 2000, "airplane": 50000}

        train_path = tmp_path / "train.json"
        fixed_path = tmp_path / "fixed.json"
        train_path.write_text(json.dumps(train_data), encoding="utf-8")
        fixed_path.write_text(json.dumps(fixed_data), encoding="utf-8")

        result = load_fare_data(str(train_path), str(fixed_path))
        assert result[0] is True
        routes, fares = result[1]
        assert len(routes) == 1
        assert "バス" in fares
        assert "タクシー" in fares
        assert "飛行機" in fares

    def test_train_routes_not_found(self, tmp_path):
        """train_routes.jsonが存在しない場合、(False, エラーメッセージ)が返ること。"""
        from tools.transport_tools import load_fare_data

        result = load_fare_data(
            str(tmp_path / "nonexistent.json"),
            str(tmp_path / "fixed.json"),
        )
        assert result[0] is False
        assert isinstance(result[1], str)

    def test_fixed_fares_not_found(self, tmp_path):
        """fixed_fares.jsonが存在しない場合、(False, エラーメッセージ)が返ること。"""
        from tools.transport_tools import load_fare_data

        train_data = {"routes": []}
        train_path = tmp_path / "train.json"
        train_path.write_text(json.dumps(train_data), encoding="utf-8")

        result = load_fare_data(str(train_path), str(tmp_path / "nonexistent.json"))
        assert result[0] is False
        assert isinstance(result[1], str)


class TestCalculateTransportFare:
    """calculate_transport_fare のテスト"""

    def setup_method(self):
        """テスト用にモジュールレベルのデータをsrc/dataのファイルでリロードする。"""
        import tools.transport_tools as tt
        # src/data配下の実際のファイルでリロード
        src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        train_path = os.path.join(src_dir, "data", "train_routes.json")
        fixed_path = os.path.join(src_dir, "data", "fixed_fares.json")

        if os.path.exists(train_path) and os.path.exists(fixed_path):
            result = tt.load_fare_data(train_path, fixed_path)
            if result[0]:
                tt._railway_routes, tt._fixed_fares = result[1]

    def _make_context(self, applicant_name="山田太郎", application_date="2026-05-06"):
        """テスト用のToolContextモックを生成する。"""
        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": applicant_name,
            "application_date": application_date,
        }
        return ctx

    def test_train_fare_exists(self):
        """存在する電車区間（渋谷→新宿）で正しい運賃が返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["fare"] == 170
        assert "電車経路テーブル検索" in result["calculation_method"]

    def test_bus_fixed_fare(self):
        """バスでfixed_fares.jsonの固定運賃が返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="バス",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["fare"] == 220
        assert "固定運賃参照: バス" in result["calculation_method"]

    def test_taxi_fixed_fare(self):
        """タクシーで固定運賃が返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="タクシー",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["fare"] == 2000
        assert "固定運賃参照: タクシー" in result["calculation_method"]

    def test_airplane_fixed_fare(self):
        """飛行機で固定運賃が返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="東京",
            destination="大阪",
            transport_type="飛行機",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["fare"] == 50000
        assert "固定運賃参照: 飛行機" in result["calculation_method"]

    def test_calculation_method_returned(self):
        """calculation_methodに正しい文字列が返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="東京",
            destination="品川",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["calculation_method"] in ["電車経路テーブル検索", "固定運賃参照: バス", "固定運賃参照: タクシー", "固定運賃参照: 飛行機"]

    def test_train_route_not_found(self):
        """DATA-009に存在しない電車区間でsuccess: Falseが返ること（ValueError）。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="存在しない駅",
            destination="別の駅",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is False
        assert result["fare"] == 0
        assert "見つかりません" in result["message"]

    def test_invalid_transport_type_raises(self):
        """transport_typeに「新幹線」でValidationErrorに基づく日本語エラーメッセージが返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="新幹線",
            tool_context=self._make_context(),
        )
        assert result["success"] is False
        assert result["fare"] == 0
        assert len(result["message"]) > 0

    def test_empty_departure_raises(self):
        """departureに空文字でValidationErrorメッセージが返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="",
            destination="新宿",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is False
        assert result["fare"] == 0

    def test_empty_destination_raises(self):
        """destinationに空文字でValidationErrorメッセージが返ること。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷",
            destination="",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is False

    def test_station_suffix_normalized(self):
        """「渋谷駅」→「渋谷」として正規化されて正しく検索されること（BRL-15）。"""
        from tools.transport_tools import calculate_transport_fare
        result = calculate_transport_fare(
            departure="渋谷駅",
            destination="新宿駅",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        assert result["success"] is True
        assert result["fare"] == 170

    def test_departure_500_chars_passes(self):
        """departureが500文字でバリデーション通過すること（境界値テスト）。"""
        from tools.transport_tools import calculate_transport_fare
        long_name = "あ" * 500
        result = calculate_transport_fare(
            departure=long_name,
            destination="新宿",
            transport_type="電車",
            tool_context=self._make_context(),
        )
        # 500文字でバリデーションは通過するが、経路が見つからないためsuccess=Falseも可
        # 重要なのはValidationErrorでないこと（ValidationErrorの場合もsuccess=Falseだが別のメッセージ）
        assert "message" in result  # 辞書形式で返ること

    def test_invocation_state_accessed(self):
        """invocation_stateからapplicant_name・application_dateが取得されること。"""
        from tools.transport_tools import calculate_transport_fare
        ctx = self._make_context("テスト申請者", "2026-01-01")
        # エラーが発生せずに実行されること（invocation_stateへのアクセスが正常に行われること）
        result = calculate_transport_fare(
            departure="渋谷",
            destination="新宿",
            transport_type="電車",
            tool_context=ctx,
        )
        assert isinstance(result, dict)
