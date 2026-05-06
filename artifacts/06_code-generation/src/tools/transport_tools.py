# 参照: DD-01a 交通費計算ツール詳細設計書
"""交通費計算ツール定義

出発地・目的地・交通手段・移動日を入力として、交通手段ごとのルールに従い運賃を自動計算する。
電車区間はDATA-009（train_routes.json）をリスト線形探索で検索し正確な運賃を返す。
バス・タクシー・飛行機はDATA-010（fixed_fares.json）を参照して固定運賃を返す。
"""
import os
import json
import logging

from pydantic import ValidationError

from handlers.error_handler import ErrorHandler
from models.data_models import FareCalculationInput

logger = logging.getLogger(__name__)
_error_handler = ErrorHandler()

# DD-01a 9.1節: データファイルパス定数
DATA_TRAIN_ROUTES_PATH = "data/train_routes.json"
DATA_FIXED_FARES_PATH = "data/fixed_fares.json"

# fixed_fares.json の英語キー → 日本語交通手段名へのマッピング
_FIXED_FARE_KEY_MAP = {
    "バス": ["バス", "bus"],
    "タクシー": ["タクシー", "taxi"],
    "飛行機": ["飛行機", "airplane"],
}


def load_fare_data(
    train_routes_path: str = DATA_TRAIN_ROUTES_PATH,
    fixed_fares_path: str = DATA_FIXED_FARES_PATH,
) -> tuple:
    """アプリケーション起動時にDATA-009・DATA-010をメモリに静的読み込みする。

    モジュールインポート時に1回だけ呼び出す（バリデーション方針準拠）。

    Args:
        train_routes_path: train_routes.jsonのファイルパス
        fixed_fares_path: fixed_fares.jsonのファイルパス

    Returns:
        tuple:
            成功: (True, (train_routes_list, fixed_fares_dict))
                  - train_routes_list: list[dict] - 電車経路データ
                  - fixed_fares_dict: dict[str, int] - バス/タクシー/飛行機の固定運賃（日本語キー）
            失敗: (False, エラーメッセージ文字列)
    """
    # train_routes.json の存在チェック（os.path.exists()による事前チェック）
    if not os.path.exists(train_routes_path):
        msg = f"運賃データファイルが見つかりません: {train_routes_path}"
        logger.warning("load_fare_data: file not found: %s", train_routes_path)
        return (False, msg)

    # train_routes.json の読み込み（routesキー配下のネスト形式）
    try:
        with open(train_routes_path, encoding="utf-8") as f:
            train_data = json.load(f)
        train_routes_list = train_data.get("routes", [])
    except Exception as e:
        msg = f"電車経路データの読み込みに失敗しました: {e}"
        logger.error("load_fare_data failed: %s", e)
        return (False, msg)

    # fixed_fares.json の存在チェック
    if not os.path.exists(fixed_fares_path):
        msg = f"運賃データファイルが見つかりません: {fixed_fares_path}"
        logger.warning("load_fare_data: file not found: %s", fixed_fares_path)
        return (False, msg)

    # fixed_fares.json の読み込み（フラットなkey-value形式）
    try:
        with open(fixed_fares_path, encoding="utf-8") as f:
            raw_fixed_fares = json.load(f)

        # 英語キーを日本語キーに変換して正規化する
        fixed_fares_dict: dict[str, int] = {}
        for jp_key, possible_keys in _FIXED_FARE_KEY_MAP.items():
            for key in possible_keys:
                if key in raw_fixed_fares:
                    fixed_fares_dict[jp_key] = int(raw_fixed_fares[key])
                    break

    except Exception as e:
        msg = f"固定運賃データの読み込みに失敗しました: {e}"
        logger.error("load_fare_data failed: %s", e)
        return (False, msg)

    return (True, (train_routes_list, fixed_fares_dict))


# DD-01a 3.3.2節: モジュールレベル静的読み込み（アプリケーション起動時に1回だけ実行）
_load_result = load_fare_data()
if not _load_result[0]:
    logger.warning("load_fare_data failed at module load: %s", _load_result[1])
    _railway_routes: list[dict] = []
    _fixed_fares: dict[str, int] = {}
else:
    _railway_routes, _fixed_fares = _load_result[1]


try:
    from strands import tool, ToolContext
    _STRANDS_AVAILABLE = True
except ImportError:
    _STRANDS_AVAILABLE = False

    def tool(context=False):
        """strands未インストール環境向けスタブデコレータ。"""
        def decorator(func):
            return func
        return decorator if context else lambda func: func

    class ToolContext:
        """strands未インストール環境向けスタブ。"""
        def __init__(self):
            self.invocation_state = {}


