"""申請種別判断正確率評価スクリプト（MET-001）

AG-001（申請受付窓口エージェント）が申請内容テキストを1ターン受け取り、
適切な専門エージェント（transportation_expense_agent / general_expense_agent）
に委譲するかどうかを ToolSelectionAccuracyEvaluator で検証する。

評価レベル: 出力レベル（シングルターン）
  - StrandsEvalsTelemetry でエージェントの実行スパンを自動キャプチャ
  - StrandsInMemorySessionMapper でスパンから Session を自動構築
  - ToolSelectionAccuracyEvaluator が期待ツールの呼び出し有無を判定

実行方法:
    python evals/eval_tool_selection.py
"""

import sys
import os
import json
import logging
import warnings
from dotenv import load_dotenv
from helpers import (
    patch_human_approval_hook, create_orchestrator_agent,
    memory_exporter, get_model, create_invocation_state,
    generate_session_id,
)
from strands_evals import Case, Experiment
from strands_evals.evaluators import ToolSelectionAccuracyEvaluator
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
            os.path.join(_LOGS_DIR, "eval_tool_selection.log"),
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

from cases.tool_selection_cases import TOOL_SELECTION_CASES

EVAL_CASES = TOOL_SELECTION_CASES


# ================================================================
# タスク関数（Experiment に渡す）
# ================================================================

def run_eval_task(case: Case) -> dict:
    """Experiment に渡す task 関数（シングルターン評価）。

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

    # ---- 1ターンだけ送信（ツール選択の判定に十分）----
    result = agent(case.input, invocation_state=state.model_dump())
    response = str(result)

    logger.info("ケース '%s': response='%s'", case.name, response[:100])

    finished_spans = memory_exporter.get_finished_spans()
    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    return {"output": response, "trajectory": session}


# ================================================================
# メイン
# ================================================================

def main():
    print("\n" + "=" * 70)
    print("MET-001 申請種別判断正確率評価（ToolSelectionAccuracyEvaluator）")
    print("=" * 70)

    evaluator = ToolSelectionAccuracyEvaluator(model=get_model())
    logger.info("ToolSelectionAccuracyEvaluator を初期化しました")

    experiment = Experiment(
        cases=EVAL_CASES,
        evaluators=[evaluator],
    )

    reports = experiment.run_evaluations(run_eval_task)

    report_path = os.path.join(_LOGS_DIR, "eval_tool_selection_report.json")
    for report in reports:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("評価完了: レポート → %s", report_path)
        report.run_display()


if __name__ == "__main__":
    main()
