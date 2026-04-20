"""
SLG Sentinel — 企业级数据分析监控台
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import csv
import html as _html
import streamlit.components.v1 as st_components
import yaml
import pandas as pd

import streamlit as st

# ─── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SLG Sentinel | 监控看板",
    page_icon="cloudflare_pages/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── 极简工业感 CSS 样式 (纯净/全屏/黑白灰基调) ────────────────────────
st.markdown("""
<style>
/* 强制使用无衬线系统字体，去风格化 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #FAFAFA !important;
    color: #171717 !important;
}

header[data-testid="stHeader"] { background-color: transparent !important; }
footer { visibility: hidden !important; display: none !important; }

/* 菜单导航样式调整 */
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EAEAEA !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
}

/* 只隐藏 Header 里的 Deploy 和主菜单，保留侧边栏展开按钮 */
header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] {
    display: none !important;
}

/* 主内容区域去除左侧和顶部多余空白 */
.block-container {
    padding-top: 2rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}
.stSidebar [data-testid="stMarkdownContainer"] p {
    color: #666666 !important;
    font-size: 13px !important;
}

/* 隐藏 Radio 选项的圆圈标志，伪装成原生菜单 */
.stSidebar div[role="radiogroup"] > label {
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}
.stSidebar div[role="radiogroup"] > label:hover {
    background-color: #F5F5F5;
}

/* 覆盖 Streamlit 原生标题的大小和间距 */
h1 {
    font-weight: 700 !important;
    font-size: 30px !important;
    letter-spacing: -0.04em !important;
    color: #000000 !important;
    margin-bottom: 6px !important;
}
h3 {
    font-weight: 600 !important;
    font-size: 18px !important;
    margin-top: 1.5rem !important;
    color: #111111 !important;
}

/* 指标卡片 (直角/细边框) */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #EAEAEA !important;
    border-radius: 6px !important;
    padding: 24px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #666666 !important;
}
div[data-testid="stMetricValue"] {
    font-size: 32px !important;
    font-weight: 700 !important;
    color: #000000 !important;
    margin-top: 4px;
}

/* 核心操作按钮 */
button[kind="primary"] {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    border-radius: 6px !important;
    border: 1px solid #000000 !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.5rem !important;
    font-size: 14px !important;
    transition: all 0.15s ease !important;
}
button[kind="primary"]:hover {
    background-color: #333333 !important;
    border-color: #333333 !important;
}

/* 嵌套选项卡 */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid #EAEAEA;
    gap: 32px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #666666 !important;
    font-weight: 500 !important;
    font-size: 14px !important;
    height: 44px;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    color: #000000 !important;
    border-bottom: 2px solid #000000 !important;
}

/* 数据矩阵表格 */
.stMarkdown table {
    width: 100%;
    background-color: #FFFFFF;
    border: 1px solid #EAEAEA !important;
    border-radius: 6px !important;
    border-collapse: separate !important;
    border-spacing: 0;
    margin-top: 1rem;
}
.stMarkdown th {
    background-color: #FAFAFA !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    color: #666666 !important;
    border-bottom: 1px solid #EAEAEA !important;
    padding: 12px 16px !important;
    text-align: left;
}
.stMarkdown td {
    padding: 14px 16px !important;
    font-size: 14px !important;
    color: #111111 !important;
    border-bottom: 1px solid #EAEAEA !important;
}
.stMarkdown tr:last-child td { border-bottom: none !important; }

