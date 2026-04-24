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
# 全局 CSS — War-Atlas 风格暗色主题
# 字体：Cinzel (标题) + IBM Plex Sans (正文) + IBM Plex Mono (数据)
# 色板：#0A0C10 底 · #E8E4DC 文 · #B4A078 金色强调
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');

/* ── 全局底色 & 字体 ─────────────────────────────── */
html, body, [class*="css"], .stApp {
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: #0A0C10 !important;
    color: #E8E4DC !important;
}
.stApp { background: #0A0C10 !important; }

/* ── 顶栏 & 页脚隐藏 ────────────────────────────── */
header[data-testid="stHeader"] { background: transparent !important; }
footer { visibility: hidden !important; display: none !important; }
[data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] { display: none !important; }

/* ── 侧边栏 ─────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0F14 0%, #0A0C10 100%) !important;
    border-right: 1px solid rgba(180, 160, 120, 0.12) !important;
    width: 200px !important;
    min-width: 200px !important;
    max-width: 200px !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: rgba(232, 228, 220, 0.5) !important;
    font-size: 12px !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 10px 14px;
    border-radius: 6px;
    cursor: pointer;
    color: rgba(232, 228, 220, 0.65) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
    border: 1px solid transparent;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(180, 160, 120, 0.08) !important;
    color: #E8E4DC !important;
    border-color: rgba(180, 160, 120, 0.15);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] [aria-checked="true"] {
    background: rgba(180, 160, 120, 0.12) !important;
    color: #B4A078 !important;
    border-color: rgba(180, 160, 120, 0.25) !important;
}
/* 侧边栏 radio 圆点颜色 */
section[data-testid="stSidebar"] div[role="radiogroup"] [data-testid="stWidgetLabel"] {
    color: rgba(232, 228, 220, 0.5) !important;
}

/* ── 主区域间距 ──────────────────────────────────── */
.block-container {
    padding-top: 1.2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 100% !important;
}

/* ── 标题体系 (Cinzel Serif) ──────────────────────── */
h1 {
    font-family: 'Cinzel', 'Times New Roman', serif !important;
    font-weight: 700 !important;
    font-size: 28px !important;
    letter-spacing: 2px !important;
    color: #E8E4DC !important;
    margin-bottom: 6px !important;
    text-transform: uppercase;
}
h2 {
    font-family: 'Cinzel', serif !important;
    font-weight: 600 !important;
    font-size: 20px !important;
    letter-spacing: 1.5px !important;
    color: #E8E4DC !important;
}
h3 {
    font-family: 'Cinzel', serif !important;
    font-weight: 600 !important;
    font-size: 17px !important;
    letter-spacing: 1px !important;
    color: rgba(232, 228, 220, 0.9) !important;
    margin-top: 1.5rem !important;
}
h4, h5 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    color: rgba(232, 228, 220, 0.85) !important;
    letter-spacing: 0.5px !important;
}

/* ── Metric 卡片 ─────────────────────────────────── */
div[data-testid="stMetric"] {
    background: rgba(12, 15, 20, 0.92) !important;
    border: 1px solid rgba(180, 160, 120, 0.15) !important;
    border-radius: 8px !important;
    padding: 24px !important;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3) !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: rgba(232, 228, 220, 0.5) !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}
div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 32px !important;
    font-weight: 500 !important;
    color: #E8E4DC !important;
    margin-top: 4px;
}

