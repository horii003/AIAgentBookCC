"""交通費計算ツール

AG-002（交通費精算申請エージェント）が利用する交通費計算ツール関数を提供する。
"""
import json
import logging
import os
from typing import Optional

from pydantic import ValidationError
from strands import tool

from handlers.error_handler import ErrorHandler
from models.data_models import TransportSectionInput

_logger = logging.getLogger(__name__)

# ============ キャッシュ変数 ============

_train_fares_cache: Optional[dict] = None
_fixed_fares_cache: Optional[dict] = None


# ============ データ読み込み関数 ============

def _load_fare_data() -> tuple:
    """DATA-003/DATA-004 をキャッシュ変数にロードする（初回のみ）。

    Returns:
        tuple[bool, str]: 成功時 (True, "")、エラー時 (False, "エラーメッセージ")
    """
    global _train_fares_cache, _fixed_fares_cache

    if _train_fares_cache is None:
        path = "./template/train_routes.json"
        if not os.path.exists(path):
            _logger.warning("calculate_transport_fare: ファイル不存在 path=%s", path)
            return (False, f"運賃データファイルが見つかりません: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            # {"routes": [{"departure": ..., "destination": ..., "fare": ...}]} 形式を変換
            if "routes" in raw:
                built: dict = {}
                for r in raw["routes"]:
                    dep = r["departure"]
                    dest = r["destination"]
                    built.setdefault(dep, {})[dest] = r["fare"]
                _train_fares_cache = built
            else:
                _train_fares_cache = raw
        except json.JSONDecodeError:
            _logger.error("calculate_transport_fare: 致命的エラー error_type=JSONDecodeError path=%s", path)
            return (False, f"運賃データファイルの形式が不正です: {path}")
        except IOError as e:
            _logger.error("calculate_transport_fare: ファイルI/Oエラー path=%s error=%s", path, e)
            return (False, "運賃データの読み込みに失敗しました。交通費を手動で入力してください。")

    if _fixed_fares_cache is None:
        path = "./template/fixed_fares.json"
        if not os.path.exists(path):
            _logger.warning("calculate_transport_fare: ファイル不存在 path=%s", path)
            return (False, f"運賃データファイルが見つかりません: {path}")
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            # 英語キー→日本語キーのマッピング
            _KEY_MAP = {"bus": "バス", "taxi": "タクシー", "airplane": "飛行機", "train": "電車"}
            _fixed_fares_cache = {
                _KEY_MAP.get(k, k): v for k, v in raw.items()
            }
        except json.JSONDecodeError:
            _logger.error("calculate_transport_fare: 致命的エラー error_type=JSONDecodeError path=%s", path)
            return (False, f"運賃データファイルの形式が不正です: {path}")
        except IOError as e:
            _logger.error("calculate_transport_fare: ファイルI/Oエラー path=%s error=%s", path, e)
            return (False, "運賃データの読み込みに失敗しました。交通費を手動で入力してください。")

    return (True, "")


def _search_train_fare(departure: str, destination: str) -> dict:
    """電車経路テーブルから運賃を検索する。"""
    ok, msg = _load_fare_data()
    if not ok:
        return {"success": False, "message": msg}

    fare = _train_fares_cache.get(departure, {}).get(destination)
    if fare is None:
        _logger.warning(
            "calculate_transport_fare: 経路未登録 departure=%s destination=%s",
            departure, destination,
        )
        return {
            "success": False,
            "message": f"経路が見つかりません: {departure}→{destination}",
        }
    calculation_basis = f"電車経路テーブル（{departure}→{destination}）: {fare}円"
    return {"fare": fare, "calculation_basis": calculation_basis}


def _get_fixed_fare(transport_type: str) -> dict:
    """固定運賃データから運賃を取得する。"""
    ok, msg = _load_fare_data()
    if not ok:
        return {"success": False, "message": msg}

    fare = _fixed_fares_cache.get(transport_type)
    if fare is None:
        return {
            "success": False,
            "message": f"固定運賃が見つかりません: {transport_type}",
        }
    calculation_basis = f"固定運賃テーブル（{transport_type}）: {fare}円"
    return {"fare": fare, "calculation_basis": calculation_basis}


# ============ ツール関数 ============

@tool
def calculate_transport_fare(
    departure: str,
    destination: str,
    transport_type: str,
    travel_date: str,
    purpose: str,
) -> dict:
    """指定された移動区間の交通費運賃を計算して返す。

    電車の場合は電車経路・運賃データ（DATA-003: ./template/train_routes.json）から
    出発地と目的地をキーに運賃を検索する。
    バス・タクシー・飛行機の場合は固定運賃データ（DATA-004: ./template/fixed_fares.json）
    から交通手段をキーに固定金額を取得する。

    Args:
        departure: 出発地（駅名またはバス停名等。末尾の「駅」は自動除去される）
        destination: 目的地（駅名またはバス停名等。末尾の「駅」は自動除去される）
        transport_type: 交通手段（電車/バス/タクシー/飛行機、英語表記も可）
        travel_date: 移動日（YYYY-MM-DD形式）
        purpose: 業務目的（500文字以内の非空文字列）

    Returns:
        dict: 成功時は fare/calculation_basis/transport_type/departure/destination/travel_date を含む辞書、
              エラー時は {"success": False, "message": "エラーメッセージ"}
    """
    _logger.info(
        "calculate_transport_fare: 開始 departure=%s destination=%s transport_type=%s travel_date=%s",
        departure, destination, transport_type, travel_date,
    )

    try:
        validated = TransportSectionInput(
            departure=departure,
            destination=destination,
            transport_type=transport_type,
            travel_date=travel_date,
            purpose=purpose,
        )
    except ValidationError as e:
        msg = ErrorHandler.handle_validation_error(e)
        return {"success": False, "message": msg}

    dep = validated.departure
    dest = validated.destination
    t_type = validated.transport_type
    t_date = str(validated.travel_date)

    if t_type == "電車":
        result = _search_train_fare(dep, dest)
    else:
        result = _get_fixed_fare(t_type)

    if result.get("success") is False:
        return result

    fare = result["fare"]
    calculation_basis = result["calculation_basis"]

    _logger.info(
        "calculate_transport_fare: 運賃取得成功 fare=%d basis=%s", fare, calculation_basis
    )

    return {
        "fare": fare,
        "calculation_basis": calculation_basis,
        "transport_type": t_type,
        "departure": dep,
        "destination": dest,
        "travel_date": t_date,
    }
