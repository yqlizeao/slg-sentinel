from __future__ import annotations

import argparse
import csv
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

SEARCH_METRIC_COLUMNS = [
    "snapshot_date",
    "platform",
    "keyword",
    "order",
    "limit",
    "total_results",
    "total_results_display",
    "is_capped",
    "num_pages",
    "page_size",
    "fetched_count",
    "pages",
    "error",
    "created_at",
]

LEGACY_SEARCH_METRIC_COLUMNS = [
    "snapshot_date",
    "platform",
    "keyword",
    "order",
    "limit",
    "total_results",
    "fetched_count",
    "pages",
    "error",
    "created_at",
]


def build_suffix(args: argparse.Namespace, num_keywords: int) -> str:
    plat_map = {
        "bilibili": "哔哩哔哩",
        "youtube": "YouTube",
        "taptap": "TapTap",
        "douyin": "抖音",
        "kuaishou": "快手",
        "xiaohongshu": "小红书",
    }
    p_name = plat_map.get(args.platform, args.platform)
    m_name = "免登陆" if getattr(args, "mode", "actions") == "actions" else "鉴权"
    d_name = "基础" if getattr(args, "depth", "shallow") == "shallow" else "深度"
    order_val = getattr(args, "order", "totalrank")
    order_names = {
        "totalrank": "TotalRank",
        "pubdate": "PublishDate",
        "click": "Click",
        "stow": "Stow",
        "danmaku": "Danmaku",
    }
    o_name = order_names.get(order_val, str(order_val).title())
    limit = getattr(args, "limit", 50)
    return f"{p_name}_{m_name}_{d_name}_{o_name}_{limit}结果_{num_keywords}关键词"


def is_deep_crawl(args: argparse.Namespace) -> bool:
    return getattr(args, "depth", "deep") == "deep"


