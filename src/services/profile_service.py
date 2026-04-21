from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def run_profile(args: argparse.Namespace) -> None:
    from src.analysis.profiler import UserProfiler

    logger.info(f"开始用户画像: platform={args.platform}, video_id={args.video_id}")
    profiler = UserProfiler()
    try:
        profiles = profiler.profile_video_users(platform=args.platform, video_id=args.video_id, max_users=args.max_users)
        if profiles:
            profiler.save_profiles(profiles, args.platform)
            print(f"✅ 已针对 {args.platform} 视频 {args.video_id} 成功生成 {len(profiles)} 个用户画像！")
            for profile in profiles[:5]:
                print(f" - [{profile.username}] 分析结果: 年龄段 {profile.age_group}, 倾向 {profile.spend_type}, 标签 {profile.tags}")
            if len(profiles) > 5:
                print(f"   ...以及其他 {len(profiles) - 5} 位用户的画像。")
        else:
            print("⚠️ 未生成任何用户画像，请检查视频是否有评论数据。")
    except Exception as e:
        logger.error(f"生成用户画像失败: {e}")
