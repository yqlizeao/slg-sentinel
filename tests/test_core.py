"""
SLG Sentinel 基础单元测试

覆盖核心模块的基本功能验证：
- models.py: dataclass 序列化 / 去重 / identity
- csv_store.py: save / load 幂等性
- sentiment.py: 情感分析准确性（含否定词）
- config.py: YAML 加载边界条件
"""

import csv
import tempfile
from pathlib import Path

import pytest

from src.core.models import VideoSnapshot, Comment, TapTapReview, UserProfile
from src.core.csv_store import CSVStore
from src.analysis.sentiment import SentimentAnalyzer


# ═══════════════════════════════════════════════════════════════════════════════
# models.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestModels:
    """数据模型基本行为验证"""

    def _make_snapshot(self, video_id="BV_test_001"):
        return VideoSnapshot(
            platform="bilibili", video_id=video_id, title="测试视频",
            author="测试UP主", author_id="12345", snapshot_date="2026-04-17",
            view_count=1000, like_count=100, comment_count=10,
            share_count=5, favorite_count=50, coin_count=20,
            danmaku_count=30, publish_date="2026-04-16",
            tags="SLG,三国", url="https://www.bilibili.com/video/BV_test_001"
        )

    def test_video_snapshot_eq(self):
        a = self._make_snapshot("BV001")
        b = self._make_snapshot("BV001")
        assert a == b

    def test_video_snapshot_neq(self):
        a = self._make_snapshot("BV001")
        b = self._make_snapshot("BV002")
        assert a != b

    def test_video_snapshot_hash(self):
        a = self._make_snapshot("BV001")
        b = self._make_snapshot("BV001")
        assert hash(a) == hash(b)
        # 可以用于 set 去重
        s = {a, b}
        assert len(s) == 1

    def test_comment_identity(self):
        c1 = Comment(platform="bilibili", video_id="BV001", comment_id="c1",
                     author="user", author_id="u1", content="好玩",
                     like_count=10, reply_count=0, publish_time="2026-04-17",
                     ip_location="北京", sentiment="", mentioned_games="")
        c2 = Comment(platform="bilibili", video_id="BV001", comment_id="c1",
                     author="user_changed", author_id="u1", content="不好玩",
                     like_count=20, reply_count=1, publish_time="2026-04-18",
                     ip_location="上海", sentiment="", mentioned_games="")
        assert c1 == c2  # 相同 comment_id → 相等
        assert hash(c1) == hash(c2)


# ═══════════════════════════════════════════════════════════════════════════════
# csv_store.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestCSVStore:
    """CSV 存储引擎核心行为验证"""

    def _make_snapshot(self, vid="BV_test_001", views=1000):
        return VideoSnapshot(
            platform="bilibili", video_id=vid, title="测试视频",
            author="UP主", author_id="12345", snapshot_date="2026-04-17",
            view_count=views, like_count=100, comment_count=10,
            share_count=5, favorite_count=50, coin_count=20,
            danmaku_count=30, publish_date="2026-04-16",
            tags="SLG", url=f"https://bilibili.com/video/{vid}"
        )

    def test_save_and_load(self, tmp_path):
        store = CSVStore(data_dir=tmp_path)
        snaps = [self._make_snapshot("BV001"), self._make_snapshot("BV002")]
        path = store.save(snaps, platform="bilibili", data_type="videos", date_str="2026-04-17")
        assert path is not None
        assert path.exists()

        loaded = store.load(VideoSnapshot, platform="bilibili", data_type="videos", date_str="2026-04-17")
        assert len(loaded) == 2
        assert loaded[0].video_id == "BV001"
        assert loaded[1].video_id == "BV002"

    def test_idempotent_save(self, tmp_path):
        """同一天重复保存不会产生重复数据"""
        store = CSVStore(data_dir=tmp_path)
        snaps = [self._make_snapshot("BV001")]
        store.save(snaps, platform="bilibili", data_type="videos", date_str="2026-04-17")
        store.save(snaps, platform="bilibili", data_type="videos", date_str="2026-04-17")

        loaded = store.load(VideoSnapshot, platform="bilibili", data_type="videos", date_str="2026-04-17")
        assert len(loaded) == 1

    def test_save_empty_list(self, tmp_path):
        store = CSVStore(data_dir=tmp_path)
        result = store.save([], platform="bilibili", data_type="videos", date_str="2026-04-17")
        assert result is None

    def test_csv_has_bom(self, tmp_path):
        """新建文件必须包含 UTF-8 BOM 头"""
        store = CSVStore(data_dir=tmp_path)
        snaps = [self._make_snapshot("BV001")]
        path = store.save(snaps, platform="bilibili", data_type="videos", date_str="2026-04-17")
        with open(path, "rb") as f:
            first_bytes = f.read(3)
        assert first_bytes == b'\xef\xbb\xbf', "CSV 文件必须以 UTF-8 BOM 开头"

    def test_int_fields_round_trip(self, tmp_path):
        """整数字段经过 CSV 序列化/反序列化后仍为 int"""
        store = CSVStore(data_dir=tmp_path)
        snaps = [self._make_snapshot("BV001", views=999999)]
        store.save(snaps, platform="bilibili", data_type="videos", date_str="2026-04-17")
        loaded = store.load(VideoSnapshot, platform="bilibili", data_type="videos", date_str="2026-04-17")
        assert loaded[0].view_count == 999999
        assert isinstance(loaded[0].view_count, int)


