from __future__ import annotations
import pandas as pd
import streamlit as st
from ui.components.common import render_empty_state, render_page_header, render_data_freshness, render_kpi_card, icon
from ui.services.app_services import load_profiles_dataframe

def render_profile_page() -> None:
    render_page_header("玩家画像", "基于评论行为和游戏偏好推断的用户分群")

    df = load_profiles_dataframe()
    if df.empty:
        render_empty_state("profile", "暂无画像数据",
            "画像数据需要先完成深度采集（获取评论），然后执行画像提取命令生成。",
            "前往「采集」页面完成一次深度采集，然后运行 profile 命令")
        return

    # KPI 卡片
    whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
    refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
    hardcore = len(df[df["tags"].str.contains("硬核|策略|重度", na=False)])
    pct = f"({whales_dolphins / len(df) * 100:.0f}%)" if len(df) > 0 else ""

    st.markdown(f"""<div style='display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:24px;'>
        {render_kpi_card("已识别玩家", str(len(df)))}
        {render_kpi_card("高付费潜力", f"{whales_dolphins} {pct}", "#5B9A6E")}
        {render_kpi_card("潜在转化对象", str(refugees), "#E85D4A")}
        {render_kpi_card("硬核策略玩家", str(hardcore), "#6B8BDB")}
    </div>""", unsafe_allow_html=True)

    # 业务洞察
    bulb = icon("lightbulb", color="#B4A078")
    st.markdown(f"""<div style='background:rgba(12,15,20,0.92); border:1px solid rgba(180,160,120,0.15);
        border-left:3px solid #B4A078; border-radius:0 8px 8px 0; padding:18px 22px;
        box-shadow:0 4px 24px rgba(0,0,0,0.25); margin-bottom:24px;'>
        <div style='font-size:13px; font-weight:600; color:#E8E4DC; margin-bottom:8px;'>{bulb} 画像解读</div>
        <div style='font-size:12px; color:rgba(232,228,220,0.55); line-height:1.8;'>
            <b style='color:rgba(232,228,220,0.75);'>高付费潜力玩家</b>对应"愿意为好内容付费"的群体，
            <b style='color:rgba(232,228,220,0.75);'>潜在转化对象</b>是对现有 SLG 手游氪金模式不满、但仍活跃在社区的玩家
            — 他们正是买断制三国 SLG 的核心目标用户。
        </div>
    </div>""", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<h3>玩家标签分布</h3>", unsafe_allow_html=True)
        tag_counts: dict[str, int] = {}
        for tags_str in df["tags"].dropna():
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag: tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            try:
                import altair as alt
                tag_df = pd.DataFrame(list(tag_counts.items()), columns=["标签", "人数"]).sort_values("人数").tail(12)
                chart = alt.Chart(tag_df).mark_bar(cornerRadiusEnd=3, color="#B4A078").encode(
                    x=alt.X("人数:Q", title="", axis=alt.Axis(labelColor="#555", gridColor="rgba(180,160,120,0.06)")),
                    y=alt.Y("标签:N", sort="-x", title="", axis=alt.Axis(labelColor="#888")),
                    tooltip=["标签", "人数"],
                ).properties(height=380, background="transparent").configure_view(strokeWidth=0)
                st.altair_chart(chart, use_container_width=True)
            except ImportError:
                st.bar_chart(pd.DataFrame(list(tag_counts.items()), columns=["Tag", "Count"]).set_index("Tag"))

    with chart_col2:
        st.markdown("<h3>消费类型分布</h3>", unsafe_allow_html=True)
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
                    range=["#555", "#6B8BDB", "#B4A078"]
                ), legend=alt.Legend(labelColor="#888", titleColor="#888")),
                tooltip=["类型", "人数"],
            ).properties(height=380, background="transparent").configure_view(strokeWidth=0)
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.bar_chart(spend_df.set_index("类型"))

    render_data_freshness()

    st.markdown("<h3>重点关注玩家</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:rgba(232,228,220,0.4); margin-bottom:10px;'>在评论中表现出明确付费意愿或竞品迁移倾向的用户</p>", unsafe_allow_html=True)
    st.dataframe(
        df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(columns={
            "platform": "平台", "username": "昵称", "age_group": "年龄段",
            "spend_type": "付费类型", "tags": "行为标签", "location": "地区",
        }),
        use_container_width=True, hide_index=True,
    )
