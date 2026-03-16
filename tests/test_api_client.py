"""Tests for CExams API client"""

import pytest
import json
from unittest.mock import patch, MagicMock
from cexams.api.client import OpenRouterClient


class TestOpenRouterClient:
    """Tests for OpenRouterClient"""

    def test_client_initialization(self):
        client = OpenRouterClient(api_key="test-key", model="test-model")
        assert client.api_key == "test-key"
        assert client.model == "test-model"
        assert client.base_url == "https://openrouter.ai/api/v1/chat/completions"

    def test_client_default_model(self):
        client = OpenRouterClient(api_key="test-key")
        assert client.model == "deepseek/deepseek-chat"

    def test_client_headers(self):
        client = OpenRouterClient(api_key="test-key")
        assert "Authorization" in client.headers
        assert client.headers["Authorization"] == "Bearer test-key"
        assert client.headers["X-Title"] == "CExams AI Reviewer"

    @patch("cexams.api.client.requests.Session")
    def test_session_creation(self, mock_session):
        client = OpenRouterClient(api_key="test-key")
        assert client.session is not None


class TestParseAIResponse:
    """Tests for parsing AI responses"""

    def test_parse_clean_json(self):
        response = '{"key": "value", "number": 42}'
        result = OpenRouterClient.parse_ai_response(response)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_with_markdown(self):
        response = '```json\n{"key": "value"}\n```'
        result = OpenRouterClient.parse_ai_response(response)
        assert result == {"key": "value"}

    def test_parse_json_with_backticks(self):
        response = '```{"key": "value"}```'
        result = OpenRouterClient.parse_ai_response(response)
        assert result == {"key": "value"}

    def test_parse_invalid_json_raises(self):
        response = "not valid json"
        with pytest.raises(json.JSONDecodeError):
            OpenRouterClient.parse_ai_response(response)
