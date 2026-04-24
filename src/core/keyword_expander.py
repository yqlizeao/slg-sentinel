"""
SLG Sentinel — AI 关键词扩展模块

使用 LLM 根据种子关键词自动扩展搜索词。
基于 LLMClient 统一基础设施层，消除内联 HTTP 调用。
"""
from __future__ import annotations
import logging, time
from typing import List, Callable
from src.core.config import SentinelConfig
from src.core.llm_client import LLMClient
from src.core.exceptions import LLMError

logger = logging.getLogger(__name__)


class KeywordExpander:
    """关键词扩展器"""

    def __init__(self, config: SentinelConfig):
        self.config = config
        self._llm = LLMClient(config)

    def expand(self, provider: str = "deepseek", max_keywords: int = 50,
               progress_callback: Callable[[int, int, str], None] = None) -> List[str]:
        """
        基于 RAG 的数据驱动关键词逆向提取

        Args:
            provider: 模型提供商 (deepseek/openai/qwen)
            max_keywords: 最大输出数量
            progress_callback: 供 UI 使用的回调函数

        Returns:
            扩展后的关键词列表
        """
        if not self.config.keywords.expansion.enabled:
            logger.info("关键词扩展未启用（keywords.yaml expansion.enabled=false）")
            return []

        if not self._llm.is_available(provider):
            logger.error(f"未找到 {provider.upper()} 的 API Key 配置，无法执行关键词扩展")
            return []

        taptap_targets = self.config.targets.taptap_games
        if not taptap_targets:
            logger.warning("目标配置中没有 TapTap 游戏，无法进行语义逆向提取")
            return []

        from src.adapters.taptap import TapTapAdapter

        # 限制只抽取前 15 个，防止超出上下文且耗时过久
        target_pool = taptap_targets[:15]
        total_games = len(target_pool)

        api = TapTapAdapter()
        corpus_blocks = []

        logger.info(f"开始拉取 {total_games} 款 SLG 侧游戏进行语料拼接...")
        for idx, game in enumerate(target_pool, 1):
            if progress_callback:
                progress_callback(idx, total_games, game.name)

            info = api.get_game_info(game.app_id)
            if info:
                desc = str(info.get("description", "")).replace("\n", " ")[:500]
                tags = [t.get("value", "") for t in info.get("tags", []) if isinstance(t, dict)]
                corpus_blocks.append(f"【{game.name}】\n官方标签：{','.join(tags)}\n简介摘要：{desc}")

            # API 礼貌间隔
            if idx < total_games:
                time.sleep(1.0)

        compiled_corpus = "\n\n".join(corpus_blocks)

        if not compiled_corpus:
            logger.error("未能成功抓取任何语料，取消提取")
            return []

        prompt = f"""
你现在是一台纯粹的 NLP 自然语言标签提词器，专精于国内 SLG/策略类 手游领域。
请详细通读我提供的这批各大顶级 SLG 游戏的【官方真实语料与标签库】。

{compiled_corpus}

指令任务：
请从以上我提供的文字材料中，**逆向提取和提纯**出最具营销价值、最能代表 SLG 核心买量与圈层文化的 50 个搜索长尾词/黑话。
包括但不限于：
1. 游戏机制的垂直术语（如：沙盘、开荒、打城、走格子、抽卡、赛季制等）
2. 这些游戏的官方推广用语与民间约定俗成的衍生词组合。

要求：
- 请严格基于我提供的语料库内容进行提取，不允许毫无根据的幻觉编造。
- 返回总数不要超过 {max_keywords} 个词汇。
- **必须且只能**返回一个合法的纯 JSON String 数组。绝不要输出任何其他前言后语或 Markdown 标记。
"""

        try:
            logger.info(f"正在使用 {provider} 请求关键词扩展...")
            result = self._llm.chat_json(
                prompt=prompt,
                system="You are a helpful assistant that outputs only raw JSON arrays.",
                provider=provider,
                temperature=0.7,
                timeout=60,
            )

            # 如果大模型返回了字典格式如 {"keywords": ["a", "b"]}
            if isinstance(result, dict):
                for k, v in result.items():
                    if isinstance(v, list):
                        result = v
                        break

            if isinstance(result, list):
                expanded = [str(k) for k in result[:max_keywords]]
                logger.info(f"成功扩展出 {len(expanded)} 个关键词")
                return expanded
            else:
                logger.error("LLM 返回的格式非列表")
                return []

        except LLMError as e:
            logger.error(f"关键词扩展 LLM 调用失败: {e}")
            return []
        except Exception as e:
            logger.error(f"关键词扩展过程出错: {e}")
            return []
