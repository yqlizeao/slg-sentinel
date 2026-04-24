"""
SLG Sentinel — 企业级数据分析监控台
"""

import streamlit as st

from ui.pages.crawl import render_crawl_page
from ui.pages.overview import render_overview_page
from ui.pages.profile import render_profile_page
from ui.pages.recursive_crawl import render_recursive_crawl_page
from ui.pages.report import render_report_page
from ui.pages.settings import render_settings_page

st.set_page_config(
    page_title="SLG Sentinel | 监控看板",
    page_icon="cloudflare_pages/favicon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background-color: #FAFAFA !important;
    color: #171717 !important;
}

header[data-testid="stHeader"] { background-color: transparent !important; }
footer { visibility: hidden !important; display: none !important; }

section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #EAEAEA !important;
    width: 180px !important;
    min-width: 180px !important;
    max-width: 180px !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stAppDeployButton"],
[data-testid="stMainMenuButton"] {
    display: none !important;
}

.block-container {
    padding-top: 1rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}
.stSidebar [data-testid="stMarkdownContainer"] p {
    color: #666666 !important;
    font-size: 13px !important;
}

.stSidebar div[role="radiogroup"] > label {
    padding: 8px 12px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}
.stSidebar div[role="radiogroup"] > label:hover {
    background-color: #F5F5F5;
}

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

.platform-icon {
    width: 18px;
    height: 18px;
    vertical-align: text-bottom;
    margin-right: 8px;
    border-radius: 2px;
}

.platform-stat-card {
    min-height: 150px;
    margin-bottom: 16px;
    padding: 18px 24px 20px;
    border: 1px solid #EAEAEA;
    border-radius: 8px;
    background: #FFFFFF;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.platform-stat-card__header {
    display: flex;
    align-items: center;
    min-width: 0;
    margin-bottom: 48px;
}

.platform-stat-card__header .platform-icon {
    flex: 0 0 18px;
    display: block;
}

.platform-stat-card__label {
    min-width: 0;
    overflow: hidden;
    color: #666666;
    font-size: 14px;
    font-weight: 500;
    line-height: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.platform-stat-card__value {
    color: #000000;
    font-size: 42px;
    font-weight: 700;
    line-height: 1;
}

.platform-stat-card__delta {
    display: inline-flex;
    align-items: center;
    max-width: 100%;
    margin-top: 22px;
    padding: 8px 12px;
    border-radius: 999px;
    background: #EAF7ED;
    color: #168A35;
    font-size: 14px;
    font-weight: 500;
    line-height: 20px;
    white-space: normal;
}
</style>
""",
    unsafe_allow_html=True,
)


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """
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
        """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "应用导航",
            ["总览", "采集", "递归采集", "画像", "智能报表", "设置"],
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
elif page == "设置":
    render_settings_page()
