"""交通費計算ツール

出発地・目的地・交通手段・移動日の情報から運賃を算出してAG-002に返す。
"""
import json
import logging
import os

from pydantic import ValidationError
from strands import tool
from strands.types.tools import ToolContext

from handlers.error_handler import ErrorHandler
from models.data_models import TrainFareRecord, TravelExpenseCalculatorInput

logger = logging.getLogger(__name__)

_error_handler = ErrorHandler()

_train_fares: list[TrainFareRecord] = []
_fixed_fares: dict[str, int] = {}

TRAIN_FARES_FILE = "data/templates/train_routes.json"
FIXED_FARES_FILE = "data/templates/fixed_fares.json"


def load_fare_data() -> tuple[bool, str]:
    """アプリ起動時に1回だけ呼び出す。失敗時は (False, エラーメッセージ) を返す。"""
    global _train_fares, _fixed_fares

    if not os.path.exists(TRAIN_FARES_FILE):
        logger.warning("Fare data file not found: %s", TRAIN_FARES_FILE)
        return (False, f"運賃データファイルが見つかりません: {TRAIN_FARES_FILE}")

    try:
        with open(TRAIN_FARES_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        _train_fares = [TrainFareRecord(**r) for r in raw]
    except ValidationError as e:
        msg = _error_handler.handle_validation_error(e)
        logger.warning("Failed to validate train fare data: %s", msg)
        return (False, msg)
    except Exception as e:
        msg = _error_handler.handle_unexpected_error(e)
        logger.warning("Failed to load fare data: %s, error=%s", TRAIN_FARES_FILE, e)
        return (False, msg)

    if not os.path.exists(FIXED_FARES_FILE):
        logger.warning("Fixed fare data file not found: %s", FIXED_FARES_FILE)
        return (False, f"固定運賃データファイルが見つかりません: {FIXED_FARES_FILE}")

    try:
        with open(FIXED_FARES_FILE, encoding="utf-8") as f:
            _fixed_fares = json.load(f)
    except Exception as e:
        msg = _error_handler.handle_unexpected_error(e)
        logger.warning("Failed to load fare data: %s, error=%s", FIXED_FARES_FILE, e)
        return (False, msg)

    logger.info(
        "Fare data loaded: %d train routes, %d fixed fares",
        len(_train_fares),
        len(_fixed_fares),
    )
    return (True, "")


@tool(context=True)
def calculate_travel_expense(
    travel_date: str,
    departure: str,
    destination: str,
    transport_type: str,
    tool_context: ToolContext,
) -> dict:
    """1区間分の移動情報から運賃を算出して返す。

    電車の場合はDATA-011（data/templates/train_routes.json）の区間運賃テーブルを参照し、
    バス・タクシー・飛行機の場合はDATA-012（data/templates/fixed_fares.json）の固定運賃を返す。

    申請者名・申請日はLLMがツールパラメータとして渡す値ではなく、
    invocation_stateからツール関数内部で取得する（@tool(context=True) デコレーター使用）。

    Args:
        travel_date (str): 移動日（YYYY-MM-DD形式。例: "2026-04-28"）
        departure (str): 出発地（正規化済み駅名または地名。例: "渋谷"）
        destination (str): 目的地（正規化済み駅名または地名。例: "新宿"）
        transport_type (str): 交通手段。許容値: "電車", "バス", "タクシー", "飛行機"。
            英語表記（"train", "bus", "taxi", "airplane", "plane"）および別表記
            （"鉄道", "地下鉄", "cab"）は正規化処理で変換される。

    Returns:
        dict: 成功時は {"success": True, "fare": int, "calculation_basis": str}、
              失敗時は {"success": False, "message": str}
    """
    invocation_state = tool_context.invocation_state or {}
    session_id = invocation_state.get("session_id", "unknown")

    logger.info(
        "calculate_travel_expense called: departure=%s, destination=%s, transport_type=%s, travel_date=%s",
        departure,
        destination,
        transport_type,
        travel_date,
    )

    try:
        validated = TravelExpenseCalculatorInput(
            travel_date=travel_date,
            departure=departure,
            destination=destination,
            transport_type=transport_type,
        )
    except ValidationError as e:
        error_message = _error_handler.handle_validation_error(e)
        logger.error(
            "ValidationError in calculate_travel_expense: %s, session_id=%s",
            error_message,
            session_id,
        )
        return {"success": False, "message": error_message}

    try:
        if validated.transport_type == "電車":
            fare = _find_train_fare(validated.departure, validated.destination)
            logger.info(
                "Travel fare calculated: %s→%s (%s) = %d円 (電車経路テーブル参照)",
                validated.departure,
                validated.destination,
                validated.transport_type,
                fare,
            )
            return {"success": True, "fare": fare, "calculation_basis": "電車経路テーブル参照"}
        else:
            fare = _fixed_fares.get(validated.transport_type)
            if fare is None:
                return {
                    "success": False,
                    "message": f"固定運賃データに{validated.transport_type}が見つかりませんでした。交通費を手動で入力してください。",
                }
            logger.info(
                "Travel fare calculated: %s = %d円 (固定運賃参照)",
                validated.transport_type,
                fare,
            )
            return {"success": True, "fare": fare, "calculation_basis": "固定運賃参照"}

    except ValueError:
        logger.error(
            "Route not found in train_fares: departure=%s, destination=%s, session_id=%s",
            validated.departure,
            validated.destination,
            session_id,
        )
        return {
            "success": False,
            "message": "指定された経路の運賃データが見つかりませんでした。交通費を手動で入力してください。",
        }
    except Exception as e:
        error_message = _error_handler.handle_unexpected_error(e)
        logger.critical(
            "Unexpected error in calculate_travel_expense: %s, session_id=%s",
            e,
            session_id,
            exc_info=True,
        )
        return {"success": False, "message": error_message}


def _find_train_fare(departure: str, destination: str) -> int:
    for record in _train_fares:
        if record.departure == departure and record.destination == destination:
            return record.fare
    raise ValueError(f"Route not found: {departure}→{destination}")
