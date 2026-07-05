"""エンドツーエンドテスト: 申請書ファイル生成まで動作確認

経費精算申請エージェント（AG-003）を直接起動し、
LLMとのリアルな会話フローを経て outputs/ に Excel ファイルが
生成されることを確認する。

実行方法:
    cd /home/coder/workspace/AIAgentBookCC2/artifacts/06_code-generation/src
    python e2e_test.py
"""
import os
import sys
import logging
import glob

# CWD を src に設定（template/ outputs/ の相対パスが正しく解決されるよう）
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SRC_DIR)
sys.path.insert(0, SRC_DIR)

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logging.getLogger("strands").setLevel(logging.WARNING)

from unittest.mock import MagicMock

from agents.base_agent import invoke_specialist_agent
from agents.expense_application_agent import _build_expense_application_agent


def collect_output_files():
    """outputs/ 配下の Excel ファイル一覧を返す"""
    pattern = os.path.join(SRC_DIR, "outputs", "*.xlsx")
    return sorted(glob.glob(pattern))


def call_agent(ctx, query, step_label):
    """エージェントを1ターン呼び出して応答を返す"""
    print(f"\n[{step_label} クエリ]\n{query}\n")
    print("-" * 60)
    print("エージェント実行中（LLM呼び出しあり）...")
    print("-" * 60)

    result = invoke_specialist_agent(
        query=query,
        tool_context=ctx,
        agent_id="AG-003",
        deadline_months=3,
        build_agent=_build_expense_application_agent,
    )

    print(f"\n[{step_label} 応答]")
    print(result)
    return result


def main():
    print("=" * 60)
    print("E2Eテスト開始: 経費精算申請エージェント → 申請書生成")
    print("=" * 60)

    # 実行前の出力ファイル一覧を記録
    before = set(collect_output_files())
    print(f"\n[Before] outputs/ の Excel ファイル数: {len(before)}")

    # セッションIDを固定してFileSessionManagerで会話を継続
    session_id = "e2e_20260704_120000_test0001"

    def make_ctx():
        ctx = MagicMock()
        ctx.invocation_state = {
            "applicant_name": "山田太郎",
            "application_date": "2026-07-04",
            "session_id": session_id,
        }
        return ctx

    # ---- Step 1: 申請情報を全件提示 ----
    query1 = (
        "経費精算申請をお願いします。\n"
        "購入日: 2026-07-01\n"
        "店舗名: 株式会社ABC文具店\n"
        "品目: ボールペン10本セット\n"
        "経費区分: 事務用品費\n"
        "金額: 1500円\n"
        "業務目的: 部署内の消耗品補充\n\n"
        "上記の内容で申請書ドラフトを作成し、最終確認を求めてください。"
    )
    call_agent(make_ctx(), query1, "Step1")

    # ---- Step 2: HitL確認「OK」で申請書生成 ----
    after_step1 = set(collect_output_files())
    if after_step1 - before:
        # Step1 でもう生成完了している場合（エージェントが自動で進めた）
        new_files = after_step1 - before
    else:
        query2 = "OK"
        call_agent(make_ctx(), query2, "Step2")
        after_step2 = set(collect_output_files())
        new_files = after_step2 - before

    print("\n" + "=" * 60)
    print("検証結果")
    print("=" * 60)
    print(f"新規生成ファイル数: {len(new_files)}")

    if new_files:
        for fpath in sorted(new_files):
            size = os.path.getsize(fpath)
            print(f"  ✓ {os.path.basename(fpath)}  ({size:,} bytes)")
        print("\n✅ テスト成功: 申請書ファイルが生成されました。")
        return 0
    else:
        print("\n❌ テスト失敗: 申請書ファイルが生成されませんでした。")
        print("  ヒント: ログ (logs/app.log) を確認してください。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
