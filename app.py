"""
SLG Sentinel — 竞品舆情监控指挥台
"""

import streamlit as st

from ui.pages.competitor import render_competitor_page
from ui.pages.crawl import render_crawl_page
from ui.pages.overview import render_overview_page
from ui.pages.profile import render_profile_page
from ui.pages.recursive_crawl import render_recursive_crawl_page
from ui.pages.report import render_report_page
from ui.pages.settings import render_settings_page

st.set_page_config(
    page_title="SLG Sentinel | 竞品舆情指挥台",
    page_icon="cloudflare_pages/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 全局 CSS — War Atlas 视觉系统复刻
# 设计令牌直接提取自 war-atlas.org 生产 CSS
# 字体：Cinzel (标题) + IBM Plex Sans (正文) + IBM Plex Mono (数据)
# 色板：#0a0c10 底 · #e8e4dc 文 · #d4af37 金色
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ═══════════════════════════════════════════════════
   War Atlas 设计令牌（从 war-atlas.org CSS 提取）
   ═══════════════════════════════════════════════════ */
:root {
    --wa-bg: #0a0c10;
    --wa-panel: rgba(12, 15, 20, 0.92);
    --wa-panel-hover: rgba(18, 22, 30, 0.95);
    --wa-border: rgba(180, 160, 120, 0.15);
    --wa-border-accent: rgba(212, 175, 55, 0.4);
    --wa-text: #e8e4dc;
    --wa-text-2: rgba(232, 228, 220, 0.6);
    --wa-text-3: rgba(232, 228, 220, 0.4);
    --wa-gold: #d4af37;
    --wa-red: #e85d4a;
    --wa-green: #5b9a6e;
    --wa-blue: #6b8bdb;
    --wa-shadow: 0 4px 24px rgba(0,0,0,.4), 0 1px 2px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.03);
    --wa-glow: 0 0 20px rgba(212, 175, 55, 0.12);
    --wa-font-display: 'Cinzel', serif;
    --wa-font-body: 'IBM Plex Sans', sans-serif;
    --wa-font-mono: 'IBM Plex Mono', monospace;
}

/* ── 全局 ────────────────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: var(--wa-font-body) !important;
    background-color: var(--wa-bg) !important;
    color: var(--wa-text) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.stApp { background: var(--wa-bg) !important; }

/* ── 顶栏 & 页脚 ────────────────────────────────── */
header[data-testid="stHeader"] { background: transparent !important; }
footer { visibility: hidden !important; display: none !important; }
[data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] { display: none !important; }

/* ── 侧边栏 ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0f14 0%, var(--wa-bg) 100%) !important;
    border-right: 1px solid var(--wa-border) !important;
    width: 200px !important; min-width: 200px !important; max-width: 200px !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--wa-text-3) !important; font-size: 12px !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 10px 14px; border-radius: 4px; cursor: pointer;
    color: var(--wa-text-2) !important; font-size: 12px !important;
    font-weight: 500 !important; transition: all 0.15s ease;
    border: 1px solid transparent;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(212,175,55,0.06) !important;
    color: var(--wa-text) !important; border-color: rgba(212,175,55,0.12);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] [aria-checked="true"] {
    background: rgba(212,175,55,0.1) !important;
    color: var(--wa-gold) !important; border-color: rgba(212,175,55,0.3) !important;
}

/* ── 主区域间距 ──────────────────────────────────── */
.block-container {
    padding-top: 1.2rem !important; padding-left: 2rem !important;
    padding-right: 2rem !important; max-width: 100% !important;
}

/* ── 标题 (Cinzel) ───────────────────────────────── */
h1 {
    font-family: var(--wa-font-display) !important; font-weight: 700 !important;
    font-size: 26px !important; letter-spacing: 3px !important;
    color: var(--wa-text) !important; margin-bottom: 4px !important;
    text-transform: uppercase;
}
h2 {
    font-family: var(--wa-font-display) !important; font-weight: 600 !important;
    font-size: 18px !important; letter-spacing: 2px !important;
    color: var(--wa-text) !important; text-transform: uppercase;
}
h3 {
    font-family: var(--wa-font-display) !important; font-weight: 600 !important;
    font-size: 14px !important; letter-spacing: 1.5px !important;
    color: rgba(232,228,220,0.85) !important; margin-top: 1.5rem !important;
    text-transform: uppercase;
}
h4, h5 {
    font-family: var(--wa-font-body) !important; font-weight: 600 !important;
    color: rgba(232,228,220,0.8) !important; letter-spacing: 0.5px !important;
}

