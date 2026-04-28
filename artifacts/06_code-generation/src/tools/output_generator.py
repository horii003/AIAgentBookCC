"""申請書生成ツール

交通費精算申請書・経費精算申請書のExcelドラフトを生成する。
"""
import logging
import os
from datetime import datetime

import openpyxl
from pydantic import ValidationError
from strands import tool
from strands.types.tools import ToolContext

from handlers.error_handler import ErrorHandler
from models.data_models import TravelApplicationFormInput

logger = logging.getLogger(__name__)

_error_handler = ErrorHandler()

TRAVEL_TEMPLATE_FILE = "data/templates/交通費申請書_template.xlsx"
EXPENSE_TEMPLATE_FILE = "data/templates/経費精算申請書_template.xlsx"
OUTPUT_DIR = "data/output"


def _save_file(wb: openpyxl.Workbook, file_path: str) -> tuple[bool, str]:
    try:
        wb.save(file_path)
        return (True, "")
    except PermissionError as e:
        msg = _error_handler.handle_file_save_error(e)
        logger.error(
            "File write error in generate_travel_expense_form: file_path=%s, error=%s",
            file_path,
            e,
        )
        return (False, msg)
    except IOError as e:
        msg = _error_handler.handle_file_save_error(e)
        logger.error(
            "File write error in generate_travel_expense_form: file_path=%s, error=%s",
            file_path,
            e,
        )
        return (False, msg)
    except Exception as e:
        msg = _error_handler.handle_unexpected_error(e)
        logger.critical(
            "Unexpected error in _save_file: file_path=%s, error=%s",
            file_path,
            e,
            exc_info=True,
        )
        return (False, msg)


