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

        # 1. 简易情感极性判断（词频相减法）
        pos_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
        neg_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)

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
