# 参照: DD-06 ツール選択精度・ゴール達成率評価テスト詳細設計書 5.3節, 6.4〜6.5節, 7.2節
"""ゴール達成率評価スクリプト（MET-002 EV-002）

評価レベル: SESSION_LEVEL
評価器クラス: GoalSuccessRateEvaluator
実行方式: マルチターン（ActorSimulator）
スコア形式: 二値（1.0/0.0）

実行方法:
    python evals/eval_goal_success.py
"""

import sys
import os

# ---- 初期設定（必須・順序固定） ----
# [1] 標準入出力 UTF-8 設定
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# [2] sys.path へプロジェクトルート追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# [3] load_dotenv
from dotenv import load_dotenv
load_dotenv()

# [4] patch_human_approval_hook（load_dotenv の直後に必須）
from helpers import (
    patch_human_approval_hook,
    create_reception_agent,
    run_actor_conversation,
    memory_exporter,
    get_model,
    create_invocation_state,
)
patch_human_approval_hook()

# ---- ログ設定 ----
import json
import logging
import warnings

# [5] ログ設定
_LOGS_DIR = os.path.join("evals", "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(_LOGS_DIR, "eval_goal_success.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)

# [6] warnings 抑制
warnings.filterwarnings("ignore")

# [7] strands SDK ログ抑制
logging.getLogger("strands").setLevel(logging.WARNING)
logging.getLogger("strands.event_loop.event_loop").setLevel(logging.CRITICAL)

try:
    from strands_evals import Case, Experiment
    from strands_evals.evaluators import GoalSuccessRateEvaluator
    from strands_evals.mappers import StrandsInMemorySessionMapper
    _EVALS_AVAILABLE = True
except ImportError:
    _EVALS_AVAILABLE = False
    logger.warning("strands-agents-evalsがインストールされていないため評価機能は制限されます。")


# ================================================================
# テストケース定義（DD-06 5.3節）
# ================================================================

if _EVALS_AVAILABLE:
    EVAL_CASES = [
        # TC-001: 交通費精算申請フロー完了（正常ケース）
        Case(
            name="TC-001-transport-flow-success",
            input="交通費を精算したい。先週の出張で電車代がかかりました。",
            metadata={
                "task_description": "交通費精算申請フロー全体が完了し、チェック合格済み申請書が生成されることを検証する",
                "goal": "チェック合格済みの交通費精算申請書（Excelファイル）が output/ ディレクトリに生成され、申請書のファイルパスが社員に提示されること",
            },
        ),
        # TC-002: 経費精算申請フロー完了（正常ケース）
        Case(
            name="TC-002-expense-flow-success",
            input="先日の取引先との会食費を申請したいです。",
            metadata={
                "task_description": "経費精算申請フロー全体が完了し、チェック合格済み申請書が生成されることを検証する",
                "goal": "チェック合格済みの経費精算申請書（Excelファイル）が output/ ディレクトリに生成され、申請書のファイルパスが社員に提示されること",
            },
        ),
        # TC-003: 申請期限超過によるゴール未達成
        Case(
            name="TC-003-expense-deadline-exceeded",
            input="半年前の事務用品購入費を申請したい",
            metadata={
                "task_description": "申請期限超過（90日以上）の場合にゴール未達成として申請停止メッセージが表示されることを検証する",
                "goal": "申請期限（経費発生日から90日以内）を超過しているため申請が停止され、社員にその旨が通知されること",
            },
        ),
    ]
else:
    EVAL_CASES = []


# ================================================================
# タスク関数（DD-06 6.4〜6.5節: マルチターン評価）
# ================================================================

def run_eval_task(case) -> dict:
    """Experiment に渡す task 関数（マルチターン評価）。

    ActorSimulatorがユーザー役を担い、申請フロー全体（CF-001〜CF-005）が完了するまで
    動的な会話を継続する。

    Args:
        case: strands_evals Caseオブジェクト

    Returns:
        dict: {"output": 最終応答, "trajectory": Sessionオブジェクト}
    """
    session_id = case.session_id
    logger.info("=== ケース '%s' 開始 (session: %s) ===", case.name, session_id)

    # 前のケースのスパンが混入しないようにリセット（必須）
    memory_exporter.clear()

    # エージェント作成
    agent = create_reception_agent(session_id)

    # InvocationState
    state = create_invocation_state(session_id)

    # ---- マルチターン実行（ActorSimulator）----
    turns = run_actor_conversation(agent, case, state)
    output = turns[-1]["agent_response"] if turns else ""

    logger.info("ケース '%s' 実行完了: output=%s", case.name, output[:100])

    finished_spans = memory_exporter.get_finished_spans()
    logger.info("ケース '%s' trajectory取得完了: spans=%d", case.name, len(finished_spans))

    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    return {"output": output, "trajectory": session}


# ================================================================
# メイン（DD-06 7.2節）
# ================================================================

def main():
    print("\n" + "=" * 70)
    print("=== ゴール達成率評価 (MET-002) 開始 ===")
    print("=" * 70)

    if not _EVALS_AVAILABLE:
        print("strands-agents-evalsがインストールされていないため評価を実行できません。")
        print("pip install strands-agents-evals を実行してください。")
        return

    evaluator = GoalSuccessRateEvaluator(model=get_model())
    logger.info("GoalSuccessRateEvaluator を初期化しました")

    experiment = Experiment(
        cases=EVAL_CASES,
        evaluators=[evaluator],
    )

    reports = experiment.run_evaluations(run_eval_task)

    report_path = os.path.join(_LOGS_DIR, "eval_goal_success_report.json")
    for report in reports:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("評価完了: レポート → %s", report_path)
        report.run_display()

    print("=== 評価完了 ===")


if __name__ == "__main__":
    main()
