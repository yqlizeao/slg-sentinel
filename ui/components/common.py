"""
SLG Sentinel — 通用 UI 组件

提供统一的页面标题、空状态、数据新鲜度指示器等组件。
所有组件遵循 War-Atlas 风格暗色主题。
"""
from __future__ import annotations

import streamlit as st

# ---------------------------------------------------------------------------
# SVG 图标库 — 替代所有 emoji，保持 16×16 统一规格
# 颜色统一使用 currentColor，由 CSS 控制
# ---------------------------------------------------------------------------
ICONS = {
    "overview": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    "crawl": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "profile": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "report": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "compare": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "settings": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "search": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "trend": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    "alert": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "lightbulb": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/></svg>',
    "shield": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "target": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "clock": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "database": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>',
    "swords": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6"/><path d="M16 16l4 4"/><path d="M19 21l2-2"/><path d="M9.5 6.5L21 18v3h-3L6.5 9.5"/><path d="M11 5l-6 6"/><path d="M8 8L4 4"/><path d="M5 3L3 5"/></svg>',
}


def icon(name: str, size: int = 16, color: str = "#d4af37") -> str:
    """返回指定名称的 SVG 图标 HTML 字符串"""
    svg = ICONS.get(name, ICONS["overview"])
    return f"<span style='display:inline-flex; align-items:center; color:{color}; vertical-align:middle;'>{svg}</span>"


def render_section_title(title: str, description: str | None = None) -> None:
    desc_html = f"<p style='color:rgba(232,228,220,0.45); font-size:12px; margin:6px 0 0 0;'>{description}</p>" if description else ""
    st.markdown(
        f"""<div style='margin-bottom:12px;'>
            <div style='font-family:Cinzel,serif; font-size:16px; font-weight:600; color:#E8E4DC; letter-spacing:1px;'>{title}</div>
            {desc_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "") -> None:
    """统一的页面顶部标题区域，War-Atlas 风格。"""
    sub_html = f"<div style='font-size:12px; color:rgba(232,228,220,0.35); margin-top:4px; letter-spacing:0.5px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""<div style='margin-bottom:24px; padding-bottom:18px; border-bottom:1px solid rgba(180,160,120,0.1);'>
            <div style='font-family:Cinzel,serif; font-size:24px; font-weight:700; color:#E8E4DC;
                        letter-spacing:3px; text-transform:uppercase;'>{title}</div>
            {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_empty_state(icon_name: str, title: str, description: str, action_hint: str = "") -> None:
    """通用空状态占位组件，暗色主题。icon_name 引用 ICONS 字典。"""
    svg = icon(icon_name, color="rgba(180,160,120,0.5)")
    action_html = f"<div style='margin-top:12px; font-size:11px; color:#d4af37; letter-spacing:0.3px;'>{action_hint}</div>" if action_hint else ""
    st.markdown(
        f"""<div style='padding:48px 24px; border:1px dashed rgba(180,160,120,0.15); border-radius:8px;
                    background:rgba(12,15,20,0.6); text-align:center; margin:24px 0;'>
            <div style='margin-bottom:16px; transform:scale(2.5); display:inline-block;'>{svg}</div>
            <div style='font-family:Cinzel,serif; font-size:16px; font-weight:600; color:rgba(232,228,220,0.7);
                        margin-bottom:8px; letter-spacing:1px;'>{title}</div>
            <div style='font-size:13px; color:rgba(232,228,220,0.4); line-height:1.7;
                        max-width:420px; margin:0 auto;'>{description}</div>
            {action_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_data_freshness(label: str = "数据截至") -> None:
    """数据新鲜度指示器。"""
    from datetime import datetime
    now = datetime.now().strftime("%m-%d %H:%M")
    clk = icon("clock", color="rgba(180,160,120,0.3)")
    st.markdown(
        f"<div style='text-align:right; font-size:10px; color:rgba(232,228,220,0.25); margin-top:8px; letter-spacing:0.5px;'>{clk} {label} {now}</div>",
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, accent: str = "#d4af37", sub: str = "") -> str:
    """返回单个 KPI 卡片的 HTML 字符串（War Atlas Stats 面板风格）。"""
    sub_html = f"<div style='font-size:10px;color:rgba(232,228,220,0.25);margin-top:10px;letter-spacing:0.5px;'>{sub}</div>" if sub else ""
    return (
        f"<div style='background:rgba(12,15,20,0.92);border:1px solid rgba(180,160,120,0.15);"
        f"border-radius:8px;padding:20px 22px;min-height:100px;"
        f"box-shadow:0 4px 24px rgba(0,0,0,.4),0 1px 2px rgba(0,0,0,.2),inset 0 1px 0 rgba(255,255,255,.03);'>"
        f"<div style='font-family:IBM Plex Sans,sans-serif;font-size:10px;font-weight:600;"
        f"color:rgba(232,228,220,0.4);text-transform:uppercase;letter-spacing:1.2px;'>{label}</div>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:26px;font-weight:500;"
        f"color:{accent};line-height:1;margin-top:12px;'>{value}</div>"
        f"{sub_html}</div>"
    )

