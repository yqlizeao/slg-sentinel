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
.stAppToolbar,
.stAppHeader,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"] {
    display: none !important;
    pointer-events: none !important;
}

/* ── 主区域间距 ──────────────────────────────────── */
.block-container {
    padding-top: 0.35rem !important; padding-left: 1.35rem !important;
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

/* ── War Atlas 基础元素皮肤 ─────────────────────────
   Mirrors the target system: thin bronze borders, low-radius controls,
   transparent black surfaces, small mono labels, and restrained gold states.
*/
button,
[role="button"],
a,
input,
textarea,
[data-baseweb="select"],
[data-baseweb="tab"],
[data-baseweb="checkbox"] {
    -webkit-font-smoothing: antialiased !important;
}

button {
    min-height: 34px !important;
    border-radius: 4px !important;
    font-family: var(--wa-font-body) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: .45px !important;
}
button p {
    font-size: inherit !important;
    font-weight: inherit !important;
    letter-spacing: inherit !important;
}
button:focus-visible,
a:focus-visible,
input:focus-visible,
textarea:focus-visible,
[data-baseweb="select"]:focus-within {
    outline: 1px solid rgba(212,175,55,.55) !important;
    outline-offset: 2px !important;
}
button:disabled,
[aria-disabled="true"] {
    opacity: .38 !important;
    cursor: not-allowed !important;
    filter: grayscale(.25);
}

/* Buttons */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button,
button[kind="secondary"],
button:not([kind]) {
    height: 36px !important;
    background: rgba(10,12,16,.34) !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    color: rgba(232,228,220,.66) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.03) !important;
    transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast) !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover,
button[kind="secondary"]:hover,
button:not([kind]):hover {
    background: rgba(212,175,55,.075) !important;
    border-color: rgba(212,175,55,.38) !important;
    color: #e8e4dc !important;
    box-shadow: 0 0 18px rgba(212,175,55,.08), inset 0 1px 0 rgba(255,255,255,.04) !important;
    transform: translateY(-1px);
}
button[kind="primary"],
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #d4af37 0%, #b8962e 100%) !important;
    border: 1px solid rgba(243,220,107,.36) !important;
    color: #0a0c10 !important;
    box-shadow: 0 3px 14px rgba(212,175,55,.22), inset 0 1px 0 rgba(255,255,255,.22) !important;
    text-transform: uppercase !important;
}
button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #e1bf4a 0%, #c3a13b 100%) !important;
    box-shadow: 0 6px 22px rgba(212,175,55,.28), var(--wa-glow) !important;
}

/* Labels and help text */
[data-testid="stWidgetLabel"] {
    min-height: 18px !important;
}
[data-testid="stWidgetLabel"] p,
.stSelectbox label p,
.stTextInput label p,
.stTextArea label p,
.stNumberInput label p,
.stDateInput label p {
    font-family: var(--wa-font-mono) !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    color: rgba(232,228,220,.38) !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
[data-testid="stCaptionContainer"],
.stCaptionContainer {
    color: rgba(232,228,220,.38) !important;
    font-size: 11px !important;
}

/* Text inputs / text areas / date / number */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    min-height: 38px !important;
    line-height: 1.4 !important;
    padding: 8px 12px !important;
    background: rgba(0,0,0,.30) !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 4px !important;
    color: #e8e4dc !important;
    font-family: var(--wa-font-body) !important;
    font-size: 12px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.03) !important;
}
/* Password / secret inputs: keep wrapper, input, and visibility toggle button aligned */
.stTextInput [data-baseweb="input"] {
    min-height: 38px !important;
    align-items: stretch !important;
    padding-right: 0 !important;
}
.stTextInput [data-baseweb="input"] > div:last-child:has(button),
.stTextInput [data-baseweb="input"] [data-baseweb="button"] {
    align-self: stretch !important;
}
.stTextInput [data-baseweb="input"] button {
    height: 38px !important;
    min-height: 38px !important;
    width: 38px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    color: rgba(232,228,220,.62) !important;
    box-shadow: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
}
.stTextInput [data-baseweb="input"] button:hover {
    color: var(--wa-gold) !important;
    background: rgba(212,175,55,.06) !important;
    transform: none !important;
}
.stTextInput [data-baseweb="input"] button svg {
    width: 16px !important;
    height: 16px !important;
}
/* Number input internals */
.stNumberInput [data-baseweb="input"] {
    min-height: 38px !important;
}
.stNumberInput button {
    height: 18px !important;
    min-height: 18px !important;
}
.stTextInput input:hover,
.stTextArea textarea:hover,
.stNumberInput input:hover,
.stDateInput input:hover,
[data-baseweb="input"]:hover input,
[data-baseweb="textarea"]:hover textarea {
    border-color: rgba(212,175,55,.26) !important;
    background: rgba(12,15,20,.72) !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
[data-baseweb="input"]:focus-within input,
[data-baseweb="textarea"]:focus-within textarea {
    border-color: rgba(212,175,55,.48) !important;
    box-shadow: 0 0 0 2px rgba(212,175,55,.10), inset 0 1px 0 rgba(255,255,255,.04) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: rgba(232,228,220,.28) !important;
}

/* Select / multiselect */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"],
[data-baseweb="select"] {
    min-height: 38px !important;
    background: rgba(0,0,0,.30) !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 4px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.03) !important;
}
.stSelectbox [data-baseweb="select"]:hover,
.stMultiSelect [data-baseweb="select"]:hover,
[data-baseweb="select"]:hover {
    border-color: rgba(212,175,55,.28) !important;
    background: rgba(12,15,20,.78) !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div,
[data-baseweb="select"] > div {
    min-height: 36px !important;
    background: transparent !important;
    border: 0 !important;
    align-items: center !important;
}
.stSelectbox [data-baseweb="select"] [data-baseweb="select-option"],
.stSelectbox [data-baseweb="select"] [class*="ValueContainer"],
.stMultiSelect [data-baseweb="select"] [class*="ValueContainer"] {
    padding: 0 12px !important;
    min-height: 36px !important;
    display: flex !important;
    align-items: center !important;
}
.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span,
[data-baseweb="select"] span {
    color: rgba(232,228,220,.78) !important;
    font-size: 12px !important;
    line-height: 1.4 !important;
}
[data-baseweb="select"] svg {
    fill: rgba(212,175,55,.70) !important;
}
[data-baseweb="popover"],
[data-baseweb="menu"] {
    background: rgba(12,15,20,.98) !important;
    border: 1px solid rgba(180,160,120,.18) !important;
    border-radius: 6px !important;
    max-width: min(460px, calc(100vw - 32px)) !important;
    max-height: min(72dvh, 640px) !important;
    overflow: auto !important;
    z-index: 100000 !important;
    box-shadow: 0 18px 52px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.03) !important;
    backdrop-filter: blur(16px) !important;
}
div[data-testid="stPopoverBody"] {
    position: fixed !important;
    left: 50% !important;
    right: auto !important;
    top: 98px !important;
    bottom: auto !important;
    transform: translateX(-50%) !important;
    width: min(1160px, calc(100vw - 72px)) !important;
    max-width: min(1160px, calc(100vw - 72px)) !important;
    max-height: calc(100dvh - 118px) !important;
    margin-top: 0 !important;
    overflow: auto !important;
    padding: 0 !important;
    border: 1px solid rgba(180,160,120,.20) !important;
    border-radius: 16px !important;
    background:
        radial-gradient(circle at 72% 12%, rgba(212,175,55,.055), transparent 31%),
        radial-gradient(circle at 16% 88%, rgba(91,154,110,.07), transparent 34%),
        linear-gradient(180deg, rgba(17,21,27,.985), rgba(8,10,14,.985)) !important;
    box-shadow: 0 30px 86px rgba(0,0,0,.80), 0 0 0 1px rgba(255,255,255,.028) inset !important;
    scrollbar-width: thin;
    scrollbar-color: rgba(212,175,55,.38) rgba(180,160,120,.08);
}
div[data-testid="stPopoverBody"]::before {
    content: "";
    position: sticky;
    top: 0;
    display: block;
    height: 0;
    z-index: 2;
    border-top: 1px solid rgba(255,255,255,.025);
}
div[data-testid="stPopoverBody"] > div {
    padding: 0 !important;
}
div[data-testid="stPopoverBody"] .block-container,
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
    overflow: visible !important;
}
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
    gap: 0 !important;
}
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] h1,
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] h2,
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] h3,
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] h4,
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] h5 {
    margin: 16px 34px 10px !important;
    color: rgba(232,228,220,.62) !important;
    font-family: var(--wa-font-display) !important;
    font-size: 15px !important;
    line-height: 1.1 !important;
    letter-spacing: 2.4px !important;
    text-transform: uppercase !important;
}
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] {
    flex-wrap: wrap !important;
    gap: 14px !important;
    padding-inline: 32px !important;
}
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
    flex: 1 1 140px !important;
    min-width: 140px !important;
}
div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] {
    color: rgba(232,228,220,.68) !important;
}
div[data-testid="stPopoverBody"] hr {
    margin: 10px 0 !important;
    border-color: rgba(180,160,120,.10) !important;
}
div[data-testid="stPopoverBody"] .stAlert {
    margin: 12px 32px !important;
}
div[data-testid="stPopoverBody"] .stCaptionContainer,
div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] {
    padding-inline: 32px !important;
    color: rgba(232,228,220,.46) !important;
}
div[data-testid="stPopoverBody"] .stButton,
div[data-testid="stPopoverBody"] [data-testid="stButton"] {
    padding: 0 32px 16px !important;
}
div[data-testid="stPopoverBody"] button[kind="primary"],
div[data-testid="stPopoverBody"] .stButton button {
    min-height: 38px !important;
    border-radius: 6px !important;
    border: 1px solid rgba(212,175,55,.40) !important;
    background: rgba(212,175,55,.085) !important;
    color: var(--wa-gold) !important;
    font-weight: 700 !important;
    letter-spacing: .2px !important;
    box-shadow: none !important;
}
div[data-testid="stPopoverBody"] .stButton button:hover,
div[data-testid="stPopoverBody"] button[kind="primary"]:hover {
    background: rgba(212,175,55,.16) !important;
    border-color: rgba(212,175,55,.64) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.04) !important;
    transform: none !important;
}
div[data-testid="stPopoverBody"] .stSelectbox,
div[data-testid="stPopoverBody"] .stRadio,
div[data-testid="stPopoverBody"] .stTextInput,
div[data-testid="stPopoverBody"] .stNumberInput,
div[data-testid="stPopoverBody"] .stTextArea {
    padding-inline: 32px !important;
}
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] .stSelectbox,
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] .stRadio,
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] .stTextInput,
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] .stNumberInput,
div[data-testid="stPopoverBody"] div[data-testid="stHorizontalBlock"] .stTextArea {
    padding-inline: 0 !important;
}
div[data-testid="stPopoverBody"] label,
div[data-testid="stPopoverBody"] [data-testid="stWidgetLabel"] {
    color: rgba(232,228,220,.48) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 10px !important;
    letter-spacing: 1.2px !important;
    text-transform: uppercase !important;
}
div[data-testid="stPopoverBody"] [data-baseweb="select"],
div[data-testid="stPopoverBody"] input,
div[data-testid="stPopoverBody"] textarea {
    min-height: 44px !important;
    border-radius: 6px !important;
    background: rgba(5,7,10,.76) !important;
    border: 1px solid rgba(180,160,120,.18) !important;
}
div[data-testid="stPopoverBody"] [data-baseweb="select"] input,
div[data-testid="stPopoverBody"] [data-baseweb="select"] [contenteditable="true"] {
    caret-color: transparent !important;
    color: transparent !important;
    text-shadow: none !important;
    opacity: 0 !important;
    width: 1px !important;
}
div[data-testid="stPopoverBody"] [data-testid="stHeaderActionElements"],
div[data-testid="stPopoverBody"] a[href^="#"] {
    display: none !important;
}
div[data-testid="stPopoverBody"] [data-baseweb="select"]:hover,
div[data-testid="stPopoverBody"] input:hover,
div[data-testid="stPopoverBody"] textarea:hover,
div[data-testid="stPopoverBody"] input:focus,
div[data-testid="stPopoverBody"] textarea:focus {
    border-color: rgba(212,175,55,.42) !important;
}
div[data-testid="stPopoverBody"] [role="radiogroup"] {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 8px !important;
}
div[data-testid="stPopoverBody"] [role="radiogroup"] label {
    min-height: 38px !important;
    align-items: center !important;
    padding: 7px 11px !important;
    border: 1px solid rgba(180,160,120,.14) !important;
    border-radius: 6px !important;
    background: rgba(9,12,16,.62) !important;
}
div[data-testid="stPopoverBody"] [data-testid="stExpander"],
div[data-testid="stPopoverBody"] [data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stPopoverBody"] [data-testid="stForm"] {
    margin: 12px 32px !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 10px !important;
    background: rgba(7,10,13,.46) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
}
div[data-testid="stPopoverBody"] [data-testid="stExpander"] details,
div[data-testid="stPopoverBody"] [data-testid="stExpander"] summary {
    background: transparent !important;
    border: 0 !important;
}
div[data-testid="stPopoverBody"] [data-testid="stTabs"] {
    padding-inline: 32px !important;
}
div[data-testid="stPopoverBody"] [data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 1px solid rgba(180,160,120,.14) !important;
}
div[data-testid="stPopoverBody"] [data-baseweb="tab"] {
    min-height: 34px !important;
    padding: 0 12px !important;
    border: 1px solid rgba(180,160,120,.14) !important;
    border-bottom: 0 !important;
    border-radius: 6px 6px 0 0 !important;
    background: rgba(10,12,16,.45) !important;
    color: rgba(232,228,220,.58) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 10px !important;
    letter-spacing: .8px !important;
}
div[data-testid="stPopoverBody"] [data-testid="stDataFrame"],
div[data-testid="stPopoverBody"] table {
    margin-inline: 32px !important;
    width: calc(100% - 64px) !important;
}
div[data-testid="stPopoverBody"] [data-testid="stDataFrame"] {
    overflow: hidden !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 10px !important;
    background: rgba(7,10,13,.48) !important;
}
div[data-testid="stPopoverBody"] .dvn-scroller,
div[data-testid="stPopoverBody"] .stDataFrameGlideDataEditor,
div[data-testid="stPopoverBody"] [class*="glide"] {
    background: rgba(7,10,13,.68) !important;
    color: rgba(232,228,220,.72) !important;
}
div[data-testid="stPopoverBody"] table {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    overflow: hidden !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 10px !important;
}
div[data-testid="stPopoverBody"] th,
div[data-testid="stPopoverBody"] td {
    border-bottom: 1px solid rgba(180,160,120,.10) !important;
    color: rgba(232,228,220,.68) !important;
    background: rgba(7,10,13,.46) !important;
}
[role="listbox"],
ul[role="listbox"] {
    padding: 4px !important;
    background: transparent !important;
}
[role="option"] {
    min-height: 32px !important;
    border-radius: 4px !important;
    color: rgba(232,228,220,.66) !important;
    font-size: 12px !important;
}
[role="option"]:hover,
[role="option"][aria-selected="true"] {
    background: rgba(212,175,55,.10) !important;
    color: #e8e4dc !important;
}

