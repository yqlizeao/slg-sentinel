"""
SLG Sentinel — 企业级数据分析监控台
"""

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

/* 主内容区域去除左侧多余空白 */
.block-container {
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
    "taptap": "https://www.taptap.cn/favicon.ico"
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

def get_system_health() -> dict:
    import os
    total_v, total_c, last_sync = 0, 0, 0
    for p in ["bilibili", "youtube", "taptap"]:
        stt = get_platform_stats(p)
        total_v += stt["videos_total"]
        total_c += stt["comments_total"]
    
    if DATA_DIR.exists():
        for f in DATA_DIR.rglob("*.csv"):
            if f.is_file():
                mtime = f.stat().st_mtime
                if mtime > last_sync: last_sync = mtime
            
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


# ─── 侧边栏菜单 ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='display: flex; align-items: center; margin-bottom: 2rem; padding: 1rem 0;'>
        <div style='background: #000; color: #fff; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-family: monospace; font-size: 18px; margin-right: 12px;'>S</div>
        <div>
            <h3 style='margin: 0; font-size: 16px; color: #111; line-height: 1.2;'>SLG Sentinel</h3>
            <p style='margin: 0; font-size: 12px; color: #666;'>舆情分析平台</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "应用导航",
        ["总览", "采集", "周报", "设置"],
        label_visibility="collapsed",
    )

    st.markdown("<br/>", unsafe_allow_html=True)
    st.caption(f"当前系统周期\n\n{datetime.now().strftime('%Y年%m月%d日')}")