def save_search_metrics(platform: str, metrics: list[dict], date_str: str) -> Path | None:
    if not metrics:
        return None

    metrics_dir = Path("data") / "search_metrics" / platform
    metrics_dir.mkdir(parents=True, exist_ok=True)
    file_path = metrics_dir / f"{date_str}_search_metrics.csv"
    fieldnames = SEARCH_METRIC_COLUMNS
    write_header = not file_path.exists()

    existing_rows = []
    if file_path.exists():
        with open(file_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            if header != fieldnames:
                for raw in reader:
                    if len(raw) == len(fieldnames):
                        existing_rows.append(dict(zip(fieldnames, raw)))
                    elif len(raw) == len(LEGACY_SEARCH_METRIC_COLUMNS):
                        existing_rows.append(dict(zip(LEGACY_SEARCH_METRIC_COLUMNS, raw)))
                write_header = True
                file_path.unlink()

    with open(file_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            for row in existing_rows:
                writer.writerow(
                    {
                        "snapshot_date": row.get("snapshot_date", ""),
                        "platform": row.get("platform", platform),
                        "keyword": row.get("keyword", ""),
                        "order": row.get("order", ""),
                        "limit": row.get("limit", ""),
                        "total_results": row.get("total_results", ""),
                        "total_results_display": row.get("total_results_display", ""),
                        "is_capped": row.get("is_capped", False),
                        "num_pages": row.get("num_pages", 0),
                        "page_size": row.get("page_size", 0),
                        "fetched_count": row.get("fetched_count", 0),
                        "pages": row.get("pages", 0),
                        "error": row.get("error", ""),
                        "created_at": row.get("created_at", ""),
                    }
                )
        for metric in metrics:
            writer.writerow(
                {
                    "snapshot_date": date_str,
                    "platform": platform,
                    "keyword": metric.get("keyword", ""),
                    "order": metric.get("order", ""),
                    "limit": metric.get("limit", ""),
                    "total_results": "" if metric.get("total_results") is None else metric.get("total_results"),
                    "total_results_display": metric.get("total_results_display", ""),
                    "is_capped": metric.get("is_capped", False),
                    "num_pages": metric.get("num_pages", 0),
                    "page_size": metric.get("page_size", 0),
                    "fetched_count": metric.get("fetched_count", 0),
                    "pages": metric.get("pages", 0),
                    "error": metric.get("error", ""),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
            )
    return file_path


def crawl(args: argparse.Namespace) -> None:
    logger.info(f"开始采集: platform={args.platform}, mode={args.mode}, date={args.date}")

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
    from src.adapters.bilibili import BilibiliAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = BilibiliAdapter()
    store = CSVStore()
    suffix = build_suffix(args, len(config.keywords.all_keywords()))
    all_snapshots = []
    search_metrics = []
    keywords = config.keywords.all_keywords()
    limit = getattr(args, "limit", 20)

    if not keywords:
        logger.warning("未找到关键词配置，请检查 keywords.yaml")
    else:
        logger.info(f"开始关键词搜索，共 {len(keywords)} 个关键词，每词限额 {limit} 条")
        for kw in keywords:
            try:
                snaps, metric = adapter.search_videos_with_meta(keyword=kw, limit=limit, order=args.order)
                all_snapshots.extend(snaps)
                search_metrics.append(metric)
                if metric.get("total_results") is None:
                    total_text = ""
                elif metric.get("is_capped"):
                    total_text = f"，B站搜索结果池 ≥{metric['total_results']}（接口封顶）"
                else:
                    total_text = f"，B站搜索结果总量 {metric['total_results']}"
                logger.info(f"关键词 '{kw}' 搜索到 {len(snaps)} 个视频{total_text}")
            except Exception as e:
                logger.error(f"关键词 '{kw}' 搜索失败: {e}")
                search_metrics.append(
                    {
                        "keyword": kw,
                        "order": args.order,
                        "limit": limit,
                        "total_results": None,
                        "total_results_display": "",
                        "is_capped": False,
                        "num_pages": 0,
                        "page_size": 0,
                        "fetched_count": 0,
                        "pages": 0,
                        "error": str(e),
                    }
                )

    metrics_path = save_search_metrics("bilibili", search_metrics, args.date)
    if metrics_path:
        print(f"📊  已记录 {len(search_metrics)} 条关键词搜索总量 → {metrics_path}")

    for channel in config.targets.bilibili_channels:
        if channel.uid and channel.uid != "xxx":
            logger.info(f"采集频道: {channel.name} (uid={channel.uid})")

    if args.mode == "actions":
        try:
            hot_snaps = adapter.get_hot_videos()
            logger.info(f"获取热门视频 {len(hot_snaps)} 条")
        except Exception as e:
            logger.error(f"获取热门视频失败（非致命）: {e}")

    if all_snapshots:
        file_path = store.save(all_snapshots, platform="bilibili", data_type="videos", date_str=args.date, filename_suffix=suffix)
        print(f"✅  已保存 {len(all_snapshots)} 条视频快照 → {file_path}")
        store.save(all_snapshots, platform="bilibili", data_type="summary", date_str=args.date, filename_suffix=suffix)
    else:
        print("⚠️  未采集到任何数据，请检查关键词配置和网络连接")

    if all_snapshots and is_deep_crawl(args):
        top_videos = sorted(all_snapshots, key=lambda s: s.view_count, reverse=True)[:3]
        for snap in top_videos:
            if not snap.video_id:
                continue
            try:
                comments = adapter.get_comments(snap.video_id, max_pages=5)
                if comments:
                    store.save(comments, platform="bilibili", data_type="comments", date_str=args.date, video_id=snap.video_id, filename_suffix=suffix)
                    logger.info(f"已保存 {len(comments)} 条评论: {snap.video_id}")
            except Exception as e:
                logger.error(f"采集评论失败 {snap.video_id}: {e}")


def _crawl_youtube(args: argparse.Namespace) -> None:
    from src.adapters.youtube import YouTubeAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = YouTubeAdapter()
    store = CSVStore()
    suffix = build_suffix(args, len(config.keywords.all_keywords()))
    all_snapshots = []
    keywords = config.keywords.all_keywords()
    limit = getattr(args, "limit", 20)

    if not keywords:
        logger.warning("未找到关键词配置，请检查 keywords.yaml")
    else:
        logger.info(f"YouTube 关键词搜索，共 {len(keywords)} 个关键词，限额 {limit} 条")
        for kw in keywords:
            try:
                snaps = adapter.search_videos(keyword=kw, limit=limit, order=args.order)
                all_snapshots.extend(snaps)
                logger.info(f"关键词 '{kw}' 搜索到 {len(snaps)} 条视频")
            except Exception as e:
                logger.error(f"关键词 '{kw}' YouTube 搜索失败: {e}")

    channel_sort = "newest" if getattr(args, "order", "totalrank") == "pubdate" else "popular"
    for channel in config.targets.youtube_channels:
        if channel.channel_id and channel.channel_id != "UCxxx":
            try:
                ch_snaps = adapter.get_channel_videos(channel_id=channel.channel_id, sort_by=channel_sort, limit=limit)
                all_snapshots.extend(ch_snaps)
                logger.info(f"频道 '{channel.name}' 获取 {len(ch_snaps)} 条视频")
            except Exception as e:
                logger.error(f"频道 '{channel.name}' 采集失败: {e}")

    seen_ids = set()
    unique_snapshots = []
    for snap in all_snapshots:
        if snap.video_id and snap.video_id not in seen_ids:
            seen_ids.add(snap.video_id)
            unique_snapshots.append(snap)
    all_snapshots = unique_snapshots

    if all_snapshots:
        file_path = store.save(all_snapshots, platform="youtube", data_type="videos", date_str=args.date, filename_suffix=suffix)
        print(f"✅  已保存 {len(all_snapshots)} 条 YouTube 视频快照 → {file_path}")
        store.save(all_snapshots, platform="youtube", data_type="summary", date_str=args.date, filename_suffix=suffix)
    else:
        print("⚠️  YouTube 未采集到任何数据，请检查关键词配置和网络连接")

    if all_snapshots and is_deep_crawl(args):
        top_videos = sorted(all_snapshots, key=lambda s: s.view_count, reverse=True)[:3]
        for snap in top_videos:
            if not snap.video_id:
                continue
            try:
                comments = adapter.get_comments(snap.video_id)
                if comments:
                    store.save(comments, platform="youtube", data_type="comments", date_str=args.date, video_id=snap.video_id, filename_suffix=suffix)
                    logger.info(f"已保存 {len(comments)} 条 YouTube 评论: {snap.video_id}")
            except Exception as e:
                logger.error(f"YouTube 评论采集失败 {snap.video_id}: {e}")


def _crawl_taptap(args: argparse.Namespace) -> None:
    from src.adapters.taptap import TapTapAdapter
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    config = load_config(keywords_file=args.keywords_file)
    adapter = TapTapAdapter()
    store = CSVStore()
    suffix = build_suffix(args, len(config.keywords.all_keywords()))
    all_reviews = []
    all_snapshots = []
    limit = getattr(args, "limit", 20)
    valid_games = [g for g in config.targets.taptap_games if g.app_id and g.app_id != "xxx"]

    if valid_games:
        logger.info(f"TapTap 采集 {len(valid_games)} 个目标游戏")
        for game in valid_games:
            try:
                snap = adapter.get_video_info(game.app_id)
                if snap:
                    snap.title = snap.title or game.name
                    all_snapshots.append(snap)
                if is_deep_crawl(args):
                    max_pages = max(1, (limit + 9) // 10)
                    reviews = adapter.get_reviews(app_id=game.app_id, game_name=game.name, sort="new", max_pages=max_pages)
                    all_reviews.extend(reviews[:limit])
                    logger.info(f"游戏 '{game.name}' 采集 {len(reviews[:limit])} 条评论")
            except Exception as e:
                logger.error(f"TapTap 游戏 '{game.name}' 采集失败: {e}")
    else:
        keywords = config.keywords.all_keywords()
        logger.info(f"targets.yaml 未配置 TapTap 游戏，改用关键词搜索（限额: {limit}）")
        for kw in keywords[:3]:
            try:
                snaps = adapter.search_videos(kw, limit=limit, order=args.order)
                all_snapshots.extend(snaps)
                logger.info(f"TapTap 搜索 '{kw}' 找到 {len(snaps)} 个游戏")
            except Exception as e:
                logger.error(f"TapTap 搜索失败 '{kw}': {e}")

    if all_snapshots:
        snap_path = store.save(all_snapshots, platform="taptap", data_type="videos", date_str=args.date, filename_suffix=suffix)
        print(f"✅  已保存 {len(all_snapshots)} 条 TapTap 游戏快照 → {snap_path}")
        store.save(all_snapshots, platform="taptap", data_type="summary", date_str=args.date, filename_suffix=suffix)

    if all_reviews:
        review_path = store.save(all_reviews, platform="taptap", data_type="reviews", date_str=args.date, filename_suffix=suffix)
        print(f"✅  已保存 {len(all_reviews)} 条 TapTap 评论 → {review_path}")
    elif not all_snapshots:
        print("⚠️  TapTap 未采集到任何数据，请在 targets.yaml 中配置 taptap_games")


def _crawl_media_crawler(args: argparse.Namespace) -> None:
    import os

    from src.adapters.media_crawler import MediaCrawlerBridge
    from src.core.config import load_config
    from src.core.csv_store import CSVStore

    if args.mode != "local":
        print(f"❌ 平台 {args.platform} 受极度严苛的风控保护，必须使用 --mode local (确保具有本地执行沙盒环境)。")
        return

    mc_root = os.environ.get("MEDIA_CRAWLER_ROOT", "MediaCrawler")
    try:
        bridge = MediaCrawlerBridge(mc_root)
    except FileNotFoundError:
        logger.error(f"未找到 MediaCrawler 隔离沙盒: {mc_root}")
        print("💡 提示: 请确保已执行 `git submodule update --init` 并完成了小本本/抖音的节点拉取。")
        return

    config = load_config(keywords_file=args.keywords_file)
    keywords = config.keywords.all_keywords()
    if keywords:
        print("🚀 [沙盒桥接] 正在向底层引擎投递参数，即将挂载爬虫进程...")
        print("👉 【注意】请观察终端随时可能弹出的【扫码请求】，务必使用对应的手机 App 配合打通鉴权！")
        success = bridge.run_spider(args.platform, keywords[:3])
        if not success:
            print("⚠️ [安全警报] 进程中断。可能需要重试扫码或目标平台的 API 结构已变更。")
            return

    print("📥 [收网作业] 扫描并迁移沙盒独立产生的 CSV 孤岛快照...")
    snaps, comments = bridge.import_platform_data(args.platform)
    if not snaps and not comments:
        logger.warning(f"由于风控流控或未发生有效产出，在 {bridge.mc_data_dir}/{args.platform} 中无新增数据。")
        return

    store = CSVStore()
    suffix = build_suffix(args, len(config.keywords.all_keywords()))
    if snaps:
        store.save(snaps, platform=args.platform, data_type="videos", date_str=args.date, filename_suffix=suffix)
        store.save(snaps, platform=args.platform, data_type="summary", date_str=args.date, filename_suffix=suffix)
    if comments:
        store.save(comments, platform=args.platform, data_type="comments", date_str=args.date, filename_suffix=suffix)
    print(f"✅  已从 MediaCrawler 导入 {args.platform} 数据: {len(snaps)} 视频, {len(comments)} 评论")