/* Checkbox and radio */
.stCheckbox label,
.stRadio label {
    min-height: 32px !important;
    height: auto !important;
    padding: 6px 8px !important;
    border-radius: 4px !important;
    color: rgba(232,228,220,.62) !important;
    align-items: flex-start !important;
    transition: color var(--transition-fast), background var(--transition-fast), border-color var(--transition-fast) !important;
}
.stCheckbox label > div:first-child,
.stCheckbox label [data-baseweb="checkbox"] {
    flex: 0 0 auto !important;
    margin-top: 2px !important;
}
.stRadio [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 6px !important;
}
.stCheckbox label,
.stRadio [role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    gap: 9px !important;
    justify-content: flex-start !important;
}
.stRadio [role="radiogroup"] label > div:first-child {
    flex: 0 0 18px !important;
    width: 18px !important;
    min-width: 18px !important;
}
.stRadio [role="radiogroup"] label > div:not(:first-child) {
    flex: 1 1 auto !important;
    width: auto !important;
    max-width: none !important;
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}
.stRadio [role="radiogroup"] label:has(input:checked) {
    background: rgba(212,175,55,.055) !important;
    border: 1px solid rgba(212,175,55,.16) !important;
}
.stRadio [role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"],
.stRadio [role="radiogroup"] label:has(input:checked) p,
.stRadio [role="radiogroup"] label:has(input:checked) span {
    background: transparent !important;
}
.stCheckbox label [data-testid="stMarkdownContainer"],
.stRadio label [data-testid="stMarkdownContainer"] {
    flex: 1 1 auto !important;
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
}
.stCheckbox label p,
.stRadio label p {
    display: block !important;
    width: 100% !important;
    max-width: none !important;
    font-family: var(--wa-font-body) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    color: rgba(232,228,220,.66) !important;
    letter-spacing: .15px !important;
    text-transform: none !important;
    white-space: normal !important;
    word-break: normal !important;
    overflow-wrap: normal !important;
    line-height: 1.35 !important;
    margin: 0 !important;
}
.stCheckbox label:hover,
.stRadio label:hover {
    color: #e8e4dc !important;
    background: rgba(212,175,55,.045) !important;
}
/* Checkbox indicator only — the leaf 14x14 square. For st.toggle, baseweb
   wraps the toggle track + ball in nested divs, so we exclude any parent
   div that itself contains a child div (that's the toggle track). */
.stCheckbox [data-baseweb="checkbox"] > div:first-child:not(:has(> div)),
.stRadio [data-baseweb="radio"] > div:first-child:not(:has(> div)) {
    width: 14px !important;
    height: 14px !important;
    border: 1px solid rgba(212,175,55,.42) !important;
    background: transparent !important;
    box-shadow: none !important;
}
/* Restore baseweb toggle visuals: never apply our checkbox border to the
   toggle's track (it has a child div = the ball). */
.stCheckbox [data-baseweb="checkbox"] > div:has(> div) {
    width: auto !important;
    height: auto !important;
    border: 0 !important;
}
/* Checked state: only paint the leaf checkmark/radio square gold, never the
   toggle track (which has a child div = the ball). */
.stCheckbox [data-baseweb="checkbox"] [aria-checked="true"] > div:not(:has(> div)),
.stCheckbox [data-baseweb="checkbox"]:has(input:checked) > div:first-child:not(:has(> div)),
.stRadio [data-baseweb="radio"] [aria-checked="true"] > div:not(:has(> div)),
.stRadio [data-baseweb="radio"]:has(input:checked) > div:first-child:not(:has(> div)) {
    background: #d4af37 !important;
    border-color: #d4af37 !important;
}
.stRadio label[data-baseweb="radio"]:has(input:checked) > div:first-child {
    background: transparent !important;
    border-color: rgba(212,175,55,.42) !important;
}
.stRadio label[data-baseweb="radio"]:has(input:checked) > div:first-child > div {
    width: 8px !important;
    height: 8px !important;
    margin: 2px !important;
    border-radius: 50% !important;
    background: #d4af37 !important;
    border-color: #d4af37 !important;
}
.stRadio label[data-baseweb="radio"]:has(input:checked) > input + div {
    background: transparent !important;
    color: rgba(232,228,220,.76) !important;
    border: 0 !important;
    box-shadow: none !important;
}
.stRadio label[data-baseweb="radio"]:has(input:checked) > input + div p {
    color: rgba(232,228,220,.76) !important;
}
.stCheckbox svg,
.stRadio svg {
    fill: #0a0c10 !important;
    color: #0a0c10 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px !important;
    padding: 0 0 1px 0 !important;
    border-bottom: 1px solid rgba(180,160,120,.16) !important;
}
.stTabs [data-baseweb="tab"] {
    height: 38px !important;
    padding: 0 14px !important;
    border: 1px solid transparent !important;
    border-radius: 4px 4px 0 0 !important;
    color: rgba(232,228,220,.42) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #e8e4dc !important;
    background: rgba(212,175,55,.045) !important;
    border-color: rgba(180,160,120,.10) !important;
}
.stTabs [aria-selected="true"] {
    color: #d4af37 !important;
    background: rgba(212,175,55,.08) !important;
    border-color: rgba(212,175,55,.28) !important;
    border-bottom-color: #d4af37 !important;
}

/* Expanders, bordered containers, panels */
details[data-testid="stExpander"],
div[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid rgba(180,160,120,.15) !important;
    border-radius: 8px !important;
    background:
        linear-gradient(rgba(212,175,55,.022) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,.018) 1px, transparent 1px),
        rgba(12,15,20,.62) !important;
    background-size: 64px 64px, 64px 64px, auto !important;
    box-shadow: var(--wa-shadow) !important;
}
details[data-testid="stExpander"] summary {
    min-height: 42px !important;
    color: rgba(232,228,220,.66) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 11px !important;
    letter-spacing: .8px !important;
    text-transform: uppercase !important;
}
details[data-testid="stExpander"] summary:hover {
    color: #d4af37 !important;
    background: rgba(212,175,55,.04) !important;
}

/* Alerts */
.stAlert,
div[data-testid="stNotification"] {
    border: 1px solid rgba(180,160,120,.16) !important;
    border-left: 3px solid rgba(212,175,55,.72) !important;
    border-radius: 0 8px 8px 0 !important;
    background: rgba(12,15,20,.88) !important;
    color: rgba(232,228,220,.74) !important;
    box-shadow: 0 10px 34px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.02) !important;
}
.stAlert p,
div[data-testid="stNotification"] p {
    color: rgba(232,228,220,.74) !important;
    font-size: 12px !important;
}
.stAlert svg {
    fill: #d4af37 !important;
    color: #d4af37 !important;
}

/* Lists, markdown links, code */
.stMarkdown ul,
.stMarkdown ol {
    color: rgba(232,228,220,.66) !important;
    font-size: 12px !important;
    line-height: 1.85 !important;
}
.stMarkdown li::marker {
    color: #d4af37 !important;
}
.stMarkdown a:not(.atlas-global-link):not(.atlas-lang-link) {
    color: #d4af37 !important;
    text-decoration: none !important;
    border-bottom: 1px solid rgba(212,175,55,.24);
    transition: border-color var(--transition-fast), color var(--transition-fast);
}
.stMarkdown a:not(.atlas-global-link):not(.atlas-lang-link):hover {
    color: #f0d66a !important;
    border-color: rgba(212,175,55,.64);
}
.stMarkdown code,
code {
    border: 1px solid rgba(180,160,120,.12) !important;
    border-radius: 3px !important;
    background: rgba(212,175,55,.06) !important;
    color: rgba(232,228,220,.78) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: .88em !important;
}
pre,
[data-testid="stCodeBlock"] {
    border: 1px solid rgba(180,160,120,.14) !important;
    border-radius: 8px !important;
    background: rgba(7,9,12,.82) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.03) !important;
}

