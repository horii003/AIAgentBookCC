"""交通費計算ツール（TOOL-001）の実装

出発地・目的地・交通手段・移動日から区間運賃を算出する。
電車は template/train_routes.json を辞書キー検索、バス・タクシー・飛行機は
template/fixed_fares.json の固定運賃を参照する。
"""
import json
import logging
import os
from typing import Dict, Optional, Tuple

from pydantic import ValidationError
from strands import tool, ToolContext

from handlers.error_handler import ErrorHandler
from models.data_models import TransportExpenseCalculatorInput

_logger = logging.getLogger(__name__)
_error_handler = ErrorHandler()

_TRAIN_ROUTES_PATH = "data/templates/train_routes.json"
_FIXED_FARES_PATH = "data/templates/fixed_fares.json"


class FareDataLoader:
    """運賃データの読み込みを担当するクラス"""

    def __init__(self) -> None:
        self.train_routes_data: Dict[str, int] = {}
        self.fixed_fares_data: Dict[str, int] = {}

    def load_train_routes(self) -> Tuple[bool, str]:
        """template/train_routes.json を読み込み、辞書形式でメモリに保持する"""
        if not os.path.exists(_TRAIN_ROUTES_PATH):
            _logger.warning("[TL-001] 運賃データファイル未存在: file_path=%s", _TRAIN_ROUTES_PATH)
            return False, "申し訳ありません。運賃データファイルが見つかりません。"
        try:
            with open(_TRAIN_ROUTES_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict) and "routes" in raw:
                self.train_routes_data = {
                    f"{r['departure']}_{r['destination']}": int(r["fare"])
                    for r in raw["routes"]
                }
            else:
                self.train_routes_data = {k: int(v) for k, v in raw.items()}
            return True, ""
        except json.JSONDecodeError as exc:
            _logger.warning("[TL-001] 運賃データ読み込みエラー（JSONDecodeError）: %s", exc)
            return False, "申し訳ありません。運賃データファイルの形式が不正です。システム管理者にご連絡ください。"
        except Exception as exc:
            _logger.warning("[TL-001] 運賃データ読み込みエラー: %s", exc)
            return False, _error_handler.handle_fare_data_error(exc)

    def load_fixed_fares(self) -> Tuple[bool, str]:
        """template/fixed_fares.json を読み込み、辞書形式でメモリに保持する"""
        if not os.path.exists(_FIXED_FARES_PATH):
            _logger.warning("[TL-001] 運賃データファイル未存在: file_path=%s", _FIXED_FARES_PATH)
            return False, "申し訳ありません。運賃データファイルが見つかりません。"
        try:
            with open(_FIXED_FARES_PATH, encoding="utf-8") as f:
                raw: Dict[str, int] = json.load(f)
            self.fixed_fares_data = {k: int(v) for k, v in raw.items()}
            return True, ""
        except json.JSONDecodeError as exc:
            _logger.warning("[TL-001] 固定運賃データ読み込みエラー（JSONDecodeError）: %s", exc)
            return False, "申し訳ありません。固定運賃データファイルの形式が不正です。システム管理者にご連絡ください。"
        except Exception as exc:
            _logger.warning("[TL-001] 固定運賃データ読み込みエラー: %s", exc)
            return False, _error_handler.handle_fare_data_error(exc)


# モジュールレベルのシングルトン（アプリ起動時に1回だけ読み込む）
_fare_loader = FareDataLoader()
_fare_loader.load_train_routes()
_fare_loader.load_fixed_fares()


@tool(context=True)
def calculate_transport_expense(
    tool_context: ToolContext,
    transport_date: str,
    departure: str,
    destination: str,
    transport_type: str,
) -> dict:
    """1区間分の移動情報（移動日・出発地・目的地・交通手段）から区間運賃（円）を算出する。

    電車の場合は template/train_routes.json の経路辞書をキー検索し、バス・タクシー・飛行機は
    template/fixed_fares.json の固定運賃辞書をキー検索する。経路が見つからない場合は success=False を返す。
    申請者名・申請日はツール関数内部で invocation_state から取得する（LLMがパラメータとして渡さない）。

    Args:
        transport_date (str): 移動日（YYYY-MM-DD形式）。申請期限チェック（BRL-13）に使用。
        departure (str): 出発地（正規化済み駅名・地名）。
        destination (str): 目的地（正規化済み駅名・地名）。
        transport_type (str): 交通手段。「電車」「バス」「タクシー」「飛行機」または英語表記・別表記
            （例: "train" → "電車", "taxi" → "タクシー"）を正規化して受け入れる。

    Returns:
        dict: {
            "success": bool,
            "fare": int,              # 成功時: 区間運賃（円）
            "calculation_basis": str, # 成功時: 計算根拠
            "message": str            # 失敗時: ユーザー向けエラーメッセージ
        }
    """
    _logger.info(
        "[TL-001] calculate_transport_expense 開始: departure=%s, destination=%s, "
        "transport_type=%s, transport_date=%s",
        departure, destination, transport_type, transport_date,
    )

    try:
        validated = TransportExpenseCalculatorInput(
            transport_date=transport_date,
            departure=departure,
            destination=destination,
            transport_type=transport_type,
        )
    except ValidationError as exc:
        _logger.error("[TL-001] 入力バリデーションエラー: %s", exc)
        return {"success": False, "message": _error_handler.handle_validation_error(exc)}

    try:
        result = _calculate(
            validated.transport_type,
            validated.departure,
            validated.destination,
        )
        _logger.info(
            "[TL-001] calculate_transport_expense 完了: fare=%s, basis=%s",
            result.get("fare"),
            result.get("calculation_basis"),
        )
        return result
    except Exception as exc:
        _logger.error("[TL-001] 運賃計算エラー: %s", exc, exc_info=True)
        return {"success": False, "message": _error_handler.handle_calculation_error(exc)}


def _calculate(transport_type: str, departure: str, destination: str) -> dict:
    """交通手段に応じた運賃計算を行う内部関数"""
    if transport_type == "電車":
        key = f"{departure}_{destination}"
        fare = _fare_loader.train_routes_data.get(key)
        if fare is None:
            _logger.warning(
                "[TL-001] 電車経路未発見: departure=%s, destination=%s", departure, destination
            )
            return {
                "success": False,
                "message": "申し訳ありません。指定された経路の運賃データが見つかりませんでした。交通費を手動で入力してください。",
            }
        return {"success": True, "fare": fare, "calculation_basis": "電車経路テーブル参照"}
    else:
        fare = _fare_loader.fixed_fares_data.get(transport_type)
        if fare is None:
            return {
                "success": False,
                "message": f"申し訳ありません。「{transport_type}」の固定運賃データが見つかりませんでした。交通費を手動で入力してください。",
            }
        return {"success": True, "fare": fare, "calculation_basis": "固定運賃参照"}
