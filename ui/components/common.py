from __future__ import annotations

import streamlit as st


def render_section_title(title: str, description: str | None = None) -> None:
    desc_html = f"<p style='color:#666; font-size:13px; margin:6px 0 0 0;'>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div style='margin-bottom:12px;'>
            <div style='font-size:18px; font-weight:700; color:#111;'>{title}</div>
            {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str = "") -> None:
    """统一的页面顶部标题区域，所有页面入口处调用。"""
    sub_html = f"<div style='font-size:13px; color:#888; margin-top:2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""<div style='margin-bottom:20px; padding-bottom:16px; border-bottom:1px solid #EAEAEA;'>
            <div style='font-size:22px; font-weight:700; color:#111; letter-spacing:-0.02em;'>{title}</div>
            {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_empty_state(icon: str, title: str, description: str, action_hint: str = "") -> None:
    """通用空状态占位组件，替代简陋的 st.warning。"""
    action_html = f"<div style='margin-top:10px; font-size:12px; color:#2563eb;'>{action_hint}</div>" if action_hint else ""
    st.markdown(
        f"""<div style='padding:40px 24px; border:1px dashed #D4D4D4; border-radius:12px;
                    background:#FCFCFC; text-align:center; margin:20px 0;'>
            <div style='font-size:36px; margin-bottom:12px;'>{icon}</div>
            <div style='font-size:16px; font-weight:600; color:#333; margin-bottom:6px;'>{title}</div>
            <div style='font-size:13px; color:#888; line-height:1.6; max-width:400px; margin:0 auto;'>{description}</div>
            {action_html}
        </div>""",
        unsafe_allow_html=True,
    )


def render_data_freshness(label: str = "数据截至") -> None:
    """数据新鲜度指示器，显示在数据区块底部。"""
    from datetime import datetime
    now = datetime.now().strftime("%m-%d %H:%M")
    st.markdown(
        f"<div style='text-align:right; font-size:11px; color:#bbb; margin-top:4px;'>{label} {now}</div>",
        unsafe_allow_html=True,
    )
