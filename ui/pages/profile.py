from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components.common import render_empty_state, render_page_header, render_data_freshness
from ui.services.app_services import load_profiles_dataframe


def render_profile_page() -> None:
    render_page_header("玩家画像", "基于评论行为和游戏偏好推断的用户分群，帮助识别目标受众特征。")

    df = load_profiles_dataframe()
    if df.empty:
        render_empty_state(
            icon="👤",
            title="暂无画像数据",
            description="画像数据需要先完成深度采集（获取评论），然后执行画像提取命令生成。",
            action_hint="前往「采集」页面完成一次深度采集，然后在终端运行：python -m src.cli profile --platform bilibili",
        )
        return

    # KPI 卡片
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div style='background:#FFF; border:1px solid #EAEAEA; padding:18px; border-radius:8px;'>
            <div style='font-size:12px; color:#666;'>已识别玩家数</div>
            <div style='font-size:28px; font-weight:700; color:#111; margin-top:6px;'>{len(df)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
        pct = f"({whales_dolphins / len(df) * 100:.0f}%)" if len(df) > 0 else ""
        st.markdown(f"""<div style='background:#FFF; border:1px solid #EAEAEA; padding:18px; border-radius:8px;'>
            <div style='font-size:12px; color:#666;'>高付费潜力玩家</div>
            <div style='font-size:28px; font-weight:700; color:#16a34a; margin-top:6px;'>{whales_dolphins} <span style='font-size:12px; color:#666; font-weight:400;'>{pct}</span></div>
        </div>""", unsafe_allow_html=True)
    with c3:
        refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
        st.markdown(f"""<div style='background:#FFF; border:1px solid #EAEAEA; padding:18px; border-radius:8px;'>
            <div style='font-size:12px; color:#666;'>潜在转化对象</div>
            <div style='font-size:28px; font-weight:700; color:#d97706; margin-top:6px;'>{refugees} <span style='font-size:12px; color:#666; font-weight:400;'>名</span></div>
        </div>""", unsafe_allow_html=True)
    with c4:
        hardcore = len(df[df["tags"].str.contains("硬核|策略|重度", na=False)])
        st.markdown(f"""<div style='background:#FFF; border:1px solid #EAEAEA; padding:18px; border-radius:8px;'>
            <div style='font-size:12px; color:#666;'>硬核策略玩家</div>
            <div style='font-size:28px; font-weight:700; color:#2563eb; margin-top:6px;'>{hardcore} <span style='font-size:12px; color:#666; font-weight:400;'>名</span></div>
        </div>""", unsafe_allow_html=True)

    # 业务洞察区
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style='padding:16px 20px; border-left:3px solid #2563eb; background:#F8FAFC; border-radius:0 8px 8px 0; margin-bottom:20px;'>
        <div style='font-size:14px; font-weight:600; color:#111; margin-bottom:6px;'>💡 画像解读</div>
        <div style='font-size:13px; color:#555; line-height:1.7;'>
            这些玩家画像来自评论区行为分析。<b>高付费潜力玩家</b>对应"愿意为好内容付费"的群体，
            <b>潜在转化对象</b>是那些对现有 SLG 手游氪金模式不满、但仍活跃在社区的"端游遗老"——他们正是买断制三国 SLG 的核心目标用户。
        </div>
    </div>""", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<h3>玩家标签分布</h3>", unsafe_allow_html=True)
        tag_counts: dict[str, int] = {}
        for tags_str in df["tags"].dropna():
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            try:
                import altair as alt
                tag_df = pd.DataFrame(list(tag_counts.items()), columns=["标签", "人数"]).sort_values("人数", ascending=True).tail(12)
                chart = alt.Chart(tag_df).mark_bar(cornerRadiusEnd=4, color="#111").encode(
                    x=alt.X("人数:Q", title="人数"),
                    y=alt.Y("标签:N", sort="-x", title=""),
                    tooltip=["标签", "人数"],
                ).properties(height=360)
                st.altair_chart(chart, use_container_width=True)
            except ImportError:
                st.bar_chart(pd.DataFrame(list(tag_counts.items()), columns=["Tag", "Count"]).set_index("Tag").sort_values("Count", ascending=True))
        else:
            st.info("当前还没有可展示的标签分布。")

    with chart_col2:
        st.markdown("<h3>消费类型分布</h3>", unsafe_allow_html=True)
        spend_df = df["spend_type"].value_counts().reset_index()
        spend_df.columns = ["类型", "人数"]
        label_map = {"free": "免费玩家", "dolphin": "中度付费", "whale": "重度付费"}
        spend_df["类型"] = spend_df["类型"].map(lambda x: label_map.get(x, x))
        try:
            import altair as alt
            chart = alt.Chart(spend_df).mark_arc(innerRadius=55, outerRadius=100).encode(
                theta=alt.Theta("人数:Q"),
                color=alt.Color("类型:N", scale=alt.Scale(
                    domain=["免费玩家", "中度付费", "重度付费"],
                    range=["#94a3b8", "#3b82f6", "#eab308"]
                )),
                tooltip=["类型", "人数"],
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)
        except ImportError:
            st.bar_chart(spend_df.set_index("类型"))

    render_data_freshness()

    st.markdown("<h3>重点关注玩家</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:13px; color:#666; margin-bottom:8px;'>以下玩家在评论中表现出明确的付费意愿或竞品迁移倾向，值得重点关注。</p>", unsafe_allow_html=True)
    st.dataframe(
        df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(
            columns={
                "platform": "平台",
                "username": "昵称",
                "age_group": "年龄段",
                "spend_type": "付费类型",
                "tags": "行为标签",
                "location": "地区",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
