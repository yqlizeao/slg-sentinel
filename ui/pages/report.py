from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from ui.components.common import render_atlas_ops_board, render_empty_state, render_page_header, render_data_freshness, icon
from ui.i18n import t
from ui.services.app_services import load_report_artifacts, run_cli
from ui.services.overview_service import get_weekly_insights


def _render_insights_summary(insights: list[dict]) -> None:
    if not insights: return
    st.markdown(f"<h3>{t('report.insights')}</h3>", unsafe_allow_html=True)
    cols = st.columns(min(len(insights), 4))
    accent_colors = ["#d4af37", "#E85D4A", "#6B8BDB", "#5B9A6E", "#9B7FD4", "#D4956B"]
    sentiment_map = {"positive": ("trend", "#5B9A6E"), "negative": ("alert", "#E85D4A"), "mixed": ("search", "#6B8BDB")}
    for idx, item in enumerate(insights[:4]):
        with cols[idx]:
            topic = item.get("topic", "")
            sentiment = item.get("sentiment", "mixed")
            demand = item.get("core_demand", "")
            count = item.get("count", 0)
            color = accent_colors[idx % len(accent_colors)]
            icon_name, icon_color = sentiment_map.get(sentiment, ("search", "#6B8BDB"))
            svg = icon(icon_name, color=icon_color)
            st.markdown(f"""<div style='background:rgba(12,15,20,0.92); border:1px solid rgba(180,160,120,0.15); border-top:2px solid {color}; border-radius:8px; padding:20px; box-shadow:0 4px 24px rgba(0,0,0,0.25); min-height:130px;'>
                <div style='font-size:10px; color:rgba(232,228,220,0.35); text-transform:uppercase; letter-spacing:0.8px;'>
                    {svg} {sentiment} · {count} 条</div>
                <div style='font-family:Cinzel,serif; font-size:14px; font-weight:600; color:#E8E4DC;
                            margin:10px 0 8px; letter-spacing:0.5px;'>{topic}</div>
                <div style='font-size:11px; color:rgba(232,228,220,0.45); line-height:1.6;'>{demand}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def render_report_page() -> None:
    render_page_header(
        t("report.title"),
        t("report.subtitle"),
        [("cycle", "weekly"), ("year", "2026 AD"), ("engine", "LLM")],
    )
    render_atlas_ops_board(
        t("report.ops.title"),
        t("report.ops.subtitle"),
        [("Cycle", "weekly"), ("Engine", "LLM"), ("Output", "markdown"), ("Scope", "signals")],
        t("report.ops.eyebrow"),
    )

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 1.5])
    with ctrl_col1:
        custom_date = st.date_input(t("report.date_label"), value=datetime.now(), label_visibility="collapsed")
    with ctrl_col2:
        clk = icon("clock", color="rgba(232,228,220,0.3)")
        st.markdown(f"<div style='padding-top:8px; font-size:12px; color:rgba(232,228,220,0.4);'>{clk} {t('report.type_weekly')}</div>", unsafe_allow_html=True)
    with ctrl_col3:
        generate_btn = st.button(t("report.generate"), type="primary", use_container_width=True)

    date_str = custom_date.strftime("%Y-%m-%d")

    if generate_btn:
        with st.spinner(t("report.generating")):
            _, stderr, code = run_cli(["analyze", "--type", "weekly", "--date", date_str])
        if code == 0:
            st.success(t("report.generated"))
            st.rerun()
        else:
            st.error(t("report.failed"))
            with st.expander(t("report.logs")):
                st.code(stderr, language="bash")

    artifacts = load_report_artifacts(date_str)
    if not artifacts:
        insights = get_weekly_insights(date_str)
        if insights:
            _render_insights_summary(insights)
        else:
            render_empty_state("report", t("report.no_report_title"), t("report.no_report_desc"), t("report.no_report_hint"))
        return

    payload = artifacts["payload"]
    insights = payload.get("insights", [])
    if insights: _render_insights_summary(insights)

    st.markdown(f"<h3>{t('report.sentiment_mentions')} ({date_str})</h3>", unsafe_allow_html=True)
    try:
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown(f"<h5>{t('report.sentiment')}</h5>", unsafe_allow_html=True)
            sent_data = payload.get("sentiment", {})
            if sum(sent_data.values()) > 0:
                try:
                    import altair as alt
                    label_map = {"positive": "正面", "negative": "负面", "neutral": "中性"}
                    s_items = [(label_map.get(k, k), v) for k, v in sent_data.items()]
                    s_df = pd.DataFrame(s_items, columns=["情感", "数量"])
                    chart = alt.Chart(s_df).mark_arc(innerRadius=60, outerRadius=110, stroke="#0A0C10", strokeWidth=2).encode(
                        theta=alt.Theta("数量:Q"),
                        color=alt.Color("情感:N", scale=alt.Scale(
                            domain=["正面", "负面", "中性"], range=["#5B9A6E", "#E85D4A", "rgba(232,228,220,0.28)"]
                        ), legend=alt.Legend(labelColor="rgba(232,228,220,0.58)", titleColor="rgba(232,228,220,0.58)")),
                        tooltip=["情感", "数量"],
                    ).properties(height=340, background="transparent").configure_view(strokeWidth=0)
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.bar_chart(pd.Series(sent_data))
            else:
                st.info(t("report.no_sentiment"))

        with chart_col2:
            st.markdown(f"<h5>{t('report.mentions')}</h5>", unsafe_allow_html=True)
            mentions_data = payload.get("mentions", {})
            if mentions_data:
                try:
                    import altair as alt
                    m_df = pd.DataFrame(list(mentions_data.items()), columns=["游戏", "提及次数"]).sort_values("提及次数").tail(10)
                    chart = alt.Chart(m_df).mark_bar(cornerRadiusEnd=3, color="#d4af37").encode(
                        x=alt.X("提及次数:Q", title="", axis=alt.Axis(labelColor="rgba(232,228,220,0.46)", gridColor="rgba(180,160,120,0.06)")),
                        y=alt.Y("游戏:N", sort="-x", title="", axis=alt.Axis(labelColor="rgba(232,228,220,0.58)")),
                        tooltip=["游戏", "提及次数"],
                    ).properties(height=340, background="transparent").configure_view(strokeWidth=0)
                    st.altair_chart(chart, use_container_width=True)
                except ImportError:
                    st.bar_chart(pd.DataFrame(list(mentions_data.items()), columns=["Game", "Mentions"]).set_index("Game"))
            else:
                st.info(t("report.no_mentions"))

        render_data_freshness()
        st.markdown("<hr style='border:none; border-top:1px solid rgba(180,160,120,0.08); margin:2rem 0;'/>", unsafe_allow_html=True)
        st.markdown(f"<h3>{t('report.body')}</h3>", unsafe_allow_html=True)
        st.markdown(artifacts["markdown"])
    except Exception as exc:
        st.error(t("report.render_failed", error=exc))
