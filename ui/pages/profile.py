from __future__ import annotations
import streamlit as st

import pandas as pd

from ui.components.common import (
    icon,
    render_atlas_callout,
    render_atlas_ops_board,
    render_data_freshness,
    render_empty_state,
    render_kpi_card,
    render_page_header,
)
from ui.i18n import t
from ui.services.app_services import load_profiles_dataframe

def render_profile_page() -> None:
    df = load_profiles_dataframe()
    render_page_header(
        t("profile.title"),
        t("profile.subtitle"),
        [
            ("profiles", str(len(df)) if not df.empty else "0"),
            ("cohort", "2026 AD"),
            ("source", "comments"),
        ],
    )
    render_atlas_ops_board(
        t("profile.ops.title"),
        t("profile.ops.subtitle"),
        [("Profiles", str(len(df)) if not df.empty else "0"), ("Segments", "4"), ("Source", "comments"), ("Cohort", "2026")],
        t("profile.ops.eyebrow"),
    )
    if df.empty:
        render_empty_state("profile", t("profile.empty_title"), t("profile.empty_desc"), t("profile.empty_hint"))
        return

    # KPI 卡片
    whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
    refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
    hardcore = len(df[df["tags"].str.contains("硬核|策略|重度", na=False)])
    pct = f"({whales_dolphins / len(df) * 100:.0f}%)" if len(df) > 0 else ""

    st.markdown(f"""<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px;'>
        {render_kpi_card(t("profile.kpi.players"), str(len(df)))}
        {render_kpi_card(t("profile.kpi.high_pay"), f"{whales_dolphins} {pct}", "#5B9A6E")}
        {render_kpi_card(t("profile.kpi.conversion"), str(refugees), "#E85D4A")}
        {render_kpi_card(t("profile.kpi.hardcore"), str(hardcore), "#6B8BDB")}
    </div>""", unsafe_allow_html=True)

    render_atlas_callout(
        t("profile.callout_title"),
        t("profile.callout_body"),
        "lightbulb",
    )
    st.markdown("<div style='height:22px;'></div>", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown(f"<h3>{t('profile.tag_distribution')}</h3>", unsafe_allow_html=True)
        tag_counts: dict[str, int] = {}
        for tags_str in df["tags"].dropna():
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag: tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            try:
                import altair as alt
                tag_df = pd.DataFrame(list(tag_counts.items()), columns=["标签", "人数"]).sort_values("人数").tail(12)
                chart = alt.Chart(tag_df).mark_bar(cornerRadiusEnd=3, color="#d4af37").encode(
                    x=alt.X("人数:Q", title="", axis=alt.Axis(labelColor="rgba(232,228,220,0.46)", gridColor="rgba(180,160,120,0.06)")),
                    y=alt.Y("标签:N", sort="-x", title="", axis=alt.Axis(labelColor="rgba(232,228,220,0.58)")),
                    tooltip=["标签", "人数"],
                ).properties(height=380, background="transparent").configure_view(strokeWidth=0)
                st.altair_chart(chart, use_container_width=True)
            except ImportError:
                st.bar_chart(pd.DataFrame(list(tag_counts.items()), columns=["Tag", "Count"]).set_index("Tag"))

    with chart_col2:
        st.markdown(f"<h3>{t('profile.spend_distribution')}</h3>", unsafe_allow_html=True)
        spend_df = df["spend_type"].value_counts().reset_index()
        spend_df.columns = ["类型", "人数"]
        label_map = {"free": "免费玩家", "dolphin": "中度付费", "whale": "重度付费"}
        spend_df["类型"] = spend_df["类型"].map(lambda x: label_map.get(x, x))
        try:
            import altair as alt
            chart = alt.Chart(spend_df).mark_arc(innerRadius=60, outerRadius=110, stroke="#0A0C10", strokeWidth=2).encode(
                theta=alt.Theta("人数:Q"),
                color=alt.Color("类型:N", scale=alt.Scale(
                    domain=["免费玩家", "中度付费", "重度付费"],
                    range=["rgba(232,228,220,0.28)", "#6B8BDB", "#d4af37"]
                ), legend=alt.Legend(labelColor="rgba(232,228,220,0.58)", titleColor="rgba(232,228,220,0.58)")),
                tooltip=["类型", "人数"],
            ).properties(height=380, background="transparent").configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.bar_chart(spend_df.set_index("类型"))

    render_data_freshness()

    st.markdown(f"<h3>{t('profile.focus_players')}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:12px; color:rgba(232,228,220,0.4); margin-bottom:10px;'>{t('profile.focus_desc')}</p>", unsafe_allow_html=True)
    st.dataframe(
        df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(columns={
            "platform": "平台", "username": "昵称", "age_group": "年龄段",
            "spend_type": "付费类型", "tags": "行为标签", "location": "地区",
        }),
        use_container_width=True, hide_index=True,
    )
