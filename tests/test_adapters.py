"""Tests for adapter search result parsing and sentiment LLM analyzer"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.core.models import Comment
from src.analysis.sentiment import SentimentAnalyzer, LLMSentimentAnalyzer


class TestBilibiliSearchParsing:
    """Test Bilibili adapter's search total extraction logic"""

    def test_extract_search_total_from_numResults(self):
        from src.adapters.bilibili import BilibiliAdapter
        result = BilibiliAdapter._extract_search_total({"numResults": 500})
        assert result == 500

    def test_extract_search_total_from_pageinfo(self):
        from src.adapters.bilibili import BilibiliAdapter
        result = BilibiliAdapter._extract_search_total({
            "pageinfo": {"video": {"numResults": 1000}}
        })
        assert result == 1000

    def test_extract_search_total_returns_none_on_empty(self):
        from src.adapters.bilibili import BilibiliAdapter
        result = BilibiliAdapter._extract_search_total({})
        assert result is None

    def test_safe_int(self):
        from src.adapters.bilibili import BilibiliAdapter
        assert BilibiliAdapter._safe_int(42) == 42
        assert BilibiliAdapter._safe_int(None) == 0
        assert BilibiliAdapter._safe_int("") == 0
        assert BilibiliAdapter._safe_int("abc") == 0


class TestLLMSentimentAnalyzer:
    """Test LLM sentiment analyzer with mock LLM client"""

    def test_fallback_when_no_client(self):
        """Without LLM client, should use dictionary-based fallback"""
        analyzer = LLMSentimentAnalyzer(llm_client=None)
        comments = [
            Comment(platform="test", video_id="v1", comment_id="c1",
                    author="u1", author_id="u1", content="这游戏好玩",
                    like_count=10, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
        ]
        analyzer.batch_analyze(comments)
        assert comments[0].sentiment == "positive"

    def test_fallback_when_no_provider(self):
        """LLM client exists but no API key configured"""
        mock_llm = MagicMock()
        mock_llm.get_available_provider.return_value = None
        analyzer = LLMSentimentAnalyzer(llm_client=mock_llm)
        comments = [
            Comment(platform="test", video_id="v1", comment_id="c1",
                    author="u1", author_id="u1", content="垃圾游戏",
                    like_count=5, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
        ]
        analyzer.batch_analyze(comments)
        assert comments[0].sentiment == "negative"

    def test_llm_batch_success(self):
        """LLM returns valid analysis results"""
        mock_llm = MagicMock()
        mock_llm.get_available_provider.return_value = "deepseek"
        mock_llm.chat_json.return_value = [
            {"id": 0, "sentiment": "negative", "games": "率土之滨", "topic": "太肝了"},
        ]
        analyzer = LLMSentimentAnalyzer(llm_client=mock_llm)
        comments = [
            Comment(platform="test", video_id="v1", comment_id="c1",
                    author="u1", author_id="u1", content="率土太累了不想玩了",
                    like_count=100, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
        ]
        analyzer.batch_analyze(comments)
        assert comments[0].sentiment == "negative"
        assert comments[0].mentioned_games == "率土之滨"

    def test_llm_failure_degrades_to_dict(self):
        """On LLM failure, should gracefully degrade to dictionary analysis"""
        mock_llm = MagicMock()
        mock_llm.get_available_provider.return_value = "deepseek"
        mock_llm.chat_json.side_effect = Exception("API timeout")
        analyzer = LLMSentimentAnalyzer(llm_client=mock_llm)
        comments = [
            Comment(platform="test", video_id="v1", comment_id="c1",
                    author="u1", author_id="u1", content="推荐这个游戏",
                    like_count=5, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
        ]
        # Should not raise, should degrade
        analyzer.batch_analyze(comments)
        assert comments[0].sentiment == "positive"


class TestSentimentAnalyzerDictionary:
    """Regression tests for existing dictionary-based analyzer"""

    def test_positive_detection(self):
        analyzer = SentimentAnalyzer()
        sentiment, _ = analyzer.analyze_comment("这游戏真好玩")
        assert sentiment == "positive"

    def test_negative_detection(self):
        analyzer = SentimentAnalyzer()
        sentiment, _ = analyzer.analyze_comment("垃圾游戏骗氪")
        assert sentiment == "negative"

    def test_game_mention(self):
        analyzer = SentimentAnalyzer()
        _, mentions = analyzer.analyze_comment("我觉得三战比率土好")
        assert "三国志战略版" in mentions
        assert "率土之滨" in mentions
