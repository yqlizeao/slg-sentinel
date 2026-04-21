from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.services.app_services import load_profiles_dataframe


def render_profile_page() -> None:
    df = load_profiles_dataframe()
    if df.empty:
        st.warning("当前暂无画像数据。请先完成深度采集，再执行画像提取命令：\n`python -m src.cli profile --platform bilibili --video-id xxx`")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>已识别玩家数</div><div style='font-size:28px; font-weight:700; color:#111;'>{len(df)}</div></div>", unsafe_allow_html=True)
    with c2:
        whales_dolphins = len(df[df["spend_type"].isin(["whale", "dolphin"])])
        st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>高付费潜力玩家</div><div style='font-size:28px; font-weight:700; color:#16a34a;'>{whales_dolphins} <span style='font-size:12px; color:#666; font-weight:400'>名</span></div></div>", unsafe_allow_html=True)
    with c3:
        refugees = len(df[df["tags"].str.contains("重氪难民|端游遗老", na=False)])
        st.markdown(f"<div style='background:#FAFAFA; border:1px solid #EAEAEA; padding:15px; border-radius:8px;'><div style='font-size:12px; color:#666;'>重点转化关注对象</div><div style='font-size:28px; font-weight:700; color:#dc2626;'>{refugees} <span style='font-size:12px; color:#666; font-weight:400'>名</span></div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<h5 style='margin-bottom:12px;'>玩家标签分布</h5>", unsafe_allow_html=True)
        tag_counts: dict[str, int] = {}
        for tags_str in df["tags"].dropna():
            for tag in tags_str.split(","):
                tag = tag.strip()
                if tag:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if tag_counts:
            tag_df = pd.DataFrame(list(tag_counts.items()), columns=["Tag", "Count"]).sort_values(by="Count", ascending=True)
            st.bar_chart(tag_df.set_index("Tag"))
        else:
            st.info("当前还没有可展示的标签分布。")

    with chart_col2:
        st.markdown("<h5 style='margin-bottom:12px;'>消费类型分布（推断）</h5>", unsafe_allow_html=True)
        spend_df = df["spend_type"].value_counts().reset_index()
        spend_df.columns = ["Type", "Count"]
        try:
            import altair as alt

            chart = alt.Chart(spend_df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Type", type="nominal", scale=alt.Scale(domain=["free", "dolphin", "whale"], range=["#94a3b8", "#3b82f6", "#eab308"])),
                tooltip=["Type", "Count"],
            ).properties(height=340)
            st.altair_chart(chart, use_container_width=True)
        except Exception:
            st.bar_chart(df["spend_type"].value_counts())

    st.markdown("<h5>重点玩家名单</h5>", unsafe_allow_html=True)
    st.dataframe(
        df[["platform", "username", "age_group", "spend_type", "tags", "location"]].rename(
            columns={
                "platform": "来源阵地",
                "username": "网民昵称",
                "age_group": "推断龄",
                "spend_type": "消费级",
                "tags": "特征向量集",
                "location": "属地",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