/* Dataframe / data editor shell — only style the OUTER wrapper.
   Do NOT set background/filter/opacity on the canvas itself or on the
   dvn-scroller, because glide-data-grid draws cell colors on the canvas
   pixel-by-pixel using Streamlit theme tokens (configured in
   .streamlit/config.toml: textColor / backgroundColor /
   dataframeHeaderBackgroundColor / dataframeBorderColor). Any CSS layer
   on the canvas or its scroll wrapper visually blends with the glide
   pixels and can washed-out / dim the rendered text. */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"] {
    position: relative !important;
    overflow: hidden !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 8px !important;
    box-shadow: 0 18px 52px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.025) !important;
}
[data-testid="stDataFrame"] button,
[data-testid="stDataEditor"] button {
    border-radius: 4px !important;
}
[data-testid="stDataFrame"] [class*="dvn-scroll"],
[data-testid="stDataEditor"] [class*="dvn-scroll"] {
    scrollbar-color: rgba(212,175,55,.45) rgba(10,12,16,.72) !important;
}
[data-testid="stDataFrame"] [class*="dvn-scroll"]::-webkit-scrollbar,
[data-testid="stDataEditor"] [class*="dvn-scroll"]::-webkit-scrollbar {
    width: 8px !important;
    height: 8px !important;
}
[data-testid="stDataFrame"] [class*="dvn-scroll"]::-webkit-scrollbar-thumb,
[data-testid="stDataEditor"] [class*="dvn-scroll"]::-webkit-scrollbar-thumb {
    background: rgba(212,175,55,.42) !important;
    border-radius: 999px !important;
    border: 2px solid rgba(7,9,12,.92) !important;
}
[data-testid="stDataFrame"] [class*="dvn-scroll"]::-webkit-scrollbar-track,
[data-testid="stDataEditor"] [class*="dvn-scroll"]::-webkit-scrollbar-track {
    background: rgba(10,12,16,.72) !important;
}
[data-testid="stDataEditor"]::before,
[data-testid="stDataFrame"]::before {
    content: "DATA GRID";
    position: absolute;
    top: 7px;
    right: 12px;
    z-index: 2;
    color: rgba(212,175,55,.36);
    font-family: var(--wa-font-mono);
    font-size: 8px;
    letter-spacing: 1.4px;
    pointer-events: none;
}

/* Sliders and progress */
.stSlider [data-baseweb="slider"] > div {
    background: rgba(180,160,120,.20) !important;
}
.stSlider [role="slider"] {
    width: 16px !important;
    height: 16px !important;
    background: #d4af37 !important;
    border: 1px solid rgba(243,220,107,.45) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.35), 0 0 16px rgba(212,175,55,.18) !important;
}
.stProgress > div {
    height: 7px !important;
    background: rgba(180,160,120,.18) !important;
    border-radius: 2px !important;
}
.stProgress > div > div {
    background: linear-gradient(90deg, rgba(212,175,55,.70), #d4af37) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 16px rgba(212,175,55,.18) !important;
}

/* Atlas library/control panels */
.atlas-library-head {
    position: relative;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 16px;
    align-items: stretch;
    margin: 0 0 14px 0;
    padding: 14px;
    border: 1px solid rgba(180,160,120,.15);
    border-radius: 6px;
    background:
        linear-gradient(90deg, rgba(212,175,55,.08), transparent 38%),
        radial-gradient(circle at 88% 18%, rgba(212,175,55,.10), transparent 30%),
        rgba(7,9,12,.56);
    overflow: hidden;
}
.atlas-library-head::before {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        linear-gradient(rgba(212,175,55,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,.025) 1px, transparent 1px);
    background-size: 28px 28px;
    mask-image: linear-gradient(90deg, rgba(0,0,0,.55), transparent 72%);
}
.atlas-mini-label {
    position: relative;
    font-family: var(--wa-font-mono);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.9px;
    color: rgba(212,175,55,.72);
    text-transform: uppercase;
}
.atlas-library-title {
    position: relative;
    margin-top: 5px;
    font-family: var(--wa-font-display);
    font-size: 21px;
    font-weight: 700;
    letter-spacing: 1.8px;
    color: #f0eee8;
    text-transform: uppercase;
}
.atlas-library-subtitle {
    position: relative;
    max-width: 560px;
    margin-top: 8px;
    color: rgba(232,228,220,.44);
    font-size: 12px;
    line-height: 1.55;
}
.atlas-library-radar {
    position: relative;
    min-width: 86px;
    display: grid;
    place-items: center;
    align-content: center;
    gap: 4px;
    border: 1px solid rgba(212,175,55,.18);
    border-radius: 50%;
    aspect-ratio: 1;
    background:
        repeating-conic-gradient(from 0deg, rgba(212,175,55,.12) 0deg 8deg, transparent 8deg 18deg),
        radial-gradient(circle, rgba(212,175,55,.16) 0 2px, transparent 3px),
        rgba(12,15,20,.58);
    box-shadow: inset 0 0 26px rgba(0,0,0,.42), 0 0 22px rgba(212,175,55,.07);
}
.atlas-library-radar span {
    width: 54px;
    text-align: center;
    font-family: var(--wa-font-mono);
    font-size: 7px;
    line-height: 1.25;
    letter-spacing: .9px;
    color: rgba(232,228,220,.45);
    text-transform: uppercase;
}
.atlas-library-radar strong {
    color: var(--wa-gold);
    font-family: var(--wa-font-display);
    font-size: 22px;
    line-height: 1;
}
.atlas-library-metric {
    min-height: 86px;
    padding: 12px 14px;
    border: 1px solid rgba(180,160,120,.14);
    border-radius: 5px;
    background: rgba(7,9,12,.54);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.atlas-library-metric span {
    display: block;
    font-family: var(--wa-font-mono);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.4px;
    color: rgba(232,228,220,.36);
    text-transform: uppercase;
}
.atlas-library-metric b {
    display: block;
    margin-top: 8px;
    color: #e8e4dc;
    font-family: var(--wa-font-display);
    font-size: 26px;
    font-weight: 700;
    letter-spacing: 1px;
}
.atlas-library-metric b.is-small {
    margin-top: 14px;
    font-family: var(--wa-font-mono);
    font-size: 12px;
    line-height: 1.35;
    letter-spacing: .4px;
    color: rgba(232,228,220,.70);
}
.atlas-panel-title {
    margin: 2px 0 5px;
    font-family: var(--wa-font-display);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 1.6px;
    color: #e8e4dc;
    text-transform: uppercase;
}
.atlas-panel-caption {
    margin: 0 0 13px;
    color: rgba(232,228,220,.42);
    font-size: 11px;
    line-height: 1.55;
}
.atlas-status-strip {
    min-height: 38px;
    display: flex;
    align-items: center;
    padding: 8px 11px;
    border: 1px dashed rgba(180,160,120,.16);
    border-radius: 4px;
    background: rgba(7,9,12,.42);
    color: rgba(232,228,220,.43);
    font-size: 11px;
    line-height: 1.45;
}

/* ── Atlas 共享页面组件 ───────────────────────────── */
.atlas-global-nav {
    position: sticky;
    top: 4px;
    z-index: 1200;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 12px;
    align-items: center;
    margin: 0 0 18px 0;
    padding: 6px 12px 6px 14px;
    border: 1px solid rgba(180,160,120,0.16);
    border-radius: 8px;
    background: rgba(12,15,20,0.78);
    box-shadow: 0 16px 44px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.03);
    backdrop-filter: blur(16px);
}
.atlas-global-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 168px;
}
.atlas-global-mark {
    width: 30px;
    height: 30px;
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
    font-size: 15px;
    line-height: 1;
    letter-spacing: 2px;
    color: #f0eee8;
}
.atlas-global-sub {
    margin-top: 2px;
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.6px;
    color: rgba(232,228,220,0.34);
    text-transform: uppercase;
}
.atlas-global-links {
    display: flex;
    align-items: center;
    gap: 6px;
    min-width: 0;
    overflow-x: auto;
    scrollbar-width: none;
}
.atlas-global-links::-webkit-scrollbar { display: none; }
.atlas-global-link {
    display: inline-flex;
    align-items: center;
    position: relative;
    z-index: 2;
    pointer-events: auto;
    height: 28px;
    white-space: nowrap;
    padding: 0 11px;
    border: 1px solid rgba(212,175,55,0.18);
    border-radius: 5px;
    background: rgba(10,12,16,0.38);
    color: rgba(212,175,55,0.78) !important;
    -webkit-text-fill-color: rgba(212,175,55,0.78) !important;
    text-decoration: none !important;
    font-size: 11.5px;
    font-weight: 600;
    letter-spacing: 0.4px;
    transition: all .15s ease;
}
.atlas-global-link:visited,
.atlas-global-link:active,
.atlas-global-link:focus {
    color: rgba(212,175,55,0.78) !important;
    -webkit-text-fill-color: rgba(212,175,55,0.78) !important;
    border-color: rgba(212,175,55,0.18);
    background: rgba(10,12,16,0.38);
}
.atlas-global-link:hover {
    color: #f0d66a !important;
    -webkit-text-fill-color: #f0d66a !important;
    border-color: rgba(212,175,55,0.40);
    background: rgba(212,175,55,0.07);
}
.atlas-global-link.is-active {
    color: var(--wa-gold) !important;
    -webkit-text-fill-color: var(--wa-gold) !important;
    border-color: rgba(212,175,55,0.55);
    background: rgba(212,175,55,0.13);
    box-shadow: 0 0 18px rgba(212,175,55,0.08);
}
.atlas-global-link.is-active:visited,
.atlas-global-link.is-active:active,
.atlas-global-link.is-active:focus {
    color: var(--wa-gold) !important;
    -webkit-text-fill-color: var(--wa-gold) !important;
    border-color: rgba(212,175,55,0.55);
    background: rgba(212,175,55,0.13);
}
.atlas-display-chip {
    min-width: 0;
    padding: 5px 10px;
    border: 1px solid rgba(180,160,120,0.13);
    border-radius: 5px;
    background: rgba(10,12,16,0.45);
    display: flex;
    align-items: center;
    gap: 8px;
    height: 28px;
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
    font-family: var(--wa-font-mono);
    color: var(--wa-gold);
    font-size: 9px;
    letter-spacing: 1.2px;
    margin-right: 4px;
}
.atlas-display-chip span {
    display: inline-flex;
    gap: 3px;
    color: rgba(232,228,220,0.52);
    font-size: 9px;
    line-height: 1;
    white-space: nowrap;
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
    text-transform: uppercase;
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
    text-transform: uppercase;
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

.recursive-inline-note {
    border: 1px solid rgba(180,160,120,0.1);
    border-left: 4px solid #d4af37;
    border-radius: 10px;
    background: rgba(12,15,20,0.7);
    color: rgba(232,228,220,0.7);
    padding: 12px 14px;
    margin-bottom: 12px;
    font-size: 13px;
    line-height: 1.65;
}

/* ═══════════════════════════════════════════════════
   Atlas Shell: single viewport product surface
   ═══════════════════════════════════════════════════ */
html,
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    overflow: hidden !important;
}
.block-container {
    height: 100dvh !important;
    overflow: hidden !important;
    padding-bottom: 12px !important;
    box-sizing: border-box !important;
}
.atlas-global-nav {
    height: 56px;
    margin-top: -8px !important;
    margin-bottom: 6px !important;
}
.atlas-shell-stage {
    position: relative;
    height: calc(100dvh - 124px);
    min-height: 0;
    overflow: hidden;
    border: 1px solid rgba(180,160,120,.16);
    border-radius: 12px;
    isolation: isolate;
    background:
        linear-gradient(rgba(212,175,55,.028) 1px, transparent 1px),
        linear-gradient(90deg, rgba(212,175,55,.022) 1px, transparent 1px),
        radial-gradient(circle at 68% 42%, color-mix(in srgb, var(--atlas-accent) 18%, transparent), transparent 24%),
        #0a0c10;
    background-size: 78px 78px, 78px 78px, auto, auto;
    box-shadow: 0 22px 60px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.03);
}
.atlas-shell-stage * {
    box-sizing: border-box;
}
.atlas-shell-stage::after {
    content: "";
    position: absolute;
    z-index: 30;
    left: 0;
    right: 0;
    bottom: 0;
    height: 2px;
    pointer-events: none;
    background: linear-gradient(90deg, rgba(212,175,55,.18), rgba(232,228,220,.34), rgba(212,175,55,.18));
    box-shadow: 0 -14px 42px rgba(10,12,16,.72), 0 -1px 0 rgba(255,255,255,.04);
}
.atlas-shell-scene {
    position: absolute;
    inset: 0;
    overflow: hidden;
}
.atlas-shell-vignette {
    position: absolute;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 50% 48%, transparent 0 38%, rgba(10,12,16,.34) 67%, rgba(10,12,16,.76) 100%),
        linear-gradient(180deg, rgba(10,12,16,.06), rgba(10,12,16,.72));
    z-index: 2;
}
.atlas-shell-hero {
    position: absolute;
    z-index: 4;
    top: 28px;
    left: 32px;
    width: min(300px, 30vw);
    text-shadow: 0 3px 18px rgba(0,0,0,.76);
}
.atlas-shell-kicker {
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.6px;
    color: var(--atlas-accent);
    text-transform: uppercase;
    margin-bottom: 7px;
}
.atlas-shell-hero-compact {
    top: 24px;
    left: 32px;
    width: min(560px, 46vw);
    max-width: calc(100% - 360px);
    pointer-events: none;
}
.atlas-shell-hero-compact .atlas-shell-kicker {
    display: -webkit-box;
    max-width: 100%;
    margin: 0;
    color: var(--atlas-accent);
    font-size: 10px;
    line-height: 1.55;
    letter-spacing: 1.15px;
    text-transform: none;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.atlas-shell-hero h1 {
    margin: 0 !important;
    font-family: var(--wa-font-display) !important;
    font-size: clamp(24px, 2.35vw, 36px) !important;
    line-height: .96 !important;
    letter-spacing: 2.2px !important;
    color: #f0eee8 !important;
}
.atlas-shell-title-line {
    width: 92px;
    height: 1px;
    margin: 9px 0 8px;
    background: linear-gradient(90deg, var(--atlas-accent), transparent);
}
.atlas-shell-hero p {
    max-width: 260px;
    margin: 0;
    color: rgba(232,228,220,.48);
    font-size: 10px;
    line-height: 1.45;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}
.atlas-shell-display {
    position: absolute;
    z-index: 4;
    top: 24px;
    right: 26px;
    width: 246px;
    padding: 12px 15px;
    border: 1px solid rgba(180,160,120,.15);
    border-radius: 8px;
    background: rgba(12,15,20,.76);
    box-shadow: 0 16px 44px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(16px);
}
.atlas-shell-display-title {
    margin-bottom: 7px;
    color: var(--atlas-accent);
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.5px;
}
.atlas-shell-display-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 14px;
    padding: 3px 0;
    color: rgba(232,228,220,.46);
    font-size: 11px;
}
.atlas-shell-display-row b {
    color: rgba(232,228,220,.84);
    font-family: var(--wa-font-mono);
    font-weight: 500;
    text-transform: uppercase;
}
.atlas-shell-panels {
    position: absolute;
    z-index: 4;
    left: 24px;
    bottom: clamp(66px, 8.5dvh, 88px);
    display: grid;
    grid-template-columns: repeat(3, minmax(200px, 1fr));
    gap: 11px;
    width: min(860px, calc(100% - 500px));
}
.atlas-shell-panel {
    height: clamp(280px, 40dvh, 380px);
    min-height: 0;
    padding: 18px 18px 20px;
    border: 1px solid rgba(180,160,120,.14);
    border-radius: 8px;
    background: rgba(12,15,20,.78);
    box-shadow: 0 16px 44px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(14px);
    display: flex;
    flex-direction: column;
}
.atlas-shell-panel-kicker {
    color: rgba(232,228,220,.38);
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}
.atlas-shell-panel h3 {
    margin: 14px 0 18px !important;
    color: #e8e4dc !important;
    font-family: var(--wa-font-display) !important;
    font-size: clamp(17px, 1.45vw, 22px) !important;
    letter-spacing: 1.45px !important;
}
.atlas-shell-panel-body {
    max-height: none;
    overflow: auto;
    flex: 1 1 auto;
    min-height: 0;
    color: rgba(232,228,220,.54);
    font-size: 11px;
    line-height: 1.55;
}
.atlas-shell-crawl .atlas-shell-panels {
    width: min(860px, calc(100% - 500px));
    grid-template-columns: repeat(3, minmax(200px, 1fr));
}
.atlas-shell-crawl .atlas-shell-list-row {
    padding: 10px 0;
}
.atlas-shell-crawl .atlas-shell-chip {
    margin: 0 6px 8px 0;
    padding: 5px 9px;
    font-size: 10.5px;
}
.atlas-shell-drawers {
    position: absolute;
    z-index: 6;
    top: 178px;
    right: 26px;
    width: 360px;
    display: grid;
    gap: 9px;
}
.atlas-shell-drawer {
    border: 1px solid rgba(180,160,120,.15);
    border-radius: 8px;
    background: rgba(12,15,20,.84);
    box-shadow: 0 16px 44px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(16px);
    overflow: hidden;
}
.atlas-shell-drawer summary {
    min-height: 42px;
    display: grid;
    grid-template-columns: minmax(0,1fr) auto;
    gap: 14px;
    align-items: center;
    padding: 0 14px;
    cursor: pointer;
    color: #e8e4dc;
    font-family: var(--wa-font-display);
    font-size: 14px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    list-style: none;
}
.atlas-shell-drawer summary::-webkit-details-marker { display: none; }
.atlas-shell-drawer summary b {
    color: var(--atlas-accent);
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.1px;
}
.atlas-shell-drawer-body {
    max-height: min(46dvh, 360px);
    overflow: auto;
    border-top: 1px solid rgba(180,160,120,.10);
    padding: 14px;
}
.atlas-shell-timeline {
    position: absolute;
    z-index: 5;
    left: 50%;
    bottom: 22px;
    width: min(720px, calc(100% - 44px));
    transform: translateX(-50%);
    display: grid;
    grid-template-columns: 42px minmax(150px, 240px) minmax(0,1fr);
    gap: 18px;
    align-items: center;
    padding: 18px 20px;
    border: 1px solid rgba(180,160,120,.16);
    border-radius: 10px;
    background: rgba(12,15,20,.84);
    box-shadow: 0 18px 52px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(16px);
}
.atlas-shell-play {
    width: 38px;
    height: 38px;
    border: 1px solid rgba(212,175,55,.62);
    border-radius: 50%;
    display: grid;
    place-items: center;
    color: #f3dc6b;
    background: rgba(212,175,55,.08);
    box-shadow: 0 0 18px rgba(212,175,55,.14);
}
.atlas-shell-era span {
    display: inline-flex;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(180,160,120,.08);
    color: rgba(232,228,220,.50);
    font-family: var(--wa-font-mono);
    font-size: 9px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}
