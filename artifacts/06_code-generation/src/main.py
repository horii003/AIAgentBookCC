"""申請受付AIシステム - メインエントリーポイント"""
import logging
import os
import sys
import warnings

from dotenv import load_dotenv

load_dotenv()

_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()

os.makedirs("logs", exist_ok=True)
_file_handler = logging.FileHandler("logs/error.log", encoding="utf-8")
_file_handler.setLevel(logging.WARNING)
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(getattr(logging, _log_level, logging.WARNING))
_console_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
)

logging.basicConfig(
    level=getattr(logging, _log_level, logging.WARNING),
    handlers=[_file_handler, _console_handler],
)

warnings.filterwarnings("ignore")

_logger = logging.getLogger(__name__)


def main() -> None:
    from handlers.error_handler import ErrorHandler
    from tools.transport_tools import _fare_loader

    error_handler = ErrorHandler()

    ok_train, msg_train = _fare_loader.load_train_routes()
    if not ok_train:
        print(msg_train)
        sys.exit(1)

    ok_fixed, msg_fixed = _fare_loader.load_fixed_fares()
    if not ok_fixed:
        print(msg_fixed)
        sys.exit(1)

    _logger.info("[MAIN] 申請受付AIシステム起動")

    from agents.orchestrator_agent import OrchestratorApp
    try:
        OrchestratorApp().run()
    except Exception as e:
        _logger.error("[MAIN] 予期しないエラー: %s", str(e), exc_info=True)
        print(error_handler.handle_unexpected_error(e))
        sys.exit(1)

    _logger.info("[MAIN] 申請受付AIシステム正常終了")


if __name__ == "__main__":
    main()
