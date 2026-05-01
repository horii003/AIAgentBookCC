"""経費精算申請マルチエージェントシステム - メインエントリーポイント"""
import logging
import os
import sys
import warnings

from dotenv import load_dotenv

load_dotenv()


warnings.filterwarnings("ignore")

_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
_log_file = os.getenv("LOG_FILE", "logs/app.log")

os.makedirs(os.path.dirname(_log_file), exist_ok=True)

logging.basicConfig(
    level=getattr(logging, _log_level, logging.WARNING),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(_log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Strands イベントループのログを抑制する
logging.getLogger("strands").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

logger = logging.getLogger("main")


def _get_applicant_name() -> str:
    """申請者名を入力させる。空欄の場合は再入力を促す。

    Returns:
        str: 申請者名
    """
    while True:
        name = input("申請者名を入力してください: ").strip()
        if name:
            return name
        print("申請者名を入力してください。空欄は使用できません。")


def main() -> None:
    """メイン関数"""
    from agents.orchestrator_agent import run

    logger.info("経費精算申請システム起動")

    try:
        run()
    except KeyboardInterrupt:
        print("\nシステムを終了しました。")
    except Exception as e:
        from handlers.error_handler import ErrorHandler
        logger.error("システム起動エラー", exc_info=True)
        print(ErrorHandler.handle_unexpected_error(e))
        sys.exit(1)

    logger.info("経費精算申請システム正常終了")


if __name__ == "__main__":
    # Windows環境でUTF-8 I/Oを強制する
    if sys.platform == "win32":
        import io
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    main()
