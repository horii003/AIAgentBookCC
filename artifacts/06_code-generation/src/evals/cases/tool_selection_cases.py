"""MET-001 評価テストケース定義（申請種別判断正確率）

eval_tool_selection.py から参照する。
"""
from strands_evals import Case

TOOL_SELECTION_CASES = [
    Case(
        name="TC_TOOL_001",
        input="東京から新宿まで電車で出張した交通費を申請したいです。先週の月曜日に打ち合わせで行きました。",
        metadata={
            "task_description": "電車移動による交通費申請が transportation_expense_agent（交通費精算申請エージェント）に委譲されること",
            "expected_tool": "transportation_expense_agent",
        },
    ),
    Case(
        name="TC_TOOL_002",
        input="先日、業務で使う文房具を購入しました。2026年3月15日に渋谷の文具店で、ノートとペンを合計2500円分買いました。経費申請をお願いします。",
        metadata={
            "task_description": "事務用品購入の経費申請が general_expense_agent（経費精算申請エージェント）に委譲されること",
            "expected_tool": "general_expense_agent",
        },
    ),
    Case(
        name="TC_TOOL_003",
        input="品川から横浜への移動費を申請したいです。先月の営業訪問で電車を使いました。",
        metadata={
            "task_description": "電車移動による交通費申請が transportation_expense_agent（交通費精算申請エージェント）に委譲されること",
            "expected_tool": "transportation_expense_agent",
        },
    ),
]
