"""Tests for src/core/llm_client.py and src/core/exceptions.py"""

from __future__ import annotations

import json
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from src.core.exceptions import LLMError, SentinelError
from src.core.llm_client import LLMClient, PROVIDERS


@dataclass
class _FakeConfig:
    deepseek_api_key: str = ""
    openai_api_key: str = ""
    qwen_api_key: str = ""


class TestExceptions:
    def test_llm_error_inherits_sentinel(self):
        assert issubclass(LLMError, SentinelError)

    def test_sentinel_error_inherits_exception(self):
        assert issubclass(SentinelError, Exception)


class TestLLMClient:
    def test_no_api_key_raises(self):
        client = LLMClient(_FakeConfig())
        with pytest.raises(LLMError, match="未配置"):
            client.chat("hello", provider="deepseek")

    def test_unsupported_provider_raises(self):
        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        with pytest.raises(LLMError, match="未配置"):
            client.chat("hello", provider="unknown_provider")

    def test_get_available_provider_returns_first(self):
        client = LLMClient(_FakeConfig(openai_api_key="sk-test"))
        assert client.get_available_provider() == "openai"

    def test_get_available_provider_none(self):
        client = LLMClient(_FakeConfig())
        assert client.get_available_provider() is None

    def test_is_available(self):
        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        assert client.is_available("deepseek") is True
        assert client.is_available("openai") is False

    @patch("src.core.llm_client.requests.post")
    def test_chat_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        result = client.chat("test prompt")
        assert result == "Hello world"
        mock_post.assert_called_once()

    @patch("src.core.llm_client.requests.post")
    def test_chat_json_success(self, mock_post):
        payload = [{"topic": "test", "count": 5}]
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": json.dumps(payload)}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        result = client.chat_json("test prompt")
        assert result == payload

    @patch("src.core.llm_client.requests.post")
    def test_chat_json_strips_markdown(self, mock_post):
        raw = '```json\n[{"a": 1}]\n```'
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": raw}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        result = client.chat_json("test")
        assert result == [{"a": 1}]

    @patch("src.core.llm_client.requests.post")
    def test_chat_json_invalid_json_raises(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "not json at all"}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        client = LLMClient(_FakeConfig(deepseek_api_key="sk-test"))
        with pytest.raises(LLMError, match="无法解析为 JSON"):
            client.chat_json("test")

    def test_providers_have_required_keys(self):
        for name, cfg in PROVIDERS.items():
            assert "url" in cfg, f"{name} missing url"
            assert "model" in cfg, f"{name} missing model"
