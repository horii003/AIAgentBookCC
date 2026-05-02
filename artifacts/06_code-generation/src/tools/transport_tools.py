import json
import logging
import os

from pydantic import ValidationError
from strands import tool
from strands.types.tools import ToolContext

from config.settings import FIXED_FARES_PATH, TRAIN_ROUTES_PATH
from handlers.error_handler import ErrorHandler
from models.data_models import FixedFareMaster, TrainRouteMaster, TransportToolInput

logger = logging.getLogger(__name__)
error_handler = ErrorHandler()


def _load_train_routes() -> TrainRouteMaster:
    with open(TRAIN_ROUTES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return TrainRouteMaster.model_validate(data)


def _load_fixed_fares() -> FixedFareMaster:
    with open(FIXED_FARES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return FixedFareMaster.model_validate(data)


@tool(context=True)
def calculate_transport_fare(
    tool_context: ToolContext,
    departure: str,
    destination: str,
    transportation_type: str,
    travel_date: str,
    purpose: str,
) -> dict:
    """移動区間の交通費を算出する。

    電車の場合は train_routes.json の経路テーブルから出発地・目的地の組み合わせを双方向検索し、
    バス・タクシー・飛行機の場合は fixed_fares.json の固定運賃テーブルから取得する。
    算出根拠（参照テーブル・エントリの要約）を result["calculation_basis"] として返す。

    Args:
        departure: 出発地（駅名または地点名）。「駅」「Station」等の接尾語は自動除去される。
        destination: 目的地（駅名または地点名）。「駅」「Station」等の接尾語は自動除去される。
        transportation_type: 交通手段。「電車」「バス」「タクシー」「飛行機」のいずれか。
        travel_date: 移動日（YYYY-MM-DD形式）。
        purpose: 業務目的（空文字不可）。

    Returns:
        dict with keys: success, fare, calculation_basis, message
    """
    logger.info(
        f"[OPE-002] calculate_transport_fare 開始: departure={departure}, destination={destination}, "
        f"transportation_type={transportation_type}, travel_date={travel_date}"
    )

    try:
        validated = TransportToolInput(
            departure=departure,
            destination=destination,
            transportation_type=transportation_type,
            travel_date=travel_date,
            purpose=purpose,
        )
    except ValidationError as e:
        return {"success": False, "fare": 0, "calculation_basis": "", "message": error_handler.handle_validation_error(e)}

    dep = validated.departure
    dst = validated.destination
    t_type = validated.transportation_type

    if t_type == "電車":
        if not os.path.exists(TRAIN_ROUTES_PATH):
            logger.error(f"[ERR-004] ファイル参照失敗: {TRAIN_ROUTES_PATH}")
            return {"success": False, "fare": 0, "calculation_basis": "", "message": error_handler.handle_fare_data_error(Exception(f"ファイル不在: {TRAIN_ROUTES_PATH}"))}
        try:
            master = _load_train_routes()
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"[ERR-006] テーブルファイル不正: {TRAIN_ROUTES_PATH} - {e}")
            return {"success": False, "fare": 0, "calculation_basis": "", "message": "申し訳ありません。運賃テーブルのデータに問題が発生しました。担当部門（管理部）にお問い合わせください。"}

        for entry in master.routes:
            if (entry.departure == dep and entry.destination == dst) or \
               (entry.departure == dst and entry.destination == dep):
                fare = entry.fare
                calculation_basis = f"電車経路テーブル（train_routes.json）より: {dep}→{dst} {fare}円"
                logger.info(f"[OPE-002] calculate_transport_fare 完了: fare={fare}, calculation_basis={calculation_basis}")
                return {"success": True, "fare": fare, "calculation_basis": calculation_basis, "message": ""}

        logger.warning(f"[ERR-002] 経路不明: {dep}→{dst} ({t_type})")
        return {"success": False, "fare": 0, "calculation_basis": "", "message": error_handler.handle_calculation_error(ValueError(f"経路不明: {dep}→{dst}"))}

    else:
        if not os.path.exists(FIXED_FARES_PATH):
            logger.error(f"[ERR-004] ファイル参照失敗: {FIXED_FARES_PATH}")
            return {"success": False, "fare": 0, "calculation_basis": "", "message": error_handler.handle_fare_data_error(Exception(f"ファイル不在: {FIXED_FARES_PATH}"))}
        try:
            master = _load_fixed_fares()
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"[ERR-006] テーブルファイル不正: {FIXED_FARES_PATH} - {e}")
            return {"success": False, "fare": 0, "calculation_basis": "", "message": "申し訳ありません。運賃テーブルのデータに問題が発生しました。担当部門（管理部）にお問い合わせください。"}

        for entry in master.entries:
            if entry.transportation_type == t_type:
                fare = entry.fare
                calculation_basis = f"固定運賃テーブル（fixed_fares.json）より: {t_type} {fare}円"
                logger.info(f"[OPE-002] calculate_transport_fare 完了: fare={fare}, calculation_basis={calculation_basis}")
                return {"success": True, "fare": fare, "calculation_basis": calculation_basis, "message": ""}

        logger.warning(f"[ERR-002] 経路不明: {dep}→{dst} ({t_type})")
        return {"success": False, "fare": 0, "calculation_basis": "", "message": error_handler.handle_calculation_error(ValueError(f"交通手段不明: {t_type}"))}
