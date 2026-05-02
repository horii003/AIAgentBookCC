# スケルトン: 専門エージェント (agents/specialist_{name}_agent.py)

## 概要

オーケストレーターからAgent as Toolsパターンで呼び出される専門エージェント。
ドメイン固有の処理（情報収集、検証、計算、出力生成等）を担当する。
各専門エージェントごとにファイルを作成する。

## ファイル配置

`agents/specialist_a_agent.py`（専門エージェントAの場合）
`agents/specialist_b_agent.py`（専門エージェントBの場合）

## スケルトンコード

```python
"""専門エージェントA

{専門エージェントAの担当するドメインの説明}を担当する専門エージェント。
オーケストレーターからAgent as Toolsパターンで呼び出される。
"""
from strands import Agent, tool, ToolContext
from strands import ModelRetryStrategy
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools.{domain}_tools import {tool_function_1}, {tool_function_2}
from tools.output_generator import {specialist_a_output_generator}
from session.session_manager import SessionManagerFactory
from handlers.human_approval_hook import HumanApprovalHook
from handlers.error_handler import LoopLimitError, ErrorHandler
from prompt.prompt_specialist_a import _get_specialist_a_system_prompt  # または SPECIALIST_A_SYSTEM_PROMPT
from handlers.loop_control_hook import LoopControlHook
from config.model_config import ModelConfig


# ============ エージェントの初期化 ============

def _get_specialist_a_agent(session_id: str) -> Agent:
    """
    専門エージェントAのインスタンスを作成

    Args:
        session_id: セッションID（必須）

    Returns:
        Agent: 専門エージェントAのインスタンス
    """
    # TODO: 詳細設計書に従い実装
    # - セッションマネージャーの作成
    #   session_manager = SessionManagerFactory.create_session_manager(session_id)
    #
    # - HumanApprovalHookの作成（出力生成を伴う場合）
    #   approval_hook = HumanApprovalHook(
    #       approval_required_tools=["{specialist_a_output_generator}"]
    #   )
    #
    # - LoopControlHookの作成
    #   loop_hook = LoopControlHook(
    #       max_iterations=10,
    #       agent_name="{専門エージェントAの表示名}"
    #   )
    #
    # - Agentインスタンスの生成
    #   agent = Agent(
    #       model=ModelConfig.get_model(),
    #       system_prompt=_get_specialist_a_system_prompt(),  # 動的プロンプト
    #       # または system_prompt=SPECIALIST_A_SYSTEM_PROMPT,  # 静的プロンプト
    #       tools=[{tool_function_1}, {tool_function_2}, {specialist_a_output_generator}],
    #       conversation_manager=SlidingWindowConversationManager(
    #           window_size=20,
    #           should_truncate_results=True,
    #           per_turn=False
    #       ),
    #       callback_handler=None,
    #       retry_strategy=ModelRetryStrategy(max_attempts=6, initial_delay=4, max_delay=240),
    #       hooks=[approval_hook, loop_hook],
    #       session_manager=session_manager
    #   )
    #
    # - エージェントの返却
    pass


# ============ Agent as Tools ============

@tool(context=True)
def specialist_a_agent(query: str, tool_context: ToolContext) -> str:
    """
    専門エージェントAツール

    {専門エージェントAの処理の説明}を実行します。
    会話履歴を保持して、複数回の呼び出しでも段階的に情報を収集します。

    Args:
        query: ユーザーからの入力や質問

    Returns:
        str: エージェントからの応答
    """
    # TODO: 詳細設計書に従い実装
    # - invocation_stateの取得とエージェント生成（R9.6.5準拠）
    # - invocation_stateの伝播構築（R9.6.6準拠）
    # - エージェント呼び出しと応答返却
    # - エラーハンドリング（R9.1, R9.7準拠）
    pass
```


## 専門エージェント追加手順

新しい専門エージェントを追加する場合、以下のファイルを作成・更新する：

1. **`agents/specialist_{name}_agent.py`**: このテンプレートをコピーして新規作成
2. **`prompt/prompt_specialist_{name}.py`**: 新エージェントのシステムプロンプトを定義
3. **`agent_knowledge/{domain}_policies.py`**: 新ドメインのビジネスルールを定義（必要な場合）
4. **`tools/{domain}_tools.py`**: 新ドメインのツール関数を定義（必要な場合）
5. **`models/data_models.py`**: 新ドメインのデータモデルを追加（必要な場合）
6. **`agents/orchestrator_agent.py`**: `tools` リストに新エージェントのツール関数を追加
7. **`prompt/prompt_orchestrator.py`**: 振り分け基準テーブルに新エージェントを追加

## カスタマイズガイド

1. **ツールの選択**: 業務要件に応じてドメイン固有ツールと出力生成ツールを選択する
2. **ウィンドウサイズの調整**: 処理の複雑さに応じてウィンドウサイズを調整する（シンプル: 15、複雑: 20〜25）
3. **HumanApprovalHookの適用**: 出力生成や外部連携を伴う場合にHumanApprovalHookを設定する
4. **invocation_stateの伝播**: 子エージェントに必要な情報のみを選択して伝播する
5. **エージェント表示名**: `LoopControlHook` や `handle_*_error` に渡すエージェント名を業務に合わせて設定する