.atlas-shell-era strong {
    display: block;
    margin-top: 4px;
    color: #f0eee8;
    font-family: var(--wa-font-display);
    font-size: 28px;
    letter-spacing: 1.8px;
}
.atlas-shell-range {
    display: grid;
    grid-template-columns: auto minmax(0,1fr) auto;
    gap: 10px;
    align-items: center;
    color: rgba(232,228,220,.36);
    font-family: var(--wa-font-mono);
    font-size: 10px;
}
.atlas-shell-range div {
    position: relative;
    height: 10px;
    border-radius: 2px;
    background: linear-gradient(90deg, rgba(212,175,55,.20), rgba(212,175,55,.70));
}
.atlas-shell-range i {
    position: absolute;
    right: 7%;
    top: 50%;
    width: 15px;
    height: 15px;
    transform: translateY(-50%);
    border-radius: 50%;
    background: #f3dc6b;
    box-shadow: 0 0 15px rgba(243,220,107,.55);
}
.atlas-shell-list-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 12px;
    padding: 10px 0;
    border-top: 1px solid rgba(180,160,120,.08);
}
.atlas-shell-list-row:first-child { border-top: 0; }
.atlas-shell-list-row span {
    color: rgba(232,228,220,.45);
    font-size: 11px;
}
.atlas-shell-list-row b {
    color: rgba(232,228,220,.82);
    font-size: 12px;
    font-weight: 600;
}
.atlas-shell-list-row.is-compact {
    padding: 7px 0;
}
.atlas-shell-chip {
    display: inline-flex;
    margin: 0 5px 6px 0;
    padding: 4px 8px;
    border: 1px solid rgba(180,160,120,.13);
    border-radius: 999px;
    background: rgba(212,175,55,.06);
    color: rgba(232,228,220,.66);
    font-size: 10px;
}
.atlas-shell-empty {
    padding: 18px;
    border: 1px dashed rgba(180,160,120,.18);
    border-radius: 8px;
    color: rgba(232,228,220,.45);
}
.atlas-shell-empty strong {
    display: block;
    margin-bottom: 6px;
    color: rgba(232,228,220,.72);
    font-family: var(--wa-font-display);
    letter-spacing: 1px;
}
.atlas-popover-head {
    position: sticky !important;
    top: 0 !important;
    z-index: 30;
    display: grid;
    grid-template-columns: 34px minmax(0, 1fr);
    gap: 20px;
    align-items: center;
    min-height: 110px;
    width: 100%;
    margin: 0 !important;
    padding: 27px 36px 24px;
    border-bottom: 1px solid rgba(180,160,120,.18);
    background:
        linear-gradient(180deg, rgba(19,23,30,.98), rgba(13,16,21,.96));
    backdrop-filter: blur(16px);
}
.atlas-popover-icon {
    display: inline-flex;
    align-items: flex-end;
    justify-content: center;
    gap: 5px;
    width: 34px;
    height: 36px;
    color: var(--wa-gold);
}
.atlas-popover-icon span {
    display: block;
    width: 7px;
    border-radius: 2px 2px 0 0;
    background: linear-gradient(180deg, #e5c64d, #a98924);
}
.atlas-popover-icon span:nth-child(1) { height: 16px; }
.atlas-popover-icon span:nth-child(2) { height: 26px; }
.atlas-popover-icon span:nth-child(3) { height: 34px; }
.atlas-popover-icon.is-text {
    align-items: flex-end;
    border: 0;
    border-radius: 0;
    background: transparent;
}
.atlas-popover-title {
    margin: 0 !important;
    color: rgba(232,228,220,.66) !important;
    font-family: var(--wa-font-display) !important;
    font-size: clamp(19px, 1.55vw, 24px) !important;
    line-height: 1.08 !important;
    letter-spacing: 3.2px !important;
    text-transform: uppercase;
}
.atlas-popover-head p {
    margin: 12px 0 0 !important;
    color: rgba(232,228,220,.40) !important;
    font-size: 15px !important;
    line-height: 1.35 !important;
}
.atlas-popover-metrics {
    display: grid;
    grid-template-columns: repeat(var(--atlas-popover-metric-cols), minmax(0, 1fr));
    gap: 20px;
    padding: 24px 34px 14px;
}
.atlas-popover-metric {
    min-height: 120px;
    padding: 28px 28px 22px;
    border: 1px solid rgba(180,160,120,.145);
    border-radius: 12px;
    background: linear-gradient(180deg, rgba(7,10,13,.76), rgba(5,7,10,.58));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.atlas-popover-metric strong {
    display: block;
    margin-bottom: 14px;
    color: #f4f0e8;
    font-family: var(--wa-font-display);
    font-size: clamp(29px, 2.9vw, 43px);
    line-height: .95;
    letter-spacing: .5px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.atlas-popover-metric strong.is-long {
    font-size: clamp(22px, 2vw, 31px);
    letter-spacing: .2px;
}
.atlas-popover-metric strong.is-text {
    color: rgba(232,228,220,.86);
    font-family: var(--wa-font-sans);
    font-size: clamp(20px, 1.65vw, 27px);
    font-weight: 700;
    letter-spacing: 0;
}
.atlas-popover-metric strong.is-text.is-long {
    font-size: clamp(17px, 1.45vw, 23px);
}
.atlas-popover-metric span {
    color: rgba(232,228,220,.38);
    font-family: var(--wa-font-mono);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.7px;
    text-transform: uppercase;
}
.atlas-popover-bars,
.atlas-popover-segments {
    padding: 22px 34px 14px;
    border-top: 1px solid rgba(180,160,120,.08);
}
.atlas-popover-section-title {
    margin: 0 0 18px !important;
    color: rgba(232,228,220,.62) !important;
    font-family: var(--wa-font-display) !important;
    font-size: 17px !important;
    letter-spacing: 3.2px !important;
    text-transform: uppercase;
}
.atlas-popover-bar-row {
    display: grid;
    grid-template-columns: minmax(112px, 178px) minmax(0, 1fr) minmax(58px, auto);
    gap: 18px;
    align-items: center;
    min-height: 34px;
    color: rgba(232,228,220,.54);
    font-size: 12px;
}
.atlas-popover-bar-row span {
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.atlas-popover-bar-row b {
    color: rgba(232,228,220,.50);
    font-family: var(--wa-font-mono);
    font-size: 12px;
    font-weight: 500;
    text-align: right;
}
.atlas-popover-bar-track {
    position: relative;
    height: 24px;
    overflow: hidden;
    border-radius: 6px;
    background: rgba(232,228,220,.055);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.02);
}
.atlas-popover-bar-track i {
    display: block;
    height: 100%;
    min-width: 4px;
    border-radius: inherit;
    background: linear-gradient(90deg, rgba(169,137,36,.74), rgba(212,175,55,.90));
}
.atlas-popover-bars.is-green .atlas-popover-bar-track i {
    background: linear-gradient(90deg, rgba(76,150,87,.76), rgba(101,190,112,.88));
}
.atlas-popover-bars.is-red .atlas-popover-bar-track i {
    background: linear-gradient(90deg, rgba(168,25,53,.78), rgba(226,45,63,.90));
}
.atlas-popover-segment-track {
    display: flex;
    overflow: hidden;
    height: 44px;
    border-radius: 9px;
    background: rgba(232,228,220,.08);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
}
.atlas-popover-segment-track i {
    display: block;
    height: 100%;
}
.atlas-popover-segment-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 28px;
    row-gap: 12px;
    margin-top: 20px;
}
.atlas-popover-segment-legend {
    display: grid;
    grid-template-columns: 10px minmax(0, 1fr) auto;
    gap: 10px;
    align-items: center;
    color: rgba(232,228,220,.56);
    font-size: 13px;
}
.atlas-popover-segment-legend span {
    width: 10px;
    height: 10px;
    border-radius: 3px;
}
.atlas-popover-segment-legend em {
    font-style: normal;
}
.atlas-popover-segment-legend b {
    color: rgba(232,228,220,.45);
    font-family: var(--wa-font-mono);
    font-weight: 500;
}
.atlas-popover-footer {
    position: sticky;
    bottom: 0;
    z-index: 3;
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: center;
    margin-top: 18px;
    padding: 15px 36px 20px;
    border-top: 1px solid rgba(180,160,120,.16);
    background: rgba(9,11,15,.97);
}
.atlas-popover-footer em {
    color: rgba(232,228,220,.42);
    font-size: 13px;
}
.atlas-popover-footer span {
    color: var(--wa-gold);
    font-family: var(--wa-font-mono);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .6px;
}

/* ===== Atlas command navigation + modal ===== */
.atlas-command-nav-sentinel {
    width: 1px;
    height: 1px;
    margin: 0;
    opacity: 0;
    pointer-events: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) {
    width: fit-content !important;
    max-width: min(920px, calc(100vw - 52px));
    margin: 0.35rem 0 0.68rem !important;
    padding: 7px !important;
    gap: 8px !important;
    overflow-x: auto !important;
    border: 1px solid rgba(180,160,120,.12);
    border-radius: 10px;
    background: linear-gradient(180deg, rgba(9,12,16,.82), rgba(7,9,12,.66));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
    scrollbar-width: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button)::-webkit-scrollbar {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) > div {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) > div:last-child {
    display: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) button {
    min-width: 116px !important;
    width: auto !important;
    height: 36px !important;
    min-height: 36px !important;
    max-height: 36px !important;
    padding: 0 14px !important;
    border: 1px solid rgba(180,160,120,.13) !important;
    border-radius: 6px !important;
    background: rgba(7,9,12,.72) !important;
    color: rgba(232,228,220,.50) !important;
    box-shadow: none !important;
    transform: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) button p {
    color: inherit !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 10.5px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    letter-spacing: 1.45px !important;
    text-transform: uppercase !important;
    white-space: nowrap !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) button:hover {
    border-color: rgba(212,175,55,.30) !important;
    background: rgba(212,175,55,.055) !important;
    color: rgba(232,228,220,.76) !important;
    transform: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
> div[data-testid="stHorizontalBlock"]:has(button) button[kind="primary"] {
    border-color: rgba(212,175,55,.55) !important;
    background: linear-gradient(180deg, rgba(212,175,55,.14), rgba(212,175,55,.055)) !important;
    color: var(--wa-gold) !important;
    box-shadow: inset 0 0 0 1px rgba(212,175,55,.08), 0 0 18px rgba(212,175,55,.06) !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] {
    width: fit-content !important;
    max-width: min(920px, calc(100vw - 52px)) !important;
    margin: 0.35rem 0 0.68rem !important;
    padding: 6px !important;
    overflow-x: auto !important;
    border: 1px solid rgba(180,160,120,.12);
    border-radius: 10px;
    background: linear-gradient(180deg, rgba(9,12,16,.82), rgba(7,9,12,.66));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025);
    scrollbar-width: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"]::-webkit-scrollbar {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] > div {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    overflow-x: auto !important;
    scrollbar-width: none;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] button,
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] [role="radio"] {
    flex: 0 0 auto !important;
    min-width: 116px !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 14px !important;
    border: 1px solid rgba(180,160,120,.13) !important;
    border-radius: 6px !important;
    background: rgba(7,9,12,.72) !important;
    color: rgba(232,228,220,.50) !important;
    box-shadow: none !important;
    transform: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] button p,
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] [role="radio"] p {
    margin: 0 !important;
    color: inherit !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
    letter-spacing: 1.35px !important;
    text-transform: uppercase !important;
    white-space: nowrap !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] button:hover,
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] [role="radio"]:hover {
    border-color: rgba(212,175,55,.30) !important;
    background: rgba(212,175,55,.055) !important;
    color: rgba(232,228,220,.76) !important;
    transform: none !important;
}
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] button[aria-checked="true"],
div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] [role="radio"][aria-checked="true"] {
    border-color: rgba(212,175,55,.55) !important;
    background: linear-gradient(180deg, rgba(212,175,55,.14), rgba(212,175,55,.055)) !important;
    color: var(--wa-gold) !important;
    box-shadow: inset 0 0 0 1px rgba(212,175,55,.08), 0 0 18px rgba(212,175,55,.06) !important;
}

