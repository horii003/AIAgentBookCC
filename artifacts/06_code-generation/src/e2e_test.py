"""
エンドツーエンドテスト: 申請書ファイル生成までの動作確認

テストシナリオ:
  シナリオ1: 交通費精算申請 (AG-001 → AG-002 → TOOL-001 → TOOL-002)
  シナリオ2: 経費精算申請   (AG-001 → AG-003 → TOOL-002)
"""
import os
import subprocess
import sys
import glob
import time

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
OUTPUT_DIR = os.path.join(SRC_DIR, "data", "output")


def run_scenario(name: str, inputs: list[str], timeout: int = 180) -> dict:
    """サブプロセスでmain.pyを起動し、stdinに入力を流して結果を取得する。"""
    print(f"\n{'='*60}")
    print(f"[{name}] 開始")
    print(f"{'='*60}")

    stdin_text = "\n".join(inputs) + "\n"

    before_files = set(glob.glob(os.path.join(OUTPUT_DIR, "**", "*.xlsx"), recursive=True))

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        [PYTHON, "-u", "main.py"],
        cwd=SRC_DIR,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    try:
        stdout_bytes, stderr_bytes = proc.communicate(
            input=stdin_text.encode("utf-8"), timeout=timeout
        )
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout_bytes, stderr_bytes = proc.communicate()
        return {
            "name": name,
            "success": False,
            "error": f"タイムアウト ({timeout}秒)",
            "stdout": stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else "",
            "stderr": stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else "",
            "new_files": [],
        }

    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

    after_files = set(glob.glob(os.path.join(OUTPUT_DIR, "**", "*.xlsx"), recursive=True))
    new_files = sorted(after_files - before_files)

    print(f"[stdout]\n{stdout}")
    if stderr.strip():
        print(f"[stderr (抜粋)]\n{stderr[-3000:]}")

    success = len(new_files) > 0
    return {
        "name": name,
        "success": success,
        "new_files": new_files,
        "stdout": stdout,
        "stderr": stderr,
        "returncode": proc.returncode,
    }


def main():
    print("=" * 60)
    print("エンドツーエンドテスト開始")
    print("=" * 60)

    # シナリオ1: 交通費精算申請
    # 入力シーケンス:
    #   1. 申請者名
    #   2. 申請内容（移動区間・業務目的を明示）
    #   3. 「完了です。申請書を作成してください。」→ AG-002がドラフト提示
    #   4. 「OK」→ AG-002がgenerate_travel_expense_form呼び出し → HumanApprovalHookが発動
    #   5. 「ok」→ HumanApprovalHookへの承認入力（stdin直読み）
    #   6. quit
    scenario1_inputs = [
        "田中太郎",
        "2026年4月28日に東京から新宿まで電車で移動しました。業務目的は社内会議です。移動区間はこれだけです。交通費精算申請書を作成してください。",
        "完了です。申請書を作成してください。",
        "OK",
        "ok",
        "quit",
    ]

    result1 = run_scenario("シナリオ1: 交通費精算申請", scenario1_inputs, timeout=240)

    # シナリオ2: 経費精算申請
    # 入力シーケンス:
    #   1. 申請者名
    #   2. 申請内容（領収書なしを明示）
    #   3. 「画像なし、手動入力でお願いします。」→ AG-003が受け付け
    #   4. 「OK」→ AG-003がgenerate_expense_form呼び出し → HumanApprovalHookが発動
    #   5. 「ok」→ HumanApprovalHookへの承認入力（stdin直読み）
    #   6. quit
    scenario2_inputs = [
        "鈴木花子",
        "2026年4月28日に書店で技術書を3000円で購入しました。業務目的は業務研究です。領収書はございません。手動入力で経費精算申請書を作成してください。",
        "画像なし、手動入力でお願いします。",
        "OK",
        "ok",
        "quit",
    ]

    result2 = run_scenario("シナリオ2: 経費精算申請", scenario2_inputs, timeout=240)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)

    results = [result1, result2]
    all_passed = True

    for r in results:
        status = "✅ PASS" if r["success"] else "❌ FAIL"
        print(f"\n{status}  {r['name']}")
        if r["success"]:
            for f in r["new_files"]:
                print(f"  生成ファイル: {f}")
        else:
            print(f"  エラー: {r.get('error', '申請書ファイルが生成されませんでした')}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("全シナリオ PASSED ✅")
    else:
        print("一部シナリオ FAILED ❌")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
