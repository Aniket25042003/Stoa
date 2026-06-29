"""Tests for langchain chat model factory."""

from unittest.mock import MagicMock, patch

from stoa_core.llm.langchain_chat import build_chat_model


@patch("stoa_core.llm.langchain_chat._build_google_genai")
def test_build_chat_model_prefers_genai(mock_genai):
    mock_genai.return_value = MagicMock()
    model = build_chat_model("premium")
    assert model is not None
    mock_genai.assert_called_once()