div[data-testid="stDialog"] {
    background: rgba(0,0,0,.54) !important;
    backdrop-filter: blur(4px);
}
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) {
    width: min(1080px, calc(100vw - 96px)) !important;
    max-width: min(1080px, calc(100vw - 96px)) !important;
    max-height: calc(100dvh - 120px) !important;
    padding: 0 !important;
    overflow: hidden !important;
    border: 1px solid rgba(180,160,120,.24) !important;
    border-radius: 14px !important;
    background:
        radial-gradient(circle at 50% -20%, rgba(212,175,55,.055), transparent 42%),
        linear-gradient(180deg, rgba(18,22,30,.965), rgba(8,10,14,.985)) !important;
    box-shadow:
        0 24px 72px rgba(0,0,0,.66),
        0 0 0 1px rgba(255,255,255,.025),
        inset 0 1px 0 rgba(255,255,255,.04) !important;
}
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) > div {
    padding: 0 !important;
    overflow-y: auto !important;
    max-height: calc(100dvh - 120px) !important;
}
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) > div:first-child:not(:has(.atlas-modal-head)) {
    display: none !important;
}
div[data-testid="stDialog"] h2 {
    display: none !important;
}
div[data-testid="stDialog"] button[aria-label="Close"] {
    position: absolute !important;
    top: 24px !important;
    right: 32px !important;
    z-index: 80 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    min-height: 42px !important;
    padding: 0 !important;
    border: 1px solid rgba(180,160,120,.16) !important;
    border-radius: 10px !important;
    background: rgba(232,228,220,.055) !important;
    color: rgba(232,228,220,.60) !important;
    box-shadow: none !important;
    transform: none !important;
}
div[data-testid="stDialog"] button[aria-label="Close"]:hover {
    border-color: rgba(212,175,55,.30) !important;
    background: rgba(232,228,220,.09) !important;
    color: var(--wa-gold) !important;
    transform: none !important;
}
div[data-testid="stDialog"] button[aria-label="Close"] svg {
    width: 21px !important;
    height: 21px !important;
}
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head)::-webkit-scrollbar,
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) > div::-webkit-scrollbar {
    width: 6px;
}
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head)::-webkit-scrollbar-thumb,
div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) > div::-webkit-scrollbar-thumb {
    border-radius: 999px;
    background: rgba(212,175,55,.55);
}
.atlas-modal-head {
    position: sticky;
    top: 0;
    z-index: 20;
    display: grid;
    grid-template-columns: 27px minmax(0, 1fr);
    gap: 16px;
    align-items: center;
    min-height: 82px;
    padding: 19px 96px 17px 32px;
    border-bottom: 1px solid rgba(180,160,120,.18);
    background: linear-gradient(180deg, rgba(18,22,30,.985), rgba(12,15,20,.965));
}
.atlas-modal-icon {
    display: inline-flex;
    align-items: flex-end;
    justify-content: center;
    gap: 5px;
    width: 27px;
    height: 30px;
    color: var(--wa-gold);
}
.atlas-modal-icon span {
    display: block;
    width: 5px;
    border-radius: 2px 2px 0 0;
    background: linear-gradient(180deg, #e4c64f, #a98924);
}
.atlas-modal-icon span:nth-child(1) { height: 12px; }
.atlas-modal-icon span:nth-child(2) { height: 20px; }
.atlas-modal-icon span:nth-child(3) { height: 28px; }
.atlas-modal-icon b {
    color: var(--wa-gold);
    font-family: var(--wa-font-display);
    font-size: 17px;
    letter-spacing: 1px;
}
.atlas-modal-title {
    color: rgba(232,228,220,.68);
    font-family: var(--wa-font-display);
    font-size: clamp(17px, 1.25vw, 21px);
    line-height: 1.06;
    letter-spacing: 2.8px;
    text-transform: uppercase;
}
.atlas-modal-copy p {
    margin: 7px 0 0 !important;
    color: rgba(232,228,220,.43) !important;
    font-size: 12.5px !important;
    line-height: 1.3 !important;
    max-width: 760px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.atlas-modal-filter-bar {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    padding: 12px 32px;
    border-bottom: 1px solid rgba(180,160,120,.14);
    background: rgba(12,15,20,.58);
}
.atlas-modal-filter-cell {
    min-height: 42px;
    padding: 7px 11px;
    border: 1px solid rgba(180,160,120,.15);
    border-radius: 6px;
    background: rgba(0,0,0,.28);
}
.atlas-modal-filter-cell span {
    display: block;
    margin-bottom: 3px;
    color: rgba(232,228,220,.33);
    font-family: var(--wa-font-mono);
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 1.15px;
    text-transform: uppercase;
}
.atlas-modal-filter-cell b {
    color: rgba(232,228,220,.70);
    font-size: 12px;
    font-weight: 500;
}
div[data-testid="stDialog"] .atlas-popover-metrics {
    padding: 20px 32px 10px;
    gap: 14px;
}
div[data-testid="stDialog"] .atlas-popover-metric {
    min-height: 78px;
    padding: 17px 19px 14px;
    border-radius: 8px;
}
div[data-testid="stDialog"] .atlas-popover-metric strong {
    margin-bottom: 8px;
    font-size: clamp(23px, 1.95vw, 31px);
}
div[data-testid="stDialog"] .atlas-popover-metric strong.is-text {
    font-size: clamp(15px, 1.22vw, 20px);
}
div[data-testid="stDialog"] .atlas-popover-metric span {
    font-size: 9px;
    letter-spacing: 1.28px;
}
div[data-testid="stDialog"] .atlas-popover-bars,
div[data-testid="stDialog"] .atlas-popover-segments,
div[data-testid="stDialog"] .atlas-shell-list-editor,
div[data-testid="stDialog"] .atlas-shell-empty {
    margin-left: 32px;
    margin-right: 32px;
}
div[data-testid="stDialog"] .atlas-popover-bars,
div[data-testid="stDialog"] .atlas-popover-segments {
    padding-left: 0;
    padding-right: 0;
}
div[data-testid="stDialog"] .atlas-popover-section-title {
    margin-bottom: 12px !important;
    font-size: 12.5px !important;
    letter-spacing: 2.25px !important;
}
div[data-testid="stDialog"] .atlas-popover-bar-row {
    grid-template-columns: minmax(98px, 152px) minmax(0, 1fr) minmax(48px, auto);
    min-height: 25px;
    gap: 12px;
    font-size: 10.5px;
}
div[data-testid="stDialog"] .atlas-popover-bar-track {
    height: 16px;
    border-radius: 4px;
}
div[data-testid="stDialog"] .atlas-library-head {
    margin: 0 0 10px;
    padding: 12px;
    border-radius: 7px;
}
div[data-testid="stDialog"] .atlas-library-title {
    margin-top: 4px;
    font-size: 18px;
    letter-spacing: 1.45px;
}
div[data-testid="stDialog"] .atlas-library-subtitle {
    margin-top: 6px;
    font-size: 11px;
}
div[data-testid="stDialog"] .atlas-library-radar {
    min-width: 74px;
}
div[data-testid="stDialog"] .atlas-library-radar strong {
    font-size: 19px;
}
div[data-testid="stDialog"] .atlas-library-metric {
    min-height: 70px;
    padding: 10px 12px;
}
div[data-testid="stDialog"] .atlas-library-metric b {
    margin-top: 6px;
    font-size: 22px;
}
div[data-testid="stDialog"] .atlas-panel-title {
    font-size: 13px;
}
div[data-testid="stDialog"] .atlas-panel-caption {
    margin-bottom: 10px;
    font-size: 10.5px;
}
div[data-testid="stDialog"] .stButton > button {
    width: auto !important;
    min-width: 118px !important;
    max-width: 100% !important;
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 14px !important;
    transform: none !important;
}
div[data-testid="stDialog"] .stButton {
    width: auto !important;
}
div[data-testid="stDialog"] [data-testid="stHorizontalBlock"] {
    padding-left: 32px;
    padding-right: 32px;
}
div[data-testid="stDialog"] [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stDialog"] [data-testid="stDataFrame"],
div[data-testid="stDialog"] iframe {
    margin-left: 32px !important;
    margin-right: 32px !important;
    max-width: calc(100% - 64px) !important;
}
.atlas-modal-footer {
    position: sticky;
    bottom: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 56px;
    margin-top: 14px;
    padding: 11px 32px 13px;
    border-top: 1px solid rgba(180,160,120,.16);
    background: linear-gradient(180deg, rgba(10,12,16,.94), rgba(7,9,12,.985));
}
.atlas-modal-footer em {
    color: rgba(232,228,220,.42);
    font-size: 11.5px;
    line-height: 1.45;
}
.atlas-modal-footer span {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 30px;
    padding: 0 12px;
    border: 1px solid rgba(212,175,55,.42);
    border-radius: 6px;
    background: rgba(212,175,55,.07);
    color: var(--wa-gold);
    font-family: var(--wa-font-mono);
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: .7px;
}
div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"]:has(.atlas-native-slot-head) {
    margin: 16px 32px 0 !important;
    border: 1px solid rgba(180,160,120,.145) !important;
    border-radius: 8px !important;
    background:
        linear-gradient(180deg, rgba(10,13,17,.72), rgba(6,8,11,.58)) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025) !important;
}
div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"]:has(.atlas-native-slot-head) > div {
    padding: 16px 18px 18px !important;
}
.atlas-native-slot-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 18px;
    margin: -1px 0 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(180,160,120,.10);
}
.atlas-native-slot-head div {
    color: rgba(232,228,220,.72);
    font-family: var(--wa-font-display);
    font-size: 13px;
    line-height: 1.1;
    letter-spacing: 2.2px;
    text-transform: uppercase;
}
.atlas-native-slot-head p {
    max-width: 58%;
    margin: 0 !important;
    color: rgba(232,228,220,.36) !important;
    font-size: 10.5px !important;
    line-height: 1.45 !important;
    text-align: right;
}
div[data-testid="stDialog"] label,
div[data-testid="stDialog"] [data-testid="stWidgetLabel"] {
    color: rgba(232,228,220,.42) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 9.5px !important;
    font-weight: 700 !important;
    letter-spacing: 1.15px !important;
    text-transform: uppercase !important;
}
div[data-testid="stDialog"] [data-baseweb="select"] > div,
div[data-testid="stDialog"] [data-testid="stTextInput"] input,
div[data-testid="stDialog"] [data-testid="stDateInput"] input,
div[data-testid="stDialog"] [data-testid="stNumberInput"] input,
div[data-testid="stDialog"] textarea {
    min-height: 36px !important;
    border: 1px solid rgba(180,160,120,.15) !important;
    border-radius: 6px !important;
    background: rgba(0,0,0,.34) !important;
    color: rgba(232,228,220,.72) !important;
    font-size: 12px !important;
    box-shadow: none !important;
}
div[data-testid="stDialog"] textarea {
    min-height: 72px !important;
}
div[data-testid="stDialog"] [data-baseweb="select"] > div:focus-within,
div[data-testid="stDialog"] [data-testid="stTextInput"] input:focus,
div[data-testid="stDialog"] [data-testid="stDateInput"] input:focus,
div[data-testid="stDialog"] [data-testid="stNumberInput"] input:focus,
div[data-testid="stDialog"] textarea:focus {
    border-color: rgba(212,175,55,.46) !important;
    box-shadow: 0 0 0 1px rgba(212,175,55,.12) !important;
}
div[data-testid="stDialog"] [role="radiogroup"] {
    gap: 8px !important;
}
div[data-testid="stDialog"] [role="radiogroup"] label,
div[data-testid="stDialog"] [data-testid="stCheckbox"] label,
div[data-testid="stDialog"] [data-testid="stToggle"] label {
    min-height: 32px !important;
    padding: 6px 9px !important;
    border: 1px solid rgba(180,160,120,.10);
    border-radius: 6px;
    background: rgba(0,0,0,.20);
    color: rgba(232,228,220,.58) !important;
    text-transform: none !important;
    letter-spacing: .2px !important;
    font-family: var(--wa-font-sans) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
}
div[data-testid="stDialog"] [data-testid="stMetric"] {
    padding: 12px 14px !important;
    border: 1px solid rgba(180,160,120,.12);
    border-radius: 8px;
    background: rgba(0,0,0,.22);
}
div[data-testid="stDialog"] [data-testid="stMetricLabel"] {
    color: rgba(232,228,220,.38) !important;
    font-size: 9px !important;
    letter-spacing: 1px !important;
}
div[data-testid="stDialog"] [data-testid="stMetricValue"] {
    color: rgba(232,228,220,.86) !important;
    font-family: var(--wa-font-display) !important;
    font-size: 24px !important;
}
.atlas-step-head {
    display: flex;
    gap: 9px;
    align-items: center;
    margin: 6px 0 7px;
}
.atlas-step-head > div {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    border: 1px solid color-mix(in srgb, var(--step-color) 34%, transparent);
    border-radius: 6px;
    background: color-mix(in srgb, var(--step-color) 13%, transparent);
    color: var(--step-color);
    font-family: var(--wa-font-mono);
    font-size: 9px;
    font-weight: 800;
}
.atlas-step-head strong {
    display: block;
    color: rgba(232,228,220,.76);
    font-size: 12px;
    font-weight: 700;
    line-height: 1.1;
}
.atlas-shell-list-editor {
    display: grid;
    gap: 2px;
}
.atlas-shell-list-title {
    margin-bottom: 4px;
    color: var(--atlas-accent);
    font-family: var(--wa-font-display);
    font-size: 15px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}
