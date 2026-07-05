"""交通費精算申請エージェント

交通費精算申請フロー（情報収集・交通費計算・HitL承認・申請書生成・申請書チェック）を
自己完結で実行する専門エージェント。
オーケストレーターから Agent as Tools パターンで呼び出される。
"""
from strands import Agent
from strands.types.tools import ToolContext
from strands import tool

from agents.base_agent import create_specialist_agent, invoke_specialist_agent
from config.settings import settings
from knowledge.transport_policies import get_transport_rules
from prompt.prompt_transport import get_transport_system_prompt
from tools.output_generator import generate_transport_expense_form
from tools.transport_tools import calculate_transport_fare


def _build_transport_application_agent(
    session_id: str,
    applicant_name: str,
    application_date: str,
    deadline: str,
) -> Agent:
    """交通費精算申請エージェントのインスタンスを作成するビルド関数。

    Args:
        session_id: セッションID
        applicant_name: 申請者名
        application_date: 申請日（YYYY-MM-DD形式）
        deadline: 申請期限（YYYY-MM-DD形式）

    Returns:
        Agent: 交通費精算申請エージェントのインスタンス
    """
    cfg = settings.transport
    system_prompt = get_transport_system_prompt(
        applicant_name=applicant_name,
        application_date=application_date,
        deadline=deadline,
        transport_rules=get_transport_rules(
            deadline_months=cfg.deadline_months,
            approval_threshold=cfg.approval_threshold,
        ),
    )
    return create_specialist_agent(
        session_id=session_id,
        system_prompt=system_prompt,
        tools=[calculate_transport_fare, generate_transport_expense_form],
        agent_name="交通費精算申請エージェント",
        window_size=cfg.window_size,
        max_iterations=cfg.max_iterations,
        max_attempts=cfg.max_attempts,
        initial_delay=cfg.initial_delay,
        max_delay=cfg.max_delay,
    )


@tool(context=True)
def transport_application_agent(query: str, tool_context: ToolContext) -> str:
    """交通費精算申請エージェント（AG-002）への委譲ツール。

    交通費精算申請フロー全体（情報収集・交通費計算・HitL承認・申請書生成・申請書チェック）を
    自己完結で実行して結果を返す。

    Args:
        query: ユーザーからの入力や質問

    Note:
        tool_context は Strands SDK が @tool(context=True) により自動注入する。
        LLM へのツールスキーマには含まれず、LLM が値を指定することもない。

        呼び出しのたびに Agent インスタンスを新規生成するが、FileSessionManager により
        会話履歴はファイルに永続化される。同一 session_id を渡すことで、
        次回呼び出し時にファイルから前回の会話履歴が復元され、段階的な情報収集が継続される。

    Returns:
        str: エージェントからの応答
    """
    return invoke_specialist_agent(
        query=query,
        tool_context=tool_context,
        agent_id="AG-002",
        deadline_months=settings.transport.deadline_months,
        build_agent=_build_transport_application_agent,
    )
