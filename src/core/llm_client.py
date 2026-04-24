"""
SLG Sentinel — 通用 LLM 客户端

提供统一的 DeepSeek / OpenAI / Qwen 调用接口，支持文本和 JSON 响应模式。
从 keyword_expander.py 抽取出的通用基础设施层，被周报、情感分析、竞品对比等模块共用。
"""

from __future__ import annotations

import json
import logging
from typing import Any

import requests

from src.core.config import SentinelConfig
from src.core.exceptions import LLMError

logger = logging.getLogger(__name__)

# LLM Providers 配置（与 keyword_expander.py 保持一致）
PROVIDERS: dict[str, dict[str, str]] = {
    "deepseek": {
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o",
    },
    "qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "model": "qwen-max",
    },
}


class LLMClient:
    """通用 LLM 客户端，支持 DeepSeek / OpenAI / Qwen"""

    def __init__(self, config: SentinelConfig):
        self.config = config

    def _get_api_key(self, provider: str) -> str:
        """根据 provider 获取对应的 API Key"""
        key_map = {
            "deepseek": self.config.deepseek_api_key,
            "openai": self.config.openai_api_key,
            "qwen": self.config.qwen_api_key,
        }
        return key_map.get(provider, "")

    def chat(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        provider: str = "deepseek",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: int = 90,
    ) -> str:
        """
        单次对话，返回文本响应。

        Args:
            prompt: 用户消息
            system: 系统消息
            provider: LLM 提供商
            temperature: 采样温度
            max_tokens: 最大输出 token 数
            timeout: 请求超时秒数

        Returns:
            LLM 响应文本

        Raises:
            LLMError: API 调用失败或响应格式异常
        """
        api_key = self._get_api_key(provider)
        if not api_key:
            raise LLMError(f"未配置 {provider.upper()} 的 API Key，请在 secrets.yaml 或环境变量中设置")

        provider_cfg = PROVIDERS.get(provider)
        if not provider_cfg:
            raise LLMError(f"不支持的 LLM Provider: {provider}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        payload: dict[str, Any] = {
            "model": provider_cfg["model"],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            logger.info(f"调用 {provider} LLM (model={provider_cfg['model']})")
            resp = requests.post(
                provider_cfg["url"],
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            resp_json = resp.json()
            content = resp_json["choices"][0]["message"]["content"]
            return content.strip()
        except requests.exceptions.Timeout:
            raise LLMError(f"{provider} API 请求超时 ({timeout}s)")
        except requests.exceptions.RequestException as e:
            raise LLMError(f"{provider} API 请求失败: {e}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"{provider} API 响应格式异常: {e}")

    def chat_json(
        self,
        prompt: str,
        system: str = "You are a helpful assistant that outputs only valid JSON.",
        provider: str = "deepseek",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        timeout: int = 90,
    ) -> dict | list:
        """
        单次对话，返回 JSON 解析后的响应。

        自动处理 LLM 常见的格式问题（markdown 包裹、字典 vs 数组）。

        Args:
            prompt: 用户消息
            system: 系统消息
            provider: LLM 提供商
            temperature: 采样温度
            max_tokens: 最大输出 token 数
            timeout: 请求超时秒数

        Returns:
            解析后的 JSON 对象（dict 或 list）

        Raises:
            LLMError: API 调用失败或 JSON 解析失败
        """
        content = self.chat(
            prompt=prompt,
            system=system,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        # 清理 markdown 包裹
        cleaned = content
        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "")
        cleaned = cleaned.strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise LLMError(f"LLM 返回的内容无法解析为 JSON: {e}\n原文前 500 字符: {content[:500]}")

        return result

    def is_available(self, provider: str = "deepseek") -> bool:
        """检查指定 provider 是否已配置 API Key"""
        return bool(self._get_api_key(provider))

    def get_available_provider(self) -> str | None:
        """返回第一个可用的 provider，如果全部未配置则返回 None"""
        for provider in ("deepseek", "openai", "qwen"):
            if self.is_available(provider):
                return provider
        return None