.atlas-shell-list-caption {
    margin: 0 0 8px 0 !important;
    color: rgba(232,228,220,.38);
    font-size: 11px;
    line-height: 1.55;
}
.atlas-shell-copy {
    color: rgba(232,228,220,.58);
    font-size: 11px;
    line-height: 1.65;
}
.atlas-shell-copy strong {
    color: rgba(232,228,220,.86);
}
.atlas-stage-map {
    position: absolute;
    inset: 0;
}
.atlas-stage-map svg {
    width: 100%;
    height: 100%;
    opacity: .88;
    filter: drop-shadow(0 24px 48px rgba(0,0,0,.5));
}
.atlas-stage-map .gridline {
    stroke: rgba(212,175,55,.08);
    stroke-width: 1;
}
.atlas-stage-map .land {
    fill: rgba(22,28,30,.55);
    stroke: rgba(232,228,220,.16);
    stroke-width: 1.2;
}
.atlas-stage-map .full-china {
    fill: rgba(20,26,27,.62);
    stroke: rgba(232,228,220,.22);
    stroke-width: 1.6;
}
.atlas-stage-map .island {
    fill: rgba(20,26,27,.45);
    stroke: rgba(232,228,220,.18);
    stroke-width: 1.1;
}
.atlas-stage-map .kingdom {
    stroke-width: 2.4;
    stroke-dasharray: 8 5;
    mix-blend-mode: screen;
}
.atlas-stage-map .wei { fill: rgba(226,45,63,.18); stroke: rgba(226,45,63,.84); }
.atlas-stage-map .shu { fill: rgba(212,175,55,.20); stroke: rgba(212,175,55,.88); }
.atlas-stage-map .wu { fill: rgba(47,107,220,.18); stroke: rgba(88,142,255,.84); }
.atlas-stage-map .route {
    fill: none;
    stroke: rgba(212,175,55,.55);
    stroke-width: 2;
    stroke-linecap: round;
    stroke-dasharray: 5 7;
}
.atlas-stage-map .admin-line {
    fill: none;
    stroke: rgba(232,228,220,.28);
    stroke-width: .9;
    stroke-dasharray: 3 5;
    stroke-linecap: round;
}
.atlas-stage-map .wei-admin { stroke: rgba(226,45,63,.40); }
.atlas-stage-map .shu-admin { stroke: rgba(212,175,55,.42); }
.atlas-stage-map .wu-admin { stroke: rgba(88,142,255,.40); }
.atlas-stage-map .frontier {
    fill: none;
    stroke: rgba(232,228,220,.38);
    stroke-width: 1.5;
    stroke-dasharray: 8 8;
    stroke-linecap: round;
}
.atlas-stage-map .capital-ring {
    fill: none;
    stroke: rgba(212,175,55,.35);
    stroke-width: 1.2;
    stroke-dasharray: 2 6;
}
.atlas-stage-map .signal {
    stroke: rgba(255,255,255,.58);
    stroke-width: 1.4;
}
.atlas-stage-map .capital {
    fill: var(--atlas-accent);
    stroke: rgba(255,255,255,.72);
    stroke-width: 1.6;
}
.atlas-stage-map .wei-capital { fill: #e22d3f; }
.atlas-stage-map .shu-capital { fill: #d4af37; }
.atlas-stage-map .wu-capital { fill: #588eff; }
.atlas-stage-map text {
    font-family: var(--wa-font-mono);
    letter-spacing: 1.5px;
    fill: rgba(232,228,220,.70);
    paint-order: stroke;
    stroke: rgba(10,12,16,.92);
    stroke-width: 4px;
    stroke-linejoin: round;
}
.atlas-stage-map .kingdom-label {
    font-family: var(--wa-font-display);
    font-size: 30px;
    letter-spacing: 4px;
    fill: rgba(232,228,220,.80);
    stroke-width: 5px;
}
.atlas-stage-map .province-label {
    font-size: 10px;
    letter-spacing: 1.7px;
    fill: rgba(232,228,220,.48);
    stroke-width: 3px;
}
.atlas-scene-sigil {
    position: absolute;
    left: 50%;
    top: 50%;
    width: min(58vw, 760px);
    aspect-ratio: 1;
    transform: translate(-50%, -50%);
    border: 1px solid rgba(212,175,55,.13);
    border-radius: 50%;
    box-shadow: inset 0 0 90px rgba(212,175,55,.05), 0 0 90px rgba(0,0,0,.36);
}
.atlas-scene-sigil:before,
.atlas-scene-sigil:after {
    content: "";
    position: absolute;
    inset: 12%;
    border: 1px dashed rgba(212,175,55,.12);
    border-radius: 50%;
}
.atlas-scene-sigil:after {
    inset: 29%;
    border-style: solid;
}
.atlas-scene-node {
    position: absolute;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid rgba(255,255,255,.6);
    background: var(--atlas-accent);
    box-shadow: 0 0 24px color-mix(in srgb, var(--atlas-accent) 60%, transparent);
}
.atlas-scene-line {
    position: absolute;
    height: 1px;
    transform-origin: left center;
    background: linear-gradient(90deg, rgba(212,175,55,.55), transparent);
}
.atlas-native-command-row {
    position: relative;
    z-index: 40;
    margin: -2px 0 8px;
}
div[data-testid="stPopover"] > button,
button[data-testid="stPopoverButton"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-width: 0 !important;
    height: 28px !important;
    padding: 0 11px !important;
    border: 1px solid rgba(180,160,120,0.13) !important;
    border-radius: 5px !important;
    background: rgba(10,12,16,0.38) !important;
    color: rgba(232,228,220,0.58) !important;
    box-shadow: none !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) {
    position: relative;
    z-index: 40;
    width: fit-content !important;
    max-width: min(100%, 560px);
    align-items: center !important;
    gap: 5px !important;
    margin: -4px 0 -8px !important;
    padding: 3px 4px !important;
    border: 1px solid rgba(180,160,120,0.08);
    border-radius: 6px;
    background: rgba(12,15,20,0.30);
    box-shadow: 0 8px 22px rgba(0,0,0,0.16), inset 0 1px 0 rgba(255,255,255,0.018);
    backdrop-filter: blur(14px);
    overflow-x: auto;
    scrollbar-width: none;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"])::-webkit-scrollbar { display: none; }
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) > div[data-testid="column"],
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) > div[data-testid="stColumn"] {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 3px !important;
    width: auto !important;
    min-width: 62px !important;
    height: 24px !important;
    min-height: 24px !important;
    max-height: 24px !important;
    padding: 0 9px !important;
    border-radius: 4px !important;
    background: rgba(10,12,16,0.32) !important;
    border-color: rgba(180,160,120,0.14) !important;
    color: rgba(232,228,220,0.55) !important;
    font-family: var(--wa-font-mono) !important;
    font-size: 9.5px !important;
    font-weight: 600 !important;
    letter-spacing: .9px !important;
    text-transform: none !important;
    line-height: 1 !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02) !important;
    transform: none !important;
    transition: color .12s ease, border-color .12s ease, background-color .12s ease !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"] div[data-testid="stMarkdownContainer"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 100% !important;
    line-height: 1 !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"] p,
button[data-testid="stPopoverButton"] p,
button[data-testid="stPopoverButton"] div[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    font-size: 9.5px !important;
    line-height: 1 !important;
    white-space: nowrap !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {
    display: none !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"]:after {
    content: "⌄";
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    margin-left: 2px;
    color: rgba(232,228,220,0.32);
    font-size: 9px;
    line-height: 1;
    transform: none !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"]:hover,
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"]:focus {
    color: rgba(212,175,55,0.82) !important;
    border-color: rgba(212,175,55,0.42) !important;
    background: rgba(10,12,16,0.32) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02) !important;
    transform: none !important;
}
div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"]:focus {
    color: var(--wa-gold) !important;
    border-color: rgba(212,175,55,0.55) !important;
    background: rgba(10,12,16,0.32) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.02) !important;
    transform: none !important;
}
/* ===== Recursive Graph (center scene) ===== */
.recursive-graph {
    position: absolute;
    inset: 154px 420px 92px 40px;
    overflow: auto;
    z-index: 3;
}
.recursive-graph-inner {
    position: relative;
    margin: 0 auto;
    flex: 0 0 auto;
}
.atlas-shell-recursive .atlas-shell-hero {
    top: 24px;
    left: 34px;
    width: min(560px, 46vw);
    max-width: calc(100% - 450px);
    pointer-events: none;
}
.atlas-shell-recursive .atlas-shell-kicker {
    margin-bottom: 0;
    font-size: 10px;
    line-height: 1.55;
    letter-spacing: 1.15px;
    text-transform: none;
}
.atlas-shell-recursive .atlas-shell-hero h1 {
    font-size: clamp(18px, 1.35vw, 22px) !important;
    line-height: 1.04 !important;
    letter-spacing: 1.25px !important;
}
.atlas-shell-recursive .atlas-shell-title-line {
    width: 68px;
    margin: 7px 0 6px;
}
.atlas-shell-recursive .atlas-shell-hero p {
    max-width: 220px;
    font-size: 9px;
    line-height: 1.35;
    opacity: .62;
    -webkit-line-clamp: 2;
}
.recursive-graph-empty {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 8px;
    color: rgba(232,228,220,.4);
    font-size: 13px;
    text-align: center;
}
.recursive-graph-empty strong {
    font-family: var(--wa-font-display);
    font-size: 18px;
    color: rgba(232,228,220,.7);
    letter-spacing: 2px;
}
.recursive-graph-edges {
    position: absolute;
    top: 0; left: 0;
    z-index: 1;
    pointer-events: none;
}
.recursive-graph-edge {
    fill: none;
    stroke: rgba(232,228,220,.32);
    stroke-width: 1.4;
    opacity: .6;
}
.recursive-graph-edge.is-success { stroke: #5B9A6E; }
.recursive-graph-edge.is-running { stroke: #6B8BDB; }
.recursive-graph-edge.is-paused  { stroke: #D4956B; }
.recursive-graph-edge.is-error   { stroke: #E85D4A; }
.recursive-graph-cols {
    position: absolute;
    top: 0; left: 0;
    z-index: 2;
}
.recursive-graph-col-head {
    position: absolute;
    top: 0;
    width: 220px;
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.6px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
    text-align: center;
    line-height: 32px;
}
.recursive-graph-node {
    position: absolute;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 10px;
    border: 1px solid rgba(180,160,120,.18);
    border-left-width: 4px;
    border-radius: 6px;
    background: rgba(12,15,20,.82);
    color: rgba(232,228,220,.8);
    text-decoration: none !important;
    box-shadow: 0 8px 22px rgba(0,0,0,.36), inset 0 1px 0 rgba(255,255,255,.03);
    opacity: .85;
    transition: opacity .12s ease, box-shadow .12s ease;
}
.recursive-graph-node:hover { opacity: 1; }
.recursive-graph-node.is-success { border-left-color: #5B9A6E; }
.recursive-graph-node.is-running { border-left-color: #6B8BDB; }
.recursive-graph-node.is-paused  { border-left-color: #D4956B; }
.recursive-graph-node.is-error   { border-left-color: #E85D4A; }
.recursive-graph-node.is-selected {
    outline: 2px solid #d4af37;
    outline-offset: -2px;
    box-shadow: 0 0 0 4px rgba(212,175,55,.14), 0 8px 22px rgba(0,0,0,.4);
    opacity: 1;
}
.recursive-graph-node .node-keyword {
    font-family: var(--wa-font-display);
    font-size: 14px;
    font-weight: 700;
    letter-spacing: .4px;
    color: #e8e4dc;
    line-height: 1.2;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}
.recursive-graph-node .node-metric {
    font-family: var(--wa-font-mono);
    font-size: 11px;
    color: rgba(232,228,220,.55);
}
.recursive-graph-node .node-extras {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    color: var(--atlas-accent);
}
.recursive-graph-node .node-status-dot { display: none; }
/* ===== Right-side node detail panel ===== */
.atlas-shell-recursive .atlas-shell-drawers {
    display: block;
    top: 120px;
    right: 26px;
    bottom: 70px;
    padding: 0;
    background: transparent;
    border: 0;
    box-shadow: none;
    width: min(380px, 28vw);
    min-width: 330px;
    height: auto;
    min-height: 0;
}
.recursive-node-detail {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
    border: 1px solid rgba(180,160,120,.15);
    border-left-width: 4px;
    border-radius: 8px;
    background: rgba(12,15,20,.84);
    box-shadow: 0 16px 44px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.03);
    backdrop-filter: blur(16px);
    overflow: hidden;
}
.recursive-node-detail[data-status="success"] { border-left-color: #5B9A6E; }
.recursive-node-detail[data-status="running"] { border-left-color: #6B8BDB; }
.recursive-node-detail[data-status="paused"]  { border-left-color: #D4956B; }
.recursive-node-detail[data-status="error"]   { border-left-color: #E85D4A; }
.recursive-node-detail header {
    flex: 0 0 auto;
    padding: 14px 16px 10px;
    border-bottom: 1px solid rgba(180,160,120,.1);
}
.recursive-node-detail .kicker {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.4px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
    margin-bottom: 4px;
}
.recursive-node-detail h3 {
    margin: 0;
    color: #e8e4dc;
    font-family: var(--wa-font-display);
    font-size: 18px;
    letter-spacing: 1.2px;
    word-break: break-word;
}
.recursive-node-detail section {
    flex: 1 1 0;
    display: flex;
    flex-direction: column;
    min-height: 0;
    border-bottom: 1px solid rgba(180,160,120,.08);
}
.recursive-node-detail section:last-child { border-bottom: 0; }
.recursive-node-detail .section-title {
    padding: 10px 16px 6px;
    font-family: var(--wa-font-mono);
    font-size: 10px;
    letter-spacing: 1.4px;
    color: rgba(232,228,220,.4);
    text-transform: uppercase;
}
.recursive-node-detail ul {
    list-style: none;
    margin: 0;
    padding: 0 8px 8px;
    overflow-y: auto;
    flex: 1 1 auto;
    min-height: 0;
}
.recursive-node-detail .videos li {
    border-bottom: 1px solid rgba(180,160,120,.06);
}
.recursive-node-detail .videos li a {
    display: block;
    padding: 8px 10px;
    color: rgba(232,228,220,.85);
    text-decoration: none;
}
.recursive-node-detail .videos .title {
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
    margin-bottom: 4px;
}
.recursive-node-detail .videos .meta {
    font-family: var(--wa-font-mono);
    font-size: 10px;
    color: rgba(232,228,220,.45);
}
.recursive-node-detail .candidates li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 10px;
    border-bottom: 1px solid rgba(180,160,120,.06);
    font-size: 12px;
}
.recursive-node-detail .candidates li b {
    color: var(--atlas-accent);
    font-family: var(--wa-font-mono);
    font-weight: 500;
}
.recursive-detail-empty {
    padding: 12px 16px;
    color: rgba(232,228,220,.35);
    font-size: 11px;
    font-style: italic;
}
.recursive-detail-hint {
    padding: 4px 16px;
    color: #D4956B;
    font-family: var(--wa-font-mono);
    font-size: 10px;
}
.recursive-detail-more {
    padding: 6px 16px;
    color: var(--atlas-accent);
    font-size: 10px;
    text-align: right;
}
/* ===== Collapsible bottom-left panels ===== */
.atlas-shell-panels-wrap {
    position: absolute;
    z-index: 4;
    left: 24px;
    bottom: clamp(66px, 8.5dvh, 88px);
    width: min(860px, calc(100% - 500px));
    border: 1px solid rgba(180,160,120,.14);
    border-radius: 8px;
    background: rgba(12,15,20,.78);
    box-shadow: 0 16px 44px rgba(0,0,0,.30);
    backdrop-filter: blur(14px);
    overflow: hidden;
}
.atlas-shell-recursive .atlas-shell-panels {
    position: static;
    width: 100%;
    height: clamp(280px, 40dvh, 380px);
    box-shadow: none;
    background: transparent;
    border: 0;
    padding: 10px;
}
.atlas-shell-recursive .atlas-shell-panel {
    height: 100%;
}
.atlas-shell-panels-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 32px;
    padding: 0 14px;
    cursor: pointer;
    color: rgba(232,228,220,.66);
    font-family: var(--wa-font-mono);
    font-size: 11px;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    list-style: none;
}
.atlas-shell-panels-summary::-webkit-details-marker { display: none; }
.atlas-shell-panels-summary .collapse-toggle {
    color: var(--atlas-accent);
    text-decoration: none;
    font-size: 14px;
    line-height: 1;
}
@media (max-width: 900px) {
    html,
    body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        overflow: hidden !important;
    }
    .block-container {
        height: 100dvh !important;
        overflow: hidden !important;
    }
    .atlas-global-nav {
        height: 92px;
        grid-template-columns: minmax(0, 1fr) !important;
        gap: 7px;
        padding: 8px 10px;
        overflow: hidden;
    }
    .atlas-global-brand {
        min-width: 0;
        gap: 8px;
    }
    .atlas-global-mark {
        width: 28px;
        height: 28px;
    }
    .atlas-global-title {
        font-size: 14px;
        letter-spacing: 2px;
    }
    .atlas-global-sub {
        display: none;
    }
    .atlas-global-links {
        width: 100%;
        gap: 6px;
    }
    .atlas-global-link {
        height: 28px;
        padding: 0 10px;
        font-size: 11px;
    }
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
    > div[data-testid="stHorizontalBlock"]:has(button) {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        width: calc(100vw - 44px) !important;
        max-width: calc(100vw - 44px) !important;
        margin: 0.25rem 0 0.55rem !important;
        padding: 5px !important;
        overflow-x: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
    > div[data-testid="stHorizontalBlock"]:has(button) > div {
        flex: 0 0 auto !important;
        width: auto !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel)
    > div[data-testid="stHorizontalBlock"]:has(button) button {
        min-width: 104px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 12px !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] {
        width: calc(100vw - 44px) !important;
        max-width: calc(100vw - 44px) !important;
        margin: 0.25rem 0 0.55rem !important;
        padding: 5px !important;
    }
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] button,
    div[data-testid="stVerticalBlock"]:has(> div .atlas-command-nav-sentinel) div[data-testid="stPills"] [role="radio"] {
        min-width: 104px !important;
        height: 32px !important;
        min-height: 32px !important;
        padding: 0 12px !important;
    }
    .atlas-shell-stage {
        height: calc(100dvh - 164px);
        min-height: 0;
        border-radius: 10px;
    }
    .atlas-shell-hero {
        top: 22px;
        left: 24px;
        width: calc(100% - 48px);
    }
    .atlas-shell-hero-compact {
        top: 16px;
        left: 20px;
        width: calc(100% - 40px);
        max-width: none;
    }
    .atlas-shell-hero-compact .atlas-shell-kicker {
        font-size: 9px;
        line-height: 1.45;
        letter-spacing: .9px;
        -webkit-line-clamp: 2;
    }
    .atlas-shell-display,
    .atlas-shell-panels {
        display: none;
    }
    .atlas-shell-drawers {
        left: 22px;
        right: 22px;
        top: 132px;
        width: auto;
    }
    .atlas-shell-recursive .atlas-shell-hero {
        top: 16px;
        left: 20px;
        width: calc(100% - 40px);
        max-width: none;
    }
    .atlas-shell-recursive .atlas-shell-hero p {
        display: none;
    }
    .recursive-graph {
        inset: 104px 18px 70px 18px;
    }
    .atlas-shell-recursive .atlas-shell-drawers {
        left: 18px;
        right: 18px;
        top: auto;
        bottom: 68px;
        width: auto;
        min-width: 0;
        height: 42dvh;
    }
    .recursive-node-detail header {
        padding: 10px 12px 8px;
    }
    .recursive-node-detail h3 {
        font-size: 15px;
    }
    .recursive-node-detail .section-title {
        padding: 8px 12px 5px;
    }
    button[data-testid="stPopoverButton"] {
        min-width: 78px !important;
        height: 28px !important;
        min-height: 28px !important;
        max-height: 28px !important;
        padding: 0 10px !important;
    }
    div[data-testid="stPopoverBody"] {
        top: 118px !important;
        width: calc(100vw - 24px) !important;
        max-width: calc(100vw - 24px) !important;
        min-height: 0 !important;
        max-height: calc(100dvh - 132px) !important;
        border-radius: 12px !important;
    }
    .atlas-popover-head {
        grid-template-columns: 32px minmax(0, 1fr);
        min-height: 86px;
        gap: 12px;
        padding: 18px 18px 16px;
    }
    .atlas-popover-icon {
        width: 30px;
        height: 30px;
    }
    .atlas-popover-title {
        font-size: 16px !important;
        letter-spacing: 2px !important;
    }
    .atlas-popover-head p {
        font-size: 12px !important;
        margin-top: 6px !important;
    }
    .atlas-popover-metrics,
    .atlas-popover-segment-grid {
        grid-template-columns: 1fr;
    }
    .atlas-popover-metrics,
    .atlas-popover-bars,
    .atlas-popover-segments {
        padding: 18px;
    }
    .atlas-popover-metric {
        min-height: 96px;
        padding: 20px;
    }
    .atlas-popover-bar-row {
        grid-template-columns: minmax(0, 1fr) minmax(84px, 1.2fr) auto;
        gap: 10px;
    }
    .atlas-popover-bar-row span {
        text-align: left;
    }
    .atlas-popover-footer {
        padding: 14px 18px 18px;
        flex-direction: column;
        align-items: flex-start;
    }
    div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) {
        width: calc(100vw - 24px) !important;
        max-width: calc(100vw - 24px) !important;
        max-height: calc(100dvh - 96px) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stDialog"] div[role="dialog"]:has(.atlas-modal-head) > div {
        max-height: calc(100dvh - 96px) !important;
    }
    div[data-testid="stDialog"] button[aria-label="Close"] {
        top: 18px !important;
        right: 18px !important;
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        min-height: 38px !important;
    }
    .atlas-modal-head {
        grid-template-columns: 24px minmax(0, 1fr);
        min-height: 74px;
        gap: 12px;
        padding: 16px 70px 14px 20px;
    }
    .atlas-modal-title {
        font-size: 15px;
        letter-spacing: 1.8px;
    }
    .atlas-modal-copy p {
        font-size: 11px !important;
        white-space: normal;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .atlas-modal-filter-bar,
    div[data-testid="stDialog"] .atlas-popover-metrics,
    div[data-testid="stDialog"] .atlas-popover-bars,
    div[data-testid="stDialog"] .atlas-popover-segments {
        padding-left: 18px;
        padding-right: 18px;
    }
    .atlas-modal-filter-bar,
    div[data-testid="stDialog"] .atlas-popover-metrics {
        grid-template-columns: 1fr;
    }
    div[data-testid="stDialog"] .atlas-popover-metric {
        min-height: 72px;
        padding: 15px 16px 12px;
    }
    div[data-testid="stDialog"] .atlas-popover-metric strong {
        font-size: 25px;
    }
    div[data-testid="stDialog"] [data-testid="stHorizontalBlock"],
    div[data-testid="stDialog"] .atlas-popover-bars,
    div[data-testid="stDialog"] .atlas-popover-segments,
    div[data-testid="stDialog"] .atlas-shell-list-editor,
    div[data-testid="stDialog"] .atlas-shell-empty,
    div[data-testid="stDialog"] [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stDialog"] [data-testid="stDataFrame"],
    div[data-testid="stDialog"] iframe,
    div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"]:has(.atlas-native-slot-head) {
        margin-left: 18px !important;
        margin-right: 18px !important;
        max-width: calc(100% - 36px) !important;
        padding-left: 0;
        padding-right: 0;
    }
    .atlas-native-slot-head {
        flex-direction: column;
        gap: 5px;
    }
    .atlas-native-slot-head p {
        max-width: 100%;
        text-align: left;
    }
    .atlas-modal-footer {
        padding: 11px 18px 13px;
        flex-direction: column;
        align-items: flex-start;
    }
    div[data-testid="stPopoverBody"] .stSelectbox,
    div[data-testid="stPopoverBody"] .stRadio,
    div[data-testid="stPopoverBody"] .stTextInput,
    div[data-testid="stPopoverBody"] .stNumberInput,
    div[data-testid="stPopoverBody"] .stTextArea,
    div[data-testid="stPopoverBody"] .stButton,
    div[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] {
        padding-inline: 18px !important;
    }
    .atlas-shell-drawer-body {
        max-height: 28dvh;
    }
    .atlas-shell-timeline {
        grid-template-columns: 38px 1fr;
        width: calc(100% - 28px);
        bottom: 14px;
        padding: 12px 14px;
    }
    .atlas-shell-range {
        grid-column: 1 / -1;
    }
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 5px !important;
        overflow-x: auto !important;
        padding: 3px 4px !important;
        margin-bottom: -6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) > div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) > div[data-testid="stColumn"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[data-testid="stPopoverButton"]) button[data-testid="stPopoverButton"] {
        min-width: 58px !important;
        height: 24px !important;
        min-height: 24px !important;
        max-height: 24px !important;
        padding: 0 8px !important;
        font-size: 9px !important;
    }
    button[data-testid="stPopoverButton"] div[data-testid="stMarkdownContainer"] p {
        font-size: 9px !important;
        line-height: 1 !important;
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
                <span><em>{t("nav.mode")}</em><strong>{t("nav.display_mode")}</strong></span>
                <span><em>{t("nav.year")}</em><strong>{t("nav.display_year")}</strong></span>
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
