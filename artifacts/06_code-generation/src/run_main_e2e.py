"""
main.py の対話ループを input() モック経由でドライブするE2E確認スクリプト。
run_e2e.py と異なり、main.py の _get_applicant_name() / 対話ループを通して実際に実行する。
"""
import sys
import os
import glob

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

from handlers.human_approval_hook import patch_human_approval_hook
patch_human_approval_hook()

import warnings
import logging
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)


def run_scenario(name: str, inputs: list[str]) -> tuple[bool, str]:
    """inputs を順番に input() へ渡して main() の対話ループを実行する。"""
    print(f"\n{'='*60}")
    print(f"【シナリオ】{name}")
    print(f"{'='*60}")

    before_files = set(glob.glob("data/output/**/*.xlsx", recursive=True))

    # --- input() をキューで差し替え ---
    queue = list(inputs)
    call_log: list[str] = []

    def fake_input(prompt=""):
        if queue:
            val = queue.pop(0)
        else:
            val = "quit"
        print(f"{prompt}{val}")
        call_log.append(val)
        return val

    # main モジュールの input を差し替えて実行
    import main as main_mod
    original_input = main_mod.__builtins__["input"] if isinstance(main_mod.__builtins__, dict) else getattr(main_mod.__builtins__, "input", None)

    import builtins
    original_builtin_input = builtins.input
    builtins.input = fake_input

    try:
        main_mod.main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"[例外] {e}")
    finally:
        builtins.input = original_builtin_input

    new_files = sorted(set(glob.glob("data/output/**/*.xlsx", recursive=True)) - before_files)
    if new_files:
        path = new_files[0]
        size = os.path.getsize(path)
        print(f"\n✅ 申請書生成確認: {path} ({size:,} bytes)")
        return True, path
    else:
        return False, "申請書ファイルが生成されませんでした"


def main():
    results = []
    os.makedirs("data/output", exist_ok=True)

    # ---- シナリオ1: 交通費精算申請 ----
    inputs_transport = [
        "田中太郎",                                          # 申請者名
        "渋谷から新宿まで電車で移動しました。交通費精算をお願いします。",
        "移動日は2026年4月25日、業務目的は営業先への訪問です。",
        "はい、その内容で申請書を作成してください。",
        "はい、お願いします。",
        "はい、確認しました。",
        "quit",
    ]
    success1, result1 = run_scenario("交通費精算申請（渋谷→新宿 電車）", inputs_transport)
    results.append(("交通費精算申請", success1, result1))

    # ---- シナリオ2: 経費精算申請 ----
    inputs_expense = [
        "田中太郎",
        "コンビニで業務用のボールペンを購入しました。200円でした。経費精算をお願いします。",
        "手動入力でお願いします。",
        "購入日は2026年4月28日、店舗名はセブンイレブン渋谷店、金額は200円、品目はボールペン、業務目的は営業資料作成用です。",
        "経費区分は事務用品費でお願いします。",
        "はい、その内容で問題ありません。申請書を作成してください。",
        "はい、お願いします。",
        "quit",
    ]
    success2, result2 = run_scenario("経費精算申請（文房具 200円）", inputs_expense)
    results.append(("経費精算申請", success2, result2))

    # ---- 結果サマリ ----
    print(f"\n{'='*60}")
    print("【main.py E2E動作確認 結果サマリ】")
    print(f"{'='*60}")
    all_passed = True
    for name, success, result in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {name}")
        if success:
            print(f"      生成ファイル: {result}")
            if os.path.exists(result):
                print(f"      ファイルサイズ: {os.path.getsize(result):,} bytes")
        else:
            print(f"      結果: {result}")
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("全シナリオ PASS — main.py 経由での申請書ファイル生成を確認しました。")
    else:
        print("一部シナリオで申請書ファイルが生成されませんでした。")
    print(f"{'='*60}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