/* ── Metric 卡片 ─────────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--wa-panel) !important; border: 1px solid var(--wa-border) !important;
    border-radius: 8px !important; padding: 24px !important;
    box-shadow: var(--wa-shadow) !important;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    transition: all 0.25s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: var(--wa-border-accent) !important;
    box-shadow: var(--wa-shadow), var(--wa-glow) !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 11px !important; font-weight: 600 !important;
    color: var(--wa-text-3) !important; text-transform: uppercase; letter-spacing: 1.2px;
}
div[data-testid="stMetricValue"] {
    font-family: var(--wa-font-mono) !important; font-size: 32px !important;
    font-weight: 500 !important; color: var(--wa-text) !important;
}

/* ── 主按钮 (金色) ───────────────────────────────── */
button[kind="primary"] {
    background: linear-gradient(135deg, #d4af37, #b8962e) !important;
    color: var(--wa-bg) !important; border-radius: 4px !important; border: none !important;
    font-family: var(--wa-font-body) !important; font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important; font-size: 11px !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(212,175,55,0.2) !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #e0bf4a, #c8a63e) !important;
    box-shadow: 0 4px 16px rgba(212,175,55,0.3), var(--wa-glow) !important;
    transform: translateY(-1px);
}
button[kind="secondary"], button:not([kind]) {
    background: transparent !important; color: var(--wa-text-2) !important;
    border: 1px solid var(--wa-border) !important; border-radius: 4px !important;
    font-size: 12px !important; transition: all 0.15s ease !important;
}
button[kind="secondary"]:hover, button:not([kind]):hover {
    border-color: var(--wa-border-accent) !important;
    color: var(--wa-text) !important; background: rgba(212,175,55,0.06) !important;
}

/* ── Tab 导航 ────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--wa-border); gap: 24px; }
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--wa-text-3) !important;
    font-family: var(--wa-font-body) !important; font-weight: 500 !important;
    font-size: 11px !important; height: 40px; border: none !important;
    letter-spacing: 0.8px; text-transform: uppercase; transition: color 0.15s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--wa-text-2) !important; }
.stTabs [aria-selected="true"] {
    color: var(--wa-gold) !important; border-bottom: 2px solid var(--wa-gold) !important;
}

/* ── 表格 ────────────────────────────────────────── */
.stMarkdown table {
    width: 100%; background: rgba(12,15,20,0.7);
    border: 1px solid var(--wa-border) !important; border-radius: 8px !important;
    border-collapse: separate !important; border-spacing: 0;
}
.stMarkdown th {
    background: rgba(180,160,120,0.05) !important;
    font-family: var(--wa-font-body) !important; font-weight: 600 !important;
    font-size: 10px !important; color: var(--wa-text-3) !important;
    text-transform: uppercase !important; letter-spacing: 1.2px !important;
    border-bottom: 1px solid var(--wa-border) !important; padding: 12px 16px !important;
}
.stMarkdown td {
    padding: 12px 16px !important; font-size: 12px !important;
    color: rgba(232,228,220,0.7) !important;
    border-bottom: 1px solid rgba(180,160,120,0.05) !important;
}
.stMarkdown tr:last-child td { border-bottom: none !important; }
.stMarkdown tr:hover td { background: rgba(212,175,55,0.03) !important; }

/* ── Dataframe ───────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--wa-border) !important; border-radius: 8px !important;
}

/* ── 输入控件 ────────────────────────────────────── */
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"],
.stTextInput input, .stTextArea textarea,
.stNumberInput input, .stDateInput input {
    background: rgba(0,0,0,0.3) !important; border: 1px solid var(--wa-border) !important;
    color: var(--wa-text) !important; border-radius: 4px !important;
    font-family: var(--wa-font-body) !important; font-size: 12px !important;
    transition: all 0.15s ease;
}
.stTextInput input:focus, .stTextArea textarea:focus,
.stNumberInput input:focus, .stDateInput input:focus {
    border-color: var(--wa-border-accent) !important;
    box-shadow: 0 0 0 2px rgba(212,175,55,0.08) !important;
}
[data-baseweb="popover"] {
    background: rgba(12,15,20,0.96) !important; border: 1px solid var(--wa-border) !important;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
[data-baseweb="menu"] { background: rgba(12,15,20,0.96) !important; }
[role="option"] { color: rgba(232,228,220,0.7) !important; font-size: 12px !important; }
[role="option"]:hover { background: rgba(212,175,55,0.06) !important; }

/* ── 通知 & 警告 ─────────────────────────────────── */
.stAlert, div[data-testid="stNotification"] {
    background: var(--wa-panel) !important; border: 1px solid var(--wa-border) !important;
    border-radius: 8px !important; color: rgba(232,228,220,0.8) !important;
}

/* ── Divider / Expander ──────────────────────────── */
hr { border-color: rgba(180,160,120,0.08) !important; }
.streamlit-expanderHeader { color: var(--wa-text-2) !important; font-size: 12px !important; }
details[data-testid="stExpander"] {
    border: 1px solid rgba(180,160,120,0.08) !important;
    background: rgba(12,15,20,0.5) !important; border-radius: 8px !important;
}

/* ── 进度条 & Spinner ────────────────────────────── */
.stProgress > div > div { background: linear-gradient(90deg, #d4af37, #b8962e) !important; }
.stSpinner > div { border-top-color: var(--wa-gold) !important; }

/* ── 自定义滚动条 (War Atlas 提取) ────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(180,160,120,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--wa-gold); }

/* ── 入场动画 (War Atlas 提取) ────────────────────── */
@keyframes waFadeIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes waSlideUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
.block-container > div { animation: waFadeIn 0.3s ease forwards; }

/* ── 容器边框 (st.container(border=True)) ────────── */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--wa-border) !important; border-radius: 8px !important;
    background: rgba(12,15,20,0.5) !important;
    box-shadow: var(--wa-shadow) !important;
    backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
}

/* ── Widget 标签 ─────────────────────────────────── */
[data-testid="stWidgetLabel"] p {
    font-size: 10px !important; font-weight: 600 !important;
    color: var(--wa-text-3) !important; text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

/* ── Radio 修复 / 平台图标 ────────────────────────── */
.stRadio [role="radiogroup"] { gap: 2px; }
.platform-icon { width: 16px; height: 16px; vertical-align: text-bottom; margin-right: 6px; border-radius: 2px; opacity: 0.8; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# 侧边栏
# ---------------------------------------------------------------------------
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
        <div style='display:flex; align-items:center; margin-bottom:2rem; padding:1rem 0; border-bottom:1px solid rgba(180,160,120,0.1);'>
            <div style='width:32px; height:32px; margin-right:12px; flex-shrink:0;'>
                <svg width="100%" height="100%" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="256" cy="256" r="256" fill="#141820" stroke="rgba(212,175,55,0.3)" stroke-width="4"/>
                    <g transform="scale(0.8) translate(64, 64)">
                        <path d="M255.968 288.494L166.211 241.067L10.4062 158.753C10.2639 158.611 9.97951 158.611 9.83728 158.611C4.14838 155.909 -1.68275 161.596 0.450591 167.283L79.8393 369.685L79.8535 369.728C79.9388 369.927 80.0099 370.126 80.0953 370.325C83.3522 377.874 90.4633 382.537 98.2002 384.371C98.8544 384.513 99.3225 384.643 100.108 384.799C100.89 384.973 101.983 385.21 102.922 385.281C103.078 385.295 103.221 385.295 103.377 385.31H103.491C103.605 385.324 103.718 385.324 103.832 385.338H103.989C104.088 385.352 104.202 385.352 104.302 385.352H104.486C104.6 385.366 104.714 385.366 104.828 385.366L167.175 392.161C226.276 398.602 285.901 398.602 345.002 392.161L407.35 385.366C408.558 385.366 409.739 385.31 410.877 385.196C411.246 385.153 411.602 385.111 411.958 385.068C412 385.054 412.057 385.054 412.1 385.039C412.342 385.011 412.583 384.968 412.825 384.926C413.181 384.883 413.536 384.812 413.892 384.741C414.603 384.585 414.926 384.471 415.891 384.139C416.856 383.808 418.458 383.228 419.461 382.745C420.464 382.261 421.159 381.798 421.999 381.272C423.037 380.618 424.024 379.948 425.025 379.198C425.457 378.868 425.753 378.656 426.066 378.358L425.895 378.258L255.968 288.494Z" fill="#d4af37"/>
                        <path d="M501.789 158.755H501.647L345.784 241.07L432.426 370.058L511.616 167.285V167.001C513.607 161.03 507.492 155.627 501.789 158.755" fill="#8C7A5E"/>
                        <path d="M264.274 119.615C260.292 113.8 251.616 113.8 247.776 119.615L166.211 241.068L255.968 288.495L426.067 378.357C427.135 377.312 427.991 376.293 428.897 375.217C430.177 373.638 431.372 371.947 432.424 370.056L345.782 241.068L264.274 119.615Z" fill="#D4C9B0"/>
                    </g>
                </svg>
            </div>
            <div>
                <div style='font-family:Cinzel,serif; font-size:14px; font-weight:700; color:#E8E4DC; letter-spacing:2px;'>SLG SENTINEL</div>
                <div style='font-size:9px; color:rgba(232,228,220,0.3); letter-spacing:2px; text-transform:uppercase; margin-top:2px; font-family:IBM Plex Sans,sans-serif;'>Intelligence Platform</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "应用导航",
            ["总览", "采集", "递归采集", "画像", "智能报表", "竞品对比", "设置"],
            label_visibility="collapsed",
        )
        st.markdown("<br/>", unsafe_allow_html=True)
        return page


page = render_sidebar()

if page == "总览":
    render_overview_page()
elif page == "采集":
    render_crawl_page()
elif page == "递归采集":
    render_recursive_crawl_page()
elif page == "画像":
    render_profile_page()
elif page == "智能报表":
    render_report_page()
elif page == "竞品对比":
    render_competitor_page()
elif page == "设置":
    render_settings_page()
