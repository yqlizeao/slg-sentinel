"""
SLG Sentinel — AI 关键词扩展模块

使用 LLM (如 DeepSeek) 根据种子关键词自动扩展搜索词。
使用 requests 实现兼容 OpenAI API 格式的调用，减少对 openai 库的重度依赖。
"""

from __future__ import annotations

import json
import logging
from typing import List

import requests

from src.core.config import SentinelConfig

logger = logging.getLogger(__name__)

# LLM Providers 配置
PROVIDERS = {
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


class KeywordExpander:
    """关键词扩展器"""

    def __init__(self, config: SentinelConfig):
        self.config = config
        self.api_key = config.deepseek_api_key

    def expand(self, provider: str = "deepseek", max_keywords: int = 50) -> List[str]:
        """
        扩展关键词
        
        Args:
            provider: 模型提供商 (deepseek/openai/qwen)
            max_keywords: 最大输出数量
            
        Returns:
            扩展后的关键词列表
        """
        if not self.config.keywords.expansion.enabled:
            logger.info("关键词扩展未启用（keywords.yaml expansion.enabled=false）")
            return []

        if not self.api_key:
            logger.error("未找到 DEEPSEEK_API_KEY 环境变量，无法执行关键词扩展")
            return []

        provider_cfg = PROVIDERS.get(provider)
        if not provider_cfg:
            logger.error(f"不支持的 LLM Provider: {provider}")
            return []

        # 准备种子核心信息
        games = self.config.keywords.games
        categories = self.config.keywords.categories
        
        if not games and not categories:
            logger.warning("没有配置种子关键词，无法扩展")
            return []

        prompt = f"""
你是一名资深的游戏营销与舆情分析专家，专精于 SLG（策略类）手游。
我需要你帮我扩展一套用于监控社交媒体（如B站、YouTube等）视频和评论的搜素关键词。

已知我们关注的核心游戏名称为：{', '.join(games)}
已知我们关注的游戏品类为：{', '.join(categories)}

请基于以上种子，帮我联想和扩展出相关的搜索关键词。包括但不限于：
1. 这些游戏的常见简称、俗称、黑话（如：“三战”、“率土”等）
2. 游戏核心玩法的垂直词汇（如：“开荒”、“配将”、“打城”、“赛季”等）与上述游戏的组合组合词（如：“三战开荒”、“率土配将”）
3. 同类竞品游戏的名称
4. 目标受众可能会搜索或讨论的话题泛词

要求：
- 返回的核心搜索词总数不要超过 {max_keywords} 个。
- 结果**必须**只返回一个 JSON 格式的数组，包含作为字符串的扩展词列表。不要有任何额外的文本或 Markdown 标记。例如：["词1", "词2"]。
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        
        # 兼容 OpenAI API 格式的 payload
        payload = {
            "model": provider_cfg["model"],
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that outputs only raw JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"} if provider != 'deepseek' else None, # deepseek json mode 有时只需 prompt 引导
            "temperature": 0.7,
        }

        try:
            logger.info(f"正在使用 {provider} 请求关键词扩展...")
            resp = requests.post(provider_cfg["url"], headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            
            resp_json = resp.json()
            content = resp_json["choices"][0]["message"]["content"]
            
            # 清理可能的 markdown 标记
            content = content.replace("```json", "").replace("```", "").strip()
            
            expanded_keywords = json.loads(content)
            
            if isinstance(expanded_keywords, dict):
                 # 如果大模型返回了字典格式如 {"keywords": ["a", "b"]}
                 for k, v in expanded_keywords.items():
                     if isinstance(v, list):
                         expanded_keywords = v
                         break
            
            if isinstance(expanded_keywords, list):
                logger.info(f"成功扩展出 {len(expanded_keywords)} 个关键词")
                return [str(k) for k in expanded_keywords[:max_keywords]]
            else:
                logger.error("LLM 返回的格式非列表")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"解析大模型返回的 JSON 失败: {e}\n原文: {content}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"调用各大模型 API 失败: {e}")
            return []
        except Exception as e:
            logger.error(f"关键词扩展过程出错: {e}")
            return []
