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
