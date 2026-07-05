"""業務ゴール達成率評価スクリプト（MET-003）

AG-001（申請受付窓口エージェント）を起点としてマルチターン会話を実行し、
交通費精算・経費精算申請のE2Eフロー完了を GoalSuccessRateEvaluator で判定する。

評価レベル: セッションレベル（マルチターン）
  - StrandsEvalsTelemetry でエージェントの実行スパンを自動キャプチャ
  - StrandsInMemorySessionMapper でスパンから Session を自動構築
  - GoalSuccessRateEvaluator が全ターン・全ツール呼び出しを LLM-as-Judge で判定

実行方法:
    python evals/eval_goal_success_rate.py
"""

import sys
import os
import json
import logging
import warnings
from dotenv import load_dotenv
from helpers import (
    patch_human_approval_hook, create_orchestrator_agent, run_actor_conversation,
    memory_exporter, get_model, create_invocation_state,
    generate_session_id,
)
from strands_evals import Case, Experiment
from strands_evals.evaluators import GoalSuccessRateEvaluator
from strands_evals.mappers import StrandsInMemorySessionMapper

# ---- 初期設定（必須・順序固定） ----
# [1] 標準入出力 UTF-8 設定
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
# [2] sys.path へプロジェクトルート追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# [3] load_dotenv
load_dotenv()
# [4] patch_human_approval_hook（load_dotenv の直後に必須）
patch_human_approval_hook()

# ---- ログ設定 ----
# [5] ログ設定
_LOGS_DIR = os.path.join("evals", "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(_LOGS_DIR, "eval_goal_success_rate.log"),
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)
# [6] warnings 抑制
warnings.filterwarnings("ignore")
# [7] strands SDK ログ抑制（評価時は不要なため）
logging.getLogger("strands").setLevel(logging.WARNING)
logging.getLogger("strands.event_loop.event_loop").setLevel(logging.CRITICAL)


# ================================================================
# テストケース定義（Case オブジェクト）
# ================================================================

from cases.goal_success_rate_cases import GOAL_SUCCESS_RATE_CASES

EVAL_CASES = GOAL_SUCCESS_RATE_CASES


# ================================================================
# タスク関数（Experiment に渡す）
# ================================================================

def run_eval_task(case: Case) -> dict:
    """Experiment に渡す task 関数（マルチターン評価）。

    Args:
        case: strands_evals Case オブジェクト

    Returns:
        dict: {"output": 最終応答, "trajectory": Session オブジェクト}
    """
    session_id = generate_session_id()
    logger.info("=== ケース '%s' 開始 (session: %s) ===", case.name, session_id)

    # 前のケースのスパンが混入しないようにリセット（必須）
    memory_exporter.clear()

    # ---- エージェント作成 ----
    agent = create_orchestrator_agent(session_id)

    # ---- InvocationState ----
    state = create_invocation_state(session_id)

    # ---- ActorSimulator による動的会話実行 ----
    turns = run_actor_conversation(agent, case, state.model_dump())

    # ---- テレメトリスパンから Session を自動構築 ----
    finished_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    final_response = turns[-1]["agent_response"] if turns else ""

    return {"output": final_response, "trajectory": session}


# ================================================================
# メイン
# ================================================================

def main():
    print("\n" + "=" * 70)
    print("MET-003 業務ゴール達成率評価（GoalSuccessRateEvaluator）")
    print("=" * 70)

    evaluator = GoalSuccessRateEvaluator(model=get_model())
    logger.info("GoalSuccessRateEvaluator を初期化しました")

    experiment = Experiment(
        cases=EVAL_CASES,
        evaluators=[evaluator],
    )

    reports = experiment.run_evaluations(run_eval_task)

    report_path = os.path.join(_LOGS_DIR, "eval_goal_success_rate_report.json")
    for report in reports:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("評価完了: レポート → %s", report_path)
        report.run_display()


if __name__ == "__main__":
    main()