/* ── 主按钮 (金色强调) ───────────────────────────── */
button[kind="primary"] {
    background: linear-gradient(135deg, #B4A078, #8C7A5E) !important;
    color: #0A0C10 !important;
    border-radius: 6px !important;
    border: none !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.6rem !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 8px rgba(180, 160, 120, 0.2) !important;
}
button[kind="primary"]:hover {
    background: linear-gradient(135deg, #C4B088, #9C8A6E) !important;
    box-shadow: 0 4px 16px rgba(180, 160, 120, 0.35) !important;
    transform: translateY(-1px);
}
/* 次级按钮 */
button[kind="secondary"], button:not([kind]) {
    background: transparent !important;
    color: rgba(232, 228, 220, 0.7) !important;
    border: 1px solid rgba(180, 160, 120, 0.2) !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    transition: all 0.2s ease !important;
}
button[kind="secondary"]:hover, button:not([kind]):hover {
    border-color: rgba(180, 160, 120, 0.4) !important;
    color: #E8E4DC !important;
    background: rgba(180, 160, 120, 0.06) !important;
}

/* ── Tab 导航 ────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 1px solid rgba(180, 160, 120, 0.12);
    gap: 28px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(232, 228, 220, 0.45) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    height: 44px;
    border: none !important;
    letter-spacing: 0.3px;
    transition: color 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    color: rgba(232, 228, 220, 0.8) !important;
}
.stTabs [aria-selected="true"] {
    color: #B4A078 !important;
    border-bottom: 2px solid #B4A078 !important;
}

/* ── 表格 ────────────────────────────────────────── */
.stMarkdown table {
    width: 100%;
    background: rgba(12, 15, 20, 0.8);
    border: 1px solid rgba(180, 160, 120, 0.12) !important;
    border-radius: 8px !important;
    border-collapse: separate !important;
    border-spacing: 0;
    margin-top: 0.8rem;
}
.stMarkdown th {
    background: rgba(180, 160, 120, 0.06) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    color: rgba(232, 228, 220, 0.5) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    border-bottom: 1px solid rgba(180, 160, 120, 0.12) !important;
    padding: 12px 16px !important;
    text-align: left;
}
.stMarkdown td {
    padding: 14px 16px !important;
    font-size: 13px !important;
    color: rgba(232, 228, 220, 0.8) !important;
    border-bottom: 1px solid rgba(180, 160, 120, 0.06) !important;
}
.stMarkdown tr:last-child td { border-bottom: none !important; }
.stMarkdown tr:hover td { background: rgba(180, 160, 120, 0.04) !important; }

/* ── Dataframe 表格 ──────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(180, 160, 120, 0.12) !important;
    border-radius: 8px !important;
}

/* ── 输入框 / 选择器 / 文本域 ─────────────────────── */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
.stTextInput input, .stTextArea textarea,
.stNumberInput input, .stDateInput input {
    background: rgba(12, 15, 20, 0.9) !important;
    border: 1px solid rgba(180, 160, 120, 0.15) !important;
    color: #E8E4DC !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
.stSelectbox [data-baseweb="select"]:hover,
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(180, 160, 120, 0.35) !important;
}
/* 下拉菜单 */
[data-baseweb="popover"] {
    background: #12151B !important;
    border: 1px solid rgba(180, 160, 120, 0.15) !important;
}
[data-baseweb="menu"] {
    background: #12151B !important;
}
[role="option"] {
    color: rgba(232, 228, 220, 0.8) !important;
}
[role="option"]:hover {
    background: rgba(180, 160, 120, 0.1) !important;
}

/* ── 警告/信息条 ─────────────────────────────────── */
.stAlert {
    background: rgba(12, 15, 20, 0.9) !important;
    border: 1px solid rgba(180, 160, 120, 0.15) !important;
    border-radius: 8px !important;
    color: rgba(232, 228, 220, 0.8) !important;
}
div[data-testid="stNotification"] {
    background: rgba(12, 15, 20, 0.9) !important;
    border: 1px solid rgba(180, 160, 120, 0.15) !important;
    color: rgba(232, 228, 220, 0.8) !important;
}

/* ── Divider / Expander ──────────────────────────── */
hr { border-color: rgba(180, 160, 120, 0.1) !important; }
.streamlit-expanderHeader {
    color: rgba(232, 228, 220, 0.7) !important;
    font-size: 13px !important;
}
details[data-testid="stExpander"] {
    border: 1px solid rgba(180, 160, 120, 0.1) !important;
    background: rgba(12, 15, 20, 0.6) !important;
    border-radius: 8px !important;
}

/* ── 进度条 ──────────────────────────────────────── */
.stProgress > div > div {
    background: linear-gradient(90deg, #B4A078, #8C7A5E) !important;
}

/* ── Spinner ─────────────────────────────────────── */
.stSpinner > div { border-top-color: #B4A078 !important; }

/* ── 通用面板类 (供内联 HTML 使用) ─────────────────── */
.sentinel-panel {
    background: rgba(12, 15, 20, 0.92);
    border: 1px solid rgba(180, 160, 120, 0.15);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
}
.sentinel-kpi {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 500;
    color: #E8E4DC;
    line-height: 1;
}
.sentinel-label {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 11px;
    font-weight: 500;
    color: rgba(232, 228, 220, 0.45);
    text-transform: uppercase;
    letter-spacing: 1px;
}
.sentinel-gold { color: #B4A078; }
.sentinel-red  { color: #E85D4A; }
.sentinel-green { color: #5B9A6E; }
.sentinel-border-gold { border-left: 3px solid #B4A078; }
.sentinel-border-red  { border-left: 3px solid #E85D4A; }
.sentinel-border-green { border-left: 3px solid #5B9A6E; }

/* ── 平台图标 ────────────────────────────────────── */
.platform-icon {
    width: 16px; height: 16px;
    vertical-align: text-bottom;
    margin-right: 6px;
    border-radius: 2px;
    opacity: 0.8;
}

/* ── Radio 圆点不可见时的修复 ────────────────────── */
.stRadio [role="radiogroup"] {
    gap: 2px;
}
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
                    <circle cx="256" cy="256" r="256" fill="#141820" stroke="rgba(180,160,120,0.3)" stroke-width="4"/>
                    <g transform="scale(0.8) translate(64, 64)">
                        <path d="M255.968 288.494L166.211 241.067L10.4062 158.753C10.2639 158.611 9.97951 158.611 9.83728 158.611C4.14838 155.909 -1.68275 161.596 0.450591 167.283L79.8393 369.685L79.8535 369.728C79.9388 369.927 80.0099 370.126 80.0953 370.325C83.3522 377.874 90.4633 382.537 98.2002 384.371C98.8544 384.513 99.3225 384.643 100.108 384.799C100.89 384.973 101.983 385.21 102.922 385.281C103.078 385.295 103.221 385.295 103.377 385.31H103.491C103.605 385.324 103.718 385.324 103.832 385.338H103.989C104.088 385.352 104.202 385.352 104.302 385.352H104.486C104.6 385.366 104.714 385.366 104.828 385.366L167.175 392.161C226.276 398.602 285.901 398.602 345.002 392.161L407.35 385.366C408.558 385.366 409.739 385.31 410.877 385.196C411.246 385.153 411.602 385.111 411.958 385.068C412 385.054 412.057 385.054 412.1 385.039C412.342 385.011 412.583 384.968 412.825 384.926C413.181 384.883 413.536 384.812 413.892 384.741C414.603 384.585 414.926 384.471 415.891 384.139C416.856 383.808 418.458 383.228 419.461 382.745C420.464 382.261 421.159 381.798 421.999 381.272C423.037 380.618 424.024 379.948 425.025 379.198C425.457 378.868 425.753 378.656 426.066 378.358L425.895 378.258L255.968 288.494Z" fill="#B4A078"/>
                        <path d="M501.789 158.755H501.647L345.784 241.07L432.426 370.058L511.616 167.285V167.001C513.607 161.03 507.492 155.627 501.789 158.755" fill="#8C7A5E"/>
                        <path d="M264.274 119.615C260.292 113.8 251.616 113.8 247.776 119.615L166.211 241.068L255.968 288.495L426.067 378.357C427.135 377.312 427.991 376.293 428.897 375.217C430.177 373.638 431.372 371.947 432.424 370.056L345.782 241.068L264.274 119.615Z" fill="#D4C9B0"/>
                    </g>
                </svg>
            </div>
            <div>
                <div style='font-family:Cinzel,serif; font-size:14px; font-weight:700; color:#E8E4DC; letter-spacing:2px;'>SLG SENTINEL</div>
                <div style='font-size:10px; color:rgba(232,228,220,0.35); letter-spacing:1.5px; text-transform:uppercase; margin-top:2px;'>Intelligence Platform</div>
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
