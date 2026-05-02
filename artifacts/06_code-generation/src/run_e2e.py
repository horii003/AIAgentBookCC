"""
E2E動作確認スクリプト
申請書Excelファイルが生成されるまで自動会話を続ける。
実行: python run_e2e.py
"""
import sys
import os
import glob
import time

# UTF-8出力設定
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from handlers.human_approval_hook import patch_human_approval_hook
patch_human_approval_hook()

import logging
import warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)

from datetime import date
from agents.orchestrator_agent import create_orchestrator_agent
from session.session_manager import SessionManagerFactory


def find_output_files(before: set) -> list[str]:
    """data/output/ 配下の新しいExcelファイルを返す。"""
    all_files = set(glob.glob("data/output/**/*.xlsx", recursive=True))
    return sorted(all_files - before)


def run_e2e(scenario: str, turns: list[str]) -> tuple[bool, str]:
    """
    Args:
        scenario: シナリオ名
        turns: エージェントへ送る発話リスト（index 0 が最初のメッセージ）

    Returns:
        (成功フラグ, 生成ファイルパス or エラーメッセージ)
    """
    print(f"\n{'='*60}")
    print(f"【シナリオ】{scenario}")
    print(f"{'='*60}")

    before_files = set(glob.glob("data/output/**/*.xlsx", recursive=True))
    os.makedirs("data/output", exist_ok=True)

    session_manager = SessionManagerFactory.create()
    application_date = date.today().isoformat()
    session_id = session_manager.create_session("田中太郎", application_date)
    invocation_state = {
        "session_id": session_id,
        "applicant_name": "田中太郎",
        "application_date": application_date,
    }

    agent = create_orchestrator_agent()
    max_extra_turns = 6  # 準備済み発話以外に追加で許容するターン数

    for i, user_input in enumerate(turns):
        print(f"\n[ユーザー] {user_input}")
        try:
            response = agent(user_input, invocation_state=invocation_state)
            response_str = str(response)
        except Exception as e:
            return False, f"エラー: {e}"

        # 応答を200文字で打ち切って表示
        preview = response_str[:200] + ("..." if len(response_str) > 200 else "")
        print(f"[エージェント] {preview}")

        new_files = find_output_files(before_files)
        if new_files:
            return True, new_files[0]

    # 準備済み発話を使い切った場合、追加で汎用応答を送る
    generic_answers = [
        "はい、お願いします。",
        "はい、その内容で申請書を作成してください。",
        "内容を確認しました。申請書を生成してください。",
        "はい、間違いありません。",
        "はい、確認しました。申請書を作成してください。",
        "はい、了解しました。",
    ]
    for answer in generic_answers[:max_extra_turns]:
        print(f"\n[ユーザー（汎用応答）] {answer}")
        try:
            response = agent(answer, invocation_state=invocation_state)
            response_str = str(response)
        except Exception as e:
            return False, f"エラー: {e}"
        preview = response_str[:200] + ("..." if len(response_str) > 200 else "")
        print(f"[エージェント] {preview}")

        new_files = find_output_files(before_files)
        if new_files:
            return True, new_files[0]

    return False, "申請書ファイルが生成されませんでした"


def main():
    results = []

    # ---- シナリオ1: 交通費精算申請 ----
    turns_transport = [
        "渋谷から新宿まで電車で移動しました。交通費精算をお願いします。",
        "申請日は本日2026年5月2日です。移動日は2026年4月25日、目的は営業先への訪問です。",
        "出発地は渋谷、目的地は新宿、交通手段は電車です。",
        "移動日は2026年4月25日、目的は営業訪問です。",
        "はい、その内容で申請書を作成してください。",
    ]
    success, result = run_e2e("交通費精算申請（渋谷→新宿 電車）", turns_transport)
    results.append(("交通費精算申請", success, result))

    # ---- シナリオ2: 経費精算申請 ----
    turns_expense = [
        "コンビニで業務用のボールペンを購入しました。200円でした。経費精算をお願いします。",
        "手動入力でお願いします。",
        "購入日は2026年4月28日、店舗名はセブンイレブン渋谷店、金額は200円、品目はボールペン、業務目的は営業資料作成用です。",
        "経費区分は事務用品費でお願いします。",
        "はい、その内容で問題ありません。申請書を作成してください。",
    ]
    success2, result2 = run_e2e("経費精算申請（文房具 200円）", turns_expense)
    results.append(("経費精算申請", success2, result2))

    # ---- 結果サマリ ----
    print(f"\n{'='*60}")
    print("【E2E動作確認 結果サマリ】")
    print(f"{'='*60}")
    all_passed = True
    for name, success, result in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
        if success:
            print(f"      生成ファイル: {result}")
            # ファイルサイズ確認
            if os.path.exists(result):
                size = os.path.getsize(result)
                print(f"      ファイルサイズ: {size:,} bytes")
        else:
            print(f"      結果: {result}")
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("全シナリオ PASS — 申請書ファイルの生成を確認しました。")
    else:
        print("一部シナリオで申請書ファイルが生成されませんでした。")
    print(f"{'='*60}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
