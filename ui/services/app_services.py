from __future__ import annotations

import csv
import html as _html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
KEYWORDS_FILE = ROOT / "keywords.yaml"
TARGETS_FILE = ROOT / "targets.yaml"

PLATFORM_BRAND_ICONS = {
    "bilibili": "https://www.bilibili.com/favicon.ico",
    "youtube": "https://www.youtube.com/favicon.ico",
    "taptap": "https://www.taptap.cn/favicon.ico",
    "douyin": "https://www.douyin.com/favicon.ico",
    "kuaishou": "https://www.kuaishou.com/favicon.ico",
    "xiaohongshu": "https://www.xiaohongshu.com/favicon.ico",
}

PLATFORM_OPTIONS = {
    "bilibili": "哔哩哔哩",
    "youtube": "YouTube",
    "taptap": "TapTap",
    "douyin": "抖音",
    "kuaishou": "快手",
    "xiaohongshu": "小红书",
}


def load_yaml(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def run_cli(args: list[str]) -> tuple[str, str, int]:
    cmd = [sys.executable, "-m", "src.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    return result.stdout, result.stderr, result.returncode


def run_cli_stream(args: list[str], on_line=None) -> tuple[str, str, int]:
    cmd = [sys.executable, "-u", "-m", "src.cli"] + args
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(ROOT),
        env=env,
        bufsize=1,
    )

    output_lines = []
    assert proc.stdout is not None
    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        output_lines.append(line)
        if on_line:
            on_line(line)

    return_code = proc.wait()
    return "\n".join(output_lines), "", return_code


def format_file_mtime(path: Path) -> str:
    if not path.exists():
        return "尚未保存"
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M:%S")


def init_crawl_progress_state(platform: str, keyword_count: int, limit_val: int) -> dict:
    return {
        "platform": platform,
        "keyword_total": max(keyword_count, 1),
        "keyword_done": 0,
        "comment_done": 0,
        "progress": 0.03,
        "stage": "准备启动",
        "detail": f"预计检索 {keyword_count} 个关键词，每词上限 {limit_val} 条",
        "started_at": datetime.now(),
    }


def update_crawl_progress_state(state: dict, line: str) -> None:
    clean = line.strip()
    if not clean:
        return

    state["detail"] = clean

    keyword_match = re.search(r"共\s+(\d+)\s+个关键词", clean)
    if keyword_match:
        state["keyword_total"] = max(int(keyword_match.group(1)), 1)
        state["stage"] = "正在检索关键词"
        state["progress"] = max(state["progress"], 0.10)
        return

    if "关键词 '" in clean and ("搜索到" in clean or "搜索失败" in clean):
        state["keyword_done"] += 1
        total = max(state["keyword_total"], 1)
        state["stage"] = f"正在检索关键词（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total)))
        return

    if "TapTap 搜索 '" in clean and ("找到" in clean or "失败" in clean):
        state["keyword_done"] += 1
        total = max(state["keyword_total"], 1)
        state["stage"] = f"正在检索关键词（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total)))
        return

    if "游戏 '" in clean and "采集" in clean and "条评论" in clean:
        state["keyword_done"] += 1
        total = max(state["keyword_total"], 1)
        state["stage"] = f"正在采集目标内容（{min(state['keyword_done'], total)}/{total}）"
        state["progress"] = max(state["progress"], min(0.72, 0.10 + 0.62 * (state["keyword_done"] / total)))
        return

    if "采集频道:" in clean or ("频道 '" in clean and "获取" in clean and "条视频" in clean):
        state["stage"] = "正在补充目标内容"
        state["progress"] = max(state["progress"], 0.76)
        return

    if "获取热门视频" in clean:
        state["stage"] = "正在补充热门内容"
        state["progress"] = max(state["progress"], 0.80)
        return

    if "已保存" in clean and ("视频快照" in clean or "游戏快照" in clean):
        state["stage"] = "正在写入视频结果"
        state["progress"] = max(state["progress"], 0.88)
        return

    if "已保存" in clean and "评论" in clean:
        state["comment_done"] += 1
        state["stage"] = "正在写入评论结果"
        state["progress"] = max(state["progress"], min(0.97, 0.90 + 0.025 * state["comment_done"]))
        return

    if "扫码授权" in clean or "[沙盒桥接]" in clean:
        state["stage"] = "等待本地授权"
        state["progress"] = max(state["progress"], 0.20)
        return

    if "[收网作业]" in clean:
        state["stage"] = "正在导入本地结果"
        state["progress"] = max(state["progress"], 0.78)
        return

    if "已从 MediaCrawler 导入" in clean:
        state["stage"] = "正在写入采集结果"
        state["progress"] = max(state["progress"], 0.96)


def estimate_remaining_seconds(progress_state: dict) -> int | None:
    progress = progress_state.get("progress", 0.0)
    if progress <= 0.08:
        return None
    elapsed = max((datetime.now() - progress_state["started_at"]).total_seconds(), 1.0)
    total_estimated = elapsed / progress
    return max(int(total_estimated - elapsed), 0)


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8-sig") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0


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


def _build_slg_filter_terms() -> set[str]:
    terms = set()
    try:
        cfg = load_yaml(KEYWORDS_FILE)
        for value in cfg.get("seed_keywords", {}).values():
            if isinstance(value, list):
                terms.update(str(term).strip() for term in value if term)
    except Exception:
        pass
    terms.update(["率土之滨", "三国志战略版", "万国觉醒", "文明与征服", "鸿图之下", "寰宇之战", "SLG", "策略"])
    return terms


_SLG_TERMS = _build_slg_filter_terms()


def _is_slg_relevant(row: dict) -> bool:
    text = (row.get("title", "") + " " + row.get("tags", "")).lower()
    return any(term.lower() in text for term in _SLG_TERMS)


@st.cache_data(ttl=300)
def get_trending_videos(top_k: int = 3) -> list[dict]:
    from src.core.csv_store import VIDEO_PLATFORMS

    all_videos = []
    for platform in ["bilibili", "youtube"]:
        category = "video_platforms" if platform in VIDEO_PLATFORMS else "community_platforms"
        video_dir = DATA_DIR / category / platform / "videos"
        if not video_dir.exists():
            continue
        for csv_file in video_dir.glob("*.csv"):
            try:
                with open(csv_file, encoding="utf-8-sig") as csv_f:
                    reader = csv.DictReader(csv_f)
                    for row in reader:
                        if "view_count" in row and row["view_count"]:
                            if not _is_slg_relevant(row):
                                continue
                            row["view_count"] = int(row["view_count"])
                            row["platform"] = platform
                            all_videos.append(row)
            except Exception:
                continue

    all_videos.sort(key=lambda item: item.get("view_count", 0), reverse=True)
    seen_ids = set()
    unique_videos = []
    for video in all_videos:
        if video["video_id"] not in seen_ids:
            seen_ids.add(video["video_id"])
            unique_videos.append(video)
            if len(unique_videos) == top_k:
                break
    return unique_videos


def get_latest_report() -> Path | None:
    if not REPORTS_DIR.exists():
        return None
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    return reports[0] if reports else None


def get_report_paths(date_str: str) -> tuple[Path, Path]:
    return REPORTS_DIR / f"{date_str}_weekly_report.json", REPORTS_DIR / f"{date_str}_weekly_report.md"


def load_report_artifacts(date_str: str) -> dict | None:
    json_path, md_path = get_report_paths(date_str)
    if not (json_path.exists() and md_path.exists()):
        return None

    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    return {
        "payload": payload,
        "markdown": md_path.read_text(encoding="utf-8"),
    }


def get_keyword_library_last_saved_at() -> str:
    return format_file_mtime(KEYWORDS_FILE)


def load_keyword_library() -> tuple[dict, list[str], dict]:
    kw_data = load_yaml(KEYWORDS_FILE)
    seed_keywords = kw_data.setdefault("seed_keywords", {})
    expansion = kw_data.setdefault(
        "expansion",
        {"enabled": True, "llm_provider": "deepseek", "max_expanded_keywords": 50},
    )

    merged_keywords = []
    seen = set()
    for group_name in ("games", "categories"):
        for raw_keyword in seed_keywords.get(group_name, []) or []:
            keyword = str(raw_keyword).strip()
            if keyword and keyword not in seen:
                merged_keywords.append(keyword)
                seen.add(keyword)

    return kw_data, merged_keywords, expansion


def normalize_keyword_rows(editor_df: pd.DataFrame, column_name: str = "关键词") -> list[str]:
    if column_name not in editor_df.columns:
        return []

    normalized = []
    seen = set()
    for _, row in editor_df.dropna(how="all").iterrows():
        keyword = str(row.get(column_name, "")).strip()
        if keyword and keyword not in seen:
            normalized.append(keyword)
            seen.add(keyword)
    return normalized


def save_keyword_library(kw_data: dict, keywords: list[str], enabled: bool, provider: str, max_keywords: int) -> None:
    kw_data["seed_keywords"] = {"games": keywords, "categories": []}
    kw_data["expansion"] = {
        "enabled": enabled,
        "llm_provider": provider,
        "max_expanded_keywords": int(max_keywords),
    }

    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(kw_data, f, allow_unicode=True, sort_keys=False)


def get_crawl_file_snapshot(platform: str) -> dict[str, dict]:
    snapshot = {}
    if not DATA_DIR.exists():
        return snapshot

    for csv_file in DATA_DIR.rglob("*.csv"):
        try:
            is_platform_file = platform in csv_file.parts
            is_summary_file = "summary" in csv_file.parts and csv_file.name.endswith("_summary.csv")
            if not (is_platform_file or is_summary_file):
                continue

            snapshot[str(csv_file)] = {
                "rows": count_csv_rows(csv_file),
                "mtime": csv_file.stat().st_mtime,
            }
        except Exception:
            continue

    return snapshot


def summarize_crawl_result(
    platform: str,
    platform_label: str,
    before_snapshot: dict[str, dict],
    after_snapshot: dict[str, dict],
    keyword_count: int,
    limit_val: int,
    started_at: datetime,
    return_code: int,
    stdout: str,
    stderr: str,
) -> dict:
    touched_files = []
    added_videos = 0
    added_comments = 0

    for path_str, after in after_snapshot.items():
        before = before_snapshot.get(path_str, {"rows": 0, "mtime": 0.0})
        row_delta = after["rows"] - before["rows"]
        touched = before["mtime"] == 0.0 or row_delta != 0 or after["mtime"] > before["mtime"]
        if not touched:
            continue

        path_obj = Path(path_str)
        try:
            rel_path = str(path_obj.relative_to(ROOT))
        except Exception:
            rel_path = path_str

        touched_files.append({"path": rel_path, "row_delta": row_delta})

        if platform in path_obj.parts and "videos" in path_obj.parts:
            added_videos += max(row_delta, 0)
        if platform in path_obj.parts and "comments" in path_obj.parts:
            added_comments += max(row_delta, 0)

    touched_files.sort(key=lambda item: item["path"])

    return {
        "platform": platform,
        "platform_label": platform_label,
        "status": "success" if return_code == 0 else "error",
        "duration_seconds": max((datetime.now() - started_at).total_seconds(), 0.1),
        "estimated_results": keyword_count * limit_val,
        "keyword_count": keyword_count,
        "limit_val": limit_val,
        "added_videos": added_videos,
        "added_comments": added_comments,
        "touched_files": touched_files,
        "stdout": stdout,
        "stderr": stderr,
    }


def list_loaded_csv_files() -> list[dict]:
    data_base_dir = DATA_DIR
    all_csv_files = list(data_base_dir.rglob("*.csv")) if data_base_dir.exists() else []
    results = []
    for file_path in sorted(all_csv_files, key=lambda path: path.name, reverse=True):
        rel_parts = file_path.relative_to(data_base_dir).parts
        file_size_kb = file_path.stat().st_size / 1024
        display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px;'><b>{file_path.name}</b></div>"
        if len(rel_parts) >= 4 and rel_parts[0] in ["video_platforms", "community_platforms"]:
            platform_name = rel_parts[1].capitalize()
            data_type = rel_parts[2].capitalize()
            badge_color = "#3b82f6" if "video" in data_type.lower() else "#8b5cf6" if "comment" in data_type.lower() else "#10b981"
            plat_tag = f"<span style='background:#f1f5f9; color:#475569; padding:2px 6px; border-radius:4px; margin-right:6px;'>{platform_name}</span>"
            type_tag = f"<span style='background:{badge_color}20; color:{badge_color}; padding:2px 6px; border-radius:4px; margin-right:8px;'>{data_type}</span>"
            display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px; white-space:nowrap;'>{plat_tag}{type_tag} <b>{file_path.name}</b></div>"
        elif len(rel_parts) == 3 and rel_parts[0] == "summary":
            display_html = (
                f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px; white-space:nowrap;'>"
                f"<span style='background:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; margin-right:6px;'>Summary</span>"
                f"<span style='background:#e0e7ff; color:#4338ca; padding:2px 6px; border-radius:4px; margin-right:8px;'>{rel_parts[1].capitalize()}</span> "
                f"<b>{file_path.name}</b></div>"
            )
        else:
            display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px;'><b>{'/'.join(rel_parts[:-1])}</b> / {file_path.name}</div>"

        results.append(
            {
                "path": file_path,
                "display_html": display_html,
                "size_kb": file_size_kb,
            }
        )
    return results


def delete_all_loaded_csv_files() -> None:
    for item in list_loaded_csv_files():
        try:
            os.remove(item["path"])
        except Exception:
            continue


def delete_loaded_csv_file(file_path: Path) -> None:
    os.remove(file_path)


def media_crawler_exists() -> bool:
    return (ROOT / "MediaCrawler").exists()


def load_profiles_dataframe() -> pd.DataFrame:
    profiles_path = DATA_DIR / "profiles" / "user_games"
    all_profiles = []
    if profiles_path.exists():
        for profile_file in profiles_path.glob("*_user_games.csv"):
            try:
                df = pd.read_csv(profile_file)
                if not df.empty:
                    df["source"] = profile_file.name
                    all_profiles.append(df)
            except Exception:
                continue

    if not all_profiles:
        return pd.DataFrame()

    df = pd.concat(all_profiles, ignore_index=True)
    return df.drop_duplicates(subset=["user_id"]).copy()


def load_targets_config() -> dict:
    targets_data = load_yaml(TARGETS_FILE)
    if "targets" not in targets_data:
        targets_data["targets"] = {}
    return targets_data


def save_targets_config(targets_data: dict) -> None:
    with open(TARGETS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(targets_data, f, allow_unicode=True, sort_keys=False)


def save_secrets_config(data: dict) -> None:
    from src.core.config import DEFAULT_SECRETS_FILE

    with open(DEFAULT_SECRETS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def format_stat_num(value) -> str:
    try:
        number = int(value)
        if number < 0:
            return "—"
        if number >= 100000000:
            return f"{number / 100000000:.1f}亿"
        if number >= 10000:
            return f"{number / 10000:.1f}万"
        return f"{number:,}"
    except Exception:
        return str(value) if value else "—"


def build_trending_rows_html(trending: list[dict]) -> str:
    rows_html_parts = []
    for index, video in enumerate(trending):
        platform = video["platform"]
        video_id = _html.escape(video["video_id"])
        title = _html.escape(video.get("title", ""))
        author = _html.escape(video.get("author", ""))
        url = _html.escape(video.get("url", "#"))
        pfav_url = _html.escape(PLATFORM_BRAND_ICONS.get(platform, ""))

        if platform == "bilibili":
            player_cell = (
                f"""<iframe src="//player.bilibili.com/player.html?isOutside=true&bvid={video_id}&p=1&autoplay=0&danmaku=0" """
                """scrolling="no" frameborder="no" allowfullscreen="true" """
                """style="width:160px;height:90px;display:block;border-radius:6px;border:none;"></iframe>"""
            )
        elif platform == "youtube":
            player_cell = (
                f"""<iframe src="https://www.youtube.com/embed/{video_id}" title="YouTube video player" frameborder="0" """
                """allow="accelerometer;clipboard-write;encrypted-media;gyroscope;picture-in-picture;web-share" """
                """referrerpolicy="strict-origin-when-cross-origin" allowfullscreen """
                """style="width:160px;height:90px;display:block;border-radius:6px;border:none;"></iframe>"""
            )
        else:
            player_cell = ""

        fav_val = format_stat_num(video.get("favorite_count", 0)) if platform == "bilibili" else "—"
        coin_val = format_stat_num(video.get("coin_count", 0)) if platform == "bilibili" else "—"
        share_val = format_stat_num(video.get("share_count", 0)) if platform == "bilibili" else "—"
        danmaku_val = format_stat_num(video.get("danmaku_count", 0)) if platform == "bilibili" else "—"

        raw_tags = str(video.get("tags", "") or "")
        tag_list = [tag.strip() for tag in raw_tags.split(",") if tag.strip()][:10]
        tags_html = ""
        for tag in tag_list:
            is_hit = any(term.lower() in tag.lower() or tag.lower() in term.lower() for term in _SLG_TERMS)
            css_class = "tag tag-hit" if is_hit else "tag"
            tags_html += f'<span class="{css_class}">{_html.escape(tag)}</span>'
        tags_block = f'<div class="tags">{tags_html}</div>' if tags_html else ""

        rows_html_parts.append(
            f"""
            <tr>
                <td class="num">{index + 1}</td>
                <td class="player-cell">{player_cell}</td>
                <td class="title-cell">
                    <a href="{url}" target="_blank">{title}</a>
                    <span class="author"><img src="{pfav_url}" class="pfav">{author}</span>
                    {tags_block}
                </td>
                <td class="stat">{format_stat_num(video.get('view_count', 0))}</td>
                <td class="stat">{format_stat_num(video.get('like_count', 0))}</td>
                <td class="stat">{format_stat_num(video.get('comment_count', 0))}</td>
                <td class="stat">{fav_val}</td>
                <td class="stat">{share_val}</td>
                <td class="stat">{coin_val}</td>
                <td class="stat">{danmaku_val}</td>
                <td class="stat muted">{video.get('publish_date', '')[:10]}</td>
            </tr>
            """
        )
    return "".join(rows_html_parts)
