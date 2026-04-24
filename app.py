"""
SLG Sentinel — 竞品舆情监控指挥台
"""

import streamlit as st
from urllib.parse import quote

from ui.i18n import alternate_locale, current_locale, page_id_from_query, t
from ui.pages.competitor import render_competitor_page
from ui.pages.crawl import render_crawl_page
from ui.pages.overview import render_overview_page
from ui.pages.profile import render_profile_page
from ui.pages.recursive_crawl import render_recursive_crawl_page
from ui.pages.report import render_report_page
from ui.pages.settings import render_settings_page

st.set_page_config(
    page_title="SLG Sentinel | Competitive Intelligence Command",
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
    display: none !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: var(--wa-text-3) !important; font-size: 12px !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    padding: 10px 14px; border-radius: 4px; cursor: pointer;
    color: var(--wa-text-2) !important; font-size: 12px !important;
    font-weight: 500 !important; transition: all 0.15s ease;
    border: 1px solid transparent;
    margin: 2px 0 !important;
    min-height: 38px;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label p {
    color: inherit !important;
    font-size: 12px !important;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(212,175,55,0.06) !important;
    color: var(--wa-text) !important; border-color: rgba(212,175,55,0.12);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked),
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has([aria-checked="true"]),
section[data-testid="stSidebar"] [aria-checked="true"] {
    background: rgba(212,175,55,0.1) !important;
    color: var(--wa-gold) !important; border-color: rgba(212,175,55,0.3) !important;
}

/* ── 主区域间距 ──────────────────────────────────── */
.block-container {
    padding-top: 1.2rem !important; padding-left: 1.35rem !important;
    padding-right: 1.35rem !important; max-width: 100% !important;
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
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
[data-baseweb="select"] > div {
    background: rgba(12,15,20,0.86) !important;
    border-color: rgba(180,160,120,0.18) !important;
    color: var(--wa-text) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03) !important;
}
.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span,
[data-baseweb="select"] span {
    color: rgba(232,228,220,0.78) !important;
}
.stSelectbox [data-baseweb="select"] svg,
.stMultiSelect [data-baseweb="select"] svg,
[data-baseweb="select"] svg {
    fill: rgba(232,228,220,0.72) !important;
}
.stTextInput input, .stTextArea textarea,
.stNumberInput input, .stDateInput input {
    background: rgba(12,15,20,0.86) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {
    color: rgba(232,228,220,0.28) !important;
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

/* ── Atlas 共享页面组件 ───────────────────────────── */
.atlas-global-nav {
    position: sticky;
    top: 8px;
    z-index: 30;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 18px;
    align-items: center;
    margin: 0 0 18px 0;
    padding: 10px 12px 10px 18px;
    border: 1px solid rgba(180,160,120,0.16);
    border-radius: 8px;
    background: rgba(12,15,20,0.78);
    box-shadow: 0 16px 44px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
}
.atlas-global-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 210px;
}
.atlas-global-mark {
    width: 34px;
    height: 34px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: #141820;
    border: 1px solid rgba(212,175,55,0.22);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), 0 0 18px rgba(212,175,55,0.08);
}
.atlas-global-title {
    font-family: var(--wa-font-display);
    font-weight: 700;
    font-size: 19px;
    line-height: 1;
    letter-spacing: 2.8px;
    color: #f0eee8;
}
.atlas-global-sub {
    margin-top: 4px;
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.6px;
    color: rgba(232,228,220,0.34);
    text-transform: uppercase;
}
.atlas-global-links {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    overflow-x: auto;
    scrollbar-width: none;
}
.atlas-global-links::-webkit-scrollbar { display: none; }
.atlas-global-link {
    display: inline-flex;
    align-items: center;
    height: 34px;
    white-space: nowrap;
    padding: 0 14px;
    border: 1px solid rgba(180,160,120,0.13);
    border-radius: 5px;
    background: rgba(10,12,16,0.38);
    color: rgba(232,228,220,0.58);
    text-decoration: none !important;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all .15s ease;
}
.atlas-global-link:visited,
.atlas-global-link:active,
.atlas-global-link:focus {
    color: rgba(232,228,220,0.58);
}
.atlas-global-link:hover {
    color: #e8e4dc;
    border-color: rgba(212,175,55,0.35);
    background: rgba(212,175,55,0.07);
}
.atlas-global-link.is-active {
    color: var(--wa-gold);
    border-color: rgba(212,175,55,0.55);
    background: rgba(212,175,55,0.13);
    box-shadow: 0 0 18px rgba(212,175,55,0.08);
}
.atlas-global-link.is-active:visited,
.atlas-global-link.is-active:active,
.atlas-global-link.is-active:focus {
    color: var(--wa-gold);
}
.atlas-display-chip {
    min-width: 178px;
    padding: 9px 13px;
    border: 1px solid rgba(180,160,120,0.13);
    border-radius: 7px;
    background: rgba(10,12,16,0.45);
}
.atlas-lang-link {
    display: inline-flex;
    justify-content: center;
    margin-top: 6px;
    color: rgba(232,228,220,0.48) !important;
    text-decoration: none !important;
    font-size: 10px;
    letter-spacing: .8px;
    text-transform: uppercase;
}
.atlas-lang-link:hover { color: var(--wa-gold) !important; }
.atlas-display-chip b {
    display: block;
    font-family: var(--wa-font-mono);
    color: var(--wa-gold);
    font-size: 10px;
    letter-spacing: 1.5px;
    margin-bottom: 3px;
}
.atlas-display-chip span {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: rgba(232,228,220,0.52);
    font-size: 10px;
    line-height: 1.45;
}
.atlas-display-chip em {
    color: rgba(232,228,220,0.38);
    font-style: normal;
}
.atlas-display-chip strong {
    color: rgba(232,228,220,0.78);
    font-weight: 500;
    font-family: var(--wa-font-mono);
}
.atlas-page-header {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--wa-border);
    border-radius: 8px;
    min-height: 156px;
    padding: 24px 26px;
    margin-bottom: 22px;
    background:
        linear-gradient(rgba(212,175,55,0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,0.035) 1px, transparent 1px),
        radial-gradient(circle at 78% 34%, rgba(255,75,11,0.11), transparent 18%),
        radial-gradient(circle at 38% 76%, rgba(212,175,55,0.09), transparent 24%),
        rgba(10,12,16,0.88);
    background-size: 72px 72px, 72px 72px, auto, auto, auto;
    box-shadow: 0 18px 52px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.03);
}
.atlas-page-header:before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(24deg, transparent 0 42%, rgba(212,175,55,0.12) 42.1%, transparent 42.4% 100%),
        linear-gradient(-16deg, transparent 0 66%, rgba(212,175,55,0.10) 66.1%, transparent 66.4% 100%);
    opacity: 0.55;
}
.atlas-header-inner {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 22px;
    align-items: start;
}
.atlas-eyebrow {
    font-family: var(--wa-font-mono);
    color: var(--wa-gold);
    font-size: 10px;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.atlas-title {
    font-family: var(--wa-font-display);
    color: #f0eee8;
    font-size: 34px;
    line-height: 0.98;
    letter-spacing: 3px;
    font-weight: 700;
    text-transform: uppercase;
    text-shadow: 0 2px 18px rgba(0,0,0,0.72);
}
.atlas-title-line {
    width: 132px;
    height: 1px;
    margin: 10px 0 0;
    background: linear-gradient(90deg, var(--wa-gold), transparent);
}
.atlas-subtitle {
    max-width: 620px;
    margin-top: 12px;
    color: rgba(232,228,220,0.48);
    font-size: 12px;
    line-height: 1.75;
    letter-spacing: 0.2px;
}
.atlas-header-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(104px, 1fr));
    gap: 9px;
    min-width: min(440px, 42vw);
}
.atlas-stat-chip {
    border: 1px solid rgba(180,160,120,0.13);
    border-radius: 6px;
    background: rgba(12,15,20,0.72);
    padding: 12px 13px;
    backdrop-filter: blur(14px);
    box-shadow: 0 12px 34px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.03);
}
.atlas-stat-label {
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1px;
    color: rgba(232,228,220,0.36);
    text-transform: uppercase;
}
.atlas-stat-value {
    font-family: var(--wa-font-display);
    font-size: 24px;
    line-height: 1;
    letter-spacing: 1px;
    color: #f0eee8;
    margin-top: 8px;
}
.atlas-stat-value.is-gold { color: var(--wa-gold); }
.atlas-header-controls {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 20px;
}
.atlas-header-control {
    height: 32px;
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 0 12px;
    border: 1px solid rgba(180,160,120,0.13);
    border-radius: 5px;
    background: rgba(12,15,20,0.66);
    color: rgba(232,228,220,0.56);
    font-size: 11px;
    font-weight: 600;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
}
.atlas-header-control b {
    color: var(--wa-gold);
    font-family: var(--wa-font-mono);
    font-weight: 500;
}
.atlas-page-range {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 64px minmax(0, 1fr) 76px;
    align-items: center;
    gap: 12px;
    margin-top: 20px;
    max-width: 620px;
    color: rgba(232,228,220,0.34);
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 0.4px;
}
.atlas-page-range-track {
    position: relative;
    height: 10px;
    border-radius: 2px;
    overflow: hidden;
    background: linear-gradient(90deg, rgba(212,175,55,0.20), rgba(212,175,55,0.70));
}
.atlas-page-range-track:before,
.atlas-page-range-track:after {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    width: 1px;
    background: rgba(10,12,16,0.42);
}
.atlas-page-range-track:before { left: 54%; }
.atlas-page-range-track:after { left: 82%; }
.atlas-page-range-thumb {
    position: absolute;
    top: 50%;
    right: 8px;
    width: 14px;
    height: 14px;
    transform: translateY(-50%);
    border-radius: 50%;
    background: #f3dc6b;
    box-shadow: 0 0 15px rgba(243,220,107,0.55);
}
.atlas-hud-panel {
    border: 1px solid rgba(180,160,120,0.15);
    border-radius: 8px;
    background: rgba(12,15,20,0.84);
    box-shadow: var(--wa-shadow);
    backdrop-filter: blur(12px);
}
.atlas-callout {
    border: 1px solid rgba(180,160,120,0.15);
    border-left: 3px solid var(--wa-gold);
    border-radius: 0 8px 8px 0;
    background: rgba(12,15,20,0.82);
    padding: 18px 22px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.02);
}
.atlas-mini-label {
    font-family: var(--wa-font-mono);
    color: rgba(232,228,220,0.36);
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.atlas-body-copy {
    color: rgba(232,228,220,0.58);
    font-size: 12px;
    line-height: 1.8;
}
.atlas-ops-board {
    display: grid;
    grid-template-columns: minmax(0, 1.42fr) minmax(320px, .72fr);
    gap: 14px;
    margin: 0 0 22px 0;
}
.atlas-radar {
    position: relative;
    min-height: 260px;
    overflow: hidden;
    border: 1px solid rgba(180,160,120,0.15);
    border-radius: 8px;
    background:
        linear-gradient(rgba(212,175,55,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,0.03) 1px, transparent 1px),
        radial-gradient(circle at 52% 52%, rgba(212,175,55,0.09), transparent 16%),
        radial-gradient(circle at 76% 36%, rgba(232,93,74,0.09), transparent 20%),
        rgba(10,12,16,0.82);
    background-size: 68px 68px, 68px 68px, auto, auto, auto;
    box-shadow: var(--wa-shadow);
}
.atlas-radar:before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(ellipse at 52% 52%, transparent 0 18%, rgba(212,175,55,0.16) 18.2%, transparent 18.7%),
        radial-gradient(ellipse at 52% 52%, transparent 0 32%, rgba(212,175,55,0.11) 32.2%, transparent 32.7%),
        linear-gradient(24deg, transparent 0 46%, rgba(212,175,55,0.11) 46.1%, transparent 46.4% 100%),
        linear-gradient(-18deg, transparent 0 58%, rgba(212,175,55,0.10) 58.1%, transparent 58.4% 100%);
    opacity: .58;
}
.atlas-radar-title {
    position: absolute;
    z-index: 2;
    top: 22px;
    left: 24px;
    max-width: 420px;
}
.atlas-radar-title b {
    display: block;
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.6px;
    color: var(--wa-gold);
    text-transform: uppercase;
    margin-bottom: 8px;
}
.atlas-radar-title strong {
    display: block;
    font-family: var(--wa-font-display);
    font-size: 26px;
    line-height: 1;
    letter-spacing: 2px;
    color: #f0eee8;
}
.atlas-radar-title span {
    display: block;
    margin-top: 10px;
    max-width: 460px;
    color: rgba(232,228,220,0.42);
    font-size: 12px;
    line-height: 1.6;
}
.atlas-radar-dot {
    position: absolute;
    z-index: 1;
    left: var(--x);
    top: var(--y);
    width: var(--s);
    height: var(--s);
    border-radius: 50%;
    transform: translate(-50%, -50%);
    background: var(--c);
    box-shadow: 0 0 14px var(--c);
}
.atlas-radar-dot:after {
    content: "";
    position: absolute;
    inset: -6px;
    border-radius: inherit;
    background: var(--c);
    opacity: .13;
}
.atlas-radar-timeline {
    position: absolute;
    z-index: 2;
    left: 24px;
    right: 24px;
    bottom: 22px;
    display: grid;
    grid-template-columns: 52px minmax(0,1fr) 68px;
    gap: 10px;
    align-items: center;
    color: rgba(232,228,220,0.34);
    font-family: var(--wa-font-mono);
    font-size: 10px;
}
.atlas-radar-track {
    position: relative;
    height: 9px;
    border-radius: 2px;
    background: linear-gradient(90deg, rgba(212,175,55,0.18), rgba(212,175,55,0.70));
}
.atlas-radar-track:after {
    content: "";
    position: absolute;
    right: 7%;
    top: 50%;
    width: 14px;
    height: 14px;
    transform: translateY(-50%);
    border-radius: 50%;
    background: #f3dc6b;
    box-shadow: 0 0 15px rgba(243,220,107,0.55);
}
.atlas-ops-side {
    border: 1px solid rgba(180,160,120,0.15);
    border-radius: 8px;
    background: rgba(12,15,20,0.86);
    box-shadow: var(--wa-shadow);
    padding: 18px;
}
.atlas-ops-side-title {
    font-family: var(--wa-font-mono);
    color: var(--wa-gold);
    font-size: 11px;
    letter-spacing: 1.6px;
    text-transform: uppercase;
    margin-bottom: 14px;
}
.atlas-ops-row {
    display: grid;
    grid-template-columns: minmax(0,1fr) auto;
    gap: 12px;
    align-items: center;
    padding: 11px 0;
    border-top: 1px solid rgba(180,160,120,0.08);
}
.atlas-ops-row:first-of-type {
    border-top: 0;
}
.atlas-ops-row span {
    color: rgba(232,228,220,0.46);
    font-size: 12px;
}
.atlas-ops-row b {
    font-family: var(--wa-font-display);
    font-size: 22px;
    letter-spacing: 1px;
    color: #f0eee8;
    font-weight: 700;
}
.atlas-ops-row.is-accent b { color: var(--wa-gold); }
.atlas-duel {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 72px minmax(0, 1fr);
    gap: 14px;
    align-items: stretch;
    margin: 18px 0 18px;
}
.atlas-duel-card {
    min-height: 150px;
    border: 1px solid rgba(180,160,120,0.15);
    border-radius: 8px;
    background:
        radial-gradient(circle at 82% 20%, rgba(212,175,55,0.08), transparent 24%),
        rgba(12,15,20,0.9);
    padding: 22px;
    box-shadow: var(--wa-shadow);
}
.atlas-duel-card.red {
    background:
        radial-gradient(circle at 82% 20%, rgba(232,93,74,0.12), transparent 24%),
        rgba(12,15,20,0.9);
}
.atlas-duel-vs {
    display: grid;
    place-items: center;
    color: var(--wa-gold);
    border: 1px solid rgba(180,160,120,0.12);
    border-radius: 8px;
    background: rgba(12,15,20,0.62);
}
@media (max-width: 900px) {
    .atlas-global-nav {
        grid-template-columns: 1fr;
    }
    .atlas-display-chip {
        display: none;
    }
    .atlas-header-inner,
    .atlas-ops-board,
    .atlas-duel {
        grid-template-columns: 1fr;
    }
    .atlas-header-stats {
        min-width: 0;
        grid-template-columns: 1fr;
    }
    .atlas-title {
        font-size: 28px;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# 顶部 Atlas 命令栏
# ---------------------------------------------------------------------------
PAGES = [
    ("overview", "nav.overview"),
    ("crawl", "nav.crawl"),
    ("recursive", "nav.recursive"),
    ("profile", "nav.profile"),
    ("report", "nav.report"),
    ("competitor", "nav.competitor"),
    ("settings", "nav.settings"),
]


def render_top_nav() -> str:
    locale = current_locale()
    alt_locale = alternate_locale(locale)
    page = page_id_from_query(st.query_params.get("page"))
    links = "".join(
        f"<a class='atlas-global-link {'is-active' if page_id == page else ''}' target='_self' href='?page={quote(page_id)}&lang={quote(locale)}'>{t(label_key)}</a>"
        for page_id, label_key in PAGES
    )
    lang_url = f"?page={quote(page)}&lang={quote(alt_locale)}"
    links += f"<a class='atlas-global-link atlas-language-pill' target='_self' href='{lang_url}'>{t('nav.switch_label')}</a>"
    st.markdown(
        f"""
        <nav class="atlas-global-nav">
            <div class="atlas-global-brand">
                <div class="atlas-global-mark">
                    <svg width="23" height="23" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M255.968 288.494L166.211 241.067L10.4062 158.753C4.14838 155.909 -1.68275 161.596 0.450591 167.283L79.8393 369.685C83.3522 377.874 90.4633 382.537 98.2002 384.371L167.175 392.161C226.276 398.602 285.901 398.602 345.002 392.161L407.35 385.366C415.891 384.139 421.999 381.272 426.067 378.358L255.968 288.494Z" fill="#d4af37"/>
                        <path d="M501.789 158.755L345.784 241.07L432.426 370.058L511.616 167.285C513.607 161.03 507.492 155.627 501.789 158.755Z" fill="#8C7A5E"/>
                        <path d="M264.274 119.615C260.292 113.8 251.616 113.8 247.776 119.615L166.211 241.068L426.067 378.357C428.897 375.217 430.177 373.638 432.424 370.056L345.782 241.068L264.274 119.615Z" fill="#D4C9B0"/>
                    </svg>
                </div>
                <div>
                    <div class="atlas-global-title">SLG SENTINEL</div>
                    <div class="atlas-global-sub">{t("nav.brand_subtitle")}</div>
                </div>
            </div>
            <div class="atlas-global-links">{links}</div>
            <div class="atlas-display-chip">
                <b>{t("nav.display")}</b>
                <span><em>{t("nav.mode")}</em><strong>Atlas UI</strong></span>
                <span><em>{t("nav.year")}</em><strong>2026 AD</strong></span>
                <span><em>{t("nav.language")}</em><strong>{t("nav.lang_short")}</strong></span>
                <a class="atlas-lang-link" target="_self" href="{lang_url}">{t("nav.switch_label")}</a>
            </div>
        </nav>
        """,
        unsafe_allow_html=True,
    )
    return page


page = render_top_nav()

if page == "overview":
    render_overview_page()
elif page == "crawl":
    render_crawl_page()
elif page == "recursive":
    render_recursive_crawl_page()
elif page == "profile":
    render_profile_page()
elif page == "report":
    render_report_page()
elif page == "competitor":
    render_competitor_page()
elif page == "settings":
    render_settings_page()
