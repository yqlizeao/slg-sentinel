"""
SLG Sentinel 命令行入口

CLI 是系统唯一的用户入口，使用 argparse 实现子命令分发。
支持双模运行：--mode actions（GitHub Actions）/ --mode local（本地）。
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from src.core.config import setup_logging

logger = logging.getLogger(__name__)


def cmd_crawl(args: argparse.Namespace) -> None:
    """执行数据采集"""
    logger.info(
        f"开始采集: platform={args.platform}, mode={args.mode}, date={args.date}"
    )

    if args.platform == "bilibili":
        _crawl_bilibili(args)
    elif args.platform == "youtube":
        _crawl_youtube(args)
    elif args.platform == "taptap":
        _crawl_taptap(args)
    elif args.platform in ("douyin", "kuaishou", "xiaohongshu"):
        _crawl_media_crawler(args)
    elif args.mode != "local":
        print(f"❌  平台 {args.platform} 的采集逻辑在 actions 下可能受限，请在本地使用 MediaCrawler。")
    else:
        print(f"⚠️  {args.platform} 采集尚未实现。")


def _crawl_bilibili(args: argparse.Namespace) -> None:
    """B站采集主逻辑（Phase 1）"""
    from src.adapters.bilibili import BilibiliAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = BilibiliAdapter()
    store = CSVStore()
    date_str = args.date

    all_snapshots = []

    # 1. 关键词搜索
    keywords = config.keywords.all_keywords()
    if not keywords:
        logger.warning("未找到关键词配置，请检查 keywords.yaml")
    else:
        logger.info(f"开始关键词搜索，共 {len(keywords)} 个关键词")
        for kw in keywords:
            try:
                snaps = adapter.search_videos(keyword=kw, page=1)
                all_snapshots.extend(snaps)
                logger.info(f"关键词 '{kw}' 搜索到 {len(snaps)} 个视频")
            except Exception as e:
                logger.error(f"关键词 '{kw}' 搜索失败: {e}")

    # 2. 指定频道的视频详情
    bilibili_channels = config.targets.bilibili_channels
    for channel in bilibili_channels:
        if channel.uid and channel.uid != "xxx":
            logger.info(f"采集频道: {channel.name} (uid={channel.uid})")
            # 此处仅记录日志，具体频道视频列表需要 Cookie
            # actions 模式下通过关键词搜索覆盖

    # 3. 热门视频快照（可选，丰富数据）
    if args.mode == "actions":
        try:
            hot_snaps = adapter.get_hot_videos()
            # 筛选与 SLG 相关的（这里全量保存，分析层再过滤）
            logger.info(f"获取热门视频 {len(hot_snaps)} 条")
            # 不自动添加到 all_snapshots，避免数据量过大
        except Exception as e:
            logger.error(f"获取热门视频失败（非致命）: {e}")

    # 4. 保存到 CSV
    if all_snapshots:
        file_path = store.save(
            all_snapshots, platform="bilibili", data_type="videos", date_str=date_str
        )
        print(f"✅  已保存 {len(all_snapshots)} 条视频快照 → {file_path}")
    else:
        print("⚠️  未采集到任何数据，请检查关键词配置和网络连接")

    # 5. 保存到 snapshots（用于周增量计算）
    if all_snapshots:
        store.save(
            all_snapshots, platform="bilibili", data_type="snapshots", date_str=date_str
        )

    # 6. 局部评论采集：对浏览量 Top 3 视频采集评论
    if all_snapshots and args.mode in ("actions", "local"):
        top_videos = sorted(all_snapshots, key=lambda s: s.view_count, reverse=True)[:3]
        for snap in top_videos:
            if not snap.video_id:
                continue
            try:
                comments = adapter.get_comments(snap.video_id, max_pages=5)
                if comments:
                    store.save(
                        comments,
                        platform="bilibili",
                        data_type="comments",
                        date_str=date_str,
                        video_id=snap.video_id,
                    )
                    logger.info(
                        f"已保存 {len(comments)} 条评论: {snap.video_id}"
                    )
            except Exception as e:
                logger.error(f"采集评论失败 {snap.video_id}: {e}")


def _crawl_youtube(args: argparse.Namespace) -> None:
    """YouTube 采集主逻辑（Phase 2）"""
    from src.adapters.youtube import YouTubeAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = YouTubeAdapter()
    store = CSVStore()
    date_str = args.date

    all_snapshots = []

    # 1. 关键词搜索（每个关键词取前 20 条）
    keywords = config.keywords.all_keywords()
    if not keywords:
        logger.warning("未找到关键词配置，请检查 keywords.yaml")
    else:
        logger.info(f"YouTube 关键词搜索，共 {len(keywords)} 个关键词")
        for kw in keywords:
            try:
                snaps = adapter.search_videos(keyword=kw, max_results=20)
                all_snapshots.extend(snaps)
                logger.info(f"关键词 '{kw}' 搜索到 {len(snaps)} 条视频")
            except Exception as e:
                logger.error(f"关键词 '{kw}' YouTube 搜索失败: {e}")

    # 2. 指定频道视频列表（scrapetube，按播放量排序）
    youtube_channels = config.targets.youtube_channels
    for channel in youtube_channels:
        if channel.channel_id and channel.channel_id != "UCxxx":
            try:
                ch_snaps = adapter.get_channel_videos(
                    channel_id=channel.channel_id, sort_by="popular", limit=30
                )
                all_snapshots.extend(ch_snaps)
                logger.info(f"频道 '{channel.name}' 获取 {len(ch_snaps)} 条视频")
            except Exception as e:
                logger.error(f"频道 '{channel.name}' 采集失败: {e}")

    # 3. 去重（按 video_id）
    seen_ids = set()
    unique_snapshots = []
    for snap in all_snapshots:
        if snap.video_id and snap.video_id not in seen_ids:
            seen_ids.add(snap.video_id)
            unique_snapshots.append(snap)
    all_snapshots = unique_snapshots

    # 4. 保存到 CSV
    if all_snapshots:
        file_path = store.save(
            all_snapshots, platform="youtube", data_type="videos", date_str=date_str
        )
        print(f"✅  已保存 {len(all_snapshots)} 条 YouTube 视频快照 → {file_path}")
    else:
        print("⚠️  YouTube 未采集到任何数据，请检查关键词配置和网络连接")

    # 5. 保存到 snapshots（用于周增量计算）
    if all_snapshots:
        store.save(
            all_snapshots, platform="youtube", data_type="snapshots", date_str=date_str
        )

    # 6. 评论采集：Top 3 视频
    if all_snapshots and args.mode in ("actions", "local"):
        top_videos = sorted(all_snapshots, key=lambda s: s.view_count, reverse=True)[:3]
        for snap in top_videos:
            if not snap.video_id:
                continue
            try:
                comments = adapter.get_comments(snap.video_id)
                if comments:
                    store.save(
                        comments,
                        platform="youtube",
                        data_type="comments",
                        date_str=date_str,
                        video_id=snap.video_id,
                    )
                    logger.info(f"已保存 {len(comments)} 条 YouTube 评论: {snap.video_id}")
            except Exception as e:
                logger.error(f"YouTube 评论采集失败 {snap.video_id}: {e}")


def _crawl_taptap(args: argparse.Namespace) -> None:
    """TapTap 采集主逻辑（Phase 3）"""
    from src.adapters.taptap import TapTapAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = TapTapAdapter()
    store = CSVStore()
    date_str = args.date

    all_reviews = []
    all_snapshots = []

    # 1. 从 targets.yaml 中采集指定游戏评论
    taptap_games = config.targets.taptap_games
    valid_games = [g for g in taptap_games if g.app_id and g.app_id != "xxx"]

    if valid_games:
        logger.info(f"TapTap 采集 {len(valid_games)} 个目标游戏")
        for game in valid_games:
            try:
                # 获取游戏 snapshot
                snap = adapter.get_video_info(game.app_id)
                if snap:
                    snap.title = snap.title or game.name
                    all_snapshots.append(snap)

                # 获取评论
                reviews = adapter.get_reviews(
                    app_id=game.app_id,
                    game_name=game.name,
                    sort="new",
                    max_pages=20,
                )
                all_reviews.extend(reviews)
                logger.info(f"游戏 '{game.name}' 采集 {len(reviews)} 条评论")
            except Exception as e:
                logger.error(f"TapTap 游戏 '{game.name}' 采集失败: {e}")
    else:
        # 没有指定游戏时，通过关键词搜索
        keywords = config.keywords.all_keywords()
        logger.info(f"targets.yaml 未配置 TapTap 游戏，改用关键词搜索（{len(keywords)} 个关键词）")
        for kw in keywords[:3]:  # 关键词搜索限制3个，避免过度采集
            try:
                snaps = adapter.search_videos(kw)
                all_snapshots.extend(snaps)
                logger.info(f"TapTap 搜索 '{kw}' 找到 {len(snaps)} 个游戏")
            except Exception as e:
                logger.error(f"TapTap 搜索失败 '{kw}': {e}")

    # 2. 保存游戏 snapshots
    if all_snapshots:
        snap_path = store.save(
            all_snapshots, platform="taptap", data_type="videos", date_str=date_str
        )
        print(f"✅  已保存 {len(all_snapshots)} 条 TapTap 游戏快照 → {snap_path}")
        store.save(
            all_snapshots, platform="taptap", data_type="snapshots", date_str=date_str
        )

    # 3. 保存评论
    if all_reviews:
        review_path = store.save(
            all_reviews, platform="taptap", data_type="reviews", date_str=date_str
        )
        print(f"✅  已保存 {len(all_reviews)} 条 TapTap 评论 → {review_path}")
    elif not all_snapshots:
        print("⚠️  TapTap 未采集到任何数据，请在 targets.yaml 中配置 taptap_games")


def _crawl_media_crawler(args: argparse.Namespace) -> None:
    """抖音/快手/小红书 采集主逻辑（Phase 5 桥接 MediaCrawler）"""
    import os
    from src.adapters.media_crawler import MediaCrawlerBridge
    from src.core.csv_store import CSVStore

    mc_dir = os.environ.get("MEDIA_CRAWLER_DIR", "MediaCrawler/data")
    try:
        bridge = MediaCrawlerBridge(mc_dir)
        snaps, comments = bridge.import_platform_data(args.platform)
    except FileNotFoundError:
        logger.error(f"未找到 MediaCrawler 数据目录: {mc_dir}")
        print("💡 提示: 请先运行 MediaCrawler 采集数据，并通过设置 MEDIA_CRAWLER_DIR 注入其 data 目录路径。")
        return

    if not snaps and not comments:
        logger.warning(f"在 {mc_dir}/{args.platform} 中未解析到数据。")
        return

    store = CSVStore()
    date_str = args.date

    if snaps:
        store.save(snaps, platform=args.platform, data_type="videos", date_str=date_str)
        store.save(snaps, platform=args.platform, data_type="snapshots", date_str=date_str)
    
    if comments:
        store.save(comments, platform=args.platform, data_type="comments", date_str=date_str)
        
    print(f"✅  已从 MediaCrawler 导入 {args.platform} 数据: {len(snaps)} 视频, {len(comments)} 评论")


def cmd_profile(args: argparse.Namespace) -> None:
    """执行用户画像推断"""
    logger.info(
        f"开始用户画像: platform={args.platform}, video_id={args.video_id}"
    )
    
    from src.analysis.profiler import UserProfiler
    profiler = UserProfiler()
    
    try:
        profiles = profiler.profile_video_users(
            platform=args.platform,
            video_id=args.video_id,
            max_users=args.max_users
        )
        
        if profiles:
            profiler.save_profiles(profiles, args.platform)
            print(f"✅ 已针对 {args.platform} 视频 {args.video_id} 成功生成 {len(profiles)} 个用户画像！")
            for p in profiles[:5]:
                print(f" - [{p.username}] 分析结果: 年龄段 {p.age_group}, 倾向 {p.spend_type}, 标签 {p.tags}")
            if len(profiles) > 5:
                print(f"   ...以及其他 {len(profiles) - 5} 位用户的画像。")
        else:
            print("⚠️ 未生成任何用户画像，请检查视频是否有评论数据。")
            
    except Exception as e:
        logger.error(f"生成用户画像失败: {e}")


def cmd_analyze(args: argparse.Namespace) -> None:
    """执行数据分析"""
    logger.info(f"开始分析: type={args.type}")
    
    from src.core.config import load_config
    config = load_config()

    if args.type == "weekly":
        from src.analysis.weekly_report import WeeklyReportGenerator
        generator = WeeklyReportGenerator(config)
        report_path = generator.generate(date_str=args.date, output_dir=args.output_dir)
        print(f"✅  周报生成完毕: {report_path}")
    elif args.type == "sentiment":
        # 预留给独立的批量情感分析命令
        print("⚠️  独立情感分析功能尚未在 CLI 中直接暴露，目前已集成在 weekly 报表中。")
    else:
        print(f"⚠️  未知的分析类型: {args.type}")


def cmd_expand_keywords(args: argparse.Namespace) -> None:
    """执行关键词扩展"""
    logger.info(f"开始关键词扩展: provider={args.provider}")
    
    from src.core.config import load_config
    config = load_config()
    
    try:
        from src.core.keyword_expander import KeywordExpander
        expander = KeywordExpander(config)
        keywords = expander.expand(provider=args.provider, max_keywords=args.max_keywords)
        
        if keywords:
            print("\n✅ AI 扩展出的关键词如下：")
            for i, kw in enumerate(keywords, 1):
                print(f"{i}. {kw}")
            print(f"\n提示：可以将以上关键词更新到 keywords.yaml 的 expansion 列表中。")
        else:
            print("⚠️ 未生成任何关键词，请检查配置和环境变量 DEEPSEEK_API_KEY。")
            
    except Exception as e:
        logger.error(f"关键词扩展报错: {e}")


def build_parser() -> argparse.ArgumentParser:
    """构建 argparse 解析器"""
    parser = argparse.ArgumentParser(
        prog="slg-sentinel",
        description="SLG Sentinel —— SLG 游戏营销舆情监控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python -m src.cli crawl --platform bilibili --mode actions
  python -m src.cli crawl --platform youtube --mode local
  python -m src.cli profile --platform bilibili --video-id BV1xxxxxxxxxx
  python -m src.cli analyze --type weekly
  python -m src.cli expand-keywords --provider deepseek
""",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="启用详细日志输出"
    )

    subparsers = parser.add_subparsers(
        title="子命令",
        description="可用的子命令",
        dest="command",
    )

    # ─── crawl: 数据采集 ───────────────────────────────────────────
    crawl_parser = subparsers.add_parser(
        "crawl",
        help="采集平台数据",
        description="从指定平台采集视频、评论数据",
    )
    crawl_parser.add_argument(
        "--platform",
        required=True,
        choices=["bilibili", "youtube", "taptap", "douyin", "kuaishou", "xiaohongshu"],
        help="目标平台",
    )
    crawl_parser.add_argument(
        "--mode",
        required=True,
        choices=["actions", "local"],
        help="运行模式: actions=GitHub Actions(免登录), local=本地(完整功能)",
    )
    crawl_parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="采集日期，格式 YYYY-MM-DD（默认: 今天）",
    )
    crawl_parser.add_argument(
        "--keywords-file",
        default="keywords.yaml",
        help="关键词配置文件路径（默认: keywords.yaml）",
    )
    crawl_parser.set_defaults(func=cmd_crawl)

    # ─── profile: 用户画像 ─────────────────────────────────────────
    profile_parser = subparsers.add_parser(
        "profile",
        help="用户画像推断（需 Cookie，仅本地）",
        description="基于视频评论推断用户画像",
    )
    profile_parser.add_argument(
        "--platform",
        required=True,
        choices=["bilibili", "youtube", "taptap", "douyin", "kuaishou", "xiaohongshu"],
        help="目标平台",
    )
    profile_parser.add_argument(
        "--video-id",
        required=True,
        help="视频 ID（如 BV 号）",
    )
    profile_parser.add_argument(
        "--max-users",
        type=int,
        default=100,
        help="最大用户数（默认: 100）",
    )
    profile_parser.set_defaults(func=cmd_profile)

    # ─── analyze: 数据分析 ─────────────────────────────────────────
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="数据分析与报告生成",
        description="执行情感分析或生成周度报告",
    )
    analyze_parser.add_argument(
        "--type",
        required=True,
        choices=["weekly", "sentiment"],
        help="分析类型: weekly=周度报告, sentiment=情感分析",
    )
    analyze_parser.add_argument(
        "--platform",
        choices=["bilibili", "youtube", "taptap"],
        help="目标平台（情感分析时必需）",
    )
    analyze_parser.add_argument(
        "--date",
        help="分析日期，格式 YYYY-MM-DD",
    )
    analyze_parser.add_argument(
        "--output-dir",
        default="reports/",
        help="报告输出目录（默认: reports/）",
    )
    analyze_parser.set_defaults(func=cmd_analyze)

    # ─── expand-keywords: 关键词扩展 ──────────────────────────────
    expand_parser = subparsers.add_parser(
        "expand-keywords",
        help="使用 AI 扩展关键词",
        description="使用 LLM 从种子关键词自动扩展搜索词",
    )
    expand_parser.add_argument(
        "--provider",
        default="deepseek",
        choices=["deepseek", "openai", "qwen"],
        help="LLM 提供商（默认: deepseek）",
    )
    expand_parser.add_argument(
        "--max-keywords",
        type=int,
        default=50,
        help="最大扩展关键词数量（默认: 50）",
    )
    expand_parser.set_defaults(func=cmd_expand_keywords)

    return parser


def main() -> None:
    """CLI 主入口"""
    parser = build_parser()
    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # 分发子命令
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
