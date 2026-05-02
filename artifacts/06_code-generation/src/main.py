"""マルチエージェントアプリケーション - メインエントリーポイント"""
import sys
import os
import logging
import warnings
from datetime import date

from dotenv import load_dotenv
from handlers.human_approval_hook import patch_human_approval_hook
from handlers.error_handler import ErrorHandler
from agents.orchestrator_agent import create_orchestrator_agent
from session.session_manager import SessionManagerFactory

load_dotenv()

_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.WARNING),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

MAX_INPUT_LENGTH = 500
RESET_COMMANDS = {"reset", "リセット", "最初から"}
QUIT_COMMANDS = {"quit", "exit"}
WELCOME_MESSAGE = "社内申請AIアシスタントへようこそ。交通費精算申請・経費精算申請のお手続きをサポートします。"
RESET_MESSAGE = "リセットしました。最初からやり直します。お名前を入力してください。"


def _get_applicant_name() -> str:
    while True:
        name = input("申請者名を入力してください: ").strip()
        if name:
            return name
        print("申請者名を入力してください。")


def main():
    patch_human_approval_hook()

    error_handler = ErrorHandler()
    logger.info("[SYS] システム起動")

    print(WELCOME_MESSAGE)

    applicant_name = _get_applicant_name()
    application_date = date.today().isoformat()

    session_manager = SessionManagerFactory.create()
    session_id = session_manager.create_session(applicant_name, application_date)

    invocation_state = {
        "session_id": session_id,
        "applicant_name": applicant_name,
        "application_date": application_date,
    }

    agent = create_orchestrator_agent()

    while True:
        try:
            user_input = input("\n\n入力内容（終了時はquit）: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n終了します。")
            break

        if user_input.lower() in QUIT_COMMANDS:
            print("終了します。")
            break

        if user_input in RESET_COMMANDS:
            print(RESET_MESSAGE)
            applicant_name = _get_applicant_name()
            application_date = date.today().isoformat()
            session_id = session_manager.create_session(applicant_name, application_date)
            invocation_state = {
                "session_id": session_id,
                "applicant_name": applicant_name,
                "application_date": application_date,
            }
            agent = create_orchestrator_agent()
            continue

        if not user_input:
            print("申請内容を入力してください。")
            continue

        if len(user_input) > MAX_INPUT_LENGTH:
            print(f"申請内容は{MAX_INPUT_LENGTH}文字以内で入力してください（現在{len(user_input)}文字）。")
            continue

        try:
            response = agent(user_input, invocation_state=invocation_state)
            print(str(response))
        except Exception as e:
            logger.error(f"[ERR] エージェント実行エラー: {str(e)[:100]}")
            print(error_handler.handle_unexpected_error(e))

    logger.info("[SYS] システム正常終了")


if __name__ == "__main__":
    main()
