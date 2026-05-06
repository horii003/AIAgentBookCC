# 参照: DD-02a 申請受付窓口エージェント詳細設計書, SD-06 共通設定方針
"""マルチエージェント申請支援アプリケーション - メインエントリーポイント

環境変数の読み込み、ログ設定、申請受付窓口エージェント（AG-001）の起動を行う。
"""
import sys
import os
import logging
import warnings
from dotenv import load_dotenv

# .envファイルを読み込み（AWS認証情報・ガードレールID等）
load_dotenv()

# R10: ログ設定
_log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=getattr(logging, _log_level, logging.WARNING),
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/error.log", encoding="utf-8"),
    ],
)

# R10: warnings非表示（エンドユーザー向け）
warnings.filterwarnings("ignore")

# R10: Strandsイベントループログレベル抑制（スタックトレース非表示）
logging.getLogger("strands.event_loop.event_loop").setLevel(logging.CRITICAL)
logging.getLogger("strands").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    """メイン関数。申請受付窓口エージェントを起動する。"""
    from agents.orchestrator_agent import OrchestratorAgent

    logger.info("システム起動")

    # 申請者名をCLI引数またはプロンプト入力で取得する
    if len(sys.argv) > 1:
        applicant_name = sys.argv[1]
    else:
        applicant_name = input("申請者名を入力してください: ").strip()
        if not applicant_name:
            print("申請者名が入力されていません。システムを終了します。")
            return

    # OrchestratorAgentを生成して対話ループを開始する
    agent = OrchestratorAgent(applicant_name=applicant_name)
    agent.run()

    logger.info("システム正常終了")


if __name__ == "__main__":
    main()
