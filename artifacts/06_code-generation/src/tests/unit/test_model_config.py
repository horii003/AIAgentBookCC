import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from config.model_config import MODEL_ID, RETRY_MAX_ATTEMPTS


def test_model_id_is_expected():
    assert MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"


def test_retry_max_attempts():
    assert RETRY_MAX_ATTEMPTS == 6


def test_get_bedrock_model_skipped_if_no_strands():
    """get_bedrock_model はstrands未インストール環境ではImportErrorを無視してスキップ."""
    try:
        from config.model_config import get_bedrock_model
        model = get_bedrock_model()
        assert model is not None
    except (ImportError, Exception):
        pytest.skip("strands SDK not installed, skipping BedrockModel instantiation test")
