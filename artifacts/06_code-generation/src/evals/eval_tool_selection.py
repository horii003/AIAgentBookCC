# 参照: DD-06 ツール選択精度・ゴール達成率評価テスト詳細設計書 5.2節, 6.2〜6.3節, 7.1節
"""ツール選択精度評価スクリプト（MET-001 EV-001）

評価レベル: TOOL_LEVEL
評価器クラス: ToolSelectionAccuracyEvaluator
実行方式: シングルターン
スコア形式: 二値（1.0/0.0）

実行方法:
    python evals/eval_tool_selection.py
"""

import sys
import os

# ---- 初期設定（必須・順序固定） ----
# [1] 標準入出力 UTF-8 設定（Windows環境での日本語文字化け防止）
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
from helpers import patch_human_approval_hook, create_reception_agent, memory_exporter, get_model, create_invocation_state
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
            os.path.join(_LOGS_DIR, "eval_tool_selection.log"),
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
    from strands_evals.evaluators import ToolSelectionAccuracyEvaluator
    from strands_evals.mappers import StrandsInMemorySessionMapper
    _EVALS_AVAILABLE = True
except ImportError:
    _EVALS_AVAILABLE = False
    logger.warning("strands-agents-evalsがインストールされていないため評価機能は制限されます。")


# ================================================================
# テストケース定義（DD-06 5.2節）
# ================================================================

if _EVALS_AVAILABLE:
    EVAL_CASES = [
        # TC-001: 交通費精算申請への振り分け（明確な交通費意図: タクシー）
        Case(
            name="TC-001-transport-clear",
            input="タクシー代を精算したい",
            metadata={
                "task_description": "明確な交通費意図（タクシー）からAG-002への振り分けを検証する",
                "expected_tool": "transport_agent_tool",
            },
        ),
        # TC-002: 交通費精算申請への振り分け（電車意図）
        Case(
            name="TC-002-transport-train",
            input="電車の交通費を申請したい",
            metadata={
                "task_description": "明確な交通費意図（電車）からAG-002への振り分けを検証する",
                "expected_tool": "transport_agent_tool",
            },
        ),
        # TC-003: 経費精算申請への振り分け（宿泊費意図）
        Case(
            name="TC-003-expense-hotel",
            input="ホテルの宿泊費を精算したい",
            metadata={
                "task_description": "明確な経費意図（宿泊費）からAG-003への振り分けを検証する",
                "expected_tool": "expense_agent_tool",
            },
        ),
        # TC-004: 経費精算申請への振り分け（会食費意図）
        Case(
            name="TC-004-expense-dining",
            input="取引先との会食費を申請したい",
            metadata={
                "task_description": "明確な経費意図（会食費）からAG-003への振り分けを検証する",
                "expected_tool": "expense_agent_tool",
            },
        ),
        # TC-005: 経費精算申請への振り分け（事務用品意図）
        Case(
            name="TC-005-expense-supplies",
            input="事務用品を購入したので申請したい",
            metadata={
                "task_description": "明確な経費意図（事務用品費）からAG-003への振り分けを検証する",
                "expected_tool": "expense_agent_tool",
            },
        ),
    ]
else:
    EVAL_CASES = []


# ================================================================
# タスク関数（DD-06 6.2〜6.3節: シングルターン評価）
# ================================================================

def run_eval_task(case) -> dict:
    """Experiment に渡す task 関数（シングルターン評価）。

    ツール選択精度はAG-001の最初のLLM推論で確認できるため、1ターンで評価が完結する。

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

    # ---- 1ターンだけ送信（ツール選択の判定に十分）----
    result = agent(case.input, invocation_state=state)
    response = str(result)

    logger.info("ケース '%s' 実行完了: output=%s", case.name, response[:100])

    finished_spans = memory_exporter.get_finished_spans()
    logger.info("ケース '%s' trajectory取得完了: spans=%d", case.name, len(finished_spans))

    mapper = StrandsInMemorySessionMapper()
    session = mapper.map_to_session(finished_spans, session_id=session_id)

    return {"output": response, "trajectory": session}


# ================================================================
# メイン（DD-06 7.1節）
# ================================================================

def main():
    print("\n" + "=" * 70)
    print("=== ツール選択精度評価 (MET-001) 開始 ===")
    print("=" * 70)

    if not _EVALS_AVAILABLE:
        print("strands-agents-evalsがインストールされていないため評価を実行できません。")
        print("pip install strands-agents-evals を実行してください。")
        return

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

    print("=== 評価完了 ===")


if __name__ == "__main__":
    main()
