from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def run_analysis(args: argparse.Namespace) -> None:
    logger.info(f"开始分析: type={args.type}")
    from src.core.config import load_config

    config = load_config()
    if args.type == "weekly":
        from src.analysis.weekly_report import WeeklyReportGenerator

        generator = WeeklyReportGenerator(config)
        report_path = generator.generate(date_str=args.date, output_dir=args.output_dir)
        print(f"✅  周报生成完毕: {report_path}")
    elif args.type == "sentiment":
        print("⚠️  独立情感分析功能尚未在 CLI 中直接暴露，目前已集成在 weekly 报表中。")
    else:
        print(f"⚠️  未知的分析类型: {args.type}")