@tool(context=True)
def calculate_transport_fare(
    departure: str,
    destination: str,
    transport_type: str,
    travel_date: str = None,
    tool_context: "ToolContext" = None,
) -> dict:
    """指定された移動区間の交通費を計算します。

    電車の場合はDATA-009（train_routes.json）をリスト線形探索で検索し、出発地・目的地に一致する
    区間の運賃を返します。バス・タクシー・飛行機の場合はDATA-010（fixed_fares.json）
    の固定運賃を返します。申請者名・申請日はツール内部でinvocation_stateから取得します。

    Args:
        departure (str): 出発地（「渋谷駅」「渋谷」等、駅名前後の「駅」「駅前」は自動除去）
        destination (str): 目的地（「新宿駅」「新宿」等、同上）
        transport_type (str): 交通手段。以下の表記を許容し内部統一表記へ正規化します:
            - 電車系: 「電車」「鉄道」「JR」「地下鉄」「電鉄」→「電車」
            - バス系: 「バス」「路線バス」→「バス」
            - タクシー系: 「タクシー」「taxi」→「タクシー」
            - 飛行機系: 「飛行機」「航空機」「airplane」→「飛行機」
        travel_date (str, optional): 移動日（「2026-05-06」等のYYYY-MM-DD形式）
        tool_context: ツールコンテキスト（invocation_stateを含む）

    Returns:
        dict: 以下のキーを持つ辞書:
            - success (bool): 計算成否フラグ
            - fare (int): 運賃（円単位）。エラー時は0
            - calculation_method (str): 計算方法の説明（「電車経路テーブル検索」または「固定運賃参照: タクシー」等）
            - message (str): エラーメッセージ（success=Trueの場合は空文字列）
    """
    # invocation_stateから申請者名・申請日を取得する（LLMはパラメータとして渡さない）
    applicant_name = ""
    application_date = ""
    if tool_context and hasattr(tool_context, "invocation_state") and tool_context.invocation_state:
        applicant_name = tool_context.invocation_state.get("applicant_name", "")
        application_date = tool_context.invocation_state.get("application_date", "")

    logger.info(
        "calculate_transport_fare called: departure=%s, destination=%s, "
        "transport_type=%s, travel_date=%s",
        departure, destination, transport_type, travel_date,
    )

    try:
        # FareCalculationInputでバリデーション・正規化（BRL-14/BRL-15）
        validated = FareCalculationInput(
            departure=departure,
            destination=destination,
            transport_type=transport_type,
            travel_date=travel_date,
        )
    except ValidationError as e:
        logger.error("calculate_transport_fare validation error: %s", e)
        error_message = _error_handler.handle_validation_error(e)
        return {"success": False, "fare": 0, "calculation_method": "", "message": error_message}
    except Exception as e:
        logger.error("calculate_transport_fare unexpected error: %s", e)
        error_message = _error_handler.handle_unexpected_error(e)
        return {"success": False, "fare": 0, "calculation_method": "", "message": error_message}

    dep = validated.departure
    dst = validated.destination
    t_type = validated.transport_type

    try:
        if t_type == "電車":
            # DD-01a 3.3.1節: 電車区間はリスト線形探索（departure・destinationの完全一致）
            matched_route = None
            for route in _railway_routes:
                if route.get("departure") == dep and route.get("destination") == dst:
                    matched_route = route
                    break

            if matched_route is None:
                logger.warning(
                    "calculate_transport_fare: route not found: departure=%s, destination=%s",
                    dep, dst,
                )
                return {
                    "success": False,
                    "fare": 0,
                    "calculation_method": "",
                    "message": "該当する電車区間が見つかりません。出発地・目的地をご確認いただくか、運賃を手動で入力してください。",
                }

            fare = int(matched_route["fare"])
            calculation_method = "電車経路テーブル検索"

        else:
            # DD-01a 3.3.1節: バス・タクシー・飛行機は固定運賃参照
            if t_type not in _fixed_fares:
                logger.warning(
                    "calculate_transport_fare: fixed fare not found for transport_type=%s",
                    t_type,
                )
                return {
                    "success": False,
                    "fare": 0,
                    "calculation_method": "",
                    "message": f"固定運賃データに「{t_type}」が見つかりません。担当部署へご連絡ください。",
                }
            fare = _fixed_fares[t_type]
            calculation_method = f"固定運賃参照: {t_type}"

        logger.info(
            "calculate_transport_fare succeeded: fare=%d, method=%s",
            fare, calculation_method,
        )
        return {
            "success": True,
            "fare": fare,
            "calculation_method": calculation_method,
            "message": "",
        }

    except Exception as e:
        logger.error("calculate_transport_fare unexpected error: %s", e)
        error_message = _error_handler.handle_unexpected_error(e)
        return {"success": False, "fare": 0, "calculation_method": "", "message": error_message}
