"""
SLG Sentinel — 情感分析与竞品提取模块

第一层：基于规则与简易词典的离线情感分析（避免依赖LLM的高昂API费用，用于大批量评论）。
第二层：实体提及（NER），提取评论中提到的其他 SLG 游戏名称。
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from src.core.models import Comment

logger = logging.getLogger(__name__)

# 简易情感极性词典
POSITIVE_WORDS = {
    "好玩", "推荐", "不错", "良心", "优秀", "喜欢", "神作", "爱了", 
    "支持", "可以", "好评", "亮点", "舒服", "出彩", "棒", "强"
}

NEGATIVE_WORDS = {
    "垃圾", "骗氪", "逼氪", "又肝又氪", "无语", "恶心", "退坑", "卸载", 
    "答辩", "策划死", "不推荐", "黑心", "失望", "差评", "太累", "坐牢"
}

# 否定词前缀（用于反转情感极性）
NEGATION_WORDS = {"不", "没", "无", "未", "别", "非", "不是", "没有", "并非"}

# 竞品实体监控词典（将俗称映射为全称）
GAMES_DICTIONARY = {
    "率土之滨": ["率土之滨", "率土"],
    "三国志战略版": ["三国志战略版", "三战"],
    "万国觉醒": ["万国觉醒", "万国", "rox", "rok"],
    "文明与征服": ["文明与征服", "文征"],
    "鸿图之下": ["鸿图之下", "鸿图"],
    "寰宇之战": ["寰宇之战"],
    "重返帝国": ["重返帝国"],
    "无尽的拉格朗日": ["无尽的拉格朗日", "拉格朗日"],
}


class SentimentAnalyzer:
    """情感分析与提及竞品提取器"""

    def __init__(self):
        # 预先构建扁平化的实体映射表，加速匹配
        self._entity_map = {}
        for game_name, aliases in GAMES_DICTIONARY.items():
            for alias in aliases:
                self._entity_map[alias.lower()] = game_name

    def analyze_comment(self, text: str) -> Tuple[str, str]:
        """
        分析单条评论文本。
        
        Args:
            text: 评论文本
            
        Returns:
            (sentiment, mentioned_games_csv) 元组
            sentiment 值为 "positive", "negative", "neutral"
            mentioned_games 值为匹配到的游戏名（逗号分隔）
        """
        if not text:
            return "neutral", ""

        text_lower = text.lower()

        # 1. 情感极性判断（支持否定词前缀反转）
        pos_count = 0
        neg_count = 0
        for word in POSITIVE_WORDS:
            if word in text_lower:
                # 检查否定前缀：如 "不好玩", "没有亮点"
                idx = text_lower.find(word)
                prefix = text_lower[max(0, idx-2):idx]
                if any(neg in prefix for neg in NEGATION_WORDS):
                    neg_count += 1  # 否定+正面 → 计为负面
                else:
                    pos_count += 1
        for word in NEGATIVE_WORDS:
            if word in text_lower:
                idx = text_lower.find(word)
                prefix = text_lower[max(0, idx-2):idx]
                if any(neg in prefix for neg in NEGATION_WORDS):
                    pos_count += 1  # 否定+负面 → 计为正面
                else:
                    neg_count += 1

        if pos_count > neg_count:
            sentiment = "positive"
        elif neg_count > pos_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # 2. 竞品提及提取
        mentions = set()
        for alias, game_name in self._entity_map.items():
            if alias in text_lower:
                mentions.add(game_name)

        mentioned_str = ",".join(sorted(list(mentions)))

        return sentiment, mentioned_str

    def batch_analyze(self, comments: List[Comment]) -> None:
        """
        批量分析评论，并直接修改传入的 Comment 对象的属性。
        
        Args:
            comments: Comment 对象列表
        """
        analyzed_count = 0
        for c in comments:
            if not c.content:
                continue
            sentiment, mentions = self.analyze_comment(c.content)
            c.sentiment = sentiment
            c.mentioned_games = mentions
            analyzed_count += 1
            
        logger.info(f"已完成 {analyzed_count} 条评论的情感分析和实体提取")


class LLMSentimentAnalyzer:
    """
    LLM 驱动的情感分析器。

    将评论批量发送给 LLM，返回更精准的情感极性、话题标签和核心洞察。
    当 LLM 不可用时自动降级为字典匹配的 SentimentAnalyzer。
    """

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLMClient 实例。传入 None 时自动降级为字典分析。
        """
        self._llm = llm_client
        self._fallback = SentimentAnalyzer()

    def batch_analyze(self, comments: List[Comment], batch_size: int = 20) -> None:
        """
        批量分析评论。优先使用 LLM，失败时降级为词典分析。

        Args:
            comments: Comment 对象列表
            batch_size: 每批发送给 LLM 的评论数（控制 token 消耗）
        """
        if not self._llm or not comments:
            self._fallback.batch_analyze(comments)
            return

        provider = self._llm.get_available_provider()
        if not provider:
            logger.info("未检测到可用的 LLM API Key，降级为字典分析模式")
            self._fallback.batch_analyze(comments)
            return

        # 按批次发送
        valid_comments = [c for c in comments if c.content]
        analyzed = 0
        for i in range(0, len(valid_comments), batch_size):
            batch = valid_comments[i : i + batch_size]
            try:
                self._analyze_batch_llm(batch, provider)
                analyzed += len(batch)
            except Exception as e:
                logger.warning(f"LLM 分析第 {i // batch_size + 1} 批失败，降级为词典分析: {e}")
                self._fallback.batch_analyze(batch)
                analyzed += len(batch)

        # 处理无内容的评论
        for c in comments:
            if not c.content and not c.sentiment:
                c.sentiment = "neutral"

        logger.info(f"已完成 {analyzed} 条评论的 LLM 情感分析")

    def _analyze_batch_llm(self, batch: List[Comment], provider: str) -> None:
        """发送一批评论给 LLM 分析"""
        entries = []
        for idx, c in enumerate(batch):
            text = c.content[:200]  # 截断过长评论
            entries.append(f"[{idx}] {text}")

        joined = "\n".join(entries)
        prompt = f"""分析以下 {len(batch)} 条 SLG 手游玩家评论的情感和话题。

{joined}

请返回一个 JSON 数组，每个元素对应一条评论：
[{{"id": 0, "sentiment": "positive/negative/neutral", "games": "提及的竞品游戏名,逗号分隔", "topic": "一句话核心观点"}}]

注意：
- sentiment 只能是 positive、negative、neutral 之一
- games 字段仅填写评论中明确提到的 SLG 游戏名称（如 率土之滨、三战、万国觉醒等），没有则为空字符串
- topic 用中文一句话概括评论的核心观点"""

        result = self._llm.chat_json(prompt, provider=provider, temperature=0.2)
        if not isinstance(result, list):
            result = result.get("results", result.get("comments", []))

        for item in result:
            try:
                idx = int(item.get("id", -1))
                if 0 <= idx < len(batch):
                    batch[idx].sentiment = item.get("sentiment", "neutral")
                    batch[idx].mentioned_games = item.get("games", "")
            except (ValueError, TypeError):
                continue
