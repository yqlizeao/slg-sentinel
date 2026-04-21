"""
SLG Sentinel 命令行入口

CLI 负责参数解析、日志配置和服务层分发。
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime

from src.core.config import setup_logging
from src.services.crawl_service import crawl
from src.services.profile_service import run_profile
from src.services.report_service import run_analysis

logger = logging.getLogger(__name__)


def cmd_crawl(args: argparse.Namespace) -> None:
    crawl(args)


def cmd_profile(args: argparse.Namespace) -> None:
    run_profile(args)


def cmd_analyze(args: argparse.Namespace) -> None:
    run_analysis(args)


def cmd_expand_keywords(args: argparse.Namespace) -> None:
    logger.info(f"开始关键词扩展: provider={args.provider}")

    from src.core.config import load_config
    from src.core.keyword_expander import KeywordExpander

    config = load_config()
    try:
        expander = KeywordExpander(config)
        keywords = expander.expand(provider=args.provider, max_keywords=args.max_keywords)
        if keywords:
            print("\n✅ AI 扩展出的关键词如下：")
            for idx, keyword in enumerate(keywords, 1):
                print(f"{idx}. {keyword}")
            print("\n提示：可以将以上关键词更新到 keywords.yaml 的 expansion 列表中。")
        else:
            print("⚠️ 未生成任何关键词，请检查配置和环境变量 DEEPSEEK_API_KEY。")
    except Exception as e:
        logger.error(f"关键词扩展报错: {e}")


def build_parser() -> argparse.ArgumentParser:
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
    parser.add_argument("-v", "--verbose", action="store_true", help="启用详细日志输出")

    subparsers = parser.add_subparsers(title="子命令", description="可用的子命令", dest="command")

    crawl_parser = subparsers.add_parser("crawl", help="采集平台数据", description="从指定平台采集视频、评论数据")
    crawl_parser.add_argument("--platform", required=True, choices=["bilibili", "youtube", "taptap", "douyin", "kuaishou", "xiaohongshu"], help="目标平台")
    crawl_parser.add_argument("--mode", required=True, choices=["actions", "local"], help="运行模式: actions=GitHub Actions(免登录), local=本地(完整功能)")
    crawl_parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"), help="采集日期，格式 YYYY-MM-DD（默认: 今天）")
    crawl_parser.add_argument("--depth", choices=["shallow", "deep"], default="deep", help="采集深度（shallow=仅元数据，deep=含完整评论体和附加信息）")
    crawl_parser.add_argument("--order", type=str, default="totalrank", choices=["totalrank", "click", "pubdate", "stow", "danmaku"], help="高级搜索排序，供特定平台使用 (如 Bilibili)")
    crawl_parser.add_argument("--keywords-file", default="keywords.yaml", help="关键词配置文件路径（默认: keywords.yaml）")
    crawl_parser.add_argument("--limit", type=int, default=20, help="最大截断限额，各平台采集阈值")
    crawl_parser.set_defaults(func=cmd_crawl)

    profile_parser = subparsers.add_parser("profile", help="用户画像推断（需 Cookie，仅本地）", description="基于视频评论推断用户画像")
    profile_parser.add_argument("--platform", required=True, choices=["bilibili", "youtube", "taptap", "douyin", "kuaishou", "xiaohongshu"], help="目标平台")
    profile_parser.add_argument("--video-id", required=True, help="视频 ID（如 BV 号）")
    profile_parser.add_argument("--max-users", type=int, default=100, help="最大用户数（默认: 100）")
    profile_parser.set_defaults(func=cmd_profile)

    analyze_parser = subparsers.add_parser("analyze", help="数据分析与报告生成", description="执行情感分析或生成周度报告")
    analyze_parser.add_argument("--type", required=True, choices=["weekly", "sentiment"], help="分析类型: weekly=周度报告, sentiment=情感分析")
    analyze_parser.add_argument("--platform", choices=["bilibili", "youtube", "taptap"], help="目标平台（情感分析时必需）")
    analyze_parser.add_argument("--date", help="分析日期，格式 YYYY-MM-DD")
    analyze_parser.add_argument("--output-dir", default="reports/", help="报告输出目录（默认: reports/）")
    analyze_parser.set_defaults(func=cmd_analyze)

    expand_parser = subparsers.add_parser("expand-keywords", help="使用 AI 扩展关键词", description="使用 LLM 从种子关键词自动扩展搜索词")
    expand_parser.add_argument("--provider", default="deepseek", choices=["deepseek", "openai", "qwen"], help="LLM 提供商（默认: deepseek）")
    expand_parser.add_argument("--max-keywords", type=int, default=50, help="最大扩展关键词数量（默认: 50）")
    expand_parser.set_defaults(func=cmd_expand_keywords)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