# ═══════════════════════════════════════════════════════════════════════════════
if page == "总览":
    st.markdown("<h1>数据大盘</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>实时监控矩阵内的媒体特征与用户反馈。</p>", unsafe_allow_html=True)

    # ── 系统运行中枢 (Pulse Bar) ─────────────────────────────────────────────
    st.markdown("<h3>哨兵中枢运行基线</h3>", unsafe_allow_html=True)
    health = get_system_health()
    st.markdown(f"""
    <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px;'>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>📡 监控探针网络</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['targets']} <span style='font-size:12px; font-weight:400; color:#666;'>频道</span></div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>映射 {health['keywords']} 项扩充词法谱系</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>📦 数据汪洋容量</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['capacity']} <span style='font-size:12px; font-weight:400; color:#666;'>组</span></div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>全局视讯与评论快照底座</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>🧠 舆情神经干线 (LLM)</div>
            <div style='font-size:24px; font-weight:700; color:{"#16a34a" if health['api_health'] else "#dc2626"}; margin-top:8px;'>{"活跃 OK" if health['api_health'] else "断连 OFFLINE"}</div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>负责语义下发与情感萃取分析</div>
        </div>
        <div style='padding:16px; border:1px solid #EAEAEA; border-radius:8px; background:#FAFAFA;'>
            <div style='font-size:12px; color:#666;'>🕑 最新潮汐探针返回</div>
            <div style='font-size:24px; font-weight:700; color:#111; margin-top:8px;'>{health['last_sync']}</div>
            <div style='font-size:11px; color:#999; margin-top:4px;'>存储池最近一次成功落盘发生时刻</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 平台增量指标 ──────────────────────────────────────────────────────────
    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("<h3>平台活水量态阵列</h3>", unsafe_allow_html=True)

    cols = st.columns(3)
    p_data = [("bilibili", "哔哩哔哩"), ("youtube", "YouTube"), ("taptap", "TapTap")]
    for i, (p_id, p_label) in enumerate(p_data):
        stats = get_platform_stats(p_id)
        with cols[i]:
            st.markdown(f"<div style='margin-bottom:-35px; z-index:10; position:relative; padding:24px 24px 0 24px;'><img class='platform-icon' src='{platform_brand_icons[p_id]}'> <span style='font-size:14px; font-weight:500; color:#666;'>{p_label}</span></div>", unsafe_allow_html=True)
            
            delta_val = f"今日新增流 {stats['videos_today']} 基底, {stats['comments_today']} 评论"
            st.metric(label="​", value=str(stats['videos_total']) if stats['videos_total'] else "0", delta=delta_val, delta_color="normal")

    # ── 内容热度增量（周度）表格视图 ─────────────────────────────────────────
    st.markdown("<hr style='border: none; border-top: 1px solid #EAEAEA; margin: 2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>🚨 全网热帖异动爆发阵列</h3>", unsafe_allow_html=True)
    c_desc, c_ctrl = st.columns([8, 2])
    with c_desc:
        st.markdown("<p style='color:#666; font-size:13px; margin-bottom:1rem;'>动态拉取跨周期全网流量异动的头部内容，作为危机公关/传播研判首要输入。</p>", unsafe_allow_html=True)
    with c_ctrl:
        view_limit = st.selectbox("单屏显示限额", [10, 20, 50, 100, 300, 500], index=2, label_visibility="collapsed")

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

    # ── 深度数据引擎舱走廊 ────────────────────────────────────────────────────────
    st.markdown("<hr style='border: none; border-top: 1px solid #EAEAEA; margin: 2rem 0;'/>", unsafe_allow_html=True)
    st.markdown("<h3>深度数据引擎舱</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:13px; margin-bottom:1rem;'>系统高阶分析能力层（AI/特征工程）状态巡检。</p>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:20px; border-radius:8px; height: 140px;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top:0'>📜 智能舆情大模型提纯器</h5>", unsafe_allow_html=True)
        report = get_latest_report()
        if report:
            time_str = datetime.fromtimestamp(report.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            st.markdown(f"<p style='font-size:13px; color:#16a34a; font-weight:500;'>✅ 最新快报已于 {time_str} 定稿产出。<br><br>👉 请前往侧边栏导航 <b>[周报]</b> 面板通读深维长卷。</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size:13px; color:#d97706; font-weight:500;'>💤 舆情分析层处于静默期未介入。<br><br>👉 请在采集收网后，前往侧边栏导航 <b>[周报]</b> 手动激发。</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_b:
        st.markdown("<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:20px; border-radius:8px; height: 140px;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='margin-top:0'>👤 跨域竞品玩家画像侧写 (Profiler)</h5>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:13px; color:#666;'><span style='background:#EAEAEA; color:#333; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:11px;'>🚀 NEXT PHASE</span><br><br>即将释出关联 TapTap 与 B站/YouTube 的长尾数据缝合能力，逆向推演玩家核心特征标签，实现精准靶向打击。</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)



elif page == "采集":
    st.markdown("<h1>内容采集</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 1.5rem;'>手动介入向指定媒介触发爬虫网络或更新快照状态。</p>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.markdown("<p style='font-weight:500; font-size:13px; color:#666;'>选择执行平台</p>", unsafe_allow_html=True)
        platform = st.selectbox("选择执行平台", ["bilibili", "youtube", "taptap", "xiaohongshu", "douyin", "kuaishou"], label_visibility="collapsed")
    
    with c2:
        st.markdown("<p style='font-weight:500; font-size:13px; color:#666;'>授权执行模式</p>", unsafe_allow_html=True)
        if platform in ["xiaohongshu", "douyin", "kuaishou"]:
            mode = st.radio("授权执行模式", ["MediaCrawler 受限沙盒模式 (强制要求本地环境)"], label_visibility="collapsed")
            st.markdown("<p style='font-size:12px; color:#dc2626; margin-top:4px;'>⚠️ 必须本地扫码。</p>", unsafe_allow_html=True)
        else:
            mode = st.radio("授权执行模式", ["基础免登录模式 (适合云端自动化配置)", "受限凭证模式 (需要载入本地会话环境)"], label_visibility="collapsed")

    with c3:
        st.markdown("<p style='font-weight:500; font-size:13px; color:#666;'>爬取深度策略</p>", unsafe_allow_html=True)
        if platform in ["xiaohongshu", "douyin", "kuaishou"]:
            depth = st.radio("采集深度", ["受限单体深度遍历"], label_visibility="collapsed", disabled=True)
        else:
            depth = st.radio("采集深度", ["简易采集 (仅广域搜索，极速过滤)", "详细采集 (包含单视频详情节点下钻)"], label_visibility="collapsed")

    # 针对研发深度分析的高级排序面板
    order_val = "totalrank"
    if platform == "bilibili":
        st.markdown("<div style='margin-top:1rem; padding:12px; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-weight:600; font-size:13px; color:#1e293b; margin-bottom:8px;'>🔥 研发雷达：高级检索排序策略</p>", unsafe_allow_html=True)
        order_map = {
            "【默认/总合】包含海量日常及手游商业推广 (totalrank)": "totalrank",
            "【时间线脉搏 / Pulse】仅取最新发布，监测公关危情 (pubdate)": "pubdate",
            "【神级传世名场面】挖掘历史曝光率最高巨额流量池 (click)": "click",
            "【极度硬核 / Deep Dive】单机玩家最爱收藏的深度拆解与评测 (stow)": "stow"
        }
        order_label = st.selectbox("排序策略", list(order_map.keys()), index=0, label_visibility="collapsed")
        order_val = order_map[order_label]
        st.markdown("</div>", unsafe_allow_html=True)

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
            <th style="width:30%">核心指令/接⼝</th>
            <th style="width:25%">备注</th>
            <th style="width:27%">可⾏性与限制</th>
        </tr></thead>
        <tbody>"""
    
    if platform == "bilibili":
        comp_title = "底层开源代理组件: <a href='https://github.com/Nemo2011/bilibili-api' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>bilibili-api-python (3.8k⭐)</a>"
        iframe_height = 680
        
        is_simple = "简易" in depth
        is_basic = "免登录" in mode
        
        sess_status = "<span class='g'>✅ 基于自算 Wbi 放行</span>" if is_basic else "<span class='g'>✅ SESSDATA 穿梭放行</span>"
        deep_status = "<span class='g'>✅ 基于自算 Wbi 放行</span>" if is_basic else "<span class='g'>✅ SESSDATA 高效下行</span>"
        
        api_call = "<code>search.search_by_type()</code>" if is_simple else "<code>video.Video().get_info()</code>"
        b_coin_status = "<span class='r'>❌ (简易广域搜索不返回)</span>" if is_simple else deep_status
        
        cmt_status = "<span class='y'>⚠️ 仅可穿透最外层浅页</span>" if is_basic else "<span class='g'>✅ 全量抽取无尽长尾评论</span>"
        fav_status = "<span class='r'>❌ 拦截: 无凭证不予下发</span>" if is_basic else "<span class='g'>✅ 若用户公开即完全采集</span>"
        follow_status = "<span class='r'>❌ 拦截: 需 SESSDATA</span>" if is_basic else "<span class='g'>✅ 解除屏蔽获得高阶权限</span>"

        rows = f"""
        <tr><td>BV号 (ID)</td><td><code>search.search_by_type()</code></td><td class="desc">作为视频全局唯一标识符主键</td><td>{sess_status}</td></tr>
        <tr><td>视频标题 (Title)</td><td><code>search.search_by_type()</code></td><td class="desc">做包含特定游戏名切分的语料</td><td>{sess_status}</td></tr>
        <tr><td>UP主名称 (Author)</td><td><code>search.search_by_type()</code></td><td class="desc">追踪头部 KOL 和腰部发声者</td><td>{sess_status}</td></tr>
        <tr><td>发布日期 (Pubdate)</td><td><code>search.search_by_type()</code></td><td class="desc">进行周报的增量周期界定标准</td><td>{sess_status}</td></tr>
        <tr><td>播放量 (View)</td><td>{api_call}</td><td class="desc">最核心的曝光量级评判指标</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>点赞数 (Like)</td><td>{api_call}</td><td class="desc">计算互动率 (Like/View) 核心参考数</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>投币数 (Coin)</td><td>{api_call}</td><td class="desc">体现高优硬派用户认可度的硬核指标</td><td>{b_coin_status}</td></tr>
        <tr><td>收藏数 (Favorite)</td><td>{api_call}</td><td class="desc">沉淀为用户长尾关注的囤积量转化</td><td>{deep_status if not is_simple else sess_status}</td></tr>
        <tr><td>分享数 (Share)</td><td>{api_call}</td><td class="desc">衡量跨平台破圈能力的传播量标识</td><td>{b_coin_status}</td></tr>
        <tr><td>评论者 UID</td><td><code>video.Video().get_comments()</code></td><td class="desc">用以溯源画像的长尾横向指标来源</td><td>{cmt_status}</td></tr>
        <tr><td>评论内容纯文本</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于 NLP 情感计算极性(正向/负向)</td><td>{cmt_status}</td></tr>
        <tr><td>被点赞数 (Like)</td><td><code>video.Video().get_comments()</code></td><td class="desc">作为该条神评在玩家群中影响力的权重</td><td>{cmt_status}</td></tr>
        <tr><td>公开收藏夹</td><td><code>get_video_favorite_list(uid)</code></td><td class="desc">反向暴露这名核心玩家它游心智偏好</td><td>{fav_status}</td></tr>
        <tr><td>关注关系链</td><td><code>API /x/relation/followings</code></td><td class="desc">挖掘订阅重合度及竞品官方追随意向</td><td>{follow_status}</td></tr>"""
    elif platform == "youtube":
        comp_title = "底层开源代理组件: <a href='https://github.com/yt-dlp/yt-dlp' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>yt-dlp (155k⭐)</a> · <a href='https://github.com/dermasmid/scrapetube' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>scrapetube (500⭐)</a> · <a href='https://github.com/egbertbouman/youtube-comment-downloader' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>yt-cmt-dl (1.2k⭐)</a>"
        iframe_height = 600
        rows = """
        <tr><td>视频 ID (videoId)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">唯一内容标识符引擎关联锚点</td><td><span class="g">✅ 工具内置安全绕过</span></td></tr>
        <tr><td>视频标题 (Title)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">提供检索和展示的语义内容实体</td><td><span class="g">✅ 工具内置安全绕过</span></td></tr>
        <tr><td>所属频道 (Channel)</td><td><code>yt-dlp ytsearch:关键词</code></td><td class="desc">追踪外围营销买量实体名溯源</td><td><span class="g">✅ 工具内置安全绕过</span></td></tr>
        <tr><td>下辖视频列表</td><td><code>scrapetube.get_channel()</code></td><td class="desc">保证不遗漏单发渠道内的任何视频</td><td><span class="g">✅ 突破万级接口限制</span></td></tr>
        <tr><td>基础发布日期</td><td><code>scrapetube.get_channel()</code></td><td class="desc">有效过滤非周报计算周期内的废料</td><td><span class="g">✅ 突破万级接口限制</span></td></tr>
        <tr><td>基础播放量</td><td><code>scrapetube.get_channel()</code></td><td class="desc">初筛高价值瀑布流水线视频门槛</td><td><span class="g">✅ 突破万级接口限制</span></td></tr>
        <tr><td>精准真播放 (viewCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">精确曝光播放真实评估数据</td><td><span class="g">✅ 原生免登录解包</span></td></tr>
        <tr><td>精准点赞数 (likeCount)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">海外受众视频正面交汇交互反馈</td><td><span class="g">✅ 原生免登录解包</span></td></tr>
        <tr><td>视频受众标签 (Tags)</td><td><code>yt-dlp --dump-json</code></td><td class="desc">读取创作者自行锚定的内容生态隐喻</td><td><span class="g">✅ 原生免登录解包</span></td></tr>
        <tr><td>网民 ID 与昵称</td><td><code>youtube-comment-downloader</code></td><td class="desc">特定海外核心主见发帖人的标识抓手</td><td><span class="g">✅ 千万级并发安全穿刺</span></td></tr>
        <tr><td>高价值点赞数</td><td><code>youtube-comment-downloader</code></td><td class="desc">找出能左右整个外围论坛社区风向的热门置顶</td><td><span class="g">✅ 千万级并发安全穿刺</span></td></tr>
        <tr><td>详细发送时间戳</td><td><code>youtube-comment-downloader</code></td><td class="desc">过滤旧网游在长尾史前周期的旧评论</td><td><span class="g">✅ 千万级并发安全穿刺</span></td></tr>
        <tr><td>评论完整纯文本</td><td><code>youtube-comment-downloader</code></td><td class="desc">进入外网语料进行大规模 NLP 情报清洗底仓</td><td><span class="g">✅ 千万级并发安全穿刺</span></td></tr>"""
    elif platform == "taptap":
        comp_title = "底层支撑策略: <span style='font-family:monospace; font-weight:600; color:#333; background:#e2e8f0; padding:4px 8px; border-radius:6px;'>自有协议解析引擎 (Requests + BS4 + 指纹 Header)</span>"
        iframe_height = 420
        rows = """
        <tr><td>核心星评 (1-5星)</td><td><code>API /v2/review/thread</code></td><td class="desc">TapTap 极具风向标价值的核心数值战损</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>测评明文大段内容</td><td><code>API /v2/review/thread</code></td><td class="desc">提供对游戏极为深刻硬核的长难句发声本体</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>社区支持度 (ups)</td><td><code>API /v2/review/thread</code></td><td class="desc">判断老哥发帖观点被附议赞同的社会学指标</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>社区反对数 (downs)</td><td><code>API /v2/review/thread</code></td><td class="desc">追踪两派群体矛盾舆情高发冲突发酵点的凭证</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>发帖物理设备名</td><td><code>API /v2/review/thread</code></td><td class="desc">推敲下沉量级机器分布和高净值氪佬占比</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>硬核游玩时长</td><td><code>API /v2/review/thread</code></td><td class="desc">分辨高声量云玩家黑粉与真正 SLG 核爆肝帝的神器</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>网民专属 UID</td><td><code>API /v2/review/thread</code></td><td class="desc">深度锁定核心目标后为二次高维解析埋下接口锚</td><td><span class="g">✅ 原生 WebAPI 头部伪装</span></td></tr>
        <tr><td>玩家曾游玩游戏库</td><td><code>API /v2/game/games</code></td><td class="desc">通过玩过的交集列表判定是否对三消等有强力沉淀</td><td><span class="g">✅ 免 Cookie 高频并发下行</span></td></tr>
        <tr><td>外部竞品评价横比</td><td><code>API /v2/game/games</code></td><td class="desc">找出该玩家从三战开溜入驻新端的核心缘由缩影</td><td><span class="g">✅ 免 Cookie 高频并发下行</span></td></tr>"""
    elif platform in ["xiaohongshu", "douyin", "kuaishou"]:
        comp_title = "外部核心桥接库: <a href='https://github.com/NanmiCoder/MediaCrawler' target='_blank' style='color:#2563eb; text-decoration:none; font-family:monospace; font-weight:600;'>MediaCrawler (16.9k⭐)</a> · <span style='font-family:monospace; color:#333; font-weight:600; font-size:11px;'>(Playwright 子进程挂载)</span>"
        iframe_height = 560
        rows = """
        <tr><td>帖子/视频 ID</td><td><code>MediaCrawler (aweme_id)</code></td><td class="desc">精准阻击买量爆款的唯一溯源标识</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>视频文案标题 (Title)</td><td><code>MediaCrawler (desc)</code></td><td class="desc">提供检索和展示的语义内容实体营销文案</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>创作者名称 (Author)</td><td><code>MediaCrawler (nickname)</code></td><td class="desc">判断出稿方主体是官方号还是野蛮生长的二创者</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>短片真实播放量</td><td><code>MediaCrawler (play_count)</code></td><td class="desc">初筛高价值瀑布流水线视频门槛和传播穿透度</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>核心点赞数 (like)</td><td><code>MediaCrawler (like_count)</code></td><td class="desc">评估受众对于该套 SLG 营销素材的正向交汇反馈</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>二次分享转发量</td><td><code>MediaCrawler (share_count)</code></td><td class="desc">衡量整包游戏被玩家“人传人”裂变的超级质变指数</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>私域背书收藏数</td><td><code>MediaCrawler (collect)</code></td><td class="desc">记录防守玩家将攻略/买量视频作为个人资产的意图</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>内容定向算法标签</td><td><code>MediaCrawler (tags)</code></td><td class="desc">捕捉小红书/抖音分发引擎为内容加盖的隐喻标识</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>评论者 ID (user_id)</td><td><code>MediaCrawler (comments)</code></td><td class="desc">追踪恶意带节奏/或死忠粉的底层账号坐标体系</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>神评文本明文</td><td><code>MediaCrawler (text)</code></td><td class="desc">大量沉淀充满缩写梗的粗粝原生态情绪语料库</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>
        <tr><td>网民 IP 物理归属</td><td><code>MediaCrawler (ip_location)</code></td><td class="desc">还原该竞品下沉市场的真实地域浓度与氪金能力分布</td><td><span class="y">⚠️ 依赖终端沙盒强取</span></td></tr>"""

    matrix_html = matrix_html_base + rows + "</tbody></table></body></html>"
    
    st.markdown(f"<div style='margin-top:1.5rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:flex-end;'><div><p style='font-size:14px; color:#111; font-weight:600; margin:0;'>当前选中模式探针约束矩阵</p></div><div style='font-size:12px; color:#666;'>{comp_title}</div></div>", unsafe_allow_html=True)
    st_components.html(matrix_html, height=iframe_height, scrolling=False)

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button(f"启动 {platform.capitalize()} 采集链路", type="primary"):
        m_val = "actions" if "基础免登录" in mode else "local"
        with st.spinner(f"探测器正在后台接入 {platform.capitalize()} 信息流，通常耗时一至两分钟，请勿刷新页面..."):
            cmd_args = ["crawl", "--platform", platform, "--mode", m_val, "--order", order_val]
            if platform not in ["xiaohongshu", "douyin", "kuaishou"] and "简易" in depth:
                cmd_args.extend(["--depth", "shallow"])
            stdout, stderr, code = run_cli(cmd_args)
        if code == 0:
            st.success(f"✅ 【{platform.capitalize()}】指令流已成功回归至正常终态，全部捕获已落盘。")
        else:
            st.error(f"❌ 子线程调度失败，返回状态码: {code}")
        with st.expander("下层标准输入输出追踪", expanded=True if code != 0 else False):
            st.code((stdout + "\n" + stderr).strip(), language="bash")

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


elif page == "周报":
    import os
    st.markdown("<h1>我的周报</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>根据给定时序处理全矩阵存储池并输出语义聚类文档。</p>", unsafe_allow_html=True)
    
    custom_date = st.date_input("时序截断点 (默认采用系统当下日)", value=datetime.now())
    
    # 缺乏 API 时的屏蔽层
    has_api = bool(os.environ.get("DEEPSEEK_API_KEY"))
    if not has_api:
        st.warning("⚠️ 侦测到 LLM 神经引擎未连接 (缺少 DEEPSEEK_API_KEY 环境变量)。由于生成报告依赖语义分析器，请先前往「设置」配置，否则无法启动生成任务。")

    if st.button("激活生成管道", type="primary", disabled=not has_api):
        date_str = custom_date.strftime("%Y-%m-%d")
        with st.spinner("LLM 神经节点正在处理全矩阵存储池并提纯海量图文舆情特征，约需 1-2 分钟..."):
            stdout, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
        if code == 0:
            st.success("🎉 生成完毕！周报结果已写入 reports 目录。")
            st.balloons()
            try:
                st.markdown((REPORTS_DIR / f"{date_str}_weekly_report.md").read_text(encoding="utf-8"))
            except Exception:
                pass
        else:
            st.error("执行链由于未捕获异常而停止。")
            with st.expander("调试层输出"):
                st.code(stderr, language="bash")
elif page == "设置":
    import os
    st.markdown("<h1>系统设置</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>直接在下方编辑配置内容，点击保存后立即生效，无需修改代码。</p>", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["追踪目标 (targets.yaml)", "关键词库 (keywords.yaml)", "运行环境变量"])

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
        kw_data = load_yaml(KEYWORDS_FILE)
        if "seed_keywords" not in kw_data: kw_data["seed_keywords"] = {"games": [], "categories": []}
        if "expansion" not in kw_data: kw_data["expansion"] = {"enabled": True, "llm_provider": "deepseek", "max_expanded_keywords": 50}

        st.info("这里的关键词会被系统直接丢到各个平台的搜索框里去执行大范围的内容检索。\n\n注：之所以把游戏名称和游戏品类拆分成两张单独的表，是因为底下的 AI 扩词功能需要同时参考这两项，才能更聪明的为你联想出类似“三战开荒”这样的民间俗称与黑话组合。")
        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1.5rem;'>操作说明：在下方表格双击单元格即可修改或新增系统追踪词条（支持选中行首数字后按 Delete 键删除行）。</p>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### ⚔️ 游戏名称种子词")
            g_df = pd.DataFrame([{"词条": k} for k in kw_data["seed_keywords"].get("games", []) if k])
            if g_df.empty: g_df = pd.DataFrame(columns=["词条"])
            edit_games = st.data_editor(g_df, num_rows="dynamic", use_container_width=True, key="ed_game", hide_index=True)

        with c2:
            st.markdown("##### 🏷️ 游戏品类种子词")
            c_df = pd.DataFrame([{"词条": k} for k in kw_data["seed_keywords"].get("categories", []) if k])
            if c_df.empty: c_df = pd.DataFrame(columns=["词条"])
            edit_cats = st.data_editor(c_df, num_rows="dynamic", use_container_width=True, key="ed_cat", hide_index=True)

        st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:1.5rem 0;'/>", unsafe_allow_html=True)
        st.markdown("<hr style='border:none; border-top:1px solid #EAEAEA; margin:1.5rem 0;'/>", unsafe_allow_html=True)
        st.markdown("##### 🤖 RAG 语义逆向提取 (数据驱动)")
        
        st.markdown("<p style='font-size:12px; color:#666;'>告别全凭 AI 脑补！系统将遍历靶标库内的头部 SLG 游戏，拉取真实文案与标签交由 AI 提纯重构。</p>", unsafe_allow_html=True)
        exp = kw_data.get("expansion", {})
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            exp_enabled = st.toggle("启用自动扩词", value=exp.get("enabled", True))
        with cc2:
            exp_provider = st.selectbox("LLM Provider", ["deepseek", "openai", "qwen"], index=["deepseek", "openai", "qwen"].index(exp.get("llm_provider", "deepseek")) if exp.get("llm_provider", "deepseek") in ["deepseek", "openai", "qwen"] else 0)
        with cc3:
            exp_max = st.number_input("最大提取数 (10-200)", min_value=10, max_value=200, value=exp.get("max_expanded_keywords", 50))
            
        c_btn, c_rag = st.columns([1, 1])

        with c_btn:
            if st.button("💾 保存 Keywords", type="primary", use_container_width=True):
                new_games = [row["词条"] for _, row in edit_games.dropna(how="all").iterrows() if str(row["词条"]).strip()]
                new_cats = [row["词条"] for _, row in edit_cats.dropna(how="all").iterrows() if str(row["词条"]).strip()]
                kw_data["seed_keywords"]["games"] = new_games
                kw_data["seed_keywords"]["categories"] = new_cats
                kw_data["expansion"] = {
                    "enabled": exp_enabled,
                    "llm_provider": exp_provider,
                    "max_expanded_keywords": exp_max
                }
                try:
                    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
                        yaml.safe_dump(kw_data, f, allow_unicode=True, sort_keys=False)
                    st.success("🎉 keywords.yaml 已保存！")
                except Exception as e:
                    st.error(f"保存失败：{e}")
                    
        with c_rag:
            if st.button("🚀 立即执行 RAG 语义提取", type="secondary", use_container_width=True):
                from src.core.config import load_config
                from src.core.keyword_expander import KeywordExpander
                
                conf = load_config()
                pbar = st.progress(0)
                status_txt = st.empty()
                
                def cb(cur, tot, name):
                    pbar.progress(cur / tot)
                    status_txt.text(f"[{cur}/{tot}] 正在抓取语料: {name}")

                with st.spinner("引擎提纯中，请勿刷新页面..."):
                    expander = KeywordExpander(conf)
                    results = expander.expand(provider=exp_provider, max_keywords=exp_max, progress_callback=cb)
                    
                    if results:
                        status_txt.text("")
                        st.success(f"✅ 成功提取 {len(results)} 个高潜长尾词！")
                        # 注入回配置文件并保留
                        new_cats = kw_data["seed_keywords"]["categories"]
                        added = 0
                        for r in results:
                            if r not in new_cats:
                                new_cats.append(r)
                                added += 1
                        with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
                            yaml.safe_dump(kw_data, f, allow_unicode=True, sort_keys=False)
                        st.info(f"已自动合并 {added} 个新词入库。请前往侧边栏或重新载入本页浏览！")
                        with st.expander("查看本次提取词典"):
                            st.json(results)
                    else:
                        st.error("提取失败或未获取到语料。")

    with t3:
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
