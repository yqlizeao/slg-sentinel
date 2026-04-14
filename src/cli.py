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
    # TODO: Phase 1-3 实现各平台采集逻辑
    print(f"⚠️  采集功能尚未实现（platform={args.platform}, mode={args.mode}）")


def cmd_profile(args: argparse.Namespace) -> None:
    """执行用户画像推断"""
    logger.info(
        f"开始用户画像: platform={args.platform}, video_id={args.video_id}"
    )
    # TODO: Phase 5 实现用户画像功能
    print(f"⚠️  用户画像功能尚未实现（platform={args.platform}）")


def cmd_analyze(args: argparse.Namespace) -> None:
    """执行数据分析"""
    logger.info(f"开始分析: type={args.type}")
    # TODO: Phase 4 实现分析功能
    print(f"⚠️  分析功能尚未实现（type={args.type}）")


def cmd_expand_keywords(args: argparse.Namespace) -> None:
    """执行关键词扩展"""
    logger.info(f"开始关键词扩展: provider={args.provider}")
    # TODO: Phase 4 实现关键词扩展
    print(f"⚠️  关键词扩展功能尚未实现（provider={args.provider}）")


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
        choices=["bilibili"],
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
