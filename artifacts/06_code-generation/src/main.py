"""マルチエージェントアプリケーション - メインエントリーポイント"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)

os.makedirs("logs", exist_ok=True)

_fmt = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
_formatter = logging.Formatter(_fmt)

_app_handler = RotatingFileHandler(
    "logs/app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_app_handler.setLevel(logging.INFO)
_app_handler.setFormatter(_formatter)

_error_handler_file = RotatingFileHandler(
    "logs/error.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_error_handler_file.setLevel(logging.ERROR)
_error_handler_file.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)

logging.basicConfig(
    level=log_level,
    handlers=[_console_handler, _app_handler, _error_handler_file],
)

logging.getLogger("strands").setLevel(logging.WARNING)

from agents.orchestrator_agent import OrchestratorAgent
from agents.transport_application_agent import transport_application_agent
from agents.expense_application_agent import expense_application_agent
from handlers.error_handler import ErrorHandler


def main():
    """メイン関数"""

    _logger = logging.getLogger(__name__)

    try:
        _logger.info("システム起動")
        agent = OrchestratorAgent()
        agent.run(transport_application_agent, expense_application_agent)
        _logger.info("システム正常終了")
    except KeyboardInterrupt:
        print(ErrorHandler.handle_keyboard_interrupt())
        _logger.info("システム終了（KeyboardInterrupt）")
    except Exception as e:
        _logger.error("システムエラー error=%s", str(e), exc_info=True)
        print(ErrorHandler.handle_unexpected_error(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