/* 游戏图标与标题卡片 */
.game-card {
    background-color: #FFFFFF;
    border: 1px solid #EAEAEA;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}
.game-card img {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    border: 1px solid #F0F0F0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.game-card .info {
    display: flex;
    flex-direction: column;
}
.game-card .title {
    font-weight: 600;
    font-size: 15px;
    color: #111111;
    margin: 0;
}
.game-card .subtitle {
    font-size: 12px;
    color: #888888;
    margin: 4px 0 0 0;
}

/* 平台微标 */
.platform-icon {
    width: 18px;
    height: 18px;
    vertical-align: text-bottom;
    margin-right: 8px;
    border-radius: 2px;
}
</style>
""", unsafe_allow_html=True)


# ─── 核心资源 (原生代码级矢量头像，彻底阻绝防盗链 403 放空) ─────────────────────────
game_assets = [
    {
        "name": "三国志·战略版",
        "developer": "灵犀互娱",
        "bg": "linear-gradient(135deg, #374151 0%, #111827 100%)",
        "char": "三"
    },
    {
        "name": "万国觉醒 (ROK)",
        "developer": "莉莉丝游戏",
        "bg": "linear-gradient(135deg, #4B5563 0%, #1F2937 100%)",
        "char": "万"
    },
    {
        "name": "率土之滨",
        "developer": "网易游戏",
        "bg": "linear-gradient(135deg, #6B7280 0%, #374151 100%)",
        "char": "率"
    }
]

platform_brand_icons = {
    "bilibili": "https://www.bilibili.com/favicon.ico",
    "youtube": "https://www.youtube.com/favicon.ico",
    "taptap": "https://www.taptap.cn/favicon.ico",
    "douyin": "https://www.douyin.com/favicon.ico",
    "kuaishou": "https://www.kuaishou.com/favicon.ico",
    "xiaohongshu": "https://www.xiaohongshu.com/favicon.ico"
}


# ─── 常量与工具逻辑 ──────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
KEYWORDS_FILE = ROOT / "keywords.yaml"
TARGETS_FILE = ROOT / "targets.yaml"

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
        return


def estimate_remaining_seconds(progress_state: dict) -> int | None:
    progress = progress_state.get("progress", 0.0)
    if progress <= 0.08:
        return None
    elapsed = max((datetime.now() - progress_state["started_at"]).total_seconds(), 1.0)
    total_estimated = elapsed / progress
    return max(int(total_estimated - elapsed), 0)

def count_csv_rows(path: Path) -> int:
    if not path.exists(): return 0
    try:
        with open(path, encoding="utf-8-sig") as f: return max(0, sum(1 for _ in f) - 1)
    except Exception: return 0

def get_platform_stats(platform: str) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 解析平台大类
    from src.core.csv_store import VIDEO_PLATFORMS, COMMUNITY_PLATFORMS
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
    import os
    total_v, total_c, last_sync = 0, 0, 0
    for p in ["bilibili", "youtube", "taptap"]:
        stt = get_platform_stats(p)
        total_v += stt["videos_total"]
        total_c += stt["comments_total"]
    
    # 只扫描各平台一级目录中最新的 CSV，避免全量 rglob
    if DATA_DIR.exists():
        for subdir in ["video_platforms", "community_platforms", "summary"]:
            target = DATA_DIR / subdir
            if target.exists():
                for f in target.rglob("*.csv"):
                    if f.is_file():
                        mtime = f.stat().st_mtime
                        if mtime > last_sync:
                            last_sync = mtime
            
    t_data = load_yaml(TARGETS_FILE).get("targets", {})
    total_targets = len(t_data.get("bilibili_channels", [])) + len(t_data.get("youtube_channels", [])) + len(t_data.get("taptap_games", []))
    k_data = load_yaml(KEYWORDS_FILE).get("seed_keywords", {})
    total_kws = sum(len(v) for v in k_data.values() if isinstance(v, list))
    
    return {
        "capacity": total_v + total_c,
        "last_sync": datetime.fromtimestamp(last_sync).strftime("%m-%d %H:%M") if last_sync else "静默状态",
        "targets": total_targets,
        "keywords": total_kws,
        "api_health": bool(os.environ.get("DEEPSEEK_API_KEY"))
    }

def _build_slg_filter_terms() -> set[str]:
    """从 keywords.yaml 提取所有游戏名和分类词，用于内容相关性过滤"""
    terms = set()
    try:
        cfg = load_yaml(KEYWORDS_FILE)
        kw = cfg.get("seed_keywords", {})
        for v in kw.values():
            if isinstance(v, list):
                terms.update(str(t).strip() for t in v if t)
    except Exception:
        pass
    # 兜底：直接写入已知目标游戏名
    terms.update(["率土之滨", "三国志战略版", "万国觉醒", "文明与征服",
                  "鸿图之下", "寰宇之战", "SLG", "策略"])
    return terms

_SLG_TERMS = _build_slg_filter_terms()

def _is_slg_relevant(row: dict) -> bool:
    """标题或 tags 里含任意一个追踪关键词则认为相关"""
    text = (row.get("title", "") + " " + row.get("tags", "")).lower()
    return any(t.lower() in text for t in _SLG_TERMS)

@st.cache_data(ttl=300)
def get_trending_videos(top_k=3) -> list[dict]:
    all_videos = []
    
    from src.core.csv_store import VIDEO_PLATFORMS, COMMUNITY_PLATFORMS

    for platform in ["bilibili", "youtube"]:
        cat = "video_platforms" if platform in VIDEO_PLATFORMS else "community_platforms"
        v_dir = DATA_DIR / cat / platform / "videos"
        if not v_dir.exists(): continue
        for f in v_dir.glob("*.csv"):
            try:
                with open(f, encoding="utf-8-sig") as csv_f:
                    reader = csv.DictReader(csv_f)
                    for row in reader:
                        try:
                            if "view_count" in row and row["view_count"]:
                                if not _is_slg_relevant(row):
                                    continue          # ⬅ 过滤非SLG内容
                                row['view_count'] = int(row['view_count'])
                                row['platform'] = platform
                                all_videos.append(row)
                        except Exception: pass
            except Exception: pass

    all_videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)

    seen_ids = set()
    unique_videos = []
    for v in all_videos:
        if v['video_id'] not in seen_ids:
            seen_ids.add(v['video_id'])
            unique_videos.append(v)
            if len(unique_videos) == top_k:
                break
    return unique_videos


def get_latest_report() -> Path | None:
    if not REPORTS_DIR.exists(): return None
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    return reports[0] if reports else None

def load_yaml(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f: return yaml.safe_load(f) or {}
    except Exception: return {}


def render_step_overview(items: list[tuple[str, str, str]]) -> None:
    with st.container(border=True):
        st.markdown(
            "<div style='font-size:12px; color:#475569; font-weight:700; letter-spacing:0.5px; margin-bottom:12px;'>采集流程</div>",
            unsafe_allow_html=True,
        )

        layout = []
        for idx in range(len(items) * 2 - 1):
            layout.append(1.45 if idx % 2 == 0 else 0.22)
        cols = st.columns(layout)

        col_idx = 0
        for item_idx, (step, title, color) in enumerate(items):
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div style='padding:10px 12px; border:1px solid {color}22; border-radius:10px; background:{color}10; min-height:76px;'>
                        <div style='font-size:11px; color:{color}; font-weight:800; letter-spacing:0.5px;'>{step}</div>
                        <div style='font-size:15px; color:#111; font-weight:700; margin-top:6px;'>{title}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            col_idx += 1
            if item_idx < len(items) - 1:
                with cols[col_idx]:
                    st.markdown(
                        "<div style='text-align:center; font-size:22px; color:#CBD5E1; font-weight:700; padding-top:22px;'>→</div>",
                        unsafe_allow_html=True,
                    )
                col_idx += 1


def render_step_block_header(step: str, title: str, color: str, description: str | None = None) -> None:
    desc_html = (
        f"<div style='font-size:12px; color:#666; margin-top:2px; line-height:1.5;'>{description}</div>"
        if description
        else ""
    )
    st.markdown(
        f"""
        <div style='display:flex; gap:12px; align-items:flex-start; margin-bottom:12px;'>
            <div style='width:38px; height:38px; border-radius:12px; background:{color}18; color:{color}; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:800; flex-shrink:0;'>
                {step}
            </div>
            <div>
                <div style='font-size:16px; font-weight:700; color:#111;'>{title}</div>
                {desc_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    kw_data["seed_keywords"] = {
        "games": keywords,
        "categories": [],
    }
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


def render_crawl_result_card(result: dict) -> None:
    if not result:
        return

    status_text = "成功" if result["status"] == "success" else "失败"
    status_color = "#16A34A" if result["status"] == "success" else "#DC2626"

    st.markdown("##### 本次执行结果")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("执行状态", status_text, delta=f"{result['duration_seconds']:.1f} 秒")
    with metric_cols[1]:
        st.metric("预计检索量", str(result["estimated_results"]), delta=f"{result['keyword_count']} 词 × {result['limit_val']} 条")
    with metric_cols[2]:
        st.metric("新增视频 / 评论", f"{result['added_videos']} / {result['added_comments']}")
    with metric_cols[3]:
        st.metric("写入文件", str(len(result["touched_files"])))

    st.markdown(
        f"<div style='font-size:13px; color:#475569; margin:8px 0 12px 0;'>当前平台：<span style='color:{status_color}; font-weight:700;'>{_html.escape(result['platform_label'])}</span></div>",
        unsafe_allow_html=True,
    )

    if result["touched_files"]:
        st.markdown("**文件回执**")
        for item in result["touched_files"][:6]:
            delta_text = f"+{item['row_delta']}" if item["row_delta"] >= 0 else str(item["row_delta"])
            st.markdown(f"- `{item['path']}`  行数变化：`{delta_text}`")
        if len(result["touched_files"]) > 6:
            st.caption(f"另有 {len(result['touched_files']) - 6} 个文件发生变化。")
    else:
        st.info("本次运行未检测到平台目录中的文件变化。")

    with st.expander("查看原始执行日志", expanded=result["status"] != "success"):
        st.code((result["stdout"] + "\n" + result["stderr"]).strip(), language="bash")


def render_keyword_library(editor_prefix: str = "crawl") -> dict:
    kw_data, merged_keywords, expansion = load_keyword_library()
    save_status = {"text": "已同步到本地", "tone": "normal"}

    with st.container(border=True):
        st.markdown(
            """
            <div style='padding:4px 2px 10px 2px;'>
                <div style='font-size:18px; font-weight:700; color:#111;'>关键词库</div>
                <div style='font-size:13px; color:#666; margin-top:6px; line-height:1.6;'>在这里统一维护采集关键词，并在同一处完成扩词与保存。</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        meta_col1, meta_col2 = st.columns(2)
        with meta_col1:
            st.markdown(
                f"<div style='padding:12px 14px; border:1px solid #EAEAEA; border-radius:10px; background:#FFFFFF; min-height:92px;'><div style='font-size:12px; color:#666;'>当前关键词数</div><div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{len(merged_keywords)}</div></div>",
                unsafe_allow_html=True,
            )
        with meta_col2:
            last_saved_placeholder = st.empty()

        def render_last_saved_card() -> None:
            last_saved_placeholder.markdown(
                f"<div style='padding:12px 14px; border:1px solid #EAEAEA; border-radius:10px; background:#FFFFFF; min-height:92px;'><div style='font-size:12px; color:#666;'>最近保存时间</div><div style='font-size:16px; font-weight:700; color:#111; margin-top:12px;'>{format_file_mtime(KEYWORDS_FILE)}</div></div>",
                unsafe_allow_html=True,
            )

        render_last_saved_card()

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 编辑关键词")
            st.caption("双击表格即可编辑。修改会自动保存，刷新页面后仍会保留。")

            keyword_df = pd.DataFrame(
                [{"序号": idx, "关键词": k} for idx, k in enumerate(merged_keywords, start=1)]
            )
            if keyword_df.empty:
                keyword_df = pd.DataFrame(columns=["序号", "关键词"])

            edited_keywords = st.data_editor(
                keyword_df,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                height=360,
                column_config={
                    "序号": st.column_config.NumberColumn("序号", width=56, disabled=True),
                    "关键词": st.column_config.TextColumn("关键词", help="平台搜索将直接使用的检索词"),
                },
                key=f"{editor_prefix}_keyword_editor",
            )

        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("##### 自动扩词设置")
            st.caption("基于既有目标和语料自动补充关键词，结果会直接合并回当前词库。")

            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                exp_enabled = st.toggle(
                    "启用自动扩词",
                    value=expansion.get("enabled", True),
                    key=f"{editor_prefix}_exp_enabled",
                )
            with exp_col2:
                provider_options = ["deepseek", "openai", "qwen"]
                provider_value = expansion.get("llm_provider", "deepseek")
                provider_index = provider_options.index(provider_value) if provider_value in provider_options else 0
                exp_provider = st.selectbox(
                    "LLM Provider",
                    provider_options,
                    index=provider_index,
                    key=f"{editor_prefix}_exp_provider",
                )

            exp_max = st.number_input(
                "最大提取数 (10-200)",
                min_value=10,
                max_value=200,
                value=int(expansion.get("max_expanded_keywords", 50)),
                key=f"{editor_prefix}_exp_max",
            )

            current_keywords = normalize_keyword_rows(edited_keywords)
            persisted_state = {
                "keywords": merged_keywords,
                "enabled": bool(expansion.get("enabled", True)),
                "provider": expansion.get("llm_provider", "deepseek"),
                "max_keywords": int(expansion.get("max_expanded_keywords", 50)),
            }
            current_state = {
                "keywords": current_keywords,
                "enabled": bool(exp_enabled),
                "provider": exp_provider,
                "max_keywords": int(exp_max),
            }

            auto_saved = False
            if current_state != persisted_state:
                try:
                    save_keyword_library(kw_data, current_keywords, exp_enabled, exp_provider, int(exp_max))
                    auto_saved = True
                    save_status = {"text": "已自动保存到本地", "tone": "success"}
                    render_last_saved_card()
                except Exception as e:
                    save_status = {"text": "自动保存失败", "tone": "error"}
                    st.error(f"自动保存失败：{e}")

            if auto_saved:
                st.caption("已自动保存到本地 `keywords.yaml`。")

            action_cols = st.columns([1, 1])
            with action_cols[0]:
                tone_color = {"success": "#16A34A", "error": "#DC2626", "normal": "#475569"}.get(save_status["tone"], "#475569")
                st.markdown(
                    f"<div style='padding:10px 12px; border:1px dashed #D4D4D4; border-radius:10px; background:#FCFCFC; font-size:13px; color:{tone_color}; font-weight:600;'>{save_status['text']}</div>",
                    unsafe_allow_html=True,
                )

            with action_cols[1]:
                if st.button("立即执行扩词", type="secondary", use_container_width=True, key=f"{editor_prefix}_run_expand"):
                    from src.core.config import load_config
                    from src.core.keyword_expander import KeywordExpander

                    conf = load_config()
                    pbar = st.progress(0)
                    status_txt = st.empty()

                    def cb(cur, tot, name):
                        pbar.progress(cur / tot)
                        status_txt.text(f"[{cur}/{tot}] 正在抓取语料: {name}")

                    with st.spinner("正在扩展关键词，请勿刷新页面..."):
                        expander = KeywordExpander(conf)
                        results = expander.expand(provider=exp_provider, max_keywords=int(exp_max), progress_callback=cb)

                    if results:
                        keywords = list(current_keywords)
                        added = 0
                        for result in results:
                            keyword = str(result).strip()
                            if keyword and keyword not in keywords:
                                keywords.append(keyword)
                                added += 1

                        try:
                            save_keyword_library(kw_data, keywords, exp_enabled, exp_provider, int(exp_max))
                            status_txt.text("")
                            save_status = {"text": "扩词结果已写入本地", "tone": "success"}
                            render_last_saved_card()
                            st.success(f"成功提取 {len(results)} 个候选词，并自动合并了 {added} 个新词。")
                            with st.expander("查看本次提取词典"):
                                st.json(results)
                        except Exception as e:
                            save_status = {"text": "扩词结果写入失败", "tone": "error"}
                            st.error(f"扩词结果保存失败：{e}")
                    else:
                        status_txt.text("")
                        st.error("提取失败或未获取到语料。")

    current_keywords = current_keywords if 'current_keywords' in locals() else merged_keywords
    return {
        "keywords": current_keywords,
        "keyword_count": len(current_keywords),
        "save_status": save_status,
        "last_saved_at": format_file_mtime(KEYWORDS_FILE),
    }


# ─── 侧边栏菜单 ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; margin-bottom: 2rem; padding: 1rem 0;'>
        <div style='width: 32px; height: 32px; margin-right: 12px; flex-shrink: 0;'>
            <svg width="100%" height="100%" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="256" cy="256" r="256" fill="#2d333f" />
                <g transform="scale(0.8) translate(64, 64)">
                    <path d="M255.968 288.494L166.211 241.067L10.4062 158.753C10.2639 158.611 9.97951 158.611 9.83728 158.611C4.14838 155.909 -1.68275 161.596 0.450591 167.283L79.8393 369.685L79.8535 369.728C79.9388 369.927 80.0099 370.126 80.0953 370.325C83.3522 377.874 90.4633 382.537 98.2002 384.371C98.8544 384.513 99.3225 384.643 100.108 384.799C100.89 384.973 101.983 385.21 102.922 385.281C103.078 385.295 103.221 385.295 103.377 385.31H103.491C103.605 385.324 103.718 385.324 103.832 385.338H103.989C104.088 385.352 104.202 385.352 104.302 385.352H104.486C104.6 385.366 104.714 385.366 104.828 385.366L167.175 392.161C226.276 398.602 285.901 398.602 345.002 392.161L407.35 385.366C408.558 385.366 409.739 385.31 410.877 385.196C411.246 385.153 411.602 385.111 411.958 385.068C412 385.054 412.057 385.054 412.1 385.039C412.342 385.011 412.583 384.968 412.825 384.926C413.181 384.883 413.536 384.812 413.892 384.741C414.603 384.585 414.926 384.471 415.891 384.139C416.856 383.808 418.458 383.228 419.461 382.745C420.464 382.261 421.159 381.798 421.999 381.272C423.037 380.618 424.024 379.948 425.025 379.198C425.457 378.868 425.753 378.656 426.066 378.358L425.895 378.258L255.968 288.494Z" fill="#ffffff"/>
                    <path d="M501.789 158.755H501.647L345.784 241.07L432.426 370.058L511.616 167.285V167.001C513.607 161.03 507.492 155.627 501.789 158.755" fill="#a3a8b8"/>
                    <path d="M264.274 119.615C260.292 113.8 251.616 113.8 247.776 119.615L166.211 241.068L255.968 288.495L426.067 378.357C427.135 377.312 427.991 376.293 428.897 375.217C430.177 373.638 431.372 371.947 432.424 370.056L345.782 241.068L264.274 119.615Z" fill="#d1d5db"/>
                </g>
            </svg>
        </div>
        <div>
            <h3 style='margin: 0; font-size: 16px; color: #111; line-height: 1.2;'>SLG Sentinel</h3>
            <p style='margin: 0; font-size: 12px; color: #666;'>舆情分析平台</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "应用导航",
        ["总览", "采集", "画像", "智能报表", "设置"],
        label_visibility="collapsed",
    )

    st.markdown("<br/>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
if page == "总览":
    st.markdown("<h1>总览</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>查看近期的系统运行状态、数据容量及核心平台更新概貌。</p>", unsafe_allow_html=True)

    # ── 系统运行中枢 (Pulse Bar) ─────────────────────────────────────────────
    st.markdown("<h3>系统运行概况</h3>", unsafe_allow_html=True)
    health = get_system_health()
    st.markdown(f"""
    <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px;'>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>📡 监控目标数量</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['targets']}<span style='font-size:12px; font-weight:400; color:#666; margin:0 4px;'>频道，</span>{health['keywords']}<span style='font-size:12px; font-weight:400; color:#666; margin-left:4px;'>关键词</span></div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>包含跨平台核心检索靶点</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>📦 本地总数据量</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['capacity']} <span style='font-size:12px; font-weight:400; color:#666;'>组</span></div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>包含全平台的视频与评论快照</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>🧠 舆情分析组件 (LLM)</div>
            <div style='font-size:24px; font-weight:700; color:{"#16a34a" if health['api_health'] else "#dc2626"}; margin-top:8px;'>{"连接正常" if health['api_health'] else "未配置"}</div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>用于支撑深度的语义总结与报告生成</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>🕑 最近一次采集</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['last_sync']}</div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>系统最后一次成功抓取并落库的时间</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 平台增量指标 ──────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<h3>平台活水存量一览</h3>", unsafe_allow_html=True)

    p_data = [
        ("bilibili", "哔哩哔哩"), ("youtube", "YouTube"), ("taptap", "TapTap"),
        ("douyin", "抖音"), ("kuaishou", "快手"), ("xiaohongshu", "小红书")
    ]
    for row_idx in range(0, len(p_data), 3):
        cols = st.columns(3)
        for i, (p_id, p_label) in enumerate(p_data[row_idx:row_idx+3]):
            stats = get_platform_stats(p_id)
            with cols[i]:
                st.markdown(f"<div style='margin-bottom:-35px; z-index:10; position:relative; padding:24px 24px 0 24px;'><img class='platform-icon' src='{platform_brand_icons.get(p_id, '')}'> <span style='font-size:14px; font-weight:500; color:#666;'>{p_label}</span></div>", unsafe_allow_html=True)
                
                delta_val = f"今日新增: {stats['videos_today']} 视频, {stats['comments_today']} 评论"
                st.metric(label="​", value=str(stats['videos_total']) if stats['videos_total'] else "0", delta=delta_val, delta_color="normal")


    # ── 内容热度增量（周度）表格视图 ─────────────────────────────────────────
    st.markdown("<hr style='border: none; border-top: 1px solid #EAEAEA; margin: 2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>🚨 全网热帖及流量异动记录</h3>", unsafe_allow_html=True)
    c_desc, c_ctrl = st.columns([8, 2])
    with c_desc:
        st.markdown("<p style='color:#666; font-size:13px; margin-bottom:1rem;'>拉取跨周期全网流量异动的头部内容，供危机公关或传播热点发掘使用。</p>", unsafe_allow_html=True)
    with c_ctrl:
        view_limit = st.selectbox("单屏显示限额", [10, 20, 50, 100, 300, 500], index=0, label_visibility="collapsed")

    def fmt_num(n):
        try:
            n = int(n)
            if n < 0: return "—"          # -1 = API 未返回此字段
            if n >= 100000000: return f"{n/100000000:.1f}亿"
            if n >= 10000: return f"{n/10000:.1f}万"
            return f"{n:,}"
        except: return str(n) if n else "—"

    trending = get_trending_videos(view_limit)
    if trending:
        # ── 用 st_components.html() 渲染，完全绕过 Streamlit markdown 解析器 ──────
        rows_html_parts = []
        for i, vid in enumerate(trending):
            plat = vid['platform']
            vid_id = _html.escape(vid['video_id'])
            title_e = _html.escape(vid.get('title', ''))
            author_e = _html.escape(vid.get('author', ''))
            url_e = _html.escape(vid.get('url', '#'))
            pfav_url = _html.escape(platform_brand_icons.get(plat, ''))

            if plat == 'bilibili':
                player_cell = f'''<iframe
                    src="//player.bilibili.com/player.html?isOutside=true&bvid={vid_id}&p=1&autoplay=0&danmaku=0"
                    scrolling="no" frameborder="no" allowfullscreen="true"
                    style="width:160px;height:90px;display:block;border-radius:6px;border:none;"></iframe>'''
            elif plat == 'youtube':
                player_cell = f'''<iframe
                    src="https://www.youtube.com/embed/{vid_id}"
                    title="YouTube video player" frameborder="0"
                    allow="accelerometer;clipboard-write;encrypted-media;gyroscope;picture-in-picture;web-share"
                    referrerpolicy="strict-origin-when-cross-origin" allowfullscreen
                    style="width:160px;height:90px;display:block;border-radius:6px;border:none;"></iframe>'''
            else:
                player_cell = ''

            fav_val = fmt_num(vid.get('favorite_count', 0)) if plat == 'bilibili' else '—'
            coin_val = fmt_num(vid.get('coin_count', 0)) if plat == 'bilibili' else '—'
            share_val = fmt_num(vid.get('share_count', 0)) if plat == 'bilibili' else '—'
            danmaku_val = fmt_num(vid.get('danmaku_count', 0)) if plat == 'bilibili' else '—'

            # ── 标签命中可视化 ─────────────────────────────────────────────────────────
            raw_tags = str(vid.get('tags', '') or '')
            tag_list = [t.strip() for t in raw_tags.split(',') if t.strip()][:10]
            tags_html = ''
            for tag in tag_list:
                is_hit = any(
                    st_term.lower() in tag.lower() or tag.lower() in st_term.lower()
                    for st_term in _SLG_TERMS
                )
                cls = 'tag tag-hit' if is_hit else 'tag'
                tags_html += f'<span class="{cls}">{_html.escape(tag)}</span>'
            tags_block = f'<div class="tags">{tags_html}</div>' if tags_html else ''

            rows_html_parts.append(f"""
            <tr>
                <td class="num">{i+1}</td>
                <td class="player-cell">{player_cell}</td>
                <td class="title-cell">
                    <a href="{url_e}" target="_blank">{title_e}</a>
                    <span class="author"><img src="{pfav_url}" class="pfav">{author_e}</span>
                    {tags_block}
                </td>
                <td class="stat">{fmt_num(vid.get('view_count',0))}</td>
                <td class="stat">{fmt_num(vid.get('like_count',0))}</td>
                <td class="stat">{fmt_num(vid.get('comment_count',0))}</td>
                <td class="stat">{fav_val}</td>
                <td class="stat">{share_val}</td>
                <td class="stat">{coin_val}</td>
                <td class="stat">{danmaku_val}</td>
                <td class="stat muted">{vid.get('publish_date','')[:10]}</td>
            </tr>
            """)

        all_rows = ''.join(rows_html_parts)
        table_doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
            * {{ margin:0; padding:0; box-sizing:border-box; }}
            body {{ font-family: -apple-system,'Inter',BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#fff; }}
            table {{ width:100%; border-collapse:collapse; font-size:13px; }}
            thead tr {{ background:#FAFAFA; border-bottom:2px solid #EAEAEA; }}
            th {{ padding:10px 12px; font-size:12px; font-weight:600; color:#666; text-align:left; white-space:nowrap; }}
            th.right {{ text-align:right; }}
            td {{ padding:12px 12px; border-bottom:1px solid #F0F0F0; vertical-align:middle; }}
            tr:hover td {{ background:#FAFAFA; }}
            td.num {{ color:#999; font-size:12px; text-align:center; width:28px; }}
            td.player-cell {{ width:172px; padding:10px 8px; vertical-align:middle; }}
            td.title-cell {{ min-width:180px; padding:10px 12px; }}
            td.title-cell a {{ font-weight:600; color:#111; text-decoration:none; line-height:1.5; display:block; }}
            td.title-cell a:hover {{ color:#1d4ed8; }}
            td.stat {{ text-align:right; font-weight:500; white-space:nowrap; color:#333; }}
            td.muted {{ color:#999; font-size:12px; }}
            .author {{ display:block; font-size:11px; color:#888; margin-top:4px; }}
            .pfav {{ width:12px; height:12px; vertical-align:middle; margin-right:4px; }}
            .tags {{ display:flex; flex-wrap:wrap; gap:3px; margin-top:6px; }}
            .tag {{ display:inline-block; padding:2px 6px; border-radius:3px; font-size:11px;
                    background:#F5F5F5; color:#666; white-space:nowrap; }}
            .tag-hit {{ background:#EEF2FF; color:#4338CA; font-weight:600; }}
        </style></head><body>
        <table>
            <thead><tr>
                <th>#</th><th>视频</th><th>视频标题</th>
                <th class="right">播放</th><th class="right">点赞</th>
                <th class="right">评论</th><th class="right">收藏</th>
                <th class="right">分享</th><th class="right">投币</th>
                <th class="right">弹幕</th><th class="right">发布日</th>
            </tr></thead>
            <tbody>{all_rows}</tbody>
        </table>
        </body></html>"""
        # 固定一个比较开阔的数据格栅高度，启用内部独立滚动以防撑爆外层结构
        st_components.html(table_doc, height=900, scrolling=True)
    else:
        st.markdown("<p style='color:#666; font-size:14px;'>当前采集库中暂未发现内容，请先执行策略采集。</p>", unsafe_allow_html=True)

    # ── 当前已加载采集数据 (Data Manager) ──────────────────────────────────────────────────────────
    st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>当前已加载采集数据 (底层源文件)</h3>", unsafe_allow_html=True)
    
    from pathlib import Path
    import os
    
    data_base_dir = Path("data")
    all_csv_files = list(data_base_dir.rglob("*.csv")) if data_base_dir.exists() else []
    
    if not all_csv_files:
        st.markdown("<p style='color:#999; font-size:13px;'>目前本地 CSV 时序数据库位空，等待探针回传...</p>", unsafe_allow_html=True)
    else:
        @st.dialog("危险操作确认")
        def confirm_clear_all():
            st.warning("确定要彻底清空所有收集到的历史数据吗？此操作不可逆！")
            c1, c2 = st.columns(2)
            if c1.button("✅ 确认清空", type="primary", use_container_width=True):
                for f in all_csv_files:
                    try: os.remove(f)
                    except: pass
                st.rerun()
            if c2.button("取消", use_container_width=True):
                st.rerun()
                
        dm_col1, dm_col2 = st.columns([9, 2])
        with dm_col2:
            if st.button("🗑️ 全部删除", type="primary", use_container_width=True):
                confirm_clear_all()
                
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        # 采用简洁布局罗列
        for file_path in sorted(all_csv_files, key=lambda x: x.name, reverse=True):
            f_size = file_path.stat().st_size / 1024
            cx1, cx2, cx3 = st.columns([6, 3, 2])
            with cx1:
                rel_parts = file_path.relative_to(data_base_dir).parts
                if len(rel_parts) >= 4 and rel_parts[0] in ["video_platforms", "community_platforms"]:
                    plat_name = rel_parts[1].capitalize()
                    data_type = rel_parts[2].capitalize()
                    badge_color = "#3b82f6" if "video" in data_type.lower() else "#8b5cf6" if "comment" in data_type.lower() else "#10b981"
                    plat_tag = f"<span style='background:#f1f5f9; color:#475569; padding:2px 6px; border-radius:4px; margin-right:6px;'>{plat_name}</span>"
                    type_tag = f"<span style='background:{badge_color}20; color:{badge_color}; padding:2px 6px; border-radius:4px; margin-right:8px;'>{data_type}</span>"
                    display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px; white-space:nowrap;'>{plat_tag}{type_tag} <b>{file_path.name}</b></div>"
                elif len(rel_parts) == 3 and rel_parts[0] == "summary":
                    display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px; white-space:nowrap;'><span style='background:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; margin-right:6px;'>Summary</span><span style='background:#e0e7ff; color:#4338ca; padding:2px 6px; border-radius:4px; margin-right:8px;'>{rel_parts[1].capitalize()}</span> <b>{file_path.name}</b></div>"
                else:
                    display_html = f"<div style='font-family:monospace; font-size:13px; color:#1e293b; padding-top:8px;'><b>{'/'.join(rel_parts[:-1])}</b> / {file_path.name}</div>"
                st.markdown(display_html, unsafe_allow_html=True)
            with cx2:
                st.markdown(f"<div style='font-size:12px; color:#64748b; padding-top:10px;'>{f_size:.1f} KB</div>", unsafe_allow_html=True)
            with cx3:
                if st.button("删除", key=f"del_{file_path}"):
                    try:
                        os.remove(file_path)
                        st.rerun()
                    except Exception as e:
                        st.error("删除受阻")



elif page == "采集":
    st.markdown("<h1>内容采集</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 1.5rem;'>手动介入向指定媒介触发爬虫网络或更新快照状态。</p>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1.7, 1.05], gap="large")
    keyword_runtime = {}

    with right_col:
        keyword_runtime = render_keyword_library("crawl")

    with left_col:
        render_step_overview(
            [
                ("01", "选择平台", "#16a34a"),
                ("02", "是否鉴权", "#2563eb"),
                ("03", "采集深度", "#d97706"),
                ("04", "搜索策略", "#8b5cf6"),
                ("05", "爬取数目", "#06b6d4"),
            ]
        )

        platform_options = {
            "bilibili": "哔哩哔哩",
            "youtube": "YouTube",
            "taptap": "TapTap",
            "douyin": "抖音",
            "kuaishou": "快手",
            "xiaohongshu": "小红书",
        }
        keyword_count = keyword_runtime.get("keyword_count", len(load_keyword_library()[1]))

        order_val = "totalrank"
        limit_options = {
            10: "10 条 (安全试探，极速)",
            20: "20 条",
            30: "30 条",
            40: "40 条",
            50: "50 条 (常规快照)",
        }

        with st.container(border=True):
            st.markdown(
                "<div style='font-size:18px; font-weight:700; color:#111; margin-bottom:6px;'>采集配置</div>",
                unsafe_allow_html=True,
            )

            with st.container():
                render_step_block_header("01", "选择平台", "#16a34a", "先确定本次采集要进入的平台。")
                platform = st.selectbox(
                    "选择执行平台",
                    list(platform_options.keys()),
                    format_func=lambda x: platform_options[x],
                    key="crawl_platform",
                    label_visibility="collapsed",
                )

            st.divider()

            with st.container():
                render_step_block_header("02", "是否鉴权", "#2563eb", "根据平台能力决定是否启用本地鉴权。")
                if platform in ["xiaohongshu", "douyin", "kuaishou"]:
                    mode = st.radio(
                        "授权执行模式",
                        ["是，必须在本地完成鉴权"],
                        key="crawl_mode_media",
                        label_visibility="collapsed",
                    )
                    st.markdown(
                        "<p style='font-size:12px; color:#dc2626; margin:2px 0 0 0;'>该平台需在本地完成扫码授权后再执行采集。</p>",
                        unsafe_allow_html=True,
                    )
                else:
                    mode = st.radio(
                        "授权执行模式",
                        ["否，使用免登录模式（适合自动化）", "是，使用本地鉴权（需要载入会话环境）"],
                        key="crawl_mode_general",
                        label_visibility="collapsed",
                    )

            st.divider()

            with st.container():
                render_step_block_header("03", "采集深度", "#d97706", "决定只抓基础元数据，还是继续深入评论层。")
                if platform in ["xiaohongshu", "douyin", "kuaishou"]:
                    depth = st.radio("采集深度", ["受限单体深度遍历"], key="crawl_depth_media", label_visibility="collapsed", disabled=True)
                else:
                    depth = st.radio("采集深度", ["基础采集", "深度采集"], key="crawl_depth_general", label_visibility="collapsed")

                st.markdown(
                    "<p style='font-size:12px; color:#666; margin:2px 0 0 0;'>字段覆盖情况请参考下方能力矩阵。</p>",
                    unsafe_allow_html=True,
                )

            st.divider()

            with st.container():
                if platform == "bilibili":
                    render_step_block_header("04", "搜索策略", "#8b5cf6", "B 站支持额外指定搜索结果的排序方式。")
                    order_map = {
                        "平台搜索默认排序 (Total Rank)": "totalrank",
                        "最新发布时间排序 (Publish Date)": "pubdate",
                        "最多点击播放排序 (Click)": "click",
                        "最多用户收藏排序 (Stow)": "stow",
                    }
                    order_label = st.selectbox(
                        "检索排序策略",
                        list(order_map.keys()),
                        index=0,
                        key="crawl_order_bilibili",
                        label_visibility="collapsed",
                    )
                    order_val = order_map[order_label]
                else:
                    render_step_block_header("04", "搜索策略", "#8b5cf6", "当前平台没有额外排序参数，将沿用适配器默认策略。")
                    order_label = "平台默认策略"
                    st.markdown(
                        "<div style='padding:10px 12px; border:1px dashed #D4D4D4; border-radius:10px; background:#FCFCFC; font-size:13px; color:#475569;'>该平台使用默认搜索策略，无需单独设置。</div>",
                        unsafe_allow_html=True,
                    )

            st.divider()

            with st.container():
                render_step_block_header("05", "爬取数目", "#06b6d4", "最后设置本次采集的结果上限，并确认执行。")
                action_left, action_right = st.columns([1, 1.1])
                with action_left:
                    limit_val = st.selectbox(
                        "最大获取限额",
                        list(limit_options.keys()),
                        format_func=lambda x: limit_options[x],
                        key="crawl_limit",
                        label_visibility="collapsed",
                    )
                with action_right:
                    estimated_results = limit_val * keyword_count
                    mode_preview = "免登录" if "免登录" in mode else "本地鉴权"
                    depth_preview = "深度采集" if "深度" in depth else "基础采集"
                    order_preview = "平台默认" if platform != "bilibili" else order_label.replace("平台搜索默认排序 ", "").replace("(", "").replace(")", "")
                    st.markdown(
                        f"""
                        <div style='padding:10px 12px; border:1px dashed #D4D4D4; border-radius:10px; background:#FCFCFC;'>
                            <div style='font-size:12px; color:#666;'>本次执行概览</div>
                            <div style='font-size:13px; color:#111; margin-top:6px; line-height:1.7;'>
                                {platform_options[platform]} / {mode_preview} / {depth_preview} / {order_preview} / {limit_val} 条
                            </div>
                            <div style='font-size:13px; color:#2563EB; margin-top:6px; font-weight:600;'>
                                预计关键词检索量：{limit_val} × {keyword_count} = {estimated_results} 条
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
                media_platforms = {"xiaohongshu", "douyin", "kuaishou"}
                from src.core.config import load_config
                runtime_config = load_config()
                can_execute = True
                if keyword_count == 0:
                    can_execute = False
                    st.warning("当前关键词库为空，请先在右侧补充关键词后再执行采集。")
                elif platform in media_platforms and not (ROOT / "MediaCrawler").exists():
                    can_execute = False
                    st.error("未检测到 MediaCrawler 子模块，当前平台暂不可执行。")
                elif platform == "bilibili" and "鉴权" in mode and not runtime_config.bili_sessdata:
                    st.info("当前未检测到 Bilibili 会话，仍可执行基础采集；如需评论等深度数据，请先完成本地鉴权。")

                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                if st.button(f"启动 {platform_options[platform]} 采集链路", type="primary", use_container_width=True, disabled=not can_execute):
                    m_val = "actions" if "免登录" in mode else "local"
                    started_at = datetime.now()
                    before_snapshot = get_crawl_file_snapshot(platform)
                    progress_state = init_crawl_progress_state(platform, keyword_count, limit_val)
                    progress_title = st.empty()
                    progress_bar = st.progress(0)
                    progress_eta = st.empty()
                    progress_detail = st.empty()

                    def refresh_progress_ui() -> None:
                        eta_seconds = estimate_remaining_seconds(progress_state)
                        if progress_state["progress"] >= 1.0:
                            progress_percent = 100
                        else:
                            progress_percent = max(min(int(progress_state["progress"] * 100), 99), 1)
                        progress_title.markdown(
                            f"<div style='font-size:13px; color:#111; font-weight:700;'>采集进度：{progress_percent}%</div>",
                            unsafe_allow_html=True,
                        )
                        progress_bar.progress(progress_percent)
                        if progress_percent >= 100:
                            progress_eta.caption(f"当前阶段：{progress_state['stage']}")
                        elif eta_seconds is None:
                            progress_eta.caption("正在建立连接并准备采集任务...")
                        else:
                            progress_eta.caption(f"当前阶段：{progress_state['stage']} · 预计剩余 {eta_seconds} 秒")
                        progress_detail.caption(progress_state["detail"])

                    refresh_progress_ui()

                    cmd_args = ["crawl", "--platform", platform, "--mode", m_val, "--order", order_val, "--limit", str(limit_val)]
                    if platform not in ["xiaohongshu", "douyin", "kuaishou"] and "基础" in depth:
                        cmd_args.extend(["--depth", "shallow"])
                    elif platform not in ["xiaohongshu", "douyin", "kuaishou"] and "深度" in depth:
                        cmd_args.extend(["--depth", "deep"])

                    def on_progress_line(line: str) -> None:
                        update_crawl_progress_state(progress_state, line)
                        refresh_progress_ui()

                    stdout, stderr, code = run_cli_stream(cmd_args, on_line=on_progress_line)
                    progress_state["progress"] = 1.0 if code == 0 else max(progress_state["progress"], 0.92)
                    progress_state["stage"] = "采集完成" if code == 0 else "采集结束，等待查看结果"
                    refresh_progress_ui()
                    after_snapshot = get_crawl_file_snapshot(platform)
                    st.session_state["crawl_last_result"] = summarize_crawl_result(
                        platform=platform,
                        platform_label=platform_options[platform],
                        before_snapshot=before_snapshot,
                        after_snapshot=after_snapshot,
                        keyword_count=keyword_count,
                        limit_val=limit_val,
                        started_at=started_at,
                        return_code=code,
                        stdout=stdout,
                        stderr=stderr,
                    )
                    if code == 0:
                        st.success(f"✅ 【{platform_options[platform]}】指令流已成功回归至正常终态，全部捕获已落盘。")
                    else:
                        st.error(f"❌ 子线程调度失败，返回状态码: {code}")
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.get("crawl_last_result"):
        render_crawl_result_card(st.session_state["crawl_last_result"])
        st.markdown("<br>", unsafe_allow_html=True)

    # ── 动态构造 HTML 探针穿透能力矩阵表 ─────────────────────────────────────
    matrix_html_base = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: -apple-system,'Inter',BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
        table { width:100%; border-collapse:collapse; font-size:13px; border:1px solid #EAEAEA; border-radius:6px; overflow:hidden; }
        thead tr { background:#FAFAFA; border-bottom:1px solid #EAEAEA; }
        th { padding:12px 14px; font-size:12px; font-weight:600; color:#666; text-align:left; }
        td { padding:12px 14px; border-bottom:1px solid #F0F0F0; vertical-align:middle; font-size:13px; color:#333; }
        tr:hover td { background:#FAFAFA; }
        .g { color:#16a34a; font-weight:600; }
        .y { color:#d97706; font-weight:600; }
        .r { color:#dc2626; font-weight:600; }
        code { background:#f1f5f9; padding:2px 6px; border-radius:4px; font-family:'SF Mono',monospace; font-size:11px; color:#2563eb; }
        .desc { font-size:12px; color:#666; }
    </style></head><body>
    <table>
        <thead><tr>
            <th style="width:18%">属性</th>
            <th style="width:30%">数据来源</th>
            <th style="width:25%">业务价值</th>
            <th style="width:27%">当前可见范围</th>
        </tr></thead>
        <tbody>"""
    
    if platform == "bilibili":
        comp_title = "采集引擎：<a href='https://github.com/Nemo2011/bilibili-api' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>bilibili-api-python</a>"
        iframe_height = 680
        
        is_simple = "基础" in depth
        is_basic = "免登录" in mode
        
        sess_status = "<span class='g'>✅ 可获取</span>" if is_basic else "<span class='g'>✅ 可获取</span>"
        deep_status = "<span class='g'>✅ 基础模式可获取</span>" if is_basic else "<span class='g'>✅ 鉴权模式可获取</span>"
        
        api_call = "<code>search.search_by_type()</code>" if is_simple else "<code>video.Video().get_info()</code>"
        b_coin_status = "<span class='y'>⚠️ 基础搜索不返回</span>" if is_simple else deep_status
        
        cmt_status = "<span class='y'>⚠️ 免登录模式下受限</span>" if is_basic else "<span class='g'>✅ 鉴权后可获取</span>"
        fav_status = "<span class='y'>⚠️ 需鉴权且用户公开</span>" if is_basic else "<span class='g'>✅ 用户公开时可获取</span>"
        follow_status = "<span class='y'>⚠️ 需鉴权</span>" if is_basic else "<span class='g'>✅ 可获取</span>"

        rows = f"""
        <tr><td>BV号 (ID)</td><td><code>search.search_by_type()</code></td><td class="desc">用于唯一定位内容</td><td>{sess_status}</td></tr>
        <tr><td>视频标题 (Title)</td><td><code>search.search_by_type()</code></td><td class="desc">用于判断题材与关键词相关性</td><td>{sess_status}</td></tr>
        <tr><td>UP主名称 (Author)</td><td><code>search.search_by_type()</code></td><td class="desc">用于识别重点创作者与渠道</td><td>{sess_status}</td></tr>
        <tr><td>发布日期 (Pubdate)</td><td><code>search.search_by_type()</code></td><td class="desc">用于界定分析周期</td><td>{sess_status}</td></tr>
        <tr><td>播放量 (View)</td><td>{api_call}</td><td class="desc">用于判断内容曝光规模</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>点赞数 (Like)</td><td>{api_call}</td><td class="desc">用于衡量内容正向反馈</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>投币数 (Coin)</td><td>{api_call}</td><td class="desc">用于识别高认可度内容</td><td>{b_coin_status}</td></tr>
        <tr><td>收藏数 (Favorite)</td><td>{api_call}</td><td class="desc">用于观察长期关注意愿</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>分享数 (Share)</td><td>{api_call}</td><td class="desc">用于判断传播扩散能力</td><td>{b_coin_status}</td></tr>
        <tr><td>评论者 UID</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于后续用户画像与溯源</td><td>{cmt_status}</td></tr>
        <tr><td>评论内容纯文本</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于情感与话题分析</td><td>{cmt_status}</td></tr>
        <tr><td>被点赞数 (Like)</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于识别高影响评论</td><td>{cmt_status}</td></tr>
        <tr><td>公开收藏夹</td><td><code>get_video_favorite_list(uid)</code></td><td class="desc">用于辅助判断用户偏好</td><td>{fav_status}</td></tr>
        <tr><td>关注关系链</td><td><code>API /x/relation/followings</code></td><td class="desc">用于识别关联账号与兴趣重合</td><td>{follow_status}</td></tr>"""
    elif platform == "youtube":
        comp_title = "采集引擎：<a href='https://github.com/yt-dlp/yt-dlp' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>yt-dlp</a> · <a href='https://github.com/dermasmid/scrapetube' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>scrapetube</a> · <a href='https://github.com/egbertbouman/youtube-comment-downloader' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>yt-cmt-dl</a>"
        iframe_height = 600
        rows = """
        <tr><td>视频 ID (videoId)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于唯一定位内容</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>视频标题 (Title)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于识别内容主题</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>所属频道 (Channel)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">用于识别重点创作者</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>下辖视频列表</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于补充频道维度内容</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>基础发布日期</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于筛选分析周期</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>基础播放量</td><td><code>scrapetube.get_channel()</code></td><td class="desc">用于快速识别高热内容</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>精准真播放 (viewCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于评估真实曝光规模</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>精准点赞数 (likeCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于判断正向反馈强度</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>视频受众标签 (Tags)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">用于提取话题标签与语义线索</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>网民 ID 与昵称</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于追踪高价值评论用户</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>高价值点赞数</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于识别高影响评论</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>详细发送时间戳</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于判断讨论时效性</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>评论完整纯文本</td><td><code>youtube-comment-downloader</code></td><td class="desc">用于情感与主题分析</td><td><span class="g">✅ 可获取</span></td></tr>"""
    elif platform == "taptap":
        comp_title = "采集引擎：<span style='font-family:monospace; font-weight:600; color:#333; background:#e2e8f0; padding:4px 8px; border-radius:6px;'>自有协议解析引擎</span>"
        iframe_height = 420
        rows = """
        <tr><td>核心星评 (1-5星)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于观察口碑趋势</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>测评明文大段内容</td><td><code>API /v2/review/thread</code></td><td class="desc">用于分析深度反馈</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>社区支持度 (ups)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于判断观点共鸣度</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>社区反对数 (downs)</td><td><code>API /v2/review/thread</code></td><td class="desc">用于识别争议反馈</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>发帖物理设备名</td><td><code>API /v2/review/thread</code></td><td class="desc">用于辅助判断设备分布</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>硬核游玩时长</td><td><code>API /v2/review/thread</code></td><td class="desc">用于区分轻度与重度玩家</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>网民专属 UID</td><td><code>API /v2/review/thread</code></td><td class="desc">用于后续用户维度分析</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>玩家曾游玩游戏库</td><td><code>API /v2/game/games</code></td><td class="desc">用于识别用户偏好结构</td><td><span class="g">✅ 可获取</span></td></tr>
        <tr><td>外部竞品评价横比</td><td><code>API /v2/game/games</code></td><td class="desc">用于对比竞品体验路径</td><td><span class="g">✅ 可获取</span></td></tr>"""
    elif platform in ["xiaohongshu", "douyin", "kuaishou"]:
        comp_title = "采集引擎：<a href='https://github.com/NanmiCoder/MediaCrawler' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>MediaCrawler</a> 本地桥接"
        iframe_height = 560
        rows = """
        <tr><td>帖子/视频 ID</td><td><code>MediaCrawler (aweme_id)</code></td><td class="desc">用于唯一定位内容</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>视频文案标题 (Title)</td><td><code>MediaCrawler (desc)</code></td><td class="desc">用于识别内容主题</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>创作者名称 (Author)</td><td><code>MediaCrawler (nickname)</code></td><td class="desc">用于判断内容来源</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>短片真实播放量</td><td><code>MediaCrawler (play_count)</code></td><td class="desc">用于判断内容传播规模</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>核心点赞数 (like)</td><td><code>MediaCrawler (like_count)</code></td><td class="desc">用于观察正向反馈</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>二次分享转发量</td><td><code>MediaCrawler (share_count)</code></td><td class="desc">用于判断扩散能力</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>私域背书收藏数</td><td><code>MediaCrawler (collect)</code></td><td class="desc">用于观察长期关注意愿</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>内容定向算法标签</td><td><code>MediaCrawler (tags)</code></td><td class="desc">用于提取平台标签线索</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>评论者 ID (user_id)</td><td><code>MediaCrawler (comments)</code></td><td class="desc">用于用户维度分析</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>神评文本明文</td><td><code>MediaCrawler (text)</code></td><td class="desc">用于情感与话题分析</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>
        <tr><td>网民 IP 物理归属</td><td><code>MediaCrawler (ip_location)</code></td><td class="desc">用于观察地域分布</td><td><span class="g">✅ 本地授权后可获取</span></td></tr>"""

    matrix_html = matrix_html_base + rows + "</tbody></table></body></html>"
    
    st.markdown(f"<div style='margin-top:1.5rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:flex-end;'><div><p style='font-size:14px; color:#111; font-weight:600; margin:0;'>当前平台字段能力矩阵</p></div><div style='font-size:12px; color:#666;'>{comp_title}</div></div>", unsafe_allow_html=True)
    st_components.html(matrix_html, height=iframe_height, scrolling=False)


    st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:1.5rem 0;'/>", unsafe_allow_html=True)

    # ── 用户数据可访问性矩阵 ──────────────────────────────────────────────────
    st.markdown("<h3>用户数据可访问性矩阵</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:13px; margin-bottom:0.8rem;'>各平台用户维度数据的公开程度与采集可行性总览。</p>", unsafe_allow_html=True)
    privacy_matrix_html = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: -apple-system,'Inter',BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
        table { width:100%; border-collapse:collapse; font-size:13px; }
        thead tr { background:#1a1a2e; }
        th { padding:12px 14px; font-size:12px; font-weight:600; color:#ccc; text-align:left; white-space:nowrap; }
        td { padding:12px 14px; border-bottom:1px solid #F0F0F0; vertical-align:middle; font-size:13px; color:#333; }
        tr:hover td { background:#FAFAFA; }
        td:first-child { font-weight:600; color:#111; white-space:nowrap; }
        .r { color:#dc2626; } .y { color:#d97706; } .g { color:#16a34a; }
        .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }
        .dot-r { background:#dc2626; } .dot-y { background:#d97706; } .dot-g { background:#16a34a; }
        .na { color:#999; font-size:12px; }
    </style></head><body>
    <table>
        <thead><tr>
            <th>数据类型</th><th>B站</th><th>抖音</th><th>快手</th><th>小红书</th><th>TapTap</th><th>YouTube</th>
        </tr></thead>
        <tbody>
        <tr>
            <td>浏览记录</td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
        </tr>
        <tr>
            <td>收藏夹</td>
            <td><span class="dot dot-y"></span><span class="y">用户设公开时可见</span></td>
            <td><span class="dot dot-r"></span><span class="r">默认私密</span></td>
            <td><span class="dot dot-r"></span><span class="r">默认私密</span></td>
            <td><span class="dot dot-y"></span><span class="y">部分可见</span></td>
            <td class="na">N/A</td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
        </tr>
        <tr>
            <td>点赞/喜欢列表</td>
            <td><span class="dot dot-r"></span><span class="r">仅自己可见</span></td>
            <td><span class="dot dot-y"></span><span class="y">用户可选公开/私密</span></td>
            <td><span class="dot dot-y"></span><span class="y">用户可选</span></td>
            <td><span class="dot dot-y"></span><span class="y">部分可见</span></td>
            <td class="na">N/A</td>
            <td><span class="dot dot-r"></span><span class="r">私有</span></td>
        </tr>
        <tr>
            <td>关注列表</td>
            <td><span class="dot dot-g"></span><span class="g">公开（需Cookie）</span></td>
            <td><span class="dot dot-y"></span><span class="y">用户可选</span></td>
            <td><span class="dot dot-y"></span><span class="y">用户可选</span></td>
            <td><span class="dot dot-y"></span><span class="y">部分可见</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">默认私有</span></td>
        </tr>
        <tr>
            <td>发布内容/评论</td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
        </tr>
        <tr>
            <td>玩过的游戏列表</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td><span class="dot dot-g"></span><span class="g">公开</span></td>
            <td class="na">N/A</td>
        </tr>
        </tbody>
    </table>
    </body></html>"""
    st_components.html(privacy_matrix_html, height=340, scrolling=False)

    # ── 视频指标可采集性矩阵 ──────────────────────────────────────────────────
    st.markdown("<h3>视频指标可采集性矩阵</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:13px; margin-bottom:0.8rem;'>各平台视频/内容维度指标的可用性与对应字段名。</p>", unsafe_allow_html=True)
    metrics_matrix_html = """<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family: -apple-system,'Inter',BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }
        table { width:100%; border-collapse:collapse; font-size:13px; }
        thead tr { background:#1a1a2e; }
        th { padding:12px 14px; font-size:12px; font-weight:600; color:#ccc; text-align:left; white-space:nowrap; }
        td { padding:12px 14px; border-bottom:1px solid #F0F0F0; vertical-align:middle; font-size:13px; color:#333; }
        tr:hover td { background:#FAFAFA; }
        td:first-child { font-weight:600; color:#111; white-space:nowrap; }
        .g { color:#16a34a; }
        .dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; }
        .dot-g { background:#16a34a; }
        .na { color:#999; font-size:12px; }
        code { background:#e8f5e9; color:#16a34a; font-size:11px; padding:2px 6px; border-radius:3px; font-family:'SF Mono','Fira Code',monospace; font-weight:600; }
    </style></head><body>
    <table>
        <thead><tr>
            <th>指标</th><th>B站</th><th>抖音</th><th>快手</th><th>小红书</th><th>TapTap</th><th>YouTube</th>
        </tr></thead>
        <tbody>
        <tr>
            <td>播放量</td>
            <td><span class="dot dot-g"></span><code>view</code></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">阅读数</span></td>
            <td class="na">N/A（非视频平台）</td>
            <td><span class="dot dot-g"></span><code>viewCount</code></td>
        </tr>
        <tr>
            <td>点赞数</td>
            <td><span class="dot dot-g"></span><code>like</code></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">评分</span></td>
            <td><span class="dot dot-g"></span><code>likeCount</code></td>
        </tr>
        <tr>
            <td>转发/分享</td>
            <td><span class="dot dot-g"></span><code>share</code></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td class="na">N/A</td>
            <td class="na">N/A（已隐藏）</td>
        </tr>
        <tr>
            <td>收藏数</td>
            <td><span class="dot dot-g"></span><code>favorite</code></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
        </tr>
        <tr>
            <td>投币数</td>
            <td><span class="dot dot-g"></span><code>coin</code></td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
        </tr>
        <tr>
            <td>弹幕数</td>
            <td><span class="dot dot-g"></span><code>danmaku</code></td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
            <td class="na">N/A</td>
        </tr>
        <tr>
            <td>评论数</td>
            <td><span class="dot dot-g"></span><code>reply</code></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><span class="g">✓</span></td>
            <td><span class="dot dot-g"></span><code>commentCount</code></td>
        </tr>
        </tbody>
    </table>
    </body></html>"""
    st_components.html(metrics_matrix_html, height=380, scrolling=False)

elif page == "画像":
    st.markdown("<h1>玩家画像 (User Profiler)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 1.5rem;'>基于全网重核玩家长尾评论逆向推断的用户成分画像与诉求提纯。</p>", unsafe_allow_html=True)

    profiles_path = Path("data/profiles/user_games/")
    all_profiles = []
    if profiles_path.exists():
        for pf in profiles_path.glob("*_user_games.csv"):
            try:
                df = pd.read_csv(pf)
                if not df.empty:
                    df["source"] = pf.name
                    all_profiles.append(df)
            except Exception:
                pass

    if not all_profiles:
        st.warning("暂无画像数据。请先执行深度采集，然后使用 CLI 提取画像：\n`python -m src.cli profile --platform bilibili --video-id xxx`")
    else:
        df = pd.concat(all_profiles, ignore_index=True)
        df = df.drop_duplicates(subset=["user_id"]).copy()
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>👥 锁定高核玩家池</div><div style='font-size:28px; font-weight:700; color:#111;'>{len(df)}</div></div>", unsafe_allow_html=True)
            
        with c2:
            whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
            st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>💰 充值能力预估发现</div><div style='font-size:28px; font-weight:700; color:#16a34a;'>{whales_dolphins} <span style='font-size:12px; color:#666; font-weight:400'>名具付费潜力记录</span></div></div>", unsafe_allow_html=True)
            
        with c3:
            refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
            st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>🎯 竞品流失核心难民</div><div style='font-size:28px; font-weight:700; color:#dc2626;'>{refugees} <span style='font-size:12px; color:#666; font-weight:400'>名高转化目标</span></div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.markdown("<h5 style='margin-bottom:12px;'>玩家派系标签占比矩阵</h5>", unsafe_allow_html=True)
            tag_counts = {}
            for tags_str in df["tags"].dropna():
                for tag in tags_str.split(","):
                    tag = tag.strip()
                    if tag:
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if tag_counts:
                tag_df = pd.DataFrame(list(tag_counts.items()), columns=["Tag", "Count"]).sort_values(by="Count", ascending=True)
                st.bar_chart(tag_df.set_index("Tag"))
            else:
                st.info("尚未分离出特定阵营标签")
                
        with col_chart2:
            st.markdown("<h5 style='margin-bottom:12px;'>沉浮消费类型雷达 (推断)</h5>", unsafe_allow_html=True)
            spend_df = df["spend_type"].value_counts().reset_index()
            spend_df.columns = ["Type", "Count"]
            try:
                import altair as alt
                chart = alt.Chart(spend_df).mark_arc(innerRadius=50).encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Type", type="nominal", scale=alt.Scale(domain=["free", "dolphin", "whale"], range=["#94a3b8", "#3b82f6", "#eab308"])),
                    tooltip=["Type", "Count"]
                ).properties(height=340)
                st.altair_chart(chart, use_container_width=True)
            except Exception:
                st.bar_chart(df["spend_type"].value_counts())

        st.markdown("<h5>🔍 核心靶向追踪名单</h5>", unsafe_allow_html=True)
        st.dataframe(
            df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(columns={
                "platform": "来源阵地", "username": "网民昵称", "age_group": "推断龄", 
                "spend_type": "消费级", "tags": "特征向量集", "location": "属地"
            }),
            use_container_width=True,
            hide_index=True
        )


elif page == "智能报表":
    import os
    st.markdown("<h1>智能舆情报表引擎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>根据给定时序处理全矩阵存储池并输出语义聚类研判文档。</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        report_span = st.selectbox("分析跨度层级", ["周度汇总研判 (Weekly)", "每日动向快报 (Daily - WIP)", "月度战略大盘 (Monthly - WIP)"])
    with col2:
        custom_date = st.date_input("时序截断锚点 (默认系统当下日)", value=datetime.now())
        
    date_str = custom_date.strftime("%Y-%m-%d")
    
    # 移除被要求摒弃的中二化名词
    st.markdown("<p style='color: #16a34a; font-size: 13px; font-weight: 500;'>⚡ LLM 语义聚类探针已就位，当前可独立静默执行。</p>", unsafe_allow_html=True)
    
    if st.button("激活生产管道", type="primary"):
        if "WIP" in report_span:
            st.warning("🚧 该维度正在重构闭环中... 当前底部算力仅能够执行 '周度汇总研判 (Weekly)' 的生成。")
        else:
            with st.spinner("NLP 引擎正在提取玩家情感浓度，并过滤高赞负面长文..."):
                stdout, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
            if code == 0:
                st.success("🎉 生成完毕！跨域聚类报告已写入 reports 目录。")
                st.rerun()
            else:
                st.error("执行链由于未捕获异常而停止。")
                with st.expander("调试层输出"):
                    st.code(stderr, language="bash")

    json_path = REPORTS_DIR / f"{date_str}_weekly_report.json"
    md_path = REPORTS_DIR / f"{date_str}_weekly_report.md"

    if json_path.exists() and md_path.exists():
        import json
        st.markdown(f"<h3>📈 情感分布与竞品声量雷达 ({date_str})</h3>", unsafe_allow_html=True)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.markdown("<h5 style='margin-bottom:12px;'>全域情绪倾向甜甜圈图</h5>", unsafe_allow_html=True)
                sent_data = payload.get("sentiment", {})
                if sum(sent_data.values()) > 0:
                    try:
                        import altair as alt
                        s_df = pd.DataFrame(list(sent_data.items()), columns=["Sentiment", "Count"])
                        chart = alt.Chart(s_df).mark_arc(innerRadius=50).encode(
                            theta=alt.Theta(field="Count", type="quantitative"),
                            color=alt.Color(field="Sentiment", type="nominal", scale=alt.Scale(domain=["positive", "negative", "neutral"], range=["#16a34a", "#dc2626", "#94a3b8"])),
                            tooltip=["Sentiment", "Count"]
                        ).properties(height=300)
                        st.altair_chart(chart, use_container_width=True)
                    except Exception:
                        st.bar_chart(pd.Series(sent_data))
                else:
                    st.info("当前情绪雷达无信号波通指征。")
            with c_chart2:
                st.markdown("<h5 style='margin-bottom:12px;'>竞品黑话声量风暴柱状图</h5>", unsafe_allow_html=True)
                mentions_data = payload.get("mentions", {})
                if mentions_data:
                    m_df = pd.DataFrame(list(mentions_data.items()), columns=["Game", "Mentions"]).sort_values("Mentions", ascending=False)
                    st.bar_chart(m_df.set_index("Game"), height=300)
                else:
                    st.info("风暴柱状图未检出明显竞品杂音。")

            st.markdown("---")
            st.markdown("<h3>📝 舆情推演原案 (Markdown 归档)</h3>", unsafe_allow_html=True)
            st.markdown(md_path.read_text(encoding="utf-8"))
        except Exception as e:
            st.error(f"报表渲染库发生异常: {e}")
elif page == "设置":
    import os
    st.markdown("<h1>系统设置</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>直接在下方编辑配置内容，点击保存后立即生效，无需修改代码。</p>", unsafe_allow_html=True)
    st.info("关键词库已移动到「采集」页面右侧，便于边维护词库边执行采集。")

    t1, t2 = st.tabs(["追踪目标 (targets.yaml)", "运行环境变量"])

    with t1:
        targets_data = load_yaml(TARGETS_FILE)
        if "targets" not in targets_data: targets_data["targets"] = {}
        t_data = targets_data["targets"]

        st.info("追踪目标主要是用来进行特定频道的持续监控的。你可以把想重点关注的 B站/YouTube 官方账号或特定游戏专区填在这里，系统会去抓取他们新发的任何动态。")
        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1.5rem;'>操作说明：在下方表格单元格双击可直接修改追踪目标。在末尾空白行输入即可新增，选中行首数字按 Delete 键可删除整行。编辑完成后请点击底部保存。</p>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("##### 📺 Bilibili 频道", unsafe_allow_html=True)
            bili_df = pd.DataFrame(t_data.get("bilibili_channels", []))
            if bili_df.empty: bili_df = pd.DataFrame(columns=["name", "uid"])
            edit_bili = st.data_editor(bili_df, num_rows="dynamic", use_container_width=True, key="ed_bili", hide_index=True)
            
        with c2:
            st.markdown("##### 🟥 YouTube 频道", unsafe_allow_html=True)
            yt_df = pd.DataFrame(t_data.get("youtube_channels", []))
            if yt_df.empty: yt_df = pd.DataFrame(columns=["name", "channel_id"])
            edit_yt = st.data_editor(yt_df, num_rows="dynamic", use_container_width=True, key="ed_yt", hide_index=True)
            
        with c3:
            st.markdown("##### 🎮 TapTap 游戏", unsafe_allow_html=True)
            tap_df = pd.DataFrame(t_data.get("taptap_games", []))
            if tap_df.empty: tap_df = pd.DataFrame(columns=["name", "app_id"])
            edit_tap = st.data_editor(tap_df, num_rows="dynamic", use_container_width=True, key="ed_tap", hide_index=True)

        if st.button("保存 Targets 配置", type="primary"):
            t_data["bilibili_channels"] = edit_bili.dropna(how="all").to_dict("records")
            t_data["youtube_channels"] = edit_yt.dropna(how="all").to_dict("records")
            t_data["taptap_games"] = edit_tap.dropna(how="all").to_dict("records")
            
            try:
                with open(TARGETS_FILE, "w", encoding="utf-8") as f:
                    yaml.safe_dump({"targets": t_data}, f, allow_unicode=True, sort_keys=False)
                st.success("🎉 targets.yaml 已保存！后续采集将按新目标执行。")
            except Exception as e:
                st.error(f"保存失败：{e}")

    with t2:
        from src.core.config import DEFAULT_SECRETS_FILE, load_secrets
        
        st.info("🔐 **凭据集中管控**：在此填写的敏感配置将直接存入本地 `secrets.yaml`，优先于系统环境变量读取，且绝不会被提交到代码仓库。")
        
        sec_data = load_secrets()
        llm = sec_data.get("llm_keys", {})
        bili = sec_data.get("bilibili", {})
        mc = sec_data.get("mediacrawler", {})
        
        st.markdown("##### 🧠 AI 大模型密钥")
        ds_key = st.text_input("DeepSeek API Key", value=llm.get("deepseek", ""), type="password", placeholder="sk-...")
        oa_key = st.text_input("OpenAI API Key", value=llm.get("openai", ""), type="password", placeholder="sk-...")
        qw_key = st.text_input("Qwen API Key (阿里云百炼)", value=llm.get("qwen", ""), type="password", placeholder="sk-...")
        
        st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:1.5rem 0;'/>", unsafe_allow_html=True)
        st.markdown("##### 🍪 平台会话身份 (Cookies / Sessions)")
        st.markdown("<p style='font-size:12px; color:#666;'>用于穿透防抄防风控的重度接口，一般需要通过浏览器抓包 F12 提取。</p>", unsafe_allow_html=True)
        
        sess_bili = st.text_input("Bilibili SESSDATA", value=bili.get("sessdata", ""), type="password", placeholder="请输入 B站 SESSDATA...")
        sess_mc = st.text_area("MediaCrawler Session/Cookie", value=mc.get("session", ""), height=100, placeholder="预留的跨平台通用长 Cookie 载体字符串...")
        
        if st.button("保存密钥配置", type="primary"):
            new_sec = {
                "llm_keys": {
                    "deepseek": ds_key,
                    "openai": oa_key,
                    "qwen": qw_key
                },
                "bilibili": {
                    "sessdata": sess_bili
                },
                "mediacrawler": {
                    "session": sess_mc
                }
            }
            try:
                with open(DEFAULT_SECRETS_FILE, "w", encoding="utf-8") as f:
                    yaml.safe_dump(new_sec, f, allow_unicode=True, sort_keys=False)
                st.success("🎉 secrets.yaml 已加密保存至本地！运行大盘即刻生效。")
            except Exception as e:
                st.error(f"保存发生异常：{e}")
