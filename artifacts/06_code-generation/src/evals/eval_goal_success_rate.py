"""AG-001/AG-002/AG-003 ゴール達成率評価スクリプト（MET-011）

評価レベル: SESSION_LEVEL
  - ActorSimulator でマルチターン会話を実行
  - GoalSuccessRateEvaluator が全ターンを LLM-as-Judge で判定

実行方法:
    python evals/eval_goal_success_rate.py
"""
import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from helpers import patch_human_approval_hook
patch_human_approval_hook()

import json
import logging
import warnings

from helpers import (
    create_reception_agent,
    run_actor_conversation,
    memory_exporter,
    get_model,
    create_invocation_state,
)
from strands_evals import Case, Experiment
from strands_evals.evaluators import GoalSuccessRateEvaluator
from strands_evals.mappers import StrandsInMemorySessionMapper

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

warnings.filterwarnings("ignore")
logging.getLogger("strands").setLevel(logging.WARNING)
logging.getLogger("strands.event_loop.event_loop").setLevel(logging.CRITICAL)


EVAL_CASES = [
    Case(
        name="TC-001_transport_expense_e2e",
        input="先日、電車で営業先を訪問しました。交通費精算をお願いします。",
        metadata={
            "task_description": "交通費精算申請のエンドツーエンドフロー（CF-003→CF-005）で申請書（下書き）の生成が完了すること",
            "goal": "交通費精算申請書（下書き）の生成が完了し、エージェントが申請書の場所を案内していること",
        },
    ),
    Case(
        name="TC-002_expense_reimbursement_e2e",
        input="先日、コンビニで業務用の文房具を購入しました。経費精算をお願いします。",
        metadata={
            "task_description": "経費精算申請のエンドツーエンドフロー（CF-004→CF-005）で申請書（下書き）の生成が完了すること",
            "goal": "経費精算申請書（下書き）の生成が完了し、エージェントが申請書の場所を案内していること",
        },
    ),
    Case(
        name="TC-003_deadline_exceeded_escalation",
        input="3か月以上前に電車で出張しました。交通費精算をしたいです。",
        metadata={
            "task_description": "申請期限（90日）を超過した入力に対してエスカレーション案内（OUT-005）が行われること",
            "goal": "申請期限超過として申請不可を通知し、担当部門への問い合わせを案内していること（BRL-14）",
        },
    ),
    Case(
        name="TC-004_turn_limit_escalation",
        input="申請について相談したいことがあります。",
        metadata={
            "task_description": "対話ターン数が30回に達した場合にエスカレーション案内（GRD-005）が行われること",
            "goal": "対話ターン数上限（30回）に達した旨を通知し、担当部門への問い合わせを案内していること（GRD-005）",
        },
    ),
]


def run_eval_task(case: Case) -> dict:
    """マルチターン評価タスク関数。"""
    session_id = case.session_id
    logger.info("=== ケース '%s' 開始 (session: %s) ===", case.name, session_id)

    memory_exporter.clear()

    agent = create_reception_agent(session_id)
    state = create_invocation_state(session_id)

    turns = run_actor_conversation(agent, case, state.model_dump())

    finished_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    final_response = turns[-1]["agent_response"] if turns else ""

    return {"output": final_response, "trajectory": session}


def main():
    print("\n" + "=" * 70)
    print("AG-001/AG-002/AG-003 ゴール達成率評価（MET-011）")
    print("=" * 70)

    logger.info("=== eval_goal_success_rate 開始 ===")

    evaluator = GoalSuccessRateEvaluator(model=get_model())

    experiment = Experiment(
        cases=EVAL_CASES,
        evaluators=[evaluator],
    )

    reports = experiment.run_evaluations(run_eval_task)

    report_path = os.path.join(_LOGS_DIR, "eval_goal_success_rate_report.json")
    for report in reports:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("レポート保存: %s", report_path)
        report.run_display()


if __name__ == "__main__":
    main()
