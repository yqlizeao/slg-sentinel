"""
SLG Sentinel — 总览页数据服务

提供总览页所需的洞察数据：周报核心发现、关键词趋势、高赞评论精选。
"""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


def get_weekly_insights(date_str: str | None = None) -> list[dict]:
    """
    从最近一份周报 JSON 中提取 LLM 聚类结果。

    Returns:
        聚类洞察列表，每个元素: {topic, sentiment, core_demand, count, representative_quotes}
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 尝试最近 14 天的周报
    for days_ago in range(15):
        d = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        json_path = REPORTS_DIR / f"{d}_weekly_report.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                insights = payload.get("insights", [])
                if insights:
                    return insights
            except Exception as e:
                logger.warning(f"读取周报 JSON 失败 {json_path}: {e}")
    return []


def get_weekly_summary_text(date_str: str | None = None) -> list[str]:
    """
    从周报 JSON 中生成简洁的摘要文案列表（用于首页 Hero 区域）。

    Returns:
        摘要文案列表，每条为一句中文描述
    """
    insights = get_weekly_insights(date_str)
    if not insights:
        return []

    summaries = []
    for item in insights[:5]:
        topic = item.get("topic", "")
        sentiment = item.get("sentiment", "mixed")
        demand = item.get("core_demand", "")
        count = item.get("count", 0)
        emoji = {"positive": "📈", "negative": "⚠️", "mixed": "💬"}.get(sentiment, "💬")
        summaries.append(f"{emoji} 「{topic}」— {demand}（{count} 条相关评论）")
    return summaries


def get_keyword_trends(days: int = 14) -> list[dict]:
    """
    读取搜索指标，返回近 N 天各关键词的搜索量趋势数据。

    Returns:
        列表，每个元素: {date, keyword, total_results}
    """
    metrics_dir = DATA_DIR / "search_metrics"
    if not metrics_dir.exists():
        return []

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = []

    for platform_dir in metrics_dir.iterdir():
        if not platform_dir.is_dir():
            continue
        for csv_file in sorted(platform_dir.glob("*_search_metrics.csv")):
            file_date = csv_file.stem[:10]
            if file_date < cutoff:
                continue
            try:
                with open(csv_file, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total = row.get("total_results", "")
                        if total and total != "None" and total != "":
                            try:
                                rows.append({
                                    "date": row.get("snapshot_date", file_date),
                                    "keyword": row.get("keyword", ""),
                                    "total_results": int(total),
                                })
                            except ValueError:
                                continue
            except Exception:
                continue

    return rows


def get_top_comments(limit: int = 10) -> list[dict]:
    """
    跨平台筛选高赞评论（按 like_count 降序）。

    Returns:
        评论字典列表: {platform, video_id, author, content, like_count, publish_time, sentiment}
    """
    comments = []

    # 扫描所有平台的 comments 目录
    for category in ("video_platforms", "community_platforms"):
        cat_dir = DATA_DIR / category
        if not cat_dir.exists():
            continue
        for platform_dir in cat_dir.iterdir():
            if not platform_dir.is_dir():
                continue
            comments_dir = platform_dir / "comments"
            if not comments_dir.exists():
                continue
            # 只读取最近 7 天的文件
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            for csv_file in sorted(comments_dir.glob("*.csv"), reverse=True):
                file_date = csv_file.stem[:10]
                if file_date < cutoff:
                    continue
                try:
                    with open(csv_file, "r", encoding="utf-8-sig") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            like = 0
                            try:
                                like = int(row.get("like_count", 0) or 0)
                            except ValueError:
                                pass
                            content = row.get("content", "")
                            if not content or like < 1:
                                continue
                            comments.append({
                                "platform": row.get("platform", platform_dir.name),
                                "video_id": row.get("video_id", ""),
                                "author": row.get("author", ""),
                                "content": content[:200],
                                "like_count": like,
                                "publish_time": row.get("publish_time", ""),
                                "sentiment": row.get("sentiment", ""),
                            })
                except Exception:
                    continue

    # 按赞数排序
    comments.sort(key=lambda c: c["like_count"], reverse=True)
    return comments[:limit]
