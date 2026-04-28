"""申請書生成ツール（TOOL-002）の実装

交通費精算申請書（generate_transport_expense_form）と
経費精算申請書（generate_expense_form）を Excel/.xlsx 形式で生成する。
"""
import logging
import os
from datetime import datetime
from typing import List, Tuple

import openpyxl
from pydantic import ValidationError
from strands import tool, ToolContext

from handlers.error_handler import ErrorHandler
from models.data_models import (
    ExpenseApplicationFormInput,
    ExpenseItem,
    TransportApplicationFormInput,
    TransportItem,
)

_logger = logging.getLogger(__name__)
_error_handler = ErrorHandler()

_TRANSPORT_TEMPLATE_PATH = "data/templates/交通費申請書_template.xlsx"
_EXPENSE_TEMPLATE_PATH = "data/templates/経費精算申請書_template.xlsx"

_TRANSPORT_REQUIRED_KEYS = {
    "no", "transport_date", "departure", "destination",
    "transport_type", "amount", "business_purpose",
}
_EXPENSE_REQUIRED_KEYS = {
    "no", "purchase_date", "store_name", "item_name",
    "expense_category", "amount", "business_purpose",
}


def _save_file(wb: openpyxl.Workbook, file_path: str) -> Tuple[bool, str]:
    """Excelファイルを保存し、成否を返す"""
    try:
        wb.save(file_path)
        return True, file_path
    except PermissionError as exc:
        return False, _error_handler.handle_file_save_error(exc)
    except IOError as exc:
        return False, _error_handler.handle_file_save_error(exc)
    except Exception as exc:
        return False, _error_handler.handle_unexpected_error(exc)


@tool(context=True)
def generate_transport_expense_form(
    tool_context: ToolContext,
    segments: List[dict],
    business_purpose: str,
) -> dict:
    """交通費精算申請書ドラフト（Excel/.xlsx）を生成する。

    Human-in-the-Loop承認（BeforeToolCallEvent OK）取得後にのみ呼び出すこと。
    収集済み交通費申請情報を申請書テンプレートの所定セルに書き込み、data/output/{session_id}/ に保存する。
    申請者名・申請日はツール関数内部で invocation_state から取得する（LLMがパラメータとして渡さない）。

    Args:
        segments (list[dict]): 移動区間リスト（1件以上）。各要素は以下のキーを持つ辞書:
            - no (int): 行番号
            - transport_date (str): 移動日（YYYY-MM-DD形式）
            - departure (str): 出発地
            - destination (str): 目的地
            - transport_type (str): 交通手段
            - amount (int): 費用（円）
            - business_purpose (str): 業務目的
        business_purpose (str): 申請全体の業務目的。

    Returns:
        dict: {
            "success": bool,
            "file_path": str,  # 成功時: 生成したファイルのパス
            "message": str     # 失敗時: ユーザー向けエラーメッセージ
        }
    """
    applicant_name = tool_context.invocation_state.get("applicant_name", "")
    application_date = tool_context.invocation_state.get("application_date", "")
    session_id = tool_context.invocation_state.get("session_id", "unknown")

    _logger.info(
        "[TL-002a] generate_transport_expense_form 開始: applicant_name=***, segments=%d件",
        len(segments) if segments else 0,
    )

    # 必須キーガード
    for i, seg in enumerate(segments or []):
        missing = _TRANSPORT_REQUIRED_KEYS - set(seg.keys())
        if missing:
            return {
                "success": False,
                "message": f"移動区間データに必須項目が不足しています。不足項目: {', '.join(sorted(missing))}",
            }

    output_dir = f"data/output/{session_id}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = f"{output_dir}/transport_expense_{timestamp}.xlsx"

    try:
        validated = TransportApplicationFormInput(
            applicant_name=applicant_name,
            application_date=application_date,
            items=[TransportItem(**seg) for seg in segments],
            business_purpose=business_purpose,
        )
    except ValidationError as exc:
        _logger.error("[TL-002a] 入力バリデーションエラー: %s, file_path=%s", exc, file_path)
        return {"success": False, "message": _error_handler.handle_validation_error(exc)}
    except Exception as exc:
        _logger.error("[TL-002a] 想定外エラー: %s, file_path=%s", exc, file_path, exc_info=True)
        return {"success": False, "message": _error_handler.handle_unexpected_error(exc)}

    if not os.path.exists(_TRANSPORT_TEMPLATE_PATH):
        _logger.warning("[TL-002a] テンプレートファイル未存在: file_path=%s", _TRANSPORT_TEMPLATE_PATH)
        return {
            "success": False,
            "message": "申し訳ありません。申請書テンプレートが見つかりません。システム管理者にご連絡ください。",
        }

    try:
        wb = openpyxl.load_workbook(_TRANSPORT_TEMPLATE_PATH)
        ws = wb.active

        ws["B3"] = validated.applicant_name
        ws["B4"] = validated.application_date.isoformat()

        n = len(validated.items)
        for i, item in enumerate(validated.items):
            row = 7 + i
            ws[f"A{row}"] = i + 1
            ws[f"B{row}"] = item.transport_date
            ws[f"C{row}"] = item.departure
            ws[f"D{row}"] = item.destination
            ws[f"E{row}"] = item.transport_type
            ws[f"F{row}"] = item.amount
            ws[f"G{row}"] = item.business_purpose

        ws[f"F{7 + n + 2}"] = sum(item.amount for item in validated.items)

        os.makedirs(output_dir, exist_ok=True)
        ok, result = _save_file(wb, file_path)

        if ok:
            _logger.info("[TL-002a] generate_transport_expense_form 完了: file_path=%s", file_path)
            return {"success": True, "file_path": file_path}
        else:
            return {"success": False, "message": result}

    except Exception as exc:
        _logger.error("[TL-002a] 想定外エラー: %s, file_path=%s", exc, file_path, exc_info=True)
        return {"success": False, "message": _error_handler.handle_unexpected_error(exc)}


