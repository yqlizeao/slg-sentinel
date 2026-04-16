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
    v_dir, c_dir, r_dir = DATA_DIR/platform/"videos", DATA_DIR/platform/"comments", DATA_DIR/platform/"reviews"
    v_total = sum(count_csv_rows(f) for f in v_dir.glob("*.csv")) if v_dir.exists() else 0
    c_total = sum(count_csv_rows(f) for f in c_dir.glob("*.csv")) if c_dir.exists() else sum(count_csv_rows(f) for f in r_dir.glob("*.csv")) if r_dir.exists() else 0
    v_today = sum(count_csv_rows(f) for f in v_dir.glob(f"{today}_*.csv")) if v_dir.exists() else 0
    c_today = sum(count_csv_rows(f) for f in c_dir.glob(f"{today}_*.csv")) if c_dir.exists() else sum(count_csv_rows(f) for f in r_dir.glob(f"{today}_*.csv")) if r_dir.exists() else 0
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
    for platform in ["bilibili", "youtube"]:
        v_dir = DATA_DIR / platform / "videos"
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
        ["总览", "采集", "周报", "扩词", "设置"],
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
    st.markdown("<p style='color:#666; font-size:13px; margin-bottom:1rem;'>动态拉取跨周期全网流量异动的头部内容，作为危机公关/传播研判首要输入。</p>", unsafe_allow_html=True)

    def fmt_num(n):
        try:
            n = int(n)
            if n < 0: return "—"          # -1 = API 未返回此字段
            if n >= 100000000: return f"{n/100000000:.1f}亿"
            if n >= 10000: return f"{n/10000:.1f}万"
            return f"{n:,}"
        except: return str(n) if n else "—"

    trending = get_trending_videos(20)  # 表格可承载更多
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
            coin_val = fmt_num(vid.get('coin_count', '0')) if plat == 'bilibili' else '—'

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
                <td class="stat">{coin_val}</td>
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
                <th class="right">投币</th><th class="right">发布日</th>
            </tr></thead>
            <tbody>{all_rows}</tbody>
        </table>
        </body></html>"""
        # 每行约 130px（播放器 90 + 标题作者标签行）
        table_height = min(len(trending) * 130 + 60, 3200)
        st_components.html(table_doc, height=table_height, scrolling=False)
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
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("<p style='font-weight:500; font-size:13px; color:#666;'>选择执行平台</p>", unsafe_allow_html=True)
        platform = st.selectbox("选择执行平台", ["bilibili", "youtube", "taptap", "xiaohongshu", "douyin", "kuaishou"], label_visibility="collapsed")
    
    with c2:
        st.markdown("<p style='font-weight:500; font-size:13px; color:#666;'>授权执行模式</p>", unsafe_allow_html=True)
        if platform in ["xiaohongshu", "douyin", "kuaishou"]:
            mode = st.radio("授权执行模式", ["MediaCrawler 受限沙盒模式 (强制要求载入本地环境与扫码态)"], label_visibility="collapsed")
            st.markdown("<p style='font-size:12px; color:#dc2626; margin-top:4px;'>⚠️ 该平台受极度严苛的指纹风控限制，完全阻断 Actions 免登调用。</p>", unsafe_allow_html=True)
        else:
            mode = st.radio("授权执行模式", ["基础免登录模式 (适合云端自动化配置)", "受限凭证模式 (需要载入本地会话环境)"], label_visibility="collapsed")

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
        if "基础免登录" in mode:
            rows = """
        <tr><td>BV号 (ID)</td><td><code>search.search_by_type()</code></td><td class="desc">作为视频全局唯一标识符主键</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>视频标题 (Title)</td><td><code>search.search_by_type()</code></td><td class="desc">做包含特定游戏名切分的语料</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>UP主名称 (Author)</td><td><code>search.search_by_type()</code></td><td class="desc">追踪头部 KOL 和腰部发声者</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>发布日期 (Pubdate)</td><td><code>search.search_by_type()</code></td><td class="desc">进行周报的增量周期界定标准</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>播放量 (View)</td><td><code>video.Video().get_info()</code></td><td class="desc">最核心的曝光量级评判指标</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>点赞数 (Like)</td><td><code>video.Video().get_info()</code></td><td class="desc">计算互动率 (Like/View) 核心参考数</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>投币数 (Coin)</td><td><code>video.Video().get_info()</code></td><td class="desc">体现高优硬派用户认可度的硬核指标</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>收藏数 (Favorite)</td><td><code>video.Video().get_info()</code></td><td class="desc">沉淀为用户长尾关注的囤积量转化</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>分享数 (Share)</td><td><code>video.Video().get_info()</code></td><td class="desc">衡量跨平台破圈能力的传播量标识</td><td><span class="g">✅ 基于自算 Wbi 放行</span></td></tr>
        <tr><td>评论者 UID</td><td><code>video.Video().get_comments()</code></td><td class="desc">用以溯源画像的长尾横向指标来源</td><td><span class="y">⚠️ 仅可穿透最外层浅页</span></td></tr>
        <tr><td>评论内容纯文本</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于 NLP 情感计算极性(正向/负向)</td><td><span class="y">⚠️ 仅可穿透最外层浅页</span></td></tr>
        <tr><td>被点赞数 (Like)</td><td><code>video.Video().get_comments()</code></td><td class="desc">作为该条神评在玩家群中影响力的权重</td><td><span class="y">⚠️ 仅可穿透最外层浅页</span></td></tr>
        <tr><td>公开收藏夹</td><td><code>get_video_favorite_list(uid)</code></td><td class="desc">反向暴露这名核心玩家它游心智偏好</td><td><span class="r">❌ 拦截: 无凭证不予下发</span></td></tr>
        <tr><td>关注关系链</td><td><code>API /x/relation/followings</code></td><td class="desc">挖掘订阅重合度及竞品官方追随意向</td><td><span class="r">❌ 拦截: 需 SESSDATA</span></td></tr>"""
        else:
            rows = """
        <tr><td>BV号 (ID)</td><td><code>search.search_by_type()</code></td><td class="desc">作为视频全局唯一标识符主键</td><td><span class="g">✅ SESSDATA 穿梭放行</span></td></tr>
        <tr><td>视频标题 (Title)</td><td><code>search.search_by_type()</code></td><td class="desc">做包含特定游戏名切分的语料</td><td><span class="g">✅ SESSDATA 穿梭放行</span></td></tr>
        <tr><td>UP主名称 (Author)</td><td><code>search.search_by_type()</code></td><td class="desc">追踪头部 KOL 和腰部发声者</td><td><span class="g">✅ SESSDATA 穿梭放行</span></td></tr>
        <tr><td>发布日期 (Pubdate)</td><td><code>search.search_by_type()</code></td><td class="desc">进行周报的增量周期界定标准</td><td><span class="g">✅ SESSDATA 穿梭放行</span></td></tr>
        <tr><td>播放量 (View)</td><td><code>video.Video().get_info()</code></td><td class="desc">最核心的曝光量级评判指标</td><td><span class="g">✅ SESSDATA 高效下行</span></td></tr>
        <tr><td>点赞数 (Like)</td><td><code>video.Video().get_info()</code></td><td class="desc">计算互动率 (Like/View) 核心参考数</td><td><span class="g">✅ SESSDATA 高效下行</span></td></tr>
        <tr><td>投币数 (Coin)</td><td><code>video.Video().get_info()</code></td><td class="desc">体现高优硬派用户认可度的硬核指标</td><td><span class="g">✅ SESSDATA 高效下行</span></td></tr>
        <tr><td>收藏数 (Favorite)</td><td><code>video.Video().get_info()</code></td><td class="desc">沉淀为用户长尾关注的囤积量转化</td><td><span class="g">✅ SESSDATA 高效下行</span></td></tr>
        <tr><td>分享数 (Share)</td><td><code>video.Video().get_info()</code></td><td class="desc">衡量跨平台破圈能力的传播量标识</td><td><span class="g">✅ SESSDATA 高效下行</span></td></tr>
        <tr><td>评论者 UID</td><td><code>video.Video().get_comments()</code></td><td class="desc">用以溯源画像的长尾横向指标来源</td><td><span class="g">✅ 全量抽取无尽长尾评论</span></td></tr>
        <tr><td>评论内容纯文本</td><td><code>video.Video().get_comments()</code></td><td class="desc">用于 NLP 情感计算极性(正向/负向)</td><td><span class="g">✅ 全量抽取无尽长尾评论</span></td></tr>
        <tr><td>被点赞数 (Like)</td><td><code>video.Video().get_comments()</code></td><td class="desc">作为该条神评在玩家群中影响力的权重</td><td><span class="g">✅ 全量抽取无尽长尾评论</span></td></tr>
        <tr><td>公开收藏夹</td><td><code>get_video_favorite_list(uid)</code></td><td class="desc">反向暴露这名核心玩家它游心智偏好</td><td><span class="g">✅ 若用户公开即完全采集</span></td></tr>
        <tr><td>关注关系链</td><td><code>API /x/relation/followings</code></td><td class="desc">挖掘订阅重合度及竞品官方追随意向</td><td><span class="g">✅ 解除屏蔽获得高阶权限</span></td></tr>"""
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
        iframe_height = 420
        rows = """
        <tr><td>多端防风控突破口</td><td><code>Playwright / JS 逆向解构</code></td><td class="desc">扫码与无头浏览器组合拳完全粉碎抖音/小黑盒墙盾</td><td><span class="y">⚠️ 极强风控：拒绝一切免登</span></td></tr>
        <tr><td>原生沙盒进程调度</td><td><code>subprocess.run('main.py')</code></td><td class="desc">基于独立沙盒调用引擎，确保核心主进程完全免疫崩溃</td><td><span class="g">✅ 本地终端环境独占放行</span></td></tr>
        <tr><td>原生数据统一清洗</td><td><code>MediaCrawlerBridge.import...</code></td><td class="desc">将外来杂乱字典映射并同构组装回 VideoSnapshot 规范</td><td><span class="g">✅ 聚合入库，免数据分裂</span></td></tr>
        <tr><td>精准瀑布流拦截</td><td><code>aweme_id / note_id 下发</code></td><td class="desc">极速阻击竞品短视频买量黑马，提取标题与播放池基数</td><td><span class="g">✅ 彻底剥离落盘分析</span></td></tr>
        <tr><td>种草神评长尾拦截</td><td><code>comment_id 万级穿透</code></td><td class="desc">提取抖音与红书下的真实用户评价，汇聚最强舆情宣泄口</td><td><span class="g">✅ 完整挂载至下属文件树</span></td></tr>
        <tr><td>发帖/点赞/收藏数</td><td><code>CSV 二次解包聚合</code></td><td class="desc">重塑买量平台在短视频维度的社交传播穿透力</td><td><span class="g">✅ 全量导出归入系统仓库</span></td></tr>"""

    matrix_html = matrix_html_base + rows + "</tbody></table></body></html>"
    
    st.markdown(f"<div style='margin-top:1.5rem; margin-bottom:8px; display:flex; justify-content:space-between; align-items:flex-end;'><div><p style='font-size:14px; color:#111; font-weight:600; margin:0;'>当前选中模式探针约束矩阵</p></div><div style='font-size:12px; color:#666;'>{comp_title}</div></div>", unsafe_allow_html=True)
    st_components.html(matrix_html, height=iframe_height, scrolling=False)

    st.markdown("<br/>", unsafe_allow_html=True)
    if st.button(f"启动 {platform.capitalize()} 采集链路", type="primary"):
        m_val = "actions" if "基础免登录" in mode else "local"
        with st.spinner(f"探测器正在后台接入 {platform.capitalize()} 信息流，通常耗时一至两分钟，请勿刷新页面..."):
            stdout, stderr, code = run_cli(["crawl", "--platform", platform, "--mode", m_val])
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

elif page == "扩词":
    import os
    st.markdown("<h1>知识网扩写</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>根据 `keywords.yaml` 的种子源，利用 AI 实现营销话术的深层泛化。</p>", unsafe_allow_html=True)
    
    api_k = os.environ.get("DEEPSEEK_API_KEY", "")
    
    c1, c2 = st.columns(2)
    with c1: provider = st.selectbox("神经网提供方", ["deepseek", "openai", "qwen"])
    with c2: max_k = st.slider("边界容量阀值", 10, 100, 50)
    
    if api_k:
        st.markdown("<p style='font-size: 14px; color: #16a34a; font-weight: 500;'>环境检测通过：DEEPSEEK_API_KEY 已发现。</p>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ 缺少大语言模型认知层 (DEEPSEEK_API_KEY)。扩词调度已被安全隔离控制，请通过「设置」面板注入环境变量后再试。")
        
    if st.button("启动深度知识关联投射", type="primary", disabled=bool(not api_k)):
        with st.spinner("AI 正在解析目标赛道同义映射表并生成拓补集合..."):
            stdout, _, code = run_cli(["expand-keywords", "--provider", provider, "--max-keywords", str(max_k)])
        if code == 0: 
            st.success("✅ 扩词网络编排完成，衍生词条已被更新至环境上下文。")
            st.code(stdout, language="json")
        else:
            st.error("执行崩溃，发生异常。")

elif page == "设置":
    import os
    st.markdown("<h1>系统设置</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 14px; margin-bottom: 2rem;'>直接在下方编辑配置内容，点击保存后立即生效，无需修改代码。</p>", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["追踪目标 (targets.yaml)", "关键词库 (keywords.yaml)", "运行环境变量"])

    with t1:
        targets_data = load_yaml(TARGETS_FILE)
        if "targets" not in targets_data: targets_data["targets"] = {}
        t_data = targets_data["targets"]

        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1.5rem;'>在表格单元格双击可直接修改追踪目标。在末尾空白行输入即可新增，选中行按 Delete 键可删除。编辑完成后点击底部保存。</p>", unsafe_allow_html=True)
        
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

        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1.5rem;'>双击单元格可修改或新增系统追踪关键词（支持按 Delete 键删除行）。</p>", unsafe_allow_html=True)

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
        st.markdown("##### 🤖 AI 扩词配置")
        exp = kw_data.get("expansion", {})
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            exp_enabled = st.toggle("启用自动扩词", value=exp.get("enabled", True))
        with cc2:
            exp_provider = st.selectbox("LLM Provider", ["deepseek", "openai", "qwen"], index=["deepseek", "openai", "qwen"].index(exp.get("llm_provider", "deepseek")) if exp.get("llm_provider", "deepseek") in ["deepseek", "openai", "qwen"] else 0)
        with cc3:
            exp_max = st.number_input("最大扩展词数", min_value=10, max_value=200, value=exp.get("max_expanded_keywords", 50))

        if st.button("保存 Keywords 配置", type="primary"):
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
                st.success("🎉 keywords.yaml 已保存！下次运行将使用新配置。")
            except Exception as e:
                st.error(f"保存失败：{e}")

    with t3:
        st.markdown("<p style='font-size:13px; color:#666; margin-bottom:1rem;'>当前进程中已加载的关键环境变量状态。如需修改，请在终端中 <code>export KEY=value</code> 后重启 GUI。</p>", unsafe_allow_html=True)
        env_vars = [
            ("DEEPSEEK_API_KEY", "AI 关键词扩展 / 情感增强"),
            ("BILI_SESSDATA", "B站深度评论采集（Cookie）"),
            ("MEDIA_CRAWLER_DIR", "MediaCrawler 本地数据目录"),
        ]
        rows = ""
        for k, desc in env_vars:
            v = os.environ.get(k, "")
            status = f'<span style="color:#16a34a; font-weight:600;">已配置</span>' if v else f'<span style="color:#dc2626;">未配置</span>'
            masked = v[:6] + "..." if len(v) > 6 else ("—" if not v else v)
            rows += f'<tr style="border-bottom:1px solid #F0F0F0;"><td style="padding:12px 16px; font-size:13px; font-family:monospace; font-weight:600;">{k}</td><td style="padding:12px 16px; font-size:13px; color:#666;">{desc}</td><td style="padding:12px 16px;">{status}</td><td style="padding:12px 16px; font-size:12px; font-family:monospace; color:#888;">{masked}</td></tr>'
        st.markdown(f"""
        <div style="background:#fff;border:1px solid #EAEAEA;border-radius:8px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#FAFAFA;border-bottom:2px solid #EAEAEA;">
                <th style="padding:10px 16px;font-size:12px;color:#666;font-weight:500;text-align:left;">变量名</th>
                <th style="padding:10px 16px;font-size:12px;color:#666;font-weight:500;text-align:left;">用途</th>
                <th style="padding:10px 16px;font-size:12px;color:#666;font-weight:500;">状态</th>
                <th style="padding:10px 16px;font-size:12px;color:#666;font-weight:500;">值预览</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table></div>
        """, unsafe_allow_html=True)