# ═══════════════════════════════════════════════════════════════════════════════
# sentiment.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestSentiment:
    """情感分析准确性验证"""

    def setup_method(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive(self):
        sent, _ = self.analyzer.analyze_comment("这游戏太好玩了，强烈推荐")
        assert sent == "positive"

    def test_negative(self):
        sent, _ = self.analyzer.analyze_comment("垃圾骗氪游戏，已卸载")
        assert sent == "negative"

    def test_neutral(self):
        sent, _ = self.analyzer.analyze_comment("今天服务器更新了版本")
        assert sent == "neutral"

    def test_negation_positive_to_negative(self):
        """否定词 + 正面词 → 负面"""
        sent, _ = self.analyzer.analyze_comment("这游戏不好玩")
        assert sent == "negative"

    def test_negation_negative_to_positive(self):
        """否定词 + 负面词 → 正面"""
        sent, _ = self.analyzer.analyze_comment("并非垃圾，其实还行")
        assert sent in ("positive", "neutral")  # 至少不应是 negative

    def test_game_mention_extraction(self):
        _, mentions = self.analyzer.analyze_comment("从三战退坑来的，率土更好")
        assert "三国志战略版" in mentions
        assert "率土之滨" in mentions

    def test_empty_text(self):
        sent, mentions = self.analyzer.analyze_comment("")
        assert sent == "neutral"
        assert mentions == ""

    def test_batch_analyze(self):
        comments = [
            Comment(platform="test", video_id="v1", comment_id="c1",
                    author="u1", author_id="uid1", content="好玩推荐",
                    like_count=0, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
            Comment(platform="test", video_id="v1", comment_id="c2",
                    author="u2", author_id="uid2", content="垃圾退坑",
                    like_count=0, reply_count=0, publish_time="",
                    ip_location="", sentiment="", mentioned_games=""),
        ]
        self.analyzer.batch_analyze(comments)
        assert comments[0].sentiment == "positive"
        assert comments[1].sentiment == "negative"


# ═══════════════════════════════════════════════════════════════════════════════
# config.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfig:
    """配置加载边界条件验证"""

    def test_load_keywords_missing_file(self):
        from src.core.config import load_keywords
        cfg = load_keywords("/nonexistent/path/keywords.yaml")
        assert cfg.games == []
        assert cfg.categories == []

    def test_load_targets_missing_file(self):
        from src.core.config import load_targets
        cfg = load_targets("/nonexistent/path/targets.yaml")
        assert cfg.bilibili_channels == []

    def test_load_config_integration(self):
        from src.core.config import load_config
        cfg = load_config()
        # 应该能正常加载而不崩溃
        assert cfg is not None
        assert isinstance(cfg.keywords.all_keywords(), list)
