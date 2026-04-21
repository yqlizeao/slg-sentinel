from src.analysis.profiler import UserProfiler
from src.core.csv_store import CSVStore
from src.core.models import Comment, UserProfile, VideoSnapshot


def _snapshot(video_id="BV001", date_str="2026-04-20", tags="SLG,三国"):
    return VideoSnapshot(
        platform="bilibili",
        video_id=video_id,
        title="SLG 测试视频",
        author="测试UP",
        author_id="up-1",
        snapshot_date=date_str,
        view_count=100,
        like_count=10,
        comment_count=2,
        share_count=0,
        favorite_count=0,
        coin_count=0,
        danmaku_count=0,
        publish_date="2026-04-20",
        tags=tags,
        url=f"https://www.bilibili.com/video/{video_id}",
    )


def _comment(comment_id, author_id, content, ip_location="上海"):
    return Comment(
        platform="bilibili",
        video_id="BV001",
        comment_id=comment_id,
        author=f"玩家{author_id}",
        author_id=author_id,
        content=content,
        like_count=0,
        reply_count=0,
        publish_time="2026-04-20",
        ip_location=ip_location,
        sentiment="",
        mentioned_games="",
    )


def test_profiler_returns_empty_when_no_comments(tmp_path):
    profiler = UserProfiler()
    profiler.store = CSVStore(data_dir=tmp_path / "data")

    profiles = profiler.profile_video_users("bilibili", "BV001", date_str="2026-04-20")

    assert profiles == []


def test_profiler_groups_comments_by_user_and_infers_rules(tmp_path):
    store = CSVStore(data_dir=tmp_path / "data")
    store.save([_snapshot()], "bilibili", "videos", "2026-04-20")
    store.save(
        [
            _comment("c1", "u1", "下班后还要上班打卡，648 充了几万，满红也累"),
            _comment("c2", "u1", "大地图机制和配将很硬核"),
            _comment("c3", "u2", "学生放假随便玩，立绘好看"),
        ],
        "bilibili",
        "comments",
        "2026-04-20",
        video_id="BV001",
    )

    profiler = UserProfiler()
    profiler.store = store

    profiles = profiler.profile_video_users("bilibili", "BV001", max_users=10, date_str="2026-04-20")
    by_user = {profile.user_id: profile for profile in profiles}

    assert len(profiles) == 2
    assert by_user["u1"].age_group == "25-35"
    assert by_user["u1"].spend_type == "whale"
    assert "重氪难民" in by_user["u1"].tags
    assert "硬核考究党" in by_user["u1"].tags
    assert "SLG受众" in by_user["u1"].tags
    assert by_user["u2"].age_group == "18-22"
    assert by_user["u2"].spend_type == "free"
    assert "休闲风景党" in by_user["u2"].tags


def test_profiler_save_profiles_writes_to_profiles_directory(tmp_path):
    profiler = UserProfiler()
    profiler.store = CSVStore(data_dir=tmp_path / "data")
    profiles = [
        UserProfile(
            platform="bilibili",
            user_id="u1",
            username="玩家u1",
            age_group="25-35",
            spend_type="dolphin",
            tags="SLG受众",
            location="北京",
            last_active_time="2026-04-20 10:00:00",
        )
    ]

    profiler.save_profiles(profiles, "bilibili")

    output_path = tmp_path / "data" / "profiles" / "user_games" / "bilibili_user_games.csv"
    assert output_path.exists()
    saved = profiler.store.load(UserProfile, platform="profiles", data_type="user_games", date_str="bilibili")
    assert len(saved) == 1
    assert saved[0].user_id == "u1"
