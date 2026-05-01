"""
交通費計算ツール

移動区間情報と運賃データファイルを照合し、交通費を自動計算して返却する。
"""
import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from strands import tool

from handlers.error_handler import ErrorHandler
from models.data_models import (
    TransportCalculatorInput,
    normalize_station_name,
    normalize_transport_type,
)

logger = logging.getLogger("tools.transport_calculator")

TRAIN_ROUTES_PATH = "data/train_routes.json"
FIXED_FARES_PATH = "data/fixed_fares.json"


class FareRouteEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    departure: str
    destination: str
    fare: int = Field(..., gt=0)


class FareRoutesModel(BaseModel):
    routes: list[FareRouteEntry]


class FareFixedModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bus: int = Field(..., alias="バス", gt=0)
    taxi: int = Field(..., alias="タクシー", gt=0)
    airplane: int = Field(..., alias="飛行機", gt=0)


def _load_json_file(file_path: str) -> tuple[bool, Any]:
    """JSON ファイルを読み込んで内容を返す。失敗時は (False, エラーメッセージ) タプルを返す。"""
    if not os.path.exists(file_path):
        logger.warning(f"交通費計算: 運賃データファイルが見つかりません: file_path={file_path}")
        return False, ErrorHandler.handle_fare_data_error(
            FileNotFoundError(f"{file_path} が見つかりません")
        )
    try:
        with open(file_path, encoding="utf-8") as f:
            return True, json.load(f)
    except Exception as e:
        logger.error(f"交通費計算: ファイル読み込みエラー: file_path={file_path}", exc_info=True)
        return False, ErrorHandler.handle_fare_data_error(e)


@tool
def calculate_transport_fare(
    transport_type: str,
    departure: str,
    destination: str,
    travel_date: str,
) -> dict:
    """
    交通費計算ツール

    移動区間情報から交通費を自動計算する。
    電車は /data/train_routes.json の経路テーブルをリスト線形探索で検索し、
    バス・タクシー・飛行機は /data/fixed_fares.json の固定運賃を返却する。

    Args:
        transport_type: 交通手段。許容値: 「電車」「バス」「タクシー」「飛行機」。
            英語・略称（train, bus, taxi, cab, airplane, plane）は自動正規化される。
        departure: 出発地。電車の場合は駅名（末尾「駅」は自動除去）。
        destination: 目的地。電車の場合は駅名（末尾「駅」は自動除去）。
        travel_date: 移動日。YYYY-MM-DD 形式の文字列。

    Returns:
        dict: 以下のキーを持つ辞書。
            - calculable (bool): 自動計算可否フラグ。True=計算成功、False=計算不可。
            - fare (int | None): 計算済み運賃（円単位）。calculable=False の場合は None。
            - success (bool): 処理成功フラグ。エラー発生時は False。
            - message (str | None): エラー時のメッセージ。成功時は None。
    """
    logger.info(
        f"交通費計算開始: transport_type={transport_type}, departure={departure}, "
        f"destination={destination}, travel_date={travel_date}"
    )

    try:
        validated = TransportCalculatorInput(
            transport_type=transport_type,
            departure=departure,
            destination=destination,
            travel_date=travel_date,
        )
    except ValidationError as e:
        logger.error("交通費計算: バリデーションエラー", exc_info=True)
        return {
            "calculable": False,
            "fare": None,
            "success": False,
            "message": ErrorHandler.handle_validation_error(e),
        }

    norm_transport = validated.transport_type
    norm_departure = validated.departure
    norm_destination = validated.destination

    if norm_transport == "電車":
        ok, data = _load_json_file(TRAIN_ROUTES_PATH)
        if not ok:
            return {"calculable": False, "fare": None, "success": False, "message": data}

        try:
            routes_model = FareRoutesModel.model_validate(data)
        except ValidationError as e:
            logger.error(f"交通費計算: スキーマ検証エラー: file_path={TRAIN_ROUTES_PATH}", exc_info=True)
            return {
                "calculable": False,
                "fare": None,
                "success": False,
                "message": ErrorHandler.handle_calculation_error(e),
            }

        for route in routes_model.routes:
            if route.departure == norm_departure and route.destination == norm_destination:
                logger.info(f"交通費計算成功: fare={route.fare}, transport_type={norm_transport}")
                return {"calculable": True, "fare": route.fare, "success": True, "message": None}

        logger.info(f"交通費計算: 経路データなし {norm_departure}->{norm_destination} ({norm_transport})")
        return {"calculable": False, "fare": None, "success": True, "message": None}

    else:
        ok, data = _load_json_file(FIXED_FARES_PATH)
        if not ok:
            return {"calculable": False, "fare": None, "success": False, "message": data}

        try:
            fixed_model = FareFixedModel.model_validate(data)
        except ValidationError as e:
            logger.error(f"交通費計算: スキーマ検証エラー: file_path={FIXED_FARES_PATH}", exc_info=True)
            return {
                "calculable": False,
                "fare": None,
                "success": False,
                "message": ErrorHandler.handle_calculation_error(e),
            }

        fare_map = {
            "バス": fixed_model.bus,
            "タクシー": fixed_model.taxi,
            "飛行機": fixed_model.airplane,
        }

        if norm_transport not in fare_map:
            err = ValueError(f"固定運賃データにキー '{norm_transport}' が存在しません")
            logger.error(f"交通費計算: 計算エラー: file_path={FIXED_FARES_PATH}")
            return {
                "calculable": False,
                "fare": None,
                "success": False,
                "message": ErrorHandler.handle_calculation_error(err),
            }

        fare = fare_map[norm_transport]
        logger.info(f"交通費計算成功: fare={fare}, transport_type={norm_transport}")
        return {"calculable": True, "fare": fare, "success": True, "message": None}
