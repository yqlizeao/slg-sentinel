from __future__ import annotations
from datetime import datetime

import pandas as pd
import streamlit as st

from ui.components.common import render_empty_state, render_page_header, render_data_freshness
from ui.services.app_services import load_report_artifacts, run_cli
from ui.services.overview_service import get_weekly_insights


def _render_insights_summary(insights: list[dict]) -> None:
    """在报表页顶部展示 LLM 聚类结果的可视化摘要"""
    if not insights:
        return

    st.markdown("<h3>本期核心洞察</h3>", unsafe_allow_html=True)
    cols = st.columns(min(len(insights), 4))
    colors = ["#16a34a", "#dc2626", "#d97706", "#2563eb", "#7c3aed", "#0891b2", "#be185d", "#4338ca"]
    sentiment_icons = {"positive": "📈", "negative": "⚠️", "mixed": "💬"}

    for idx, item in enumerate(insights[:4]):
        with cols[idx]:
            topic = item.get("topic", "")
            sentiment = item.get("sentiment", "mixed")
            demand = item.get("core_demand", "")
            count = item.get("count", 0)
            color = colors[idx % len(colors)]
            icon = sentiment_icons.get(sentiment, "💬")
            st.markdown(f"""<div style='padding:16px; border:1px solid #EAEAEA; border-top:3px solid {color};
                        border-radius:8px; background:#FFF; min-height:120px;'>
                <div style='font-size:11px; color:#888;'>{icon} {sentiment.upper()} · {count} 条</div>
                <div style='font-size:15px; font-weight:700; color:#111; margin:8px 0 6px;'>{topic}</div>
                <div style='font-size:12px; color:#555; line-height:1.5;'>{demand}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


def render_report_page() -> None:
    render_page_header("智能报表", "基于采集数据自动生成情感分析报告，支持 LLM 深度评论聚类。")

    # 控件区：一行内收敛
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 1.5])
    with ctrl_col1:
        custom_date = st.date_input("分析日期", value=datetime.now(), label_visibility="collapsed")
    with ctrl_col2:
        st.markdown("<div style='padding-top:6px; font-size:13px; color:#666;'>报告类型：周度汇总</div>", unsafe_allow_html=True)
    with ctrl_col3:
        generate_btn = st.button("生成周报", type="primary", use_container_width=True)

    date_str = custom_date.strftime("%Y-%m-%d")

    if generate_btn:
        with st.spinner("正在汇总平台数据并生成分析报告..."):
            _, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
        if code == 0:
            st.success("报告已生成，结果如下。")
            st.rerun()
        else:
            st.error("报告生成失败，请查看日志。")
            with st.expander("详细日志"):
                st.code(stderr, language="bash")

    # 尝试加载现有报告
    artifacts = load_report_artifacts(date_str)
    if not artifacts:
        # 尝试展示最近已有的洞察
        insights = get_weekly_insights(date_str)
        if insights:
            _render_insights_summary(insights)
            st.info(f"上方展示的是最近一份报告的核心洞察。如需查看 {date_str} 的完整报告，请点击「生成周报」。")
        else:
            render_empty_state(
                icon="📊",
                title="暂无分析报告",
                description="选择日期并点击「生成周报」，系统将自动汇总近期采集数据并生成情感分析报告。",
                action_hint="首次使用前，请确保已完成至少一次数据采集。",
            )
        return

    # 展示 LLM 聚类结果卡片
    payload = artifacts["payload"]
    insights = payload.get("insights", [])
    if insights:
        _render_insights_summary(insights)

    st.markdown(f"<h3>情感分布与竞品提及（{date_str}）</h3>", unsafe_allow_html=True)
    try:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("<h5 style='margin-bottom:12px;'>情感分布</h5>", unsafe_allow_html=True)
            sent_data = payload.get("sentiment", {})
            if sum(sent_data.values()) > 0:
                try:
                    import altair as alt
                    label_map = {"positive": "正面", "negative": "负面", "neutral": "中性"}
                    s_items = [(label_map.get(k, k), v) for k, v in sent_data.items()]
                    s_df = pd.DataFrame(s_items, columns=["情感", "数量"])
                    chart = alt.Chart(s_df).mark_arc(innerRadius=55, outerRadius=100).encode(
                        theta=alt.Theta("数量:Q"),
                        color=alt.Color("情感:N", scale=alt.Scale(
                            domain=["正面", "负面", "中性"],
                            range=["#16a34a", "#dc2626", "#94a3b8"]
                        )),
                        tooltip=["情感", "数量"],
                    ).properties(height=320)
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.bar_chart(pd.Series(sent_data))
            else:
                st.info("当前没有可展示的情感分布数据。")

        with chart_col2:
            st.markdown("<h5 style='margin-bottom:12px;'>竞品提及分布</h5>", unsafe_allow_html=True)
            mentions_data = payload.get("mentions", {})
            if mentions_data:
                try:
                    import altair as alt
                    m_df = pd.DataFrame(list(mentions_data.items()), columns=["游戏", "提及次数"]).sort_values("提及次数", ascending=True).tail(10)
                    chart = alt.Chart(m_df).mark_bar(cornerRadiusEnd=4, color="#111").encode(
                        x=alt.X("提及次数:Q", title="提及次数"),
                        y=alt.Y("游戏:N", sort="-x", title=""),
                        tooltip=["游戏", "提及次数"],
                    ).properties(height=320)
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.bar_chart(pd.DataFrame(list(mentions_data.items()), columns=["Game", "Mentions"]).set_index("Game"))
            else:
                st.info("当前没有可展示的竞品提及数据。")

        render_data_freshness()

        st.markdown("---")
        st.markdown("<h3>报告正文</h3>", unsafe_allow_html=True)
        st.markdown(artifacts["markdown"])
    except Exception as exc:
        st.error(f"报告渲染失败：{exc}")
