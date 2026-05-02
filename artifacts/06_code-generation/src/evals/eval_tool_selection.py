"""AG-001 ツール選択精度評価スクリプト（MET-010）

評価レベル: TOOL_LEVEL
  - ToolSelectionAccuracyEvaluator が trajectory のツール呼び出しを LLM-as-Judge で判定

実行方法:
    python evals/eval_tool_selection.py
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
    memory_exporter,
    get_model,
    create_invocation_state,
)
from strands_evals import Case, Experiment
from strands_evals.evaluators import ToolSelectionAccuracyEvaluator
from strands_evals.mappers import StrandsInMemorySessionMapper

_LOGS_DIR = os.path.join("evals", "logs")
os.makedirs(_LOGS_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(_LOGS_DIR, "eval_tool_selection.log"),
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
        name="TC-001_transport_expense_routing",
        input="先日、新幹線で出張しました。交通費を精算したいです。",
        metadata={
            "task_description": "交通費精算申請テキストに対して AG-002（transport_agent_tool）を選択すること",
            "expected_tool": "transport_agent_tool",
        },
    ),
    Case(
        name="TC-002_expense_reimbursement_routing",
        input="コンビニで業務用の文房具を買いました。経費精算をお願いします。",
        metadata={
            "task_description": "経費精算申請テキストに対して AG-003（expense_agent_tool）を選択すること",
            "expected_tool": "expense_agent_tool",
        },
    ),
    Case(
        name="TC-003_ambiguous_input",
        input="申請の手続きをお願いします。",
        metadata={
            "task_description": "申請種別が不明な入力に対して、AG-001 が選択肢提示（CF-002）を行い、AG-002/AG-003 のどちらも呼び出さないこと",
            "expected_tool": "",
        },
    ),
]


def run_eval_task(case: Case) -> dict:
    """シングルターン評価タスク関数。"""
    session_id = case.session_id
    logger.info("=== ケース '%s' 開始 (session: %s) ===", case.name, session_id)

    memory_exporter.clear()

    agent = create_reception_agent(session_id)
    state = create_invocation_state(session_id)

    result = agent(case.input, invocation_state=state.model_dump())
    response = str(result)

    logger.info("ケース '%s': response='%s'", case.name, response[:100])

    finished_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    return {"output": response, "trajectory": session}


def main():
    print("\n" + "=" * 70)
    print("AG-001 ツール選択精度評価（MET-010）")
    print("=" * 70)

    logger.info("=== eval_tool_selection 開始 ===")

    evaluator = ToolSelectionAccuracyEvaluator(model=get_model())

    experiment = Experiment(
        cases=EVAL_CASES,
        evaluators=[evaluator],
    )

    reports = experiment.run_evaluations(run_eval_task)

    report_path = os.path.join(_LOGS_DIR, "eval_tool_selection_report.json")
    for report in reports:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("レポート保存: %s", report_path)
        report.run_display()


if __name__ == "__main__":
    main()
