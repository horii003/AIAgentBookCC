import os

MODEL_ID = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
RETRY_MAX_ATTEMPTS = 6
RETRY_INITIAL_DELAY = 4
RETRY_MAX_DELAY = 240


def get_bedrock_model():
    """Return a configured BedrockModel instance."""
    try:
        from strands.models import BedrockModel
        from strands.models.bedrock import ModelRetryStrategy
    except ImportError:
        from strands_tools.models import BedrockModel
        from strands_tools.models.bedrock import ModelRetryStrategy

    region = os.environ.get("AWS_REGION", "ap-northeast-1")

    return BedrockModel(
        model_id=MODEL_ID,
        region_name=region,
        retry_config=ModelRetryStrategy(
            max_attempts=RETRY_MAX_ATTEMPTS,
            initial_delay=RETRY_INITIAL_DELAY,
            max_delay=RETRY_MAX_DELAY,
        ),
    )