@tool(context=True)
def generate_expense_form(
    tool_context: ToolContext,
    items: List[dict],
    business_purpose: str,
) -> dict:
    """経費精算申請書ドラフト（Excel/.xlsx）を生成する。

    Human-in-the-Loop承認（BeforeToolCallEvent OK）取得後にのみ呼び出すこと。
    収集済み経費申請情報を申請書テンプレートの所定セルに書き込み、data/output/{session_id}/ に保存する。
    申請者名・申請日はツール関数内部で invocation_state から取得する（LLMがパラメータとして渡さない）。

    Args:
        items (list[dict]): 経費明細リスト（1件以上）。各要素は以下のキーを持つ辞書:
            - no (int): 行番号
            - purchase_date (str): 購入日（YYYY-MM-DD形式）
            - store_name (str): 店舗名
            - item_name (str): 品目
            - expense_category (str): 経費区分（「事務用品費」「宿泊費」「資格精算費」「その他経費」）
            - amount (int): 金額（円）
            - business_purpose (str): 業務目的
        business_purpose (str): 申請全体の業務目的。

    Returns:
        dict: {
            "success": bool,
            "file_path": str,  # 成功時: 生成したファイルのパス
            "message": str     # 失敗時: ユーザー向けエラーメッセージ
        }
    """
    applicant_name = tool_context.invocation_state.get("applicant_name", "")
    application_date = tool_context.invocation_state.get("application_date", "")
    session_id = tool_context.invocation_state.get("session_id", "unknown")

    _logger.info(
        "[TL-002b] generate_expense_form 開始: applicant_name=***, items=%d件",
        len(items) if items else 0,
    )

    # 必須キーガード
    for i, item in enumerate(items or []):
        missing = _EXPENSE_REQUIRED_KEYS - set(item.keys())
        if missing:
            return {
                "success": False,
                "message": f"経費明細データに必須項目が不足しています。不足項目: {', '.join(sorted(missing))}",
            }

    output_dir = f"data/output/{session_id}"
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = f"{output_dir}/expense_{timestamp}.xlsx"

    try:
        validated = ExpenseApplicationFormInput(
            applicant_name=applicant_name,
            application_date=application_date,
            items=[ExpenseItem(**item) for item in items],
            business_purpose=business_purpose,
        )
    except ValidationError as exc:
        _logger.error("[TL-002b] 入力バリデーションエラー: %s, file_path=%s", exc, file_path)
        return {"success": False, "message": _error_handler.handle_validation_error(exc)}
    except Exception as exc:
        _logger.error("[TL-002b] 想定外エラー: %s, file_path=%s", exc, file_path, exc_info=True)
        return {"success": False, "message": _error_handler.handle_unexpected_error(exc)}

    if not os.path.exists(_EXPENSE_TEMPLATE_PATH):
        _logger.warning("[TL-002b] テンプレートファイル未存在: file_path=%s", _EXPENSE_TEMPLATE_PATH)
        return {
            "success": False,
            "message": "申し訳ありません。申請書テンプレートが見つかりません。システム管理者にご連絡ください。",
        }

    try:
        wb = openpyxl.load_workbook(_EXPENSE_TEMPLATE_PATH)
        ws = wb.active

        ws["B3"] = validated.applicant_name
        ws["B4"] = validated.application_date.isoformat()

        n = len(validated.items)
        for i, item in enumerate(validated.items):
            row = 7 + i
            ws[f"A{row}"] = i + 1
            ws[f"B{row}"] = item.purchase_date
            ws[f"C{row}"] = item.store_name
            ws[f"D{row}"] = item.item_name
            ws[f"E{row}"] = item.expense_category
            ws[f"F{row}"] = item.amount
            ws[f"G{row}"] = item.business_purpose

        ws[f"F{7 + n + 2}"] = sum(item.amount for item in validated.items)

        os.makedirs(output_dir, exist_ok=True)
        ok, result = _save_file(wb, file_path)

        if ok:
            _logger.info("[TL-002b] generate_expense_form 完了: file_path=%s", file_path)
            return {"success": True, "file_path": file_path}
        else:
            return {"success": False, "message": result}

    except Exception as exc:
        _logger.error("[TL-002b] 想定外エラー: %s, file_path=%s", exc, file_path, exc_info=True)
        return {"success": False, "message": _error_handler.handle_unexpected_error(exc)}