@tool(context=True)
def generate_travel_expense_form(
    items: list[dict],
    business_purpose: str,
    tool_context: ToolContext,
) -> dict:
    """交通費精算申請書（Excel/.xlsx）のドラフトを生成して data/output/{session_id}/ に保存する。

    HumanApprovalHook（BeforeToolCallEvent）による承認OK取得後にのみ呼び出すこと。
    出力ファイルパスはツール内部でタイムスタンプを使用して自律的に生成する。

    申請者名・申請日・session_id はLLMがツールパラメータとして渡す値ではなく、
    invocation_stateからツール関数内部で取得する（@tool(context=True) デコレーター使用）。

    Args:
        items (list[dict]): 移動区間リスト（1件以上）。各要素は以下のキーを持つ辞書:
            - travel_date (str): 移動日（YYYY-MM-DD形式）
            - departure (str): 出発地（min_length=1）
            - destination (str): 目的地（min_length=1）
            - transport_type (str): 交通手段（"電車"/"バス"/"タクシー"/"飛行機"）
            - amount (int または str): 費用（円、0以上。"1,000円" 等の文字列も変換）
        business_purpose (str): 業務目的（min_length=1, BRL-20）

    Returns:
        dict: 成功時は {"success": True, "file_path": str}、
              失敗時は {"success": False, "message": str}
    """
    invocation_state = tool_context.invocation_state or {}
    session_id = invocation_state.get("session_id", "unknown")
    applicant_name = invocation_state.get("applicant_name", "")
    application_date = invocation_state.get("application_date", "")

    logger.info("generate_travel_expense_form called: items_count=%d", len(items))

    try:
        validated = TravelApplicationFormInput(
            applicant_name=applicant_name,
            application_date=application_date,
            items=items,
            business_purpose=business_purpose,
        )
    except ValidationError as e:
        error_message = _error_handler.handle_validation_error(e)
        logger.error(
            "ValidationError in generate_travel_expense_form: %s, session_id=%s",
            error_message,
            session_id,
        )
        return {"success": False, "message": error_message}

    try:
        if not os.path.exists(TRAVEL_TEMPLATE_FILE):
            logger.error(
                "Template file not found: %s, session_id=%s",
                TRAVEL_TEMPLATE_FILE,
                session_id,
            )
            return {
                "success": False,
                "message": "申し訳ありません。申請書テンプレートが見つかりません。システム管理者にご連絡ください。",
            }

        wb = openpyxl.load_workbook(TRAVEL_TEMPLATE_FILE)
        ws = wb.active

        ws["B3"] = validated.applicant_name
        ws["B4"] = str(validated.application_date)

        for i, item in enumerate(validated.items):
            row = 7 + i
            ws[f"A{row}"] = i + 1
            ws[f"B{row}"] = str(item.travel_date)
            ws[f"C{row}"] = item.departure
            ws[f"D{row}"] = item.destination
            ws[f"E{row}"] = item.transport_type
            ws[f"F{row}"] = item.amount
            ws[f"G{row}"] = business_purpose
            ws[f"H{row}"] = ""

        n = len(validated.items)
        ws[f"H{7 + n + 2}"] = sum(item.amount for item in validated.items)

        os.makedirs(f"{OUTPUT_DIR}/{session_id}", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"{OUTPUT_DIR}/{session_id}/交通費精算申請書_{timestamp}.xlsx"

        save_result = _save_file(wb, file_path)
        if not save_result[0]:
            return {"success": False, "message": save_result[1]}

        logger.info("Travel expense form generated: %s", file_path)
        return {"success": True, "file_path": file_path}

    except Exception as e:
        error_message = _error_handler.handle_unexpected_error(e)
        logger.critical(
            "Unexpected error in generate_travel_expense_form: %s, session_id=%s",
            e,
            session_id,
            exc_info=True,
        )
        return {"success": False, "message": error_message}


@tool(context=True)
def generate_expense_form(
    items: list[dict],
    business_purpose: str,
    tool_context: ToolContext,
) -> dict:
    """経費精算申請書（Excel/.xlsx）のドラフトを生成して data/output/{session_id}/ に保存する。

    HumanApprovalHook（BeforeToolCallEvent）による承認OK取得後にのみ呼び出すこと。
    出力ファイルパスはツール内部でタイムスタンプを使用して自律的に生成する。

    申請者名・申請日・session_id はLLMがツールパラメータとして渡す値ではなく、
    invocation_stateからツール関数内部で取得する（@tool(context=True) デコレーター使用）。

    Args:
        items (list[dict]): 経費明細リスト（1件以上）。各要素は以下のキーを持つ辞書:
            - purchase_date (str): 購入日（YYYY-MM-DD形式）
            - store_name (str): 店舗名（min_length=1）
            - item_name (str): 品目（min_length=1）
            - expense_category (str): 経費区分（"事務用品費"/"宿泊費"/"資格精算費"/"その他経費"）
            - amount (int または str): 金額（円、0以上。"1,000円" 等の文字列も変換）
        business_purpose (str): 業務目的（min_length=1, BRL-20）

    Returns:
        dict: 成功時は {"success": True, "file_path": str}、
              失敗時は {"success": False, "message": str}
    """
    invocation_state = tool_context.invocation_state or {}
    session_id = invocation_state.get("session_id", "unknown")
    applicant_name = invocation_state.get("applicant_name", "")
    application_date = invocation_state.get("application_date", "")

    logger.info("generate_expense_form called: items_count=%d", len(items))

    if not items:
        return {"success": False, "message": "申請明細が1件以上必要です。経費情報を入力してください。"}

    try:
        if not os.path.exists(EXPENSE_TEMPLATE_FILE):
            logger.error(
                "Template file not found: %s, session_id=%s",
                EXPENSE_TEMPLATE_FILE,
                session_id,
            )
            return {
                "success": False,
                "message": "申し訳ありません。申請書テンプレートが見つかりません。システム管理者にご連絡ください。",
            }

        wb = openpyxl.load_workbook(EXPENSE_TEMPLATE_FILE)
        ws = wb.active

        ws["B3"] = applicant_name
        ws["B4"] = str(application_date)

        total = 0
        for i, item in enumerate(items):
            row = 7 + i
            amount = item.get("amount", 0)
            if isinstance(amount, str):
                amount = int(amount.replace(",", "").replace("円", "").strip())
            ws[f"A{row}"] = i + 1
            ws[f"B{row}"] = item.get("purchase_date", "")
            ws[f"C{row}"] = item.get("store_name", "")
            ws[f"D{row}"] = item.get("item_name", "")
            ws[f"E{row}"] = item.get("expense_category", "")
            ws[f"F{row}"] = amount
            ws[f"G{row}"] = business_purpose
            ws[f"H{row}"] = ""
            total += amount

        n = len(items)
        ws[f"H{7 + n + 2}"] = total

        os.makedirs(f"{OUTPUT_DIR}/{session_id}", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_path = f"{OUTPUT_DIR}/{session_id}/経費精算申請書_{timestamp}.xlsx"

        save_result = _save_file(wb, file_path)
        if not save_result[0]:
            return {"success": False, "message": save_result[1]}

        logger.info("Expense form generated: %s", file_path)
        return {"success": True, "file_path": file_path}

    except Exception as e:
        error_message = _error_handler.handle_unexpected_error(e)
        logger.critical(
            "Unexpected error in generate_expense_form: %s, session_id=%s",
            e,
            session_id,
            exc_info=True,
        )
        return {"success": False, "message": error_message}
