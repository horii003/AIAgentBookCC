"""社内申請システム エントリーポイント"""
import logging
import os
import sys

from dotenv import load_dotenv


def _setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/error.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    load_dotenv()
    _setup_logging()
    logger = logging.getLogger(__name__)

    from tools.travel_tools import load_fare_data
    from handlers.error_handler import ErrorHandler

    error_handler = ErrorHandler()
    success, msg = load_fare_data()
    if not success:
        print(error_handler.handle_fare_data_error(msg))
        logger.error("Failed to load fare data: %s", msg)
        sys.exit(1)

    logger.info("Fare data loaded successfully.")

    from agents.orchestrator_agent import main as agent_main
    agent_main()


if __name__ == "__main__":
    main()
