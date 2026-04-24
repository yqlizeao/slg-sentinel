"""
SLG Sentinel — 平台统计服务

提供各平台数据量统计、系统健康概况、数据文件管理。
拆分自 app_services.py。
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from ui.services.app_services import DATA_DIR, KEYWORDS_FILE, TARGETS_FILE, load_yaml, count_csv_rows


def get_platform_stats(platform: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")

    from src.core.csv_store import COMMUNITY_PLATFORMS, VIDEO_PLATFORMS

    if platform in VIDEO_PLATFORMS:
        cat = "video_platforms"
    elif platform in COMMUNITY_PLATFORMS:
        cat = "community_platforms"
    else:
        cat = "misc_platforms"

    v_dir = DATA_DIR / cat / platform / "videos"
    c_dir = DATA_DIR / cat / platform / "comments"

    v_total = sum(count_csv_rows(f) for f in v_dir.glob("*.csv")) if v_dir.exists() else 0
    c_total = sum(count_csv_rows(f) for f in c_dir.glob("*.csv")) if c_dir.exists() else 0
    v_today = sum(count_csv_rows(f) for f in v_dir.glob(f"{today}_*.csv")) if v_dir.exists() else 0
    c_today = sum(count_csv_rows(f) for f in c_dir.glob(f"{today}_*.csv")) if c_dir.exists() else 0
    return {"videos_total": v_total, "comments_total": c_total, "videos_today": v_today, "comments_today": c_today}


@st.cache_data(ttl=300)
def get_system_health() -> dict:
    total_v, total_c, last_sync = 0, 0, 0
    for platform in ["bilibili", "youtube", "taptap"]:
        stats = get_platform_stats(platform)
        total_v += stats["videos_total"]
        total_c += stats["comments_total"]

    if DATA_DIR.exists():
        for subdir in ["video_platforms", "community_platforms", "summary"]:
            target = DATA_DIR / subdir
            if target.exists():
                for csv_file in target.rglob("*.csv"):
                    if csv_file.is_file():
                        mtime = csv_file.stat().st_mtime
                        if mtime > last_sync:
                            last_sync = mtime

    targets_data = load_yaml(TARGETS_FILE).get("targets", {})
    total_targets = (
        len(targets_data.get("bilibili_channels", []))
        + len(targets_data.get("youtube_channels", []))
        + len(targets_data.get("taptap_games", []))
    )
    keyword_data = load_yaml(KEYWORDS_FILE).get("seed_keywords", {})
    total_keywords = sum(len(v) for v in keyword_data.values() if isinstance(v, list))

    return {
        "capacity": total_v + total_c,
        "last_sync": datetime.fromtimestamp(last_sync).strftime("%m-%d %H:%M") if last_sync else "暂无记录",
        "targets": total_targets,
        "keywords": total_keywords,
        "api_health": bool(os.environ.get("DEEPSEEK_API_KEY")),
    }


def list_loaded_csv_files() -> list[dict]:
    data_base_dir = DATA_DIR
    all_csv_files = list(data_base_dir.rglob("*.csv")) if data_base_dir.exists() else []
    results = []
    for file_path in sorted(all_csv_files, key=lambda path: path.name, reverse=True):
        rel_parts = file_path.relative_to(data_base_dir).parts
        file_size_kb = file_path.stat().st_size / 1024
        display_html = f"<div style='font-family:monospace; font-size:13px; color:rgba(232,228,220,0.72); padding-top:8px;'><b>{file_path.name}</b></div>"
        if len(rel_parts) >= 4 and rel_parts[0] in ["video_platforms", "community_platforms"]:
            platform_name = rel_parts[1].capitalize()
            data_type = rel_parts[2].capitalize()
            badge_color = "#6B8BDB" if "video" in data_type.lower() else "#9B7FD4" if "comment" in data_type.lower() else "#5B9A6E"
            plat_tag = f"<span style='background:rgba(180,160,120,0.10); color:rgba(232,228,220,0.55); padding:2px 6px; border-radius:4px; margin-right:6px;'>{platform_name}</span>"
            type_tag = f"<span style='background:{badge_color}20; color:{badge_color}; padding:2px 6px; border-radius:4px; margin-right:8px;'>{data_type}</span>"
            display_html = f"<div style='font-family:monospace; font-size:13px; color:rgba(232,228,220,0.72); padding-top:8px; white-space:nowrap;'>{plat_tag}{type_tag} <b>{file_path.name}</b></div>"
        elif len(rel_parts) == 3 and rel_parts[0] == "summary":
            display_html = (
                f"<div style='font-family:monospace; font-size:13px; color:rgba(232,228,220,0.72); padding-top:8px; white-space:nowrap;'>"
                f"<span style='background:rgba(212,175,55,0.12); color:#d4af37; padding:2px 6px; border-radius:4px; margin-right:6px;'>Summary</span>"
                f"<span style='background:rgba(107,139,219,0.12); color:#6B8BDB; padding:2px 6px; border-radius:4px; margin-right:8px;'>{rel_parts[1].capitalize()}</span> "
                f"<b>{file_path.name}</b></div>"
            )
        else:
            display_html = f"<div style='font-family:monospace; font-size:13px; color:rgba(232,228,220,0.72); padding-top:8px;'><b>{'/'.join(rel_parts[:-1])}</b> / {file_path.name}</div>"

        results.append({"path": file_path, "display_html": display_html, "size_kb": file_size_kb})
    return results


def delete_all_loaded_csv_files() -> None:
    for item in list_loaded_csv_files():
        try:
            os.remove(item["path"])
        except Exception:
            continue


def delete_loaded_csv_file(file_path: Path) -> None:
    os.remove(file_path)
