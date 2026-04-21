from __future__ import annotations
from datetime import datetime

import pandas as pd
import streamlit as st

from ui.services.app_services import load_report_artifacts, run_cli


def render_report_page() -> None:
    col1, col2 = st.columns([1, 1])
    with col1:
        report_span = st.selectbox("分析跨度层级", ["周度汇总研判 (Weekly)", "每日动向快报 (Daily - WIP)", "月度战略大盘 (Monthly - WIP)"])
    with col2:
        custom_date = st.date_input("时序截断锚点 (默认系统当下日)", value=datetime.now())

    date_str = custom_date.strftime("%Y-%m-%d")
    st.markdown("<p style='color: #16a34a; font-size: 13px; font-weight: 500;'>当前已支持按日期生成周报，请先选择分析跨度和日期。</p>", unsafe_allow_html=True)

    if st.button("生成分析报告", type="primary"):
        if "WIP" in report_span:
            st.warning("当前仅支持“周度汇总研判 (Weekly)”报告，其余类型暂未开放。")
        else:
            with st.spinner("正在汇总平台数据并生成分析报告..."):
                _, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
            if code == 0:
                st.success("报告已生成，并写入 reports 目录。")
                st.rerun()
            else:
                st.error("报告生成失败，请查看下方日志。")
                with st.expander("详细日志"):
                    st.code(stderr, language="bash")

    artifacts = load_report_artifacts(date_str)
    if not artifacts:
        return

    st.markdown(f"<h3>情绪分布与竞品提及情况（{date_str}）</h3>", unsafe_allow_html=True)
    try:
        payload = artifacts["payload"]

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("<h5 style='margin-bottom:12px;'>情绪分布</h5>", unsafe_allow_html=True)
            sent_data = payload.get("sentiment", {})
            if sum(sent_data.values()) > 0:
                try:
                    import altair as alt

                    s_df = pd.DataFrame(list(sent_data.items()), columns=["Sentiment", "Count"])
                    chart = alt.Chart(s_df).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta(field="Count", type="quantitative"),
                        color=alt.Color(field="Sentiment", type="nominal", scale=alt.Scale(domain=["positive", "negative", "neutral"], range=["#16a34a", "#dc2626", "#94a3b8"])),
                        tooltip=["Sentiment", "Count"],
                    ).properties(height=300)
                    st.altair_chart(chart, use_container_width=True)
                except Exception:
                    st.bar_chart(pd.Series(sent_data))
            else:
                st.info("当前没有可展示的情绪分布数据。")

        with chart_col2:
            st.markdown("<h5 style='margin-bottom:12px;'>竞品提及分布</h5>", unsafe_allow_html=True)
            mentions_data = payload.get("mentions", {})
            if mentions_data:
                mentions_df = pd.DataFrame(list(mentions_data.items()), columns=["Game", "Mentions"]).sort_values("Mentions", ascending=False)
                st.bar_chart(mentions_df.set_index("Game"), height=300)
            else:
                st.info("当前没有可展示的竞品提及数据。")

        st.markdown("---")
        st.markdown("<h3>报告正文（Markdown）</h3>", unsafe_allow_html=True)
        st.markdown(artifacts["markdown"])
    except Exception as exc:
        st.error(f"报告渲染失败：{exc}")
