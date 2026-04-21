import json

from src.analysis.weekly_report import WeeklyReportGenerator
from src.core.config import SentinelConfig
from src.core.csv_store import CSVStore
from src.core.models import Comment, TapTapReview, VideoSnapshot


def _snapshot(video_id="BV001", date_str="2026-04-20", views=1000, likes=100, comments=2):
    return VideoSnapshot(
        platform="bilibili",
        video_id=video_id,
        title="三战竞品观察",
        author="测试UP",
        author_id="up-1",
        snapshot_date=date_str,
        view_count=views,
        like_count=likes,
        comment_count=comments,
        share_count=1,
        favorite_count=5,
        coin_count=3,
        danmaku_count=4,
        publish_date="2026-04-18",
        tags="SLG,三国",
        url=f"https://www.bilibili.com/video/{video_id}",
    )


def _comment(comment_id, content, likes=0, author_id="user-1"):
    return Comment(
        platform="bilibili",
        video_id="BV001",
        comment_id=comment_id,
        author=author_id,
        author_id=author_id,
        content=content,
        like_count=likes,
        reply_count=0,
        publish_time="2026-04-20",
        ip_location="北京",
        sentiment="",
        mentioned_games="",
    )


def test_weekly_report_generates_markdown_and_json_with_video_snapshot(tmp_path):
    store = CSVStore(data_dir=tmp_path / "data")
    store.save([_snapshot(date_str="2026-04-13", views=500, likes=50, comments=1)], "bilibili", "snapshots", "2026-04-13")
    store.save([_snapshot(date_str="2026-04-20", views=1200, likes=120, comments=3)], "bilibili", "snapshots", "2026-04-20")
    store.save(
        [
            _comment("c1", "三战玩家觉得这游戏好玩推荐", likes=2, author_id="u1"),
            _comment("c2", "率土玩家也觉得垃圾骗氪", likes=5, author_id="u2"),
        ],
        "bilibili",
        "comments",
        "2026-04-20",
        video_id="BV001",
    )

    generator = WeeklyReportGenerator(SentinelConfig())
    generator.store = store

    report_path = generator.generate(date_str="2026-04-20", output_dir=str(tmp_path / "reports"))
    json_path = report_path.with_suffix(".json")

    assert report_path.exists()
    assert json_path.exists()
    assert "+700" in report_path.read_text(encoding="utf-8")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["sentiment"]["positive"] == 1
    assert payload["sentiment"]["negative"] == 1
    assert payload["mentions"]["三国志战略版"] == 1
    assert payload["mentions"]["率土之滨"] == 1


def test_weekly_report_no_increment_message_when_no_video_data(tmp_path):
    generator = WeeklyReportGenerator(SentinelConfig())
    generator.store = CSVStore(data_dir=tmp_path / "data")

    report_path = generator.generate(date_str="2026-04-20", output_dir=str(tmp_path / "reports"))
    report_text = report_path.read_text(encoding="utf-8")

    assert "本周暂无视频播放量增量数据" in report_text
    assert report_path.with_suffix(".json").exists()


def test_taptap_reviews_convert_to_comments_for_analysis():
    review = TapTapReview(
        game_id="game-1",
        game_name="测试游戏",
        review_id="review-1",
        author="玩家A",
        author_id="author-1",
        score=2,
        content="垃圾骗氪",
        device="iPhone",
        spent="10小时",
        ups=7,
        downs=1,
        publish_time="2026-04-20",
        sentiment="",
        mentioned_games="",
    )

    comments = WeeklyReportGenerator._reviews_to_comments([review])

    assert len(comments) == 1
    assert comments[0].platform == "taptap"
    assert comments[0].video_id == "game-1"
    assert comments[0].comment_id == "review-1"
    assert comments[0].like_count == 7
    assert comments[0].content == "垃圾骗氪"


def test_weekly_report_json_includes_taptap_sentiment_and_mentions(tmp_path):
    store = CSVStore(data_dir=tmp_path / "data")
    review = TapTapReview(
        game_id="game-1",
        game_name="测试游戏",
        review_id="review-1",
        author="玩家A",
        author_id="author-1",
        score=5,
        content="三战和率土玩家也关注，这个很好玩，推荐",
        device="Android",
        spent="20小时",
        ups=3,
        downs=0,
        publish_time="2026-04-20",
        sentiment="",
        mentioned_games="",
    )
    store.save([review], "taptap", "reviews", "2026-04-20")

    generator = WeeklyReportGenerator(SentinelConfig())
    generator.store = store

    report_path = generator.generate(date_str="2026-04-20", output_dir=str(tmp_path / "reports"))
    payload = json.loads(report_path.with_suffix(".json").read_text(encoding="utf-8"))

    assert payload["sentiment"]["positive"] == 1
    assert payload["mentions"]["三国志战略版"] == 1
    assert payload["mentions"]["率土之滨"] == 1
